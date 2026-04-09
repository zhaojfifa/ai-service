from __future__ import annotations

from dataclasses import replace
from typing import Any

from app.config import get_settings
from app.services.email.copy_safety import (
    compress_marketing_point,
    normalize_marketing_subtitle,
    normalize_marketing_title,
)

from .contracts import CopyOptimizationSpec, PosterSpec, TemplateSpec
from .gemini_copy_optimizer import GeminiPoster2CopyOptimizer


def _normalize_feature_items(items: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for item in items:
        clean = compress_marketing_point(str(item or "").strip())
        if clean:
            normalized.append(clean)
    return tuple(normalized[:4])


def _build_deterministic_candidate(effective_spec: PosterSpec) -> dict[str, Any]:
    title = normalize_marketing_title(effective_spec.title) or effective_spec.title
    subtitle = normalize_marketing_subtitle(
        effective_spec.subtitle,
        title=title or effective_spec.title,
    )
    features = _normalize_feature_items(effective_spec.features)
    suggestion_title = title
    suggestion_subtitle = subtitle
    suggestion_features = features

    if features:
        first_feature = features[0]
        if first_feature and first_feature.casefold() not in title.casefold():
            suggestion_title = normalize_marketing_title(f"{title} · {first_feature}") or suggestion_title
        if len(features) >= 2:
            joined = " · ".join(item for item in features[:2] if item)
            if joined:
                suggestion_subtitle = normalize_marketing_subtitle(joined, title=suggestion_title or title)
        elif first_feature:
            suggestion_subtitle = normalize_marketing_subtitle(first_feature, title=suggestion_title or title)

        tightened_features: list[str] = []
        for index, item in enumerate(features):
            compact = compress_marketing_point(item)
            if compact and compact != item:
                tightened_features.append(compact)
                continue
            if index == 0 and compact:
                tightened_features.append(compact.replace(" for ", " · "))
            else:
                tightened_features.append(compact)
        suggestion_features = tuple(tightened_features[: len(features)])

    if suggestion_title == title and suggestion_subtitle == subtitle and suggestion_features == features:
        if subtitle and subtitle.casefold() not in title.casefold():
            suggestion_title = normalize_marketing_title(f"{title} · {subtitle}") or title
        elif title:
            suggestion_subtitle = normalize_marketing_subtitle(f"Optimized: {title}", title=title)
    return {
        "title": suggestion_title,
        "subtitle": suggestion_subtitle,
        "features": suggestion_features,
        "generated_from": "deterministic_suggestion",
    }


def _sanitize_candidate(
    candidate: dict[str, Any],
    effective_spec: PosterSpec,
) -> dict[str, Any]:
    title = normalize_marketing_title(str(candidate.get("title") or "").strip()) or effective_spec.title
    subtitle = normalize_marketing_subtitle(
        str(candidate.get("subtitle") or "").strip(),
        title=title or effective_spec.title,
    )
    max_feature_count = len(effective_spec.features)
    features = _normalize_feature_items(candidate.get("features") or effective_spec.features)[:max_feature_count]
    return {
        "title": title,
        "subtitle": subtitle,
        "features": features,
        "generated_from": str(candidate.get("generated_from") or "deterministic"),
    }


def _build_candidate(effective_spec: PosterSpec) -> dict[str, Any]:
    deterministic = _build_deterministic_candidate(effective_spec)
    settings = get_settings()
    if not settings.email_copy.gemini_enabled:
        return deterministic
    try:
        optimizer = GeminiPoster2CopyOptimizer(settings.email_copy)
        optimized = optimizer.optimize(
            {
                "template_id": effective_spec.template_id,
                "title": effective_spec.title,
                "subtitle": effective_spec.subtitle,
                "features": list(effective_spec.features),
            }
        )
    except Exception:
        fallback = dict(deterministic)
        fallback["generated_from"] = "gemini_fallback_deterministic"
        return fallback
    optimized["generated_from"] = "gemini"
    sanitized = _sanitize_candidate(optimized, effective_spec)
    if (
        sanitized["title"] == effective_spec.title
        and sanitized["subtitle"] == effective_spec.subtitle
        and sanitized["features"] == tuple(effective_spec.features)
    ):
        fallback = dict(deterministic)
        fallback["generated_from"] = "gemini_fallback_deterministic"
        return fallback
    return sanitized


def _pick_applied_candidate(
    optimization: CopyOptimizationSpec,
    effective_spec: PosterSpec,
    suggested: dict[str, Any],
) -> dict[str, Any]:
    title = normalize_marketing_title(optimization.accepted_title.strip()) or suggested["title"]
    subtitle = normalize_marketing_subtitle(
        optimization.accepted_subtitle.strip(),
        title=title or suggested["title"],
    )
    max_feature_count = len(effective_spec.features)
    features = _normalize_feature_items(optimization.accepted_features)[:max_feature_count] or suggested["features"]
    return {
        "title": title,
        "subtitle": subtitle,
        "features": features,
        "generated_from": suggested["generated_from"],
    }


def resolve_copy_optimization(
    template: TemplateSpec,
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
) -> tuple[PosterSpec, dict[str, Any]]:
    if template.template_id != "template_dual_v2":
        return effective_spec, {}

    optimization = requested_spec.copy_optimization
    if optimization.mode == "off":
        return effective_spec, {
            "enabled": False,
            "template_scope": "family_a_only",
            "optimizer_scope": "title_subtitle_annotation_only",
            "mode": "off",
            "decision": "pending",
            "disabled_reason": "mode_off_no_copy_optimization_requested",
            "optimizer_requested": get_settings().email_copy.optimizer,
            "optimizer_used": "off",
            "applied_to_rendered_output": False,
            "changed_fields": [],
            "operator_controls": {
                "visible": False,
                "can_accept": False,
                "can_reject": False,
                "disabled_reason": "mode_off_no_copy_optimization_requested",
            },
            "truth_guard": {
                "renderer_executes_truth": True,
                "gemini_may_not_define_layout_or_control": True,
                "template_a_only": True,
            },
            "title": {
                "requested_text": requested_spec.title,
                "sanitized_text": effective_spec.title,
                "optimized_text": "",
                "rendered_text": effective_spec.title,
                "optimization_applied": False,
            },
            "subtitle": {
                "requested_text": requested_spec.subtitle,
                "sanitized_text": effective_spec.subtitle,
                "optimized_text": "",
                "rendered_text": effective_spec.subtitle,
                "optimization_applied": False,
            },
            "annotation_items": [
                {
                    "index": index,
                    "requested_text": requested_spec.features[index] if index < len(requested_spec.features) else "",
                    "sanitized_text": effective_spec.features[index] if index < len(effective_spec.features) else "",
                    "optimized_text": "",
                    "rendered_text": effective_spec.features[index] if index < len(effective_spec.features) else "",
                    "optimization_applied": False,
                }
                for index in range(len(effective_spec.features))
            ],
        }

    suggested = _build_candidate(effective_spec)
    apply_optimized = optimization.mode == "apply" or optimization.decision == "accepted"
    if optimization.decision == "rejected":
        apply_optimized = False

    applied = _pick_applied_candidate(optimization, effective_spec, suggested) if apply_optimized else suggested
    rendered_spec = replace(
        effective_spec,
        title=applied["title"] if apply_optimized else effective_spec.title,
        subtitle=applied["subtitle"] if apply_optimized else effective_spec.subtitle,
        features=applied["features"] if apply_optimized else effective_spec.features,
    )

    annotation_items = []
    base_features = tuple(effective_spec.features)
    optimized_features = tuple(suggested["features"])
    rendered_features = tuple(rendered_spec.features)
    for index in range(max(len(base_features), len(optimized_features), len(rendered_features))):
        requested_text = requested_spec.features[index] if index < len(requested_spec.features) else ""
        sanitized_text = base_features[index] if index < len(base_features) else ""
        optimized_text = optimized_features[index] if index < len(optimized_features) else ""
        rendered_text = rendered_features[index] if index < len(rendered_features) else ""
        annotation_items.append(
            {
                "index": index,
                "requested_text": requested_text,
                "sanitized_text": sanitized_text,
                "optimized_text": optimized_text,
                "rendered_text": rendered_text,
                "optimization_applied": rendered_text != sanitized_text,
            }
        )

    changed_fields = [
        field_name
        for field_name, base_value, optimized_value in (
            ("title", effective_spec.title, suggested["title"]),
            ("subtitle", effective_spec.subtitle, suggested["subtitle"]),
            ("annotation", tuple(effective_spec.features), tuple(suggested["features"])),
        )
        if optimized_value != base_value
    ]

    review = {
        "enabled": True,
        "template_scope": "family_a_only",
        "optimizer_scope": "title_subtitle_annotation_only",
        "mode": optimization.mode,
        "decision": optimization.decision,
        "optimizer_requested": get_settings().email_copy.optimizer,
        "optimizer_used": suggested["generated_from"],
        "applied_to_rendered_output": apply_optimized,
        "changed_fields": changed_fields,
        "disabled_reason": "" if changed_fields else "no_material_copy_diff_available",
        "operator_controls": {
            "visible": True,
            "can_accept": bool(changed_fields),
            "can_reject": bool(changed_fields),
            "disabled_reason": "" if changed_fields else "no_material_copy_diff_available",
        },
        "truth_guard": {
            "renderer_executes_truth": True,
            "gemini_may_not_define_layout_or_control": True,
            "template_a_only": True,
        },
        "title": {
            "requested_text": requested_spec.title,
            "sanitized_text": effective_spec.title,
            "optimized_text": suggested["title"],
            "rendered_text": rendered_spec.title,
            "optimization_applied": rendered_spec.title != effective_spec.title,
        },
        "subtitle": {
            "requested_text": requested_spec.subtitle,
            "sanitized_text": effective_spec.subtitle,
            "optimized_text": suggested["subtitle"],
            "rendered_text": rendered_spec.subtitle,
            "optimization_applied": rendered_spec.subtitle != effective_spec.subtitle,
        },
        "annotation_items": annotation_items,
    }
    return rendered_spec, review


__all__ = ["resolve_copy_optimization"]
