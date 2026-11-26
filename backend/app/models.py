"""ORM models (SPEC section 9). Every tenant table carries installer_id via TenantMixin."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (JSON, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base, TenantMixin, utcnow

Money = Numeric(14, 2)


class Installer(Base):
    """A tenant. Its own id is the installer_id used everywhere else."""
    __tablename__ = "installer"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="active")
    is_platform: Mapped[bool] = mapped_column(Boolean, default=False)
    next_quote_number: Mapped[int] = mapped_column(Integer, default=1)
    next_request_number: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Role(TenantMixin, Base):
    """Role catalogue per installer (names are fixed in code; descriptions editable)."""
    __tablename__ = "role"
    __table_args__ = (UniqueConstraint("installer_id", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(String(200), default="")


class User(TenantMixin, Base):
    __tablename__ = "app_user"
    __table_args__ = (UniqueConstraint("installer_id", "email"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32))   # admin | sales | engineer | technician | platform_owner
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    totp_secret: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Customer(TenantMixin, Base):
    __tablename__ = "customer"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(32), index=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), index=True)
    whatsapp: Mapped[Optional[str]] = mapped_column(String(32))          # 10-digit Indian mobile
    contact_pref: Mapped[str] = mapped_column(String(12), default="email")  # email | whatsapp | both
    preferred_language: Mapped[str] = mapped_column(String(8), default="en")
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Site(TenantMixin, Base):
    __tablename__ = "site"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id", ondelete="CASCADE"), index=True)
    address: Mapped[str] = mapped_column(Text, default="")
    pincode: Mapped[Optional[str]] = mapped_column(String(10))
    district: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    site_type: Mapped[str] = mapped_column(String(20), default="home")   # home | commercial | industry
    eb_consumer_no: Mapped[Optional[str]] = mapped_column(String(40))
    tariff: Mapped[Optional[str]] = mapped_column(String(20))
    phase: Mapped[int] = mapped_column(Integer, default=1)
    sanction_load_kw: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    roof_type: Mapped[str] = mapped_column(String(20), default="rcc")
    roof_area_m2: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    roof_length_m: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    roof_width_m: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    direction: Mapped[str] = mapped_column(String(20), default="south")
    shade: Mapped[str] = mapped_column(String(10), default="none")
    floors: Mapped[Optional[int]] = mapped_column(Integer)


STAGES = ["new", "analysed", "quoted", "site_visit", "accepted", "installation", "net_metering", "completed",
          "lost", "on_hold"]
# Customer-facing status (SPEC 4.2)
PUBLIC_STATUS = {
    "new": "received", "analysed": "under_review", "quoted": "quotation_ready", "site_visit": "site_visit",
    "accepted": "accepted", "installation": "installation", "net_metering": "installation",
    "completed": "completed", "lost": "closed", "on_hold": "under_review",
}


class ServiceRequest(TenantMixin, Base):
    __tablename__ = "service_request"
    __table_args__ = (UniqueConstraint("installer_id", "reference"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id", ondelete="CASCADE"), index=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("site.id", ondelete="CASCADE"))
    stage: Mapped[str] = mapped_column(String(20), default="new", index=True)
    goal: Mapped[str] = mapped_column(String(20), default="reduce_bill")
    budget_range: Mapped[Optional[str]] = mapped_column(String(40))
    monthly_units: Mapped[Optional[float]] = mapped_column(Numeric(10, 1))
    monthly_bill: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    backup_load_w: Mapped[Optional[float]] = mapped_column(Numeric(10, 1))
    overrides: Mapped[dict] = mapped_column(JSON, default=dict)
    owner_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("app_user.id", ondelete="SET NULL"))
    engineer_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("app_user.id", ondelete="SET NULL"))
    site_visit_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    latest_analysis_id: Mapped[Optional[int]] = mapped_column(Integer)
    status_salt: Mapped[str] = mapped_column(String(64))
    lost_reason: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    customer: Mapped[Customer] = relationship(lazy="joined")
    site: Mapped[Site] = relationship(lazy="joined")


class RequestFile(TenantMixin, Base):
    __tablename__ = "request_file"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[Optional[int]] = mapped_column(ForeignKey("service_request.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))   # eb_bill | roof_photo | site_photo | logo
    storage_key: Mapped[str] = mapped_column(String(300))
    content_type: Mapped[str] = mapped_column(String(80))
    size: Mapped[int] = mapped_column(Integer)
    extracted: Mapped[Optional[dict]] = mapped_column(JSON)
    uploaded_by: Mapped[str] = mapped_column(String(20), default="customer")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AnalysisRun(TenantMixin, Base):
    """Immutable: inputs, settings snapshot and outputs, so an old quotation can be explained."""
    __tablename__ = "analysis_run"
    __immutable__ = True
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("service_request.id", ondelete="CASCADE"), index=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    trigger: Mapped[str] = mapped_column(String(20), default="submit")   # submit | edit | manual
    engine_version: Mapped[str] = mapped_column(String(20))
    inputs: Mapped[dict] = mapped_column(JSON)
    settings_snapshot: Mapped[dict] = mapped_column(JSON)
    outputs: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PanelModel(TenantMixin, Base):
    __tablename__ = "panel_model"
    id: Mapped[int] = mapped_column(primary_key=True)
    make: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(200))
    wp: Mapped[float] = mapped_column(Numeric(8, 1))
    voc: Mapped[float] = mapped_column(Numeric(8, 2))
    vmp: Mapped[float] = mapped_column(Numeric(8, 2))
    isc: Mapped[float] = mapped_column(Numeric(8, 2))
    imp: Mapped[float] = mapped_column(Numeric(8, 2))
    temp_coeff_voc_pct: Mapped[float] = mapped_column(Numeric(6, 3))
    temp_coeff_pmax_pct: Mapped[float] = mapped_column(Numeric(6, 3))
    length_mm: Mapped[float] = mapped_column(Numeric(8, 1))
    width_mm: Mapped[float] = mapped_column(Numeric(8, 1))
    price: Mapped[Optional[Decimal]] = mapped_column(Money)
    hsn: Mapped[str] = mapped_column(String(20), default="85414012")
    gst_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("5"))
    warranty_text: Mapped[str] = mapped_column(Text, default="")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_placeholder: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class InverterModel(TenantMixin, Base):
    __tablename__ = "inverter_model"
    id: Mapped[int] = mapped_column(primary_key=True)
    make: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(20), default="on_grid")
    ac_kw: Mapped[float] = mapped_column(Numeric(8, 2))
    phase: Mapped[int] = mapped_column(Integer)
    max_dc_voltage: Mapped[float] = mapped_column(Numeric(8, 1))
    mppt_min_v: Mapped[float] = mapped_column(Numeric(8, 1))
    mppt_max_v: Mapped[float] = mapped_column(Numeric(8, 1))
    num_mppt: Mapped[int] = mapped_column(Integer, default=1)
    max_input_current_per_mppt: Mapped[float] = mapped_column(Numeric(8, 2))
    ac_max_current: Mapped[float] = mapped_column(Numeric(8, 2))
    battery_voltage: Mapped[Optional[float]] = mapped_column(Numeric(8, 1))
    price: Mapped[Optional[Decimal]] = mapped_column(Money)
    hsn: Mapped[str] = mapped_column(String(20), default="8504")
    gst_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("5"))
    warranty_text: Mapped[str] = mapped_column(Text, default="")
    is_placeholder: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class PriceItem(TenantMixin, Base):
    __tablename__ = "price_item"
    __table_args__ = (UniqueConstraint("installer_id", "code"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(300))
    details: Mapped[str] = mapped_column(Text, default="")
    hsn: Mapped[str] = mapped_column(String(20), default="")
    unit: Mapped[str] = mapped_column(String(30), default="No")
    unit_price: Mapped[Decimal] = mapped_column(Money)
    cost_price: Mapped[Optional[Decimal]] = mapped_column(Money)
    gst_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("18"))
    qty_rule: Mapped[str] = mapped_column(String(20), default="fixed")
    qty_factor: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=Decimal("1"))
    phase: Mapped[Optional[int]] = mapped_column(Integer)
    inverter_phase: Mapped[Optional[int]] = mapped_column(Integer)
    system_kind: Mapped[Optional[str]] = mapped_column(String(20))
    min_kw: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))
    max_kw: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))
    requires_la: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=100)
    is_placeholder: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class NetworkRateRow(TenantMixin, Base):
    __tablename__ = "network_rate"
    __table_args__ = (UniqueConstraint("installer_id", "effective_from"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    effective_from: Mapped[date] = mapped_column(Date)
    rate: Mapped[Decimal] = mapped_column(Numeric(8, 3))
    note: Mapped[str] = mapped_column(String(300), default="")


class Setting(TenantMixin, Base):
    __tablename__ = "setting"
    __table_args__ = (UniqueConstraint("installer_id", "key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64))
    value: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Quotation(TenantMixin, Base):
    __tablename__ = "quotation"
    __table_args__ = (UniqueConstraint("installer_id", "number"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("service_request.id", ondelete="CASCADE"), index=True)
    analysis_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("analysis_run.id", ondelete="SET NULL"))
    number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="draft")   # draft | sent | accepted | superseded
    quote_date: Mapped[date] = mapped_column(Date)
    valid_until: Mapped[date] = mapped_column(Date)
    system_summary: Mapped[str] = mapped_column(String(300), default="")
    terms_text: Mapped[str] = mapped_column(Text, default="")
    warranty_text: Mapped[str] = mapped_column(Text, default="")
    scope_text: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    subtotal: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"))
    tax: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"))
    grand_total: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"))
    cost_total: Mapped[Optional[Decimal]] = mapped_column(Money)
    subsidy_amount: Mapped[Optional[Decimal]] = mapped_column(Money)   # placeholder, not computed in v1
    pdf_key: Mapped[Optional[str]] = mapped_column(String(300))
    public_token_hash: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    lines: Mapped[list["QuotationLine"]] = relationship(order_by="QuotationLine.sort", cascade="all, delete-orphan",
                                                        lazy="selectin")


class QuotationLine(TenantMixin, Base):
    __tablename__ = "quotation_line"
    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_id: Mapped[int] = mapped_column(ForeignKey("quotation.id", ondelete="CASCADE"), index=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)
    code: Mapped[str] = mapped_column(String(40), default="")
    description: Mapped[str] = mapped_column(String(300))
    details: Mapped[str] = mapped_column(Text, default="")
    hsn: Mapped[str] = mapped_column(String(20), default="")
    qty: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit: Mapped[str] = mapped_column(String(30), default="No")
    unit_price: Mapped[Decimal] = mapped_column(Money)
    gst_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    amount: Mapped[Decimal] = mapped_column(Money)
    tax: Mapped[Decimal] = mapped_column(Money)
    total: Mapped[Decimal] = mapped_column(Money)
    cost_price: Mapped[Optional[Decimal]] = mapped_column(Money)


class Project(TenantMixin, Base):
    __tablename__ = "project"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("service_request.id", ondelete="CASCADE"), index=True)
    quotation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("quotation.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(20), default="planned")   # planned | in_progress | done
    technician_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("app_user.id", ondelete="SET NULL"))
    pack: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ChecklistItem(TenantMixin, Base):
    __tablename__ = "checklist_item"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    step_no: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    title_ta: Mapped[Optional[str]] = mapped_column(String(200))
    points: Mapped[list] = mapped_column(JSON, default=list)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    done_by: Mapped[Optional[int]] = mapped_column(Integer)
    done_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str] = mapped_column(Text, default="")


class ProjectReading(TenantMixin, Base):
    __tablename__ = "project_reading"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(30))   # voc | isc | earth_resistance | insulation | other
    label: Mapped[str] = mapped_column(String(100), default="")
    value: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit: Mapped[str] = mapped_column(String(10), default="")
    expected: Mapped[Optional[str]] = mapped_column(String(60))
    ok: Mapped[Optional[bool]] = mapped_column(Boolean)
    recorded_by: Mapped[Optional[int]] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Diagram(TenantMixin, Base):
    __tablename__ = "diagram"
    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_run_id: Mapped[int] = mapped_column(ForeignKey("analysis_run.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))   # sld | roof | schedule
    svg: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EmailLog(TenantMixin, Base):
    __tablename__ = "email_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    to_address: Mapped[str] = mapped_column(String(200))
    template: Mapped[str] = mapped_column(String(40))
    language: Mapped[str] = mapped_column(String(8), default="en")
    subject: Mapped[str] = mapped_column(String(300))
    body_html: Mapped[str] = mapped_column(Text)
    body_text: Mapped[str] = mapped_column(Text, default="")
    reply_to: Mapped[Optional[str]] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)   # queued | sent | failed | dead
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    provider: Mapped[Optional[str]] = mapped_column(String(20))
    provider_id: Mapped[Optional[str]] = mapped_column(String(200))
    error: Mapped[Optional[str]] = mapped_column(Text)
    next_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class ActivityLog(TenantMixin, Base):
    __tablename__ = "activity_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    quotation_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer)
    actor: Mapped[str] = mapped_column(String(20), default="staff")   # staff | customer | system
    action: Mapped[str] = mapped_column(String(40))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class SubsidyCase(TenantMixin, Base):
    """Placeholder only (SPEC 1: PM Surya Ghar workflow is out of scope for v1)."""
    __tablename__ = "subsidy_case"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("service_request.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="not_started")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class OtpCode(TenantMixin, Base):
    __tablename__ = "otp_code"
    id: Mapped[int] = mapped_column(primary_key=True)
    channel: Mapped[str] = mapped_column(String(10))   # phone | email
    target_hash: Mapped[str] = mapped_column(String(128), index=True)
    code_hash: Mapped[str] = mapped_column(String(128))
    purpose: Mapped[str] = mapped_column(String(20))   # verify | login
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class KbDocument(TenantMixin, Base):
    """Reference document for the staff knowledge base (RAG). Not shown to customers."""
    __tablename__ = "kb_document"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    filename: Mapped[str] = mapped_column(String(300))
    storage_key: Mapped[str] = mapped_column(String(300))
    content_type: Mapped[str] = mapped_column(String(80))
    size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending|processing|ready|error
    error: Mapped[Optional[str]] = mapped_column(String(500))
    pages: Mapped[int] = mapped_column(Integer, default=0)
    vision_pages: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow)


class KbChunk(TenantMixin, Base):
    __tablename__ = "kb_chunk"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("kb_document.id", ondelete="CASCADE"), index=True)
    page: Mapped[int] = mapped_column(Integer, default=1)
    ordinal: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Optional[list]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
