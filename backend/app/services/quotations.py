"""Quotations: draft from an analysis run, edit lines (totals always computed server-side),
render PDF, send, and customer accept / question."""
from __future__ import annotations

import base64
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.orm import Session

from diagrams.svg import GENERATORS
from solarcalc.costing import Line, totals

from ..config import get_config
from ..db import utcnow
from ..models import AnalysisRun, Diagram, Installer, Quotation, QuotationLine, RequestFile, ServiceRequest
from ..security import new_secret_token, token_hash
from . import activity, storage
from .settings import load_all

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
_env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=select_autoescape(["html"]))


def latest_sent_quotation(db: Session, request_id: int) -> Optional[Quotation]:
    return db.scalar(select(Quotation).where(Quotation.request_id == request_id,
                                             Quotation.status.in_(["sent", "accepted"]))
                     .order_by(Quotation.id.desc()))


# ------------------------------------------------------------------ amounts in words (Indian system)
_ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve",
         "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _two(n: int) -> str:
    return _ONES[n] if n < 20 else (_TENS[n // 10] + (" " + _ONES[n % 10] if n % 10 else ""))


def _three(n: int) -> str:
    h, r = divmod(n, 100)
    return ((_ONES[h] + " Hundred" + (" " if r else "")) if h else "") + (_two(r) if r else "")


def rupees_in_words(amount: Decimal) -> str:
    amount = Decimal(str(amount)).quantize(Decimal("0.01"))
    rupees = int(amount)
    paise = int((amount - rupees) * 100)
    parts = []
    crore, rem = divmod(rupees, 10_000_000)
    lakh, rem = divmod(rem, 100_000)
    thousand, rem = divmod(rem, 1000)
    if crore:
        parts.append(_three(crore) + " Crore")
    if lakh:
        parts.append(_two(lakh) + " Lakh")
    if thousand:
        parts.append(_two(thousand) + " Thousand")
    if rem:
        parts.append(_three(rem))
    words = "Rupees " + (" ".join(parts) if parts else "Zero")
    if paise:
        words += " and " + _two(paise) + " Paise"
    return words + " Only"


def inr(v) -> str:
    """Indian digit grouping: 205451.2 -> 2,05,451.20"""
    d = Decimal(str(v or 0)).quantize(Decimal("0.01"))
    neg = d < 0
    s = f"{abs(d):.2f}"
    whole, frac = s.split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups + [tail])
    return ("-" if neg else "") + whole + "." + frac


_env.filters["inr"] = inr


# ------------------------------------------------------------------ draft / totals
def _line_from(d: dict, i: int) -> QuotationLine:
    l = Line(description=d["description"], qty=Decimal(str(d["qty"])), unit_price=Decimal(str(d["unit_price"])),
             gst_pct=Decimal(str(d["gst_pct"])), unit=d.get("unit") or "No", hsn=d.get("hsn") or "",
             details=d.get("details") or "", code=d.get("code") or "",
             cost_price=None if d.get("cost_price") in (None, "") else Decimal(str(d["cost_price"])))
    return QuotationLine(sort=i, code=l.code, description=l.description, details=l.details, hsn=l.hsn, qty=l.qty,
                         unit=l.unit, unit_price=l.unit_price, gst_pct=l.gst_pct, amount=l.amount, tax=l.tax,
                         total=l.total, cost_price=l.cost_price)


def recompute(q: Quotation) -> None:
    lines = [Line(description=x.description, qty=Decimal(str(x.qty)), unit_price=Decimal(str(x.unit_price)),
                  gst_pct=Decimal(str(x.gst_pct)), cost_price=None if x.cost_price is None else Decimal(str(x.cost_price)))
             for x in q.lines]
    t = totals(lines)
    q.subtotal, q.tax, q.grand_total = t.subtotal, t.tax, t.grand_total
    q.cost_total = t.cost_total


def system_summary(outputs: dict) -> str:
    sz = outputs.get("sizing") or {}
    inv = (outputs.get("inverter") or {}).get("inverter") or {}
    kind = "hybrid" if outputs.get("system_kind") == "hybrid" else "on-grid"
    return (f"{sz.get('nominal_kw', '?'):g} kW ({sz.get('dc_kwp')} kWp) {kind}: {sz.get('panel_count')} × "
            f"{(outputs.get('panel') or {}).get('wp', '?'):g} Wp panels, {inv.get('model', 'inverter TBD')}")


def create_draft(db: Session, req: ServiceRequest, user_id: Optional[int]) -> Quotation:
    if not req.latest_analysis_id:
        raise ValueError("Run an analysis first")
    run = db.get(AnalysisRun, req.latest_analysis_id)
    cost = (run.outputs or {}).get("cost")
    if not cost:
        raise ValueError("The analysis has no cost estimate (check price list and inverter catalogue)")
    s = load_all(db)
    inst = db.get(Installer, req.installer_id)
    number = inst.next_quote_number or 1
    inst.next_quote_number = number + 1
    qs = s["quotation"]
    today = date.today()
    q = Quotation(request_id=req.id, analysis_run_id=run.id, number=number, status="draft", quote_date=today,
                  valid_until=today + timedelta(days=int(qs.get("validity_days", 7))),
                  system_summary=system_summary(run.outputs),
                  terms_text=qs["terms_text"].replace("{validity_days}", str(qs.get("validity_days", 7))),
                  warranty_text=qs["warranty_text"], scope_text=qs["scope_text"], created_by=user_id)
    q.lines = [_line_from(d, i) for i, d in enumerate(cost["lines"], start=1)]
    recompute(q)
    db.add(q)
    db.flush()
    activity.log(db, "quotation_created", request_id=req.id, quotation_id=q.id, user_id=user_id, number=number,
                 grand_total=str(q.grand_total))
    return q


def update_draft(db: Session, q: Quotation, data: dict, user_id: Optional[int]) -> Quotation:
    if q.status != "draft":
        raise ValueError("Only draft quotations can be edited; use Revise to make a new version")
    before = {"grand_total": str(q.grand_total), "lines": len(q.lines)}
    for k in ("terms_text", "warranty_text", "scope_text", "notes", "system_summary"):
        if k in data and data[k] is not None:
            setattr(q, k, data[k])
    if data.get("valid_until"):
        q.valid_until = date.fromisoformat(data["valid_until"])
    if "subsidy_amount" in data:
        q.subsidy_amount = None if data["subsidy_amount"] in (None, "") else Decimal(str(data["subsidy_amount"]))
    if "lines" in data and data["lines"] is not None:
        q.lines.clear()
        db.flush()
        q.lines.extend(_line_from(d, i) for i, d in enumerate(data["lines"], start=1))
    recompute(q)
    db.flush()
    activity.log(db, "quotation_edited", request_id=q.request_id, quotation_id=q.id, user_id=user_id,
                 before=before, after={"grand_total": str(q.grand_total), "lines": len(q.lines)})
    return q


def revise(db: Session, q: Quotation, user_id: Optional[int]) -> Quotation:
    inst = db.get(Installer, q.installer_id)
    number = inst.next_quote_number
    inst.next_quote_number = number + 1
    today = date.today()
    validity = (q.valid_until - q.quote_date).days if q.valid_until and q.quote_date else 7
    n = Quotation(request_id=q.request_id, analysis_run_id=q.analysis_run_id, number=number, status="draft",
                  quote_date=today, valid_until=today + timedelta(days=validity), system_summary=q.system_summary,
                  terms_text=q.terms_text, warranty_text=q.warranty_text, scope_text=q.scope_text, notes=q.notes,
                  subsidy_amount=q.subsidy_amount, created_by=user_id)
    n.lines = [QuotationLine(sort=l.sort, code=l.code, description=l.description, details=l.details, hsn=l.hsn,
                             qty=l.qty, unit=l.unit, unit_price=l.unit_price, gst_pct=l.gst_pct, amount=l.amount,
                             tax=l.tax, total=l.total, cost_price=l.cost_price) for l in q.lines]
    recompute(n)
    db.add(n)
    db.flush()
    activity.log(db, "quotation_revised", request_id=q.request_id, quotation_id=n.id, user_id=user_id,
                 from_number=q.number, number=n.number)
    return n


# ------------------------------------------------------------------ diagrams
def diagram_svg(db: Session, run: AnalysisRun, kind: str) -> str:
    if kind not in GENERATORS:
        raise KeyError(kind)
    row = db.scalar(select(Diagram).where(Diagram.analysis_run_id == run.id, Diagram.kind == kind))
    if row:
        return row.svg
    svg = GENERATORS[kind](run.outputs or {})
    db.add(Diagram(analysis_run_id=run.id, kind=kind, svg=svg))
    db.flush()
    return svg


def _data_uri_svg(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


# ------------------------------------------------------------------ PDF
def _logo_uri(db: Session, company: dict) -> Optional[str]:
    fid = company.get("logo_file_id")
    if not fid:
        return None
    f = db.get(RequestFile, fid)
    if not f:
        return None
    return f"data:{f.content_type};base64," + base64.b64encode(storage.get_bytes(f.storage_key)).decode()


def render_html(db: Session, q: Quotation, *, internal: bool = False, lang: str = "en") -> str:
    s = load_all(db)
    req = db.get(ServiceRequest, q.request_id)
    run = db.get(AnalysisRun, q.analysis_run_id) if q.analysis_run_id else None
    diagrams = {}
    if run:
        diagrams = {k: _data_uri_svg(diagram_svg(db, run, k)) for k in ("sld", "roof")}
    t = _env.get_template("pdf/quotation.html")
    return t.render(q=q, req=req, customer=req.customer, site=req.site, company=s["company"], qs=s["quotation"],
                    lines=q.lines, words=rupees_in_words(q.grand_total), internal=internal,
                    disclaimer=s["quotation"]["disclaimer_ta" if lang == "ta" else "disclaimer_en"],
                    disclaimer_en=s["quotation"]["disclaimer_en"], logo=_logo_uri(db, s["company"]),
                    diagrams=diagrams, outputs=(run.outputs if run else {}))


def html_to_pdf(html: str) -> bytes:
    from weasyprint import HTML
    return HTML(string=html, base_url=str(TEMPLATES)).write_pdf()


def pdf_bytes(db: Session, q: Quotation, *, internal: bool = False) -> bytes:
    lang = (db.get(ServiceRequest, q.request_id).customer.preferred_language or "en")
    return html_to_pdf(render_html(db, q, internal=internal, lang=lang))


def store_pdf(db: Session, q: Quotation) -> str:
    data = pdf_bytes(db, q)
    key = f"{q.installer_id}/quotations/quotation-{q.number}-{q.id}.pdf"
    storage.put_bytes(key, data)
    q.pdf_key = key
    return key


# ------------------------------------------------------------------ send / accept
def quote_url(slug: str, token: str) -> str:
    return f"{get_config().public_base_url}/s/{slug}/q/{token}"


def send(db: Session, q: Quotation, user_id: Optional[int]) -> str:
    """Returns the customer token (only shown to staff in development)."""
    from .email import queue_email
    if q.status not in ("draft", "sent"):
        raise ValueError(f"Cannot send a {q.status} quotation")
    if not q.lines:
        raise ValueError("Quotation has no lines")
    req = db.get(ServiceRequest, q.request_id)
    inst = db.get(Installer, q.installer_id)
    store_pdf(db, q)
    token = new_secret_token()
    q.public_token_hash = token_hash(token)
    q.status, q.sent_at = "sent", utcnow()
    for other in db.scalars(select(Quotation).where(Quotation.request_id == q.request_id, Quotation.id != q.id,
                                                    Quotation.status == "sent")):
        other.status = "superseded"
    if req.stage in ("new", "analysed", "on_hold"):
        req.stage = "quoted"
    cust = req.customer
    email_status = "no_email"
    if cust.email:
        lang = cust.preferred_language if cust.preferred_language in ("en", "ta") else "en"
        s = load_all(db)
        row = queue_email(db, to=cust.email, template="quotation_ready", lang=lang, request_id=req.id,
                          ctx={"customer_name": cust.name, "quote_number": q.number, "system_summary": q.system_summary,
                               "quote_url": quote_url(inst.slug, token), "valid_until": q.valid_until.strftime("%d/%m/%Y"),
                               "disclaimer": s["quotation"]["disclaimer_ta" if lang == "ta" else "disclaimer_en"]})
        email_status = row.status
    activity.log(db, "quotation_sent", request_id=req.id, quotation_id=q.id, user_id=user_id, number=q.number,
                 grand_total=str(q.grand_total), email=email_status)
    return token


def find_by_token(db: Session, token: str) -> Optional[Quotation]:
    if not token:
        return None
    return db.scalar(select(Quotation).where(Quotation.public_token_hash == token_hash(token)))


def public_view(db: Session, q: Quotation) -> dict:
    s = load_all(db)
    req = db.get(ServiceRequest, q.request_id)
    lang = req.customer.preferred_language or "en"
    return {
        "number": q.number, "status": q.status, "quote_date": q.quote_date.isoformat(),
        "valid_until": q.valid_until.isoformat(), "expired": q.valid_until < date.today() and q.status == "sent",
        "system_summary": q.system_summary, "customer_name": req.customer.name, "reference": req.reference,
        "lines": [{"description": l.description, "details": l.details, "hsn": l.hsn, "qty": str(l.qty), "unit": l.unit,
                   "unit_price": str(l.unit_price), "gst_pct": str(l.gst_pct), "tax": str(l.tax), "total": str(l.total)}
                  for l in q.lines],
        "subtotal": str(q.subtotal), "tax": str(q.tax), "grand_total": str(q.grand_total),
        "in_words": rupees_in_words(q.grand_total), "terms_text": q.terms_text, "warranty_text": q.warranty_text,
        "scope_text": q.scope_text, "accepted_at": q.accepted_at.isoformat() if q.accepted_at else None,
        "disclaimer": s["quotation"]["disclaimer_ta" if lang == "ta" else "disclaimer_en"],
        "company": {k: s["company"].get(k) for k in ("name", "phone", "email", "address")},
    }


def accept(db: Session, q: Quotation) -> None:
    from .requests import notify_staff
    if q.status == "accepted":
        return
    if q.status != "sent":
        raise ValueError("This quotation is no longer open")
    if q.valid_until < date.today():
        raise ValueError("This quotation has expired; please ask us for a fresh quotation")
    req = db.get(ServiceRequest, q.request_id)
    q.status, q.accepted_at = "accepted", utcnow()
    req.stage = "accepted"
    activity.log(db, "quotation_accepted", request_id=req.id, quotation_id=q.id, actor="customer", number=q.number)
    notify_staff(db, req, f"Quotation #{q.number} accepted", f"Total Rs {inr(q.grand_total)}")
    on_accepted(db, req, q)


def on_accepted(db: Session, req: ServiceRequest, q: Quotation) -> None:
    """Hook: Phase 3 creates the project pack here."""
    try:
        from .projects import create_project
    except ImportError:
        return
    create_project(db, req, q)


def ask_question(db: Session, q: Quotation, message: str) -> None:
    from .requests import notify_staff
    req = db.get(ServiceRequest, q.request_id)
    activity.log(db, "customer_question", request_id=req.id, quotation_id=q.id, actor="customer",
                 text=message[:2000])
    notify_staff(db, req, f"Question on quotation #{q.number}", message[:2000])
