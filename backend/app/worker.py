"""Background job runner.

A simple database-backed queue: the email_log table is the outbox. The API tries to send
right after a request (BackgroundTasks); this worker loop retries failures with back-off
for every installer. Run with:  python -m app.worker
"""
from __future__ import annotations

import logging
import time

from fastapi import BackgroundTasks
from sqlalchemy import select

from .config import get_config
from .db import session_scope
from .models import Installer
from .services.email import dispatch_pending

log = logging.getLogger("worker")


def dispatch_for(installer_id: int) -> int:
    with session_scope(installer_id) as db:
        return dispatch_pending(db)


def dispatch_soon(background: BackgroundTasks, installer_id: int) -> None:
    if get_config().email_send_inline:
        background.add_task(_safe_dispatch, installer_id)


def _safe_dispatch(installer_id: int) -> None:
    try:
        dispatch_for(installer_id)
    except Exception:  # noqa: BLE001
        log.exception("inline dispatch failed; worker will retry")


def run_once() -> int:
    with session_scope(None, bypass=True) as db:
        ids = [i for i in db.scalars(select(Installer.id).where(Installer.status == "active"))]
    total = 0
    for iid in ids:
        total += dispatch_for(iid)
    return total


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    log.info("worker started")
    while True:
        try:
            n = run_once()
            if n:
                log.info("processed %s emails", n)
        except Exception:  # noqa: BLE001
            log.exception("worker loop error")
        time.sleep(15)


if __name__ == "__main__":
    main()
