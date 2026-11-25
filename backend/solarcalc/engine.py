"""Full analysis of a request: one call, plain data in, plain JSON-able dict out."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional, Sequence

from . import roof as roofmod
from .cables import design_electrical
from .costing import PriceRule, build_lines, totals
from .models import CalcSettings, InverterSpec, NetworkRate, PanelSpec, SiteInputs, TariffSlab, Warning_
from .network import money, network_charge, network_percentage, rate_on
from .offgrid import offgrid_design
from .savings import savings_estimate
from .sizing import size_system, sizing_yield, units_per_kw_day_cuf
from .strings import select_inverter
from .tariff import units_for_bill

ENGINE_VERSION = "1.0.0"


def system_kind_for(goal: str) -> str:
    return "hybrid" if goal == "backup" else "on_grid"


def analyse(inp: SiteInputs, s: CalcSettings, *, panels: Sequence[PanelSpec], inverters: Sequence[InverterSpec],
            network_rates: Sequence[NetworkRate] = (), tariff_slabs: Sequence[TariffSlab] = (),
            price_rules: Sequence[PriceRule] = (), on: Optional[date] = None,
            panel_id: Optional[int] = None, inverter_id: Optional[int] = None) -> dict:
    on = on or date.today()
    warns: list[Warning_] = []
    result: dict = {"engine_version": ENGINE_VERSION, "as_of": on.isoformat()}

    # ---- consumption --------------------------------------------------------------
    monthly_units = inp.monthly_units
    if not monthly_units and inp.monthly_bill:
        if tariff_slabs:
            cycle_units = units_for_bill(inp.monthly_bill * s.billing_cycle_months, tariff_slabs)
            monthly_units = round(cycle_units / s.billing_cycle_months, 1)
        else:
            monthly_units = round(inp.monthly_bill / float(s.commercial_flat_rate), 1)
        result["monthly_units_source"] = "bill_amount"
    else:
        result["monthly_units_source"] = "units" if monthly_units else None
    result["monthly_units"] = monthly_units
    if not monthly_units and not inp.target_kw and not inp.panel_count:
        warns.append(Warning_("NO_CONSUMPTION_DATA", "No monthly units or bill amount given; cannot size the system.", "error"))
        result["warnings"] = [w.to_dict() for w in warns]
        result["ok"] = False
        return result

    # ---- panel ---------------------------------------------------------------------
    if not panels:
        warns.append(Warning_("MISSING_CATALOGUE", "No panel models in the catalogue.", "error"))
        result["warnings"] = [w.to_dict() for w in warns]
        result["ok"] = False
        return result
    panel = next((p for p in panels if p.id == panel_id), None) if panel_id else None
    panel = panel or panels[0]
    for attr in ("voc", "vmp", "isc", "imp", "length_mm", "width_mm"):
        if not getattr(panel, attr):
            warns.append(Warning_("MISSING_CATALOGUE", f"Panel {panel.model} is missing {attr}.", "error"))

    # ---- roof capacity ---------------------------------------------------------------
    roof_given = bool(inp.roof_area_m2 or (inp.roof_length_m and inp.roof_width_m))
    max_panels_roof = None
    if roof_given:
        probe = roofmod.layout(panel, 10_000, s, length_m=inp.roof_length_m, width_m=inp.roof_width_m,
                               area_m2=inp.roof_area_m2)
        max_panels_roof = probe.capacity

    sizing = size_system(panel, s, monthly_units=monthly_units, sanction_load_kw=inp.sanction_load_kw,
                         max_panels_by_roof=max_panels_roof, target_kw_override=inp.target_kw,
                         panel_count_override=inp.panel_count)
    warns += sizing.warnings
    n = sizing.panel_count
    result["panel"] = {"id": panel.id, "model": panel.model, "wp": panel.wp,
                       "length_mm": panel.length_mm, "width_mm": panel.width_mm}
    result["sizing"] = sizing.to_dict() | {
        "yield_used_kwh_per_kw_day": sizing_yield(s), "cuf_units_per_kw_day": units_per_kw_day_cuf(s.cuf_tnerc)}

    # ---- roof --------------------------------------------------------------------------
    thumb = roofmod.rule_of_thumb_area(sizing.dc_kwp, s)
    lay = roofmod.layout(panel, n, s, length_m=inp.roof_length_m, width_m=inp.roof_width_m, area_m2=inp.roof_area_m2)
    available = inp.roof_area_m2 or ((inp.roof_length_m or 0) * (inp.roof_width_m or 0)) or None
    roof = {"rule_of_thumb": thumb, "available_m2": available, "layout": lay.to_dict(include_panels=True),
            "tilt_deg": s.tilt_deg, "direction": inp.direction}
    if available:
        roof["fits"] = lay.fits and available >= thumb["min_m2"]
        if not roof["fits"]:
            warns.append(Warning_("ROOF_TOO_SMALL",
                f"{n} panels need about {max(lay.required_area_m2, thumb['min_m2']):.1f} m2; "
                f"about {available:.1f} m2 available.", "warning"))
    else:
        roof["fits"] = None
        warns.append(Warning_("ROOF_UNKNOWN", "Roof area not given; confirm at site visit.", "info"))
    result["roof"] = roof

    if inp.shade == "heavy":
        warns.append(Warning_("HEAVY_SHADE", "Heavy shade reported: generation may be much lower; site survey needed.", "warning"))
    elif inp.shade == "some":
        warns.append(Warning_("SOME_SHADE", "Some shade reported: check shade-free window 9:00-16:00 at site.", "info"))
    if (inp.direction or "").lower() in ("north", "n"):
        warns.append(Warning_("NORTH_FACING", "North-facing roof: avoid; use a south-facing structure.", "warning"))

    # ---- inverter & strings --------------------------------------------------------------
    kind = system_kind_for(inp.goal)
    choice = select_inverter(panel, n, inverters, s, supply_phase=inp.phase, kind=kind, preferred_id=inverter_id)
    if choice.inverter is None and kind == "hybrid":
        warns.append(Warning_("NO_HYBRID_INVERTER", "No hybrid inverter in catalogue; showing on-grid design.", "warning"))
        kind = "on_grid"
        choice = select_inverter(panel, n, inverters, s, supply_phase=inp.phase, kind=kind, preferred_id=inverter_id)
    warns += choice.warnings
    result["system_kind"] = kind
    result["inverter"] = choice.to_dict()

    electrical = None
    if choice.inverter and choice.strings and choice.strings.feasible:
        electrical = design_electrical(panel, choice.inverter, choice.strings, s,
                                       dc_run_one_way_m=inp.dc_run_one_way_m, ac_run_m=inp.ac_run_m)
        warns += electrical.warnings
        result["electrical"] = electrical.to_dict()
    else:
        result["electrical"] = None

    # ---- off-grid / hybrid battery ---------------------------------------------------------
    if kind != "on_grid" or inp.daily_backup_load_w:
        if inp.daily_backup_load_w:
            result["battery"] = offgrid_design(inp.daily_backup_load_w, n * panel.wp, s, backup_h=inp.backup_hours,
                                               battery_v=(choice.inverter.battery_voltage if choice.inverter else None))
        else:
            warns.append(Warning_("BACKUP_LOAD_UNKNOWN", "Backup load not given; battery not sized.", "info"))

    # ---- network charges ---------------------------------------------------------------------
    nr = rate_on(on, network_rates)
    pct = network_percentage(sizing.dc_kwp, inp.category, s)
    if nr:
        days = int(s.days_per_month * s.billing_cycle_months)
        nc = network_charge(sizing.dc_kwp, days, s, rate=nr.rate, category=inp.category)
        result["network_charge"] = nc.to_dict() | {"rate_effective_from": nr.effective_from.isoformat(),
                                                   "per": f"{s.billing_cycle_months}-month billing cycle"}
    else:
        result["network_charge"] = None
        warns.append(Warning_("NO_NETWORK_RATE", "No network-charge rate configured for today.", "warning"))

    # ---- cost --------------------------------------------------------------------------------
    cost = None
    if price_rules and choice.inverter:
        ctx = bom_context(sizing, panel, choice, electrical, inp, kind)
        lines = build_lines(price_rules, ctx)
        t = totals(lines)
        band = Decimal(str(s.cost_range_band_pct)) / 100
        cost = {"lines": [l.to_dict() for l in lines], "totals": t.to_dict(),
                "range_low": str(money(t.grand_total * (1 - band))),
                "range_high": str(money(t.grand_total * (1 + band)))}
    elif not price_rules:
        warns.append(Warning_("NO_PRICE_LIST", "Price list is empty; no cost estimate.", "info"))
    result["cost"] = cost

    # ---- savings -------------------------------------------------------------------------------
    net_cost = Decimal(cost["totals"]["grand_total"]) if cost else None
    result["savings"] = savings_estimate(dc_kwp=sizing.dc_kwp, monthly_units=monthly_units, slabs=tariff_slabs, s=s,
                                         network_rate=nr.rate if nr else None, network_pct=pct, net_cost=net_cost)
    result["generation"] = {
        "per_day_low": round(sizing.dc_kwp * s.realistic_yield_low, 1),
        "per_day_high": round(sizing.dc_kwp * s.realistic_yield_high, 1),
        "per_month_low": round(sizing.dc_kwp * s.realistic_yield_low * s.days_per_month),
        "per_month_high": round(sizing.dc_kwp * s.realistic_yield_high * s.days_per_month),
        "per_day_cuf": round(sizing.dc_kwp * units_per_kw_day_cuf(s.cuf_tnerc), 2),
    }

    # de-duplicate warnings by code+message
    seen, uniq = set(), []
    for w in warns:
        key = (w.code, w.message)
        if key not in seen:
            seen.add(key)
            uniq.append(w)
    result["warnings"] = [w.to_dict() for w in uniq]
    result["ok"] = not any(w.severity == "error" for w in uniq)
    return result


def bom_context(sizing, panel: PanelSpec, choice, electrical, inp: SiteInputs, kind: str) -> dict:
    inv = choice.inverter
    return {
        "nominal_kw": sizing.nominal_kw, "dc_kwp": sizing.dc_kwp, "panel_count": sizing.panel_count,
        "dc_cable_m": electrical.dc_cable_total_m if electrical else 0,
        "ac_cable_m": electrical.ac_cable_total_m if electrical else 0,
        "earthing_pits": electrical.earthing_pits if electrical else 0,
        "la_cable_m": electrical.la_cable_m if electrical else 0,
        "lightning_arrester": electrical.lightning_arrester if electrical else False,
        "strings": choice.strings.string_count if choice.strings else 0,
        "mppts": len({st["mppt"] for st in choice.strings.strings}) if choice.strings else 0,
        "phase": inp.phase, "system_kind": kind,
        "panel": {"model": panel.model, "wp": f"{panel.wp:g}", "price": panel.price},
        "inverter": {"model": inv.model, "ac_kw": f"{inv.ac_kw:g}", "phase": inv.phase,
                     "phase_label": "Single Phase" if inv.phase == 1 else "Three Phase", "price": inv.price},
    }
