from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import requests

from app.config import EmailCopyConfig


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class GeminiEmailCopyOptimizer:
    def __init__(self, config: EmailCopyConfig) -> None:
        self._config = config

    def optimize(self, canonical_input: dict[str, Any]) -> dict[str, Any]:
        prompt = self._build_prompt(canonical_input)
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self._config.model}:generateContent?key={self._config.gemini_api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                },
            },
            timeout=self._config.timeout_sec,
        )
        response.raise_for_status()
        payload = response.json()
        text = (
            payload.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        if not text:
            raise RuntimeError("Gemini optimizer returned no text")
        data = json.loads(text)
        return {
            "subject": str(data["subject"]).strip(),
            "preview_text": str(data["preview_text"]).strip(),
            "html": str(data["html"]).strip(),
            "text": str(data["text"]).strip(),
            "summary_points": [
                str(item).strip()
                for item in (data.get("summary_points") or [])
                if str(item).strip()
            ][:3],
            "tone": str(data.get("tone") or "clean_product_business").strip(),
            "generated_at": _utc_now(),
        }

    def _build_prompt(self, canonical_input: dict[str, Any]) -> str:
        deterministic_base = {
            "subject": f"{canonical_input.get('brand_name') or 'Brand'} | {canonical_input.get('title') or 'Poster Update'}",
            "preview_priority": list(canonical_input.get("summary_points") or [])[:2],
        }
        return (
            "You are optimizing outbound marketing email copy.\n"
            "Rewrite and summarize only the provided facts.\n"
            "Gemini is optimizer only, never a fact source.\n"
            "Do not invent specs, pricing, certification, shipping, delivery promises, offers, or extra claims.\n"
            "Prefer compact product selling points over long descriptive phrasing.\n"
            "Normalize title and subtitle into clean campaign-ready copy.\n"
            "Prefer product sell points from summary_points over subtitle.\n"
            "Use subtitle only as weak support text.\n"
            "If summary_points are present, do not let preview_text be only a subtitle echo.\n"
            "Keep the result more marketing-clean than the deterministic base.\n"
            "Return strict JSON with keys: subject, preview_text, html, text, summary_points, tone.\n\n"
            f"DETERMINISTIC_BASE={json.dumps(deterministic_base, ensure_ascii=False)}\n"
            f"FACTS_JSON={json.dumps(canonical_input, ensure_ascii=False)}"
        )
