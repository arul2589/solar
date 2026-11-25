"""Roof space (SPEC 6.3).

Two views:
* rule of thumb: m2 per kW (min 7.5, recommended 9-10 from the institute's 1 kW guideline)
* geometric: panels in rows, portrait, tilted; row pitch includes the shadow gap
  shadow gap = module height x sin(tilt) / tan(sun elevation)  (trigonometry sheet)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from .models import CalcSettings, PanelSpec


def rule_of_thumb_area(kw: float, s: CalcSettings) -> dict:
    return {
        "min_m2": round(kw * s.roof_min_m2_per_kw, 2),
        "recommended_m2": round(kw * s.roof_recommended_m2_per_kw, 2),
    }


def row_geometry(panel: PanelSpec, s: CalcSettings) -> dict:
    L = panel.length_mm / 1000.0
    W = panel.width_mm / 1000.0
    t = math.radians(s.tilt_deg)
    footprint = L * math.cos(t)                      # horizontal depth of one row
    rise = L * math.sin(t)                           # height of the raised edge
    elev = math.radians(s.design_sun_elevation_deg)
    shadow = rise / math.tan(elev) if elev > 0 else 0.0
    gap = max(shadow, s.min_row_gap_m)
    return {
        "module_length_m": L, "module_width_m": W, "row_depth_m": round(footprint, 4),
        "raised_edge_height_m": round(rise, 4), "shadow_length_m": round(shadow, 4),
        "row_gap_m": round(gap, 4), "row_pitch_m": round(footprint + gap, 4),
    }


@dataclass
class LayoutResult:
    roof_length_m: float
    roof_width_m: float
    rows: int
    per_row: int
    capacity: int
    placed: int
    requested: int
    fits: bool
    required_area_m2: float
    available_area_m2: float
    geometry: dict
    panels: list = field(default_factory=list)   # [(x, y, w, h)] in metres, plan view
    dims_assumed: bool = False

    def to_dict(self, include_panels: bool = False):
        d = {k: v for k, v in self.__dict__.items() if k != "panels"}
        if include_panels:
            d["panels"] = self.panels
        return d


def roof_dims(s: CalcSettings, *, length_m: Optional[float], width_m: Optional[float],
              area_m2: Optional[float]) -> tuple[float, float, bool]:
    if length_m and width_m:
        return float(length_m), float(width_m), False
    if area_m2:
        usable = area_m2 * s.usable_roof_fraction
        side = math.sqrt(usable)
        return side, side, True
    return 0.0, 0.0, True


def layout(panel: PanelSpec, count: int, s: CalcSettings, *, length_m: Optional[float] = None,
           width_m: Optional[float] = None, area_m2: Optional[float] = None) -> LayoutResult:
    """Place `count` panels on the roof. Rows run east-west along the roof width;
    successive rows step north along the roof length (array faces south)."""
    g = row_geometry(panel, s)
    rl, rw, assumed = roof_dims(s, length_m=length_m, width_m=width_m, area_m2=area_m2)
    W = g["module_width_m"]
    depth = g["row_depth_m"]
    pitch = g["row_pitch_m"]
    e = s.edge_clearance_m
    gap = s.panel_side_gap_m

    usable_w = rw - 2 * e
    usable_l = rl - 2 * e
    per_row = int(math.floor((usable_w + gap) / (W + gap) + 1e-9)) if usable_w >= W else 0
    rows = int(math.floor((usable_l - depth) / pitch + 1e-9)) + 1 if usable_l >= depth else 0
    capacity = max(0, per_row * rows)

    placed = min(count, capacity)
    panels = []
    for i in range(placed):
        r, c = divmod(i, per_row) if per_row else (0, 0)
        x = e + c * (W + gap)
        y = e + r * pitch
        panels.append((round(x, 3), round(y, 3), round(W, 3), round(depth, 3)))

    # area actually needed for `count` panels (independent of this roof)
    if count > 0:
        cols = per_row if per_row else count
        cols = max(1, min(cols, count))
        need_rows = math.ceil(count / cols)
        need_w = cols * W + (cols - 1) * gap + 2 * e
        need_l = (need_rows - 1) * pitch + depth + 2 * e
        required = round(need_w * need_l, 2)
    else:
        required = 0.0

    return LayoutResult(
        roof_length_m=round(rl, 2), roof_width_m=round(rw, 2), rows=rows, per_row=per_row,
        capacity=capacity, placed=placed, requested=count, fits=count <= capacity,
        required_area_m2=required,
        available_area_m2=round(area_m2 if (area_m2 and assumed) else rl * rw, 2),
        geometry=g, panels=panels, dims_assumed=assumed,
    )
