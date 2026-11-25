"""Project pack (SPEC 5.4): generated when a quotation is accepted."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AnalysisRun, ChecklistItem, Project, ProjectReading, Quotation, ServiceRequest
from . import activity
from .settings import load_all

# Defaults live in settings ("project" section) so each installer can edit them.
CHECKLIST = [
    ("Site survey & feasibility", "தள ஆய்வு மற்றும் சாத்தியக்கூறு",
     ["Roof type (RCC / sheet / tile)", "Shadow analysis (buildings, trees)", "Orientation (south best)",
      "Tilt angle ~10-15° (Tamil Nadu)", "Shadow-free area 9:00-16:00", "EB service type (1 / 3 phase)",
      "Load and EB bill analysis"]),
    ("System design", "அமைப்பு வடிவமைப்பு",
     ["System size finalised", "Panel selection", "Inverter selection", "String calculation (Voc within limit)",
      "Mounting structure design", "Cable sizing (DC & AC)", "Earthing & lightning plan"]),
    ("Material checklist", "பொருட்கள் சரிபார்ப்பு",
     ["Solar panels", "Inverter", "Mounting structure (GI/aluminium)", "DC cable (4/6 sq mm)", "AC cable",
      "MC4 connectors", "DCDB & ACDB", "Earthing kit", "Lightning arrester", "Cable trays / conduits"]),
    ("Structure installation", "கட்டமைப்பு நிறுவல்",
     ["Mark layout as per design", "Fix base (chemical anchor / clamp)", "Align structure (tilt & direction)",
      "Tighten all bolts (torque check)", "Corrosion protection"]),
    ("Panel mounting", "பேனல் பொருத்துதல்",
     ["Place panels carefully (no damage)", "Proper mid & end clamps", "Maintain spacing for airflow",
      "Label panel strings"]),
    ("DC wiring", "DC வயரிங்",
     ["Series connection (string formation)", "Proper MC4 crimping", "Polarity check (+/-)",
      "Cable routing, no loose hanging", "DC cable in conduit / tray", "String voltage check (Voc test)"]),
    ("Inverter installation", "இன்வெர்ட்டர் நிறுவல்",
     ["Mount in shade / ventilated area", "Clearance around inverter", "Connect DC input from strings",
      "Connect AC output to ACDB", "Earthing connection"]),
    ("Protection system", "பாதுகாப்பு அமைப்பு",
     ["DCDB installation (SPD + MCB/isolator)", "ACDB installation (MCB + SPD)", "Proper earthing (min 2 pits)",
      "Lightning arrester (if needed)"]),
    ("Earthing & testing", "எர்த்திங் மற்றும் சோதனை",
     ["Panel earthing", "Inverter earthing", "Structure earthing", "Earth resistance check (< 5 ohm)"]),
    ("Pre-commissioning tests", "இயக்கத்திற்கு முந்தைய சோதனைகள்",
     ["String Voc measurement", "Polarity verification", "Continuity test", "Insulation test (Megger)",
      "Tightness check of all terminals"]),
    ("Commissioning", "இயக்கம்",
     ["Turn ON DC isolator", "Turn ON inverter", "Turn ON AC side", "Check inverter display",
      "Verify generation data"]),
    ("Net metering & handover", "நெட் மீட்டரிங் மற்றும் ஒப்படைப்பு",
     ["Apply EB net meter", "Documentation submission", "System demo to customer", "Warranty & manuals",
      "Explain monitoring app"]),
]

TOOLS = ["Screwdriver set", "Spanner / wrench set", "Electric drill machine", "MC4 crimping tool", "Wire stripper",
         "Cable cutter", "Measuring tape", "Clamp meter", "Spirit level", "Hammer",
         "Safety tools (helmet, gloves, harness)", "Digital multimeter", "DC clamp meter",
         "Insulation tester (Megger)", "Earth resistance tester", "Solar irradiance meter",
         "Non-contact voltage tester", "MC4 spanner"]

# From the TANGEDCO net-metering memo (Memo CE/Comml/EE/R&C/AEE1/F.Solar NM/D.023/14) and its forms.
NET_METERING_DOCS = [
    "Form-1 net-metering connection application (with Rs 100 registration fee)",
    "Copy of latest electricity bill (Annexure-II declaration)",
    "Annexure-II declaration signed by consumer",
    "Solar grid inverter make/type; confirmation of automatic isolation (anti-islanding) protection",
    "Single-line diagram of the SPV generator",
    "Specification sheets of all equipment (modules, inverter, protection)",
    "Readiness intimation to Section Office after installation",
    "Safety inspection: AEE/O&M below 10 kW; Electrical Inspectorate (CEIG) for 10 kW and above",
    "Form-2 net-metering connection agreement (signed)",
    "Bi-directional meter (TANGEDCO approved), and solar generation meter if GBI is claimed",
    "Caution stickers 'Solar PV Systems' and sign board near meter",
    "Manual isolator with locking at ground floor; separate earthing and lightning arrester",
]

PROJECT_DEFAULTS = {
    "checklist": [{"title": t, "title_ta": ta, "points": p} for t, ta, p in CHECKLIST],
    "tools": TOOLS,
    "net_metering_docs": NET_METERING_DOCS,
}


def create_project(db: Session, req: ServiceRequest, q: Quotation) -> Project:
    existing = db.scalar(select(Project).where(Project.request_id == req.id))
    if existing:
        return existing
    cfg = load_all(db).get("project") or PROJECT_DEFAULTS
    run = db.get(AnalysisRun, q.analysis_run_id) if q.analysis_run_id else None
    o = run.outputs if run else {}
    el = o.get("electrical") or {}
    pack = {
        "quotation_number": q.number, "analysis_run_id": q.analysis_run_id,
        "system_summary": q.system_summary,
        "bom": [{"description": l.description, "details": l.details, "qty": str(l.qty), "unit": l.unit, "code": l.code}
                for l in q.lines],
        "tools": cfg.get("tools", TOOLS),
        "net_metering_docs": cfg.get("net_metering_docs", NET_METERING_DOCS),
        "cable_schedule": el.get("cable_schedule", []),
        "protection": el.get("protection", []),
        "strings": ((o.get("inverter") or {}).get("strings") or {}).get("strings", []),
        "expected": expected_values(o),
        "warnings": o.get("warnings", []),
    }
    p = Project(request_id=req.id, quotation_id=q.id, status="planned", pack=pack,
                technician_user_id=req.engineer_user_id)
    db.add(p)
    db.flush()
    for i, step in enumerate(cfg.get("checklist", PROJECT_DEFAULTS["checklist"]), start=1):
        db.add(ChecklistItem(project_id=p.id, step_no=i, title=step["title"], title_ta=step.get("title_ta"),
                             points=[{"text": pt, "done": False} for pt in step.get("points", [])]))
    activity.log(db, "project_created", request_id=req.id, actor="system", project_id=p.id)
    return p


def expected_values(o: dict) -> dict:
    """Expected test readings from the design, so the technician sees pass/fail."""
    st = (o.get("inverter") or {}).get("strings") or {}
    strings = st.get("strings") or []
    return {
        "string_voc_cold_max": st.get("string_voc_cold_max"),
        "voc_per_module_cold": st.get("voc_cold_per_module"),
        "string_modules": [s["modules"] for s in strings],
    }


def evaluate_reading(project: Project, kind: str, label: str, value: Decimal, settings: dict) -> tuple[Optional[str], Optional[bool]]:
    exp = project.pack.get("expected") or {}
    v = float(value)
    if kind == "earth_resistance":
        limit = float(settings["calc"].get("earth_resistance_target_ohm", 5.0))
        return f"< {limit:g} ohm", v < limit
    if kind == "voc":
        per_mod = exp.get("voc_per_module_cold")
        mods = exp.get("string_modules") or []
        idx = _string_index(label)
        n = mods[idx] if idx is not None and idx < len(mods) else (mods[0] if mods else None)
        vmax = exp.get("string_voc_cold_max")
        if per_mod and n:
            # measured Voc at site temperature should be roughly 80-105% of the cold-design value
            hi = per_mod * n
            lo = hi * 0.8
            return f"{lo:.0f}-{hi:.0f} V", lo <= v <= (vmax or hi) * 1.02
    if kind == "insulation":
        return "> 1 Mohm", v > 1.0
    return None, None


def _string_index(label: str) -> Optional[int]:
    digits = "".join(ch for ch in (label or "") if ch.isdigit())
    return int(digits) - 1 if digits else None


def readings(db: Session, project_id: int) -> list[ProjectReading]:
    return list(db.scalars(select(ProjectReading).where(ProjectReading.project_id == project_id)
                           .order_by(ProjectReading.id)))
