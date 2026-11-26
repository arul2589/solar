"""Minimal OpenAI client over httpx (no extra SDK): embeddings, chat answers and page transcription.

Configured with OPENAI_API_KEY (and optional OPENAI_BASE_URL / model names) in .env.
Only standard request fields are sent so newer models keep working.
"""
from __future__ import annotations

import base64
from typing import Sequence

import httpx

from ..config import get_config


class AIError(RuntimeError):
    """A user-facing error from the AI service (shown to staff as-is)."""


class OpenAIClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, *, timeout: float = 180.0):
        cfg = get_config()
        self.api_key = api_key if api_key is not None else cfg.openai_api_key
        if not self.api_key:
            raise AIError("The document assistant is not configured (set OPENAI_API_KEY in .env and restart).")
        self.base_url = (base_url or cfg.openai_base_url).rstrip("/")
        self.chat_model = cfg.openai_chat_model
        self.vision_model = cfg.openai_vision_model
        self.embed_model = cfg.openai_embed_model
        self.embed_dims = cfg.openai_embed_dims
        self._http = httpx.Client(timeout=timeout, headers={"Authorization": f"Bearer {self.api_key}"})

    # ------------------------------------------------------------------ transport
    def _post(self, path: str, body: dict) -> dict:
        try:
            r = self._http.post(f"{self.base_url}{path}", json=body)
        except httpx.HTTPError as exc:
            raise AIError("Could not reach the OpenAI service.") from exc
        if r.status_code == 401:
            raise AIError("OpenAI rejected the API key (check OPENAI_API_KEY).")
        if r.status_code == 429:
            raise AIError("OpenAI rate limit or quota reached; try again in a minute or check billing.")
        if r.status_code >= 400:
            try:
                msg = r.json().get("error", {}).get("message", "")
            except ValueError:
                msg = r.text[:200]
            raise AIError(f"OpenAI error {r.status_code}: {msg[:300]}")
        return r.json()

    # ------------------------------------------------------------------ API
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), 64):
            batch = [t[:8000] or " " for t in texts[i:i + 64]]
            body = {"model": self.embed_model, "input": batch}
            if self.embed_dims:
                body["dimensions"] = self.embed_dims
            data = self._post("/embeddings", body)
            out.extend(d["embedding"] for d in sorted(data["data"], key=lambda d: d["index"]))
        return out

    def chat(self, system: str, user: str) -> str:
        data = self._post("/chat/completions", {
            "model": self.chat_model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        })
        return _content(data)

    def chat_json(self, system: str, user: str) -> dict:
        """Chat answer constrained to a JSON object (the prompt describes the shape)."""
        import json
        data = self._post("/chat/completions", {
            "model": self.chat_model,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        })
        try:
            return json.loads(_content(data))
        except ValueError as exc:
            raise AIError("The model returned an unreadable answer; try again.") from exc

    def transcribe_image(self, image: bytes, content_type: str, prompt: str) -> str:
        url = f"data:{content_type};base64,{base64.b64encode(image).decode()}"
        data = self._post("/chat/completions", {
            "model": self.vision_model,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": url, "detail": "high"}},
            ]}],
        })
        return _content(data)


def _content(data: dict) -> str:
    try:
        choice = data["choices"][0]
        text = choice["message"].get("content") or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise AIError("Unexpected reply from OpenAI.") from exc
    if not text and choice["message"].get("refusal"):
        raise AIError("The model declined this request.")
    return text.strip()
