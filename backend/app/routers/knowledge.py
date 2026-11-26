"""Admin: knowledge base (RAG) - upload reference documents, ask questions, design review notes."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_config
from ..deps import Principal, get_staff, require_roles, staff_db
from ..models import AnalysisRun, KbChunk, KbDocument, ServiceRequest
from ..ratelimit import allow
from ..services import activity, kb
from ..services.openai_client import AIError, OpenAIClient

router = APIRouter(prefix="/api/admin", tags=["knowledge"])

EDITORS = ("admin", "engineer")
REVIEWERS = ("admin", "sales", "engineer", "normal")


def get_ai() -> OpenAIClient:
    """Dependency so tests can swap in a fake client."""
    try:
        return OpenAIClient()
    except AIError as exc:
        raise HTTPException(503, str(exc))


def _doc_out(d: KbDocument) -> dict:
    return {"id": d.id, "title": d.title, "filename": d.filename, "content_type": d.content_type, "size": d.size,
            "status": d.status, "error": d.error, "pages": d.pages, "vision_pages": d.vision_pages,
            "chunk_count": d.chunk_count, "created_at": d.created_at.isoformat(),
            "updated_at": d.updated_at.isoformat() if d.updated_at else None}


@router.get("/kb/status")
def kb_status(p: Principal = Depends(get_staff), db: Session = Depends(staff_db)):
    cfg = get_config()
    return {"configured": bool(cfg.openai_api_key), "chat_model": cfg.openai_chat_model,
            "embed_model": cfg.openai_embed_model, **kb.stats(db)}


@router.get("/kb/documents")
def list_documents(p: Principal = Depends(get_staff), db: Session = Depends(staff_db)):
    docs = db.scalars(select(KbDocument).order_by(KbDocument.title)).all()
    return {"items": [_doc_out(d) for d in docs]}


@router.post("/kb/documents")
async def upload_documents(files: List[UploadFile] = File(...), p: Principal = Depends(require_roles(*EDITORS)),
                           db: Session = Depends(staff_db)):
    if len(files) > 60:
        raise HTTPException(422, "Upload at most 60 files at a time")
    added, skipped = [], []
    for f in files:
        data = await f.read()
        doc, reason = kb.save_document(db, data, f.filename or "document", uploaded_by=p.user_id)
        if doc:
            added.append(_doc_out(doc))
        else:
            skipped.append({"filename": f.filename, "reason": reason})
    if added:
        activity.log(db, "kb_upload", user_id=p.user_id, count=len(added))
    return {"added": added, "skipped": skipped}


@router.post("/kb/documents/{doc_id}/reindex")
def reindex(doc_id: int, p: Principal = Depends(require_roles(*EDITORS)), db: Session = Depends(staff_db)):
    d = db.get(KbDocument, doc_id)
    if d is None:
        raise HTTPException(404, "Document not found")
    d.status, d.error = "pending", None
    return _doc_out(d)


@router.delete("/kb/documents/{doc_id}")
def delete_document(doc_id: int, p: Principal = Depends(require_roles("admin")), db: Session = Depends(staff_db)):
    d = db.get(KbDocument, doc_id)
    if d is None:
        raise HTTPException(404, "Document not found")
    db.query(KbChunk).filter(KbChunk.document_id == d.id).delete(synchronize_session=False)
    key = d.storage_key
    db.delete(d)
    db.flush()
    from ..services import storage
    storage.delete(key)
    activity.log(db, "kb_delete", user_id=p.user_id, title=d.title)
    return {"deleted": doc_id}


@router.get("/kb/documents/{doc_id}/file")
def document_file(doc_id: int, p: Principal = Depends(get_staff), db: Session = Depends(staff_db)):
    d = db.get(KbDocument, doc_id)
    if d is None:
        raise HTTPException(404, "Document not found")
    ext = "pdf" if d.content_type == "application/pdf" else "jpg"
    return Response(kb.read_file(d), media_type=d.content_type,
                    headers={"Content-Disposition": f'inline; filename="document-{d.id}.{ext}"'})


class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


@router.post("/kb/ask")
def ask(body: AskIn, request: Request, p: Principal = Depends(get_staff), db: Session = Depends(staff_db),
        ai=Depends(get_ai)):
    if not allow(f"kb-ask:{p.installer_id}:{p.user_id}", 120):
        raise HTTPException(429, "Too many questions this hour; try again later.")
    try:
        return kb.answer(db, body.question, ai)
    except AIError as exc:
        raise HTTPException(502, str(exc))


class NotesIn(BaseModel):
    analysis_id: Optional[int] = None


def _run_for(db: Session, r: ServiceRequest, analysis_id: Optional[int]) -> AnalysisRun:
    aid = analysis_id or r.latest_analysis_id
    run = db.get(AnalysisRun, aid) if aid else None
    if run is None or run.request_id != r.id:
        raise HTTPException(409, "This request has no analysis yet")
    return run


@router.post("/requests/{rid}/design-notes")
def request_design_notes(rid: int, body: NotesIn | None = None, p: Principal = Depends(require_roles(*REVIEWERS)),
                         db: Session = Depends(staff_db), ai=Depends(get_ai)):
    """Run the design check (structured verdicts with citations) for the request's analysis."""
    r = db.get(ServiceRequest, rid)
    if r is None:
        raise HTTPException(404, "Request not found")
    run = _run_for(db, r, body.analysis_id if body else None)
    if not allow(f"kb-notes:{p.installer_id}:{p.user_id}", 60):
        raise HTTPException(429, "Too many requests this hour; try again later.")
    try:
        rv = kb.run_design_review(db, run, ai, p.user_id)
    except AIError as exc:
        raise HTTPException(502, str(exc))
    activity.log(db, "kb_design_review", request_id=r.id, user_id=p.user_id, analysis_id=run.id,
                 conflicts=rv.conflicts, checks=rv.checks)
    return {"summary_text": kb.design_summary(run.outputs or {}, run.inputs or {}), **kb.review_out(rv)}


@router.get("/requests/{rid}/design-review")
def get_design_review(rid: int, analysis_id: Optional[int] = None, p: Principal = Depends(require_roles(*REVIEWERS)),
                      db: Session = Depends(staff_db)):
    r = db.get(ServiceRequest, rid)
    if r is None:
        raise HTTPException(404, "Request not found")
    aid = analysis_id or r.latest_analysis_id
    rv = kb.latest_review(db, aid) if aid else None
    return {"review": kb.review_out(rv) if rv else None, "kb_ready": kb.kb_ready(db)}


class AckIn(BaseModel):
    note: str = Field(min_length=5, max_length=2000)


@router.post("/design-reviews/{review_id}/acknowledge")
def acknowledge_review(review_id: int, body: AckIn, p: Principal = Depends(require_roles("admin", "sales", "engineer")),
                       db: Session = Depends(staff_db)):
    from ..db import utcnow
    from ..models import DesignReview
    rv = db.get(DesignReview, review_id)
    if rv is None:
        raise HTTPException(404, "Review not found")
    rv.acknowledged_by, rv.acknowledged_at, rv.ack_note = p.user_id, utcnow(), body.note.strip()
    run = db.get(AnalysisRun, rv.analysis_run_id)
    activity.log(db, "kb_conflicts_acknowledged", request_id=run.request_id if run else None, user_id=p.user_id,
                 review_id=rv.id, conflicts=rv.conflicts, note=rv.ack_note)
    return kb.review_out(rv)


# ------------------------------------------------------------------ placeholder settings from documents
@router.get("/settings/suggestable")
def suggestable(p: Principal = Depends(require_roles("admin")), db: Session = Depends(staff_db)):
    return {"keys": {k: bool(v["fields"]) for k, v in kb.SUGGEST.items()}, "kb_ready": kb.kb_ready(db)}


@router.post("/settings/placeholders/{key}/suggest")
def suggest_placeholder(key: str, p: Principal = Depends(require_roles("admin")), db: Session = Depends(staff_db),
                        ai=Depends(get_ai)):
    from ..services.settings import load_all
    if key not in kb.SUGGEST:
        raise HTTPException(404, "No document suggestion for this setting")
    try:
        return kb.suggest_setting(db, key, ai, load_all(db)["calc"])
    except AIError as exc:
        raise HTTPException(502, str(exc))


class ApplyIn(BaseModel):
    values: dict[str, float]
    sources: list[dict] = []


@router.post("/settings/placeholders/{key}/apply")
def apply_placeholder(key: str, body: ApplyIn, p: Principal = Depends(require_roles("admin")),
                      db: Session = Depends(staff_db)):
    """Write only the suggested fields into the calculation settings (other values are kept)."""
    from solarcalc import CalcSettings
    from ..services.settings import load_all, save_section
    spec = kb.SUGGEST.get(key)
    if spec is None or not spec["fields"]:
        raise HTTPException(404, "This setting cannot be applied automatically")
    current = dict(load_all(db)["calc"])
    for f, v in body.values.items():
        if f not in spec["fields"]:
            raise HTTPException(422, f"{f} is not part of {key}")
        lo, hi, unit = spec["fields"][f]
        if not lo <= v <= hi:
            raise HTTPException(422, f"{f} must be between {lo} and {hi} {unit}")
        current[f] = v
    if current.get("realistic_yield_low", 0) > current.get("realistic_yield_high", 99):
        raise HTTPException(422, "Low yield cannot be above high yield")
    save_section(db, "calc", CalcSettings.from_dict(current).to_dict())
    activity.log(db, "settings_from_documents", user_id=p.user_id, key=key, values=body.values,
                 sources=[f"{s_.get('title')} p.{s_.get('page')}" for s_ in body.sources][:10])
    return {"ok": True, "calc": load_all(db)["calc"]}


# ------------------------------------------------------------------ design explanation for a project
class ExplainIn(BaseModel):
    lang: str = Field(default="en", pattern="^(en|ta)$")


@router.post("/projects/{pid}/explanation")
def project_explanation(pid: int, body: ExplainIn, p: Principal = Depends(require_roles("admin", "sales", "engineer")),
                        db: Session = Depends(staff_db), ai=Depends(get_ai)):
    from sqlalchemy.orm.attributes import flag_modified
    from ..models import Project
    proj = db.get(Project, pid)
    if proj is None:
        raise HTTPException(404, "Project not found")
    run = db.get(AnalysisRun, (proj.pack or {}).get("analysis_run_id") or 0)
    if run is None:
        raise HTTPException(409, "This project has no design to explain")
    if not allow(f"kb-explain:{p.installer_id}:{p.user_id}", 40):
        raise HTTPException(429, "Too many requests this hour; try again later.")
    try:
        ex = kb.design_explanation(db, run.outputs or {}, run.inputs or {}, ai, body.lang)
    except AIError as exc:
        raise HTTPException(502, str(exc))
    pack = dict(proj.pack or {})
    pack["explanation"] = {**(pack.get("explanation") or {}), body.lang: ex}
    proj.pack = pack
    flag_modified(proj, "pack")
    activity.log(db, "project_explanation", request_id=proj.request_id, user_id=p.user_id, lang=body.lang)
    return ex
