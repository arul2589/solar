"""Password changes: own password (needs the current one) and admin reset of another user's password."""
import uuid

from .conftest import login


def _new_user(client, admin, role="sales", password="first-pass-123"):
    email = f"pw-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/admin/users", headers=admin,
                    json={"email": email, "name": "PW Test", "role": role, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["id"], email


def _login_status(client, email, password):
    return client.post("/api/auth/login", json={"installer": "alpha", "email": email, "password": password}).status_code


def test_change_own_password(client, alpha_admin):
    _, email = _new_user(client, alpha_admin)
    me = login(client, "alpha", email, "first-pass-123")
    bad = client.post("/api/auth/change-password", headers=me,
                      json={"current_password": "not-it-123", "new_password": "second-pass-456"})
    assert bad.status_code == 400
    short = client.post("/api/auth/change-password", headers=me,
                        json={"current_password": "first-pass-123", "new_password": "short"})
    assert short.status_code == 422
    ok = client.post("/api/auth/change-password", headers=me,
                     json={"current_password": "first-pass-123", "new_password": "second-pass-456"})
    assert ok.status_code == 200, ok.text
    assert _login_status(client, email, "first-pass-123") == 401
    assert _login_status(client, email, "second-pass-456") == 200


def test_change_password_needs_sign_in(client):
    r = client.post("/api/auth/change-password", json={"current_password": "a" * 8, "new_password": "b" * 8})
    assert r.status_code == 401


def test_admin_resets_user_password(client, alpha_admin):
    uid, email = _new_user(client, alpha_admin)
    r = client.post(f"/api/admin/users/{uid}/password", headers=alpha_admin, json={"password": "reset-pass-789"})
    assert r.status_code == 200, r.text
    assert _login_status(client, email, "reset-pass-789") == 200
    assert _login_status(client, email, "first-pass-123") == 401


def test_only_admin_can_reset_passwords(client, alpha_admin):
    uid, _ = _new_user(client, alpha_admin)
    _, sales_email = _new_user(client, alpha_admin, password="sales-pass-123")
    sales = login(client, "alpha", sales_email, "sales-pass-123")
    r = client.post(f"/api/admin/users/{uid}/password", headers=sales, json={"password": "hacked-pass-1"})
    assert r.status_code == 403


def test_admin_cannot_reset_other_installers_user(client, alpha_admin, beta_admin):
    uid, _ = _new_user(client, alpha_admin)
    r = client.post(f"/api/admin/users/{uid}/password", headers=beta_admin, json={"password": "cross-tenant-1"})
    assert r.status_code == 404
