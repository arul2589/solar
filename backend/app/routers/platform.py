"""Platform owner: create and manage installers (tenants)."""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select

from ..db import tenant_session
from ..deps import Principal, require_roles
from ..models import Installer, ServiceRequest
from ..services.seed import seed_installer

router = APIRouter(prefix="/api/platform", tags=["platform"])


class InstallerIn(BaseModel):
    slug: str = Field(min_length=3, max_length=40)
    name: str = Field(min_length=2)
    admin_email: EmailStr
    admin_password: str = Field(min_length=8)


@router.get("/installers")
def list_installers(p: Principal = Depends(require_roles("platform_owner"))):
    db = tenant_session(None, bypass=True)
    try:
        counts = dict(db.execute(select(ServiceRequest.installer_id, func.count()).group_by(ServiceRequest.installer_id)).all())
        return [{"id": i.id, "slug": i.slug, "name": i.name, "status": i.status, "requests": counts.get(i.id, 0),
                 "created_at": i.created_at.isoformat()}
                for i in db.scalars(select(Installer).where(Installer.is_platform.is_(False)).order_by(Installer.id))]
    finally:
        db.close()


@router.post("/installers")
def create_installer(body: InstallerIn, p: Principal = Depends(require_roles("platform_owner"))):
    slug = body.slug.lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]+", slug) or slug in ("platform", "admin", "api", "www"):
        raise HTTPException(422, "Slug must be lowercase letters, digits and hyphens")
    db = tenant_session(None)
    try:
        if db.scalar(select(Installer).where(Installer.slug == slug)):
            raise HTTPException(409, "Slug already used")
    finally:
        db.close()
    iid = seed_installer(slug, body.name, admin_email=body.admin_email, admin_password=body.admin_password)
    return {"id": iid, "slug": slug}


class StatusIn(BaseModel):
    status: str


@router.put("/installers/{iid}/status")
def set_status(iid: int, body: StatusIn, p: Principal = Depends(require_roles("platform_owner"))):
    if body.status not in ("active", "suspended"):
        raise HTTPException(422)
    db = tenant_session(None)
    try:
        inst = db.get(Installer, iid)
        if inst is None or inst.is_platform:
            raise HTTPException(404)
        inst.status = body.status
        db.commit()
        return {"ok": True}
    finally:
        db.close()
