"""Cables and protection (SPEC 6.5).

Basic formulas: P = V x I; series strings add voltage, parallel strings add current.
Voltage drop (DC, and AC single phase) = 2 x L x I x rho / A
Voltage drop (AC three phase)          = sqrt(3) x L x I x rho / A
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from .models import CalcSettings, InverterSpec, PanelSpec, Warning_
from .strings import StringDesign


def vdrop_pct(length_m: float, current_a: float, area_mm2: float, voltage_v: float,
              rho: float, three_phase: bool = False) -> float:
    if voltage_v <= 0 or area_mm2 <= 0:
        return 0.0
    k = math.sqrt(3) if three_phase else 2.0
    return k * length_m * current_a * rho / area_mm2 / voltage_v * 100


def pick_cable(sizes, ampacity: dict, design_current: float, length_m: float, op_current: float,
               voltage: float, max_pct: float, rho: float, three_phase: bool = False) -> tuple[Optional[float], float]:
    for size in sorted(sizes):
        amp = ampacity.get(size) or ampacity.get(float(size))
        if amp is None or amp < design_current:
            continue
        pct = vdrop_pct(length_m, op_current, size, voltage, rho, three_phase)
        if pct <= max_pct:
            return size, pct
    largest = max(sizes)
    return None, vdrop_pct(length_m, op_current, largest, voltage, rho, three_phase)


def next_rating(value: float, ratings) -> Optional[float]:
    for r in sorted(ratings):
        if r >= value - 1e-9:
            return r
    return None


@dataclass
class ElectricalDesign:
    cable_schedule: list = field(default_factory=list)
    protection: list = field(default_factory=list)
    dc_cable_mm2: Optional[float] = None
    ac_cable_mm2: Optional[float] = None
    dc_cable_total_m: float = 0.0
    ac_cable_total_m: float = 0.0
    earthing_pits: int = 0
    lightning_arrester: bool = True
    la_cable_m: float = 0.0
    warnings: list = field(default_factory=list)

    def to_dict(self):
        d = {k: v for k, v in self.__dict__.items() if k != "warnings"}
        d["warnings"] = [w.to_dict() for w in self.warnings]
        return d


def design_electrical(panel: PanelSpec, inv: InverterSpec, sd: StringDesign, s: CalcSettings, *,
                      dc_run_one_way_m: Optional[float] = None, ac_run_m: Optional[float] = None,
                      lightning_arrester: Optional[bool] = None, inverter_count: int = 1) -> ElectricalDesign:
    warnings: list[Warning_] = []
    one_way = dc_run_one_way_m if dc_run_one_way_m is not None else s.dc_run_one_way_m
    ac_len = ac_run_m if ac_run_m is not None else s.ac_run_m
    la = s.lightning_arrester_default if lightning_arrester is None else lightning_arrester
    sf = s.current_safety_factor
    rho = s.copper_resistivity

    # ---- DC: per string -------------------------------------------------------
    string_design_current = panel.isc * sf
    string_vmp = max(1.0, sd.vmp_hot_per_module * min((st["modules"] for st in sd.strings), default=1))
    dc_size, dc_pct = pick_cable(s.dc_cable_sizes_mm2, s.dc_cable_ampacity, string_design_current,
                                 one_way, panel.imp, string_vmp, s.dc_vdrop_max_pct, rho)
    if dc_size is None:
        dc_size = max(s.dc_cable_sizes_mm2)
        warnings.append(Warning_("DC_VDROP_HIGH",
            f"DC voltage drop {dc_pct:.2f}% exceeds {s.dc_vdrop_max_pct:g}% even with {dc_size:g} sq mm; "
            f"shorten the run or use a larger cable.", "warning"))

    schedule = []
    total_dc = 0.0
    for i, st in enumerate(sd.strings, start=1):
        length = 2 * one_way
        total_dc += length
        where = f"inverter {st.get('inverter', 1)} MPPT {st['mppt']}" if inverter_count > 1 else f"MPPT {st['mppt']}"
        schedule.append({"from": f"String {i} ({where}, {st['modules']} modules)", "to": "DCDB",
                         "size_mm2": dc_size, "cores": "2 x 1C", "length_m": round(length, 1),
                         "type": "Solar DC cable (UV resistant, MC4 terminated)",
                         "current_a": round(panel.imp, 2), "vdrop_pct": round(dc_pct, 2)})
    mppt_current = {}
    for st in sd.strings:
        key = (st.get("inverter", 1), st["mppt"])
        mppt_current[key] = mppt_current.get(key, 0) + panel.imp
    if s.dcdb_to_inverter_m > 0:
        for (u, m), cur in sorted(mppt_current.items()):
            length = 2 * s.dcdb_to_inverter_m
            total_dc += length
            to = f"Inverter {u} MPPT {m}" if inverter_count > 1 else f"Inverter MPPT {m}"
            schedule.append({"from": "DCDB", "to": to, "size_mm2": dc_size, "cores": "2 x 1C",
                             "length_m": round(length, 1), "type": "Solar DC cable",
                             "current_a": round(cur, 2), "vdrop_pct": None})

    # ---- AC ---------------------------------------------------------------------
    three = inv.phase == 3
    v_ac = s.ac_voltage_3ph if three else s.ac_voltage_1ph
    ac_design = inv.ac_max_current * sf
    n_inv = max(1, inverter_count)
    total_ac_len = n_inv * s.inverter_to_acdb_m + ac_len
    out_current = inv.ac_max_current * n_inv
    ac_size, ac_pct = pick_cable(s.ac_cable_sizes_mm2, s.ac_cable_ampacity, out_current * sf,
                                 s.inverter_to_acdb_m + ac_len, out_current, v_ac, s.ac_vdrop_max_pct, rho, three)
    if ac_size is None:
        ac_size = max(s.ac_cable_sizes_mm2)
        warnings.append(Warning_("AC_VDROP_HIGH",
            f"AC voltage drop {ac_pct:.2f}% exceeds {s.ac_vdrop_max_pct:g}%.", "warning"))
    unit_size = ac_size
    if n_inv > 1:
        unit_size, _ = pick_cable(s.ac_cable_sizes_mm2, s.ac_cable_ampacity, ac_design, s.inverter_to_acdb_m,
                                  inv.ac_max_current, v_ac, 100.0, rho, three)
        unit_size = unit_size or ac_size
    cores = "4C" if three else "2C"
    for u in range(1, n_inv + 1):
        schedule.append({"from": f"Inverter {u} AC output" if n_inv > 1 else "Inverter AC output", "to": "ACDB",
                         "size_mm2": unit_size, "cores": cores,
                         "length_m": round(s.inverter_to_acdb_m, 1), "type": "Cu PVC insulated AC cable",
                         "current_a": round(inv.ac_max_current, 2), "vdrop_pct": None})
    schedule.append({"from": "ACDB", "to": "Main LT panel / net meter", "size_mm2": ac_size, "cores": cores,
                     "length_m": round(ac_len, 1), "type": "Cu PVC insulated AC cable",
                     "current_a": round(out_current, 2), "vdrop_pct": round(ac_pct, 2)})

    # ---- earthing ---------------------------------------------------------------
    pits = s.earthing_pits_min + (1 if la else 0)
    schedule.append({"from": "Array structure / module frames", "to": "Earth pit 1 (DC)",
                     "size_mm2": s.earth_conductor_mm2, "cores": "1C", "length_m": None,
                     "type": "Cu earth conductor", "current_a": None, "vdrop_pct": None})
    schedule.append({"from": "Inverter / ACDB body", "to": "Earth pit 2 (AC)",
                     "size_mm2": s.earth_conductor_mm2, "cores": "1C", "length_m": None,
                     "type": "Cu earth conductor", "current_a": None, "vdrop_pct": None})
    if la:
        schedule.append({"from": "Lightning arrester", "to": f"Earth pit {pits} (LA, dedicated)",
                         "size_mm2": s.la_conductor_mm2, "cores": "1C", "length_m": s.la_cable_m,
                         "type": "Cu LA down conductor", "current_a": None, "vdrop_pct": None})

    # ---- protection -------------------------------------------------------------
    voc_string = sd.string_voc_cold_max
    dc_class = next_rating(voc_string * 1.0, s.dc_device_voltage_classes) or max(s.dc_device_voltage_classes)
    protection = []
    fuse = next_rating(panel.isc * sf, s.dc_fuse_ratings_a)
    protection.append({"location": "DCDB", "device": "DC fuse per string (+ and -)",
                       "rating": f"{fuse or '?'} A, {dc_class} V DC", "qty": 2 * len(sd.strings)})
    max_mppt_i = max(mppt_current.values(), default=0) / panel.imp * panel.isc if panel.imp else 0
    iso = next_rating(max_mppt_i * sf, s.standard_breaker_ratings_a)
    protection.append({"location": "DCDB", "device": "DC isolator / MCB (per MPPT)",
                       "rating": f"{iso or '?'} A, {dc_class} V DC", "qty": len(mppt_current)})
    protection.append({"location": "DCDB", "device": "DC SPD Type 2",
                       "rating": f"Ucpv >= {voc_string * 1.2:.0f} V ({dc_class} V class)", "qty": len(mppt_current)})
    mcb = next_rating(out_current * sf, s.standard_breaker_ratings_a)
    if n_inv > 1:
        unit_mcb = next_rating(ac_design, s.standard_breaker_ratings_a)
        protection.append({"location": "ACDB", "device": f"AC MCB {'4P' if three else '2P'} per inverter",
                           "rating": f"{unit_mcb or '?'} A, C-curve", "qty": n_inv})
    protection.append({"location": "ACDB", "device": f"AC {'MCCB' if (mcb or 999) > 63 else 'MCB'} "
                                                     f"{'4P' if three else '2P'}{' outgoing' if n_inv > 1 else ''}",
                       "rating": f"{mcb or '?'} A, C-curve", "qty": 1})
    protection.append({"location": "ACDB", "device": "AC SPD Type 2",
                       "rating": f"Uc {'385' if three else '275'} V", "qty": 1})
    protection.append({"location": "Ground floor", "device": "Manual AC isolator with locking (TANGEDCO)",
                       "rating": f"{mcb or '?'} A", "qty": 1})
    protection.append({"location": "Earthing", "device": "Earth pits (chemical, Cu bonded electrode)",
                       "rating": f"< {s.earth_resistance_target_ohm:g} ohm each", "qty": pits})
    if la:
        protection.append({"location": "Roof", "device": "Lightning arrester (ESE / multi-spike)",
                           "rating": "Cu bonded", "qty": 1})
    if fuse is None or iso is None or mcb is None:
        warnings.append(Warning_("PROTECTION_RATING", "A protection rating is outside the configured standard ratings.", "warning"))

    return ElectricalDesign(
        cable_schedule=schedule, protection=protection, dc_cable_mm2=dc_size, ac_cable_mm2=ac_size,
        dc_cable_total_m=round(total_dc, 1), ac_cable_total_m=round(total_ac_len, 1), earthing_pits=pits,
        lightning_arrester=la, la_cable_m=s.la_cable_m if la else 0.0, warnings=warnings)
