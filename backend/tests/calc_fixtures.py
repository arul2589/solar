"""Sample catalogue data used by the calculation tests.

The 615 W panel electrical values are typical TOPCon figures used as placeholders until
the owner supplies the datasheet (see DECISIONS.md). The UTL GT-5K values come from the
nameplate photo in reference/08_Images_Reference/Panel_Inverter_Ratings.
"""
from datetime import date
from decimal import Decimal

from solarcalc import CalcSettings, InverterSpec, NetworkRate, PanelSpec, TariffSlab
from solarcalc.costing import PriceRule

PANEL_615 = PanelSpec(model="Adani 615 Wp TOPCon bifacial DCR", wp=615, voc=52.6, vmp=44.0, isc=14.75, imp=13.98,
                      temp_coeff_voc_pct=-0.25, temp_coeff_pmax_pct=-0.29, length_mm=2382, width_mm=1134,
                      price=Decimal("19200"), id=1)

UTL_33 = InverterSpec(model="UTL 3.3 kW single phase on-grid", ac_kw=3.3, phase=1, max_dc_voltage=550,
                      mppt_min_v=80, mppt_max_v=500, num_mppt=1, max_input_current_per_mppt=16,
                      ac_max_current=15.0, price=Decimal("27000"), id=1)
UTL_GT5K = InverterSpec(model="UTL GT-5K-GXS1", ac_kw=5.0, phase=1, max_dc_voltage=550, mppt_min_v=250,
                        mppt_max_v=500, num_mppt=1, max_input_current_per_mppt=20, ac_max_current=25.0,
                        price=Decimal("38000"), id=2)
THREE_PH_10K = InverterSpec(model="Generic 10 kW three phase on-grid", ac_kw=10.0, phase=3, max_dc_voltage=1100,
                            mppt_min_v=200, mppt_max_v=950, num_mppt=2, max_input_current_per_mppt=16,
                            ac_max_current=16.0, price=Decimal("75000"), id=3)
INVERTERS = [UTL_33, UTL_GT5K, THREE_PH_10K]

NETWORK_RATES = [
    NetworkRate(date(2000, 1, 1), Decimal("1.27")),
    NetworkRate(date(2022, 9, 10), Decimal("1.48")),
    NetworkRate(date(2023, 7, 1), Decimal("1.53")),
    NetworkRate(date(2024, 7, 1), Decimal("1.59")),
]

# Placeholder TN domestic slabs per 2-month cycle (VERIFY with owner)
SLABS = [
    TariffSlab(100, Decimal("0")), TariffSlab(200, Decimal("2.35")), TariffSlab(400, Decimal("4.70")),
    TariffSlab(500, Decimal("6.30")), TariffSlab(600, Decimal("8.40")), TariffSlab(800, Decimal("9.45")),
    TariffSlab(1000, Decimal("10.50")), TariffSlab(None, Decimal("11.55")),
]

S = CalcSettings()


def rules_276():
    """Price master seeded from sample quotation #276 (Sri Vinayaka Solar)."""
    D = Decimal
    return [
        PriceRule("PANEL", "{model}", D("19200"), D("5"), "Nos", "85414012",
                  "{wp} WATTS SOLAR - {panel_count} NOS / {dc_wp} Watts. TOTAL KW - {nominal_kw} KW", "panel", sort_order=1),
        PriceRule("INVERTER", "{model}", D("27000"), D("5"), "No", "8504", "10 YEARS WARRANTY", "inverter", sort_order=2),
        PriceRule("STRUCTURE", "High raising pre-galvanised structure with fasteners", D("6850"), D("18"), "KW",
                  "7308", "", "per_kw", sort_order=3),
        PriceRule("ACDB_1PH", "ACDB 1 In 1 Out, 1-Ph, MCB+SPD", D("2100"), D("18"), "No", "85371000", "", "fixed",
                  inverter_phase=1, sort_order=4),
        PriceRule("DCDB", "DCDB 1-6 kW 1 string (DC fuse 1000V + MCB 500V + SPD 600)", D("2500"), D("18"), "No",
                  "85371000", "", "per_mppt", sort_order=5),
        PriceRule("EARTH_ELECTRODE", "Earthing electrode Cu bonded with chemical bag", D("1500"), D("18"), "No",
                  "85389000", "", "earth_pits", sort_order=6),
        PriceRule("EARTH_CHAMBER", "Earth pit chamber box", D("450"), D("0"), "Nos", "8538", "", "earth_pits", sort_order=7),
        PriceRule("PIPE_CLAMP", "Electrical pipe, clamp, screw, channel", D("2500"), D("0"), "No", "3917", "", "fixed",
                  sort_order=8),
        PriceRule("DC_CABLE", "1C x 4 sq mm solar DC flexible cable", D("103"), D("18"), "Mtrs", "85444990", "",
                  "dc_cable_m", sort_order=9),
        PriceRule("LABOUR", "Erection, installation and commissioning", D("3500"), D("0"), "KW", "9954", "", "per_kw",
                  sort_order=10),
        PriceRule("TRANSPORT", "Transport", D("8000"), D("0"), "Wheeler Pickup", "", "", "fixed", sort_order=11),
        PriceRule("NET_METER", "TNEB solar net metering charges", D("4850"), D("0"), "Energy Meter", "", "", "fixed",
                  sort_order=12),
        PriceRule("STAMP", "Stamp paper charges and TNEB", D("5000"), D("0"), "Set", "", "", "fixed", sort_order=13),
        PriceRule("AC_CABLE", "AC wire 4 sq mm", D("65"), D("18"), "Mtr", "854460", "", "ac_cable_m", sort_order=14),
        PriceRule("LA", "Lightning arrester Cu bonded multi-spike", D("2500"), D("18"), "No", "85389000", "", "fixed",
                  requires_la=True, sort_order=15),
        PriceRule("LA_CABLE", "Lightning arrester cable Cu 16 sq mm", D("210"), D("18"), "Mtrs", "8544", "",
                  "la_cable_m", requires_la=True, sort_order=16),
    ]
