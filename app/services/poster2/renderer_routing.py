"""
Family-aware renderer routing and fallback gating for poster2.

This layer keeps the current pipeline shape while making renderer selection
and fallback eligibility explicit, explainable, and contract-aware.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from .contracts import PosterSpec, RendererMode, ResolvedAssets, TemplateSpec
from .slot_contracts import evaluate_slot_bindings
from .template_registry import TemplateMetadata

RoutingFailureType = Literal["renderer_failure", "contract_input_failure", "fallback_structure_failure"]


@dataclass(frozen=True)
class RendererRoutingDecision:
    requested_renderer_mode: RendererMode
    preferred_renderer: RendererMode
    effective_renderer_mode: RendererMode
    fallback_renderer: Optional[RendererMode]
    template_family: str
    template_id: str
    template_version: str
    family_mode: str


@dataclass(frozen=True)
class FallbackEligibility:
    eligible: bool
    failure_type: RoutingFailureType
    reason_code: Optional[str]
    detail: Optional[str]


class RendererRoutingError(RuntimeError):
    """Raised when renderer routing cannot legally degrade."""

    def __init__(self, reason_code: str, detail: str, *, failure_type: RoutingFailureType):
        super().__init__(detail)
        self.reason_code = reason_code
        self.detail = detail
        self.failure_type = failure_type


def resolve_renderer_routing(
    metadata: TemplateMetadata,
    requested_renderer_mode: RendererMode,
    *,
    default_mode: RendererMode = "pillow",
) -> RendererRoutingDecision:
    preferred_renderer = metadata.preferred_renderer
    if preferred_renderer == "auto":
        preferred_renderer = default_mode

    if requested_renderer_mode == "auto":
        effective_renderer_mode = preferred_renderer
    else:
        effective_renderer_mode = requested_renderer_mode

    fallback_renderer = metadata.fallback_renderer
    if fallback_renderer == "auto":
        fallback_renderer = default_mode

    return RendererRoutingDecision(
        requested_renderer_mode=requested_renderer_mode,
        preferred_renderer=preferred_renderer,
        effective_renderer_mode=effective_renderer_mode,
        fallback_renderer=fallback_renderer,
        template_family=metadata.template_family,
        template_id=metadata.template_id,
        template_version=metadata.template_version,
        family_mode=metadata.family_mode,
    )


def evaluate_fallback_eligibility(
    metadata: TemplateMetadata,
    template: TemplateSpec,
    spec: PosterSpec,
    assets: ResolvedAssets,
) -> FallbackEligibility:
    if assets.product is None:
        return FallbackEligibility(
            eligible=False,
            failure_type="contract_input_failure",
            reason_code="missing_product_image",
            detail="product_image is required and fallback must not hide its absence",
        )

    slot_report = evaluate_slot_bindings(metadata, template, spec, assets)
    if slot_report.missing_required_slots:
        return FallbackEligibility(
            eligible=False,
            failure_type="contract_input_failure",
            reason_code="missing_required_input",
            detail=(
                "required slot bindings are missing: "
                + ", ".join(sorted(slot_report.missing_required_slots))
            ),
        )

    if not metadata.fallback_renderer:
        return FallbackEligibility(
            eligible=False,
            failure_type="renderer_failure",
            reason_code="fallback_renderer_unavailable",
            detail="template family has no configured fallback renderer",
        )

    return FallbackEligibility(
        eligible=True,
        failure_type="renderer_failure",
        reason_code=None,
        detail=None,
    )


def assert_fallback_result_is_deliverable(
    *,
    slot_binding_status: dict[str, object],
    region_completeness_status: dict[str, object],
) -> None:
    missing_required_slots = slot_binding_status.get("missing_required_slots") or []
    if missing_required_slots:
        raise RendererRoutingError(
            "fallback_missing_required_slots",
            "fallback result is missing required slots: " + ", ".join(missing_required_slots),
            failure_type="fallback_structure_failure",
        )

    family_complete = bool(region_completeness_status.get("family_minimum_region_complete", False))
    if not family_complete:
        missing_regions = region_completeness_status.get("missing_mandatory_regions") or []
        detail = "fallback result does not satisfy minimum deliverable regions"
        if missing_regions:
            detail += ": " + ", ".join(missing_regions)
        raise RendererRoutingError(
            "fallback_incomplete_structure",
            detail,
            failure_type="fallback_structure_failure",
        )


def assert_quality_guard_deliverable(
    *,
    deliverable: bool,
    missing_required_slots: list[str],
    missing_mandatory_regions: list[str],
) -> None:
    if missing_required_slots:
        raise RendererRoutingError(
            "fallback_missing_required_slots",
            "fallback result is missing required slots: " + ", ".join(missing_required_slots),
            failure_type="fallback_structure_failure",
        )
    if not deliverable:
        detail = "fallback result does not satisfy minimum deliverable regions"
        if missing_mandatory_regions:
            detail += ": " + ", ".join(missing_mandatory_regions)
        raise RendererRoutingError(
            "fallback_incomplete_structure",
            detail,
            failure_type="fallback_structure_failure",
        )
