"""Design check gate before sending, settings suggestions from documents, design explanation."""
import pytest

from app.services import kb

from .conftest import PASSWORD, login, submit
from .test_knowledge import FakeAI, _upload, text_pdf


class ReviewAI(FakeAI):
    def __init__(self, verdict="CONFLICT", values=None):
        super().__init__()
        self.verdict, self.values = verdict, values or {}

    def chat_json(self, system, user):
        self.chats.append((system, user))
        if "checking a rooftop PV design" in system:
            return {"summary": "One conflict.", "items": [
                {"topic": "DC cable", "design": "4 mm2", "documents": "Use 6 mm2 above 30 m", "verdict": self.verdict, "cite": [1]},
                {"topic": "Earthing and lightning protection", "design": "3 pits", "documents": "2 pits minimum",
                 "verdict": "OK", "cite": [1]}]}
        return {"found": True, "values": self.values, "explanation": "Generation is 4 to 4.6 units per kW per day [1].",
                "cite": [1]}


@pytest.fixture
def ai_on(client, monkeypatch, database):
    """OpenAI 'configured' (fake client) with one indexed document."""
    from app import config
    from app.main import app
    from app.routers.knowledge import get_ai
    monkeypatch.setattr(config.get_config(), "openai_api_key", "test-key")
    holder = {"ai": ReviewAI()}
    app.dependency_overrides[get_ai] = lambda: holder["ai"]
    yield holder
    app.dependency_overrides.pop(get_ai, None)


def _quote(client, headers, phone):
    ref = submit(client, phone=phone).json()["reference"]
    items = client.get("/api/admin/requests", headers=headers, params={"q": ref}).json()["items"]
    rid = next(i["id"] for i in items if i["reference"] == ref)
    q = client.post(f"/api/admin/requests/{rid}/quotations", headers=headers).json()
    return rid, q


def _index_doc(client, headers, database, text):
    _upload(client, headers, [("Guide.pdf", text_pdf(text * 8), "application/pdf")])
    kb.process_pending(database["alpha"], client=FakeAI())


def test_send_needs_design_check_and_conflict_review(client, alpha_admin, database, ai_on):
    _index_doc(client, alpha_admin, database, "DC cable 6 mm2 for runs above 30 metres. Two earth pits minimum. ")
    rid, q = _quote(client, alpha_admin, "9222200001")
    r = client.post(f"/api/admin/quotations/{q['id']}/send", headers=alpha_admin, json={})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "design_review_required"

    rv = client.post(f"/api/admin/requests/{rid}/design-notes", headers=alpha_admin, json={}).json()
    assert rv["conflicts"] == 1 and any(i["verdict"] == "CONFLICT" for i in rv["items"])
    # topics the model skipped are listed as not covered
    assert any(i["verdict"] == "NOT_COVERED" for i in rv["items"])
    got = client.get(f"/api/admin/requests/{rid}/design-review", headers=alpha_admin).json()
    assert got["review"]["id"] == rv["id"] and got["kb_ready"]

    r = client.post(f"/api/admin/quotations/{q['id']}/send", headers=alpha_admin, json={})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "conflicts_unacknowledged"

    assert client.post(f"/api/admin/design-reviews/{rv['id']}/acknowledge", headers=alpha_admin,
                       json={"note": "x"}).status_code == 422          # a real reason is required
    ack = client.post(f"/api/admin/design-reviews/{rv['id']}/acknowledge", headers=alpha_admin,
                      json={"note": "Run is 18 m, 4 mm2 is fine"}).json()
    assert ack["acknowledged"]
    assert client.post(f"/api/admin/quotations/{q['id']}/send", headers=alpha_admin, json={}).status_code == 200


def test_no_conflicts_sends_after_check(client, alpha_admin, database, ai_on):
    ai_on["ai"] = ReviewAI(verdict="OK")
    _index_doc(client, alpha_admin, database, "String fuse rating guidance for rooftop arrays. ")
    rid, q = _quote(client, alpha_admin, "9222200002")
    client.post(f"/api/admin/requests/{rid}/design-notes", headers=alpha_admin, json={})
    assert client.post(f"/api/admin/quotations/{q['id']}/send", headers=alpha_admin, json={}).status_code == 200


def test_admin_can_skip_with_reason_sales_cannot(client, alpha_admin, database, ai_on):
    _index_doc(client, alpha_admin, database, "Lightning arrester on a separate pit. ")
    rid, q = _quote(client, alpha_admin, "9222200003")
    sales = login(client, "alpha", "sales@alpha.local")
    r = client.post(f"/api/admin/quotations/{q['id']}/send", headers=sales, json={"skip_review_reason": "customer waiting"})
    assert r.status_code == 409
    r = client.post(f"/api/admin/quotations/{q['id']}/send", headers=alpha_admin, json={"skip_review_reason": "ok"})
    assert r.status_code == 409                                        # reason too short
    r = client.post(f"/api/admin/quotations/{q['id']}/send", headers=alpha_admin,
                    json={"skip_review_reason": "Owner approved by phone"})
    assert r.status_code == 200


def test_conflict_without_citation_becomes_check():
    items = kb._clean_items([{"topic": "DC cable", "verdict": "conflict", "cite": []},
                             {"topic": "X", "verdict": "weird", "cite": [99]}], 3, ["DC cable"])
    assert items[0]["verdict"] == "CHECK" and items[1]["verdict"] == "CHECK" and items[1]["cite"] == []


def test_suggest_and_apply_setting(client, alpha_admin, database, ai_on):
    ai_on["ai"] = ReviewAI(values={"realistic_yield_low": 4.0, "realistic_yield_high": 4.6})
    _index_doc(client, alpha_admin, database, "A 1 kW rooftop system generates about 4 to 4.6 units per day. ")
    keys = client.get("/api/admin/settings/suggestable", headers=alpha_admin).json()
    assert keys["kb_ready"] and keys["keys"]["calc.realistic_yield"] is True
    before = client.get("/api/admin/settings", headers=alpha_admin).json()["calc"]
    sg = client.post("/api/admin/settings/placeholders/calc.realistic_yield/suggest", headers=alpha_admin).json()
    assert sg["values"] == {"realistic_yield_low": 4.0, "realistic_yield_high": 4.6} and sg["sources"]
    bad = client.post("/api/admin/settings/placeholders/calc.realistic_yield/apply", headers=alpha_admin,
                      json={"values": {"realistic_yield_low": 40}})
    assert bad.status_code == 422
    ok = client.post("/api/admin/settings/placeholders/calc.realistic_yield/apply", headers=alpha_admin,
                     json={"values": sg["values"], "sources": sg["sources"]})
    assert ok.status_code == 200
    after = client.get("/api/admin/settings", headers=alpha_admin).json()["calc"]
    assert after["realistic_yield_low"] == 4.0 and after["realistic_yield_high"] == 4.6
    assert after["cuf_tnerc"] == before["cuf_tnerc"]                   # other settings untouched
    # restore for other tests
    client.post("/api/admin/settings/placeholders/calc.realistic_yield/apply", headers=alpha_admin,
                json={"values": {"realistic_yield_low": before["realistic_yield_low"],
                                 "realistic_yield_high": before["realistic_yield_high"]}})
    eng = login(client, "alpha", "engineer@alpha.local")
    assert client.post("/api/admin/settings/placeholders/calc.realistic_yield/suggest", headers=eng).status_code == 403


def test_out_of_range_suggestion_is_dropped(client, alpha_admin, database, ai_on):
    ai_on["ai"] = ReviewAI(values={"commercial_flat_rate": 950})
    _index_doc(client, alpha_admin, database, "Commercial tariff per unit in Tamil Nadu. ")
    sg = client.post("/api/admin/settings/placeholders/calc.commercial_flat_rate/suggest", headers=alpha_admin).json()
    assert sg["values"] == {} and sg["problems"]


def test_design_explanation_and_pdf_html():
    from app.routers.projects import _simple_html

    class Ex(FakeAI):
        def chat(self, system, user):
            assert "Tamil" in system and "Design summary" in user
            return "## ஏன் 9 பேனல்கள்\n- **4 mm2** DC கேபிள் [1]\n<script>x</script>"
    html = _simple_html(Ex().chat("Write in Tamil", "Design summary: x"))
    assert "<h3>" in html and "<li><strong>4 mm2</strong>" in html and "<script>" not in html
