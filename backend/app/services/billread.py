"""Bill-photo reading (SPEC Phase 3): a vision model extracts units, sanction load, tariff etc.
from an EB bill photo or PDF. Values are suggestions only; staff confirm before they are used."""
from __future__ import annotations

import base64
import json
from typing import Any

from ..config import get_config

FIELDS = {
    "consumer_number": {"type": ["string", "null"], "description": "TANGEDCO/EB service connection (consumer) number"},
    "consumer_name": {"type": ["string", "null"]},
    "tariff": {"type": ["string", "null"], "description": "Tariff code, e.g. LA1A, IA, IIB"},
    "phase": {"type": ["integer", "null"], "description": "1 or 3"},
    "sanction_load_kw": {"type": ["number", "null"]},
    "units_consumed": {"type": ["number", "null"], "description": "Units (kWh) consumed in this bill's period"},
    "billing_period_months": {"type": ["number", "null"], "description": "Months covered, usually 2 for TANGEDCO domestic"},
    "bill_amount": {"type": ["number", "null"], "description": "Total amount payable in rupees"},
    "period_from": {"type": ["string", "null"], "description": "YYYY-MM-DD"},
    "period_to": {"type": ["string", "null"], "description": "YYYY-MM-DD"},
    "confidence_notes": {"type": "string", "description": "What was unclear or unreadable"},
}
SCHEMA = {"type": "object", "properties": FIELDS, "required": list(FIELDS), "additionalProperties": False}

PROMPT = ("This is an Indian electricity bill (usually TANGEDCO / TNEB, Tamil Nadu; text may be in Tamil or English). "
          "Extract the fields. Use null for anything not clearly readable - never guess. Units consumed is the "
          "energy for the billing period, not the meter reading. Phase is 1 or 3.")


class BillReadError(RuntimeError):
    pass


def _client():
    import anthropic
    cfg = get_config()
    if not cfg.anthropic_api_key:
        raise BillReadError("Bill reading is not configured (set ANTHROPIC_API_KEY on the server).")
    return anthropic.Anthropic(api_key=cfg.anthropic_api_key)


def content_block(data: bytes, content_type: str) -> dict:
    b64 = base64.standard_b64encode(data).decode("utf-8")
    if content_type == "application/pdf":
        return {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64}}
    return {"type": "image", "source": {"type": "base64", "media_type": content_type, "data": b64}}


def read_bill(data: bytes, content_type: str, client: Any = None) -> dict:
    import anthropic
    client = client or _client()
    try:
        resp = client.beta.messages.create(
            model=get_config().bill_reader_model,
            max_tokens=4000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": [content_block(data, content_type), {"type": "text", "text": PROMPT}]}],
        )
    except anthropic.RateLimitError as exc:
        raise BillReadError("Bill reader is busy; try again in a minute.") from exc
    except anthropic.APIStatusError as exc:
        raise BillReadError(f"Bill reader error ({exc.status_code}).") from exc
    except anthropic.APIConnectionError as exc:
        raise BillReadError("Could not reach the bill reader service.") from exc
    if resp.stop_reason == "refusal":
        raise BillReadError("The model declined to read this file.")
    if resp.stop_reason == "max_tokens":
        raise BillReadError("Bill reading was cut off; try a clearer photo.")
    text = next((b.text for b in resp.content if b.type == "text"), None)
    if not text:
        raise BillReadError("No result from the bill reader.")
    raw = json.loads(text)
    return {"raw": raw, "fields": suggested_inputs(raw), "model": resp.model}


def suggested_inputs(raw: dict) -> dict:
    """Map extracted bill fields to analysis inputs (monthly units from the billing period)."""
    months = raw.get("billing_period_months") or 2
    units = raw.get("units_consumed")
    return {
        "monthly_units": round(units / months, 1) if units else None,
        "sanction_load_kw": raw.get("sanction_load_kw"),
        "phase": raw.get("phase") if raw.get("phase") in (1, 3) else None,
        "tariff": raw.get("tariff"),
        "consumer_number": raw.get("consumer_number"),
        "bill_amount": raw.get("bill_amount"),
    }
