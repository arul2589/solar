"""Phase 1 acceptance: a customer submits a request, gets the acknowledgement email
(logged), and staff see the analysis. No price is ever shown to the customer."""
from sqlalchemy import select

from app.db import session_scope
from app.models import EmailLog

from .conftest import login, submit


def test_health(client):
    assert client.get("/api/health").json() == {"ok": True}


def test_installer_info_public(client):
    r = client.get("/api/public/alpha")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Alpha Solar"
    assert "en" in body["languages"] and "ta" in body["languages"]


def test_submit_request_ack_email_and_analysis(client, alpha_admin, database):
    r = submit(client)
    assert r.status_code == 200, r.text
    ref, token = r.json()["reference"], r.json()["status_token"]
    assert ref.startswith("SR")
    # customer response never contains a price
    assert "price" not in r.text.lower() and "grand_total" not in r.text

    # acknowledgement email queued and sent through the log provider
    with session_scope(database["alpha"]) as db:
        emails = db.scalars(select(EmailLog).where(EmailLog.template == "acknowledgement")).all()
        mine = [e for e in emails if ref in e.subject]
        assert mine and mine[0].status == "sent" and mine[0].provider_id.startswith("log-")
        assert "Rs" not in mine[0].body_text and "₹" not in mine[0].body_text
        assert mine[0].reply_to == "arulmurugan08@outlook.com"

    # status page
    st = client.get(f"/api/public/alpha/requests/{ref}", params={"t": token}).json()
    assert st["status"] == "under_review"          # auto-analysis moved it to 'analysed'
    assert st["quotation_available"] is False
    assert client.get(f"/api/public/alpha/requests/{ref}", params={"t": "wrong"}).status_code == 404

    # staff see it in the pipeline with analysis
    items = client.get("/api/admin/requests", headers=alpha_admin).json()["items"]
    row = next(i for i in items if i["reference"] == ref)
    assert row["stage"] == "analysed" and row["panels"] >= 1
    detail = client.get(f"/api/admin/requests/{row['id']}", headers=alpha_admin).json()
    a = detail["analysis"]["outputs"]
    assert a["sizing"]["panel_count"] >= 1
    assert a["roof"]["rule_of_thumb"]["min_m2"] > 0
    assert a["network_charge"]["units"] > 0
    assert a["cost"]["totals"]["grand_total"]
    assert detail["files"][0]["url"].startswith("/api/files/")
    # signed URL works, tampered URL does not
    assert client.get(detail["files"][0]["url"]).status_code == 200
    assert client.get(detail["files"][0]["url"].replace("sig=", "sig=x")).status_code == 403


def test_override_inputs_recalculates(client, alpha_admin):
    ref = submit(client).json()["reference"]
    items = client.get("/api/admin/requests", headers=alpha_admin).json()["items"]
    rid = next(i["id"] for i in items if i["reference"] == ref)
    pv = client.post(f"/api/admin/requests/{rid}/preview", headers=alpha_admin,
                     json={"overrides": {"panel_count": 9}}).json()
    assert pv["outputs"]["sizing"]["panel_count"] == 9
    r = client.patch(f"/api/admin/requests/{rid}", headers=alpha_admin, json={"overrides": {"panel_count": 9}})
    assert r.status_code == 200
    d = r.json()
    assert d["analysis"]["outputs"]["sizing"]["panel_count"] == 9
    assert len(d["analysis_runs"]) == 2


def test_validation_errors(client):
    r = submit(client, consent=False)
    assert r.status_code == 422
    r = submit(client, monthly_units=None)
    assert r.status_code == 422
    r = submit(client, phone="123")
    assert r.status_code == 422


def test_honeypot_stores_nothing(client, alpha_admin):
    before = len(client.get("/api/admin/requests", headers=alpha_admin).json()["items"])
    r = submit(client, website="http://spam.example")
    assert r.status_code == 200
    after = len(client.get("/api/admin/requests", headers=alpha_admin).json()["items"])
    assert before == after


def test_rate_limit(client):
    codes = [submit(client).status_code for _ in range(12)]
    assert 429 in codes


def test_upload_type_checked(client):
    import json as _j
    r = client.post("/api/public/alpha/requests",
                    data={"data": _j.dumps({"name": "X Y", "phone": "9876543210", "address": "abc st",
                                            "monthly_units": 300, "consent": True})},
                    files=[("roof_photos", ("evil.jpg", b"<?php echo 1; ?>", "image/jpeg"))])
    assert r.status_code == 422


def test_roles_technician_cannot_see_pipeline(client):
    tech = login(client, "alpha", "technician@alpha.local")
    assert client.get("/api/admin/requests", headers=tech).status_code == 403


def test_engineer_sees_no_margin(client):
    eng = login(client, "alpha", "engineer@alpha.local")
    ref = submit(client).json()["reference"]
    items = client.get("/api/admin/requests", headers=eng).json()["items"]
    rid = next(i["id"] for i in items if i["reference"] == ref)
    cost = client.get(f"/api/admin/requests/{rid}", headers=eng).json()["analysis"]["outputs"]["cost"]
    assert "margin" not in cost["totals"]


def test_wrong_password(client):
    r = client.post("/api/auth/login", json={"installer": "alpha", "email": "admin@alpha.test", "password": "nope"})
    assert r.status_code == 401


def test_otp_flow_dev(client):
    r = client.post("/api/public/alpha/otp/request", json={"phone": "9000000001"}).json()
    assert r["sent"] and len(r["dev_code"]) == 6
    bad = client.post("/api/public/alpha/otp/verify", json={"phone": "9000000001", "code": "000000"})
    if r["dev_code"] != "000000":
        assert bad.status_code == 400
    ok = client.post("/api/public/alpha/otp/verify", json={"phone": "9000000001", "code": r["dev_code"]})
    assert ok.status_code == 200 and ok.json()["phone_token"]
    tok = ok.json()["phone_token"]
    r2 = submit(client, phone="9000000001", phone_token=tok)
    assert r2.status_code == 200


def test_customer_magic_link_login(client):
    submit(client, email="magic@example.com", phone="9111111111")
    r = client.post("/api/public/alpha/customer/magic-link", json={"email": "magic@example.com"}).json()
    token = r["dev_link"].split("magic=")[1]
    s = client.post("/api/public/alpha/customer/session", json={"token": token}).json()
    mine = client.get("/api/customer/requests", headers={"Authorization": f"Bearer {s['token']}"}).json()
    assert len(mine) >= 1 and "price" not in str(mine).lower()


def test_settings_placeholders_visible(client, alpha_admin):
    s = client.get("/api/admin/settings", headers=alpha_admin).json()
    keys = {p["key"] for p in s["placeholders"]}
    assert "calc.realistic_yield" in keys and "network_rate.latest" in keys
    r = client.post("/api/admin/settings/placeholders", headers=alpha_admin,
                    json={"key": "calc.realistic_yield", "confirmed": True}).json()
    assert next(p for p in r["placeholders"] if p["key"] == "calc.realistic_yield")["confirmed"]


def test_settings_reject_bank_account_number(client, alpha_admin):
    r = client.put("/api/admin/settings/company", headers=alpha_admin,
                   json={"name": "X", "bank_account_number": "123456"})
    assert r.status_code == 422


def test_settings_drive_calculation(client, alpha_admin):
    """Changing the yield setting changes the suggested system size (no hard-coded yield)."""
    s = client.get("/api/admin/settings", headers=alpha_admin).json()["calc"]
    base = client.post("/api/admin/analyse", headers=alpha_admin,
                       json={"overrides": {"monthly_units": 600, "phase": 1}}).json()["outputs"]["sizing"]["panel_count"]
    client.put("/api/admin/settings/calc", headers=alpha_admin,
               json=s | {"realistic_yield_low": 3.0, "realistic_yield_high": 3.0})
    low = client.post("/api/admin/analyse", headers=alpha_admin,
                      json={"overrides": {"monthly_units": 600, "phase": 1}}).json()["outputs"]["sizing"]["panel_count"]
    client.put("/api/admin/settings/calc", headers=alpha_admin, json=s)
    assert low > base
