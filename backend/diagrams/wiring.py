"""Detailed wiring diagram: every module and string, DCDB devices, inverter ports, battery / backup
board (hybrid), ACDB, main panel, net meter, EB supply, lightning arrester and the earth pits.

Pure function of the engine's analysis outputs, like the other diagrams: no AI, same input -> same drawing.
Two colour themes: "dark" (screen, like a wiring poster) and "light" (print / PDF).
"""
from __future__ import annotations

from xml.sax.saxutils import escape

FONT = 'font-family="Segoe UI, DejaVu Sans, Arial, sans-serif"'

THEMES = {
    "dark": {
        "bg": "#151515", "ink": "#ececE6", "muted": "#a8a8a2", "box": "#3a3a37", "box_line": "#5d5d58",
        "panel": "#123f78", "panel_line": "#2f73c9", "panel_ink": "#9ccaff", "frame": "#8a8a85",
        "dc_chip": "#6b3a06", "dc_line": "#e0902a", "dc_ink": "#ffbf66",
        "ac_chip": "#0b5345", "ac_line": "#2fbf95", "ac_ink": "#86f2cf",
        "dcdb": "#1f1f1e", "pos": "#e45555", "neg": "#ececE6", "earth": "#6aa121", "note": "#1f1f1e",
    },
    "light": {
        "bg": "#ffffff", "ink": "#1d2327", "muted": "#5f6b73", "box": "#f2f2ef", "box_line": "#8c8c86",
        "panel": "#dbe9fb", "panel_line": "#2f6fc0", "panel_ink": "#123f78", "frame": "#8c8c86",
        "dc_chip": "#fff1dc", "dc_line": "#c97a12", "dc_ink": "#7a4300",
        "ac_chip": "#dcf5ec", "ac_line": "#1f9e78", "ac_ink": "#0b5345",
        "dcdb": "#fafafa", "pos": "#c62828", "neg": "#37474f", "earth": "#2e7d32", "note": "#fafafa",
    },
}


class _D:
    """Tiny SVG builder bound to a theme."""

    def __init__(self, theme: str):
        self.c = THEMES.get(theme, THEMES["dark"])
        self.parts: list[str] = []

    def add(self, s: str) -> None:
        self.parts.append(s)

    def text(self, x, y, s, size=14, anchor="middle", weight="normal", fill=None) -> None:
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" {FONT} font-size="{size}" text-anchor="{anchor}" '
                 f'font-weight="{weight}" fill="{fill or self.c["ink"]}">{escape(str(s))}</text>')

    def rect(self, x, y, w, h, fill, stroke, rx=8, dash=False, sw=1.5) -> None:
        d = ' stroke-dasharray="7 6"' if dash else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def path(self, pts, color, width=2.5, arrow=False) -> None:
        d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        m = ' marker-end="url(#arr)"' if arrow else ""
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"{m}/>')

    def box(self, x, y, w, h, title, sub=(), fill=None, line=None, ink=None, title_size=18) -> None:
        self.rect(x, y, w, h, fill or self.c["box"], line or self.c["box_line"])
        n = len(sub)
        ty = y + h / 2 - (n * 9) + (6 if n == 0 else 0)
        self.text(x + w / 2, ty + (0 if n else 0), title, title_size, weight="bold", fill=ink)
        for i, s in enumerate(sub):
            self.text(x + w / 2, ty + 24 + i * 19, s, 13, fill=ink or self.c["muted"])

    def chip(self, x, y, w, h, label, kind) -> None:
        f, l, k = (self.c["dc_chip"], self.c["dc_line"], self.c["dc_ink"]) if kind == "dc" else \
                  (self.c["ac_chip"], self.c["ac_line"], self.c["ac_ink"])
        self.rect(x, y, w, h, f, l, rx=4)
        self.text(x + w / 2, y + h / 2 + 6, label, 17, fill=k)

    def ground(self, x, y) -> None:
        c = self.c["muted"]
        for i, half in enumerate((20, 13, 6)):
            yy = y + i * 7
            self.add(f'<line x1="{x - half}" y1="{yy}" x2="{x + half}" y2="{yy}" stroke="{c}" stroke-width="2.5"/>')


def _wrap(text: str, n: int) -> list[str]:
    words, out, cur = str(text).split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > n:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return out + ([cur] if cur else [])


def _find(items, location, starts):
    for p in items:
        if p.get("location") == location and str(p.get("device", "")).startswith(starts):
            return p
    return None


def _num(v, fmt="{:g}"):
    try:
        return fmt.format(float(v))
    except (TypeError, ValueError):
        return "?"


def wiring_diagram(outputs: dict, title: str = "", theme: str = "dark") -> str:
    d = _D(theme)
    c = d.c
    sz = outputs.get("sizing") or {}
    panel = outputs.get("panel") or {}
    inv_choice = outputs.get("inverter") or {}
    inv = inv_choice.get("inverter") or {}
    st = inv_choice.get("strings") or {}
    strings = st.get("strings") or []
    n_inv = int(inv_choice.get("count") or 1)
    el = outputs.get("electrical") or {}
    prot = el.get("protection") or []
    sched = el.get("cable_schedule") or []
    roof = outputs.get("roof") or {}
    hybrid = outputs.get("system_kind") == "hybrid"
    battery = outputs.get("battery") or {}
    three = int(inv.get("phase") or 1) == 3
    la = bool(el.get("lightning_arrester"))
    wp = panel.get("wp", "?")

    W = 1400
    # ------------------------------------------------------------------ header
    head = title or "Wiring diagram"
    d.text(40, 40, head, 24, anchor="start", weight="bold")
    kind = "hybrid (with battery)" if hybrid else "on-grid (net metering)"
    d.text(40, 66, f"{sz.get('dc_kwp', '?')} kWp {kind} · {sz.get('panel_count', '?')} × {wp} Wp · "
                   f"{len(strings)} string(s){f' · {n_inv} inverters' if n_inv > 1 else ''}",
           15, anchor="start", fill=c["muted"])

    # ------------------------------------------------------------------ PV array
    # Each string is drawn as a "snake": long strings wrap onto more rows joined at the end, like site drawings.
    all_strings = strings or [{"mppt": 1, "modules": sz.get("panel_count") or 1}]
    long_strings = max(int(x["modules"]) for x in all_strings) > 10
    MW, MH, GAP = (74, 40, 12) if long_strings else (92, 46, 16)
    ax0, ay0 = 410, 132
    avail = (W - 360 - 60) - ax0
    per_row_max = max(2, int((avail + GAP) // (MW + GAP)))
    plan, used_rows = [], 0
    for s_ in all_strings:
        n = int(s_["modules"])
        nrows = -(-n // per_row_max)
        if plan and used_rows + nrows > 6:
            break
        per = -(-n // nrows)
        plan.append((s_, n, nrows, per))
        used_rows += nrows
    widest = max(p_[3] for p_ in plan)
    row_w = widest * MW + (widest - 1) * GAP
    pitch = MH + 26
    label_h = 22
    arr_h = 20 + sum(label_h + nr * pitch for _, _, nr, _ in plan) + (22 if len(plan) < len(all_strings) else 0)
    d.rect(ax0 - 24, ay0 - 14, row_w + 48, arr_h, "none", c["frame"], rx=10, dash=True)
    d.text(ax0 + row_w / 2, ay0 - 26, f"{sz.get('panel_count', '?')} × {wp} W · "
                                      f"{', '.join(str(r['modules']) for r in all_strings[:6])} in series",
           17, fill=c["muted"])
    ends = []   # (plus_xy, minus_xy, minus_side) per drawn string
    y = ay0 + 8
    for si, (s_, n, nrows, per) in enumerate(plan):
        d.text(ax0, y + 12, f"String {si + 1} · MPPT {s_.get('mppt', 1)} · {n} modules in series", 12,
               anchor="start", fill=c["muted"])
        y += label_h
        k = 0
        first = last = None
        for r in range(nrows):
            cnt = min(per, n - k)
            ltr = (r % 2 == 0)
            ry = y + r * pitch
            xs = [ax0 + j * (MW + GAP) for j in range(cnt)]
            if not ltr:
                xs = [ax0 + (per - 1 - j) * (MW + GAP) for j in range(cnt)]
            for j, x in enumerate(xs):
                d.rect(x, ry, MW, MH, c["panel"], c["panel_line"], rx=3)
                d.text(x + MW / 2, ry + MH / 2 + 5, f"{wp}W", 13 if long_strings else 15, fill=c["panel_ink"])
                if j:
                    a, b_ = sorted((xs[j - 1], x))
                    d.path([(a + MW, ry + MH / 2), (b_, ry + MH / 2)], c["frame"], 2)
            if first is None:
                first = (xs[0], ry + MH / 2)
            if r < nrows - 1:   # row-to-row series link at the turning end
                edge = (xs[-1] + MW) if ltr else xs[-1]
                off = 12 if ltr else -12
                d.path([(edge, ry + MH / 2), (edge + off, ry + MH / 2), (edge + off, ry + pitch + MH / 2),
                        (edge, ry + pitch + MH / 2)], c["frame"], 2)
            last_xs, last_ltr, last_y = xs, ltr, ry + MH / 2
            k += cnt
        minus = (last_xs[-1] + MW, last_y, "right") if last_ltr else (last_xs[-1], last_y, "left")
        ends.append((first, minus))
        y += nrows * pitch
    if len(plan) < len(all_strings):
        d.text(ax0 + row_w / 2, y + 12, f"+ {len(all_strings) - len(plan)} more string(s) wired the same way",
               13, fill=c["muted"])
    arr_bottom = ay0 - 14 + arr_h

    # ------------------------------------------------------------------ notes box
    dc_run = next((r for r in sched if str(r.get("from", "")).startswith("String")), {})
    ac_run = next((r for r in sched if r.get("from") == "ACDB"), {})
    earth = next((r for r in sched if "Earth pit 1" in str(r.get("to", ""))), {})
    la_run = next((r for r in sched if r.get("from") == "Lightning arrester"), {})
    pits = _find(prot, "Earthing", "Earth pits") or {}
    notes = [
        f"Panel: {panel.get('model', '?')}",
        f"String Voc (cold) {st.get('string_voc_cold_max', '?')} V · Vmp (hot) {st.get('string_vmp_hot_min', '?')} V",
        f"DC cable {_num(el.get('dc_cable_mm2'))} mm² solar · {_num(dc_run.get('length_m'))} m per string",
        f"AC cable {_num(el.get('ac_cable_mm2'))} mm² {ac_run.get('cores', '')} · {_num(ac_run.get('length_m'))} m",
        f"Earth {_num(earth.get('size_mm2'))} mm² Cu · {pits.get('qty', el.get('earthing_pits', '?'))} pits, "
        f"{pits.get('rating', '< 5 ohm each')}",
        f"Structure tilt {roof.get('tilt_deg', '?')}°, facing {roof.get('direction') or 'south'}",
    ]
    wrapped = [w for n in notes for w in _wrap(n, 38)]
    nx, ny, nw = W - 360, 96, 320
    nh = 30 + len(wrapped) * 24
    d.rect(nx, ny, nw, nh, c["note"], c["box_line"], rx=10)
    for i, line in enumerate(wrapped):
        d.text(nx + 22, ny + 36 + i * 24, line, 15, anchor="start")

    # ------------------------------------------------------------------ row 2: DCDB, inverter, ACDB
    r2 = max(arr_bottom, ny + nh) + 150
    fuse = _find(prot, "DCDB", "DC fuse") or {}
    spd = _find(prot, "DCDB", "DC SPD") or {}
    iso = _find(prot, "DCDB", "DC isolator") or {}
    dc_rows = [f"Fuse ×{fuse.get('qty', '?')}: {fuse.get('rating', '?')}",
               f"SPD: {spd.get('rating', '?')}",
               f"MCB / isolator ×{iso.get('qty', '?')}: {iso.get('rating', '?')}"]
    DX, DWID = 250, 420
    dh = 120 + 20 * len(dc_rows)
    d.rect(DX, r2, DWID, dh, c["dcdb"], c["box_line"], rx=10)
    d.text(DX + DWID / 2, r2 + 34, "DCDB", 22, weight="bold")
    chip_w, chip_h, cy = 118, 52, r2 + 52
    chips_x = [DX + 22 + k * (chip_w + 16) for k in range(3)]
    for x, lab in zip(chips_x, ("Fuse", "SPD", "MCB")):
        d.chip(x, cy, chip_w, chip_h, lab, "dc")
    for i, t in enumerate(dc_rows):
        d.text(DX + 22, cy + chip_h + 28 + i * 20, t, 12.5, anchor="start", fill=c["muted"])

    IX, IW = 720, 250
    ih = max(dh, 220)
    d.rect(IX, r2 - 20, IW, ih + 20, c["box"], c["box_line"], rx=10)
    d.text(IX + IW / 2, r2 + 14, "Inverter" + (f" ×{n_inv}" if n_inv > 1 else ""), 22, weight="bold")
    d.text(IX + IW / 2, r2 + 40, f"{_num(inv.get('ac_kw'))} kW {'hybrid' if hybrid else 'on-grid'} · "
                                 f"{inv.get('phase', '?')}-phase", 15, fill=c["muted"])
    for i, line in enumerate(_wrap(inv.get("model", ""), 28)[:2]):
        d.text(IX + IW / 2, r2 + 62 + i * 18, line, 12.5, fill=c["muted"])
    pv_y = r2 + 110
    d.text(IX + 16, pv_y + 6, "PV", 15, anchor="start", fill=c["muted"])
    d.text(IX + IW - 16, pv_y + 6, "GRID", 15, anchor="end", fill=c["muted"])
    ib = r2 + ih
    if hybrid:
        d.text(IX + 34, ib - 16, "BAT", 15, anchor="start", fill=c["muted"])
        d.text(IX + IW - 14, ib - 16, "LOAD", 15, anchor="end", fill=c["muted"])

    AXX, AW = 1020, 330
    ah = dh
    acmcb = next((p for p in prot if p.get("location") == "ACDB" and "MC" in str(p.get("device", ""))
                  and "per inverter" not in str(p.get("device", ""))), {})
    acspd = _find(prot, "ACDB", "AC SPD") or {}
    ac_rows = [f"{str(acmcb.get('device', 'MCB')).replace('AC ', '')}: {acmcb.get('rating', '?')}",
               f"SPD: {acspd.get('rating', '?')}", "TB: terminal block for the outgoing cable"]
    d.rect(AXX, r2, AW, ah, c["dcdb"], c["box_line"], rx=10)
    d.text(AXX + AW / 2, r2 + 34, "ACDB", 22, weight="bold")
    achips = [AXX + 22 + k * (92 + 12) for k in range(3)]
    for x, lab in zip(achips, ("MCB", "SPD", "TB")):
        d.chip(x, cy, 92, chip_h, lab, "ac")
    for i, t in enumerate(ac_rows):
        d.text(AXX + 22, cy + chip_h + 28 + i * 20, t, 12.5, anchor="start", fill=c["muted"])

    # ------------------------------------------------------------------ DC wiring: strings -> DCDB
    for i, ((px, py_), (mx_, my_, side)) in enumerate(ends):
        red_x = DX + 100 - i * 12
        d.path([(px, py_), (red_x, py_), (red_x, r2)], c["pos"])
        white_x = DX + 170 + i * 12
        if side == "left":
            d.path([(mx_, my_), (white_x, my_), (white_x, r2)], c["neg"])
        else:
            gap_y = arr_bottom + 30 + i * 10
            d.path([(mx_, my_), (mx_ + 16 + i * 6, my_), (mx_ + 16 + i * 6, gap_y), (white_x, gap_y), (white_x, r2)],
                   c["neg"])
    d.text(DX + 180 + len(ends) * 12, r2 - 24, f"{_num(el.get('dc_cable_mm2'))} mm² DC", 13, anchor="start",
           fill=c["muted"])
    # DCDB -> inverter PV, inverter GRID -> ACDB
    d.path([(DX + DWID, pv_y - 10), (IX, pv_y - 10)], c["pos"])
    d.path([(DX + DWID, pv_y + 10), (IX, pv_y + 10)], c["neg"])
    d.path([(IX + IW, pv_y - 10), (AXX, pv_y - 10)], c["pos"])
    d.path([(IX + IW, pv_y + 10), (AXX, pv_y + 10)], c["neg"])
    d.text((IX + IW + AXX) / 2, pv_y - 20, "3P+N" if three else "L / N", 12, fill=c["muted"])

    # ------------------------------------------------------------------ row 3/4
    r3 = r2 + max(ah, ih) + 90
    bottom = r3
    if hybrid:
        bx, bw, bh = 470, 220, 96
        bat_lines = ([f"{battery.get('battery_voltage')}V, {battery.get('battery_kwh')} kWh",
                      f"{battery.get('battery_ah_rounded')} Ah"] if battery else ["size at site"])
        d.box(bx, r3, bw, bh, "Battery", bat_lines, fill=c["dc_chip"], line=c["dc_line"], ink=c["dc_ink"])
        d.path([(IX + 40, ib), (IX + 40, r3 + 30), (bx + bw, r3 + 30)], c["pos"])
        d.path([(IX + 64, ib), (IX + 64, r3 + 66), (bx + bw, r3 + 66)], c["neg"])
        kx, kw = 862, 150
        d.box(kx, r3, kw, 96, "Backup DB", ["MCB, RCCB"], fill=c["ac_chip"], line=c["ac_line"], ink=c["ac_ink"])
        d.path([(IX + IW - 50, ib), (IX + IW - 50, r3)], c["pos"])
        d.path([(IX + IW - 30, ib), (IX + IW - 30, r3)], c["neg"])
        d.box(kx, r3 + 150, kw, 70, "Backup loads", [], fill=c["ac_chip"], line=c["ac_line"], ink=c["ac_ink"])
        d.path([(kx + kw / 2, r3 + 96), (kx + kw / 2, r3 + 146)], c["muted"], 2, arrow=True)
        bottom = max(bottom, r3 + 220)

    mx, mw = 1080, 270
    d.box(mx, r3, mw, 96, "Main LT panel", ["house / building loads"], fill=c["ac_chip"], line=c["ac_line"],
          ink=c["ac_ink"])
    d.path([(AXX + 230, r2 + ah), (AXX + 230, r3)], c["pos"])
    d.path([(AXX + 260, r2 + ah), (AXX + 260, r3)], c["neg"])
    d.text(AXX + 270, r2 + ah + 40, f"{_num(el.get('ac_cable_mm2'))} mm²", 12, anchor="start", fill=c["muted"])
    iso_gf = _find(prot, "Ground floor", "Manual AC isolator") or {}
    r4 = r3 + 150
    d.box(mx, r4, 160, 96, "Net meter", ["bi-directional", f"isolator {iso_gf.get('rating', '')}".strip()],
          fill=c["ac_chip"], line=c["ac_line"], ink=c["ac_ink"], title_size=17)
    d.path([(mx + 60, r3 + 96), (mx + 60, r4)], c["pos"])
    d.path([(mx + 90, r3 + 96), (mx + 90, r4)], c["neg"])
    d.box(mx + 190, r4, 80, 96, "EB", ["grid"], title_size=17)
    d.path([(mx + 160, r4 + 36), (mx + 190, r4 + 36)], c["pos"])
    d.path([(mx + 160, r4 + 60), (mx + 190, r4 + 60)], c["neg"])
    bottom = max(bottom, r4 + 96)

    # ------------------------------------------------------------------ earthing
    py = bottom + 90
    pit_h = 70
    lpx, dpx, apx = 40, 230, 760
    if la:
        d.box(lpx, py, 160, pit_h, "LA pit", [])
        d.ground(lpx + 80, py + pit_h + 16)
        lx = lpx + 80
        d.add(f'<circle cx="{lx}" cy="120" r="9" fill="none" stroke="{c["ink"]}" stroke-width="2.5"/>')
        d.path([(lx, 129), (lx, 330)], c["muted"], 4)
        d.text(lx + 22, 128, "LA", 22, anchor="start", weight="bold")
        d.path([(lx, 330), (lx, py)], c["earth"])
        d.text(lx + 14, 460, f"{_num(la_run.get('size_mm2'))} mm²", 15, anchor="start")
    d.box(dpx, py, 180, pit_h, "DC earth", [])
    d.ground(dpx + 90, py + pit_h + 16)
    d.box(apx, py, 180, pit_h, "AC earth", [])
    d.ground(apx + 90, py + pit_h + 16)
    # module frames / structure -> DC earth
    fx = ax0 + row_w / 2
    gy2 = arr_bottom + 40 + len(ends) * 10 + 20
    d.path([(fx, arr_bottom), (fx, gy2), (dpx + 14, gy2), (dpx + 14, py)], c["earth"])
    # DC SPD -> DC earth
    d.path([(DX + 60, r2 + dh), (DX + 60, py)], c["earth"])
    d.text(DX + 68, r2 + dh + 22, "SPD + body", 12, anchor="start", fill=c["earth"])
    # inverter body -> AC earth
    d.path([(IX + IW / 2 - 20, ib), (IX + IW / 2 - 20, py)], c["earth"])
    # ACDB SPD -> AC earth
    ey = py - 40
    d.path([(AXX + 16, r2 + ah), (AXX + 16, ey), (apx + 150, ey), (apx + 150, py)], c["earth"])
    d.text(AXX + 24, r2 + ah + 22, "SPD + body", 12, anchor="start", fill=c["earth"])
    # separation note between pits
    d.add(f'<path d="M {dpx + 190} {py + pit_h / 2} L {apx - 10} {py + pit_h / 2}" stroke="{c["muted"]}" '
          f'stroke-width="1.5" marker-end="url(#arr)" marker-start="url(#arr)"/>')
    d.text((dpx + 190 + apx - 10) / 2, py + pit_h / 2 - 12, "separate pits - do not join DC and AC earth", 14,
           fill=c["muted"])

    # ------------------------------------------------------------------ legend
    ly = py + pit_h + 80
    for x, color, label in ((70, c["pos"], "DC + / AC L"), (460, c["neg"], "DC − / AC N"), (840, c["earth"], "Earth")):
        d.path([(x, ly), (x + 60, ly)], color, 4)
        d.text(x + 76, ly + 6, label, 17, anchor="start")
    H = ly + 40

    defs = (f'<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c["muted"]}"/></marker></defs>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="{escape(head)}">{defs}<rect width="{W}" height="{H}" fill="{c["bg"]}"/>'
            + "".join(d.parts) + "</svg>")
