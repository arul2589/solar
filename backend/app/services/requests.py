"""Customer request lifecycle helpers shared by public and admin routes."""
from __future__ import annotations

import hmac
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_config
from ..models import PUBLIC_STATUS, Installer, ServiceRequest
from ..security import new_secret_token, token_hash
from . import activity
from .email import queue_email
from .settings import STATUS_MESSAGES, load_all

PUBLIC_STEPS = ["received", "under_review", "quotation_ready", "site_visit", "accepted", "installation", "completed"]


def next_reference(db: Session, installer_id: int) -> str:
    inst = db.get(Installer, installer_id)
    n = inst.next_request_number or 1
    inst.next_request_number = n + 1
    yy = datetime.now().strftime("%y")
    return f"SR{yy}-{n:05d}"


def init_status_salt(req: ServiceRequest) -> None:
    req.status_salt = new_secret_token(16)


def status_token(req: ServiceRequest) -> str:
    """Stable secret for the customer's status link, derived from a per-request salt."""
    return token_hash(f"status|{req.installer_id}|{req.reference}|{req.status_salt}")[:40]


def status_url(slug: str, reference: str, token: str) -> str:
    return f"{get_config().public_base_url}/s/{slug}/status/{reference}?t={token}"


def find_by_status_token(db: Session, reference: str, token: str) -> Optional[ServiceRequest]:
    req = db.scalar(select(ServiceRequest).where(ServiceRequest.reference == reference))
    if req is None or not hmac.compare_digest(status_token(req), token or ""):
        return None
    return req


def public_status(req: ServiceRequest) -> dict:
    current = PUBLIC_STATUS.get(req.stage, "received")
    return {
        "reference": req.reference, "status": current,
        "steps": [{"key": k, "done": PUBLIC_STEPS.index(k) <= PUBLIC_STEPS.index(current) if current in PUBLIC_STEPS else False,
                   "current": k == current} for k in PUBLIC_STEPS],
        "submitted_at": req.created_at.isoformat() if req.created_at else None,
        "site_visit_at": req.site_visit_at.isoformat() if req.site_visit_at else None,
        "closed": req.stage == "lost",
    }


def notify_status(db: Session, req: ServiceRequest, slug: str, stage: str, when: Optional[str] = None) -> None:
    """Optional customer status emails (SPEC 8.3) for site visit / installation / completed."""
    msgs = STATUS_MESSAGES.get(stage)
    cust = req.customer
    if not msgs or not cust.email:
        return
    lang = cust.preferred_language if cust.preferred_language in ("en", "ta") else "en"
    token = status_token(req)
    message = msgs[lang].format(when=f" on {when}" if when else "")
    queue_email(db, to=cust.email, template="status_update", lang=lang, request_id=req.id,
                ctx={"customer_name": cust.name, "reference": req.reference, "status_message": message,
                     "status_url": status_url(slug, req.reference, token)})
    activity.log(db, "status_email", request_id=req.id, actor="system", stage=stage)


def notify_staff(db: Session, req: ServiceRequest, event: str, message: str = "") -> None:
    to = load_all(db)["email"].get("staff_notify")
    if not to:
        return
    queue_email(db, to=to, template="staff_notification", lang="en", request_id=req.id,
                ctx={"event": event, "reference": req.reference, "customer_name": req.customer.name,
                     "message": message, "admin_url": f"{get_config().public_base_url}/admin/requests/{req.id}"})
