"""System sizing (SPEC 6.1, 6.2)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from .models import CalcSettings, PanelSpec, Warning_


def units_per_kw_day_cuf(cuf: float) -> float:
    """Generation per kW per day = 24 x CUF (5.04 at CUF 21%)."""
    return round(24 * cuf, 6)


def sizing_yield(s: CalcSettings) -> float:
    if s.sizing_yield_basis == "cuf":
        return units_per_kw_day_cuf(s.cuf_tnerc)
    if s.sizing_yield_basis == "realistic_low":
        return s.realistic_yield_low
    return (s.realistic_yield_low + s.realistic_yield_high) / 2


def kw_needed(monthly_units: float, s: CalcSettings) -> float:
    per_kw_month = sizing_yield(s) * s.days_per_month
    if per_kw_month <= 0:
        raise ValueError("Yield setting must be positive")
    return monthly_units / per_kw_month


def panels_for_wp(target_wp: float, panel_wp: float) -> int:
    """Panels = ceil(target Wp / panel Wp)."""
    if panel_wp <= 0:
        raise ValueError("Panel Wp must be positive")
    return max(1, math.ceil(round(target_wp / panel_wp, 9)))


def nominal_kw(dc_kwp: float, s: CalcSettings) -> float:
    """The 'sold as' label: 5 x 615 W = 3.075 kWp -> '3 kW' (quotation #276)."""
    if s.nominal_kw_rounding == "round":
        return float(max(1, round(dc_kwp)))
    return float(max(1, math.floor(round(dc_kwp, 6))))


@dataclass
class SizingResult:
    monthly_units: Optional[float]
    kw_needed: Optional[float]
    target_kw: float
    panel_count: int
    panel_wp: float
    dc_kwp: float
    nominal_kw: float
    limited_by: Optional[str] = None
    max_kw_by_sanction: Optional[float] = None
    max_kw_by_roof: Optional[float] = None
    warnings: list = field(default_factory=list)

    def to_dict(self):
        d = {k: v for k, v in self.__dict__.items() if k != "warnings"}
        return d


def size_system(
    panel: PanelSpec,
    s: CalcSettings,
    *,
    monthly_units: Optional[float] = None,
    sanction_load_kw: Optional[float] = None,
    max_panels_by_roof: Optional[int] = None,
    target_kw_override: Optional[float] = None,
    panel_count_override: Optional[int] = None,
) -> SizingResult:
    warnings: list[Warning_] = []
    need = kw_needed(monthly_units, s) if monthly_units else None

    if panel_count_override:
        count = int(panel_count_override)
        target = count * panel.wp / 1000
        limited = "override"
    else:
        target = target_kw_override if target_kw_override else need
        if target is None:
            raise ValueError("Need monthly units or a target kW")
        count = panels_for_wp(target * 1000, panel.wp)
        limited = "override" if target_kw_override else None

    max_by_sanction = None
    if sanction_load_kw and not panel_count_override:
        max_by_sanction = sanction_load_kw
        cap = max(1, math.floor(round(sanction_load_kw * 1000 / panel.wp, 9)))
        if count > cap:
            count = cap
            limited = "sanction_load"
            warnings.append(Warning_(
                "SANCTION_LOAD_CAP",
                f"System capped at sanction load {sanction_load_kw:g} kW. A load enhancement "
                f"application is needed for a larger system.", "warning"))
    elif sanction_load_kw and count * panel.wp / 1000 > sanction_load_kw:
        warnings.append(Warning_(
            "SANCTION_LOAD_EXCEEDED",
            f"PV capacity exceeds sanction load {sanction_load_kw:g} kW; TANGEDCO requires a load "
            f"enhancement application.", "warning"))

    max_by_roof_kw = None
    if max_panels_by_roof is not None:
        max_by_roof_kw = max_panels_by_roof * panel.wp / 1000
        if count > max_panels_by_roof and not panel_count_override:
            if max_panels_by_roof <= 0:
                warnings.append(Warning_("ROOF_TOO_SMALL", "No panels fit on the stated roof area.", "error"))
                count = max(count, 1)
            else:
                count = max_panels_by_roof
                limited = "roof_area"
                warnings.append(Warning_(
                    "ROOF_LIMITS_SIZE",
                    f"Roof space limits the system to {max_panels_by_roof} panels "
                    f"({max_by_roof_kw:.2f} kWp).", "warning"))

    dc_kwp = round(count * panel.wp / 1000, 3)
    res = SizingResult(
        monthly_units=monthly_units, kw_needed=round(need, 3) if need else None,
        target_kw=round(target, 3), panel_count=count, panel_wp=panel.wp, dc_kwp=dc_kwp,
        nominal_kw=nominal_kw(dc_kwp, s), limited_by=limited,
        max_kw_by_sanction=max_by_sanction, max_kw_by_roof=max_by_roof_kw, warnings=warnings,
    )
    return res
