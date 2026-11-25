"""One-time codes for phone verification and customer login.

SMS sending uses the `log` provider until an SMS gateway is configured: the code is
written to the server log (with the phone masked) and, in development only, returned
in the API response so the flow can be tested end to end.
"""
from __future__ import annotations

import logging
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_config
from ..db import utcnow
from ..models import OtpCode
from ..security import mask_phone, token_hash

log = logging.getLogger("otp")
MAX_ATTEMPTS = 5


def issue(db: Session, channel: str, target: str, purpose: str) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    db.add(OtpCode(channel=channel, target_hash=token_hash(f"{channel}:{target}"), code_hash=token_hash(code),
                   purpose=purpose, expires_at=utcnow() + timedelta(minutes=get_config().otp_ttl_minutes)))
    log.info("[sms:log] OTP for %s is %s", mask_phone(target) if channel == "phone" else "email", code)
    return code


def verify(db: Session, channel: str, target: str, purpose: str, code: str) -> bool:
    row = db.scalar(select(OtpCode).where(OtpCode.target_hash == token_hash(f"{channel}:{target}"),
                                          OtpCode.purpose == purpose, OtpCode.used_at.is_(None))
                    .order_by(OtpCode.id.desc()))
    if row is None:
        return False
    exp = row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=utcnow().tzinfo)
    if exp < utcnow() or row.attempts >= MAX_ATTEMPTS:
        return False
    row.attempts += 1
    if row.code_hash != token_hash(code.strip()):
        return False
    row.used_at = utcnow()
    return True
