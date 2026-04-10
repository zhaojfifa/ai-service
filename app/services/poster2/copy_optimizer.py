from __future__ import annotations

from dataclasses import replace
import re
from typing import Any

from app.config import get_settings
from app.services.email.copy_safety import (
    compress_marketing_point,
    normalize_marketing_subtitle,
    normalize_marketing_title,
    sanitize_marketing_text,
)

from .contracts import CopyOptimizationSpec, PosterSpec, TemplateSpec
from .gemini_copy_optimizer import GeminiPoster2CopyOptimizer


_SUBTITLE_OPTIMIZE_TARGET_BUDGET = 72
_ANNOTATION_OPTIMIZE_TARGET_BUDGET = 24
_SUBTITLE_REDUNDANT_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bwith guided presets\b",
        r"\bwith smart presets\b",
        r"\bfor daily convenience\b",
        r"\bfor daily use\b",
        r"\bfor busy weeknight cooking\b",
        r"\bwith less guesswork\b",
    )
]
_STOPWORDS = {
    "a",
    "an",
    "and",
    "after",
    "for",
    "from",
    "less",
    "more",
    "of",
    "the",
    "to",
    "with",
}
_ANNOTATION_PHRASE_REWRITES = (
    (re.compile(r"\bsmart controls?\s+for\s+daily\s+convenience\b", re.IGNORECASE), "Daily smart controls"),
    (re.compile(r"\bsmart controls?\s+for\s+daily\s+use\b", re.IGNORECASE), "Daily smart controls"),
    (re.compile(r"\bfast preheat\s+for\s+busy\s+weeknight\s+cooking\b", re.IGNORECASE), "Weeknight-ready preheat"),
    (re.compile(r"\beven cooking\s+with\s+less\s+guesswork\b", re.IGNORECASE), "More even cooking"),
    (re.compile(r"\beasy cleanup\s+after\s+family\s+dinners\b", re.IGNORECASE), "Easy cleanup"),
)
_SUBTITLE_TRAILING_NOISE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"(?:\s*[\-|/|•·]+\s*)?(?:describe|description|copy|subtitle)[!?.,:;]*\s*$",
        r"(?:\s*[\-|/|•·]+\s*)?(?:please describe|for description only)[!?.,:;]*\s*$",
    )
]
_COMMERCIAL_SUBTITLE_SIGNAL_PATTERNS = {
    "fast_heating": re.compile(r"\bfast heating\b", re.IGNORECASE),
    "precise_control": re.compile(r"\bprecise control\b", re.IGNORECASE),
    "stainless_steel": re.compile(r"\bstainless steel\b", re.IGNORECASE),
}


def _trim_to_budget(text: str, budget: int) -> str:
    if not text or budget <= 0 or len(text) <= budget:
        return text
    truncated = text[:budget]
    last_break = max(truncated.rfind(" "), truncated.rfind("·"))
    if last_break >= int(budget * 0.6):
        truncated = truncated[:last_break]
    return truncated.strip(" ·,-")


def _contains_subtitle_redundancy(text: str, title: str) -> bool:
    if not text:
        return False
    title_tokens = {
        token.casefold()
        for token in re.findall(r"[A-Za-z0-9]+", title or "")
        if len(token) >= 4
    }
    text_tokens = [
        token.casefold()
        for token in re.findall(r"[A-Za-z0-9]+", text)
        if len(token) >= 4
    ]
    overlap = [token for token in text_tokens if token in title_tokens]
    if overlap:
        return True
    return any(pattern.search(text) for pattern in _SUBTITLE_REDUNDANT_PATTERNS)


def _dedupe_title_terms(text: str, title: str) -> str:
    if not text:
        return ""
    title_terms = {
        token.casefold()
        for token in re.findall(r"[A-Za-z0-9]+", title or "")
        if len(token) >= 4
    }
    if not title_terms:
        return text
    words = text.split()
    kept: list[str] = []
    for word in words:
        key = re.sub(r"[^A-Za-z0-9]+", "", word).casefold()
        if key and key in title_terms:
            continue
        kept.append(word)
    return " ".join(kept).strip(" ·,-")


def _optimize_subtitle_candidate(text: str, title: str) -> str:
    subtitle = normalize_marketing_subtitle(text, title=title)
    if not subtitle:
        return ""
    optimized = subtitle
    title_clean = clean_copy_candidate(title)
    if title_clean and title_clean.casefold() in optimized.casefold():
        optimized = re.sub(re.escape(title_clean), "", optimized, flags=re.IGNORECASE).strip(" ·,-")
    replacements = (
        ("Steam, bake, and roast", "Steam, bake, roast"),
        ("steam, bake, and roast", "steam, bake, roast"),
        ("with guided presets", "guided presets"),
        ("with smart presets", "smart presets"),
        ("smart daily convenience", "daily-use controls"),
        ("for daily convenience", "for daily use"),
        ("for busy weeknight cooking", "for weeknight cooking"),
        ("create chef-level deliciousness", "chef-level results"),
        ("with less guesswork", "with guided results"),
    )
    for source, target in replacements:
        optimized = optimized.replace(source, target)
    optimized = clean_copy_candidate(optimized)
    commercial_rewrite = _rewrite_commercial_subtitle_candidate(optimized)
    if commercial_rewrite:
        optimized = commercial_rewrite
    if len(optimized) > _SUBTITLE_OPTIMIZE_TARGET_BUDGET:
        segments = [segment.strip(" ·,-") for segment in re.split(r"[;,]|(?:\s+\u00b7\s+)|(?:\s+\band\b\s+)|(?:\s+\bwith\b\s+)", optimized) if segment.strip()]
        if segments:
            first_segment = segments[0]
            trailing = next(
                (
                    segment for segment in segments[1:]
                    if re.search(r"\b(preset|control|result|cleanup|preheat|steam|bake|roast)\b", segment, re.IGNORECASE)
                ),
                segments[-1],
            )
            optimized = f"{first_segment} · {trailing}" if trailing != first_segment else first_segment
    optimized = clean_copy_candidate(_trim_to_budget(optimized, _SUBTITLE_OPTIMIZE_TARGET_BUDGET))
    return optimized or subtitle


def _keyword_compress_annotation(text: str) -> str:
    raw_tokens = re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)?", text)
    if not raw_tokens:
        return text
    kept: list[str] = []
    for token in raw_tokens:
        key = token.casefold()
        if key in _STOPWORDS:
            continue
        if key == "convenience":
            token = "use"
        elif key == "dinners":
            token = "dinner"
        kept.append(token)
    if not kept:
        return text
    if len(kept) >= 3 and kept[1].casefold() == "controls" and kept[2].casefold() in {"daily", "use"}:
        kept = [kept[2], kept[0], kept[1]]
    candidate = " ".join(kept[:3]).strip()
    return clean_copy_candidate(candidate)


def clean_copy_candidate(text: str) -> str:
    return " ".join((text or "").strip().split()).strip(" ·,-")


def _cleanup_subtitle_text(text: str) -> str:
    cleaned = clean_copy_candidate(sanitize_marketing_text(text))
    if not cleaned:
        return ""
    for pattern in _SUBTITLE_TRAILING_NOISE_PATTERNS:
        cleaned = pattern.sub("", cleaned).strip(" ·,-")
    cleaned = re.sub(r"\s*[\r\n]+\s*", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ·,-")
    return cleaned


def _rewrite_commercial_subtitle_candidate(text: str) -> str:
    cleaned = clean_copy_candidate(text)
    if not cleaned:
        return ""
    if all(pattern.search(cleaned) for pattern in _COMMERCIAL_SUBTITLE_SIGNAL_PATTERNS.values()):
        return "Fast heating, precise control, and stainless steel durability."
    return ""


def _build_subtitle_fit_rewrite(text: str, title: str, *, render_budget: int) -> tuple[str, bool, str]:
    cleaned = _cleanup_subtitle_text(text)
    if not cleaned:
        return "", False, ""
    if len(cleaned) <= render_budget:
        return cleaned, False, ""
    rewritten = _optimize_subtitle_candidate(cleaned, title)
    if rewritten and rewritten != cleaned:
        return rewritten, True, "subtitle_budget_fit_required"
    return cleaned, False, ""


def _build_annotation_fit_rewrite(text: str, *, render_budget: int) -> tuple[str, bool, str]:
    cleaned = clean_copy_candidate(sanitize_marketing_text(text))
    if not cleaned:
        return "", False, ""
    if len(cleaned) <= render_budget:
        return cleaned, False, ""
    rewritten = _optimize_annotation_candidate(cleaned)
    if rewritten and rewritten != cleaned:
        return rewritten, True, "annotation_slot_budget_fit_required"
    return cleaned, False, ""


def _optimize_annotation_candidate(text: str) -> str:
    point = compress_marketing_point(text)
    if not point:
        return ""
    original = clean_copy_candidate(text)
    for pattern, replacement in _ANNOTATION_PHRASE_REWRITES:
        if pattern.search(original):
            return clean_copy_candidate(_trim_to_budget(replacement, _ANNOTATION_OPTIMIZE_TARGET_BUDGET))

    candidate = point
    if len(candidate) > _ANNOTATION_OPTIMIZE_TARGET_BUDGET or len(candidate.split()) <= 2:
        keyword_candidate = _keyword_compress_annotation(original)
        if keyword_candidate and keyword_candidate != candidate:
            candidate = keyword_candidate
    if len(candidate) > _ANNOTATION_OPTIMIZE_TARGET_BUDGET:
        candidate = _trim_to_budget(candidate, _ANNOTATION_OPTIMIZE_TARGET_BUDGET)
    return clean_copy_candidate(candidate) or point


def _normalize_feature_items(items: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for item in items:
        clean = clean_copy_candidate(sanitize_marketing_text(str(item or "").strip()))
        if clean:
            normalized.append(clean)
    return tuple(normalized[:4])


def _build_deterministic_candidate(effective_spec: PosterSpec) -> dict[str, Any]:
    title = normalize_marketing_title(effective_spec.title) or effective_spec.title
    subtitle = normalize_marketing_subtitle(
        effective_spec.subtitle,
        title=title or effective_spec.title,
    )
    features = tuple(str(item or "").strip() for item in effective_spec.features if str(item or "").strip())
    suggestion_title = title
    suggestion_subtitle = subtitle
    suggestion_features = features

    if subtitle and (len(subtitle) > _SUBTITLE_OPTIMIZE_TARGET_BUDGET or _contains_subtitle_redundancy(subtitle, title)):
        suggestion_subtitle = _optimize_subtitle_candidate(subtitle, suggestion_title or title)

    if features:
        tightened_features = tuple(_optimize_annotation_candidate(item) for item in features)
        suggestion_features = tightened_features[: len(features)]

    if suggestion_subtitle == subtitle and len(features) >= 2 and not subtitle:
        joined = " · ".join(item for item in suggestion_features[:2] if item)
        if joined:
            suggestion_subtitle = _optimize_subtitle_candidate(joined, suggestion_title or title)

    if suggestion_title == title and suggestion_subtitle == subtitle and suggestion_features == features and subtitle:
        suggestion_subtitle = _optimize_subtitle_candidate(subtitle, title)
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
    raw_features = tuple(candidate.get("features") or effective_spec.features)
    features = tuple(
        clean_copy_candidate(_trim_to_budget(sanitize_marketing_text(item), _ANNOTATION_OPTIMIZE_TARGET_BUDGET))
        or effective_spec.features[index]
        for index, item in enumerate(raw_features[:max_feature_count])
    )
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
    ) or suggested["subtitle"]
    max_feature_count = len(effective_spec.features)
    features = _normalize_feature_items(optimization.accepted_features)[:max_feature_count] or suggested["features"]
    return {
        "title": title,
        "subtitle": subtitle,
        "features": features,
        "generated_from": suggested["generated_from"],
    }


def _build_text_review(
    *,
    requested_text: str,
    sanitized_text: str,
    cleanup_text: str,
    fit_rewrite_text: str,
    fit_rewrite_applied: bool,
    fit_rewrite_reason: str,
    optimized_text: str,
    accepted_text: str,
    rendered_text: str,
    rendered_text_source: str,
    optimization_applied: bool,
) -> dict[str, Any]:
    return {
        "requested_text": requested_text,
        "sanitized_text": sanitized_text,
        "cleanup_text": cleanup_text,
        "fit_rewrite_text": fit_rewrite_text,
        "fit_rewrite_applied": fit_rewrite_applied,
        "fit_rewrite_reason": fit_rewrite_reason,
        "optimized_text": optimized_text,
        "accepted_text": accepted_text,
        "rendered_text": rendered_text,
        "rendered_text_source": rendered_text_source,
        "optimization_applied": optimization_applied,
    }


def resolve_copy_optimization(
    template: TemplateSpec,
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
) -> tuple[PosterSpec, dict[str, Any]]:
    if template.template_id != "template_dual_v2":
        return effective_spec, {}

    from .template_behavior import resolve_bottom_behavior

    optimization = requested_spec.copy_optimization
    title_cleanup = effective_spec.title
    title_fit = effective_spec.title
    bottom_mode = effective_spec.bottom_mode or requested_spec.bottom_mode or template.behavior_modes.bottom_mode
    gallery_mode = effective_spec.gallery_mode or requested_spec.gallery_mode or template.behavior_modes.gallery_mode
    requested_gallery_count = int(
        effective_spec.gallery_requested_count
        if effective_spec.gallery_requested_count is not None
        else (
            requested_spec.gallery_requested_count
            if requested_spec.gallery_requested_count is not None
            else len(effective_spec.gallery_images or requested_spec.gallery_images or ())
        )
    )
    normalized_gallery_count = int(
        effective_spec.gallery_input_count_normalized
        if effective_spec.gallery_input_count_normalized is not None
        else (
            requested_spec.gallery_input_count_normalized
            if requested_spec.gallery_input_count_normalized is not None
            else requested_gallery_count
        )
    )
    resolved_gallery_count = min(len(effective_spec.gallery_images or requested_spec.gallery_images or ()), template.gallery_slot.count)
    render_bottom_policy = resolve_bottom_behavior(
        bottom_mode,
        requested_bottom_mode=effective_spec.bottom_mode or requested_spec.bottom_mode,
        template_bottom_mode=template.behavior_modes.bottom_mode,
        gallery_mode=gallery_mode,
        title_text=effective_spec.title,
        subtitle_text=effective_spec.subtitle or requested_spec.subtitle,
        requested_gallery_count=requested_gallery_count,
        normalized_gallery_count=normalized_gallery_count,
        resolved_gallery_count=resolved_gallery_count,
        max_items=template.gallery_slot.count,
    )
    subtitle_render_budget = max(int(render_bottom_policy.subtitle_char_budget), _SUBTITLE_OPTIMIZE_TARGET_BUDGET)
    subtitle_cleanup = _cleanup_subtitle_text(effective_spec.subtitle or requested_spec.subtitle)
    subtitle_fit, subtitle_fit_applied, subtitle_fit_reason = _build_subtitle_fit_rewrite(
        subtitle_cleanup,
        effective_spec.title,
        render_budget=subtitle_render_budget,
    )

    base_requested_features = tuple(requested_spec.features)
    base_sanitized_features = tuple(effective_spec.features)
    base_cleanup_features = tuple(base_sanitized_features)
    base_fit_features: list[str] = []
    base_fit_flags: list[bool] = []
    base_fit_reasons: list[str] = []
    visible_feature_count = max(1, min(max(len(base_requested_features), len(base_sanitized_features), 1), 3))
    annotation_render_budget = {1: 56, 2: 52, 3: 48}.get(visible_feature_count, 48)
    for index in range(max(len(base_requested_features), len(base_sanitized_features))):
        requested_text = base_requested_features[index] if index < len(base_requested_features) else ""
        sanitized_text = base_sanitized_features[index] if index < len(base_sanitized_features) else ""
        fit_text, fit_applied, fit_reason = _build_annotation_fit_rewrite(
            requested_text or sanitized_text,
            render_budget=annotation_render_budget,
        )
        base_fit_features.append(fit_text or sanitized_text)
        base_fit_flags.append(fit_applied)
        base_fit_reasons.append(fit_reason)

    base_render_spec = replace(
        effective_spec,
        subtitle=subtitle_fit or subtitle_cleanup or effective_spec.subtitle,
        features=tuple(base_fit_features),
    )

    if optimization.mode == "off":
        return base_render_spec, {
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
            "title": _build_text_review(
                requested_text=requested_spec.title,
                sanitized_text=effective_spec.title,
                cleanup_text=title_cleanup,
                fit_rewrite_text=title_fit,
                fit_rewrite_applied=False,
                fit_rewrite_reason="",
                optimized_text="",
                accepted_text="",
                rendered_text=base_render_spec.title,
                rendered_text_source="sanitized_text",
                optimization_applied=False,
            ),
            "subtitle": _build_text_review(
                requested_text=requested_spec.subtitle,
                sanitized_text=effective_spec.subtitle,
                cleanup_text=subtitle_cleanup,
                fit_rewrite_text=subtitle_fit,
                fit_rewrite_applied=subtitle_fit_applied,
                fit_rewrite_reason=subtitle_fit_reason,
                optimized_text="",
                accepted_text="",
                rendered_text=base_render_spec.subtitle,
                rendered_text_source="fit_rewrite_text" if subtitle_fit_applied else ("cleanup_text" if subtitle_cleanup != effective_spec.subtitle else "sanitized_text"),
                optimization_applied=False,
            ),
            "annotation_items": [
                {
                    "index": index,
                    **_build_text_review(
                        requested_text=base_requested_features[index] if index < len(base_requested_features) else "",
                        sanitized_text=base_sanitized_features[index] if index < len(base_sanitized_features) else "",
                        cleanup_text=base_cleanup_features[index] if index < len(base_cleanup_features) else "",
                        fit_rewrite_text=base_fit_features[index] if index < len(base_fit_features) else "",
                        fit_rewrite_applied=base_fit_flags[index] if index < len(base_fit_flags) else False,
                        fit_rewrite_reason=base_fit_reasons[index] if index < len(base_fit_reasons) else "",
                        optimized_text="",
                        accepted_text="",
                        rendered_text=base_render_spec.features[index] if index < len(base_render_spec.features) else "",
                        rendered_text_source="fit_rewrite_text" if (index < len(base_fit_flags) and base_fit_flags[index]) else "sanitized_text",
                        optimization_applied=False,
                    ),
                }
                for index in range(max(len(base_requested_features), len(base_render_spec.features)))
            ],
        }

    candidate_source_spec = replace(
        base_render_spec,
        subtitle=requested_spec.subtitle or subtitle_cleanup or base_render_spec.subtitle,
        features=tuple(requested_spec.features) or base_render_spec.features,
    )
    suggested = _sanitize_candidate(_build_candidate(candidate_source_spec), effective_spec)
    apply_optimized = optimization.mode == "apply" or optimization.decision == "accepted"
    if optimization.decision == "rejected":
        apply_optimized = False

    applied = _pick_applied_candidate(optimization, base_render_spec, suggested) if apply_optimized else suggested
    rendered_spec = replace(
        base_render_spec,
        title=applied["title"] if apply_optimized else base_render_spec.title,
        subtitle=applied["subtitle"] if apply_optimized else base_render_spec.subtitle,
        features=applied["features"] if apply_optimized else base_render_spec.features,
    )

    annotation_items = []
    base_features = tuple(base_render_spec.features)
    optimized_features = tuple(suggested["features"])
    rendered_features = tuple(rendered_spec.features)
    for index in range(max(len(base_features), len(optimized_features), len(rendered_features))):
        requested_text = requested_spec.features[index] if index < len(requested_spec.features) else ""
        sanitized_text = base_sanitized_features[index] if index < len(base_sanitized_features) else ""
        cleanup_text = base_cleanup_features[index] if index < len(base_cleanup_features) else sanitized_text
        fit_rewrite_text = base_features[index] if index < len(base_features) else ""
        optimized_text = optimized_features[index] if index < len(optimized_features) else ""
        rendered_text = rendered_features[index] if index < len(rendered_features) else ""
        accepted_text = (
            clean_copy_candidate(optimization.accepted_features[index])
            if index < len(optimization.accepted_features)
            else ""
        )
        annotation_items.append(
            {
                "index": index,
                **_build_text_review(
                    requested_text=requested_text,
                    sanitized_text=sanitized_text,
                    cleanup_text=cleanup_text,
                    fit_rewrite_text=fit_rewrite_text,
                    fit_rewrite_applied=base_fit_flags[index] if index < len(base_fit_flags) else False,
                    fit_rewrite_reason=base_fit_reasons[index] if index < len(base_fit_reasons) else "",
                    optimized_text=optimized_text,
                    accepted_text=accepted_text,
                    rendered_text=rendered_text,
                    rendered_text_source=(
                        "accepted_text"
                        if apply_optimized and accepted_text
                        else (
                            "optimized_text"
                            if apply_optimized and optimized_text
                            else ("fit_rewrite_text" if index < len(base_fit_flags) and base_fit_flags[index] else "sanitized_text")
                        )
                    ),
                    optimization_applied=rendered_text != base_features[index] if index < len(base_features) else bool(rendered_text),
                ),
            }
        )

    changed_fields = [
        field_name
        for field_name, base_value, optimized_value in (
            ("title", base_render_spec.title, suggested["title"]),
            ("subtitle", base_render_spec.subtitle, suggested["subtitle"]),
            ("annotation", tuple(base_render_spec.features), tuple(suggested["features"])),
        )
        if optimized_value != base_value
    ]

    accepted_title = normalize_marketing_title(optimization.accepted_title.strip())
    accepted_subtitle = _cleanup_subtitle_text(optimization.accepted_subtitle.strip())

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
            **_build_text_review(
                requested_text=requested_spec.title,
                sanitized_text=effective_spec.title,
                cleanup_text=title_cleanup,
                fit_rewrite_text=title_fit,
                fit_rewrite_applied=False,
                fit_rewrite_reason="",
                optimized_text=suggested["title"],
                accepted_text=accepted_title,
                rendered_text=rendered_spec.title,
                rendered_text_source=(
                    "accepted_text"
                    if apply_optimized and accepted_title
                    else ("optimized_text" if apply_optimized and suggested["title"] else "sanitized_text")
                ),
                optimization_applied=rendered_spec.title != base_render_spec.title,
            ),
        },
        "subtitle": {
            **_build_text_review(
                requested_text=requested_spec.subtitle,
                sanitized_text=effective_spec.subtitle,
                cleanup_text=subtitle_cleanup,
                fit_rewrite_text=subtitle_fit,
                fit_rewrite_applied=subtitle_fit_applied,
                fit_rewrite_reason=subtitle_fit_reason,
                optimized_text=suggested["subtitle"],
                accepted_text=accepted_subtitle,
                rendered_text=rendered_spec.subtitle,
                rendered_text_source=(
                    "accepted_text"
                    if apply_optimized and accepted_subtitle
                    else (
                        "optimized_text"
                        if apply_optimized and suggested["subtitle"]
                        else ("fit_rewrite_text" if subtitle_fit_applied else ("cleanup_text" if subtitle_cleanup != effective_spec.subtitle else "sanitized_text"))
                    )
                ),
                optimization_applied=rendered_spec.subtitle != base_render_spec.subtitle,
            ),
        },
        "annotation_items": annotation_items,
    }
    return rendered_spec, review


__all__ = ["resolve_copy_optimization"]
