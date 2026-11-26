"""Wiring diagram: generated from the engine design (strings, DCDB/ACDB devices, earthing, battery)."""
import xml.dom.minidom
from datetime import date

import pytest

from diagrams.svg import GENERATORS
from diagrams.wiring import wiring_diagram
from solarcalc import CalcSettings, SiteInputs, analyse
from solarcalc.models import InverterSpec

from .calc_fixtures import INVERTERS, NETWORK_RATES, PANEL_615, SLABS, rules_276

HYBRID = InverterSpec(model="Test 5 kW hybrid", ac_kw=5.0, phase=1, max_dc_voltage=550, mppt_min_v=120, mppt_max_v=500,
                      num_mppt=2, max_input_current_per_mppt=18, ac_max_current=22.0, kind="hybrid", battery_voltage=48)


def run(**kw):
    inv = kw.pop("inverters", INVERTERS)
    s = CalcSettings(realistic_yield_low=4.0, realistic_yield_high=4.2)
    return analyse(SiteInputs(**kw), s, panels=[PANEL_615], inverters=inv, network_rates=NETWORK_RATES,
                   tariff_slabs=SLABS, price_rules=rules_276(), on=date(2025, 1, 1))


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_on_grid_wiring(theme):
    o = run(panel_count=9, phase=1, roof_length_m=8, roof_width_m=7)
    svg = wiring_diagram(o, theme=theme)
    xml.dom.minidom.parseString(svg)
    for label in ("DCDB", "ACDB", "Fuse", "SPD", "MCB", "Net meter", "DC earth", "AC earth", "LA pit", "String 1"):
        assert label in svg, label
    assert svg.count(">615W<") == 9                      # every module drawn
    fuse = next(p for p in o["electrical"]["protection"] if p["device"].startswith("DC fuse"))
    assert fuse["rating"] in svg                           # ratings come from the engine
    assert "Battery" not in svg and "Backup DB" not in svg


def test_hybrid_has_battery_and_backup():
    o = run(panel_count=8, phase=1, goal="backup", daily_backup_load_w=600, roof_length_m=8, roof_width_m=7,
            inverters=[HYBRID] + INVERTERS)
    assert o["system_kind"] == "hybrid"
    svg = GENERATORS["wiring"](o)
    for label in ("Battery", "Backup DB", "BAT", "LOAD", f"{o['battery']['battery_ah_rounded']} Ah"):
        assert label in svg, label


def test_large_plant_is_summarised():
    o = run(panel_count=50, phase=3, category="industrial", roof_length_m=30, roof_width_m=20)
    svg = GENERATORS["wiring_print"](o)
    xml.dom.minidom.parseString(svg)
    assert "3P+N" in svg and "more string(s)" in svg and "inverters" in svg
