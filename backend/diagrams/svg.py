"""Generated diagrams (SPEC 7). Pure functions: analysis outputs (dict) in, SVG string out.
Reused by the admin UI and embedded in PDFs."""
from __future__ import annotations

from xml.sax.saxutils import escape

FONT = "font-family=\"DejaVu Sans, Arial, sans-serif\""
INK = "#1d2327"
DC = "#c0392b"
AC = "#1f4e9c"
EARTH = "#2e7d32"


def _t(x, y, s, size=12, anchor="middle", weight="normal", fill=INK) -> str:
    return (f'<text x="{x:.1f}" y="{y:.1f}" {FONT} font-size="{size}" text-anchor="{anchor}" '
            f'font-weight="{weight}" fill="{fill}">{escape(str(s))}</text>')


def _wrap(text: str, max_chars: int) -> list[str]:
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_chars:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines or [""]


def _box_height(w, lines) -> int:
    n = sum(len(_wrap(l, int((w - 14) / 6.4))) for l in lines)
    return 30 + n * 15


def _box(x, y, w, h, title, lines=(), fill="#ffffff", stroke=INK) -> str:
    """Box with a bold title; body lines wrap to the box width. h=None sizes the box to fit."""
    wrapped = [part for l in lines for part in _wrap(l, int((w - 14) / 6.4))]
    h = h or (30 + 15 * len(wrapped))
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>',
           _t(x + w / 2, y + 18, title, 13, weight="bold")]
    for i, line in enumerate(wrapped):
        out.append(_t(x + w / 2, y + 34 + i * 15, line, 11))
    return "".join(out)


def _earth(x, y) -> str:
    return (f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + 18}" stroke="{EARTH}" stroke-width="1.5"/>'
            f'<line x1="{x - 10}" y1="{y + 18}" x2="{x + 10}" y2="{y + 18}" stroke="{EARTH}" stroke-width="2"/>'
            f'<line x1="{x - 6}" y1="{y + 22}" x2="{x + 6}" y2="{y + 22}" stroke="{EARTH}" stroke-width="2"/>'
            f'<line x1="{x - 2}" y1="{y + 26}" x2="{x + 2}" y2="{y + 26}" stroke="{EARTH}" stroke-width="2"/>')


def _wire(x1, y1, x2, y2, color, label=None, dy=-6) -> str:
    out = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2.5"/>'
    if label:
        out += _t((x1 + x2) / 2, min(y1, y2) + dy, label, 10, fill=color)
    return out


def _svg(w, h, body, title) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{escape(title)}"><rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>')


def _prot(outputs: dict, location: str) -> list[str]:
    el = outputs.get("electrical") or {}
    return [f"{p['device']}: {p['rating']}" for p in el.get("protection", []) if p["location"] == location]


def single_line_diagram(outputs: dict, title: str = "") -> str:
    sz = outputs.get("sizing") or {}
    inv = (outputs.get("inverter") or {}).get("inverter") or {}
    st = (outputs.get("inverter") or {}).get("strings") or {}
    el = outputs.get("electrical") or {}
    panel = outputs.get("panel") or {}
    hybrid = outputs.get("system_kind") == "hybrid"
    battery = outputs.get("battery")
    strings = st.get("strings") or []
    W = 1120
    b = []
    b.append(_t(W / 2, 26, title or "Single-line diagram", 16, weight="bold"))
    b.append(_t(W / 2, 44, f"{sz.get('dc_kwp', '?')} kWp {'hybrid' if hybrid else 'on-grid'} rooftop PV system · "
                           f"{sz.get('panel_count', '?')} × {panel.get('wp', '?')} Wp", 12, fill="#555"))
    ys = 80
    PX, PW = 20, 250      # PV array
    DX, DW = 320, 250     # DCDB
    IX, IW = 620, 220     # inverter
    AX, AW = 890, 210     # ACDB

    arr_lines = [str(panel.get("model", ""))]
    for i, s_ in enumerate(strings[:4], start=1):
        arr_lines.append(f"String {i}: {s_['modules']} in series (MPPT {s_['mppt']})")
    if len(strings) > 4:
        arr_lines.append(f"... {len(strings)} strings total")
    arr_lines.append(f"Voc cold {st.get('string_voc_cold_max', '?')} V · Vmp hot {st.get('string_vmp_hot_min', '?')} V")
    ph = _box_height(PW, arr_lines) + 18
    b.append(_box(PX, ys, PW, ph, "PV ARRAY", arr_lines, fill="#fff8e1"))
    for i in range(min(sz.get("panel_count", 0) or 0, 10)):
        b.append(f'<rect x="{PX + 12 + i * 23}" y="{ys + ph - 14}" width="18" height="10" fill="#1f3f73" stroke="#0c1f3a"/>')

    dcdb_lines = _prot(outputs, "DCDB") or ["DC fuse, isolator, SPD"]
    dh = _box_height(DW, dcdb_lines)
    b.append(_box(DX, ys, DW, dh, "DCDB", dcdb_lines))

    inv_lines = [str(inv.get("model", "-")), f"{inv.get('ac_kw', '?')} kW AC · {inv.get('phase', '?')}-phase",
                 f"MPPT {inv.get('mppt_min_v', '?')}-{inv.get('mppt_max_v', '?')} V",
                 f"Max {inv.get('max_dc_voltage', '?')} V DC",
                 f"DC/AC ratio {(outputs.get('inverter') or {}).get('dc_ac_ratio', '?')}"]
    ih = _box_height(IW, inv_lines)
    b.append(_box(IX, ys, IW, ih, "INVERTER", inv_lines, fill="#eef4ff"))

    acdb_lines = _prot(outputs, "ACDB") or ["MCB, SPD"]
    ah = _box_height(AW, acdb_lines)
    b.append(_box(AX, ys, AW, ah, "ACDB", acdb_lines))

    row2 = ys + max(ph, dh, ih, ah) + 60
    b.append(_box(AX, row2, AW, 64, "NET METER", ["Bi-directional (TANGEDCO)", "Lockable manual isolator"], fill="#f3f3f3"))
    b.append(_box(IX, row2, IW, 64, "MAIN LT PANEL", ["Consumer loads"], fill="#f3f3f3"))
    b.append(_box(DX, row2, DW, 64, "GRID", ["TANGEDCO distribution", "230/415 V AC"], fill="#f3f3f3"))

    wy = ys + 40
    b.append(_wire(PX + PW, wy, DX, wy, DC, f"{el.get('dc_cable_mm2', '?')} sq mm"))
    b.append(_t((PX + PW + DX) / 2, wy + 16, f"{len(strings)} string(s)", 10, fill=DC))
    b.append(_wire(DX + DW, wy, IX, wy, DC, f"{el.get('dc_cable_mm2', '?')} sq mm"))
    b.append(_wire(IX + IW, wy, AX, wy, AC, f"{el.get('ac_cable_mm2', '?')} sq mm"))
    b.append(_wire(AX + AW / 2, ys + ah, AX + AW / 2, row2, AC))
    b.append(_wire(AX, row2 + 32, IX + IW, row2 + 32, AC, f"{el.get('ac_cable_mm2', '?')} sq mm"))
    b.append(_wire(IX, row2 + 32, DX + DW, row2 + 32, AC))
    for x, y in ((PX + PW / 2, ys + ph), (DX + DW / 2, ys + dh), (IX + IW / 2, ys + ih), (AX + AW - 20, ys + ah)):
        b.append(_earth(x, y))
    pits = el.get("earthing_pits", 0)
    ly = row2 + 100
    b.append(_t(20, ly, f"Earthing: {pits} pits (target < 5 ohm each); array/DC and inverter/AC earthed separately"
                        f"{'; dedicated pit for the lightning arrester' if el.get('lightning_arrester') else ''}.",
                11, anchor="start", fill=EARTH))
    if el.get("lightning_arrester"):
        b.append(f'<polygon points="{PX + PW - 20},{ys - 4} {PX + PW - 14},{ys - 16} {PX + PW - 8},{ys - 4}" '
                 f'fill="none" stroke="{EARTH}" stroke-width="1.5"/>')
        b.append(_t(PX + PW - 14, ys - 20, "LA", 10, fill=EARTH))
    ly += 20
    b.append(_t(20, ly, "Legend:", 11, anchor="start", weight="bold"))
    b.append(_wire(80, ly - 4, 110, ly - 4, DC))
    b.append(_t(116, ly, "DC", 11, anchor="start"))
    b.append(_wire(150, ly - 4, 180, ly - 4, AC))
    b.append(_t(186, ly, "AC", 11, anchor="start"))
    b.append(_earth(230, ly - 14))
    b.append(_t(248, ly, "Earth", 11, anchor="start"))
    H = ly + 20
    if hybrid:
        bl = ["Size at site"]
        if battery:
            bl = [f"{battery.get('battery_ah_rounded')} Ah @ {battery.get('battery_voltage')} V",
                  f"{battery.get('battery_kwh')} kWh"]
        by = ly + 20
        b.append(_box(IX, by, IW, None, "BATTERY BANK", bl, fill="#f1f8e9"))
        b.append(_wire(IX + 30, ys + ih, IX + 30, by, DC))
        H = by + 30 + 15 * len(bl) + 10
    return _svg(W, H, "".join(b), title or "Single-line diagram")


def roof_layout(outputs: dict, title: str = "") -> str:
    roof = outputs.get("roof") or {}
    lay = roof.get("layout") or {}
    g = lay.get("geometry") or {}
    rl, rw = float(lay.get("roof_length_m") or 0), float(lay.get("roof_width_m") or 0)
    W, H = 760, 560
    b = [_t(W / 2, 26, title or "Roof layout (plan view)", 16, weight="bold")]
    if rl <= 0 or rw <= 0:
        b.append(_t(W / 2, H / 2, "Roof dimensions not given - layout drawn at site visit.", 14, fill="#a15c00"))
        return _svg(W, H, "".join(b), "Roof layout")
    area_w, area_h = 600, 400
    scale = min(area_w / rw, area_h / rl)
    ox, oy = 80, 70
    pw, ph = rw * scale, rl * scale
    # roof (x = east-west width, y = north-south length; north at top)
    b.append(f'<rect x="{ox}" y="{oy}" width="{pw:.1f}" height="{ph:.1f}" fill="#f4f1ea" stroke="{INK}" stroke-width="2"/>')
    e = 0.3 * scale
    b.append(f'<rect x="{ox + e:.1f}" y="{oy + e:.1f}" width="{pw - 2 * e:.1f}" height="{ph - 2 * e:.1f}" fill="none" '
             f'stroke="#999" stroke-dasharray="4 4"/>')
    # panels: layout y grows from the south edge -> draw from bottom
    for (x, y, w, h) in lay.get("panels", []):
        px = ox + x * scale
        py = oy + ph - (y + h) * scale
        b.append(f'<rect x="{px:.1f}" y="{py:.1f}" width="{w * scale:.1f}" height="{h * scale:.1f}" fill="#1f3f73" '
                 f'stroke="#c9d6ea" stroke-width="0.8"/>')
    b.append(_t(ox + pw / 2, oy + ph + 22, f"{rw:.2f} m (east-west)", 12))
    b.append(f'<text x="{ox - 14}" y="{oy + ph / 2}" {FONT} font-size="12" text-anchor="middle" '
             f'transform="rotate(-90 {ox - 14} {oy + ph / 2})">{rl:.2f} m (north-south)</text>')
    # north arrow
    b.append(f'<polygon points="{W - 50},60 {W - 58},84 {W - 42},84" fill="{INK}"/>')
    b.append(_t(W - 50, 100, "N", 13, weight="bold"))
    b.append(_t(W - 50, oy + ph + 2, "S", 13, weight="bold"))
    placed, req = lay.get("placed", 0), lay.get("requested", 0)
    info = (f"{placed} of {req} panels placed · {lay.get('rows')} row(s) × {lay.get('per_row')} · tilt {roof.get('tilt_deg')}° "
            f"facing south · row pitch {g.get('row_pitch_m')} m (shadow gap {g.get('row_gap_m')} m)")
    b.append(_t(W / 2, H - 40, info, 11))
    if lay.get("dims_assumed"):
        b.append(_t(W / 2, H - 24, "Roof drawn as a square from the stated area; confirm dimensions at site.", 11, fill="#a15c00"))
    if req > placed:
        b.append(_t(W / 2, 50, f"WARNING: only {placed} of {req} panels fit on this roof.", 13, weight="bold", fill="#b42318"))
    return _svg(W, H, "".join(b), "Roof layout")


def cable_schedule(outputs: dict, title: str = "") -> str:
    el = outputs.get("electrical") or {}
    cables = el.get("cable_schedule") or []
    prot = el.get("protection") or []
    W = 1000
    row_h = 20
    H = 90 + row_h * (len(cables) + len(prot) + 3)
    b = [_t(W / 2, 26, title or "Cable and protection schedule", 16, weight="bold")]
    y = 54
    cols = [(20, "From"), (330, "To"), (560, "Size"), (640, "Cores"), (720, "Length"), (800, "Type")]
    for x, h in cols:
        b.append(_t(x, y, h, 11, anchor="start", weight="bold"))
    b.append(f'<line x1="16" y1="{y + 5}" x2="{W - 16}" y2="{y + 5}" stroke="{INK}"/>')
    for c in cables:
        y += row_h
        vals = [c["from"], c["to"], f"{c['size_mm2']:g} sq mm" if c.get("size_mm2") else "-", c.get("cores", ""),
                f"{c['length_m']:g} m" if c.get("length_m") is not None else "as req.", c.get("type", "")]
        for (x, _), v in zip(cols, vals):
            b.append(_t(x, y, str(v)[:44], 10.5, anchor="start"))
    y += row_h + 10
    b.append(_t(20, y, "Protection devices", 12, anchor="start", weight="bold"))
    y += 6
    b.append(f'<line x1="16" y1="{y}" x2="{W - 16}" y2="{y}" stroke="{INK}"/>')
    for p in prot:
        y += row_h
        b.append(_t(20, y, p["location"], 10.5, anchor="start"))
        b.append(_t(160, y, p["device"], 10.5, anchor="start"))
        b.append(_t(560, y, p["rating"], 10.5, anchor="start"))
        b.append(_t(900, y, f"qty {p['qty']}", 10.5, anchor="start"))
    if not cables:
        b.append(_t(W / 2, 90, "No electrical design (no feasible inverter/string arrangement).", 12, fill="#b42318"))
    return _svg(W, max(H, 140), "".join(b), "Cable and protection schedule")


GENERATORS = {"sld": single_line_diagram, "roof": roof_layout, "schedule": cable_schedule}
