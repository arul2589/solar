"""Snapshot tests for generated diagrams. Regenerate after an intended change with
UPDATE_SNAPSHOTS=1 python -m pytest tests/test_diagrams.py"""
import os
import xml.dom.minidom
from datetime import date
from pathlib import Path

import pytest

from diagrams.svg import GENERATORS
from solarcalc import CalcSettings, SiteInputs, analyse

from .calc_fixtures import INVERTERS, NETWORK_RATES, PANEL_615, SLABS, rules_276

SNAP = Path(__file__).parent / "snapshots"


def outputs(case):
    s = CalcSettings(realistic_yield_low=4.0, realistic_yield_high=4.2)
    if case == "3kw":
        inp = SiteInputs(panel_count=5, phase=3, roof_length_m=6, roof_width_m=5)
    elif case == "5kw":
        inp = SiteInputs(panel_count=9, phase=1, roof_length_m=8, roof_width_m=7)
    else:   # roof too small
        inp = SiteInputs(panel_count=9, phase=1, roof_length_m=3, roof_width_m=4)
    return analyse(inp, s, panels=[PANEL_615], inverters=INVERTERS, network_rates=NETWORK_RATES,
                   tariff_slabs=SLABS, price_rules=rules_276(), on=date(2025, 1, 1))


@pytest.mark.parametrize("case", ["3kw", "5kw", "small_roof"])
@pytest.mark.parametrize("kind", ["sld", "roof", "schedule"])
def test_diagram_snapshot(case, kind):
    svg = GENERATORS[kind](outputs(case))
    xml.dom.minidom.parseString(svg)       # well-formed XML
    path = SNAP / f"{kind}_{case}.svg"
    if os.environ.get("UPDATE_SNAPSHOTS") or not path.exists():
        SNAP.mkdir(exist_ok=True)
        path.write_text(svg, encoding="utf-8")
    assert svg == path.read_text(encoding="utf-8")


def test_roof_layout_warns_when_panels_do_not_fit():
    svg = GENERATORS["roof"](outputs("small_roof"))
    assert "WARNING" in svg


def test_svg_escapes_text():
    o = outputs("3kw")
    o["panel"]["model"] = '<script>alert("x")</script>'
    svg = GENERATORS["sld"](o)
    assert "<script>" not in svg
