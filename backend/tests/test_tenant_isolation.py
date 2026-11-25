"""Tenant isolation: one installer can never read or change another installer's data."""
import pytest
from sqlalchemy import select

from app.db import TenantError, session_scope, tenant_session
from app.models import Customer, PriceItem, ServiceRequest, Setting

from .conftest import login, submit


def _rid(client, headers, ref):
    items = client.get("/api/admin/requests", headers=headers).json()["items"]
    return next((i["id"] for i in items if i["reference"] == ref), None)


def test_api_isolation_requests(client, alpha_admin, beta_admin):
    ref = submit(client, slug="alpha", name="Alpha Only").json()["reference"]
    rid = _rid(client, alpha_admin, ref)
    assert rid
    # beta cannot list, read, patch, preview or note alpha's request
    assert _rid(client, beta_admin, ref) is None
    assert client.get(f"/api/admin/requests/{rid}", headers=beta_admin).status_code == 404
    assert client.patch(f"/api/admin/requests/{rid}", headers=beta_admin, json={"stage": "lost"}).status_code == 404
    assert client.post(f"/api/admin/requests/{rid}/preview", headers=beta_admin, json={"overrides": {}}).status_code == 404
    assert client.post(f"/api/admin/requests/{rid}/notes", headers=beta_admin, json={"text": "x"}).status_code == 404
    assert client.get(f"/api/admin/requests/{rid}", headers=alpha_admin).json()["request"]["stage"] != "lost"


def test_api_isolation_catalogue(client, alpha_admin, beta_admin):
    a_items = client.get("/api/admin/price-items", headers=alpha_admin).json()
    target = a_items[0]["id"]
    beta_ids = {i["id"] for i in client.get("/api/admin/price-items", headers=beta_admin).json()}
    assert target not in beta_ids
    r = client.put(f"/api/admin/price-items/{target}", headers=beta_admin, json={"unit_price": "1"})
    assert r.status_code == 404
    assert client.delete(f"/api/admin/price-items/{target}", headers=beta_admin).status_code == 404


def test_api_isolation_settings(client, alpha_admin, beta_admin):
    client.put("/api/admin/settings/company", headers=alpha_admin, json={"name": "Alpha Renamed"})
    assert client.get("/api/admin/settings", headers=beta_admin).json()["company"]["name"] != "Alpha Renamed"
    assert client.get("/api/public/beta").json()["name"] != "Alpha Renamed"


def test_status_link_is_per_installer(client):
    r = submit(client, slug="alpha").json()
    assert client.get(f"/api/public/beta/requests/{r['reference']}", params={"t": r["status_token"]}).status_code == 404


def test_cannot_login_to_other_installer(client):
    r = client.post("/api/auth/login", json={"installer": "beta", "email": "admin@alpha.test",
                                             "password": "Test-pass-123"})
    assert r.status_code == 401


def test_orm_filter_scopes_every_query(database):
    with session_scope(database["alpha"]) as db:
        ids = {p.installer_id for p in db.scalars(select(PriceItem))}
        assert ids == {database["alpha"]}
        assert all(s.installer_id == database["alpha"] for s in db.scalars(select(Setting)))
        assert all(r.installer_id == database["alpha"] for r in db.scalars(select(ServiceRequest)))


def test_unscoped_session_refuses_tenant_tables():
    db = tenant_session(None)
    try:
        with pytest.raises(TenantError):
            db.scalars(select(Customer)).all()
    finally:
        db.close()


def test_cannot_write_into_another_tenant(database):
    db = tenant_session(database["alpha"])
    try:
        db.add(Customer(installer_id=database["beta"], name="x", phone="1"))
        with pytest.raises(TenantError):
            db.flush()
    finally:
        db.rollback()
        db.close()


def test_get_by_id_cannot_cross_tenant(database, client):
    submit(client, slug="beta", name="Beta Customer")
    with session_scope(database["beta"]) as db:
        beta_req = db.scalars(select(ServiceRequest)).first()
        bid = beta_req.id
    with session_scope(database["alpha"]) as db:
        assert db.get(ServiceRequest, bid) is None


def test_customer_token_scoped(client):
    submit(client, slug="beta", email="b-cust@example.com", phone="9222222222")
    link = client.post("/api/public/beta/customer/magic-link", json={"email": "b-cust@example.com"}).json()["dev_link"]
    tok = link.split("magic=")[1]
    # exchanging a beta magic token at alpha fails
    assert client.post("/api/public/alpha/customer/session", json={"token": tok}).status_code == 401


def test_platform_owner_lists_installers(client):
    h = login(client, "platform", "owner@platform.test")
    slugs = {i["slug"] for i in client.get("/api/platform/installers", headers=h).json()}
    assert {"alpha", "beta"} <= slugs
    # installer admins cannot use platform endpoints
    a = login(client, "alpha", "admin@alpha.test")
    assert client.get("/api/platform/installers", headers=a).status_code == 403
