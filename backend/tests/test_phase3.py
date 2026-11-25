"""Phase 3: project pack, technician checklist, bill-photo reading, industrial/3-phase, Tamil templates."""
import io
import json
from types import SimpleNamespace

from pypdf import PdfReader
from sqlalchemy import select

from app.db import session_scope
from app.models import EmailLog
from app.services import billread
from solarcalc import CalcSettings, SiteInputs, analyse

from .calc_fixtures import INVERTERS, NETWORK_RATES, PANEL_615, rules_276
from .conftest import login, submit


def _rid(client, h, ref):
    return next(i["id"] for i in client.get("/api/admin/requests", headers=h).json()["items"] if i["reference"] == ref)


def _accepted_project(client, h, **over):
    ref = submit(client, **over).json()["reference"]
    rid = _rid(client, h, ref)
    q = client.post(f"/api/admin/requests/{rid}/quotations", headers=h).json()
    tok = client.post(f"/api/admin/quotations/{q['id']}/send", headers=h).json()["dev_quote_url"].split("/q/")[1]
    client.post(f"/api/public/alpha/quotations/{tok}/accept")
    projects = client.get("/api/admin/projects", headers=h).json()
    return rid, next(p for p in projects if p["request_id"] == rid)


def test_project_pack_created_on_accept(client, alpha_admin):
    rid, p = _accepted_project(client, alpha_admin)
    d = client.get(f"/api/admin/projects/{p['id']}", headers=alpha_admin).json()
    assert len(d["checklist"]) == 12
    assert d["checklist"][0]["title"].startswith("Site survey") and d["checklist"][0]["title_ta"]
    assert d["checklist"][11]["title"].startswith("Net metering")
    assert d["pack"]["bom"] and d["pack"]["tools"] and d["pack"]["net_metering_docs"]
    assert d["pack"]["cable_schedule"] and d["pack"]["protection"]
    assert "price" not in json.dumps(d["pack"]["bom"]).lower()
    pdf = client.get(f"/api/admin/projects/{p['id']}/pack.pdf", headers=alpha_admin)
    text = "\n".join(pg.extract_text() for pg in PdfReader(io.BytesIO(pdf.content)).pages)
    assert "Bill of materials" in text and "Net-metering documents" in text and "₹" not in text


def test_technician_flow(client, alpha_admin):
    rid, p = _accepted_project(client, alpha_admin)
    tech = login(client, "alpha", "technician@alpha.local")
    # not assigned yet -> invisible
    assert all(x["id"] != p["id"] for x in client.get("/api/admin/projects", headers=tech).json())
    assert client.get(f"/api/admin/projects/{p['id']}", headers=tech).status_code == 404
    users = client.get("/api/admin/users", headers=alpha_admin).json()
    tid = next(u["id"] for u in users if u["role"] == "technician")
    client.patch(f"/api/admin/projects/{p['id']}", headers=alpha_admin, json={"technician_user_id": tid})
    d = client.get(f"/api/admin/projects/{p['id']}", headers=tech).json()
    step1 = d["checklist"][0]
    r = client.patch(f"/api/admin/projects/{p['id']}/checklist/{step1['id']}", headers=tech, json={"done": True, "notes": "ok"})
    assert r.json()["done"]
    assert client.get(f"/api/admin/requests/{rid}", headers=alpha_admin).json()["request"]["stage"] == "installation"
    # readings with pass/fail against design
    good = client.post(f"/api/admin/projects/{p['id']}/readings", headers=tech,
                       json={"kind": "earth_resistance", "label": "Pit 1", "value": 2.4}).json()
    bad = client.post(f"/api/admin/projects/{p['id']}/readings", headers=tech,
                      json={"kind": "earth_resistance", "label": "Pit 2", "value": 7.5}).json()
    assert good["ok"] is True and bad["ok"] is False
    voc = client.post(f"/api/admin/projects/{p['id']}/readings", headers=tech,
                      json={"kind": "voc", "label": "String 1", "value": 9999}).json()
    assert voc["ok"] is False and voc["expected"].endswith("V")
    # photo upload
    from .conftest import jpeg_bytes
    ph = client.post(f"/api/admin/projects/{p['id']}/photos", headers=tech,
                     files={"file": ("site.jpg", jpeg_bytes(), "image/jpeg")})
    assert ph.status_code == 200
    # technicians cannot see prices or quotations
    assert client.get(f"/api/admin/requests/{rid}", headers=tech).status_code == 403
    assert client.patch(f"/api/admin/projects/{p['id']}", headers=tech, json={"technician_user_id": 0}).status_code == 403
    # completion moves the request and emails the customer
    client.patch(f"/api/admin/projects/{p['id']}", headers=alpha_admin, json={"status": "done"})
    act = client.get(f"/api/admin/requests/{rid}/activity", headers=alpha_admin).json()
    assert client.get(f"/api/admin/requests/{rid}", headers=alpha_admin).json()["request"]["stage"] == "completed"
    assert any(e["template"] == "status_update" for e in act["emails"])


def test_projects_tenant_isolation(client, alpha_admin, beta_admin):
    _, p = _accepted_project(client, alpha_admin)
    assert client.get(f"/api/admin/projects/{p['id']}", headers=beta_admin).status_code == 404
    assert client.post(f"/api/admin/projects/{p['id']}/readings", headers=beta_admin,
                       json={"kind": "voc", "value": 1}).status_code == 404


class FakeClient:
    def __init__(self, payload, stop="end_turn"):
        self.payload, self.stop, self.calls = payload, stop, []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(stop_reason=self.stop, model=kw["model"],
                               content=[SimpleNamespace(type="text", text=json.dumps(self.payload))])


BILL = {"consumer_number": "09-455-008-1061", "consumer_name": "X", "tariff": "LA1A", "phase": 3, "sanction_load_kw": 4,
        "units_consumed": 920, "billing_period_months": 2, "bill_amount": 6120, "period_from": "2026-05-01",
        "period_to": "2026-06-30", "confidence_notes": ""}


def test_bill_reader_request_shape_and_mapping():
    fc = FakeClient(BILL)
    out = billread.read_bill(b"%PDF-1.4 fake", "application/pdf", client=fc)
    kw = fc.calls[0]
    assert kw["model"] == "claude-opus-5-5"
    assert kw["output_config"]["format"]["type"] == "json_schema"
    assert kw["messages"][0]["content"][0]["type"] == "document"
    assert out["fields"]["monthly_units"] == 460.0 and out["fields"]["phase"] == 3
    img = billread.read_bill(b"\xff\xd8\xff", "image/jpeg", client=FakeClient(BILL))
    assert img["fields"]["sanction_load_kw"] == 4


def test_bill_reader_refusal_and_missing_key(client, alpha_admin, monkeypatch):
    import pytest
    with pytest.raises(billread.BillReadError):
        billread.read_bill(b"x", "image/jpeg", client=FakeClient(BILL, stop="refusal"))
    # endpoint without an API key gives a clear message, not a crash
    ref = submit(client).json()["reference"]
    rid = _rid(client, alpha_admin, ref)
    from .conftest import jpeg_bytes
    f = client.post(f"/api/admin/requests/{rid}/files?kind=eb_bill", headers=alpha_admin,
                    files={"file": ("bill.jpg", jpeg_bytes(), "image/jpeg")}).json()
    r = client.post(f"/api/admin/files/{f['id']}/read-bill", headers=alpha_admin)
    assert r.status_code == 422 and "not configured" in r.json()["detail"]
    monkeypatch.setattr(billread, "_client", lambda: FakeClient(BILL))
    r = client.post(f"/api/admin/files/{f['id']}/read-bill", headers=alpha_admin)
    assert r.status_code == 200 and r.json()["extracted"]["fields"]["monthly_units"] == 460.0
    # values are suggestions only: the request inputs are unchanged until staff save overrides
    assert client.get(f"/api/admin/requests/{rid}", headers=alpha_admin).json()["request"]["overrides"] == {}


def test_industrial_three_phase_uses_multiple_inverters():
    s = CalcSettings(realistic_yield_low=4.0, realistic_yield_high=4.0)
    r = analyse(SiteInputs(target_kw=30, phase=3, category="industrial"), s, panels=[PANEL_615], inverters=INVERTERS,
                network_rates=NETWORK_RATES, price_rules=rules_276())
    inv = r["inverter"]
    assert inv["inverter"]["phase"] == 3 and inv["count"] == 3
    assert 1.0 <= inv["dc_ac_ratio"] <= 1.3
    codes = {w["code"] for w in r["warnings"]}
    assert "CEIG_INSPECTION" in codes and "MULTIPLE_INVERTERS" in codes
    inv_line = next(l for l in r["cost"]["lines"] if l["code"] == "INVERTER")
    assert inv_line["qty"] == "3"
    assert r["network_charge"]["percentage"] == s.network_pct_other
    sched = r["electrical"]["cable_schedule"]
    assert any(c["from"] == "Inverter 3 AC output" for c in sched)


def test_tamil_acknowledgement_email(client, database):
    ref = submit(client, language="ta", email="tamil@example.com", phone="9333333333").json()["reference"]
    with session_scope(database["alpha"]) as db:
        e = db.scalars(select(EmailLog).where(EmailLog.template == "acknowledgement")).all()
        mine = next(x for x in e if ref in x.subject)
        assert mine.language == "ta" and "குறிப்பு எண்" in mine.body_text
