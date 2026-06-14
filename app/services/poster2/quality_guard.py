"""
Poster2 quality guard: preflight validation and deliverability semantics.

This module separates "an image was rendered" from "a deliverable poster was
produced" and keeps the outcome explainable for engineering, ops, and product.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .contracts import PosterSpec, ResolvedAssets, TemplateSpec
from .region_matrix import evaluate_region_completeness
from .slot_contracts import evaluate_slot_bindings
from .template_registry import (
    TemplateRegistryError,
    resolve_family_definition,
    resolve_template_metadata,
    validate_template_registration,
)


class QualityGuardError(ValueError):
    """Raised when poster2 preflight or deliverability validation fails."""

    def __init__(self, reason_code: str, detail: str):
        super().__init__(detail)
        self.reason_code = reason_code
        self.detail = detail


@dataclass(frozen=True)
class QualityGuardReport:
    structure_complete: bool
    incomplete_structure: bool
    deliverable: bool
    structure_evidence_source: str
    structure_evidence_complete: bool
    missing_mandatory_regions: list[str]
    missing_required_slots: list[str]
    region_render_status: dict[str, dict[str, object]]
    slot_binding_status: dict[str, object]
    region_completeness_status: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "structure_complete": self.structure_complete,
            "incomplete_structure": self.incomplete_structure,
            "deliverable": self.deliverable,
            "structure_evidence_source": self.structure_evidence_source,
            "structure_evidence_complete": self.structure_evidence_complete,
            "missing_mandatory_regions": list(self.missing_mandatory_regions),
            "missing_required_slots": list(self.missing_required_slots),
            "region_render_status": self.region_render_status,
            "slot_binding_status": self.slot_binding_status,
            "region_completeness_status": self.region_completeness_status,
        }


def run_preflight_guard(template: TemplateSpec, spec: PosterSpec) -> None:
    try:
        metadata = validate_template_registration(template)
        resolve_family_definition(metadata.template_family)
    except TemplateRegistryError as exc:
        raise QualityGuardError("invalid_template_contract", str(exc)) from exc

    if not spec.product_image or not (spec.product_image.url or "").strip():
        raise QualityGuardError(
            "missing_product_image",
            "product_image is required for deliverable poster generation",
        )

    slot_inputs = _build_preflight_slot_inputs(spec)
    # Resolve the effective bottom mode so mode-specific rules apply correctly.
    # gallery_only mode has no title band by design; title is not required.
    requested_mode = spec.bottom_mode or (template.behavior_modes.bottom_mode if template else None)
    title_required = requested_mode != "gallery_only"
    required_issues = []
    if not slot_inputs["product_image"]:
        required_issues.append("product_image_slot")
    if title_required and not slot_inputs["title"]:
        required_issues.append("title_slot")

    if required_issues:
        raise QualityGuardError(
            "missing_required_input",
            "required inputs are missing: " + ", ".join(required_issues),
        )


def evaluate_deliverability(
    *,
    template: TemplateSpec,
    spec: PosterSpec,
    assets: ResolvedAssets,
    layer_render_status: dict[str, dict[str, object]],
    region_render_status: dict[str, dict[str, object]],
    structure_evidence_source: str,
    structure_evidence_complete: bool,
    binding_inputs: Optional[dict[str, Any]] = None,
) -> QualityGuardReport:
    metadata = resolve_template_metadata(template.template_id)
    binding_inputs = binding_inputs or {}
    slot_binding_status = evaluate_slot_bindings(
        metadata,
        template,
        spec,
        assets,
        binding_inputs=binding_inputs,
    ).to_dict()
    region_completeness_status = evaluate_region_completeness(
        metadata,
        layer_status=layer_render_status,
        region_status=region_render_status,
        binding_inputs=binding_inputs or {},
    ).to_dict()

    missing_required_slots = sorted(slot_binding_status.get("missing_required_slots") or [])
    missing_mandatory_regions = sorted(region_completeness_status.get("missing_mandatory_regions") or [])
    structure_complete = (
        structure_evidence_complete
        and not missing_required_slots
        and not missing_mandatory_regions
    )
    incomplete_structure = not structure_complete
    deliverable = structure_complete and structure_evidence_complete and bool(
        region_completeness_status.get("family_minimum_region_complete", False)
    )

    return QualityGuardReport(
        structure_complete=structure_complete,
        incomplete_structure=incomplete_structure,
        deliverable=deliverable,
        structure_evidence_source=structure_evidence_source,
        structure_evidence_complete=structure_evidence_complete,
        missing_mandatory_regions=missing_mandatory_regions,
        missing_required_slots=missing_required_slots,
        region_render_status=region_render_status,
        slot_binding_status=slot_binding_status,
        region_completeness_status=region_completeness_status,
    )


def _build_preflight_slot_inputs(spec: PosterSpec) -> dict[str, object]:
    return {
        "product_image": bool(spec.product_image and (spec.product_image.url or "").strip()),
        "title": bool(spec.title),
    }


def assert_relaxation_non_geometric(
    baseline_geometry: dict,
    relaxed_geometry: dict,
    *,
    preset_id: str,
) -> dict[str, object]:
    """Prove a relaxation preset is non-geometric by differencing geometry evidence.

    Compares the ``region_bounds`` and ``slot_bounds`` (the {x,y,w,h} maps emitted
    by both Family A and Template B geometry evidence) of a baseline render against
    a relaxed render. Any difference means the preset moved a region/slot boundary,
    which is a contract violation -> :class:`QualityGuardError`. Returns a small
    proof payload on success (suitable for the manifest relaxation report).
    """
    diffs: list[str] = []
    for key in ("region_bounds", "slot_bounds"):
        base = baseline_geometry.get(key, {}) or {}
        relaxed = relaxed_geometry.get(key, {}) or {}
        for name in sorted(set(base) | set(relaxed)):
            if base.get(name) != relaxed.get(name):
                diffs.append(f"{key}.{name}: {base.get(name)!r} != {relaxed.get(name)!r}")
    if diffs:
        raise QualityGuardError(
            "relaxation_geometry_drift",
            f"relaxation preset {preset_id!r} changed geometry: " + "; ".join(diffs),
        )
    return {
        "preset": preset_id,
        "geometry_invariant": True,
        "region_bounds_match": True,
        "slot_bounds_match": True,
    }
