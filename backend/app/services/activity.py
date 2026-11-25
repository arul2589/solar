from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from ..models import ActivityLog


def log(db: Session, action: str, *, request_id: Optional[int] = None, quotation_id: Optional[int] = None,
        user_id: Optional[int] = None, actor: str = "staff", **detail) -> None:
    db.add(ActivityLog(action=action, request_id=request_id, quotation_id=quotation_id, user_id=user_id,
                       actor=actor, detail=detail))
