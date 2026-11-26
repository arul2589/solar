"""Passwords, tokens, signing and personal-data masking."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from .config import get_config

_ph = PasswordHasher()
ALGO = "HS256"

ROLES = ("admin", "sales", "engineer", "technician", "normal", "platform_owner")
# "normal": read-only staff (requests, designs, diagrams, knowledge base) with customer details hidden
PRICE_ROLES = {"admin", "sales", "engineer", "platform_owner"}    # technicians never see prices
MARGIN_ROLES = {"admin", "sales"}
PII_ROLES = {"admin", "sales", "engineer", "technician", "platform_owner"}   # may see customer contact details


def hash_password(pw: str) -> str:
    return _ph.hash(pw)


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, pw)
    except (VerifyMismatchError, InvalidHashError, Exception):
        return False


def create_token(claims: dict[str, Any], minutes: int | None = None) -> str:
    cfg = get_config()
    now = datetime.now(timezone.utc)
    payload = dict(claims)
    payload["iat"] = int(now.timestamp())
    payload["exp"] = int((now + timedelta(minutes=minutes or cfg.access_token_minutes)).timestamp())
    return jwt.encode(payload, cfg.secret_key, algorithm=ALGO)


def decode_token(token: str) -> dict:
    return jwt.decode(token, get_config().secret_key, algorithms=[ALGO])


def new_secret_token(nbytes: int = 24) -> str:
    return secrets.token_urlsafe(nbytes)


def token_hash(token: str) -> str:
    """Keyed hash for tokens and lookup values stored at rest."""
    return hmac.new(get_config().secret_key.encode(), token.encode(), hashlib.sha256).hexdigest()


def sign(value: str, expires_at: int) -> str:
    msg = f"{value}|{expires_at}".encode()
    return hmac.new(get_config().secret_key.encode(), msg, hashlib.sha256).hexdigest()[:40]


def signed_url_params(key: str, ttl_seconds: int = 900) -> str:
    exp = int(time.time()) + ttl_seconds
    return f"exp={exp}&sig={sign(key, exp)}"


def check_signature(key: str, exp: int, sig: str) -> bool:
    if exp < time.time():
        return False
    return hmac.compare_digest(sign(key, exp), sig)


def mask_phone(phone: str | None) -> str:
    if not phone:
        return ""
    digits = "".join(ch for ch in phone if ch.isdigit())
    return ("*" * max(0, len(digits) - 4)) + digits[-4:]


def mask_email(email: str | None) -> str:
    if not email or "@" not in email:
        return ""
    user, dom = email.split("@", 1)
    return (user[:1] + "***@" + dom)


def normalise_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits
