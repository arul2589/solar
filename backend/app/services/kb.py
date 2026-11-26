"""Document knowledge base (RAG) for staff: calculation, plan and design reference.

Documents (PDFs and images from reference/ or uploaded by staff) are split into page-level text
(scanned pages and images are transcribed by a vision model), cut into chunks, embedded and stored
per installer. Staff questions are answered only from retrieved chunks, with [n] citations.

The calculation engine (solarcalc) stays the source of truth for every number in an analysis or
quotation. The knowledge base explains and cross-checks; it never changes a calculation.
"""
from __future__ import annotations

import hashlib
import io
import logging
import math
import re
import threading
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Optional

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..db import session_scope, utcnow
from ..models import KbChunk, KbDocument
from . import storage
from .openai_client import AIError, OpenAIClient

log = logging.getLogger("kb")

MAX_DOC_BYTES = 40 * 1024 * 1024
CHUNK_CHARS = 1200
CHUNK_OVERLAP = 200
MIN_TEXT_CHARS = 80              # a PDF page with less text than this is treated as a scan
RENDER_ZOOM = 2.0                # ~144 dpi for scanned pages
MAX_RENDER_PX = 2000

TRANSCRIBE_PROMPT = (
    "This is one page or image from a solar PV training book, technical note, government form, datasheet or "
    "quotation used by a rooftop solar installer in Tamil Nadu, India. Transcribe ALL text exactly as written, "
    "in reading order (English and Tamil). Write formulas in plain text, e.g. 'I = P / V'. Reproduce tables as "
    "rows separated by ' | '. For every diagram, wiring drawing or photo, add a section 'DIAGRAM:' describing "
    "the components, how they are connected (series/parallel, polarity, protection devices, earthing), and every "
    "value or label shown. Do not add information that is not on the page. Output plain text only."
)

SYSTEM_ANSWER = (
    "You are the technical reference assistant for staff of a rooftop solar installer in Tamil Nadu, India. "
    "Answer ONLY from the numbered excerpts provided. Cite every fact with its excerpt number in square "
    "brackets, e.g. [2]. If the excerpts do not contain the answer, say clearly that the documents do not cover "
    "it - never guess numbers, cable sizes, ratings or rules. Show formulas and a worked example when the "
    "excerpts give one. Keep answers short and practical. If excerpts disagree, say so and cite both. Answer in "
    "the language of the question (English or Tamil)."
)

SYSTEM_NOTES = (
    "You are a senior solar design engineer reviewing a rooftop PV design produced by a calculation engine. "
    "Using ONLY the numbered reference excerpts, write design review notes for the installer's engineer. "
    "For each topic give: what the design has, what the reference documents say (with [n] citations), and a "
    "verdict: OK, CHECK (needs site confirmation) or CONFLICT (documents suggest something different). "
    "Never change or recalculate the engine's numbers yourself and never invent values; if the documents say "
    "nothing on a topic, write 'Not covered by the documents'. Use short headings and bullet points."
)


# ------------------------------------------------------------------ storage of uploads
class KbUploadError(ValueError):
    pass


def save_document(db: Session, data: bytes, filename: str, *, uploaded_by: Optional[int],
                  title: Optional[str] = None) -> tuple[Optional[KbDocument], Optional[str]]:
    """Store a PDF or image as a pending document. Returns (doc, None) or (None, reason it was skipped)."""
    if not data:
        return None, "empty file"
    if len(data) > MAX_DOC_BYTES:
        return None, f"too large (max {MAX_DOC_BYTES // (1024 * 1024)} MB)"
    kind = storage._sniff(data)  # noqa: SLF001 - same sniffing rules as other uploads
    if kind == "application/pdf":
        ctype, ext = "application/pdf", "pdf"
    elif kind in ("image/jpeg", "image/png", "image/webp"):
        try:
            data = storage.reencode_image(data)
        except storage.UploadError as exc:
            return None, str(exc)
        ctype, ext = "image/jpeg", "jpg"
    else:
        return None, "only PDF, JPEG, PNG or WEBP files are supported"
    sha = hashlib.sha256(data).hexdigest()
    if db.scalar(select(KbDocument.id).where(KbDocument.sha256 == sha)):
        return None, "already in the knowledge base"
    key = f"{db.info['installer_id']}/kb/{uuid.uuid4().hex}.{ext}"
    storage.put_bytes(key, data)
    doc = KbDocument(title=(title or _title_from(filename))[:300], filename=filename[:300], storage_key=key,
                     content_type=ctype, size=len(data), sha256=sha, status="pending", uploaded_by=uploaded_by)
    db.add(doc)
    db.flush()
    return doc, None


def _title_from(filename: str) -> str:
    base = re.sub(r"\.(pdf|jpe?g|png|webp)$", "", filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1], flags=re.I)
    base = re.sub(r"\.(jpe?g)$", "", base, flags=re.I)
    return re.sub(r"[_]+", " ", base).strip(" .") or "Document"


# ------------------------------------------------------------------ text extraction
def extract_pages(data: bytes, content_type: str, client: Any) -> list[tuple[int, str, str]]:
    """Return [(page_number, text, method)] where method is 'text' or 'vision'."""
    if content_type != "application/pdf":
        return [(1, client.transcribe_image(data, content_type, TRANSCRIBE_PROMPT), "vision")]
    import pypdfium2 as pdfium  # Apache-2.0 / BSD (PDFium)
    out = []
    pdf = pdfium.PdfDocument(data)
    try:
        for i in range(len(pdf)):
            page = pdf[i]
            text = page.get_textpage().get_text_range() or ""
            if len(text.strip()) >= MIN_TEXT_CHARS:
                out.append((i + 1, text, "text"))
                continue
            w, h = page.get_size()
            scale = min(RENDER_ZOOM, MAX_RENDER_PX / max(w, h, 1))
            img = page.render(scale=scale).to_pil().convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=75)
            out.append((i + 1, client.transcribe_image(buf.getvalue(), "image/jpeg", TRANSCRIBE_PROMPT), "vision"))
    finally:
        pdf.close()
    return out


def chunk_text(text: str, size: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            # prefer to break at a paragraph, line or sentence end
            window = text[start:end]
            cut = max(window.rfind("\n\n"), window.rfind("\n"), window.rfind(". "))
            if cut > size * 0.5:
                end = start + cut + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


# ------------------------------------------------------------------ ingestion
def ingest(db: Session, doc: KbDocument, client: Any) -> int:
    """Extract, chunk and embed one document (replacing older chunks). Returns chunk count."""
    data = storage.get_bytes(doc.storage_key)
    pages = extract_pages(data, doc.content_type, client)
    rows: list[tuple[int, str]] = []
    for page_no, text, _method in pages:
        for c in chunk_text(text):
            rows.append((page_no, c))
    vectors = client.embed([f"{doc.title} (page {p})\n{t}" for p, t in rows]) if rows else []
    db.query(KbChunk).filter(KbChunk.document_id == doc.id).delete(synchronize_session=False)
    for n, ((page_no, text), vec) in enumerate(zip(rows, vectors)):
        db.add(KbChunk(document_id=doc.id, page=page_no, ordinal=n, text=text, embedding=[round(x, 6) for x in vec]))
    doc.pages = len(pages)
    doc.vision_pages = sum(1 for _, _, m in pages if m == "vision")
    doc.chunk_count = len(rows)
    doc.status = "ready"
    doc.error = None
    doc.updated_at = utcnow()
    _CACHE.pop(db.info["installer_id"], None)
    return len(rows)


def claim(db: Session, doc_id: int) -> bool:
    res = db.execute(update(KbDocument).where(KbDocument.id == doc_id, KbDocument.status == "pending")
                     .values(status="processing", updated_at=utcnow()))
    db.commit()
    return res.rowcount == 1


def process_pending(installer_id: int, client: Any = None, limit: int = 5) -> int:
    """Process up to `limit` pending documents for one installer. Safe to run from several processes."""
    done = 0
    if client is None:
        from ..config import get_config
        if not get_config().openai_api_key:
            return 0          # not configured yet: leave documents pending until OPENAI_API_KEY is set
    with session_scope(installer_id) as db:
        stale = utcnow() - timedelta(minutes=30)
        db.execute(update(KbDocument).where(KbDocument.status == "processing", KbDocument.updated_at < stale)
                   .values(status="pending"))
        ids = list(db.scalars(select(KbDocument.id).where(KbDocument.status == "pending")
                              .order_by(KbDocument.id).limit(limit)))
    for doc_id in ids:
        with session_scope(installer_id) as db:
            if not claim(db, doc_id):
                continue
            doc = db.get(KbDocument, doc_id)
            try:
                c = client or OpenAIClient()
                ingest(db, doc, c)
                done += 1
            except AIError as exc:
                doc.status, doc.error = "error", str(exc)[:500]
            except Exception as exc:  # noqa: BLE001
                log.exception("kb ingest failed for document %s", doc_id)
                doc.status, doc.error = "error", f"Could not read this file ({type(exc).__name__})."
            doc.updated_at = utcnow()
    return done


def installers_with_pending() -> list[int]:
    with session_scope(None, bypass=True) as db:
        return list(db.scalars(select(KbDocument.installer_id)
                               .where(KbDocument.status.in_(("pending", "processing"))).distinct()))


# ------------------------------------------------------------------ retrieval
@dataclass
class Hit:
    chunk_id: int
    document_id: int
    title: str
    page: int
    text: str
    score: float


_CACHE: dict[int, tuple[tuple, list]] = {}
_CACHE_LOCK = threading.Lock()


def _load(db: Session) -> list:
    iid = db.info["installer_id"]
    sig = tuple(db.execute(select(func.count(KbChunk.id), func.max(KbChunk.id))).one())
    with _CACHE_LOCK:
        hit = _CACHE.get(iid)
        if hit and hit[0] == sig:
            return hit[1]
    rows = db.execute(select(KbChunk.id, KbChunk.document_id, KbDocument.title, KbChunk.page, KbChunk.text,
                             KbChunk.embedding).join(KbDocument, KbDocument.id == KbChunk.document_id)
                      .where(KbDocument.status == "ready")).all()
    items = []
    for r in rows:
        vec = r.embedding or []
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        items.append((r.id, r.document_id, r.title, r.page, r.text, vec, norm))
    with _CACHE_LOCK:
        _CACHE[iid] = (sig, items)
    return items


_WORD = re.compile(r"[\w஀-௿]+", re.UNICODE)


def search(db: Session, query: str, client: Any, k: int = 8) -> list[Hit]:
    items = _load(db)
    if not items:
        return []
    qv = client.embed([query])[0]
    qn = math.sqrt(sum(x * x for x in qv)) or 1.0
    terms = {w.lower() for w in _WORD.findall(query) if len(w) > 2}
    scored = []
    for cid, did, title, page, text, vec, norm in items:
        if len(vec) != len(qv):
            continue
        cos = sum(a * b for a, b in zip(qv, vec)) / (qn * norm)
        low = text.lower()
        kw = (sum(1 for t in terms if t in low) / len(terms)) if terms else 0.0
        scored.append((cos + 0.15 * kw, cid, did, title, page, text))
    scored.sort(reverse=True)
    hits, per_page = [], {}
    for s, cid, did, title, page, text in scored:
        key = (did, page)
        if per_page.get(key, 0) >= 2:
            continue
        per_page[key] = per_page.get(key, 0) + 1
        hits.append(Hit(cid, did, title, page, text, round(s, 4)))
        if len(hits) >= k:
            break
    return hits


def _excerpts(hits: list[Hit]) -> str:
    return "\n\n".join(f"[{i}] {h.title}, page {h.page}:\n{h.text}" for i, h in enumerate(hits, start=1))


def _sources(hits: list[Hit]) -> list[dict]:
    return [{"n": i, "document_id": h.document_id, "title": h.title, "page": h.page, "score": h.score,
             "snippet": h.text[:400]} for i, h in enumerate(hits, start=1)]


def answer(db: Session, question: str, client: Any, k: int = 8) -> dict:
    hits = search(db, question, client, k=k)
    if not hits:
        return {"answer": "No documents are indexed yet. Upload documents in Knowledge first.", "sources": []}
    text = client.chat(SYSTEM_ANSWER, f"Reference excerpts:\n\n{_excerpts(hits)}\n\nQuestion: {question}")
    return {"answer": text, "sources": _sources(hits)}


# ------------------------------------------------------------------ design review for a request
NOTE_TOPICS = [
    "string sizing open circuit voltage Voc temperature correction inverter maximum DC voltage MPPT range",
    "DC cable size selection voltage drop MC4 connector solar cable",
    "DC fuse SPD surge protection DCDB isolator rating",
    "AC cable MCB RCCB ACDB inverter output protection",
    "earthing earth pit lightning arrester resistance",
    "mounting structure tilt angle row spacing shadow roof area per kW",
    "net metering documents TANGEDCO application network charges",
    "battery inverter charge controller sizing backup hours",
]


def design_summary(outputs: dict, inputs: dict) -> str:
    """Plain-text summary of an engine analysis, used as the subject of the design review."""
    sz = outputs.get("sizing") or {}
    panel = outputs.get("panel") or {}
    inv = (outputs.get("inverter") or {}).get("inverter") or {}
    st = (outputs.get("inverter") or {}).get("strings") or {}
    el = outputs.get("electrical") or {}
    roof = outputs.get("roof") or {}
    lay = roof.get("layout") or {}
    lines = [
        f"System type: {outputs.get('system_kind')}; supply {inputs.get('phase')}-phase; category {inputs.get('category')}",
        f"Size: {sz.get('panel_count')} x {panel.get('wp')} Wp panels ({panel.get('model')}) = {sz.get('dc_kwp')} kWp",
        f"Inverter: {(outputs.get('inverter') or {}).get('count', 1)} x {inv.get('model')} {inv.get('ac_kw')} kW "
        f"{inv.get('phase')}-phase, max DC {inv.get('max_dc_voltage')} V, MPPT {inv.get('mppt_min_v')}-{inv.get('mppt_max_v')} V, "
        f"DC/AC ratio {(outputs.get('inverter') or {}).get('dc_ac_ratio')}",
        f"Strings: {st.get('strings')}; string Voc at cold {st.get('string_voc_cold_max')} V; "
        f"Vmp hot {st.get('string_vmp_hot_min')} V; modules per string allowed {st.get('modules_per_string_min')}-{st.get('modules_per_string_max')}",
        f"DC cable {el.get('dc_cable_mm2')} mm2 x {el.get('dc_cable_total_m')} m; AC cable {el.get('ac_cable_mm2')} mm2 x {el.get('ac_cable_total_m')} m",
        f"Protection: {el.get('protection')}",
        f"Earthing pits: {el.get('earthing_pits')}; lightning arrester: {el.get('lightning_arrester')}",
        f"Roof: needs {(roof.get('rule_of_thumb') or {}).get('min_m2')}-{(roof.get('rule_of_thumb') or {}).get('recommended_m2')} m2, "
        f"available {roof.get('available_m2')} m2; layout {lay.get('rows')} rows x {lay.get('per_row')}; tilt {roof.get('tilt_deg')} deg",
    ]
    if outputs.get("battery"):
        lines.append(f"Battery: {outputs.get('battery')}")
    return "\n".join(lines)


def design_notes(db: Session, outputs: dict, inputs: dict, client: Any) -> dict:
    topics = list(NOTE_TOPICS)
    if outputs.get("system_kind") == "on_grid" and not outputs.get("battery"):
        topics = [t for t in topics if not t.startswith("battery")]
    merged: dict[int, Hit] = {}
    for t in topics:
        for h in search(db, t, client, k=3):
            if h.chunk_id not in merged or merged[h.chunk_id].score < h.score:
                merged[h.chunk_id] = h
    hits = sorted(merged.values(), key=lambda h: -h.score)[:16]
    if not hits:
        return {"notes": "No documents are indexed yet. Upload documents in Knowledge first.", "sources": [],
                "summary": design_summary(outputs, inputs)}
    summary = design_summary(outputs, inputs)
    text = client.chat(SYSTEM_NOTES, f"Design from the calculation engine:\n{summary}\n\n"
                                     f"Reference excerpts:\n\n{_excerpts(hits)}\n\nWrite the design review notes.")
    return {"notes": text, "sources": _sources(hits), "summary": summary}


def stats(db: Session) -> dict:
    rows = db.execute(select(KbDocument.status, func.count(KbDocument.id)).group_by(KbDocument.status)).all()
    return {"documents": {s: n for s, n in rows}, "chunks": db.scalar(select(func.count(KbChunk.id))) or 0}


def read_file(doc: KbDocument) -> bytes:
    return storage.get_bytes(doc.storage_key)

