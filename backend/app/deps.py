"""Request-scoped dependencies: tenant sessions, current staff user, customer, roles."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional

import jwt
from fastapi import Depends, Header, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import tenant_session
from .models import Installer, User
from .security import decode_token


@dataclass
class Principal:
    kind: str                  # staff | customer
    installer_id: int
    user_id: Optional[int] = None
    customer_id: Optional[int] = None
    role: Optional[str] = None
    name: str = ""


def _bearer(authorization: Optional[str]) -> Optional[str]:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def get_principal(authorization: Optional[str] = Header(default=None)) -> Principal:
    token = _bearer(authorization)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    try:
        c = decode_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired")
    if c.get("typ") not in ("staff", "customer"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bad token")
    return Principal(kind=c["typ"], installer_id=int(c["iid"]), user_id=c.get("uid"), customer_id=c.get("cid"),
                     role=c.get("role"), name=c.get("name", ""))


def get_staff(p: Principal = Depends(get_principal)) -> Principal:
    if p.kind != "staff":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Staff only")
    return p


def get_customer(p: Principal = Depends(get_principal)) -> Principal:
    if p.kind != "customer":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Customer only")
    return p


def require_roles(*roles: str):
    def dep(p: Principal = Depends(get_staff)) -> Principal:
        if p.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot do this")
        return p
    return dep


def staff_db(p: Principal = Depends(get_staff)) -> Iterator[Session]:
    db = tenant_session(p.installer_id)
    try:
        # the user must still exist and be active
        u = db.get(User, p.user_id)
        if u is None or not u.active:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account disabled")
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def customer_db(p: Principal = Depends(get_customer)) -> Iterator[Session]:
    db = tenant_session(p.installer_id)
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def resolve_installer(slug: str) -> Installer:
    db = tenant_session(None)
    try:
        inst = db.scalar(select(Installer).where(Installer.slug == slug, Installer.status == "active",
                                                 Installer.is_platform.is_(False)))
        if inst is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Installer not found")
        db.expunge(inst)
        return inst
    finally:
        db.close()


def public_db(slug: str = Path(...)) -> Iterator[Session]:
    inst = resolve_installer(slug)
    db = tenant_session(inst.id)
    db.info["installer"] = inst
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
