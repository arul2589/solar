"""Public savings estimate for the website calculator.

Runs the normal calculation engine with the installer's own settings (tariff slabs, yields,
catalogue) and returns ONLY size, generation and savings. Cost, price lines, totals and payback
are always removed: customers never see a price automatically (CLAUDE.md / SPEC).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

# warning codes that are useful to a member of the public; everything else is staff-only
PUBLIC_NOTE_CODES = {"SANCTION_LOAD_CAP", "CEIG_INSPECTION", "HT_CONNECTION", "NO_HYBRID_INVERTER"}


def _money(v) -> Optional[float]:
    if v in (None, ""):
        return None
    return float(Decimal(str(v)).quantize(Decimal("1")))


def shape_public_estimate(out: dict) -> dict:
    """Reduce full engine output to the no-price public view."""
    if not out.get("ok") and not out.get("sizing"):
        return {"ok": False, "notes": [w["code"] for w in out.get("warnings", [])]}
    sizing = out.get("sizing") or {}
    roof = (out.get("roof") or {}).get("rule_of_thumb") or {}
    gen = out.get("generation") or {}
    sav = out.get("savings") or {}
    low, high = sav.get("low") or {}, sav.get("high") or {}
    a_low, a_high = _money(low.get("annual_saving")), _money(high.get("annual_saving"))
    return {
        "ok": True,
        "monthly_units": out.get("monthly_units"),
        "monthly_units_source": out.get("monthly_units_source"),
        "system": {
            "nominal_kw": sizing.get("nominal_kw"), "dc_kwp": sizing.get("dc_kwp"),
            "panel_count": sizing.get("panel_count"), "panel_wp": sizing.get("panel_wp"),
            "kind": out.get("system_kind"),
        },
        "roof": {"min_m2": roof.get("min_m2"), "recommended_m2": roof.get("recommended_m2")},
        "generation": {"per_month_low": gen.get("per_month_low"), "per_month_high": gen.get("per_month_high")},
        "savings": {
            "annual_low": a_low, "annual_high": a_high,
            "monthly_low": None if a_low is None else round(a_low / 12),
            "monthly_high": None if a_high is None else round(a_high / 12),
        },
        "notes": sorted({w["code"] for w in out.get("warnings", []) if w.get("code") in PUBLIC_NOTE_CODES}),
    }
