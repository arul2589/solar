import json
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="solar-test-")
# Never inherit the app's DATABASE_URL: the session fixture drops all tables on Postgres.
# To test against Postgres, point TEST_DATABASE_URL at a separate, disposable database.
_test_url = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{_tmp}/test.sqlite3")
if _test_url == os.environ.get("DATABASE_URL"):
    raise RuntimeError("TEST_DATABASE_URL must not be the application database")
os.environ["DATABASE_URL"] = _test_url
os.environ["STORAGE_DIR"] = os.path.join(_tmp, "storage")
os.environ["ENVIRONMENT"] = "test"
os.environ["EMAIL_PROVIDER"] = "log"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests-only-0123456789"
os.environ.setdefault("PUBLIC_BASE_URL", "http://testserver")

import io  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

from app import db as dbmod  # noqa: E402
from app.db import Base  # noqa: E402
from app import models  # noqa: E402,F401
from app.ratelimit import reset as reset_rate_limits  # noqa: E402
from app.services.seed import seed_installer, seed_platform  # noqa: E402

PASSWORD = "Test-pass-123"


@pytest.fixture(scope="session", autouse=True)
def database():
    url = os.environ["DATABASE_URL"]
    if url.startswith("postgresql"):
        Base.metadata.drop_all(dbmod.engine)
    Base.metadata.create_all(dbmod.engine)
    seed_platform("owner@platform.test", PASSWORD)
    a = seed_installer("alpha", "Alpha Solar", admin_email="admin@alpha.test", admin_password=PASSWORD,
                       demo_staff=True)
    b = seed_installer("beta", "Beta Solar", admin_email="admin@beta.test", admin_password=PASSWORD,
                       demo_staff=True)
    yield {"alpha": a, "beta": b}


@pytest.fixture(autouse=True)
def _reset_limits():
    reset_rate_limits()
    yield


@pytest.fixture
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


def login(client, installer, email, password=PASSWORD):
    r = client.post("/api/auth/login", json={"installer": installer, "email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture
def alpha_admin(client):
    return login(client, "alpha", "admin@alpha.test")


@pytest.fixture
def beta_admin(client):
    return login(client, "beta", "admin@beta.test")


def jpeg_bytes(color=(200, 100, 50)):
    buf = io.BytesIO()
    Image.new("RGB", (40, 30), color).save(buf, format="JPEG")
    return buf.getvalue()


def submit(client, slug="alpha", **over):
    data = {
        "name": "Test Customer", "phone": "98765 43210", "email": "customer@example.com", "language": "en",
        "address": "1 Test Street, Coimbatore", "pincode": "641016", "district": "Coimbatore",
        "site_type": "home", "phase": 1, "sanction_load_kw": 5, "monthly_units": 450, "roof_type": "rcc",
        "roof_area": 600, "roof_area_unit": "sqft", "direction": "south", "shade": "none",
        "goal": "reduce_bill", "consent": True,
    }
    data.update(over)
    files = [("roof_photos", ("roof.jpg", jpeg_bytes(), "image/jpeg"))]
    r = client.post(f"/api/public/{slug}/requests", data={"data": json.dumps(data)}, files=files)
    return r
