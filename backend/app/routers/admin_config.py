"""Admin: settings, placeholders, catalogue, price master, network rates, users, email log."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from solarcalc import CalcSettings

from ..deps import Principal, get_staff, require_roles, staff_db
from ..models import EmailLog, InverterModel, NetworkRateRow, PanelModel, PriceItem, RequestFile, User
from ..security import ROLES, hash_password, mask_email
from ..services import activity, storage
from ..services.settings import (DEFAULTS, PLACEHOLDERS, confirm_placeholder, load_all, placeholder_status,
                                 save_section)
from ..worker import dispatch_soon

router = APIRouter(prefix="/api/admin", tags=["admin-config"])

SECTIONS = ("company", "email", "calc", "tariff_slabs", "quotation", "templates", "features", "project")


# ------------------------------------------------------------------ settings
@router.get("/settings")
def get_settings(p: Principal = Depends(get_staff), db: Session = Depends(staff_db)):
    s = load_all(db)
    out = {k: s[k] for k in SECTIONS}
    if p.role not in ("admin", "platform_owner"):
        out.pop("templates", None)
    out["placeholders"] = placeholder_status(db)
    return out


@router.put("/settings/{section}")
def put_settings(section: str, body: dict[str, Any], p: Principal = Depends(require_roles("admin")),
                 db: Session = Depends(staff_db)):
    if section not in SECTIONS:
        raise HTTPException(404, "Unknown section")
    value = body.get("value", body)
    if section == "calc":
        try:
            value = CalcSettings.from_dict(value).to_dict()     # validates types / unknown keys dropped
        except (TypeError, ValueError, InvalidOperation) as exc:
            raise HTTPException(422, f"Invalid calculation settings: {exc}")
    if section == "company":
        for banned in ("bank_account_number", "account_number", "aadhaar", "pan"):
            if banned in value:
                raise HTTPException(422, "Bank account numbers and government IDs are not stored")
    if section == "tariff_slabs":
        for cat, slabs in value.items():
            for row in slabs:
                if len(row) != 2:
                    raise HTTPException(422, "Each slab is [upto_units_or_null, rate]")
                Decimal(str(row[1]))
    save_section(db, section, value)
    activity.log(db, "settings_updated", user_id=p.user_id, section=section)
    return {"ok": True, "value": load_all(db)[section]}


@router.post("/settings/reset/{section}")
def reset_settings(section: str, p: Principal = Depends(require_roles("admin")), db: Session = Depends(staff_db)):
    if section not in DEFAULTS:
        raise HTTPException(404)
    save_section(db, section, DEFAULTS[section])
    activity.log(db, "settings_reset", user_id=p.user_id, section=section)
    return {"ok": True}


class ConfirmIn(BaseModel):
    key: str
    confirmed: bool = True


@router.post("/settings/placeholders")
def confirm(body: ConfirmIn, p: Principal = Depends(require_roles("admin")), db: Session = Depends(staff_db)):
    if body.key not in PLACEHOLDERS:
        raise HTTPException(404)
    confirm_placeholder(db, body.key, body.confirmed)
    activity.log(db, "placeholder_confirmed" if body.confirmed else "placeholder_reopened", user_id=p.user_id,
                 key=body.key)
    return {"placeholders": placeholder_status(db)}


@router.post("/settings/logo")
async def upload_logo(file: UploadFile = File(...), p: Principal = Depends(require_roles("admin")),
                      db: Session = Depends(staff_db)):
    raw = await file.read()
    try:
        key, ctype, size = storage.save_upload(p.installer_id, raw)
    except storage.UploadError as exc:
        raise HTTPException(422, str(exc))
    f = RequestFile(kind="logo", storage_key=key, content_type=ctype, size=size, uploaded_by="staff")
    db.add(f)
    db.flush()
    company = load_all(db)["company"] | {"logo_file_id": f.id}
    save_section(db, "company", company)
    return {"ok": True, "logo_file_id": f.id}


# ------------------------------------------------------------------ generic catalogue CRUD
def _ser(obj) -> dict:
    out = {}
    for c in obj.__table__.columns:
        v = getattr(obj, c.name)
        if isinstance(v, Decimal):
            v = str(v)
        elif isinstance(v, date):
            v = v.isoformat()
        out[c.name] = v
    out.pop("installer_id", None)
    return out


def _apply(obj, data: dict, model) -> None:
    cols = {c.name: c for c in model.__table__.columns}
    for k, v in data.items():
        if k in ("id", "installer_id") or k not in cols:
            continue
        if v == "":
            v = None
        setattr(obj, k, v)


def crud(path: str, model, *, write_roles=("admin",), read_roles=("admin", "sales", "engineer"),
         order=None, price_fields=()):
    @router.get(f"/{path}", name=f"list_{path}")
    def _list(p: Principal = Depends(require_roles(*read_roles)), db: Session = Depends(staff_db)):
        rows = db.scalars(select(model).order_by(*(order or [model.id]))).all()
        return [_ser(r) for r in rows]

    @router.post(f"/{path}", name=f"create_{path}")
    def _create(body: dict[str, Any], p: Principal = Depends(require_roles(*write_roles)),
                db: Session = Depends(staff_db)):
        obj = model()
        _apply(obj, body, model)
        db.add(obj)
        try:
            db.flush()
        except IntegrityError:
            raise HTTPException(409, "Duplicate entry")
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(422, f"Invalid data: {exc.__class__.__name__}")
        activity.log(db, f"{path}_created", user_id=p.user_id, id=obj.id)
        return _ser(obj)

    @router.put(f"/{path}/{{oid}}", name=f"update_{path}")
    def _update(oid: int, body: dict[str, Any], p: Principal = Depends(require_roles(*write_roles)),
                db: Session = Depends(staff_db)):
        obj = db.get(model, oid)
        if obj is None:
            raise HTTPException(404)
        before = _ser(obj)
        _apply(obj, body, model)
        try:
            db.flush()
        except IntegrityError:
            raise HTTPException(409, "Duplicate entry")
        after = _ser(obj)
        diff = {k: {"from": before[k], "to": after[k]} for k in after if before.get(k) != after[k]}
        activity.log(db, f"{path}_updated", user_id=p.user_id, id=oid, changes=diff)
        return after

    @router.delete(f"/{path}/{{oid}}", name=f"delete_{path}")
    def _delete(oid: int, p: Principal = Depends(require_roles(*write_roles)), db: Session = Depends(staff_db)):
        obj = db.get(model, oid)
        if obj is None:
            raise HTTPException(404)
        if hasattr(obj, "active"):
            obj.active = False          # soft delete keeps old analyses explainable
        else:
            db.delete(obj)
        activity.log(db, f"{path}_deleted", user_id=p.user_id, id=oid)
        return {"ok": True}


crud("panels", PanelModel)
crud("inverters", InverterModel)
crud("price-items", PriceItem, order=[PriceItem.sort_order, PriceItem.code])
crud("network-rates", NetworkRateRow, order=[NetworkRateRow.effective_from])


# ------------------------------------------------------------------ users
class UserIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1)
    role: str
    phone: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8)
    active: bool = True


def _user_out(u: User) -> dict:
    return {"id": u.id, "email": u.email, "name": u.name, "role": u.role, "phone": u.phone, "active": u.active,
            "two_factor": bool(u.totp_secret)}


@router.get("/users")
def list_users(p: Principal = Depends(get_staff), db: Session = Depends(staff_db)):
    return [_user_out(u) for u in db.scalars(select(User).order_by(User.id))]


@router.post("/users")
def create_user(body: UserIn, p: Principal = Depends(require_roles("admin")), db: Session = Depends(staff_db)):
    if body.role not in ROLES or body.role == "platform_owner":
        raise HTTPException(422, "Bad role")
    if not body.password:
        raise HTTPException(422, "Password required (min 8 characters)")
    if db.scalar(select(User).where(User.email == body.email.lower())):
        raise HTTPException(409, "Email already used")
    u = User(email=body.email.lower(), name=body.name, role=body.role, phone=body.phone, active=body.active,
             password_hash=hash_password(body.password))
    db.add(u)
    db.flush()
    activity.log(db, "user_created", user_id=p.user_id, target=u.id, role=u.role)
    return _user_out(u)


@router.put("/users/{uid}")
def update_user(uid: int, body: UserIn, p: Principal = Depends(require_roles("admin")), db: Session = Depends(staff_db)):
    u = db.get(User, uid)
    if u is None:
        raise HTTPException(404)
    if body.role not in ROLES or body.role == "platform_owner":
        raise HTTPException(422, "Bad role")
    if uid == p.user_id and (body.role != "admin" or not body.active):
        raise HTTPException(422, "You cannot remove your own admin access")
    u.email, u.name, u.role, u.phone, u.active = body.email.lower(), body.name, body.role, body.phone, body.active
    if body.password:
        u.password_hash = hash_password(body.password)
    activity.log(db, "user_updated", user_id=p.user_id, target=u.id, role=u.role, active=u.active)
    return _user_out(u)


# ------------------------------------------------------------------ email log
@router.get("/emails")
def email_log(p: Principal = Depends(require_roles("admin", "sales")), db: Session = Depends(staff_db)):
    rows = db.scalars(select(EmailLog).order_by(EmailLog.id.desc()).limit(300)).all()
    return [{"id": e.id, "request_id": e.request_id, "to": mask_email(e.to_address), "template": e.template,
             "language": e.language, "subject": e.subject, "status": e.status, "attempts": e.attempts,
             "provider": e.provider, "provider_id": e.provider_id, "error": e.error,
             "created_at": e.created_at.isoformat(), "sent_at": e.sent_at.isoformat() if e.sent_at else None}
            for e in rows]


@router.post("/emails/{eid}/retry")
def retry_email(eid: int, background: BackgroundTasks, p: Principal = Depends(require_roles("admin", "sales")),
                db: Session = Depends(staff_db)):
    e = db.get(EmailLog, eid)
    if e is None:
        raise HTTPException(404)
    e.status, e.next_attempt_at = "queued", None
    db.commit()
    dispatch_soon(background, p.installer_id)
    return {"ok": True}
