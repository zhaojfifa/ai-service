"""
Poster2 template family registry and metadata resolution.

This module establishes the family-level source of truth that later routing,
region, slot, and quality-guard logic can build on top of.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from .contracts import TemplateSpec

RegistryRendererMode = Literal["auto", "pillow", "puppeteer"]


class TemplateRegistryError(ValueError):
    """Raised when template registry metadata cannot be resolved or validated."""


@dataclass(frozen=True)
class TemplateFamilyDefinition:
    family_id: str
    display_name: str
    description: str
    default_preferred_renderer: RegistryRendererMode
    default_fallback_renderer: Optional[RegistryRendererMode]
    output_semantics: tuple[str, ...]


@dataclass(frozen=True)
class TemplateMetadata:
    template_id: str
    template_version: str
    template_family: str
    family_mode: str
    preferred_renderer: RegistryRendererMode
    fallback_renderer: Optional[RegistryRendererMode]
    allowed_fallback_reason_codes: tuple[str, ...]
    minimum_deliverable_regions: tuple[str, ...]


FAMILY_A_CAMPAIGN_EXPLAINER = "family_a_campaign_explainer"
FAMILY_B_PRODUCT_SHEET_STORY = "family_b_product_sheet_story"

_FAMILY_REGISTRY: dict[str, TemplateFamilyDefinition] = {
    FAMILY_A_CAMPAIGN_EXPLAINER: TemplateFamilyDefinition(
        family_id=FAMILY_A_CAMPAIGN_EXPLAINER,
        display_name="Family A: Campaign Explainer",
        description="Marketing explainer posters with coordinated header, hero, title band, and gallery regions.",
        default_preferred_renderer="puppeteer",
        default_fallback_renderer="pillow",
        output_semantics=(
            "degraded_must_be_explicit",
            "incomplete_structure_must_be_explicit",
            "deliverable_requires_minimum_structure",
        ),
    ),
    FAMILY_B_PRODUCT_SHEET_STORY: TemplateFamilyDefinition(
        family_id=FAMILY_B_PRODUCT_SHEET_STORY,
        display_name="Family B: Product Sheet / Product Story",
        description="Product-sheet and product-story posters with hero product and structured info regions.",
        default_preferred_renderer="puppeteer",
        default_fallback_renderer="pillow",
        output_semantics=(
            "degraded_must_be_explicit",
            "incomplete_structure_must_be_explicit",
            "deliverable_requires_minimum_structure",
        ),
    ),
}

_TEMPLATE_REGISTRY: dict[str, TemplateMetadata] = {
    "template_dual_v2": TemplateMetadata(
        template_id="template_dual_v2",
        template_version="2.1.6",
        template_family=FAMILY_A_CAMPAIGN_EXPLAINER,
        family_mode="campaign_explainer_core",
        preferred_renderer="puppeteer",
        fallback_renderer="pillow",
        allowed_fallback_reason_codes=(
            "puppeteer_timeout",
            "puppeteer_template_render_failed",
            "puppeteer_navigation_failed",
            "puppeteer_screenshot_failed",
            "puppeteer_browser_launch_failed",
            "puppeteer_asset_load_failed",
            "puppeteer_missing_chromium",
            "puppeteer_missing_system_libs",
            "puppeteer_unknown_error",
        ),
        minimum_deliverable_regions=(
            "header_region",
            "product_region",
            "title_band_region",
        ),
    ),
    # Opt-in Visual Relaxation variant of template_dual_v2. Same Family A shell,
    # assets, regions, slots, ownership, and behavior — differs ONLY by the
    # non-geometric relaxation preset baked into its spec (relaxation_preset:
    # "airy"). Reuses template_dual_v2's render assets as byte-identical copies.
    "template_dual_v2_airy": TemplateMetadata(
        template_id="template_dual_v2_airy",
        template_version="2.1.6-airy.1",
        template_family=FAMILY_A_CAMPAIGN_EXPLAINER,
        family_mode="campaign_explainer_core",
        preferred_renderer="puppeteer",
        fallback_renderer="pillow",
        allowed_fallback_reason_codes=(
            "puppeteer_timeout",
            "puppeteer_template_render_failed",
            "puppeteer_navigation_failed",
            "puppeteer_screenshot_failed",
            "puppeteer_browser_launch_failed",
            "puppeteer_asset_load_failed",
            "puppeteer_missing_chromium",
            "puppeteer_missing_system_libs",
            "puppeteer_unknown_error",
        ),
        minimum_deliverable_regions=(
            "header_region",
            "product_region",
            "title_band_region",
        ),
    ),
    "template_product_sheet_v1": TemplateMetadata(
        template_id="template_product_sheet_v1",
        template_version="1.0.0",
        template_family=FAMILY_B_PRODUCT_SHEET_STORY,
        family_mode="product_sheet_core",
        preferred_renderer="puppeteer",
        fallback_renderer="pillow",
        allowed_fallback_reason_codes=(
            "puppeteer_timeout",
            "puppeteer_template_render_failed",
            "puppeteer_navigation_failed",
            "puppeteer_screenshot_failed",
            "puppeteer_browser_launch_failed",
            "puppeteer_asset_load_failed",
            "puppeteer_missing_chromium",
            "puppeteer_missing_system_libs",
            "puppeteer_unknown_error",
        ),
        minimum_deliverable_regions=(
            "logo_banner_region",
            "top_copy_region",
            "product_hero_region",
        ),
    ),
}


def get_family_registry() -> dict[str, TemplateFamilyDefinition]:
    return dict(_FAMILY_REGISTRY)


def get_template_registry() -> dict[str, TemplateMetadata]:
    return dict(_TEMPLATE_REGISTRY)


def resolve_family_definition(family_id: str) -> TemplateFamilyDefinition:
    try:
        return _FAMILY_REGISTRY[family_id]
    except KeyError as exc:
        raise TemplateRegistryError(f"Unknown template family: {family_id}") from exc


def resolve_template_metadata(template_id: str) -> TemplateMetadata:
    try:
        return _TEMPLATE_REGISTRY[template_id]
    except KeyError as exc:
        raise TemplateRegistryError(
            f"Template family registry has no entry for template_id={template_id}"
        ) from exc


def validate_template_registration(template: TemplateSpec) -> TemplateMetadata:
    metadata = resolve_template_metadata(template.template_id)
    if metadata.template_version != template.version:
        raise TemplateRegistryError(
            "Template registry version mismatch for "
            f"{template.template_id}: registry={metadata.template_version} spec={template.version}"
        )
    resolve_family_definition(metadata.template_family)
    return metadata


# Family A campaign-explainer template lineage (template_dual_v2 + its opt-in
# relaxation variants). Used by the Stage2 pipeline / copy optimizer to apply the
# identical Family A background, text-normalization, and copy-optimization
# branches to every member, so a relaxation variant differs from the base ONLY by
# its non-geometric relaxation preset. Membership preserves existing behavior for
# template_dual_v2 (still True) and template_product_sheet_v1 (still False).
CAMPAIGN_EXPLAINER_TEMPLATE_IDS: frozenset[str] = frozenset(
    {
        "template_dual_v2",
        "template_dual_v2_airy",
    }
)


def is_campaign_explainer_template(template_id: str) -> bool:
    """True for the template_dual_v2 Family A campaign-explainer lineage."""
    return template_id in CAMPAIGN_EXPLAINER_TEMPLATE_IDS
