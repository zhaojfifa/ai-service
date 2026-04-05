from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.config import get_settings
from app.services.email.drafts import (
    build_deterministic_email_draft,
    build_email_draft_from_poster_record,
)
from app.services.email.gemini_optimizer import GeminiEmailCopyOptimizer


def _clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())


def _collect_annotation_points(record: dict[str, Any]) -> list[str]:
    render_result = record.get("render_result") or {}
    annotation_review = render_result.get("product_annotation_contract_review") or {}
    points: list[str] = []

    for slot in annotation_review.get("annotation_slots") or []:
        value = _clean_text(
            slot.get("sanitized_text")
            or slot.get("rendered_excerpt")
            or slot.get("requested_text")
        )
        if value and value not in points:
            points.append(value)

    for value in (render_result.get("product_contract_review") or {}).get("rendered_annotation_items") or []:
        clean = _clean_text(value)
        if clean and clean not in points:
            points.append(clean)

    for value in (record.get("request_snapshot") or {}).get("features") or []:
        clean = _clean_text(value)
        if clean and clean not in points:
            points.append(clean)

    return points[:3]


def build_canonical_copy_input(record: dict[str, Any]) -> dict[str, Any]:
    request_snapshot = record.get("request_snapshot") or {}
    render_result = record.get("render_result") or {}
    final_poster = record.get("final_poster") or {}

    brand_name = _clean_text(
        request_snapshot.get("brand_name")
        or (render_result.get("header_contract_review") or {}).get("rendered_brand_excerpt")
        or "Brand"
    )
    agent_name = _clean_text(
        request_snapshot.get("agent_name")
        or (render_result.get("header_contract_review") or {}).get("rendered_agent_excerpt")
    )
    title = _clean_text(
        request_snapshot.get("title")
        or (render_result.get("title_text_layer") or {}).get("rendered_excerpt")
        or "Poster Update"
    )
    subtitle = _clean_text(
        request_snapshot.get("subtitle")
        or (render_result.get("subtitle_text_layer") or {}).get("rendered_excerpt")
    )
    summary_points = _collect_annotation_points(record)
    final_url = _clean_text(final_poster.get("url") or render_result.get("final_url"))

    return {
        "brand_name": brand_name,
        "agent_name": agent_name,
        "title": title,
        "subtitle": subtitle,
        "summary_points": summary_points,
        "final_poster_url": final_url,
    }


def build_email_draft_for_poster_record(record: dict[str, Any]) -> dict[str, Any]:
    canonical = build_canonical_copy_input(record)
    deterministic = build_deterministic_email_draft(canonical)

    settings = get_settings()
    if not settings.email_copy.gemini_enabled:
        return deterministic

    try:
        optimizer = GeminiEmailCopyOptimizer(settings.email_copy)
        optimized = optimizer.optimize(deepcopy(canonical))
    except Exception:
        fallback = deepcopy(deterministic)
        fallback["generated_from"] = "gemini_fallback_deterministic"
        return fallback

    optimized["generated_at"] = optimized.get("generated_at") or deterministic["generated_at"]
    optimized["generated_from"] = "gemini"
    return optimized


__all__ = [
    "build_canonical_copy_input",
    "build_email_draft_for_poster_record",
]
