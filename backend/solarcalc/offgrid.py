"""Off-grid / hybrid sizing (SPEC 6.4), formulas from the institute's
'CALCULATIONS AND FORMULA BATTERY, INVERTER, CHARGER CONTROLLER SELECTION' sheet.

Battery Ah          = load W x backup h / (system V x efficiency)   [/ DoD for usable capacity]
Inverter VA         = load W x safety margin / power factor
Charge controller A = array W / battery V x safety factor
Backup time h       = Ah x V x efficiency / load W
"""
from __future__ import annotations

import math

from .models import CalcSettings


def battery_ah(load_w: float, backup_h: float, system_v: float, efficiency: float, dod: float = 1.0) -> float:
    if system_v <= 0 or efficiency <= 0 or dod <= 0:
        raise ValueError("voltage, efficiency and DoD must be positive")
    return load_w * backup_h / (system_v * efficiency) / dod


def inverter_va(load_w: float, safety: float, pf: float) -> float:
    return load_w * safety / pf


def charge_controller_a(array_w: float, battery_v: float, safety: float) -> float:
    return array_w / battery_v * safety


def backup_hours(ah: float, v: float, efficiency: float, load_w: float) -> float:
    return ah * v * efficiency / load_w


def offgrid_design(load_w: float, array_w: float, s: CalcSettings, *, backup_h: float | None = None,
                   battery_v: float | None = None) -> dict:
    h = backup_h if backup_h is not None else s.default_backup_hours
    v = battery_v if battery_v is not None else s.default_battery_voltage
    ah = battery_ah(load_w, h, v, s.battery_efficiency, s.battery_dod)
    return {
        "load_w": load_w, "backup_hours": h, "battery_voltage": v,
        "battery_ah": round(ah, 1), "battery_ah_rounded": int(math.ceil(ah / 10.0) * 10),
        "battery_kwh": round(ah * v / 1000, 2),
        "inverter_va": round(inverter_va(load_w, s.inverter_va_safety, s.inverter_power_factor), 0),
        "charge_controller_a": round(charge_controller_a(array_w, v, s.charge_controller_safety), 1),
    }
