"""Tamil Nadu network charges (SPEC 6.6).

Generated units = PV kW x 24 x CUF x days
Network charge  = generated units x network rate x percentage allowed
GST             = network charge x GST%  (split CGST/SGST equally)
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional

from .models import CalcSettings, NetworkRate

TWO = Decimal("0.01")


def money(x) -> Decimal:
    return Decimal(str(x)).quantize(TWO, rounding=ROUND_HALF_UP)


def rate_on(on: date, table: Iterable[NetworkRate]) -> Optional[NetworkRate]:
    """Latest rate whose effective date is on/before `on`."""
    best = None
    for r in table:
        if r.effective_from <= on and (best is None or r.effective_from > best.effective_from):
            best = r
    return best


def generated_units(pv_kw: float, cuf: float, days: int, rounding: str = "floor") -> int | float:
    raw = pv_kw * 24 * cuf * days
    # avoid float noise such as 1637.9999999 before flooring
    raw = round(raw, 6)
    if rounding == "floor":
        return math.floor(raw)
    if rounding == "round":
        return int(Decimal(str(raw)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return raw


def network_percentage(pv_kw: float, category: str, s: CalcSettings) -> float:
    if category == "domestic" and pv_kw <= s.network_domestic_kw_limit:
        return s.network_pct_domestic_upto_10kw
    return s.network_pct_other


@dataclass
class NetworkChargeResult:
    pv_kw: float
    days: int
    cuf: float
    units: float
    rate: Decimal
    percentage: float
    charge: Decimal
    cgst: Decimal
    sgst: Decimal
    total: Decimal
    rate_effective_from: Optional[date] = None

    def to_dict(self):
        return {
            "pv_kw": self.pv_kw, "days": self.days, "cuf": self.cuf, "units": self.units,
            "rate": str(self.rate), "percentage": self.percentage, "charge": str(self.charge),
            "cgst": str(self.cgst), "sgst": str(self.sgst), "total": str(self.total),
            "rate_effective_from": self.rate_effective_from.isoformat() if self.rate_effective_from else None,
        }


def network_charge(
    pv_kw: float,
    days: int,
    s: CalcSettings,
    *,
    rate: Optional[Decimal] = None,
    on: Optional[date] = None,
    table: Iterable[NetworkRate] = (),
    category: str = "domestic",
    include_gst: bool = True,
) -> NetworkChargeResult:
    eff = None
    if rate is None:
        r = rate_on(on or date.today(), table)
        if r is None:
            raise ValueError("No network rate configured for the date")
        rate, eff = r.rate, r.effective_from
    units = generated_units(pv_kw, s.cuf_tnerc, days, s.network_units_rounding)
    pct = network_percentage(pv_kw, category, s)
    charge = money(Decimal(str(units)) * Decimal(str(rate)) * Decimal(str(pct)))
    if include_gst:
        half = Decimal(str(s.network_gst_pct)) / 2 / 100
        cgst = money(charge * half)
        sgst = money(charge * half)
    else:
        cgst = sgst = Decimal("0.00")
    return NetworkChargeResult(pv_kw, days, s.cuf_tnerc, units, Decimal(str(rate)), pct, charge,
                               cgst, sgst, charge + cgst + sgst, eff)
