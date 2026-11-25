from __future__ import annotations

from typing import Optional

import pyotp
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from ..db import tenant_session
from ..deps import Principal, get_staff, staff_db
from ..models import Installer, User
from ..security import create_token, verify_password
from ..services import activity

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    installer: str
    email: str
    password: str
    otp: Optional[str] = None


@router.post("/login")
def login(body: LoginIn):
    db = tenant_session(None)
    try:
        inst = db.scalar(select(Installer).where(Installer.slug == body.installer.strip().lower(),
                                                 Installer.status == "active"))
        if inst is None:
            raise HTTPException(401, "Wrong installer, email or password")
        db.info["installer_id"] = inst.id
        user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
        if user is None or not user.active or not verify_password(body.password, user.password_hash):
            raise HTTPException(401, "Wrong installer, email or password")
        if user.totp_secret:
            if not body.otp:
                raise HTTPException(401, "Two-factor code required")
            if not pyotp.TOTP(user.totp_secret).verify(body.otp, valid_window=1):
                raise HTTPException(401, "Wrong two-factor code")
        activity.log(db, "login", user_id=user.id)
        db.commit()
        token = create_token({"typ": "staff", "iid": inst.id, "uid": user.id, "role": user.role, "name": user.name})
        return {"token": token, "user": _me(user, inst)}
    finally:
        db.close()


def _me(user: User, inst: Installer) -> dict:
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role,
            "installer": {"id": inst.id, "slug": inst.slug, "name": inst.name, "is_platform": inst.is_platform},
            "two_factor": bool(user.totp_secret)}


@router.get("/me")
def me(p: Principal = Depends(get_staff), db=Depends(staff_db)):
    user = db.get(User, p.user_id)
    db2 = tenant_session(None)
    try:
        inst = db2.get(Installer, p.installer_id)
        return _me(user, inst)
    finally:
        db2.close()


@router.post("/2fa/setup")
def twofa_setup(p: Principal = Depends(get_staff), db=Depends(staff_db)):
    user = db.get(User, p.user_id)
    secret = pyotp.random_base32()
    return {"secret": secret, "uri": pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="Solar Platform")}


class TwoFaIn(BaseModel):
    secret: str
    code: str


@router.post("/2fa/enable")
def twofa_enable(body: TwoFaIn, p: Principal = Depends(get_staff), db=Depends(staff_db)):
    if not pyotp.TOTP(body.secret).verify(body.code, valid_window=1):
        raise HTTPException(400, "Code does not match")
    user = db.get(User, p.user_id)
    user.totp_secret = body.secret
    activity.log(db, "2fa_enabled", user_id=user.id)
    return {"ok": True}


@router.post("/2fa/disable")
def twofa_disable(p: Principal = Depends(get_staff), db=Depends(staff_db)):
    user = db.get(User, p.user_id)
    user.totp_secret = None
    activity.log(db, "2fa_disabled", user_id=user.id)
    return {"ok": True}
