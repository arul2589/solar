"""Convert catalogue / price-master rows into solarcalc data types."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from solarcalc import InverterSpec, NetworkRate, PanelSpec
from solarcalc.costing import PriceRule

from ..models import InverterModel, NetworkRateRow, PanelModel, PriceItem


def f(x):
    return None if x is None else float(x)


def panel_spec(p: PanelModel) -> PanelSpec:
    return PanelSpec(model=f"{p.make} {p.model}".strip(), wp=f(p.wp), voc=f(p.voc), vmp=f(p.vmp), isc=f(p.isc),
                     imp=f(p.imp), temp_coeff_voc_pct=f(p.temp_coeff_voc_pct),
                     temp_coeff_pmax_pct=f(p.temp_coeff_pmax_pct), length_mm=f(p.length_mm), width_mm=f(p.width_mm),
                     price=p.price, id=p.id)


def inverter_spec(i: InverterModel) -> InverterSpec:
    return InverterSpec(model=f"{i.make} {i.model}".strip(), ac_kw=f(i.ac_kw), phase=int(i.phase),
                        max_dc_voltage=f(i.max_dc_voltage), mppt_min_v=f(i.mppt_min_v), mppt_max_v=f(i.mppt_max_v),
                        num_mppt=int(i.num_mppt), max_input_current_per_mppt=f(i.max_input_current_per_mppt),
                        ac_max_current=f(i.ac_max_current), kind=i.kind, battery_voltage=f(i.battery_voltage),
                        price=i.price, id=i.id)


def panels(db: Session) -> list[PanelSpec]:
    rows = db.scalars(select(PanelModel).where(PanelModel.active.is_(True))
                      .order_by(PanelModel.is_default.desc(), PanelModel.id)).all()
    return [panel_spec(p) for p in rows]


def inverters(db: Session) -> list[InverterSpec]:
    rows = db.scalars(select(InverterModel).where(InverterModel.active.is_(True)).order_by(InverterModel.id)).all()
    return [inverter_spec(i) for i in rows]


def network_rates(db: Session) -> list[NetworkRate]:
    rows = db.scalars(select(NetworkRateRow).order_by(NetworkRateRow.effective_from)).all()
    return [NetworkRate(r.effective_from, Decimal(str(r.rate))) for r in rows]


def price_rules(db: Session) -> list[PriceRule]:
    rows = db.scalars(select(PriceItem).where(PriceItem.active.is_(True))).all()
    return [PriceRule(code=r.code, name=r.name, unit_price=Decimal(str(r.unit_price)), gst_pct=Decimal(str(r.gst_pct)),
                      unit=r.unit, hsn=r.hsn, details=r.details, qty_rule=r.qty_rule,
                      qty_factor=Decimal(str(r.qty_factor)), phase=r.phase, system_kind=r.system_kind,
                      min_kw=f(r.min_kw), max_kw=f(r.max_kw), requires_la=r.requires_la,
                      cost_price=None if r.cost_price is None else Decimal(str(r.cost_price)), sort_order=r.sort_order)
            for r in rows]


def catalogue_snapshot(db: Session) -> dict:
    """Stored with every analysis run so it can be explained later."""
    def dec(v):
        return None if v is None else str(v)
    return {
        "panels": [p.__dict__ | {"price": dec(p.price)} for p in panels(db)],
        "inverters": [i.__dict__ | {"price": dec(i.price)} for i in inverters(db)],
        "network_rates": [{"effective_from": r.effective_from.isoformat(), "rate": str(r.rate)} for r in network_rates(db)],
        "price_rules": [r.__dict__ | {k: dec(getattr(r, k)) for k in ("unit_price", "gst_pct", "qty_factor", "cost_price")}
                        for r in price_rules(db)],
    }
