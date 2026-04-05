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
        return (
            "You are optimizing outbound marketing email copy.\n"
            "Rewrite and summarize only the provided facts.\n"
            "Do not invent specs, pricing, certification, shipping, offers, or extra claims.\n"
            "Prefer annotation summary points over subtitle.\n"
            "Return strict JSON with keys: subject, preview_text, html, text, summary_points, tone.\n\n"
            f"FACTS_JSON={json.dumps(canonical_input, ensure_ascii=False)}"
        )
