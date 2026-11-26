from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response

from .config import get_config
from .routers import admin_config, admin_requests, auth, platform, public
from .security import check_signature
from .services import storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("app")

_cfg = get_config()
if _cfg.environment == "production" and _cfg.production_problems():
    # refuse to start an insecure production server; the log says exactly what to fix in .env
    raise RuntimeError("Unsafe production settings: " + "; ".join(_cfg.production_problems()))
if _cfg.environment == "development" and not _cfg.is_dev:
    log.warning("ENVIRONMENT=development on a non-local PUBLIC_BASE_URL: developer helpers are switched off. "
                "Set ENVIRONMENT=production for a real deployment.")

app = FastAPI(title="Solar Platform API", version="1.0.0",
              docs_url="/api/docs" if _cfg.is_dev else None, redoc_url=None,
              openapi_url="/api/openapi.json" if _cfg.is_dev else None)

app.include_router(auth.router)
app.include_router(public.router)
app.include_router(public.customer_router)
app.include_router(admin_requests.router)
app.include_router(admin_config.router)
app.include_router(platform.router)


def _optional_routers():
    # Phase 2/3 routers are added here as they are built; real import errors still surface
    import importlib
    import importlib.util
    for name in ("quotations", "projects", "knowledge"):
        if importlib.util.find_spec(f"app.routers.{name}") is None:
            continue
        mod = importlib.import_module(f"app.routers.{name}")
        for attr in ("router", "public_router"):
            if hasattr(mod, attr):
                app.include_router(getattr(mod, attr))


_optional_routers()


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/files/{key:path}")
def get_file(key: str, exp: int = Query(...), sig: str = Query(...)):
    """Private files via short-lived signed URLs only."""
    if not check_signature(key, exp, sig):
        raise HTTPException(403, "Link expired")
    try:
        data = storage.get_bytes(key)
    except (FileNotFoundError, storage.UploadError):
        raise HTTPException(404)
    ctype = "application/pdf" if key.endswith(".pdf") else ("image/svg+xml" if key.endswith(".svg") else "image/jpeg")
    return Response(data, media_type=ctype, headers={"Cache-Control": "private, max-age=600",
                                                     "X-Content-Type-Options": "nosniff"})
