"""Projects: pack, technician checklist, readings, site photos; and bill-photo reading."""
from __future__ import annotations

import base64
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import utcnow
from ..deps import Principal, require_roles, staff_db
from ..models import AnalysisRun, ChecklistItem, Installer, Project, ProjectReading, RequestFile, ServiceRequest, User
from ..services import activity, billread, storage
from ..services import projects as ps
from ..services.quotations import _env, diagram_svg, html_to_pdf
from ..services.requests import notify_status
from ..services.settings import load_all
from ..worker import dispatch_soon

router = APIRouter(prefix="/api/admin", tags=["projects"])

ALL_STAFF = ("admin", "sales", "engineer", "technician")
MANAGERS = ("admin", "sales", "engineer")
STAGE_FOR_STATUS = {"in_progress": "installation", "net_metering": "net_metering", "done": "completed"}


def _get(db: Session, pid: int, p: Principal) -> Project:
    proj = db.get(Project, pid)
    if proj is None:
        raise HTTPException(404, "Project not found")
    if p.role == "technician" and proj.technician_user_id != p.user_id:
        raise HTTPException(404, "Project not found")
    return proj


def _proj_out(db: Session, proj: Project, p: Principal, full: bool = False) -> dict:
    req = db.get(ServiceRequest, proj.request_id)
    items = db.scalars(select(ChecklistItem).where(ChecklistItem.project_id == proj.id).order_by(ChecklistItem.step_no)).all()
    done = sum(1 for i in items if i.done)
    out = {"id": proj.id, "request_id": req.id, "reference": req.reference, "customer_name": req.customer.name,
           "address": req.site.address, "district": req.site.district, "status": proj.status,
           "technician_user_id": proj.technician_user_id, "system_summary": proj.pack.get("system_summary"),
           "progress": f"{done}/{len(items)}", "created_at": proj.created_at.isoformat(),
           "site_visit_at": req.site_visit_at.isoformat() if req.site_visit_at else None}
    if full:
        pack = dict(proj.pack)
        out["customer_phone"] = req.customer.phone
        out["pack"] = pack          # BOM has quantities only - no prices, safe for technicians
        out["checklist"] = [{"id": i.id, "step_no": i.step_no, "title": i.title, "title_ta": i.title_ta,
                             "points": i.points, "done": i.done, "notes": i.notes,
                             "done_at": i.done_at.isoformat() if i.done_at else None} for i in items]
        out["readings"] = [{"id": r.id, "kind": r.kind, "label": r.label, "value": str(r.value), "unit": r.unit,
                            "expected": r.expected, "ok": r.ok, "recorded_at": r.recorded_at.isoformat()}
                           for r in ps.readings(db, proj.id)]
        out["photos"] = [{"id": f.id, "url": storage.signed_url(f.storage_key), "created_at": f.created_at.isoformat()}
                         for f in db.scalars(select(RequestFile).where(RequestFile.project_id == proj.id))]
    return out


@router.get("/projects")
def list_projects(p: Principal = Depends(require_roles(*ALL_STAFF)), db: Session = Depends(staff_db)):
    stmt = select(Project).order_by(Project.id.desc())
    if p.role == "technician":
        stmt = stmt.where(Project.technician_user_id == p.user_id)
    return [_proj_out(db, x, p) for x in db.scalars(stmt)]


@router.get("/projects/{pid}")
def get_project(pid: int, p: Principal = Depends(require_roles(*ALL_STAFF)), db: Session = Depends(staff_db)):
    return _proj_out(db, _get(db, pid, p), p, full=True)


class ProjectPatch(BaseModel):
    status: Optional[str] = None
    technician_user_id: Optional[int] = None


@router.patch("/projects/{pid}")
def patch_project(pid: int, body: ProjectPatch, background: BackgroundTasks,
                  p: Principal = Depends(require_roles(*ALL_STAFF)), db: Session = Depends(staff_db)):
    proj = _get(db, pid, p)
    if body.technician_user_id is not None:
        if p.role == "technician":
            raise HTTPException(403, "Only managers assign technicians")
        if body.technician_user_id and db.get(User, body.technician_user_id) is None:
            raise HTTPException(422, "User not found")
        proj.technician_user_id = body.technician_user_id or None
    if body.status and body.status != proj.status:
        if body.status not in ("planned", "in_progress", "net_metering", "done"):
            raise HTTPException(422, "Bad status")
        proj.status = body.status
        req = db.get(ServiceRequest, proj.request_id)
        stage = STAGE_FOR_STATUS.get(body.status)
        if stage and req.stage != stage:
            req.stage = stage
            inst = db.get(Installer, proj.installer_id)
            notify_status(db, req, inst.slug, stage)
    activity.log(db, "project_updated", request_id=proj.request_id, user_id=p.user_id, project_id=proj.id,
                 status=proj.status, technician=proj.technician_user_id)
    db.commit()
    dispatch_soon(background, p.installer_id)
    return _proj_out(db, proj, p, full=True)


class ChecklistPatch(BaseModel):
    done: Optional[bool] = None
    notes: Optional[str] = None
    points: Optional[list[dict]] = None


@router.patch("/projects/{pid}/checklist/{cid}")
def patch_checklist(pid: int, cid: int, body: ChecklistPatch, p: Principal = Depends(require_roles(*ALL_STAFF)),
                    db: Session = Depends(staff_db)):
    proj = _get(db, pid, p)
    item = db.get(ChecklistItem, cid)
    if item is None or item.project_id != proj.id:
        raise HTTPException(404)
    if body.points is not None:
        item.points = [{"text": str(x.get("text", ""))[:300], "done": bool(x.get("done"))} for x in body.points]
    if body.notes is not None:
        item.notes = body.notes[:4000]
    if body.done is not None:
        item.done = body.done
        item.done_by = p.user_id if body.done else None
        item.done_at = utcnow() if body.done else None
    if proj.status == "planned" and (body.done or any(x.get("done") for x in (body.points or []))):
        proj.status = "in_progress"
        req = db.get(ServiceRequest, proj.request_id)
        if req.stage in ("accepted", "site_visit"):
            req.stage = "installation"
    activity.log(db, "checklist_updated", request_id=proj.request_id, user_id=p.user_id, step=item.step_no,
                 done=item.done)
    return {"id": item.id, "done": item.done, "points": item.points, "notes": item.notes}


class ReadingIn(BaseModel):
    kind: str = Field(pattern="^(voc|isc|earth_resistance|insulation|ac_voltage|other)$")
    label: str = ""
    value: float
    unit: Optional[str] = None


UNITS = {"voc": "V", "isc": "A", "earth_resistance": "ohm", "insulation": "Mohm", "ac_voltage": "V"}


@router.post("/projects/{pid}/readings")
def add_reading(pid: int, body: ReadingIn, p: Principal = Depends(require_roles(*ALL_STAFF)),
                db: Session = Depends(staff_db)):
    proj = _get(db, pid, p)
    value = Decimal(str(body.value))
    expected, ok = ps.evaluate_reading(proj, body.kind, body.label, value, load_all(db))
    r = ProjectReading(project_id=proj.id, kind=body.kind, label=body.label[:100], value=value,
                       unit=body.unit or UNITS.get(body.kind, ""), expected=expected, ok=ok, recorded_by=p.user_id)
    db.add(r)
    db.flush()
    activity.log(db, "reading_recorded", request_id=proj.request_id, user_id=p.user_id, kind=body.kind,
                 label=body.label, value=str(value), ok=ok)
    return {"id": r.id, "kind": r.kind, "label": r.label, "value": str(r.value), "unit": r.unit,
            "expected": expected, "ok": ok}


@router.delete("/projects/{pid}/readings/{rid}")
def delete_reading(pid: int, rid: int, p: Principal = Depends(require_roles(*ALL_STAFF)), db: Session = Depends(staff_db)):
    proj = _get(db, pid, p)
    r = db.get(ProjectReading, rid)
    if r is None or r.project_id != proj.id:
        raise HTTPException(404)
    activity.log(db, "reading_deleted", request_id=proj.request_id, user_id=p.user_id, kind=r.kind, value=str(r.value))
    db.delete(r)
    return {"ok": True}


@router.post("/projects/{pid}/photos")
async def add_photo(pid: int, file: UploadFile = File(...), p: Principal = Depends(require_roles(*ALL_STAFF)),
                    db: Session = Depends(staff_db)):
    proj = _get(db, pid, p)
    try:
        key, ctype, size = storage.save_upload(p.installer_id, await file.read())
    except storage.UploadError as exc:
        raise HTTPException(422, str(exc))
    f = RequestFile(project_id=proj.id, kind="site_photo", storage_key=key, content_type=ctype, size=size,
                    uploaded_by="staff")
    db.add(f)
    db.flush()
    activity.log(db, "site_photo", request_id=proj.request_id, user_id=p.user_id, project_id=proj.id)
    return {"id": f.id, "url": storage.signed_url(key)}


def _simple_html(text: str) -> str:
    """Model text (headings, bullets, **bold**) -> safe HTML for the PDF."""
    import html as _h
    import re as _re
    out, in_list = [], False
    for raw in (text or "").splitlines():
        line = _h.escape(raw.rstrip())
        line = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        m_b = _re.match(r"^\s*(?:[-*•]|\d+[.)])\s+(.*)$", line)
        m_h = _re.match(r"^#{1,4}\s+(.*)$", line)
        if m_b:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{m_b.group(1)}</li>")
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        if m_h:
            out.append(f"<h3>{m_h.group(1)}</h3>")
        elif line.strip():
            out.append(f"<p>{line}</p>")
    if in_list:
        out.append("</ul>")
    return "".join(out)


@router.get("/projects/{pid}/pack.pdf")
def pack_pdf(pid: int, lang: str = "en", p: Principal = Depends(require_roles(*ALL_STAFF)), db: Session = Depends(staff_db)):
    proj = _get(db, pid, p)
    data = _get_project_out(db, proj, p)
    s = load_all(db)
    run = db.get(AnalysisRun, proj.pack.get("analysis_run_id")) if proj.pack.get("analysis_run_id") else None
    svgs = {}
    if run:
        for k in ("wiring_print", "sld", "roof", "schedule"):
            svgs[k] = "data:image/svg+xml;base64," + base64.b64encode(diagram_svg(db, run, k).encode()).decode()
    exps = (proj.pack or {}).get("explanation") or {}
    ex = exps.get(lang) or exps.get("en") or exps.get("ta")
    explanation = None
    if ex:
        from markupsafe import Markup
        explanation = {"html": Markup(_simple_html(ex.get("text", ""))), "sources": ex.get("sources", [])}
    html = _env.get_template("pdf/project_pack.html").render(p=data, company=s["company"], diagrams=svgs,
                                                               explanation=explanation)
    return Response(html_to_pdf(html), media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="project-pack-{data["reference"]}.pdf"'})


def _get_project_out(db, proj, p):
    return _proj_out(db, proj, p, full=True)


# ------------------------------------------------------------------ bill reading
@router.post("/files/{fid}/read-bill")
def read_bill(fid: int, p: Principal = Depends(require_roles(*MANAGERS)), db: Session = Depends(staff_db)):
    f = db.get(RequestFile, fid)
    if f is None or f.kind != "eb_bill":
        raise HTTPException(404, "Bill file not found")
    if not load_all(db)["features"].get("bill_reading_enabled", True):
        raise HTTPException(422, "Bill reading is turned off in Settings")
    try:
        result = billread.read_bill(storage.get_bytes(f.storage_key), f.content_type)
    except billread.BillReadError as exc:
        raise HTTPException(422, str(exc))
    f.extracted = result | {"read_at": utcnow().isoformat(), "confirmed": False}
    activity.log(db, "bill_read", request_id=f.request_id, user_id=p.user_id, fields=result["fields"])
    return {"id": f.id, "extracted": f.extracted}
