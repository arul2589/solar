"""Savings and payback (SPEC 6.7). Ranges, not single numbers, for customers.

Savings per cycle = bill(before) - bill(after net metering) - network charges
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional, Sequence

from .models import CalcSettings, TariffSlab
from .network import money
from .tariff import bill_for_units


def cycle_bill(units: float, slabs: Sequence[TariffSlab], s: CalcSettings) -> Decimal:
    if slabs:
        return bill_for_units(units, slabs)
    return money(Decimal(str(units)) * s.commercial_flat_rate)


def savings_estimate(*, dc_kwp: float, monthly_units: Optional[float], slabs: Sequence[TariffSlab],
                     s: CalcSettings, network_rate: Optional[Decimal], network_pct: float,
                     net_cost: Optional[Decimal]) -> dict:
    months = s.billing_cycle_months
    days = s.days_per_month * months
    out = {"cycle_months": months, "low": None, "high": None}
    for label, y in (("low", s.realistic_yield_low), ("high", s.realistic_yield_high)):
        gen_cycle = dc_kwp * y * days
        if monthly_units:
            use_cycle = monthly_units * months
            before = cycle_bill(use_cycle, slabs, s)
            after = cycle_bill(max(0.0, use_cycle - gen_cycle), slabs, s)
            energy_saving = before - after
        else:
            # no consumption known: value generation at the top applicable slab is unsafe,
            # use the flat rate setting
            energy_saving = money(Decimal(str(gen_cycle)) * s.commercial_flat_rate)
        nw = Decimal("0.00")
        if network_rate is not None:
            units_cuf = dc_kwp * 24 * s.cuf_tnerc * days
            nw = money(Decimal(str(units_cuf)) * Decimal(str(network_rate)) * Decimal(str(network_pct)))
            nw = money(nw * (1 + Decimal(str(s.network_gst_pct)) / 100))
        cycle_saving = energy_saving - nw
        annual = money(cycle_saving * Decimal(12) / Decimal(months))
        payback = None
        if net_cost is not None and annual > 0:
            payback = round(float(Decimal(str(net_cost)) / annual), 1)
        out[label] = {
            "yield_kwh_per_kw_day": y,
            "generation_per_month": round(dc_kwp * y * s.days_per_month, 0),
            "energy_saving_per_cycle": str(energy_saving), "network_charge_per_cycle": str(nw),
            "net_saving_per_cycle": str(cycle_saving), "annual_saving": str(annual), "payback_years": payback,
        }
    return out
