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


@router.post("/requests/{rid}/design-notes")
def request_design_notes(rid: int, body: NotesIn | None = None, p: Principal = Depends(require_roles(*REVIEWERS)),
                         db: Session = Depends(staff_db), ai=Depends(get_ai)):
    r = db.get(ServiceRequest, rid)
    if r is None:
        raise HTTPException(404, "Request not found")
    aid = (body.analysis_id if body and body.analysis_id else None) or r.latest_analysis_id
    run = db.get(AnalysisRun, aid) if aid else None
    if run is None or run.request_id != r.id:
        raise HTTPException(409, "This request has no analysis yet")
    if not allow(f"kb-notes:{p.installer_id}:{p.user_id}", 60):
        raise HTTPException(429, "Too many requests this hour; try again later.")
    try:
        out = kb.design_notes(db, run.outputs or {}, run.inputs or {}, ai)
    except AIError as exc:
        raise HTTPException(502, str(exc))
    activity.log(db, "kb_design_notes", request_id=r.id, user_id=p.user_id, analysis_id=run.id)
    return {"analysis_id": run.id, **out}
