"""Website savings calculator: sizes and savings only, never a price."""
import json

from app.services.estimate import shape_public_estimate

PRICE_WORDS = ("cost", "price", "total", "payback", "gst", "margin", "range_low", "range_high", "lines")


def _keys(obj, acc=None):
    acc = set() if acc is None else acc
    if isinstance(obj, dict):
        for k, v in obj.items():
            acc.add(k.lower())
            _keys(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _keys(v, acc)
    return acc


def test_estimate_home_from_bill(client):
    r = client.post("/api/public/alpha/estimate", json={"monthly_bill": 4000, "site_type": "home"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["system"]["nominal_kw"] >= 1
    assert body["system"]["panel_count"] >= 1
    assert body["savings"]["annual_high"] >= body["savings"]["annual_low"] > 0
    assert body["roof"]["recommended_m2"] > 0
    keys = _keys(body)
    assert not any(any(w in k for w in PRICE_WORDS) for k in keys), keys


def test_estimate_needs_bill_or_units(client):
    assert client.post("/api/public/alpha/estimate", json={"site_type": "home"}).status_code == 422


def test_estimate_commercial_three_phase(client):
    r = client.post("/api/public/alpha/estimate",
                    json={"monthly_units": 3000, "site_type": "commercial", "phase": 3})
    assert r.status_code == 200
    assert r.json()["system"]["dc_kwp"] > 5


def test_shape_strips_prices():
    full = {
        "ok": True, "monthly_units": 400, "monthly_units_source": "bill_amount", "system_kind": "on_grid",
        "sizing": {"nominal_kw": 3, "dc_kwp": 3.075, "panel_count": 5, "panel_wp": 615},
        "roof": {"rule_of_thumb": {"min_m2": 23, "recommended_m2": 29}},
        "generation": {"per_month_low": 370, "per_month_high": 420},
        "cost": {"totals": {"grand_total": "208120.48"}, "range_low": "1", "range_high": "2"},
        "savings": {"low": {"annual_saving": "24000.4", "payback_years": 8.7},
                    "high": {"annual_saving": "30000", "payback_years": 6.9}},
        "warnings": [{"code": "CEIG_INSPECTION"}, {"code": "NO_PRICE_LIST"}],
    }
    out = shape_public_estimate(full)
    text = json.dumps(out)
    assert "208120" not in text and "payback" not in text and "cost" not in text
    assert out["savings"]["monthly_low"] == 2000
    assert out["notes"] == ["CEIG_INSPECTION"]
