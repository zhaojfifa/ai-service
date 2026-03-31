"""
Poster2 slot contract resolver and binding evaluation.

This module moves poster2 from region-level structure to executable slot-level
contracts without introducing layout or beauty logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .contracts import PosterSpec, ResolvedAssets, TemplateSpec
from .template_registry import (
    FAMILY_A_CAMPAIGN_EXPLAINER,
    FAMILY_B_PRODUCT_SHEET_STORY,
    TemplateMetadata,
    resolve_template_metadata,
)


class SlotContractResolverError(ValueError):
    """Raised when slot contracts cannot be resolved for a template family."""


@dataclass(frozen=True)
class SlotContractDefinition:
    slot_id: str
    region_id: str
    source_binding: str
    required: bool
    count_min: int
    count_max: int
    collapse_rule: str
    failure_semantics: str
    is_array: bool = False


@dataclass(frozen=True)
class ResolvedSlotContracts:
    template_id: str
    template_family: str
    family_mode: str
    slots: dict[str, SlotContractDefinition]


@dataclass
class SlotBindingReport:
    rendered_required_slots: list[str] = field(default_factory=list)
    missing_required_slots: list[str] = field(default_factory=list)
    collapsed_optional_slots: list[str] = field(default_factory=list)
    slot_violation_reasons: dict[str, list[str]] = field(default_factory=dict)

    def add_violation(self, slot_id: str, reason: str) -> None:
        self.slot_violation_reasons.setdefault(slot_id, []).append(reason)

    def to_dict(self) -> dict[str, object]:
        return {
            "rendered_required_slots": sorted(self.rendered_required_slots),
            "missing_required_slots": sorted(self.missing_required_slots),
            "collapsed_optional_slots": sorted(self.collapsed_optional_slots),
            "slot_violation_reasons": {
                key: reasons
                for key, reasons in sorted(self.slot_violation_reasons.items())
            },
        }


def resolve_slot_contracts_for_template(
    template_id: str,
    template: Optional[TemplateSpec] = None,
) -> ResolvedSlotContracts:
    metadata = resolve_template_metadata(template_id)
    return resolve_slot_contracts(metadata, template=template)


def resolve_slot_contracts(
    metadata: TemplateMetadata,
    template: Optional[TemplateSpec] = None,
) -> ResolvedSlotContracts:
    if metadata.template_family == FAMILY_A_CAMPAIGN_EXPLAINER:
        return _resolve_family_a_slot_contracts(metadata, template)
    if metadata.template_family == FAMILY_B_PRODUCT_SHEET_STORY:
        return _resolve_family_b_slot_contracts(metadata)
    raise SlotContractResolverError(
        f"Unsupported template family for slot contract resolution: {metadata.template_family}"
    )


# Slots that are excused from the required check when a given bottom_mode is active.
# In gallery_only mode, title_slot is collapsed by design (no title band is shown),
# so it must not count as missing_required even when the request omits a title.
_BOTTOM_MODE_EXCUSED_REQUIRED_SLOTS: dict[str, frozenset[str]] = {
    "gallery_only": frozenset({"title_slot"}),
}


def evaluate_slot_bindings(
    metadata: TemplateMetadata,
    template: TemplateSpec,
    spec: PosterSpec,
    assets: ResolvedAssets,
    *,
    binding_inputs: Optional[dict[str, Any]] = None,
) -> SlotBindingReport:
    contracts = resolve_slot_contracts(metadata, template=template)
    report = SlotBindingReport()
    binding_inputs = binding_inputs or {}
    bottom_mode = binding_inputs.get("bottom_mode") or ""
    mode_excused = _BOTTOM_MODE_EXCUSED_REQUIRED_SLOTS.get(bottom_mode, frozenset())
    for slot_id, contract in contracts.slots.items():
        rendered_count = _resolve_rendered_count(contract, spec, assets, binding_inputs)
        effective_required = contract.required and slot_id not in mode_excused
        if effective_required:
            if rendered_count >= contract.count_min:
                report.rendered_required_slots.append(slot_id)
            else:
                report.missing_required_slots.append(slot_id)
                report.add_violation(slot_id, contract.failure_semantics)
                continue
        elif rendered_count == 0:
            report.collapsed_optional_slots.append(slot_id)

        if rendered_count < contract.count_min:
            report.add_violation(
                slot_id,
                f"count_below_min:{rendered_count}<{contract.count_min}",
            )
        if rendered_count > contract.count_max:
            report.add_violation(
                slot_id,
                f"count_above_max:{rendered_count}>{contract.count_max}",
            )
    _apply_cross_slot_rules(metadata, spec, assets, binding_inputs, report)
    return report


def _resolve_family_a_slot_contracts(
    metadata: TemplateMetadata,
    template: Optional[TemplateSpec],
) -> ResolvedSlotContracts:
    feature_count_max = len(template.feature_callouts) if template else 4
    gallery_count_max = template.gallery_slot.count if template else 4
    slots = {
        "brand_logo_slot": SlotContractDefinition(
            slot_id="brand_logo_slot",
            region_id="header_region",
            source_binding="logo",
            required=False,
            count_min=0,
            count_max=1,
            collapse_rule="collapse when logo binding is absent",
            failure_semantics="header_region fails when logo and brand text are both missing",
        ),
        "brand_text_slot": SlotContractDefinition(
            slot_id="brand_text_slot",
            region_id="header_region",
            source_binding="brand_name",
            required=False,
            count_min=0,
            count_max=1,
            collapse_rule="collapse when brand_name is empty",
            failure_semantics="header_region fails when logo and brand text are both missing",
        ),
        "agent_name_text_slot": SlotContractDefinition(
            slot_id="agent_name_text_slot",
            region_id="header_region",
            source_binding="agent_name",
            required=False,
            count_min=0,
            count_max=1,
            collapse_rule="collapse when agent_name is empty",
            failure_semantics="secondary agent text may collapse without invalidating header_region",
        ),
        "product_image_slot": SlotContractDefinition(
            slot_id="product_image_slot",
            region_id="product_region",
            source_binding="product_image",
            required=True,
            count_min=1,
            count_max=1,
            collapse_rule="must not collapse",
            failure_semantics="product_region fails when product_image is missing",
        ),
        "scenario_image_slot": SlotContractDefinition(
            slot_id="scenario_image_slot",
            region_id="scenario_region",
            source_binding="scenario_image",
            required=False,
            count_min=0,
            count_max=1,
            collapse_rule="collapse when scenario_image is absent",
            failure_semantics="scenario_region may collapse without failing Family A minimum deliverable",
        ),
        "feature_item_slot[]": SlotContractDefinition(
            slot_id="feature_item_slot[]",
            region_id="feature_region",
            source_binding="features",
            required=False,
            count_min=0,
            count_max=feature_count_max,
            collapse_rule="collapse unused feature slots and connectors together",
            failure_semantics="feature_region violation when ghost connectors or ghost boxes remain",
            is_array=True,
        ),
        "title_slot": SlotContractDefinition(
            slot_id="title_slot",
            region_id="title_band_region",
            source_binding="title",
            required=True,
            count_min=1,
            count_max=1,
            collapse_rule="must not collapse",
            failure_semantics="title_band_region fails when title is missing",
        ),
        "subtitle_slot": SlotContractDefinition(
            slot_id="subtitle_slot",
            region_id="title_band_region",
            source_binding="subtitle",
            required=False,
            count_min=0,
            count_max=1,
            collapse_rule="collapse when subtitle is empty",
            failure_semantics="subtitle may collapse without invalidating title_band_region",
        ),
        "gallery_item_slot[]": SlotContractDefinition(
            slot_id="gallery_item_slot[]",
            region_id="gallery_strip_region",
            source_binding="gallery_images",
            required=False,
            count_min=0,
            count_max=gallery_count_max,
            collapse_rule="collapse gallery strip when no gallery items are available",
            failure_semantics="gallery_strip_region violation when strip is shown with empty gallery items",
            is_array=True,
        ),
    }
    return ResolvedSlotContracts(
        template_id=metadata.template_id,
        template_family=metadata.template_family,
        family_mode=metadata.family_mode,
        slots=slots,
    )


def _resolve_family_b_slot_contracts(metadata: TemplateMetadata) -> ResolvedSlotContracts:
    slots = {
        "brand_text_slot": SlotContractDefinition(
            slot_id="brand_text_slot",
            region_id="brand_banner_region",
            source_binding="brand_name",
            required=True,
            count_min=1,
            count_max=1,
            collapse_rule="must not collapse",
            failure_semantics="brand_banner_region fails when brand identity is missing",
        ),
        "reference_slot": SlotContractDefinition(
            slot_id="reference_slot",
            region_id="reference_region",
            source_binding="reference_text",
            required=False,
            count_min=0,
            count_max=1,
            collapse_rule="collapse when reference_text is empty",
            failure_semantics="reference_region may collapse without failing Family B",
        ),
        "product_image_slot": SlotContractDefinition(
            slot_id="product_image_slot",
            region_id="hero_product_region",
            source_binding="product_image",
            required=True,
            count_min=1,
            count_max=1,
            collapse_rule="must not collapse",
            failure_semantics="hero_product_region fails when product_image is missing",
        ),
        "supporting_image_slot[]": SlotContractDefinition(
            slot_id="supporting_image_slot[]",
            region_id="hero_product_region",
            source_binding="supporting_images",
            required=False,
            count_min=0,
            count_max=4,
            collapse_rule="collapse unused supporting images without changing hero product semantics",
            failure_semantics="supporting visuals may collapse without failing Family B",
            is_array=True,
        ),
        "spec_item_slot[]": SlotContractDefinition(
            slot_id="spec_item_slot[]",
            region_id="spec_region",
            source_binding="spec_items",
            required=False,
            count_min=0,
            count_max=8,
            collapse_rule="collapse when no spec items exist",
            failure_semantics="spec_region requires valid spec entries when rendered",
            is_array=True,
        ),
        "copy_slot": SlotContractDefinition(
            slot_id="copy_slot",
            region_id="copy_region",
            source_binding="copy_text",
            required=False,
            count_min=0,
            count_max=1,
            collapse_rule="collapse when copy_text is empty",
            failure_semantics="copy_region requires text when rendered",
        ),
        "cta_slot": SlotContractDefinition(
            slot_id="cta_slot",
            region_id="cta_region",
            source_binding="cta_text",
            required=False,
            count_min=0,
            count_max=1,
            collapse_rule="collapse when cta_text is empty",
            failure_semantics="cta may collapse without failing Family B",
        ),
        "footer_brand_slot": SlotContractDefinition(
            slot_id="footer_brand_slot",
            region_id="footer_brand_region",
            source_binding="footer_brand_text",
            required=False,
            count_min=0,
            count_max=1,
            collapse_rule="collapse when footer brand text is empty",
            failure_semantics="footer brand may collapse without failing Family B",
        ),
    }
    return ResolvedSlotContracts(
        template_id=metadata.template_id,
        template_family=metadata.template_family,
        family_mode=metadata.family_mode,
        slots=slots,
    )


def _resolve_rendered_count(
    contract: SlotContractDefinition,
    spec: PosterSpec,
    assets: ResolvedAssets,
    binding_inputs: dict[str, Any],
) -> int:
    binding = contract.source_binding
    if binding == "logo":
        return 1 if assets.logo is not None else 0
    if binding == "brand_name":
        return 1 if spec.brand_name else 0
    if binding == "agent_name":
        return 1 if spec.agent_name else 0
    if binding == "product_image":
        return 1 if assets.product is not None else 0
    if binding == "scenario_image":
        return 1 if assets.scenario is not None else 0
    if binding == "features":
        return min(len([item for item in spec.features if item]), contract.count_max)
    if binding == "title":
        return 1 if spec.title else 0
    if binding == "subtitle":
        return 1 if spec.subtitle else 0
    if binding == "gallery_images":
        return min(len(assets.gallery), contract.count_max)
    raw = binding_inputs.get(binding)
    if contract.is_array:
        if not raw:
            return 0
        if isinstance(raw, (list, tuple)):
            return len([item for item in raw if item])
        return 1
    return 1 if raw else 0


def _apply_cross_slot_rules(
    metadata: TemplateMetadata,
    spec: PosterSpec,
    assets: ResolvedAssets,
    binding_inputs: dict[str, Any],
    report: SlotBindingReport,
) -> None:
    if metadata.template_family == FAMILY_A_CAMPAIGN_EXPLAINER:
        if not spec.brand_name and assets.logo is None:
            report.add_violation(
                "header_region",
                "brand_logo_slot and brand_text_slot cannot both be absent",
            )
        return
    if metadata.template_family == FAMILY_B_PRODUCT_SHEET_STORY:
        spec_items = binding_inputs.get("spec_items") or []
        copy_text = binding_inputs.get("copy_text") or ""
        if not spec_items and not copy_text:
            report.add_violation(
                "family_b_information_core",
                "spec_item_slot[] or copy_slot must satisfy minimum information delivery",
            )
