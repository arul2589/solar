"""String design and inverter selection (SPEC 6.4).

Voc_cold x N <= inverter max DC voltage
Vmp_hot  x N >= MPPT minimum
Isc x parallel strings on one MPPT <= MPPT max input current
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Sequence

from .models import CalcSettings, InverterSpec, PanelSpec, Warning_


def voc_at(panel: PanelSpec, cell_temp_c: float) -> float:
    return panel.voc * (1 + panel.temp_coeff_voc_pct / 100 * (cell_temp_c - 25))


def vmp_at(panel: PanelSpec, cell_temp_c: float) -> float:
    # Vmp tracks the power coefficient closely when no Vmp coefficient is published.
    return panel.vmp * (1 + panel.temp_coeff_pmax_pct / 100 * (cell_temp_c - 25))


@dataclass
class StringDesign:
    feasible: bool
    strings: list = field(default_factory=list)   # [{"mppt": 1, "modules": 5}]
    modules_per_string_min: int = 0
    modules_per_string_max: int = 0
    voc_cold_per_module: float = 0.0
    vmp_hot_per_module: float = 0.0
    vmp_cold_per_module: float = 0.0
    string_voc_cold_max: float = 0.0
    string_vmp_hot_min: float = 0.0
    string_vmp_cold_max: float = 0.0
    max_mppt_current: float = 0.0
    warnings: list = field(default_factory=list)

    def to_dict(self):
        d = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in self.__dict__.items() if k != "warnings"}
        d["warnings"] = [w.to_dict() for w in self.warnings]
        return d

    @property
    def string_count(self) -> int:
        return len(self.strings)


def series_limits(panel: PanelSpec, inv: InverterSpec, s: CalcSettings) -> tuple[int, int, float, float, float]:
    voc_c = voc_at(panel, s.design_min_cell_temp_c)
    vmp_h = vmp_at(panel, s.design_max_cell_temp_c)
    vmp_c = vmp_at(panel, s.design_min_cell_temp_c)
    n_max = int(math.floor(inv.max_dc_voltage / voc_c + 1e-9)) if voc_c > 0 else 0
    n_min = int(math.ceil(inv.mppt_min_v / vmp_h - 1e-9)) if vmp_h > 0 else 0
    return n_min, n_max, voc_c, vmp_h, vmp_c


def _split(n: int, k: int) -> list[int]:
    base, extra = divmod(n, k)
    return [base + 1 if i < extra else base for i in range(k)]


def design_strings(panel: PanelSpec, n_modules: int, inv: InverterSpec, s: CalcSettings) -> StringDesign:
    n_min, n_max, voc_c, vmp_h, vmp_c = series_limits(panel, inv, s)
    base = dict(modules_per_string_min=n_min, modules_per_string_max=n_max,
                voc_cold_per_module=voc_c, vmp_hot_per_module=vmp_h, vmp_cold_per_module=vmp_c)

    best = None
    max_strings = max(1, inv.num_mppt * 4)
    for k in range(1, max_strings + 1):
        lengths = _split(n_modules, k)
        if min(lengths) < 1:
            break
        if len(set(lengths)) > 1 and k > inv.num_mppt:
            continue  # unequal strings only when each sits on its own MPPT
        if not all(n_min <= L <= n_max for L in lengths):
            continue
        # assign strings to MPPTs round-robin
        per_mppt = [0] * inv.num_mppt
        assignment = []
        for i, L in enumerate(lengths):
            m = i % inv.num_mppt
            per_mppt[m] += 1
            assignment.append({"mppt": m + 1, "modules": L})
        max_current = max(per_mppt) * panel.isc
        if max_current > inv.max_input_current_per_mppt + 1e-9:
            continue
        best = (assignment, lengths, max_current)
        break

    if best is None:
        d = StringDesign(feasible=False, **base)
        if n_max < 1 or n_min > n_max:
            d.warnings.append(Warning_("STRING_VOLTAGE_RANGE",
                f"{panel.model} cannot form a valid string on {inv.model}: needs "
                f">= {n_min} modules for MPPT minimum but max {n_max} for DC voltage limit.", "error"))
        elif n_modules < n_min:
            d.warnings.append(Warning_("STRING_VOLTAGE_LOW",
                f"{n_modules} modules give {n_modules * vmp_h:.0f} V at {s.design_max_cell_temp_c:g} C, "
                f"below the MPPT minimum {inv.mppt_min_v:g} V of {inv.model}.", "error"))
        else:
            d.warnings.append(Warning_("STRING_DESIGN_FAILED",
                f"No string arrangement of {n_modules} modules fits {inv.model} voltage/current limits.", "error"))
        return d

    assignment, lengths, max_current = best
    d = StringDesign(
        feasible=True, strings=assignment, max_mppt_current=max_current,
        string_voc_cold_max=max(lengths) * voc_c, string_vmp_hot_min=min(lengths) * vmp_h,
        string_vmp_cold_max=max(lengths) * vmp_c, **base)
    if d.string_vmp_cold_max > inv.mppt_max_v:
        d.warnings.append(Warning_("STRING_ABOVE_MPPT",
            f"String Vmp at {s.design_min_cell_temp_c:g} C ({d.string_vmp_cold_max:.0f} V) is above the "
            f"MPPT range upper limit {inv.mppt_max_v:g} V; some clipping in cool weather.", "info"))
    return d


@dataclass
class InverterChoice:
    inverter: Optional[InverterSpec]
    dc_ac_ratio: Optional[float]
    strings: Optional[StringDesign]
    candidates_considered: int
    warnings: list = field(default_factory=list)

    def to_dict(self):
        inv = self.inverter
        return {
            "inverter": None if inv is None else {
                "id": inv.id, "model": inv.model, "ac_kw": inv.ac_kw, "phase": inv.phase, "kind": inv.kind,
                "max_dc_voltage": inv.max_dc_voltage, "mppt_min_v": inv.mppt_min_v, "mppt_max_v": inv.mppt_max_v,
                "num_mppt": inv.num_mppt, "ac_max_current": inv.ac_max_current,
            },
            "dc_ac_ratio": None if self.dc_ac_ratio is None else round(self.dc_ac_ratio, 3),
            "strings": self.strings.to_dict() if self.strings else None,
            "candidates_considered": self.candidates_considered,
        }


def allowed_phases(supply_phase: int, dc_kwp: float, s: CalcSettings) -> list[int]:
    if supply_phase == 1:
        return [1]
    # 3-phase supply: single-phase inverter allowed for small systems (quotation #276)
    return [3, 1] if dc_kwp > s.single_phase_max_kw else [1, 3]


def select_inverter(panel: PanelSpec, n_modules: int, catalogue: Sequence[InverterSpec],
                    s: CalcSettings, *, supply_phase: int = 1, kind: str = "on_grid",
                    preferred_id: Optional[int] = None) -> InverterChoice:
    dc_kw = n_modules * panel.wp / 1000
    warnings: list[Warning_] = []
    pool = [i for i in catalogue if i.kind == kind]
    if not pool:
        warnings.append(Warning_("MISSING_CATALOGUE", f"No {kind.replace('_', '-')} inverter in the catalogue.", "error"))
        return InverterChoice(None, None, None, 0, warnings)

    if preferred_id is not None:
        chosen = next((i for i in catalogue if i.id == preferred_id), None)
        if chosen:
            sd = design_strings(panel, n_modules, chosen, s)
            ratio = dc_kw / chosen.ac_kw
            warnings += _ratio_warnings(ratio, chosen, s) + _phase_warnings(chosen, supply_phase, dc_kw, s)
            warnings += sd.warnings
            return InverterChoice(chosen, ratio, sd, 1, warnings)

    phases = allowed_phases(supply_phase, dc_kw, s)
    ranked = []
    for inv in pool:
        if inv.phase not in phases:
            continue
        ratio = dc_kw / inv.ac_kw
        sd = design_strings(panel, n_modules, inv, s)
        in_range = s.dc_ac_ratio_min <= ratio <= s.dc_ac_ratio_max
        # lower score is better: feasible strings, ratio in range, preferred phase, then
        # the smallest inverter, then price
        score = (
            0 if sd.feasible else 1,
            0 if in_range else 1,
            phases.index(inv.phase),
            0 if in_range else abs(ratio - (s.dc_ac_ratio_min + s.dc_ac_ratio_max) / 2),
            inv.ac_kw,
            float(inv.price or 0),
        )
        ranked.append((score, inv, ratio, sd))
    if not ranked:
        warnings.append(Warning_("PHASE_MISMATCH",
            f"No inverter in the catalogue matches a {supply_phase}-phase supply.", "error"))
        return InverterChoice(None, None, None, 0, warnings)
    ranked.sort(key=lambda r: r[0])
    _, inv, ratio, sd = ranked[0]
    warnings += _ratio_warnings(ratio, inv, s) + _phase_warnings(inv, supply_phase, dc_kw, s) + sd.warnings
    return InverterChoice(inv, ratio, sd, len(ranked), warnings)


def _ratio_warnings(ratio: float, inv: InverterSpec, s: CalcSettings) -> list[Warning_]:
    if ratio < s.dc_ac_ratio_min:
        return [Warning_("INVERTER_OVERSIZED",
            f"{inv.model} is large for the array: DC/AC ratio {ratio:.2f} below {s.dc_ac_ratio_min:g}.", "info")]
    if ratio > s.dc_ac_ratio_max:
        return [Warning_("INVERTER_UNDERSIZED",
            f"{inv.model} is small for the array: DC/AC ratio {ratio:.2f} above {s.dc_ac_ratio_max:g}.", "warning")]
    return []


def _phase_warnings(inv: InverterSpec, supply_phase: int, dc_kw: float, s: CalcSettings) -> list[Warning_]:
    if supply_phase == 1 and inv.phase == 3:
        return [Warning_("PHASE_MISMATCH", "Three-phase inverter selected for a single-phase supply.", "error")]
    if supply_phase == 1 and dc_kw > s.single_phase_max_kw:
        return [Warning_("PHASE_MISMATCH",
            f"{dc_kw:.2f} kWp on a single-phase supply exceeds {s.single_phase_max_kw:g} kW; "
            f"a three-phase connection may be required.", "warning")]
    return []
