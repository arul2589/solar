"""Transactional email via an outbox table (email_log).

queue_email() renders a per-installer template and stores it as `queued`. dispatch_pending()
sends queued/failed messages through the configured provider with exponential back-off;
it runs inline after a request (best effort) and in the worker process (retries).
Every message is logged: to, template, time, provider id, status.
"""
from __future__ import annotations

import html
import logging
from datetime import timedelta
from typing import Optional

import httpx
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..config import get_config
from ..db import utcnow
from ..models import EmailLog
from ..security import mask_email
from .settings import load_all

log = logging.getLogger("email")


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def render(settings: dict, template: str, lang: str, ctx: dict) -> tuple[str, str, str]:
    tpls = settings["templates"].get(template) or {}
    t = tpls.get(lang) or tpls.get("en")
    if not t:
        raise KeyError(f"Unknown email template {template}")
    company = settings["company"]
    base = {"company_name": company.get("name", ""), "company_phone": company.get("phone", "")}
    data = _SafeDict(base | {k: ("" if v is None else v) for k, v in ctx.items()})
    subject = t["subject"].format_map(data)
    text = t["body"].format_map(data)
    body_html = ("<div style=\"font-family:Arial,'Noto Sans Tamil',sans-serif;font-size:15px;line-height:1.5\">"
                 + "<br>".join(_linkify(html.escape(line)) for line in text.split("\n")) + "</div>")
    return subject, text, body_html


def _linkify(line: str) -> str:
    out = []
    for word in line.split(" "):
        if word.startswith("http://") or word.startswith("https://"):
            out.append(f'<a href="{word}">{word}</a>')
        else:
            out.append(word)
    return " ".join(out)


def queue_email(db: Session, *, to: str, template: str, lang: str = "en", ctx: dict,
                request_id: Optional[int] = None) -> EmailLog:
    settings = load_all(db)
    subject, text, body_html = render(settings, template, lang, ctx)
    row = EmailLog(to_address=to, template=template, language=lang, subject=subject, body_text=text,
                   body_html=body_html, reply_to=settings["email"].get("reply_to"), request_id=request_id,
                   status="queued", next_attempt_at=utcnow())
    db.add(row)
    db.flush()
    log.info("email queued id=%s template=%s to=%s", row.id, template, mask_email(to))
    return row


# --------------------------------------------------------------------------- providers
def _send_resend(cfg, sender: str, row: EmailLog) -> str:
    r = httpx.post("https://api.resend.com/emails", timeout=20,
                   headers={"Authorization": f"Bearer {cfg.resend_api_key}"},
                   json={"from": sender, "to": [row.to_address], "subject": row.subject, "html": row.body_html,
                         "text": row.body_text, "reply_to": row.reply_to})
    r.raise_for_status()
    return r.json().get("id", "")


def _send_brevo(cfg, sender_name: str, sender_addr: str, row: EmailLog) -> str:
    payload = {"sender": {"name": sender_name, "email": sender_addr}, "to": [{"email": row.to_address}],
               "subject": row.subject, "htmlContent": row.body_html, "textContent": row.body_text}
    if row.reply_to:
        payload["replyTo"] = {"email": row.reply_to}
    r = httpx.post("https://api.brevo.com/v3/smtp/email", timeout=20,
                   headers={"api-key": cfg.brevo_api_key, "accept": "application/json"}, json=payload)
    r.raise_for_status()
    return r.json().get("messageId", "")


def send_one(db: Session, row: EmailLog) -> None:
    cfg = get_config()
    es = load_all(db)["email"]
    sender_addr, sender_name = es.get("from_address"), es.get("from_name", "")
    row.attempts += 1
    row.provider = cfg.email_provider
    try:
        if cfg.email_provider == "resend":
            pid = _send_resend(cfg, f"{sender_name} <{sender_addr}>", row)
        elif cfg.email_provider == "brevo":
            pid = _send_brevo(cfg, sender_name, sender_addr, row)
        else:   # "log": development provider, nothing leaves the server
            pid = f"log-{row.id}"
            log.info("[email:log] to=%s subject=%s", mask_email(row.to_address), row.subject)
        row.status, row.provider_id, row.sent_at, row.error = "sent", pid, utcnow(), None
    except Exception as exc:  # noqa: BLE001
        row.error = str(exc)[:500]
        if row.attempts >= cfg.email_max_attempts:
            row.status = "dead"
        else:
            row.status = "failed"
            row.next_attempt_at = utcnow() + timedelta(minutes=2 ** row.attempts)
        log.warning("email send failed id=%s attempt=%s: %s", row.id, row.attempts, row.error)


def dispatch_pending(db: Session, limit: int = 50) -> int:
    now = utcnow()
    rows = db.scalars(select(EmailLog).where(EmailLog.status.in_(["queued", "failed"]))
                      .where(or_(EmailLog.next_attempt_at.is_(None), EmailLog.next_attempt_at <= now))
                      .order_by(EmailLog.id).limit(limit)).all()
    for row in rows:
        send_one(db, row)
    return len(rows)
