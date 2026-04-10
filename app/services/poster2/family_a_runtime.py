from __future__ import annotations

from .contracts import TemplateSpec
from .template_registry import FAMILY_A_CAMPAIGN_EXPLAINER

FAMILY_A_STRUCTURE_REGION_ORDER: tuple[str, ...] = (
    "header_region",
    "scenario_region",
    "product_region",
    "feature_region",
    "bottom_region",
    "title_band_region",
    "gallery_strip_region",
)

FAMILY_A_VISIBLE_TRUTH_KEYS: frozenset[str] = frozenset(
    {
        "header_region",
        "header_identity_zone_slot",
        "header_agent_zone_slot",
        "brand_logo_slot",
        "brand_name_slot",
        "agent_name_slot",
        "scenario_region",
        "scenario_image",
        "product_region",
        "product_canvas_shell_layer",
        "product_image_layer",
        "product_secondary_image_layer",
        "feature_region",
        "bottom_region",
        "title_band_region",
        "gallery_strip_region",
        "title_text_layer",
        "subtitle_text_layer",
    }
)

FAMILY_A_FORBIDDEN_TEMPLATE_B_KEYS: frozenset[str] = frozenset(
    {
        "logo_banner_region",
        "top_copy_region",
        "materials_strip_region",
        "product_hero_region",
        "description_region",
        "top_copy_title_layer",
        "top_copy_subtitle_layer",
        "description_title_layer",
        "description_body_layer",
    }
)

FAMILY_A_CANONICAL_SAMPLE_VARIANTS: tuple[dict[str, object], ...] = (
    {
        "sample_id": "annotation_triplet_gallery_triplet_subtitle_present",
        "annotation_items": 3,
        "gallery_items": 3,
        "subtitle_present": True,
    },
    {
        "sample_id": "annotation_triplet_gallery_dense_quad_subtitle_present",
        "annotation_items": 3,
        "gallery_items": 4,
        "subtitle_present": True,
    },
    {
        "sample_id": "annotation_triplet_gallery_triplet_subtitle_empty",
        "annotation_items": 3,
        "gallery_items": 3,
        "subtitle_present": False,
    },
)


def filter_family_a_visible_truth_evidence(evidence: dict[str, object]) -> dict[str, object]:
    if not evidence:
        return {}
    return {key: value for key, value in evidence.items() if key in FAMILY_A_VISIBLE_TRUTH_KEYS}


def build_family_a_control_surface(resolved_behavior) -> dict[str, object]:
    return {
        "family_id": FAMILY_A_CAMPAIGN_EXPLAINER,
        "mode_surface": {
            "header_mode": resolved_behavior.header_policy.mode,
            "hero_mode": resolved_behavior.hero_policy.mode,
            "feature_mode": resolved_behavior.feature_policy.mode,
            "product_annotation_mode": resolved_behavior.product_annotation_mode,
            "bottom_mode": resolved_behavior.bottom_policy.effective_mode,
            "gallery_mode": resolved_behavior.bottom_policy.gallery_mode,
            "product_layout_mode": resolved_behavior.product_policy.product_layout_mode,
            "secondary_product_mode": resolved_behavior.product_policy.secondary_product_mode,
        },
        "ownership_guards": {
            "product_annotation_owner_region": "product_region",
            "title_owner_region": "title_band_region",
            "subtitle_owner_region": "title_band_region",
            "feature_owner_region": "feature_region",
        },
        "policy_surface": {
            "header_visual_mode": resolved_behavior.header_policy.visual_mode,
            "hero_peer_layout_policy": resolved_behavior.hero_policy.peer_layout_policy,
            "feature_connector_policy": resolved_behavior.feature_policy.connector_policy,
            "bottom_peer_balance_policy": resolved_behavior.bottom_policy.bottom_peer_balance_policy,
            "gallery_distribution_policy": resolved_behavior.bottom_policy.gallery_distribution_policy,
            "product_geometry_mode": resolved_behavior.product_policy.product_geometry_mode,
        },
    }


def build_family_a_structure_surface(
    template: TemplateSpec,
    *,
    resolved_behavior,
    layer_render_status: dict[str, dict[str, object]],
    region_render_status: dict[str, dict[str, object]],
) -> dict[str, object]:
    return {
        "family_id": FAMILY_A_CAMPAIGN_EXPLAINER,
        "template_id": template.template_id,
        "region_order": list(FAMILY_A_STRUCTURE_REGION_ORDER),
        "region_bounds": {
            "header_region": _header_region_bounds(resolved_behavior),
            "scenario_region": _scenario_region_bounds(resolved_behavior),
            "product_region": _product_region_bounds(resolved_behavior),
            "feature_region": _feature_region_bounds(template),
            "bottom_region": _bottom_region_bounds(resolved_behavior),
            "title_band_region": _title_band_region_bounds(resolved_behavior),
            "gallery_strip_region": _gallery_strip_region_bounds(template, resolved_behavior),
        },
        "slot_bounds": {
            "brand_logo_slot": _header_logo_slot_bounds(template, resolved_behavior),
            "brand_name_slot": _brand_name_slot_bounds(resolved_behavior),
            "agent_name_slot": _agent_name_slot_bounds(resolved_behavior),
            "scenario_slot": _scenario_region_bounds(resolved_behavior),
            "product_slot": _product_primary_slot_bounds(resolved_behavior),
            "product_primary_slot": _product_primary_slot_bounds(resolved_behavior),
            "product_secondary_slot": _product_secondary_slot_bounds(resolved_behavior),
            "title_slot": _title_slot_bounds(template, resolved_behavior),
            "subtitle_slot": _subtitle_slot_bounds(template, resolved_behavior),
            "gallery_slot": _gallery_item_slot_bounds(template, resolved_behavior),
        },
        "visible_item_count": {
            "header_region": int(region_render_status.get("header_region", {}).get("count", 0)),
            "scenario_region": int(region_render_status.get("scenario_region", {}).get("count", 0)),
            "product_region": int(region_render_status.get("product_region", {}).get("count", 0)),
            "feature_region": int(region_render_status.get("feature_region", {}).get("count", 0)),
            "title_band_region": int(region_render_status.get("title_band_region", {}).get("count", 0)),
            "gallery_strip_region": int(layer_render_status.get("bottom_gallery_items_layer", {}).get("count_visible", 0)),
            "bottom_region": int(region_render_status.get("bottom_region", {}).get("count", 0)),
        },
    }


def _header_region_bounds(resolved_behavior) -> dict[str, int]:
    metrics = resolved_behavior.header_policy.layout_metrics
    return {
        "x": int(metrics["header_banner_left"]),
        "y": int(metrics["header_banner_top"]),
        "w": int(metrics["header_banner_width"]),
        "h": int(metrics["header_banner_height"]),
    }


def _header_logo_slot_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    metrics = resolved_behavior.header_policy.layout_metrics
    return {
        "x": int(template.logo_slot.x),
        "y": int(template.logo_slot.y),
        "w": int(metrics["header_logo_width"]),
        "h": int(metrics["header_logo_height"]),
    }


def _brand_name_slot_bounds(resolved_behavior) -> dict[str, int]:
    metrics = resolved_behavior.header_policy.layout_metrics
    return {
        "x": int(metrics["brand_slot_x"]),
        "y": int(metrics["brand_slot_y"]),
        "w": int(metrics["brand_slot_w"]),
        "h": int(metrics["brand_slot_h"]),
    }


def _agent_name_slot_bounds(resolved_behavior) -> dict[str, int]:
    metrics = resolved_behavior.header_policy.layout_metrics
    return {
        "x": int(metrics["agent_slot_x"]),
        "y": int(metrics["agent_slot_y"]),
        "w": int(metrics["agent_slot_w"]),
        "h": int(metrics["agent_slot_h"]),
    }


def _scenario_region_bounds(resolved_behavior) -> dict[str, int]:
    metrics = resolved_behavior.hero_policy.layout_metrics
    return {
        "x": int(metrics["scenario_region_x"]),
        "y": int(metrics["scenario_region_y"]),
        "w": int(metrics["scenario_region_w"]),
        "h": int(metrics["scenario_region_h"]),
    }


def _product_region_bounds(resolved_behavior) -> dict[str, int]:
    product_policy = getattr(resolved_behavior, "product_policy", None)
    metrics = getattr(product_policy, "layout_metrics", None) or resolved_behavior.hero_policy.layout_metrics
    return {
        "x": int(metrics["product_region_x"]),
        "y": int(metrics["product_region_y"]),
        "w": int(metrics["product_region_w"]),
        "h": int(metrics["product_region_h"]),
    }


def _feature_region_bounds(template: TemplateSpec) -> dict[str, int]:
    if not template.feature_callouts:
        return {"x": 0, "y": 0, "w": 0, "h": 0}
    left = min(int(callout.label_box.x) for callout in template.feature_callouts)
    top = min(int(callout.label_box.y) for callout in template.feature_callouts)
    right = max(int(callout.label_box.x + callout.label_box.w) for callout in template.feature_callouts)
    bottom = max(int(callout.label_box.y + callout.label_box.h) for callout in template.feature_callouts)
    return {"x": left, "y": top, "w": right - left, "h": bottom - top}


def _bottom_region_bounds(resolved_behavior) -> dict[str, int]:
    layout = resolved_behavior.bottom_policy.layout_metrics
    return {
        "x": 96,
        "y": int(layout.get("bottom_shell_top", 0)),
        "w": 832,
        "h": int(layout.get("bottom_shell_height", layout.get("bottom_shell_h", 0))),
    }


def _title_band_region_bounds(resolved_behavior) -> dict[str, int]:
    layout = resolved_behavior.bottom_policy.layout_metrics
    return {
        "x": int(layout.get("title_band_x", 112)),
        "y": int(layout["title_band_top"]),
        "w": int(layout.get("title_band_w", 800)),
        "h": int(layout["title_band_height"]),
    }


def _gallery_strip_region_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    layout = resolved_behavior.bottom_policy.layout_metrics
    return {
        "x": int(layout.get("gallery_shell_x", template.gallery_slot.x)),
        "y": int(layout.get("gallery_shell_top", template.gallery_slot.y)),
        "w": int(layout.get("gallery_shell_w", template.gallery_slot.w)),
        "h": int(layout.get("gallery_shell_height", template.gallery_slot.h)),
    }


def _product_primary_slot_bounds(resolved_behavior) -> dict[str, int]:
    primary = resolved_behavior.product_policy.product_primary_slot
    return {
        "x": int(primary["x"]),
        "y": int(primary["y"]),
        "w": int(primary["w"]),
        "h": int(primary["h"]),
    }


def _product_secondary_slot_bounds(resolved_behavior) -> dict[str, int]:
    secondary = resolved_behavior.product_policy.product_secondary_slot
    if secondary is None:
        return {"x": 0, "y": 0, "w": 0, "h": 0}
    return {
        "x": int(secondary["x"]),
        "y": int(secondary["y"]),
        "w": int(secondary["w"]),
        "h": int(secondary["h"]),
    }


def _title_slot_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    layout = resolved_behavior.bottom_policy.layout_metrics
    return {
        "x": int(layout.get("title_band_x", template.title_slot.x)),
        "y": int(layout.get("title_slot_y", template.title_slot.y)),
        "w": int(layout.get("title_band_w", template.title_slot.w)),
        "h": int(layout.get("title_slot_height", template.title_slot.h)),
    }


def _subtitle_slot_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    layout = resolved_behavior.bottom_policy.layout_metrics
    return {
        "x": int(layout.get("subtitle_slot_x", template.subtitle_slot.x)),
        "y": int(layout.get("subtitle_slot_y", template.subtitle_slot.y)),
        "w": int(layout.get("subtitle_slot_w", template.subtitle_slot.w)),
        "h": int(layout.get("subtitle_slot_height", template.subtitle_slot.h)),
    }


def _gallery_item_slot_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    gallery_layouts = list(resolved_behavior.bottom_policy.layout_metrics.get("gallery_item_layouts", []))
    if gallery_layouts:
        first = gallery_layouts[0]
        return {
            "x": int(first["x"]),
            "y": int(first["y"]),
            "w": int(first["w"]),
            "h": int(first["h"]),
        }
    return {
        "x": int(template.gallery_slot.x),
        "y": int(template.gallery_slot.y),
        "w": int(template.gallery_slot.thumb_w),
        "h": int(template.gallery_slot.h),
    }
