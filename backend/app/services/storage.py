"""Private file storage on a local volume, with type/size checks and image re-encoding.

Files are never served directly; the API hands out short-lived signed URLs.
"""
from __future__ import annotations

import io
import os
import uuid
from pathlib import Path

from PIL import Image, ImageOps

from ..config import get_config
from ..security import signed_url_params

MAX_BYTES = 8 * 1024 * 1024
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
DOC_TYPES = {"application/pdf"}
MAX_PIXELS = 4000


class UploadError(ValueError):
    pass


def root() -> Path:
    p = Path(get_config().storage_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _sniff(data: bytes) -> str | None:
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:5] == b"%PDF-":
        return "application/pdf"
    return None


def reencode_image(data: bytes) -> bytes:
    """Re-encode to JPEG: strips EXIF/GPS and any payload hidden in the file."""
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)
        img.thumbnail((MAX_PIXELS, MAX_PIXELS))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=85)
        return out.getvalue()
    except Exception as exc:  # noqa: BLE001
        raise UploadError("File is not a valid image") from exc


def save_upload(installer_id: int, data: bytes, *, allow_pdf: bool = False) -> tuple[str, str, int]:
    if len(data) > MAX_BYTES:
        raise UploadError("File too large (max 8 MB)")
    kind = _sniff(data)
    if kind in IMAGE_TYPES:
        data = reencode_image(data)
        ctype, ext = "image/jpeg", "jpg"
    elif kind in DOC_TYPES and allow_pdf:
        ctype, ext = "application/pdf", "pdf"
    else:
        raise UploadError("Only JPEG, PNG or WEBP images" + (" or PDF" if allow_pdf else "") + " are allowed")
    key = f"{installer_id}/{uuid.uuid4().hex}.{ext}"
    put_bytes(key, data)
    return key, ctype, len(data)


def put_bytes(key: str, data: bytes) -> None:
    path = root() / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def get_bytes(key: str) -> bytes:
    path = (root() / key).resolve()
    if root().resolve() not in path.parents:
        raise UploadError("bad key")
    return path.read_bytes()


def delete(key: str) -> None:
    try:
        os.remove(root() / key)
    except FileNotFoundError:
        pass


def signed_url(key: str, ttl: int = 900) -> str:
    return f"/api/files/{key}?{signed_url_params(key, ttl)}"
