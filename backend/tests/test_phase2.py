"""Phase 2 acceptance: staff produce and send a correct PDF quotation for a 3 kW and a 5 kW
home example, matching a hand calculation; customer views and accepts."""
import io
from decimal import Decimal

import pytest
from pypdf import PdfReader

from .conftest import login, submit


def _rid(client, h, ref):
    return next(i["id"] for i in client.get("/api/admin/requests", headers=h).json()["items"] if i["reference"] == ref)


def _pdf_text(data: bytes) -> str:
    return "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(data)).pages)


# Hand calculation, 3 kW home (5 x 615 Wp = 3.075 kWp sold as 3 kW; UTL 3.3 kW 1-ph inverter).
# Quantities from the design: DC cable 2x15 m string + 2x1 m DCDB-inverter = 32 m;
# AC cable 1 m inverter-ACDB + 15 m ACDB-panel = 16 m; 3 earth pits (2 + LA); LA cable 15 m.
HAND_3KW = [
    # code, qty, rate, gst%, amount, tax
    ("PANEL", 5, 19200, 5, 96000, 4800),
    ("INVERTER", 1, 27000, 5, 27000, 1350),
    ("STRUCTURE", 3, 6850, 18, 20550, 3699),
    ("ACDB_1PH", 1, 2100, 18, 2100, 378),
    ("DCDB", 1, 2500, 18, 2500, 450),
    ("EARTH_ELECTRODE", 3, 1500, 18, 4500, 810),
    ("EARTH_CHAMBER", 3, 450, 0, 1350, 0),
    ("PIPE_CLAMP", 1, 2500, 0, 2500, 0),
    ("DC_CABLE", 32, 103, 18, 3296, Decimal("593.28")),
    ("LABOUR", 3, 3500, 0, 10500, 0),
    ("TRANSPORT", 1, 8000, 0, 8000, 0),
    ("NET_METER_1PH", 1, 4850, 0, 4850, 0),
    ("STAMP", 1, 5000, 0, 5000, 0),
    ("AC_CABLE", 16, 65, 18, 1040, Decimal("187.20")),
    ("LA", 1, 2500, 18, 2500, 450),
    ("LA_CABLE", 15, 210, 18, 3150, 567),
]
# subtotal 1,94,836.00 ; tax 6,150.00 (5%) + 7,134.48 (18%) = 13,284.48 ; grand 2,08,120.48

# 5 kW home on a 3-phase supply: 9 x 615 Wp = 5.535 kWp sold as 5 kW; UTL GT-5K 1-ph inverter
# (DC/AC 1.107); 1-ph ACDB (inverter phase) but 3-phase net meter (supply phase), as in #276.
HAND_5KW = [
    ("PANEL", 9, 19200, 5, 172800, 8640),
    ("INVERTER", 1, 38000, 5, 38000, 1900),
    ("STRUCTURE", 5, 6850, 18, 34250, 6165),
    ("ACDB_1PH", 1, 2100, 18, 2100, 378),
    ("DCDB", 1, 2500, 18, 2500, 450),
    ("EARTH_ELECTRODE", 3, 1500, 18, 4500, 810),
    ("EARTH_CHAMBER", 3, 450, 0, 1350, 0),
    ("PIPE_CLAMP", 1, 2500, 0, 2500, 0),
    ("DC_CABLE", 32, 103, 18, 3296, Decimal("593.28")),
    ("LABOUR", 5, 3500, 0, 17500, 0),
    ("TRANSPORT", 1, 8000, 0, 8000, 0),
    ("NET_METER_3PH", 1, 4850, 0, 4850, 0),
    ("STAMP", 1, 5000, 0, 5000, 0),
    ("AC_CABLE", 16, 65, 18, 1040, Decimal("187.20")),
    ("LA", 1, 2500, 18, 2500, 450),
    ("LA_CABLE", 15, 210, 18, 3150, 567),
]
# subtotal 3,03,336.00 ; tax 10,540.00 + 9,600.48 = 20,140.48 ; grand 3,23,476.48


def _check(q, hand, subtotal, tax, grand):
    got = [(l["code"], Decimal(l["qty"]), Decimal(l["unit_price"]), Decimal(l["gst_pct"]), Decimal(l["amount"]),
            Decimal(l["tax"])) for l in q["lines"]]
    want = [(c, Decimal(qty), Decimal(rate), Decimal(g), Decimal(a), Decimal(str(t))) for c, qty, rate, g, a, t in hand]
    assert got == want
    assert sum(Decimal(str(a)) for *_, a, _t in hand) == Decimal(subtotal)
    assert Decimal(q["subtotal"]) == Decimal(subtotal)
    assert Decimal(q["tax"]) == Decimal(tax)
    assert Decimal(q["grand_total"]) == Decimal(grand)


@pytest.mark.parametrize("case", ["3kw", "5kw"])
def test_quotation_matches_hand_calculation(client, alpha_admin, case):
    if case == "3kw":
        # 360 units / (4.1 x 30) = 2.93 kW -> 5 panels
        r = submit(client, monthly_units=360, phase=1, sanction_load_kw=4, roof_area=600)
        hand, sub, tax, grand, words = HAND_3KW, "194836.00", "13284.48", "208120.48", "2,08,120.48"
    else:
        # 640 units / 123 = 5.20 kW -> 9 panels
        r = submit(client, monthly_units=640, phase=3, sanction_load_kw=8, roof_area=900)
        hand, sub, tax, grand, words = HAND_5KW, "303336.00", "20140.48", "323476.48", "3,23,476.48"
    ref = r.json()["reference"]
    rid = _rid(client, alpha_admin, ref)
    q = client.post(f"/api/admin/requests/{rid}/quotations", headers=alpha_admin)
    assert q.status_code == 200, q.text
    q = q.json()
    _check(q, hand, sub, tax, grand)

    pdf = client.get(f"/api/admin/quotations/{q['id']}/pdf", headers=alpha_admin)
    assert pdf.status_code == 200 and pdf.content[:5] == b"%PDF-"
    text = _pdf_text(pdf.content)
    assert f"Quotation# {q['number']}" in text or str(q["number"]) in text
    assert words in text                       # grand total printed in Indian grouping
    assert "Rupees" in text
    assert "approximate" in text.lower()       # disclaimer on every customer-facing estimate

    sent = client.post(f"/api/admin/quotations/{q['id']}/send", headers=alpha_admin).json()
    assert sent["status"] == "sent"
    token = sent["dev_quote_url"].split("/q/")[1]
    view = client.get(f"/api/public/alpha/quotations/{token}").json()
    assert view["grand_total"] == grand
    assert "cost_price" not in str(view) and "margin" not in str(view)
    acc = client.post(f"/api/public/alpha/quotations/{token}/accept").json()
    assert acc["status"] == "accepted"
    detail = client.get(f"/api/admin/requests/{rid}", headers=alpha_admin).json()
    assert detail["request"]["stage"] == "accepted"


def test_edit_lines_recomputes_server_side(client, alpha_admin):
    rid = _rid(client, alpha_admin, submit(client, monthly_units=360).json()["reference"])
    q = client.post(f"/api/admin/requests/{rid}/quotations", headers=alpha_admin).json()
    lines = q["lines"]
    lines[0]["unit_price"] = "20000"
    # a tampered client total is ignored
    lines[0]["total"] = "1"
    r = client.put(f"/api/admin/quotations/{q['id']}", headers=alpha_admin, json={"lines": lines}).json()
    assert Decimal(r["lines"][0]["amount"]) == Decimal(r["lines"][0]["qty"]) * 20000
    assert Decimal(r["grand_total"]) == Decimal(q["grand_total"]) + Decimal(r["lines"][0]["qty"]) * 800 * Decimal("1.05")
    # sent quotations are locked; revise makes a new number
    client.post(f"/api/admin/quotations/{q['id']}/send", headers=alpha_admin)
    assert client.put(f"/api/admin/quotations/{q['id']}", headers=alpha_admin, json={"notes": "x"}).status_code == 422
    rev = client.post(f"/api/admin/quotations/{q['id']}/revise", headers=alpha_admin).json()
    assert rev["number"] == q["number"] + 1 and rev["status"] == "draft"
    # audit log
    act = client.get(f"/api/admin/requests/{rid}/activity", headers=alpha_admin).json()["activity"]
    actions = {a["action"] for a in act}
    assert {"quotation_created", "quotation_edited", "quotation_sent", "quotation_revised"} <= actions


def test_quote_numbers_sequence_per_installer(client, alpha_admin, beta_admin):
    ra = _rid(client, alpha_admin, submit(client, slug="alpha").json()["reference"])
    rb = _rid(client, beta_admin, submit(client, slug="beta").json()["reference"])
    qa = client.post(f"/api/admin/requests/{ra}/quotations", headers=alpha_admin).json()
    qb = client.post(f"/api/admin/requests/{rb}/quotations", headers=beta_admin).json()
    qa2 = client.post(f"/api/admin/requests/{ra}/quotations", headers=alpha_admin).json()
    assert qa2["number"] == qa["number"] + 1
    assert qb["number"] >= 277
    # isolation
    assert client.get(f"/api/admin/quotations/{qa['id']}", headers=beta_admin).status_code == 404
    assert client.post(f"/api/admin/quotations/{qa['id']}/send", headers=beta_admin).status_code == 404


def test_customer_question_and_status_token_view(client, alpha_admin):
    sub = submit(client).json()
    rid = _rid(client, alpha_admin, sub["reference"])
    q = client.post(f"/api/admin/requests/{rid}/quotations", headers=alpha_admin).json()
    # not visible to the customer before staff press Send
    st = client.get(f"/api/public/alpha/requests/{sub['reference']}", params={"t": sub["status_token"]}).json()
    assert st["quotation_available"] is False
    assert client.get(f"/api/public/alpha/requests/{sub['reference']}/quotation",
                      params={"t": sub["status_token"]}).status_code == 404
    client.post(f"/api/admin/quotations/{q['id']}/send", headers=alpha_admin)
    st = client.get(f"/api/public/alpha/requests/{sub['reference']}", params={"t": sub["status_token"]}).json()
    assert st["quotation_available"] and st["status"] == "quotation_ready"
    v = client.get(f"/api/public/alpha/requests/{sub['reference']}/quotation", params={"t": sub["status_token"]})
    assert v.status_code == 200
    r = client.post(f"/api/public/alpha/requests/{sub['reference']}/quotation/question",
                    params={"t": sub["status_token"]}, json={"message": "Can you add a battery?"})
    assert r.status_code == 200
    act = client.get(f"/api/admin/requests/{rid}/activity", headers=alpha_admin).json()
    assert any(a["action"] == "customer_question" for a in act["activity"])
    assert any(e["template"] == "quotation_ready" and e["status"] == "sent" for e in act["emails"])


def test_internal_estimate_only_admin_sales(client, alpha_admin):
    rid = _rid(client, alpha_admin, submit(client).json()["reference"])
    q = client.post(f"/api/admin/requests/{rid}/quotations", headers=alpha_admin).json()
    eng = login(client, "alpha", "engineer@alpha.local")
    assert client.get(f"/api/admin/quotations/{q['id']}/pdf?internal=true", headers=eng).status_code == 403
    r = client.get(f"/api/admin/quotations/{q['id']}/pdf?internal=true", headers=alpha_admin)
    assert r.status_code == 200 and "INTERNAL" in _pdf_text(r.content).upper()
    tech = login(client, "alpha", "technician@alpha.local")
    assert client.get(f"/api/admin/quotations/{q['id']}", headers=tech).status_code == 403


def test_diagram_endpoints(client, alpha_admin):
    rid = _rid(client, alpha_admin, submit(client, monthly_units=640).json()["reference"])
    aid = client.get(f"/api/admin/requests/{rid}", headers=alpha_admin).json()["analysis"]["id"]
    for k in ("sld", "roof", "schedule"):
        r = client.get(f"/api/admin/analysis/{aid}/diagram/{k}", headers=alpha_admin)
        assert r.status_code == 200 and r.json()["svg"].startswith("<svg")


def test_amount_in_words():
    from app.services.quotations import inr, rupees_in_words
    assert rupees_in_words(Decimal("205451.20")) == "Rupees Two Lakh Five Thousand Four Hundred Fifty One and Twenty Paise Only"
    assert inr(Decimal("205451.2")) == "2,05,451.20"
    assert inr(Decimal("12345678.9")) == "1,23,45,678.90"
