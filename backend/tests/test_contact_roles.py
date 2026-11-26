"""Customer contact channel (email / WhatsApp) and the read-only "normal" staff role."""
from urllib.parse import unquote

from .conftest import PASSWORD, login, submit


def _rid(client, headers, ref):
    items = client.get("/api/admin/requests", headers=headers, params={"q": ref}).json()["items"]
    return next(i["id"] for i in items if i["reference"] == ref)


def test_email_or_whatsapp_required(client):
    r = submit(client, phone="9111100001", email=None, whatsapp=None, contact_pref="email")
    assert r.status_code == 422 and "WhatsApp" in r.text
    r = submit(client, phone="9111100002", email=None, whatsapp="9111100002", contact_pref="both")
    assert r.status_code == 422 and "email" in r.text.lower()
    r = submit(client, phone="9111100003", whatsapp="12345", contact_pref="whatsapp")
    assert r.status_code == 422


def test_whatsapp_only_customer_gets_whatsapp_link(client, alpha_admin):
    ref = submit(client, phone="9111100004", name="Ravi Kumar", email=None, whatsapp="+91 91111 00004",
                 contact_pref="whatsapp").json()["reference"]
    rid = _rid(client, alpha_admin, ref)
    d = client.get(f"/api/admin/requests/{rid}", headers=alpha_admin).json()
    assert d["customer"]["whatsapp"] == "9111100004" and d["customer"]["contact_pref"] == "whatsapp"
    q = client.post(f"/api/admin/requests/{rid}/quotations", headers=alpha_admin).json()
    sent = client.post(f"/api/admin/quotations/{q['id']}/send", headers=alpha_admin).json()
    assert sent["email_status"] == "no_email"
    wa = sent["whatsapp"]
    assert wa["number"] == "+919111100004"
    assert wa["url"].startswith("https://wa.me/919111100004?text=")
    assert sent["customer_url"] in unquote(wa["url"]) and "Ravi" in wa["text"]


def test_whatsapp_preference_skips_email(client, alpha_admin):
    ref = submit(client, phone="9111100005", email="pref@example.com", whatsapp="9111100005",
                 contact_pref="whatsapp").json()["reference"]
    rid = _rid(client, alpha_admin, ref)
    q = client.post(f"/api/admin/requests/{rid}/quotations", headers=alpha_admin).json()
    sent = client.post(f"/api/admin/quotations/{q['id']}/send", headers=alpha_admin).json()
    assert sent["email_status"] == "not_requested" and sent["whatsapp"]


def test_both_channels(client, alpha_admin):
    ref = submit(client, phone="9111100006", email="both@example.com", whatsapp="9111100006",
                 contact_pref="both").json()["reference"]
    rid = _rid(client, alpha_admin, ref)
    q = client.post(f"/api/admin/requests/{rid}/quotations", headers=alpha_admin).json()
    sent = client.post(f"/api/admin/quotations/{q['id']}/send", headers=alpha_admin).json()
    assert sent["email_status"] == "queued" and sent["whatsapp"]


def test_normal_role_sees_no_customer_details(client, alpha_admin):
    r = client.post("/api/admin/users", headers=alpha_admin, json={
        "email": "viewer@example.com", "name": "Viewer", "role": "normal", "password": PASSWORD, "active": True})
    assert r.status_code in (200, 201), r.text
    viewer = login(client, "alpha", "viewer@example.com")
    ref = submit(client, phone="9111100007", name="Secret Person", email="secret@example.com",
                 address="99 Private Lane", eb_consumer_no="0123456789").json()["reference"]
    rid = _rid(client, alpha_admin, ref)

    lst = client.get("/api/admin/requests", headers=viewer).json()["items"]
    row = next(i for i in lst if i["id"] == rid)
    assert row["customer_name"] == f"Customer {ref}" and row["phone_masked"] == ""
    # cannot search by customer name or phone
    assert client.get("/api/admin/requests", headers=viewer, params={"q": "Secret"}).json()["items"] == []

    d = client.get(f"/api/admin/requests/{rid}", headers=viewer)
    assert d.status_code == 200
    text = d.text
    for secret in ("Secret Person", "9111100007", "secret@example.com", "99 Private Lane", "0123456789"):
        assert secret not in text, secret
    body = d.json()
    assert body["hidden_customer_details"] and body["quotations"] == [] and body["request"]["status_url"] is None
    assert all(f["kind"] in ("roof_photo", "site_photo") for f in body["files"])
    assert "cost" not in (body["analysis"]["outputs"] or {})          # no prices
    aid = body["analysis"]["id"]
    assert client.get(f"/api/admin/analysis/{aid}/diagram/sld", headers=viewer).status_code == 200

    # read-only: no edits, quotations, projects, activity or email log
    assert client.patch(f"/api/admin/requests/{rid}", headers=viewer, json={"stage": "lost"}).status_code == 403
    assert client.post(f"/api/admin/requests/{rid}/quotations", headers=viewer).status_code == 403
    assert client.post(f"/api/admin/requests/{rid}/notes", headers=viewer, json={"text": "x"}).status_code == 403
    assert client.get(f"/api/admin/requests/{rid}/activity", headers=viewer).status_code == 403
    assert client.get("/api/admin/projects", headers=viewer).status_code == 403
    assert client.get("/api/admin/emails", headers=viewer).status_code == 403

    # staff who need contact details still see them
    full = client.get(f"/api/admin/requests/{rid}", headers=alpha_admin).json()
    assert full["customer"]["name"] == "Secret Person"
