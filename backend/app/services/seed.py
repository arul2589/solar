"""Seed data: platform tenant, a demo installer, catalogue and price list.

Catalogue prices and BOS items come from sample quotation #276 (reference/03_Quotations).
Panel/inverter electrical values are placeholders except the UTL GT-5K nameplate.
"""
from __future__ import annotations

import os
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from ..db import session_scope
from ..models import InverterModel, Installer, NetworkRateRow, PanelModel, PriceItem, Role, User
from ..security import hash_password
from .settings import DEFAULTS, save_section

D = Decimal

ROLE_DESCRIPTIONS = {
    "admin": "Installer owner: everything for this installer",
    "sales": "Review requests, edit and send quotations",
    "engineer": "Edit survey data, run calculations, edit diagrams",
    "technician": "Assigned projects, checklist, wiring sheet, site photos. No prices.",
}

NETWORK_RATES = [
    (date(2000, 1, 1), D("1.27"), "Before 10.09.2022 (sheet)"),
    (date(2022, 9, 10), D("1.48"), "From 10.09.2022 (sheet)"),
    (date(2023, 7, 1), D("1.53"), "From 01.07.2023 (sheet)"),
    (date(2024, 7, 1), D("1.59"), "From 01.07.2024 (sheet) - VERIFY: bills show 1.56 / 1.6"),
]

PANELS = [
    dict(make="Adani", model="615 Wp N-type TOPCon bifacial DCR", wp=615, voc=52.6, vmp=44.0, isc=14.75, imp=13.98,
         temp_coeff_voc_pct=-0.25, temp_coeff_pmax_pct=-0.29, length_mm=2382, width_mm=1134, price=D("19200"),
         hsn="85414012", gst_pct=D("5"), is_default=True, is_placeholder=True,
         warranty_text="12 years product warranty. Performance and working life 25 years."),
    dict(make="Waaree", model="BiH-11-710 HJT bifacial", wp=710, voc=50.09, vmp=42.04, isc=17.94, imp=16.89,
         temp_coeff_voc_pct=-0.22, temp_coeff_pmax_pct=-0.24, length_mm=2384, width_mm=1303, price=None,
         hsn="85414012", gst_pct=D("5"), is_default=False, is_placeholder=False,
         warranty_text="12 years product warranty, 30 years power output warranty."),
]

INVERTERS = [
    dict(make="UTL", model="3.3 kW single phase on-grid", kind="on_grid", ac_kw=3.3, phase=1, max_dc_voltage=550,
         mppt_min_v=80, mppt_max_v=500, num_mppt=1, max_input_current_per_mppt=16, ac_max_current=15,
         price=D("27000"), gst_pct=D("5"), is_placeholder=True, warranty_text="10 years warranty"),
    dict(make="UTL", model="GT-5K-GXS1 single phase on-grid", kind="on_grid", ac_kw=5.0, phase=1, max_dc_voltage=550,
         mppt_min_v=250, mppt_max_v=500, num_mppt=1, max_input_current_per_mppt=20, ac_max_current=25,
         price=D("38000"), gst_pct=D("5"), is_placeholder=True, warranty_text="10 years warranty"),
    dict(make="Generic", model="10 kW three phase on-grid", kind="on_grid", ac_kw=10.0, phase=3, max_dc_voltage=1100,
         mppt_min_v=200, mppt_max_v=950, num_mppt=2, max_input_current_per_mppt=16, ac_max_current=16,
         price=D("75000"), gst_pct=D("5"), is_placeholder=True, warranty_text="10 years warranty"),
    dict(make="Generic", model="5 kW hybrid 48 V", kind="hybrid", ac_kw=5.0, phase=1, max_dc_voltage=500,
         mppt_min_v=120, mppt_max_v=450, num_mppt=1, max_input_current_per_mppt=18, ac_max_current=22,
         battery_voltage=48, price=D("65000"), gst_pct=D("5"), is_placeholder=True, warranty_text="5 years warranty"),
]

# code, name, details, hsn, unit, price, gst, rule, extra
PRICE_ITEMS = [
    ("PANEL", "{model}", "{wp} WATTS SOLAR - {panel_count} NOS / {dc_wp} Watts. TOTAL KW - {nominal_kw} KW",
     "85414012", "Nos", "19200", "5", "panel", {"sort_order": 1}),
    ("INVERTER", "{model}", "", "8504", "No", "27000", "5", "inverter", {"sort_order": 2}),
    ("STRUCTURE", "High raising supply of pre-galvanised structure with fasteners",
     "Solar module structure. Civil work customer scope.", "7308", "KW", "6850", "18", "per_kw", {"sort_order": 3}),
    ("ACDB_1PH", "ACDB 1 In 1 Out, 1-Ph, MCB + SPD", "", "85371000", "No", "2100", "18", "fixed",
     {"sort_order": 4, "phase": 1}),
    ("ACDB_3PH", "ACDB 3-Ph, 4P MCB + SPD", "", "85371000", "No", "4500", "18", "fixed",
     {"sort_order": 4, "phase": 3, "is_placeholder": True}),
    ("DCDB", "DCDB 1 string (DC fuse 1000V + MCB 500V + SPD 600V)", "", "85371000", "No", "2500", "18", "per_mppt",
     {"sort_order": 5}),
    ("EARTH_ELECTRODE", "Earthing electrode Cu bonded 100 micron, 1.2 m / 17.2 mm dia, 10 kg chemical bag", "",
     "85389000", "No", "1500", "18", "earth_pits", {"sort_order": 6}),
    ("EARTH_CHAMBER", "Earth pit chamber box", "", "8538", "Nos", "450", "0", "earth_pits", {"sort_order": 7}),
    ("PIPE_CLAMP", "Electrical pipe, clamp, screw, channel 3/4\" or 1\"", "", "3917", "No", "2500", "0", "fixed",
     {"sort_order": 8}),
    ("DC_CABLE", "1C solar DC flexible cable (Polycab)", "Size as per design", "85444990", "Mtrs", "103", "18",
     "dc_cable_m", {"sort_order": 9}),
    ("LABOUR", "Solar power plant erection, installation and commissioning services", "", "9954", "KW", "3500", "0",
     "per_kw", {"sort_order": 10}),
    ("TRANSPORT", "Transport charges", "", "", "Trip", "8000", "0", "fixed", {"sort_order": 11}),
    ("NET_METER_1PH", "TNEB solar net metering charges", "Single phase meter", "", "Energy Meter", "4850", "0",
     "fixed", {"sort_order": 12, "phase": 1, "is_placeholder": True}),
    ("NET_METER_3PH", "TNEB solar net metering charges", "3 phase meter", "", "Energy Meter", "4850", "0", "fixed",
     {"sort_order": 12, "phase": 3}),
    ("STAMP", "Stamp paper charges and TNEB documentation", "", "", "Set", "5000", "0", "fixed", {"sort_order": 13}),
    ("AC_CABLE", "AC wire (Polycab or Finolex)", "Size as per design", "854460", "Mtr", "65", "18", "ac_cable_m",
     {"sort_order": 14}),
    ("LA", "Lightning arrester Cu bonded 100 micron multi-spike, 1 m / 20 mm dia with nylon insulated base", "",
     "85389000", "No", "2500", "18", "fixed", {"sort_order": 15, "requires_la": True}),
    ("LA_CABLE", "Lightning arrester cable copper 16 sq mm", "", "8544", "Mtrs", "210", "18", "la_cable_m",
     {"sort_order": 16, "requires_la": True}),
    ("BATTERY", "Lithium battery 48 V (per kWh)", "Sized from backup load", "8507", "kWh", "18000", "18", "fixed",
     {"sort_order": 17, "system_kind": "hybrid", "is_placeholder": True}),
]


def seed_installer(slug: str, name: str, *, admin_email: str, admin_password: str, demo_staff: bool = False) -> int:
    with session_scope(None, bypass=True) as db:
        inst = db.scalar(select(Installer).where(Installer.slug == slug))
        if inst:
            return inst.id
        inst = Installer(slug=slug, name=name, next_quote_number=277, next_request_number=1)
        db.add(inst)
        db.flush()
        iid = inst.id
    with session_scope(iid) as db:
        for rname, desc in ROLE_DESCRIPTIONS.items():
            db.add(Role(name=rname, description=desc))
        db.add(User(email=admin_email.lower(), name="Owner", password_hash=hash_password(admin_password), role="admin"))
        if demo_staff:
            for role in ("sales", "engineer", "technician"):
                db.add(User(email=f"{role}@{slug}.local", name=role.title(), role=role,
                             password_hash=hash_password(admin_password)))
        company = dict(DEFAULTS["company"]) | {"name": name}
        save_section(db, "company", company)
        save_section(db, "email", dict(DEFAULTS["email"]) | {"from_name": name})
        for eff, rate, note in NETWORK_RATES:
            db.add(NetworkRateRow(effective_from=eff, rate=rate, note=note))
        for p in PANELS:
            db.add(PanelModel(**p))
        for i in INVERTERS:
            db.add(InverterModel(**i))
        for code, pname, details, hsn, unit, price, gst, rule, extra in PRICE_ITEMS:
            extra = dict(extra)
            db.add(PriceItem(code=code, name=pname, details=details, hsn=hsn, unit=unit, unit_price=D(price),
                             gst_pct=D(gst), qty_rule=rule, is_placeholder=extra.pop("is_placeholder", True), **extra))
    return iid


def seed_platform(owner_email: str, password: str) -> int:
    with session_scope(None, bypass=True) as db:
        inst = db.scalar(select(Installer).where(Installer.slug == "platform"))
        if inst:
            return inst.id
        inst = Installer(slug="platform", name="Platform", is_platform=True)
        db.add(inst)
        db.flush()
        db.add(User(installer_id=inst.id, email=owner_email.lower(), name="Platform owner",
                    password_hash=hash_password(password), role="platform_owner"))
        return inst.id


def seed_all() -> None:
    pw = os.environ.get("SEED_ADMIN_PASSWORD", "ChangeMe-2026!")
    seed_platform(os.environ.get("SEED_PLATFORM_EMAIL", "platform@example.com"), pw)
    seed_installer(os.environ.get("SEED_INSTALLER_SLUG", "demo"), os.environ.get("SEED_INSTALLER_NAME", "Demo Rooftop Solar"),
                   admin_email=os.environ.get("SEED_ADMIN_EMAIL", "admin@example.com"), admin_password=pw,
                   demo_staff=os.environ.get("SEED_DEMO_STAFF", "1") == "1")


if __name__ == "__main__":
    seed_all()
    print("seed complete")
