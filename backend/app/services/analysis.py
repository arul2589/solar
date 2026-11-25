"""Run the calculation engine for a request and store an immutable AnalysisRun."""
from __future__ import annotations

from dataclasses import asdict, fields
from typing import Optional

from sqlalchemy.orm import Session

from solarcalc import SiteInputs, analyse
from solarcalc.engine import ENGINE_VERSION

from ..models import AnalysisRun, ServiceRequest
from . import catalog
from .settings import calc_settings, load_all, tariff_slabs

OVERRIDABLE = {f.name for f in fields(SiteInputs)} | {"panel_id", "inverter_id"}


def _num(v):
    return None if v is None else float(v)


def inputs_for_request(req: ServiceRequest) -> dict:
    site = req.site
    category = {"home": "domestic", "commercial": "commercial", "industry": "industrial"}.get(site.site_type, "domestic")
    base = {
        "monthly_units": _num(req.monthly_units), "monthly_bill": _num(req.monthly_bill),
        "phase": int(site.phase or 1), "sanction_load_kw": _num(site.sanction_load_kw),
        "roof_area_m2": _num(site.roof_area_m2), "roof_length_m": _num(site.roof_length_m),
        "roof_width_m": _num(site.roof_width_m), "roof_type": site.roof_type, "direction": site.direction,
        "shade": site.shade, "category": category, "goal": req.goal,
        "daily_backup_load_w": _num(req.backup_load_w), "tariff": site.tariff,
    }
    for k, v in (req.overrides or {}).items():
        if k in OVERRIDABLE and v not in ("", None):
            base[k] = v
    return base


def run_engine(db: Session, inputs: dict) -> tuple[dict, dict]:
    s = calc_settings(db)
    site_kw = {k: v for k, v in inputs.items() if k in {f.name for f in fields(SiteInputs)}}
    inp = SiteInputs(**site_kw)
    out = analyse(inp, s, panels=catalog.panels(db), inverters=catalog.inverters(db),
                  network_rates=catalog.network_rates(db), tariff_slabs=tariff_slabs(db, inp.category),
                  price_rules=catalog.price_rules(db), panel_id=inputs.get("panel_id"),
                  inverter_id=inputs.get("inverter_id"))
    snapshot = {"calc": s.to_dict(), "tariff_slabs": load_all(db)["tariff_slabs"],
                "catalogue": catalog.catalogue_snapshot(db)}
    return out, snapshot


def analyse_request(db: Session, req: ServiceRequest, *, trigger: str = "submit",
                    user_id: Optional[int] = None) -> AnalysisRun:
    inputs = inputs_for_request(req)
    outputs, snapshot = run_engine(db, inputs)
    run = AnalysisRun(request_id=req.id, created_by=user_id, trigger=trigger, engine_version=ENGINE_VERSION,
                      inputs=inputs, settings_snapshot=snapshot, outputs=outputs)
    db.add(run)
    db.flush()
    req.latest_analysis_id = run.id
    if req.stage == "new":
        req.stage = "analysed"
    return run


def preview(db: Session, req: Optional[ServiceRequest], overrides: dict) -> dict:
    inputs = inputs_for_request(req) if req else {}
    for k, v in overrides.items():
        if k in OVERRIDABLE:
            inputs[k] = v if v != "" else None
    out, _ = run_engine(db, inputs)
    return {"inputs": inputs, "outputs": out}
