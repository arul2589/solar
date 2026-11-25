"""Unit tests for the pure calculation library, using the worked examples in SPEC section 6
and the reference sheets."""
from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from solarcalc import SiteInputs, analyse
from solarcalc.cables import design_electrical, vdrop_pct
from solarcalc.costing import Line, build_lines, totals
from solarcalc.models import CalcSettings
from solarcalc.network import generated_units, network_charge, rate_on
from solarcalc.offgrid import backup_hours, battery_ah, charge_controller_a, inverter_va
from solarcalc import roof
from solarcalc.sizing import kw_needed, nominal_kw, panels_for_wp, size_system, units_per_kw_day_cuf
from solarcalc.strings import design_strings, select_inverter
from solarcalc.tariff import bill_for_units, units_for_bill

from .calc_fixtures import INVERTERS, NETWORK_RATES, PANEL_615, S, SLABS, UTL_33, UTL_GT5K, rules_276

D = Decimal


# ---------------------------------------------------------------- 6.1 sizing
def test_units_per_kw_day_at_cuf_21():
    assert units_per_kw_day_cuf(0.21) == pytest.approx(5.04)
    # institute example: 5 kW -> 25.2 units/day
    assert 5 * units_per_kw_day_cuf(0.21) == pytest.approx(25.2)


def test_kw_needed_uses_configured_yield():
    s = CalcSettings(realistic_yield_low=4.0, realistic_yield_high=4.0, days_per_month=30)
    assert kw_needed(480, s) == pytest.approx(4.0)
    s_cuf = CalcSettings(sizing_yield_basis="cuf", cuf_tnerc=0.21, days_per_month=30)
    assert kw_needed(756, s_cuf) == pytest.approx(5.0)


# ---------------------------------------------------------------- 6.2 panel count
def test_panel_count_quotation_276():
    # 5 x 615 W = 3,075 Wp -> sold as 3 kW
    assert panels_for_wp(3000, 615) == 5
    assert 5 * 615 == 3075
    assert nominal_kw(3.075, S) == 3.0


def test_size_system_caps_by_sanction_load():
    r = size_system(PANEL_615, S, monthly_units=900, sanction_load_kw=4)
    assert r.panel_count == 6          # floor(4000/615)
    assert r.limited_by == "sanction_load"
    assert any(w.code == "SANCTION_LOAD_CAP" for w in r.warnings)


def test_size_system_caps_by_roof():
    r = size_system(PANEL_615, S, monthly_units=900, max_panels_by_roof=4)
    assert r.panel_count == 4 and r.limited_by == "roof_area"


# ---------------------------------------------------------------- 6.3 roof
def test_rule_of_thumb_area_from_1kw_guideline():
    a = roof.rule_of_thumb_area(1, S)
    assert a["min_m2"] == 7.5
    assert 9 <= a["recommended_m2"] <= 10


def test_row_spacing_uses_trigonometry():
    s = CalcSettings(tilt_deg=11, design_sun_elevation_deg=45, min_row_gap_m=0)
    g = roof.row_geometry(PANEL_615, s)
    import math
    rise = 2.382 * math.sin(math.radians(11))
    assert g["raised_edge_height_m"] == pytest.approx(rise, abs=1e-3)
    # tan(45) = 1 so the shadow equals the rise
    assert g["shadow_length_m"] == pytest.approx(rise, abs=1e-3)


def test_layout_fit_and_no_fit():
    ok = roof.layout(PANEL_615, 5, S, length_m=8, width_m=7)
    assert ok.fits and ok.placed == 5
    tight = roof.layout(PANEL_615, 9, S, length_m=3, width_m=4)
    assert not tight.fits and tight.capacity < 9


# ---------------------------------------------------------------- 6.4 strings / inverter
def test_string_design_3kw_on_utl_3_3():
    sd = design_strings(PANEL_615, 5, UTL_33, S)
    assert sd.feasible and sd.strings == [{"mppt": 1, "modules": 5}]
    assert sd.string_voc_cold_max <= UTL_33.max_dc_voltage


def test_string_design_5kw_on_gt5k_respects_mppt_minimum():
    sd = design_strings(PANEL_615, 9, UTL_GT5K, S)
    assert sd.feasible
    assert sd.string_vmp_hot_min >= UTL_GT5K.mppt_min_v
    too_few = design_strings(PANEL_615, 4, UTL_GT5K, S)
    assert not too_few.feasible
    assert too_few.warnings[0].code == "STRING_VOLTAGE_LOW"


def test_voc_cold_limit():
    # 11 modules x ~54.6 V cold exceeds 550 V
    sd = design_strings(PANEL_615, 11, UTL_GT5K, S)
    assert sd.modules_per_string_max == 10
    assert all(st["modules"] <= 10 for st in sd.strings) or not sd.feasible


def test_select_inverter_prefers_ratio_in_range():
    c = select_inverter(PANEL_615, 9, INVERTERS, S, supply_phase=1)
    assert c.inverter.model == "UTL GT-5K-GXS1"
    assert 1.0 <= c.dc_ac_ratio <= 1.3


def test_select_inverter_warns_oversized_for_276():
    c = select_inverter(PANEL_615, 5, [UTL_33, UTL_GT5K], S, supply_phase=3)
    assert c.inverter.model.startswith("UTL 3.3")
    assert any(w.code == "INVERTER_OVERSIZED" for w in c.warnings)


def test_single_phase_supply_never_gets_three_phase_inverter():
    c = select_inverter(PANEL_615, 16, INVERTERS, S, supply_phase=1)
    assert c.inverter is None or c.inverter.phase == 1


# ---------------------------------------------------------------- 6.5 cables
def test_vdrop_formula():
    # 2 x 15 m x 14 A x 0.0178 / 4 mm2 / 200 V = 0.93 %
    assert vdrop_pct(15, 14, 4, 200, 0.0178) == pytest.approx(0.9345, abs=1e-3)


def test_electrical_design_minimum_two_pits_plus_la():
    sd = design_strings(PANEL_615, 5, UTL_33, S)
    e = design_electrical(PANEL_615, UTL_33, sd, S)
    assert e.dc_cable_mm2 in (4.0, 6.0)
    assert e.earthing_pits == 3      # 2 minimum + dedicated LA pit (quotation #276 had 3)
    assert e.dc_cable_total_m == 2 * 15 + 2 * 1
    assert any(p["device"].startswith("AC MCB") for p in e.protection)


# ---------------------------------------------------------------- 6.6 network charges
def test_generated_units_worked_example():
    # SPEC: 5 kW, 65 days, CUF 21% -> 1,638 units
    assert generated_units(5, 0.21, 65) == 1638


def test_network_charge_sheet_july_2024():
    # Working sheet: 1638 x 1.56 x 20% = Rs 511.06
    r = network_charge(5, 65, S, rate=D("1.56"))
    assert r.units == 1638
    assert r.charge == D("511.06")
    assert r.cgst == r.sgst == D("46.00")  # 9% each


def test_network_charge_sheet_nov_2025():
    # 4.8 x 24 x 0.21 x 65 = 1572.48 -> 1572 units; 1572 x 1.6 x 0.2 = 503.04
    r = network_charge(4.8, 65, S, rate=D("1.6"), include_gst=False)
    assert r.units == 1572
    assert r.charge == D("503.04")


def test_network_rate_table_by_effective_date():
    assert rate_on(date(2022, 9, 9), NETWORK_RATES).rate == D("1.27")
    assert rate_on(date(2022, 9, 10), NETWORK_RATES).rate == D("1.48")
    assert rate_on(date(2023, 7, 1), NETWORK_RATES).rate == D("1.53")
    assert rate_on(date(2025, 1, 1), NETWORK_RATES).rate == D("1.59")


def test_network_pct_only_for_domestic_upto_10kw():
    s = CalcSettings(network_pct_other=0.5)
    assert network_charge(12, 60, s, rate=D("1.59"), include_gst=False).percentage == 0.5
    assert network_charge(5, 60, s, rate=D("1.59"), include_gst=False, category="commercial").percentage == 0.5


# ---------------------------------------------------------------- 6.7 tariff, costing
def test_slab_bill_and_inverse():
    # 300 units: 100 free + 100 x 2.35 + 100 x 4.70 = 705
    assert bill_for_units(300, SLABS) == D("705.00")
    assert units_for_bill(705, SLABS) == pytest.approx(300, abs=0.2)


def test_quotation_276_totals_by_hand():
    q = [
        Line("Panel", D(5), D("19200"), D(5)), Line("Inverter", D(1), D("27000"), D(5)),
        Line("Structure", D(3), D("6850"), D(18)), Line("ACDB", D(1), D("2100"), D(18)),
        Line("DCDB", D(1), D("2500"), D(18)), Line("Earthing", D(3), D("1500"), D(18)),
        Line("Chamber", D(3), D("450"), D(0)), Line("Pipe", D(1), D("2500"), D(0)),
        Line("DC cable", D(30), D("103"), D(18)), Line("Labour", D(2), D("3500"), D(0)),
        Line("Transport", D(1), D("8000"), D(0)), Line("Net meter", D(1), D("4850"), D(0)),
        Line("Stamp", D(1), D("5000"), D(0)), Line("AC wire", D(30), D("65"), D(18)),
        Line("LA", D(1), D("2500"), D(18)), Line("LA cable", D(15), D("210"), D(18)),
    ]
    assert q[0].tax == D("4800.00") and q[0].total == D("100800.00")
    assert q[2].tax == D("3699.00")
    assert q[8].tax == D("556.20")
    t = totals(q)
    assert t.subtotal == D("192040.00")
    assert t.tax == D("13411.20")
    assert t.grand_total == D("205451.20")


def test_bom_lines_from_price_master_3kw():
    ctx = {"nominal_kw": 3.0, "dc_kwp": 3.075, "panel_count": 5, "dc_cable_m": 30, "ac_cable_m": 30,
           "earthing_pits": 3, "la_cable_m": 15, "strings": 1, "mppts": 1, "phase": 1, "system_kind": "on_grid",
           "lightning_arrester": True,
           "panel": {"model": "ADANI 615", "wp": "615", "price": D("19200")},
           "inverter": {"model": "UTL 3.3", "ac_kw": "3.3", "phase": 1, "phase_label": "Single Phase",
                        "price": D("27000")}}
    lines = build_lines(rules_276(), ctx)
    by = {l.code: l for l in lines}
    assert by["PANEL"].qty == 5 and "3075 Watts" in by["PANEL"].details
    assert by["STRUCTURE"].qty == 3
    assert by["EARTH_ELECTRODE"].qty == 3
    assert by["LABOUR"].qty == 3
    # identical to #276 except labour charged for 3 kW instead of 2: +3,500
    assert totals(lines).subtotal == D("192040.00") + D("3500")


# ---------------------------------------------------------------- off-grid (institute sheets)
def test_offgrid_formulas_institute_examples():
    assert battery_ah(370, 4, 12, 1.0) == pytest.approx(123.33, abs=0.01)
    assert inverter_va(1450, 1.25, 0.8) == pytest.approx(2265.6, abs=0.1)
    assert charge_controller_a(400, 12, 1.25) == pytest.approx(41.67, abs=0.01)
    assert backup_hours(150, 12, 0.85, 300) == pytest.approx(5.1)


# ---------------------------------------------------------------- engine
def test_engine_full_analysis_5kw_home():
    inp = SiteInputs(monthly_units=600, phase=1, sanction_load_kw=8, roof_area_m2=80, shade="none")
    s = CalcSettings(realistic_yield_low=4.0, realistic_yield_high=4.4)
    r = analyse(inp, s, panels=[PANEL_615], inverters=INVERTERS, network_rates=NETWORK_RATES,
                tariff_slabs=SLABS, price_rules=rules_276(), on=date(2025, 1, 1))
    assert r["ok"], r["warnings"]
    # 600 / (4.2 x 30) = 4.76 kW -> 8 panels x 615 = 4.92 kWp
    assert r["sizing"]["panel_count"] == 8
    assert r["inverter"]["inverter"]["model"] == "UTL GT-5K-GXS1"
    assert r["network_charge"]["rate"] == "1.59"
    assert r["cost"]["totals"]["grand_total"]
    assert r["savings"]["low"]["payback_years"] >= r["savings"]["high"]["payback_years"] > 0


def test_engine_warnings_heavy_shade_small_roof():
    inp = SiteInputs(monthly_units=600, phase=1, roof_area_m2=10, shade="heavy")
    r = analyse(inp, S, panels=[PANEL_615], inverters=INVERTERS, network_rates=NETWORK_RATES)
    codes = {w["code"] for w in r["warnings"]}
    assert "HEAVY_SHADE" in codes
    assert "ROOF_LIMITS_SIZE" in codes or "ROOF_TOO_SMALL" in codes


def test_engine_needs_consumption():
    r = analyse(SiteInputs(), S, panels=[PANEL_615], inverters=INVERTERS)
    assert not r["ok"]
    assert r["warnings"][0]["code"] == "NO_CONSUMPTION_DATA"


def test_engine_missing_catalogue():
    r = analyse(SiteInputs(monthly_units=300), S, panels=[PANEL_615], inverters=[])
    assert any(w["code"] == "MISSING_CATALOGUE" for w in r["warnings"])


def test_engine_monthly_units_from_bill_amount():
    # bill of 705 per 2 months = 352.5 per month -> 300 units / 2 = 150 per month
    r = analyse(SiteInputs(monthly_bill=352.5), S, panels=[PANEL_615], inverters=INVERTERS, tariff_slabs=SLABS)
    assert r["monthly_units"] == pytest.approx(150, abs=0.5)


def test_engine_settings_drive_results():
    a = analyse(SiteInputs(monthly_units=600), CalcSettings(realistic_yield_low=3.0, realistic_yield_high=3.0),
                panels=[PANEL_615], inverters=INVERTERS)
    b = analyse(SiteInputs(monthly_units=600), CalcSettings(realistic_yield_low=5.0, realistic_yield_high=5.0),
                panels=[PANEL_615], inverters=INVERTERS)
    assert a["sizing"]["panel_count"] > b["sizing"]["panel_count"]
