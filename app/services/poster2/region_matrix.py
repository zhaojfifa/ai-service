"""
Poster2 region matrix resolver.

This module resolves family-level region contracts into executable metadata
without changing renderer, slot, or quality-guard behavior yet.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .template_registry import (
    FAMILY_A_CAMPAIGN_EXPLAINER,
    FAMILY_B_PRODUCT_SHEET_STORY,
    TemplateMetadata,
    resolve_template_metadata,
)

_HTML_TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "app" / "templates_html"


class RegionMatrixResolverError(ValueError):
    """Raised when a region matrix cannot be resolved for a template family."""


@dataclass(frozen=True)
class RegionDefinition:
    region_id: str
    role: str
    status: str
    mandatory: bool
    collapsible: bool
    x: Optional[int] = None
    y: Optional[int] = None
    w: Optional[int] = None
    h: Optional[int] = None
    z_index: Optional[int] = None
    replacement_rules: tuple[str, ...] = ()
    minimum_success_conditions: tuple[str, ...] = ()
    collapse_conditions: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResolvedRegionMatrix:
    template_id: str
    template_family: str
    family_mode: str
    region_order: tuple[str, ...]
    mandatory_regions: tuple[str, ...]
    collapsible_regions: tuple[str, ...]
    regions: dict[str, RegionDefinition]


@dataclass
class RegionCompletenessReport:
    rendered_regions: list[str]
    collapsed_regions: list[str]
    missing_mandatory_regions: list[str]
    region_violation_reasons: dict[str, list[str]]
    family_minimum_region_complete: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "rendered_regions": sorted(self.rendered_regions),
            "collapsed_regions": sorted(self.collapsed_regions),
            "missing_mandatory_regions": sorted(self.missing_mandatory_regions),
            "region_violation_reasons": {
                key: reasons for key, reasons in sorted(self.region_violation_reasons.items())
            },
            "family_minimum_region_complete": self.family_minimum_region_complete,
        }


def resolve_region_matrix_for_template(template_id: str) -> ResolvedRegionMatrix:
    metadata = resolve_template_metadata(template_id)
    return resolve_region_matrix(metadata)


def resolve_region_matrix(metadata: TemplateMetadata) -> ResolvedRegionMatrix:
    if metadata.template_family == FAMILY_A_CAMPAIGN_EXPLAINER:
        return _resolve_family_a_matrix(metadata)
    if metadata.template_family == FAMILY_B_PRODUCT_SHEET_STORY:
        return _resolve_family_b_matrix(metadata)
    raise RegionMatrixResolverError(
        f"Unsupported template family for region matrix resolution: {metadata.template_family}"
    )


def evaluate_region_completeness(
    metadata: TemplateMetadata,
    *,
    layer_status: Optional[dict[str, dict[str, object]]] = None,
    region_status: Optional[dict[str, dict[str, object]]] = None,
    binding_inputs: Optional[dict[str, Any]] = None,
) -> RegionCompletenessReport:
    matrix = resolve_region_matrix(metadata)
    presence = _resolve_region_presence(
        matrix,
        layer_status=layer_status or {},
        region_status=region_status or {},
        binding_inputs=binding_inputs or {},
    )
    rendered_regions = [name for name, state in presence.items() if state["rendered"]]
    collapsed_regions = [name for name, state in presence.items() if state["collapsed"]]
    missing_mandatory_regions = [
        name for name in matrix.mandatory_regions if not presence.get(name, {}).get("rendered", False)
    ]
    region_violation_reasons: dict[str, list[str]] = {}
    for name, state in presence.items():
        reasons = list(state.get("reasons", []))
        if reasons:
            region_violation_reasons[name] = reasons
    for name in missing_mandatory_regions:
        region_violation_reasons.setdefault(name, []).append("mandatory_region_missing")
    return RegionCompletenessReport(
        rendered_regions=rendered_regions,
        collapsed_regions=collapsed_regions,
        missing_mandatory_regions=missing_mandatory_regions,
        region_violation_reasons=region_violation_reasons,
        family_minimum_region_complete=len(missing_mandatory_regions) == 0,
    )


def _resolve_family_a_matrix(metadata: TemplateMetadata) -> ResolvedRegionMatrix:
    slot_spec = _load_slot_spec(metadata.template_id)
    region_bounds = slot_spec.get("regions", {})
    region_order = (
        "header_region",
        "scenario_region",
        "product_region",
        "feature_region",
        "bottom_region",
        "title_band_region",
        "gallery_strip_region",
    )
    regions = {
        "header_region": _make_region(
            "header_region",
            role="branding_region",
            status="mandatory",
            mandatory=True,
            collapsible=False,
            bounds=region_bounds.get("header_region"),
            minimum_success_conditions=(
                "brand_logo_slot or brand_text_slot must render",
            ),
            collapse_conditions=(),
            replacement_rules=(
                "agent_name_text_slot may collapse without invalidating header_region",
            ),
        ),
        "scenario_region": _make_region(
            "scenario_region",
            role="supporting_visual_region",
            status="collapsible_preferred",
            mandatory=False,
            collapsible=True,
            bounds=region_bounds.get("scenario_region"),
            minimum_success_conditions=(
                "scenario_image_slot renders when scenario_image exists",
            ),
            collapse_conditions=(
                "collapse when scenario_image is absent",
                "collapse when family mode disables scenario visuals",
            ),
            replacement_rules=(
                "product_region may expand only within hero wrapper bounds after scenario collapse",
            ),
        ),
        "product_region": _make_region(
            "product_region",
            role="hero_region",
            status="mandatory",
            mandatory=True,
            collapsible=False,
            bounds=region_bounds.get("product_region"),
            minimum_success_conditions=(
                "product_image_slot must render once",
                "product image must not distort",
            ),
            collapse_conditions=(),
            replacement_rules=(
                "supporting visuals must not substitute product_region",
            ),
        ),
        "feature_region": _make_region(
            "feature_region",
            role="proof_region",
            status="collapsible",
            mandatory=False,
            collapsible=True,
            bounds=region_bounds.get("feature_region"),
            minimum_success_conditions=(
                "feature_item slots must match resolved feature count",
            ),
            collapse_conditions=(
                "collapse when features array is empty",
            ),
            replacement_rules=(
                "unused callout slots must fully collapse without ghost connectors",
            ),
        ),
        "bottom_region": _make_region(
            "bottom_region",
            role="footer_region",
            status="structural_wrapper",
            mandatory=False,
            collapsible=True,
            bounds=region_bounds.get("bottom_region"),
            minimum_success_conditions=(
                "bottom wrapper may exist only as parent of title_band_region and gallery_strip_region",
            ),
            collapse_conditions=(
                "collapse when both title_band_region and gallery_strip_region are absent",
            ),
            replacement_rules=(
                "bottom wrapper must not merge title band and gallery strip semantics",
            ),
        ),
        "title_band_region": _make_region(
            "title_band_region",
            role="conversion_region",
            status="mandatory",
            mandatory=True,
            collapsible=False,
            bounds=region_bounds.get("title_band_region"),
            minimum_success_conditions=(
                "title_slot must render once",
            ),
            collapse_conditions=(),
            replacement_rules=(
                "subtitle may collapse without invalidating title_band_region",
            ),
        ),
        "gallery_strip_region": _make_region(
            "gallery_strip_region",
            role="proof_region",
            status="collapsible",
            mandatory=False,
            collapsible=True,
            bounds=region_bounds.get("gallery_strip_region"),
            minimum_success_conditions=(
                "gallery items render only for valid gallery inputs",
            ),
            collapse_conditions=(
                "collapse when gallery_images array is empty",
            ),
            replacement_rules=(
                "gallery strip must not invade title_band_region bounds",
            ),
        ),
    }
    mandatory_regions = tuple(name for name in region_order if regions[name].mandatory)
    collapsible_regions = tuple(name for name in region_order if regions[name].collapsible)
    return ResolvedRegionMatrix(
        template_id=metadata.template_id,
        template_family=metadata.template_family,
        family_mode=metadata.family_mode,
        region_order=region_order,
        mandatory_regions=mandatory_regions,
        collapsible_regions=collapsible_regions,
        regions=regions,
    )


def _resolve_family_b_matrix(metadata: TemplateMetadata) -> ResolvedRegionMatrix:
    region_order = (
        "brand_banner_region",
        "reference_region",
        "hero_product_region",
        "spec_region",
        "copy_region",
        "cta_region",
        "footer_brand_region",
    )
    regions = {
        "brand_banner_region": RegionDefinition(
            region_id="brand_banner_region",
            role="branding_region",
            status="mandatory",
            mandatory=True,
            collapsible=False,
            minimum_success_conditions=("brand banner must remain visible",),
        ),
        "reference_region": RegionDefinition(
            region_id="reference_region",
            role="proof_region",
            status="collapsible",
            mandatory=False,
            collapsible=True,
            collapse_conditions=("collapse when reference binding is empty",),
        ),
        "hero_product_region": RegionDefinition(
            region_id="hero_product_region",
            role="hero_region",
            status="mandatory",
            mandatory=True,
            collapsible=False,
            minimum_success_conditions=(
                "hero product image must render without distortion",
            ),
        ),
        "spec_region": RegionDefinition(
            region_id="spec_region",
            role="proof_region",
            status="conditional_mandatory",
            mandatory=False,
            collapsible=True,
            replacement_rules=(
                "spec_region or copy_region must satisfy minimum information delivery",
            ),
        ),
        "copy_region": RegionDefinition(
            region_id="copy_region",
            role="conversion_region",
            status="conditional_mandatory",
            mandatory=False,
            collapsible=True,
            replacement_rules=(
                "copy_region or spec_region must satisfy minimum information delivery",
            ),
        ),
        "cta_region": RegionDefinition(
            region_id="cta_region",
            role="conversion_region",
            status="collapsible",
            mandatory=False,
            collapsible=True,
            collapse_conditions=("collapse when CTA binding is empty",),
        ),
        "footer_brand_region": RegionDefinition(
            region_id="footer_brand_region",
            role="footer_region",
            status="collapsible",
            mandatory=False,
            collapsible=True,
            collapse_conditions=("collapse when footer branding is disabled",),
        ),
    }
    return ResolvedRegionMatrix(
        template_id=metadata.template_id,
        template_family=metadata.template_family,
        family_mode=metadata.family_mode,
        region_order=region_order,
        mandatory_regions=("brand_banner_region", "hero_product_region"),
        collapsible_regions=(
            "reference_region",
            "spec_region",
            "copy_region",
            "cta_region",
            "footer_brand_region",
        ),
        regions=regions,
    )


def _load_slot_spec(template_id: str) -> dict:
    path = _HTML_TEMPLATES_DIR / f"slot_spec.{template_id}.json"
    if not path.exists():
        raise RegionMatrixResolverError(f"slot spec not found for template_id={template_id}: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_region_presence(
    matrix: ResolvedRegionMatrix,
    *,
    layer_status: dict[str, dict[str, object]],
    region_status: dict[str, dict[str, object]],
    binding_inputs: dict[str, Any],
) -> dict[str, dict[str, object]]:
    if matrix.template_family == FAMILY_A_CAMPAIGN_EXPLAINER:
        return _resolve_family_a_presence(
            layer_status=layer_status,
            region_status=region_status,
            binding_inputs=binding_inputs,
        )
    if matrix.template_family == FAMILY_B_PRODUCT_SHEET_STORY:
        return _resolve_family_b_presence(binding_inputs=binding_inputs)
    raise RegionMatrixResolverError(
        f"Unsupported template family for presence evaluation: {matrix.template_family}"
    )


# Frozen per-mode bottom region contracts for Family A.
# For each canonical bottom_mode, lists the regions that are intentionally absent (collapsed by
# design). A collapsed-by-design region must NOT count as a missing mandatory region.
#
# Rules:
#   title_gallery_split   — both title_band_region and gallery_strip_region may render;
#                           neither is collapsed by design
#   text_gallery_expanded — same as title_gallery_split; gallery_strip may still be empty
#                           when no gallery items are provided, but is not absent by mode
#   text_only_expanded    — gallery_strip_region is always absent; no gallery in this mode
#   gallery_only          — title_band_region is always absent; no title band in this mode
#
# Any bottom_mode not present here is treated as unknown. Unknown modes fall back
# conservatively: no regions are excused from the mandatory check (structure may fail).
_BOTTOM_MODE_COLLAPSED_BY_DESIGN: dict[str, frozenset[str]] = {
    "title_gallery_split":   frozenset(),
    "text_gallery_expanded": frozenset(),
    "text_only_expanded":    frozenset({"gallery_strip_region"}),
    "gallery_only":          frozenset({"title_band_region"}),
}

# Reason codes emitted in presence state when a region is collapsed by design for a given mode.
_BOTTOM_MODE_COLLAPSE_REASON_CODES: dict[str, dict[str, str]] = {
    "text_only_expanded": {
        "gallery_strip_region": "collapsed_by_text_only_expanded_mode",
    },
    "gallery_only": {
        "title_band_region": "collapsed_by_gallery_only_mode",
    },
}


def _resolve_family_a_presence(
    *,
    layer_status: dict[str, dict[str, object]],
    region_status: dict[str, dict[str, object]],
    binding_inputs: dict[str, Any],
) -> dict[str, dict[str, object]]:
    def count(layer_name: str) -> int:
        return int(layer_status.get(layer_name, {}).get("count", 0))

    def region_rendered(region_name: str) -> bool:
        return bool(region_status.get(region_name, {}).get("rendered", False))

    bottom_mode = binding_inputs.get("bottom_mode") or ""
    title_rendered = count("title_layer") > 0
    gallery_rendered = count("bottom_gallery_items_layer") > 0
    bottom_rendered = region_rendered("bottom_region") or title_rendered or gallery_rendered

    # Look up frozen per-mode region collapse rules. Unknown modes fall back
    # conservatively (no regions excused) so unknown modes can never silently
    # bypass mandatory-region checks.
    mode_collapsed_by_design = _BOTTOM_MODE_COLLAPSED_BY_DESIGN.get(bottom_mode, frozenset())
    mode_collapse_reasons = _BOTTOM_MODE_COLLAPSE_REASON_CODES.get(bottom_mode, {})

    # title_band_region is intentionally absent only for modes that declare it
    # collapsed by design in the frozen contract above.
    title_band_collapsed_by_design = "title_band_region" in mode_collapsed_by_design
    title_band_region_ok = title_rendered or title_band_collapsed_by_design

    # gallery_strip_region is intentionally absent only for modes that declare it
    # collapsed by design (e.g. text_only_expanded). Its absence in other modes
    # is simply "no gallery items", not a structural failure (it is not mandatory).
    gallery_strip_collapsed_by_design = "gallery_strip_region" in mode_collapsed_by_design

    return {
        "header_region": {
            "rendered": region_rendered("header_region"),
            "collapsed": not region_rendered("header_region"),
            "reasons": [] if region_rendered("header_region") else ["brand identity missing"],
        },
        "scenario_region": {
            "rendered": region_rendered("scenario_region"),
            "collapsed": not region_rendered("scenario_region"),
            "reasons": [] if region_rendered("scenario_region") else ["scenario collapsed or unavailable"],
        },
        "product_region": {
            "rendered": region_rendered("product_region"),
            "collapsed": not region_rendered("product_region"),
            "reasons": [] if region_rendered("product_region") else ["product image missing"],
        },
        "feature_region": {
            "rendered": region_rendered("feature_region"),
            "collapsed": not region_rendered("feature_region"),
            "reasons": [] if region_rendered("feature_region") else ["feature callouts collapsed or empty"],
        },
        "title_band_region": {
            "rendered": title_band_region_ok,
            "collapsed": not title_band_region_ok,
            "collapsed_by_design": title_band_collapsed_by_design and not title_rendered,
            "reasons": (
                []
                if title_band_region_ok
                else ["title missing from title band"]
            ),
            "collapse_reason_code": (
                mode_collapse_reasons.get("title_band_region")
                if not title_rendered and title_band_collapsed_by_design
                else None
            ),
        },
        "gallery_strip_region": {
            "rendered": gallery_rendered,
            "collapsed": not gallery_rendered,
            "collapsed_by_design": gallery_strip_collapsed_by_design and not gallery_rendered,
            "reasons": [] if gallery_rendered else ["gallery strip collapsed or empty"],
            "collapse_reason_code": (
                mode_collapse_reasons.get("gallery_strip_region")
                if not gallery_rendered and gallery_strip_collapsed_by_design
                else None
            ),
        },
        "bottom_region": {
            "rendered": bottom_rendered,
            "collapsed": not bottom_rendered,
            "reasons": [] if bottom_rendered else ["bottom wrapper collapsed"],
        },
    }


def _resolve_family_b_presence(
    *,
    binding_inputs: dict[str, Any],
) -> dict[str, dict[str, object]]:
    def has_text(key: str) -> bool:
        value = binding_inputs.get(key)
        return isinstance(value, str) and bool(value.strip())

    def has_items(key: str) -> bool:
        value = binding_inputs.get(key)
        return isinstance(value, (list, tuple)) and any(bool(item) for item in value)

    brand_rendered = has_text("brand_name") or has_text("brand_banner_text")
    hero_rendered = bool(binding_inputs.get("hero_product_present"))
    reference_rendered = has_text("reference_text")
    spec_rendered = has_items("spec_items")
    copy_rendered = has_text("copy_text")
    cta_rendered = has_text("cta_text")
    footer_rendered = has_text("footer_brand_text")
    return {
        "brand_banner_region": {
            "rendered": brand_rendered,
            "collapsed": not brand_rendered,
            "reasons": [] if brand_rendered else ["brand banner missing"],
        },
        "reference_region": {
            "rendered": reference_rendered,
            "collapsed": not reference_rendered,
            "reasons": [] if reference_rendered else ["reference region collapsed"],
        },
        "hero_product_region": {
            "rendered": hero_rendered,
            "collapsed": not hero_rendered,
            "reasons": [] if hero_rendered else ["hero product missing"],
        },
        "spec_region": {
            "rendered": spec_rendered,
            "collapsed": not spec_rendered,
            "reasons": [] if spec_rendered else ["spec region collapsed"],
        },
        "copy_region": {
            "rendered": copy_rendered,
            "collapsed": not copy_rendered,
            "reasons": [] if copy_rendered else ["copy region collapsed"],
        },
        "cta_region": {
            "rendered": cta_rendered,
            "collapsed": not cta_rendered,
            "reasons": [] if cta_rendered else ["cta region collapsed"],
        },
        "footer_brand_region": {
            "rendered": footer_rendered,
            "collapsed": not footer_rendered,
            "reasons": [] if footer_rendered else ["footer brand region collapsed"],
        },
    }


def _make_region(
    region_id: str,
    *,
    role: str,
    status: str,
    mandatory: bool,
    collapsible: bool,
    bounds: Optional[dict],
    replacement_rules: tuple[str, ...],
    minimum_success_conditions: tuple[str, ...],
    collapse_conditions: tuple[str, ...],
) -> RegionDefinition:
    bounds = bounds or {}
    return RegionDefinition(
        region_id=region_id,
        role=role,
        status=status,
        mandatory=mandatory,
        collapsible=collapsible,
        x=bounds.get("x"),
        y=bounds.get("y"),
        w=bounds.get("w"),
        h=bounds.get("h"),
        z_index=bounds.get("z"),
        replacement_rules=replacement_rules,
        minimum_success_conditions=minimum_success_conditions,
        collapse_conditions=collapse_conditions,
    )
