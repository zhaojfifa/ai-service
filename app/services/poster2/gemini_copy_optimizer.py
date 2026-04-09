from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import requests

from app.config import EmailCopyConfig


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class GeminiPoster2CopyOptimizer:
    def __init__(self, config: EmailCopyConfig) -> None:
        self._config = config

    def optimize(self, canonical_input: dict[str, Any]) -> dict[str, Any]:
        prompt = self._build_prompt(canonical_input)
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self._config.model}:generateContent?key={self._config.gemini_api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"},
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
            raise RuntimeError("Gemini poster2 optimizer returned no text")
        data = json.loads(text)
        return {
            "title": str(data.get("title") or "").strip(),
            "subtitle": str(data.get("subtitle") or "").strip(),
            "features": [
                str(item).strip()
                for item in (data.get("features") or [])
                if str(item).strip()
            ][:4],
            "generated_at": _utc_now(),
        }

    def _build_prompt(self, canonical_input: dict[str, Any]) -> str:
        return (
            "You are optimizing Family A poster copy.\n"
            "Gemini is optimizer only and may not define layout, geometry, ownership, or behavior truth.\n"
            "Only optimize title, subtitle, and annotation feature copy.\n"
            "Do not invent specs, pricing, performance claims, offers, delivery claims, or new structure.\n"
            "Keep the product meaning grounded in the provided facts.\n"
            "Prefer compact, readable campaign copy.\n"
            "Return strict JSON with keys: title, subtitle, features.\n\n"
            f"FACTS_JSON={json.dumps(canonical_input, ensure_ascii=False)}"
        )


__all__ = ["GeminiPoster2CopyOptimizer"]
