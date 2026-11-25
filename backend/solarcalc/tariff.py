"""Electricity bill from telescopic tariff slabs, and the inverse (units from a bill).

Slabs are a per-installer setting (SPEC 6.7, marked VERIFY). They are defined per
billing cycle (TANGEDCO domestic bills every two months).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from .models import TariffSlab
from .network import money


def bill_for_units(units: float, slabs: Sequence[TariffSlab]) -> Decimal:
    """Energy charge for `units` in one billing cycle (telescopic slabs)."""
    if units <= 0 or not slabs:
        return Decimal("0.00")
    remaining = Decimal(str(units))
    lower = Decimal("0")
    total = Decimal("0")
    for slab in sorted(slabs, key=lambda s: (s.upto is None, s.upto or 0)):
        upper = Decimal(slab.upto) if slab.upto is not None else None
        width = (upper - lower) if upper is not None else remaining
        take = min(remaining, width)
        if take > 0:
            total += take * Decimal(str(slab.rate))
            remaining -= take
        if upper is not None:
            lower = upper
        if remaining <= 0:
            break
    if remaining > 0:  # beyond last bounded slab: charge at last rate
        total += remaining * Decimal(str(sorted(slabs, key=lambda s: (s.upto is None, s.upto or 0))[-1].rate))
    return money(total)


def units_for_bill(amount: float, slabs: Sequence[TariffSlab], max_units: int = 100000) -> float:
    """Smallest unit count whose slab bill reaches `amount` (binary search)."""
    if amount <= 0 or not slabs:
        return 0.0
    target = Decimal(str(amount))
    lo, hi = 0.0, float(max_units)
    if bill_for_units(hi, slabs) < target:
        return hi
    for _ in range(60):
        mid = (lo + hi) / 2
        if bill_for_units(mid, slabs) < target:
            lo = mid
        else:
            hi = mid
    return round(hi, 1)
