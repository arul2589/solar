"""Security hardening: login brute-force limit, account probing, 2FA removal, production settings."""
import pyotp

from app.config import Config

from .conftest import PASSWORD, login


def _try(client, email, password, installer="alpha"):
    return client.post("/api/auth/login", json={"installer": installer, "email": email, "password": password})


def test_login_locks_after_repeated_failures(client):
    for i in range(8):
        assert _try(client, "admin@alpha.test", f"wrong-{i}").status_code == 401
    # even the right password is refused while locked
    r = _try(client, "admin@alpha.test", PASSWORD)
    assert r.status_code == 429 and "15 minutes" in r.json()["detail"]
    # other accounts are not affected
    assert _try(client, "admin@beta.test", PASSWORD, installer="beta").status_code == 200


def test_unknown_account_same_answer(client):
    a = _try(client, "nobody@alpha.test", "whatever-123")
    b = _try(client, "admin@alpha.test", "whatever-123")
    c = _try(client, "admin@alpha.test", "whatever-123", installer="no-such-installer")
    assert a.status_code == b.status_code == c.status_code == 401
    assert a.json() == b.json() == c.json()


def test_successful_login_clears_failures(client):
    for i in range(5):
        _try(client, "engineer@alpha.local", f"bad-{i}")
    assert _try(client, "engineer@alpha.local", PASSWORD).status_code == 200
    for i in range(5):
        _try(client, "engineer@alpha.local", f"bad-again-{i}")
    assert _try(client, "engineer@alpha.local", PASSWORD).status_code == 200


def test_disabling_2fa_needs_a_current_code(client):
    h = login(client, "alpha", "sales@alpha.local")
    secret = client.post("/api/auth/2fa/setup", headers=h).json()["secret"]
    assert client.post("/api/auth/2fa/enable", headers=h,
                       json={"secret": secret, "code": pyotp.TOTP(secret).now()}).status_code == 200
    try:
        assert client.post("/api/auth/2fa/disable", headers=h, json={}).status_code == 422
        assert client.post("/api/auth/2fa/disable", headers=h, json={"code": "000000"}).status_code == 400
    finally:
        r = client.post("/api/auth/2fa/disable", headers=h, json={"code": pyotp.TOTP(secret).now()})
        assert r.status_code == 200


def test_dev_helpers_only_on_local_addresses():
    assert Config(environment="development", public_base_url="http://localhost:8088").is_dev
    assert not Config(environment="development", public_base_url="https://solar.example.com").is_dev
    assert not Config(environment="production", public_base_url="http://localhost:8088").is_dev


def test_production_settings_check():
    bad = Config(environment="production", secret_key="dev-secret-change-me",
                 database_url="postgresql+psycopg://solar:solar-dev-password@db/solar",
                 public_base_url="http://solar.example.com").production_problems()
    assert len(bad) == 3
    good = Config(environment="production", secret_key="x" * 48,
                  database_url="postgresql+psycopg://solar:Str0ng-Pass@db/solar",
                  public_base_url="https://solar.example.com").production_problems()
    assert good == []


def test_dev_otp_code_not_returned_outside_dev(client, monkeypatch):
    from app import config
    real = config.get_config()
    monkeypatch.setattr(real, "environment", "production")
    r = client.post("/api/public/alpha/otp/request", json={"phone": "9000077777", "purpose": "verify"}).json()
    assert "dev_code" not in r
