"""Knowledge base (RAG): upload, indexing (text PDF + vision for images), cited answers,
design notes for a request, roles and tenant isolation. OpenAI is replaced by a fake client."""
import hashlib
import math
import re

import pytest

from app.services import kb

from .conftest import jpeg_bytes, login, submit

DIM = 64


class FakeAI:
    """Deterministic stand-in for OpenAIClient: bag-of-words embeddings, canned chat and vision."""

    def __init__(self):
        self.chats = []
        self.vision_calls = 0

    def embed(self, texts):
        out = []
        for t in texts:
            v = [0.0] * DIM
            for w in re.findall(r"\w+", t.lower()):
                v[int(hashlib.md5(w.encode()).hexdigest(), 16) % DIM] += 1.0
            out.append(v)
        return out

    def chat(self, system, user):
        self.chats.append((system, user))
        return "Use 4 mm2 solar DC cable [1]."

    def chat_json(self, system, user):
        self.chats.append((system, user))
        return {"summary": "ok", "items": [{"topic": "Earthing and lightning protection", "design": "3 pits",
                                            "documents": "below 5 ohm", "verdict": "OK", "cite": [1]}]}

    def transcribe_image(self, image, content_type, prompt):
        self.vision_calls += 1
        return "DIAGRAM: three panels in series, string fuse 15 A, SPD in DCDB, earthing pit resistance below 5 ohm."


def text_pdf(body: str) -> bytes:
    from weasyprint import HTML
    return HTML(string=f"<html><body><p>{body}</p></body></html>").write_pdf()


CABLE_TEXT = ("DC cable selection. For rooftop solar strings use 4 mm2 copper solar DC cable for runs up to "
              "30 metres. Keep voltage drop below 2 percent. Use MC4 connectors of the same make on both sides. ") * 3


@pytest.fixture
def fake_ai(client):
    from app.main import app
    from app.routers.knowledge import get_ai
    ai = FakeAI()
    app.dependency_overrides[get_ai] = lambda: ai
    yield ai
    app.dependency_overrides.pop(get_ai, None)


def _upload(client, headers, files):
    return client.post("/api/admin/kb/documents", headers=headers,
                       files=[("files", (name, data, ctype)) for name, data, ctype in files])


def test_chunk_text_splits_with_overlap():
    text = ("Line about cables. " * 200).strip()
    chunks = kb.chunk_text(text, size=500, overlap=100)
    assert len(chunks) > 3
    assert all(len(c) <= 500 for c in chunks)
    assert kb.chunk_text("   ") == []


def test_upload_index_and_ask_with_citations(client, alpha_admin, database, fake_ai):
    r = _upload(client, alpha_admin, [("DC_Cable_Guide.pdf", text_pdf(CABLE_TEXT), "application/pdf"),
                                      ("wiring.jpg", jpeg_bytes((10, 200, 30)), "image/jpeg")])
    assert r.status_code == 200, r.text
    assert len(r.json()["added"]) == 2
    # duplicate is skipped
    again = _upload(client, alpha_admin, [("copy.pdf", text_pdf(CABLE_TEXT), "application/pdf")]).json()
    assert again["added"] == [] and "already" in again["skipped"][0]["reason"]

    assert kb.process_pending(database["alpha"], client=fake_ai) == 2
    docs = {d["filename"]: d for d in client.get("/api/admin/kb/documents", headers=alpha_admin).json()["items"]}
    pdf, img = docs["DC_Cable_Guide.pdf"], docs["wiring.jpg"]
    assert pdf["status"] == "ready" and pdf["chunk_count"] >= 1 and pdf["vision_pages"] == 0
    assert img["status"] == "ready" and img["vision_pages"] == 1
    assert fake_ai.vision_calls == 1
    assert pdf["title"] == "DC Cable Guide"

    ans = client.post("/api/admin/kb/ask", headers=alpha_admin, json={"question": "What DC cable size for strings?"})
    assert ans.status_code == 200, ans.text
    body = ans.json()
    assert "[1]" in body["answer"]
    assert body["sources"][0]["title"] == "DC Cable Guide"
    assert body["sources"][0]["page"] == 1
    # the model only saw retrieved excerpts, numbered
    assert "[1] DC Cable Guide, page 1" in fake_ai.chats[-1][1]

    f = client.get(f"/api/admin/kb/documents/{pdf['id']}/file", headers=alpha_admin)
    assert f.status_code == 200 and f.content[:5] == b"%PDF-"


def test_tenant_isolation_and_roles(client, alpha_admin, beta_admin, database, fake_ai):
    _upload(client, alpha_admin, [("alpha_only.pdf", text_pdf("Alpha secret earthing note. " * 20), "application/pdf")])
    kb.process_pending(database["alpha"], client=fake_ai)
    assert client.get("/api/admin/kb/documents", headers=beta_admin).json()["items"] == []
    beta_ans = client.post("/api/admin/kb/ask", headers=beta_admin, json={"question": "earthing note"}).json()
    assert beta_ans["sources"] == []
    alpha_doc = client.get("/api/admin/kb/documents", headers=alpha_admin).json()["items"][0]
    assert client.get(f"/api/admin/kb/documents/{alpha_doc['id']}/file", headers=beta_admin).status_code == 404

    tech = login(client, "alpha", "technician@alpha.local")
    assert _upload(client, tech, [("x.jpg", jpeg_bytes(), "image/jpeg")]).status_code == 403
    assert client.post("/api/admin/kb/ask", headers=tech, json={"question": "earthing note"}).status_code == 200
    eng = login(client, "alpha", "engineer@alpha.local")
    assert client.delete(f"/api/admin/kb/documents/{alpha_doc['id']}", headers=eng).status_code == 403


def test_ask_without_key_is_clear(client, alpha_admin):
    r = client.post("/api/admin/kb/ask", headers=alpha_admin, json={"question": "anything at all"})
    assert r.status_code == 503
    assert "OPENAI_API_KEY" in r.json()["detail"]


def test_design_notes_for_request(client, alpha_admin, database, fake_ai):
    _upload(client, alpha_admin, [("Protection.pdf", text_pdf(
        "String fuse and SPD in the DCDB. Earthing pit resistance must be below 5 ohm. Lightning arrester on roof. " * 6),
        "application/pdf")])
    kb.process_pending(database["alpha"], client=fake_ai)
    ref = submit(client).json()["reference"]
    items = client.get("/api/admin/requests", headers=alpha_admin).json()["items"]
    rid = next(i["id"] for i in items if i["reference"] == ref)
    r = client.post(f"/api/admin/requests/{rid}/design-notes", headers=alpha_admin, json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["sources"] and "kWp" in body["summary_text"]
    assert body["conflicts"] == 0 and body["items"][0]["verdict"] == "OK"
    system, user = fake_ai.chats[-1]
    assert "Never recalculate" in system
    assert "Design from the calculation engine" in user
    # no prices are sent to the model
    assert "grand_total" not in user and "₹" not in user


def test_vector_scores_are_finite(client, alpha_admin, database, fake_ai):
    _upload(client, alpha_admin, [("Tilt.pdf", text_pdf("Tilt angle equals latitude for fixed structures. " * 10),
                                   "application/pdf")])
    kb.process_pending(database["alpha"], client=fake_ai)
    from app.db import session_scope
    with session_scope(database["alpha"]) as db:
        hits = kb.search(db, "tilt angle latitude", fake_ai, k=3)
    assert hits and all(math.isfinite(h.score) for h in hits)
    assert hits[0].title == "Tilt"


def test_pending_documents_wait_for_key(client, alpha_admin, database):
    _upload(client, alpha_admin, [("Later.pdf", text_pdf("Inverter sizing note for later. " * 10), "application/pdf")])
    assert kb.process_pending(database["alpha"]) == 0          # no OPENAI_API_KEY in tests
    docs = client.get("/api/admin/kb/documents", headers=alpha_admin).json()["items"]
    assert next(d for d in docs if d["filename"] == "Later.pdf")["status"] == "pending"
