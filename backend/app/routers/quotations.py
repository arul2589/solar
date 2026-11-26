"""Quotation builder (staff) and quotation view / accept / question (customer)."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_config
from ..deps import Principal, public_db, require_roles, staff_db
from ..models import AnalysisRun, Installer, Quotation, ServiceRequest
from ..security import MARGIN_ROLES
from ..services import quotations as qs
from ..services import storage
from ..services.requests import find_by_status_token
from ..worker import dispatch_soon

router = APIRouter(prefix="/api/admin", tags=["quotations"])
public_router = APIRouter(prefix="/api/public/{slug}", tags=["public-quotations"])

QUOTERS = ("admin", "sales")
VIEWERS = ("admin", "sales", "engineer")


def q_out(q: Quotation, role: str) -> dict:
    margin = role in MARGIN_ROLES
    return {
        "id": q.id, "number": q.number, "status": q.status, "request_id": q.request_id,
        "analysis_run_id": q.analysis_run_id, "quote_date": q.quote_date.isoformat(),
        "valid_until": q.valid_until.isoformat(), "system_summary": q.system_summary, "terms_text": q.terms_text,
        "warranty_text": q.warranty_text, "scope_text": q.scope_text, "notes": q.notes,
        "subtotal": str(q.subtotal), "tax": str(q.tax), "grand_total": str(q.grand_total),
        "cost_total": str(q.cost_total) if (margin and q.cost_total is not None) else None,
        "margin": str(q.subtotal - q.cost_total) if (margin and q.cost_total is not None) else None,
        "subsidy_amount": None if q.subsidy_amount is None else str(q.subsidy_amount),
        "sent_at": q.sent_at.isoformat() if q.sent_at else None,
        "accepted_at": q.accepted_at.isoformat() if q.accepted_at else None,
        "in_words": qs.rupees_in_words(q.grand_total),
        "lines": [{"id": l.id, "code": l.code, "description": l.description, "details": l.details, "hsn": l.hsn,
                   "qty": str(l.qty), "unit": l.unit, "unit_price": str(l.unit_price), "gst_pct": str(l.gst_pct),
                   "amount": str(l.amount), "tax": str(l.tax), "total": str(l.total),
                   "cost_price": (None if l.cost_price is None else str(l.cost_price)) if margin else None}
                  for l in q.lines],
    }


@router.post("/requests/{rid}/quotations")
def create_quotation(rid: int, p: Principal = Depends(require_roles(*QUOTERS)), db: Session = Depends(staff_db)):
    req = db.get(ServiceRequest, rid)
    if req is None:
        raise HTTPException(404, "Request not found")
    try:
        q = qs.create_draft(db, req, p.user_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    return q_out(q, p.role)


@router.get("/quotations/{qid}")
def get_quotation(qid: int, p: Principal = Depends(require_roles(*VIEWERS)), db: Session = Depends(staff_db)):
    q = db.get(Quotation, qid)
    if q is None:
        raise HTTPException(404)
    req = db.get(ServiceRequest, q.request_id)
    out = q_out(q, p.role)
    out["request"] = {"id": req.id, "reference": req.reference, "customer_name": req.customer.name,
                      "customer_email": req.customer.email,
                      "customer_whatsapp": req.customer.whatsapp, "contact_pref": req.customer.contact_pref or "email",
                      "stage": req.stage}
    return out


class LineIn(BaseModel):
    code: str = ""
    description: str = Field(min_length=1)
    details: str = ""
    hsn: str = ""
    qty: float = Field(gt=0)
    unit: str = "No"
    unit_price: float = Field(ge=0)
    gst_pct: float = Field(ge=0, le=28)
    cost_price: Optional[float] = None


class QuoteIn(BaseModel):
    lines: Optional[list[LineIn]] = None
    terms_text: Optional[str] = None
    warranty_text: Optional[str] = None
    scope_text: Optional[str] = None
    notes: Optional[str] = None
    system_summary: Optional[str] = None
    valid_until: Optional[str] = None
    subsidy_amount: Optional[Any] = None


@router.put("/quotations/{qid}")
def update_quotation(qid: int, body: QuoteIn, p: Principal = Depends(require_roles(*QUOTERS)),
                     db: Session = Depends(staff_db)):
    q = db.get(Quotation, qid)
    if q is None:
        raise HTTPException(404)
    data = body.model_dump(exclude_unset=True)
    if body.lines is not None:
        data["lines"] = [l.model_dump() for l in body.lines]
    try:
        qs.update_draft(db, q, data, p.user_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    return q_out(q, p.role)


@router.post("/quotations/{qid}/revise")
def revise_quotation(qid: int, p: Principal = Depends(require_roles(*QUOTERS)), db: Session = Depends(staff_db)):
    q = db.get(Quotation, qid)
    if q is None:
        raise HTTPException(404)
    return q_out(qs.revise(db, q, p.user_id), p.role)


@router.get("/quotations/{qid}/pdf")
def quotation_pdf(qid: int, internal: bool = False, p: Principal = Depends(require_roles(*VIEWERS)),
                  db: Session = Depends(staff_db)):
    q = db.get(Quotation, qid)
    if q is None:
        raise HTTPException(404)
    if internal and p.role not in MARGIN_ROLES:
        raise HTTPException(403, "Internal estimate is for Admin/Sales only")
    data = qs.pdf_bytes(db, q, internal=internal)
    name = f"{'estimate' if internal else 'quotation'}-{q.number}.pdf"
    return Response(data, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{name}"'})


class SendIn(BaseModel):
    skip_review_reason: Optional[str] = Field(default=None, max_length=1000)


@router.post("/quotations/{qid}/send")
def send_quotation(qid: int, background: BackgroundTasks, body: Optional[SendIn] = None,
                   p: Principal = Depends(require_roles(*QUOTERS)), db: Session = Depends(staff_db)):
    from ..services import kb
    q = db.get(Quotation, qid)
    if q is None:
        raise HTTPException(404)
    # design check against the knowledge base must be done (and conflicts acknowledged) before sending
    gate = kb.send_gate(db, q.analysis_run_id)
    if gate:
        reason = (body.skip_review_reason or "").strip() if body else ""
        if p.role == "admin" and len(reason) >= 5:
            activity.log(db, "design_review_skipped", request_id=q.request_id, quotation_id=q.id, user_id=p.user_id,
                         reason=reason, gate=gate["code"])
        else:
            raise HTTPException(409, gate)
    try:
        token = qs.send(db, q, p.user_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    db.commit()
    dispatch_soon(background, p.installer_id)
    inst = db.get(Installer, q.installer_id)
    out = q_out(q, p.role)
    cust = db.get(ServiceRequest, q.request_id).customer
    pref = cust.contact_pref or "email"
    wants_email = pref in ("email", "both") or not cust.whatsapp
    out["email_status"] = ("queued" if wants_email else "not_requested") if cust.email else "no_email"
    out["customer_url"] = qs.quote_url(inst.slug, token)   # staff can also share it by WhatsApp/phone
    # free WhatsApp delivery: a click-to-chat link staff open in their own WhatsApp (see services/whatsapp.py)
    from ..services import settings as settings_svc
    from ..services.whatsapp import quotation_link
    wa_target = cust.whatsapp if (pref in ("whatsapp", "both") or not cust.email) else None
    company = settings_svc.load_all(db)["company"].get("name") or inst.name
    out["contact_pref"] = pref
    out["whatsapp"] = quotation_link(number=wa_target, customer_name=cust.name, company=company,
                                     quote_number=q.number, url=out["customer_url"],
                                     lang=cust.preferred_language or "en") if wa_target else None
    if get_config().is_dev:
        out["dev_quote_url"] = out["customer_url"]
    return out


@router.get("/analysis/{aid}/diagram/{kind}")
def diagram(aid: int, kind: str, p: Principal = Depends(require_roles(*VIEWERS, "technician", "normal")),
            db: Session = Depends(staff_db)):
    run = db.get(AnalysisRun, aid)
    if run is None:
        raise HTTPException(404)
    try:
        return {"kind": kind, "svg": qs.diagram_svg(db, run, kind)}
    except KeyError:
        raise HTTPException(404, "Unknown diagram")


# ------------------------------------------------------------------ customer side
def _resolve(db: Session, token: str) -> Quotation:
    q = qs.find_by_token(db, token)
    if q is None or q.status not in ("sent", "accepted", "superseded"):
        raise HTTPException(404, "Quotation not found")
    return q


def _resolve_by_status(db: Session, reference: str, t: str) -> Quotation:
    req = find_by_status_token(db, reference, t)
    q = qs.latest_sent_quotation(db, req.id) if req else None
    if q is None:
        raise HTTPException(404, "Quotation not found")
    return q


@public_router.get("/quotations/{token}")
def view_quotation(token: str, db: Session = Depends(public_db)):
    return qs.public_view(db, _resolve(db, token))


@public_router.get("/requests/{reference}/quotation")
def view_quotation_by_status(reference: str, t: str, db: Session = Depends(public_db)):
    return qs.public_view(db, _resolve_by_status(db, reference, t))


def _pdf_response(db: Session, q: Quotation) -> Response:
    data = storage.get_bytes(q.pdf_key) if q.pdf_key else qs.pdf_bytes(db, q)
    return Response(data, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="quotation-{q.number}.pdf"'})


@public_router.get("/quotations/{token}/pdf")
def quotation_pdf_public(token: str, db: Session = Depends(public_db)):
    return _pdf_response(db, _resolve(db, token))


@public_router.get("/requests/{reference}/quotation/pdf")
def quotation_pdf_by_status(reference: str, t: str, db: Session = Depends(public_db)):
    return _pdf_response(db, _resolve_by_status(db, reference, t))


def _accept(db: Session, q: Quotation, background: BackgroundTasks) -> dict:
    try:
        qs.accept(db, q)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    db.commit()
    dispatch_soon(background, q.installer_id)
    return {"status": q.status, "accepted_at": q.accepted_at.isoformat()}


@public_router.post("/quotations/{token}/accept")
def accept_quotation(token: str, background: BackgroundTasks, db: Session = Depends(public_db)):
    return _accept(db, _resolve(db, token), background)


@public_router.post("/requests/{reference}/quotation/accept")
def accept_by_status(reference: str, t: str, background: BackgroundTasks, db: Session = Depends(public_db)):
    return _accept(db, _resolve_by_status(db, reference, t), background)


class QuestionIn(BaseModel):
    message: str = Field(min_length=2, max_length=2000)


@public_router.post("/quotations/{token}/question")
def question(token: str, body: QuestionIn, background: BackgroundTasks, db: Session = Depends(public_db)):
    q = _resolve(db, token)
    qs.ask_question(db, q, body.message)
    db.commit()
    dispatch_soon(background, q.installer_id)
    return {"ok": True}


@public_router.post("/requests/{reference}/quotation/question")
def question_by_status(reference: str, t: str, body: QuestionIn, background: BackgroundTasks,
                       db: Session = Depends(public_db)):
    q = _resolve_by_status(db, reference, t)
    qs.ask_question(db, q, body.message)
    db.commit()
    dispatch_soon(background, q.installer_id)
    return {"ok": True}
