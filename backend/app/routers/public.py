"""Public (customer-facing) API. No prices are ever returned here except a quotation
that staff have explicitly sent."""
from __future__ import annotations

import json
from datetime import timedelta
from typing import List, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, EmailStr, Field, ValidationError, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_config
from ..db import utcnow
from ..deps import Principal, customer_db, get_customer, public_db
from ..models import Customer, RequestFile, ServiceRequest, Site
from ..ratelimit import allow
from ..security import create_token, decode_token, mask_phone, new_secret_token, normalise_phone, token_hash
from ..services import activity, otp, storage
from ..services.analysis import analyse_request
from ..services.email import queue_email
from ..services.requests import (find_by_status_token, init_status_salt, next_reference, notify_staff, public_status,
                                 status_token, status_url)
from ..services.settings import load_all
from ..worker import dispatch_soon

router = APIRouter(prefix="/api/public/{slug}", tags=["public"])


@router.get("")
def installer_info(db: Session = Depends(public_db)):
    s = load_all(db)
    inst = db.info["installer"]
    c = s["company"]
    return {"slug": inst.slug, "name": c.get("name") or inst.name, "phone": c.get("phone"), "email": c.get("email"),
            "address": c.get("address"), "logo_url": f"/api/public/{inst.slug}/logo" if c.get("logo_file_id") else None,
            "languages": s["features"].get("languages", ["en", "ta"]),
            "require_phone_otp": bool(s["features"].get("require_phone_otp")),
            "disclaimer_en": s["quotation"]["disclaimer_en"], "disclaimer_ta": s["quotation"]["disclaimer_ta"]}


@router.get("/logo")
def logo(db: Session = Depends(public_db)):
    from fastapi.responses import Response
    fid = load_all(db)["company"].get("logo_file_id")
    f = db.get(RequestFile, fid) if fid else None
    if not f:
        raise HTTPException(404)
    return Response(storage.get_bytes(f.storage_key), media_type=f.content_type,
                    headers={"Cache-Control": "public, max-age=3600"})


# ------------------------------------------------------------------ phone OTP
class OtpRequestIn(BaseModel):
    phone: str
    purpose: Literal["verify", "login"] = "verify"


@router.post("/otp/request")
def otp_request(body: OtpRequestIn, request: Request, db: Session = Depends(public_db)):
    phone = normalise_phone(body.phone)
    if len(phone) != 10:
        raise HTTPException(422, "Enter a 10-digit mobile number")
    ip = request.client.host if request.client else "?"
    if not allow(f"otp:{ip}", 10) or not allow(f"otp:{phone}", 5):
        raise HTTPException(429, "Too many attempts. Try again later.")
    if body.purpose == "login":
        exists = db.scalar(select(Customer.id).where(Customer.phone == phone, Customer.deleted_at.is_(None)))
        if not exists:
            # do not reveal whether the number is registered
            return {"sent": True}
    code = otp.issue(db, "phone", phone, body.purpose)
    out = {"sent": True, "to": mask_phone(phone)}
    if get_config().is_dev and get_config().sms_provider == "log":
        out["dev_code"] = code
    return out


class OtpVerifyIn(BaseModel):
    phone: str
    code: str


@router.post("/otp/verify")
def otp_verify(body: OtpVerifyIn, db: Session = Depends(public_db)):
    phone = normalise_phone(body.phone)
    if not otp.verify(db, "phone", phone, "verify", body.code):
        db.commit()
        raise HTTPException(400, "Wrong or expired code")
    inst = db.info["installer"]
    return {"phone_token": create_token({"typ": "phone", "iid": inst.id, "phone": phone}, minutes=60)}


# ------------------------------------------------------------------ request form
class RequestIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    phone: str
    email: Optional[EmailStr] = None
    whatsapp: Optional[str] = Field(default=None, max_length=20)
    contact_pref: Literal["email", "whatsapp", "both"] = "email"
    language: Literal["en", "ta"] = "en"
    address: str = Field(min_length=3, max_length=1000)
    pincode: Optional[str] = Field(default=None, max_length=10)
    district: Optional[str] = Field(default=None, max_length=100)
    site_type: Literal["home", "commercial", "industry"] = "home"
    eb_consumer_no: Optional[str] = Field(default=None, max_length=40)
    tariff: Optional[str] = Field(default=None, max_length=20)
    phase: Literal[1, 3] = 1
    sanction_load_kw: Optional[float] = Field(default=None, ge=0, le=10000)
    monthly_units: Optional[float] = Field(default=None, ge=0, le=10_000_000)
    monthly_bill: Optional[float] = Field(default=None, ge=0, le=100_000_000)
    roof_type: Literal["rcc", "sheet", "tile"] = "rcc"
    roof_area: Optional[float] = Field(default=None, ge=0, le=1_000_000)
    roof_area_unit: Literal["sqft", "sqm"] = "sqft"
    roof_length_m: Optional[float] = Field(default=None, ge=0, le=1000)
    roof_width_m: Optional[float] = Field(default=None, ge=0, le=1000)
    direction: Literal["south", "south_east", "south_west", "east", "west", "north", "flat", "unknown"] = "south"
    shade: Literal["none", "some", "heavy"] = "none"
    floors: Optional[int] = Field(default=None, ge=0, le=200)
    goal: Literal["reduce_bill", "backup", "industrial"] = "reduce_bill"
    backup_load_w: Optional[float] = Field(default=None, ge=0, le=1_000_000)
    budget_range: Optional[str] = Field(default=None, max_length=40)
    consent: bool
    phone_token: Optional[str] = None
    website: Optional[str] = None          # honeypot: must stay empty

    @field_validator("whatsapp")
    @classmethod
    def _whatsapp(cls, v):
        if v in (None, ""):
            return None
        p = normalise_phone(v)
        if len(p) != 10:
            raise ValueError("Enter a 10-digit WhatsApp number")
        return p

    @field_validator("phone")
    @classmethod
    def _phone(cls, v):
        p = normalise_phone(v)
        if len(p) != 10:
            raise ValueError("Enter a 10-digit mobile number")
        return p


SQFT_TO_SQM = 0.092903


@router.post("/requests")
async def submit_request(
    request: Request, background: BackgroundTasks, slug: str,
    data: str = Form(...),
    eb_bill: Optional[UploadFile] = File(default=None),
    roof_photos: List[UploadFile] = File(default=[]),
    db: Session = Depends(public_db),
):
    cfg = get_config()
    try:
        body = RequestIn.model_validate(json.loads(data))
    except (ValidationError, ValueError) as exc:
        detail = exc.errors() if isinstance(exc, ValidationError) else "Invalid form data"
        raise HTTPException(422, json.loads(json.dumps(detail, default=str)))
    if body.website:
        # honeypot filled: pretend success, store nothing
        return {"reference": "SR00-00000", "status_token": "x"}
    ip = request.client.host if request.client else "?"
    if not allow(f"submit:{slug}:{ip}", cfg.public_rate_limit_per_hour):
        raise HTTPException(429, "Too many requests from this network. Please call us instead.")
    if not body.consent:
        raise HTTPException(422, "Consent is required")
    if not body.monthly_units and not body.monthly_bill:
        raise HTTPException(422, "Give either average monthly units or the monthly bill amount")
    if not body.email and not body.whatsapp:
        raise HTTPException(422, "Give an email address or a WhatsApp number so we can send your quotation")
    if body.contact_pref in ("email", "both") and not body.email:
        raise HTTPException(422, "Enter your email address to get the quotation by email")
    if body.contact_pref in ("whatsapp", "both") and not body.whatsapp:
        raise HTTPException(422, "Enter your WhatsApp number to get the quotation on WhatsApp")
    if len(roof_photos) > 6:
        raise HTTPException(422, "Up to 6 roof photos")

    settings = load_all(db)
    inst = db.info["installer"]
    phone_verified = False
    if body.phone_token:
        try:
            c = decode_token(body.phone_token)
            phone_verified = c.get("typ") == "phone" and c.get("iid") == inst.id and c.get("phone") == body.phone
        except Exception:  # noqa: BLE001
            phone_verified = False
    if settings["features"].get("require_phone_otp") and not phone_verified:
        raise HTTPException(422, "Please verify your phone number with the OTP")

    # read uploads before writing anything
    uploads = []
    for kind, f in [("eb_bill", eb_bill)] + [("roof_photo", p) for p in roof_photos]:
        if f is None or not f.filename:
            continue
        raw = await f.read()
        if not raw:
            continue
        try:
            key, ctype, size = storage.save_upload(inst.id, raw, allow_pdf=(kind == "eb_bill"))
        except storage.UploadError as exc:
            for k, *_ in uploads:
                storage.delete(k)
            raise HTTPException(422, f"{f.filename}: {exc}")
        uploads.append((key, ctype, size, kind))

    cust = db.scalar(select(Customer).where(Customer.phone == body.phone, Customer.deleted_at.is_(None)))
    if cust is None:
        cust = Customer(name=body.name.strip(), phone=body.phone, email=body.email, whatsapp=body.whatsapp,
                        contact_pref=body.contact_pref, preferred_language=body.language)
        db.add(cust)
    else:
        cust.name = body.name.strip()
        cust.email = body.email or cust.email
        cust.whatsapp = body.whatsapp or cust.whatsapp
        cust.contact_pref = body.contact_pref
        cust.preferred_language = body.language
    cust.consent_at = utcnow()
    cust.phone_verified = cust.phone_verified or phone_verified
    db.flush()

    area_m2 = None
    if body.roof_area:
        area_m2 = round(body.roof_area * (SQFT_TO_SQM if body.roof_area_unit == "sqft" else 1.0), 2)
    site = Site(customer_id=cust.id, address=body.address.strip(), pincode=body.pincode, district=body.district,
                site_type=body.site_type, eb_consumer_no=body.eb_consumer_no, tariff=body.tariff, phase=body.phase,
                sanction_load_kw=body.sanction_load_kw, roof_type=body.roof_type, roof_area_m2=area_m2,
                roof_length_m=body.roof_length_m, roof_width_m=body.roof_width_m, direction=body.direction,
                shade=body.shade, floors=body.floors)
    db.add(site)
    db.flush()
    req = ServiceRequest(reference=next_reference(db, inst.id), customer_id=cust.id, site_id=site.id,
                         goal=body.goal, budget_range=body.budget_range, monthly_units=body.monthly_units,
                         monthly_bill=body.monthly_bill, backup_load_w=body.backup_load_w, status_salt="",
                         overrides={})
    init_status_salt(req)
    db.add(req)
    db.flush()
    token = status_token(req)
    for key, ctype, size, kind in uploads:
        db.add(RequestFile(request_id=req.id, kind=kind, storage_key=key, content_type=ctype, size=size))
    activity.log(db, "request_submitted", request_id=req.id, actor="customer", phone=mask_phone(body.phone),
                 files=len(uploads))

    # auto-analysis on submit (staff only see it)
    db.refresh(req)
    try:
        analyse_request(db, req, trigger="submit")
    except Exception as exc:  # noqa: BLE001  analysis must never block a submission
        activity.log(db, "analysis_failed", request_id=req.id, actor="system", error=str(exc)[:300])

    if cust.email:
        queue_email(db, to=cust.email, template="acknowledgement", lang=body.language, request_id=req.id,
                    ctx={"customer_name": cust.name, "reference": req.reference,
                         "status_url": status_url(inst.slug, req.reference, token)})
    notify_staff(db, req, "New solar request", f"{site.district or ''} {body.site_type}")
    db.commit()
    dispatch_soon(background, inst.id)
    return {"reference": req.reference, "status_token": token,
            "status_url": status_url(inst.slug, req.reference, token), "email_sent": bool(cust.email)}


@router.get("/requests/{reference}")
def request_status(reference: str, t: str, db: Session = Depends(public_db)):
    req = find_by_status_token(db, reference, t)
    if req is None:
        raise HTTPException(404, "Request not found")
    out = public_status(req)
    from ..services.quotations import latest_sent_quotation
    q = latest_sent_quotation(db, req.id)
    out["quotation_available"] = q is not None
    out["quotation_number"] = q.number if q else None
    return out


# ------------------------------------------------------------------ customer login
class MagicIn(BaseModel):
    email: EmailStr


@router.post("/customer/magic-link")
def magic_link(body: MagicIn, request: Request, background: BackgroundTasks, db: Session = Depends(public_db)):
    ip = request.client.host if request.client else "?"
    if not allow(f"magic:{ip}", 10):
        raise HTTPException(429, "Too many attempts")
    inst = db.info["installer"]
    cust = db.scalar(select(Customer).where(Customer.email == str(body.email), Customer.deleted_at.is_(None))
                     .order_by(Customer.id.desc()))
    out = {"sent": True}
    if cust:
        tok = create_token({"typ": "magic", "iid": inst.id, "cid": cust.id}, minutes=30)
        url = f"{get_config().public_base_url}/s/{inst.slug}/login?magic={tok}"
        queue_email(db, to=cust.email, template="magic_link", lang=cust.preferred_language or "en",
                    ctx={"login_url": url})
        db.commit()
        dispatch_soon(background, inst.id)
        if get_config().is_dev:
            out["dev_link"] = url
    return out


class MagicExchangeIn(BaseModel):
    token: str


@router.post("/customer/session")
def magic_exchange(body: MagicExchangeIn, db: Session = Depends(public_db)):
    inst = db.info["installer"]
    try:
        c = decode_token(body.token)
    except Exception:  # noqa: BLE001
        raise HTTPException(401, "Link expired")
    if c.get("typ") != "magic" or c.get("iid") != inst.id:
        raise HTTPException(401, "Invalid link")
    cust = db.get(Customer, c["cid"])
    if cust is None or cust.deleted_at:
        raise HTTPException(401, "Invalid link")
    return {"token": create_token({"typ": "customer", "iid": inst.id, "cid": cust.id, "name": cust.name},
                                  minutes=60 * 24), "name": cust.name}


class OtpLoginIn(BaseModel):
    phone: str
    code: str


@router.post("/customer/otp-login")
def otp_login(body: OtpLoginIn, db: Session = Depends(public_db)):
    phone = normalise_phone(body.phone)
    inst = db.info["installer"]
    if not otp.verify(db, "phone", phone, "login", body.code):
        db.commit()
        raise HTTPException(400, "Wrong or expired code")
    cust = db.scalar(select(Customer).where(Customer.phone == phone, Customer.deleted_at.is_(None)))
    if cust is None:
        raise HTTPException(400, "Wrong or expired code")
    cust.phone_verified = True
    return {"token": create_token({"typ": "customer", "iid": inst.id, "cid": cust.id, "name": cust.name},
                                  minutes=60 * 24), "name": cust.name}


# Customer-authenticated routes (installer comes from the token; slug must match)
customer_router = APIRouter(prefix="/api/customer", tags=["customer"])


@customer_router.get("/requests")
def my_requests(p: Principal = Depends(get_customer), db: Session = Depends(customer_db)):
    from ..services.quotations import latest_sent_quotation
    reqs = db.scalars(select(ServiceRequest).where(ServiceRequest.customer_id == p.customer_id)
                      .order_by(ServiceRequest.id.desc())).all()
    out = []
    for r in reqs:
        st = public_status(r)
        q = latest_sent_quotation(db, r.id)
        st |= {"id": r.id, "status_token": status_token(r), "quotation_available": q is not None, "address": r.site.address}
        out.append(st)
    return out


# ------------------------------------------------------------------ website savings calculator
class EstimateIn(BaseModel):
    monthly_bill: Optional[float] = Field(default=None, gt=0, le=100_000_000)
    monthly_units: Optional[float] = Field(default=None, gt=0, le=10_000_000)
    site_type: Literal["home", "commercial", "industry"] = "home"
    phase: Literal[1, 3] = 1
    goal: Literal["reduce_bill", "backup"] = "reduce_bill"


@router.post("/estimate")
def estimate(body: EstimateIn, request: Request, db: Session = Depends(public_db)):
    """Indicative size and savings for the public calculator. Never returns a price."""
    from ..services.analysis import run_engine
    from ..services.estimate import shape_public_estimate

    if not body.monthly_bill and not body.monthly_units:
        raise HTTPException(422, "Enter your monthly bill or monthly units")
    ip = request.client.host if request.client else "?"
    if not allow(f"estimate:{ip}", 60):
        raise HTTPException(429, "Too many attempts. Try again later.")
    category = {"home": "domestic", "commercial": "commercial", "industry": "industrial"}[body.site_type]
    out, _ = run_engine(db, {"monthly_bill": body.monthly_bill, "monthly_units": body.monthly_units,
                             "phase": body.phase, "category": category, "goal": body.goal})
    return shape_public_estimate(out)
