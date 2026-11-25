"""Quotation helpers (Phase 2 fills in the builder, PDF and send flow)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Quotation


def latest_sent_quotation(db: Session, request_id: int) -> Optional[Quotation]:
    return db.scalar(select(Quotation).where(Quotation.request_id == request_id,
                                             Quotation.status.in_(["sent", "accepted"]))
                     .order_by(Quotation.id.desc()))
