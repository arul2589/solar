"""Admin: request pipeline, review screen, analysis, notes, assignment, stages."""
from __future__ import annotations

import copy
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..db import tenant_session, utcnow
from ..deps import Principal, require_roles, staff_db
from ..models import (STAGES, ActivityLog, AnalysisRun, Customer, EmailLog, Installer, Quotation, RequestFile,
                      ServiceRequest, Site, SubsidyCase, User)
from ..security import MARGIN_ROLES, PRICE_ROLES, mask_email, mask_phone
from ..services import activity, storage
from ..services.analysis import OVERRIDABLE, analyse_request, preview
from ..services.requests import notify_status, status_token, status_url
from ..worker import dispatch_soon

router = APIRouter(prefix="/api/admin", tags=["admin"])

REVIEWERS = ("admin", "sales", "engineer")


def strip_prices(outputs: dict, role: str) -> dict:
    out = copy.deepcopy(outputs or {})
    if role not in PRICE_ROLES:
        out.pop("cost", None)
        out.pop("savings", None)
    elif role not in MARGIN_ROLES and out.get("cost"):
        for line in out["cost"].get("lines", []):
            line.pop("cost_price", None)
        out["cost"]["totals"].pop("cost_total", None)
        out["cost"]["totals"].pop("margin", None)
    return out


def request_row(r: ServiceRequest, latest: Optional[AnalysisRun] = None) -> dict:
    o = (latest.outputs if latest else {}) or {}
    sizing = o.get("sizing") or {}
    return {
        "id": r.id, "reference": r.reference, "stage": r.stage, "created_at": r.created_at.isoformat(),
        "customer_name": r.customer.name, "phone_masked": mask_phone(r.customer.phone),
        "district": r.site.district, "site_type": r.site.site_type, "phase": r.site.phase, "goal": r.goal,
        "owner_user_id": r.owner_user_id, "engineer_user_id": r.engineer_user_id,
        "kw": sizing.get("dc_kwp"), "panels": sizing.get("panel_count"),
        "warnings": len([w for w in o.get("warnings", []) if w.get("severity") != "info"]),
        "site_visit_at": r.site_visit_at.isoformat() if r.site_visit_at else None,
    }


@router.get("/requests")
def list_requests(stage: Optional[str] = None, owner: Optional[int] = None, district: Optional[str] = None,
                  kw_min: Optional[float] = None, kw_max: Optional[float] = None,
                  date_from: Optional[str] = None, date_to: Optional[str] = None, q: Optional[str] = None,
                  p: Principal = Depends(require_roles(*REVIEWERS)), db: Session = Depends(staff_db)):
    stmt = select(ServiceRequest).join(Customer, ServiceRequest.customer_id == Customer.id) \
        .join(Site, ServiceRequest.site_id == Site.id).order_by(ServiceRequest.id.desc())
    if stage:
        stmt = stmt.where(ServiceRequest.stage.in_(stage.split(",")))
    if owner:
        stmt = stmt.where(or_(ServiceRequest.owner_user_id == owner, ServiceRequest.engineer_user_id == owner))
    if district:
        stmt = stmt.where(func.lower(Site.district).like(f"%{district.lower()}%"))
    if date_from:
        stmt = stmt.where(ServiceRequest.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        stmt = stmt.where(ServiceRequest.created_at <= datetime.fromisoformat(date_to + "T23:59:59"))
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(ServiceRequest.reference).like(like), func.lower(Customer.name).like(like),
                              Customer.phone.like(f"%{q}%")))
    reqs = db.scalars(stmt.limit(500)).unique().all()
    ids = [r.latest_analysis_id for r in reqs if r.latest_analysis_id]
    runs = {a.id: a for a in db.scalars(select(AnalysisRun).where(AnalysisRun.id.in_(ids)))} if ids else {}
    rows = [request_row(r, runs.get(r.latest_analysis_id)) for r in reqs]
    if kw_min is not None:
        rows = [x for x in rows if x["kw"] is not None and x["kw"] >= kw_min]
    if kw_max is not None:
        rows = [x for x in rows if x["kw"] is not None and x["kw"] <= kw_max]
    return {"stages": STAGES, "items": rows}


def _file_out(f: RequestFile) -> dict:
    return {"id": f.id, "kind": f.kind, "content_type": f.content_type, "size": f.size,
            "url": storage.signed_url(f.storage_key), "extracted": f.extracted,
            "created_at": f.created_at.isoformat(), "uploaded_by": f.uploaded_by}


@router.get("/requests/{rid}")
def get_request(rid: int, p: Principal = Depends(require_roles(*REVIEWERS)), db: Session = Depends(staff_db)):
    r = db.get(ServiceRequest, rid)
    if r is None:
        raise HTTPException(404, "Request not found")
    latest = db.get(AnalysisRun, r.latest_analysis_id) if r.latest_analysis_id else None
    files = db.scalars(select(RequestFile).where(RequestFile.request_id == rid).order_by(RequestFile.id)).all()
    run_meta = [{"id": a.id, "created_at": a.created_at.isoformat(), "trigger": a.trigger, "created_by": a.created_by}
                for a in db.scalars(select(AnalysisRun).where(AnalysisRun.request_id == rid)
                                    .order_by(AnalysisRun.id.desc()))]
    quotes = db.scalars(select(Quotation).where(Quotation.request_id == rid).order_by(Quotation.id.desc())).all()
    c, s = r.customer, r.site
    inst = db.get(Installer, r.installer_id)
    return {
        "request": request_row(r, latest) | {
            "monthly_units": r.monthly_units and float(r.monthly_units),
            "monthly_bill": r.monthly_bill and float(r.monthly_bill), "budget_range": r.budget_range,
            "backup_load_w": r.backup_load_w and float(r.backup_load_w), "overrides": r.overrides or {},
            "lost_reason": r.lost_reason,
            "status_url": status_url(inst.slug, r.reference, status_token(r)),
        },
        "customer": {"id": c.id, "name": c.name, "phone": c.phone, "email": c.email,
                     "language": c.preferred_language, "phone_verified": c.phone_verified,
                     "consent_at": c.consent_at.isoformat() if c.consent_at else None},
        "site": {"address": s.address, "pincode": s.pincode, "district": s.district, "site_type": s.site_type,
                 "eb_consumer_no": s.eb_consumer_no, "tariff": s.tariff, "phase": s.phase,
                 "sanction_load_kw": s.sanction_load_kw and float(s.sanction_load_kw), "roof_type": s.roof_type,
                 "roof_area_m2": s.roof_area_m2 and float(s.roof_area_m2),
                 "roof_length_m": s.roof_length_m and float(s.roof_length_m),
                 "roof_width_m": s.roof_width_m and float(s.roof_width_m),
                 "direction": s.direction, "shade": s.shade, "floors": s.floors},
        "files": [_file_out(f) for f in files],
        "analysis": None if latest is None else {
            "id": latest.id, "created_at": latest.created_at.isoformat(), "inputs": latest.inputs,
            "outputs": strip_prices(latest.outputs, p.role), "engine_version": latest.engine_version},
        "analysis_runs": run_meta,
        "quotations": [{"id": q.id, "number": q.number, "status": q.status, "grand_total": str(q.grand_total)
                        if p.role in PRICE_ROLES else None, "created_at": q.created_at.isoformat(),
                        "sent_at": q.sent_at.isoformat() if q.sent_at else None} for q in quotes],
        "overridable": sorted(OVERRIDABLE),
    }


class RequestPatch(BaseModel):
    stage: Optional[str] = None
    owner_user_id: Optional[int] = None
    engineer_user_id: Optional[int] = None
    site_visit_at: Optional[datetime] = None
    lost_reason: Optional[str] = None
    overrides: Optional[dict[str, Any]] = None
    notify_customer: bool = True


@router.patch("/requests/{rid}")
def patch_request(rid: int, body: RequestPatch, background: BackgroundTasks,
                  p: Principal = Depends(require_roles(*REVIEWERS)), db: Session = Depends(staff_db)):
    r = db.get(ServiceRequest, rid)
    if r is None:
        raise HTTPException(404, "Request not found")
    changes = {}
    inst = db.get(Installer, r.installer_id)
    if body.overrides is not None:
        clean = {k: v for k, v in body.overrides.items() if k in OVERRIDABLE}
        changes["overrides"] = {"from": r.overrides, "to": clean}
        r.overrides = clean
    for field in ("owner_user_id", "engineer_user_id"):
        val = getattr(body, field)
        if val is not None:
            if val and db.get(User, val) is None:
                raise HTTPException(422, "User not found")
            changes[field] = {"from": getattr(r, field), "to": val or None}
            setattr(r, field, val or None)
    if body.site_visit_at is not None:
        changes["site_visit_at"] = {"from": r.site_visit_at and r.site_visit_at.isoformat(),
                                    "to": body.site_visit_at.isoformat()}
        r.site_visit_at = body.site_visit_at
        if r.stage in ("new", "analysed", "quoted"):
            body.stage = body.stage or "site_visit"
    if body.lost_reason is not None:
        r.lost_reason = body.lost_reason
    if body.stage and body.stage != r.stage:
        if body.stage not in STAGES:
            raise HTTPException(422, "Unknown stage")
        changes["stage"] = {"from": r.stage, "to": body.stage}
        r.stage = body.stage
        if body.notify_customer:
            when = r.site_visit_at.strftime("%d %b %Y %H:%M") if (body.stage == "site_visit" and r.site_visit_at) else None
            notify_status(db, r, inst.slug, body.stage, when)
    activity.log(db, "request_updated", request_id=r.id, user_id=p.user_id, changes=changes)
    if body.overrides is not None:
        db.flush()
        analyse_request(db, r, trigger="edit", user_id=p.user_id)
    db.commit()
    dispatch_soon(background, p.installer_id)
    return get_request(rid, p, db)


class PreviewIn(BaseModel):
    overrides: dict[str, Any] = {}


@router.post("/requests/{rid}/preview")
def preview_analysis(rid: int, body: PreviewIn, p: Principal = Depends(require_roles(*REVIEWERS)),
                     db: Session = Depends(staff_db)):
    r = db.get(ServiceRequest, rid)
    if r is None:
        raise HTTPException(404, "Request not found")
    merged = dict(r.overrides or {}) | body.overrides
    res = preview(db, r, merged)
    res["outputs"] = strip_prices(res["outputs"], p.role)
    return res


@router.post("/analyse")
def standalone_analysis(body: PreviewIn, p: Principal = Depends(require_roles(*REVIEWERS)),
                        db: Session = Depends(staff_db)):
    """Calculator without a request (walk-in enquiries, phone calls)."""
    res = preview(db, None, body.overrides)
    res["outputs"] = strip_prices(res["outputs"], p.role)
    return res


@router.post("/requests/{rid}/analyse")
def rerun_analysis(rid: int, p: Principal = Depends(require_roles(*REVIEWERS)), db: Session = Depends(staff_db)):
    r = db.get(ServiceRequest, rid)
    if r is None:
        raise HTTPException(404, "Request not found")
    run = analyse_request(db, r, trigger="manual", user_id=p.user_id)
    activity.log(db, "analysis_run", request_id=r.id, user_id=p.user_id, analysis_id=run.id)
    db.commit()
    return get_request(rid, p, db)


@router.get("/analysis/{aid}")
def get_analysis(aid: int, p: Principal = Depends(require_roles(*REVIEWERS)), db: Session = Depends(staff_db)):
    a = db.get(AnalysisRun, aid)
    if a is None:
        raise HTTPException(404)
    return {"id": a.id, "request_id": a.request_id, "created_at": a.created_at.isoformat(), "trigger": a.trigger,
            "engine_version": a.engine_version, "inputs": a.inputs, "settings_snapshot": a.settings_snapshot,
            "outputs": strip_prices(a.outputs, p.role)}


class NoteIn(BaseModel):
    text: str


@router.post("/requests/{rid}/notes")
def add_note(rid: int, body: NoteIn, p: Principal = Depends(require_roles(*REVIEWERS)), db: Session = Depends(staff_db)):
    if db.get(ServiceRequest, rid) is None:
        raise HTTPException(404)
    activity.log(db, "note", request_id=rid, user_id=p.user_id, text=body.text[:4000])
    return {"ok": True}


@router.get("/requests/{rid}/activity")
def request_activity(rid: int, p: Principal = Depends(require_roles(*REVIEWERS)), db: Session = Depends(staff_db)):
    users = {u.id: u.name for u in db.scalars(select(User))}
    rows = db.scalars(select(ActivityLog).where(ActivityLog.request_id == rid).order_by(ActivityLog.id.desc())).all()
    emails = db.scalars(select(EmailLog).where(EmailLog.request_id == rid).order_by(EmailLog.id.desc())).all()
    return {
        "activity": [{"id": a.id, "action": a.action, "actor": a.actor, "user": users.get(a.user_id),
                      "detail": a.detail, "created_at": a.created_at.isoformat()} for a in rows],
        "emails": [{"id": e.id, "template": e.template, "to": mask_email(e.to_address), "status": e.status,
                    "attempts": e.attempts, "provider_id": e.provider_id, "created_at": e.created_at.isoformat(),
                    "sent_at": e.sent_at.isoformat() if e.sent_at else None, "error": e.error} for e in emails],
    }


@router.post("/requests/{rid}/files")
async def upload_staff_file(rid: int, kind: str = "site_photo", file: UploadFile = File(...),
                            p: Principal = Depends(require_roles(*REVIEWERS, "technician")),
                            db: Session = Depends(staff_db)):
    if db.get(ServiceRequest, rid) is None:
        raise HTTPException(404)
    if kind not in ("eb_bill", "roof_photo", "site_photo"):
        raise HTTPException(422, "Bad kind")
    raw = await file.read()
    try:
        key, ctype, size = storage.save_upload(p.installer_id, raw, allow_pdf=(kind == "eb_bill"))
    except storage.UploadError as exc:
        raise HTTPException(422, str(exc))
    f = RequestFile(request_id=rid, kind=kind, storage_key=key, content_type=ctype, size=size, uploaded_by="staff")
    db.add(f)
    db.flush()
    activity.log(db, "file_uploaded", request_id=rid, user_id=p.user_id, kind=kind)
    return _file_out(f)


@router.post("/requests/{rid}/anonymise")
def anonymise(rid: int, p: Principal = Depends(require_roles("admin")), db: Session = Depends(staff_db)):
    """Delete-on-request: remove the customer's personal data, keep anonymous figures."""
    r = db.get(ServiceRequest, rid)
    if r is None:
        raise HTTPException(404)
    c, s = r.customer, r.site
    c.name, c.phone, c.email, c.deleted_at = "Deleted customer", f"deleted-{c.id}", None, utcnow()
    s.address, s.eb_consumer_no, s.pincode = "", None, None
    for f in db.scalars(select(RequestFile).where(RequestFile.request_id == rid)):
        storage.delete(f.storage_key)
        db.delete(f)
    for e in db.scalars(select(EmailLog).where(EmailLog.request_id == rid)):
        e.to_address, e.body_html, e.body_text = "deleted", "", ""
    activity.log(db, "customer_data_deleted", request_id=rid, user_id=p.user_id)
    return {"ok": True}


@router.get("/dashboard")
def dashboard(p: Principal = Depends(require_roles(*REVIEWERS)), db: Session = Depends(staff_db)):
    counts = dict(db.execute(select(ServiceRequest.stage, func.count()).group_by(ServiceRequest.stage)).all())
    return {"by_stage": {s: counts.get(s, 0) for s in STAGES},
            "emails_failed": db.scalar(select(func.count()).select_from(EmailLog)
                                       .where(EmailLog.status.in_(["failed", "dead"])))}


@router.get("/subsidy/{rid}")
def subsidy_placeholder(rid: int, p: Principal = Depends(require_roles(*REVIEWERS)), db: Session = Depends(staff_db)):
    """Placeholder only; PM Surya Ghar workflow comes in Phase 4."""
    case = db.scalar(select(SubsidyCase).where(SubsidyCase.request_id == rid))
    return {"status": case.status if case else "not_started", "note": "Subsidy workflow is not built yet (Phase 4)."}
