"""Quotation arithmetic and bill-of-materials lines from a price master (SPEC 5.3, 6.7).

All money uses Decimal, rounded half-up to paise per line:
  amount = qty x unit price;  tax = amount x GST%;  total = amount + tax
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Sequence

from .network import money


@dataclass
class Line:
    description: str
    qty: Decimal
    unit_price: Decimal
    gst_pct: Decimal
    unit: str = "No"
    hsn: str = ""
    details: str = ""
    code: str = ""
    cost_price: Optional[Decimal] = None   # internal, for margin

    @property
    def amount(self) -> Decimal:
        return money(Decimal(str(self.qty)) * Decimal(str(self.unit_price)))

    @property
    def tax(self) -> Decimal:
        return money(self.amount * Decimal(str(self.gst_pct)) / 100)

    @property
    def total(self) -> Decimal:
        return self.amount + self.tax

    def to_dict(self):
        return {"code": self.code, "description": self.description, "details": self.details, "hsn": self.hsn,
                "qty": str(self.qty), "unit": self.unit, "unit_price": str(self.unit_price),
                "gst_pct": str(self.gst_pct), "amount": str(self.amount), "tax": str(self.tax),
                "total": str(self.total),
                "cost_price": None if self.cost_price is None else str(self.cost_price)}


@dataclass
class Totals:
    subtotal: Decimal
    tax: Decimal
    grand_total: Decimal
    tax_by_rate: dict = field(default_factory=dict)
    cost_total: Optional[Decimal] = None
    margin: Optional[Decimal] = None

    def to_dict(self):
        return {"subtotal": str(self.subtotal), "tax": str(self.tax), "grand_total": str(self.grand_total),
                "tax_by_rate": {k: str(v) for k, v in self.tax_by_rate.items()},
                "cost_total": None if self.cost_total is None else str(self.cost_total),
                "margin": None if self.margin is None else str(self.margin)}


def totals(lines: Sequence[Line]) -> Totals:
    sub = sum((l.amount for l in lines), Decimal("0.00"))
    tax = sum((l.tax for l in lines), Decimal("0.00"))
    by_rate: dict = {}
    for l in lines:
        key = f"{Decimal(str(l.gst_pct)).normalize():f}"
        by_rate[key] = by_rate.get(key, Decimal("0.00")) + l.tax
    cost = None
    if lines and all(l.cost_price is not None for l in lines):
        cost = sum((money(Decimal(str(l.qty)) * l.cost_price) for l in lines), Decimal("0.00"))
    return Totals(sub, tax, sub + tax, by_rate, cost, None if cost is None else sub - cost)


# --------------------------------------------------------------------------------------
# Bill of materials from price master rules
# --------------------------------------------------------------------------------------
@dataclass
class PriceRule:
    """A price-master item and the rule that decides its quantity."""
    code: str
    name: str
    unit_price: Decimal
    gst_pct: Decimal
    unit: str = "No"
    hsn: str = ""
    details: str = ""
    qty_rule: str = "fixed"        # fixed | per_kw | per_panel | dc_cable_m | ac_cable_m | earth_pits |
                                   # la_cable_m | per_string | per_mppt | panel | inverter
    qty_factor: Decimal = Decimal("1")
    phase: Optional[int] = None    # only for this supply phase
    system_kind: Optional[str] = None   # on_grid | hybrid | off_grid
    min_kw: Optional[float] = None
    max_kw: Optional[float] = None
    requires_la: bool = False
    cost_price: Optional[Decimal] = None
    sort_order: int = 100


def _qty(rule: PriceRule, ctx: dict) -> Decimal:
    f = Decimal(str(rule.qty_factor))
    r = rule.qty_rule
    base = {
        "fixed": Decimal("1"),
        "per_kw": Decimal(str(ctx["nominal_kw"])),
        "per_kwp": Decimal(str(ctx["dc_kwp"])),
        "per_panel": Decimal(ctx["panel_count"]),
        "panel": Decimal(ctx["panel_count"]),
        "inverter": Decimal("1"),
        "dc_cable_m": Decimal(str(math.ceil(ctx["dc_cable_m"]))),
        "ac_cable_m": Decimal(str(math.ceil(ctx["ac_cable_m"]))),
        "earth_pits": Decimal(ctx["earthing_pits"]),
        "la_cable_m": Decimal(str(math.ceil(ctx["la_cable_m"]))),
        "per_string": Decimal(ctx["strings"]),
        "per_mppt": Decimal(ctx["mppts"]),
    }.get(r, Decimal("1"))
    return base * f


def build_lines(rules: Sequence[PriceRule], ctx: dict) -> list[Line]:
    """ctx keys: nominal_kw, dc_kwp, panel_count, dc_cable_m, ac_cable_m, earthing_pits,
    la_cable_m, strings, mppts, phase, system_kind, lightning_arrester, panel (dict), inverter (dict)."""
    out = []
    for r in sorted(rules, key=lambda x: (x.sort_order, x.code)):
        if r.phase is not None and r.phase != ctx.get("phase"):
            continue
        if r.system_kind and r.system_kind != ctx.get("system_kind", "on_grid"):
            continue
        if r.min_kw is not None and ctx["dc_kwp"] < r.min_kw:
            continue
        if r.max_kw is not None and ctx["dc_kwp"] > r.max_kw:
            continue
        if r.requires_la and not ctx.get("lightning_arrester"):
            continue
        name, price, details, hsn, gst = r.name, r.unit_price, r.details, r.hsn, r.gst_pct
        if r.qty_rule == "panel" and ctx.get("panel"):
            p = ctx["panel"]
            name = r.name.format(**p) if "{" in r.name else r.name
            details = (r.details or "").format(**p, panel_count=ctx["panel_count"], dc_wp=int(round(ctx["dc_kwp"] * 1000)),
                                               nominal_kw=_fmt(ctx["nominal_kw"]))
            if p.get("price") is not None:
                price = Decimal(str(p["price"]))
        if r.qty_rule == "inverter" and ctx.get("inverter"):
            inv = ctx["inverter"]
            name = r.name.format(**inv) if "{" in r.name else r.name
            details = (r.details or "").format(**inv)
            if inv.get("price") is not None:
                price = Decimal(str(inv["price"]))
        qty = _qty(r, ctx)
        if qty <= 0:
            continue
        out.append(Line(description=name, qty=qty, unit_price=Decimal(str(price)), gst_pct=Decimal(str(gst)),
                        unit=r.unit, hsn=hsn, details=details, code=r.code, cost_price=r.cost_price))
    return out


def _fmt(x: float) -> str:
    return f"{x:g}"
