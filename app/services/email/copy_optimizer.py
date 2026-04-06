from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.config import get_settings
from app.services.email.copy_safety import (
    contains_ungrounded_claims,
    sanitize_marketing_points,
    sanitize_marketing_text,
)
from app.services.email.drafts import (
    build_deterministic_email_draft,
)
from app.services.email.gemini_optimizer import GeminiEmailCopyOptimizer


def _collect_annotation_points(record: dict[str, Any]) -> list[str]:
    render_result = record.get("render_result") or {}
    annotation_review = render_result.get("product_annotation_contract_review") or {}
    points: list[str] = []

    for slot in annotation_review.get("annotation_slots") or []:
        value = sanitize_marketing_text(
            slot.get("sanitized_text")
            or slot.get("rendered_excerpt")
            or slot.get("requested_text")
        )
        if value and value not in points:
            points.append(value)

    for value in (render_result.get("product_contract_review") or {}).get("rendered_annotation_items") or []:
        clean = sanitize_marketing_text(value)
        if clean and clean not in points:
            points.append(clean)

    for value in (record.get("request_snapshot") or {}).get("features") or []:
        clean = sanitize_marketing_text(value)
        if clean and clean not in points:
            points.append(clean)

    return sanitize_marketing_points(points)[:3]


def build_canonical_copy_input(record: dict[str, Any]) -> dict[str, Any]:
    request_snapshot = record.get("request_snapshot") or {}
    render_result = record.get("render_result") or {}
    final_poster = record.get("final_poster") or {}

    brand_name = sanitize_marketing_text(
        request_snapshot.get("brand_name")
        or (render_result.get("header_contract_review") or {}).get("rendered_brand_excerpt")
        or "Brand"
    )
    agent_name = sanitize_marketing_text(
        request_snapshot.get("agent_name")
        or (render_result.get("header_contract_review") or {}).get("rendered_agent_excerpt")
    )
    title = sanitize_marketing_text(
        request_snapshot.get("title")
        or (render_result.get("title_text_layer") or {}).get("rendered_excerpt")
        or "Poster Update"
    )
    subtitle = sanitize_marketing_text(
        request_snapshot.get("subtitle")
        or (render_result.get("subtitle_text_layer") or {}).get("rendered_excerpt")
    )
    summary_points = _collect_annotation_points(record)
    final_url = sanitize_marketing_text(final_poster.get("url") or render_result.get("final_url"))

    return {
        "brand_name": brand_name or "Brand",
        "agent_name": agent_name,
        "title": title or "Poster Update",
        "subtitle": subtitle,
        "summary_points": summary_points,
        "final_poster_url": final_url,
    }


def _sanitize_optimized_draft(
    optimized: dict[str, Any],
    canonical: dict[str, Any],
    deterministic: dict[str, Any],
) -> dict[str, Any]:
    cleaned = {
        "subject": sanitize_marketing_text(optimized.get("subject")) or deterministic["subject"],
        "preview_text": sanitize_marketing_text(optimized.get("preview_text")) or deterministic["preview_text"],
        "html": str(optimized.get("html") or "").strip() or deterministic["html"],
        "text": str(optimized.get("text") or "").strip() or deterministic["text"],
        "summary_points": sanitize_marketing_points(optimized.get("summary_points") or [])[:3] or list(deterministic.get("summary_points") or []),
        "tone": sanitize_marketing_text(optimized.get("tone")) or deterministic.get("tone") or "clean_product_business",
        "generated_at": optimized.get("generated_at") or deterministic["generated_at"],
    }

    for field in ("subject", "preview_text", "text", "html"):
        if contains_ungrounded_claims(cleaned[field], canonical):
            cleaned[field] = deterministic[field]

    if any(contains_ungrounded_claims(point, canonical) for point in cleaned["summary_points"]):
        cleaned["summary_points"] = list(deterministic.get("summary_points") or [])

    if (
        cleaned["subject"] == deterministic["subject"]
        and cleaned["preview_text"] == deterministic["preview_text"]
        and cleaned["summary_points"] == list(deterministic.get("summary_points") or [])
    ):
        fallback = deepcopy(deterministic)
        fallback["generated_from"] = "gemini_fallback_deterministic"
        return fallback

    cleaned["generated_from"] = "gemini"
    return cleaned


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

    return _sanitize_optimized_draft(optimized, canonical, deterministic)


__all__ = [
    "build_canonical_copy_input",
    "build_email_draft_for_poster_record",
]
