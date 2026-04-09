from __future__ import annotations

from ...family_a_runtime import (
    FAMILY_A_CANONICAL_SAMPLE_VARIANTS,
    FAMILY_A_FORBIDDEN_TEMPLATE_B_KEYS,
    FAMILY_A_VISIBLE_TRUTH_KEYS,
    filter_family_a_visible_truth_evidence,
)
from ...template_registry import FAMILY_A_CAMPAIGN_EXPLAINER

SKILL_ID = "family_a_evidence_surface_v1"


def build_evidence_surface(visible_truth_evidence: dict[str, object]) -> dict[str, object]:
    return {
        "family_id": FAMILY_A_CAMPAIGN_EXPLAINER,
        "accepted_visible_truth_keys": get_visible_truth_keys(),
        "forbidden_cross_family_keys": get_forbidden_cross_family_keys(),
        "canonical_sample_variants": get_canonical_sample_variants(),
        "filtered_visible_truth_evidence": filter_visible_truth_evidence(visible_truth_evidence),
    }


def filter_visible_truth_evidence(visible_truth_evidence: dict[str, object]) -> dict[str, object]:
    return filter_family_a_visible_truth_evidence(visible_truth_evidence)


def get_visible_truth_keys() -> list[str]:
    return sorted(FAMILY_A_VISIBLE_TRUTH_KEYS)


def get_forbidden_cross_family_keys() -> list[str]:
    return sorted(FAMILY_A_FORBIDDEN_TEMPLATE_B_KEYS)


def get_canonical_sample_variants() -> list[dict[str, object]]:
    return [dict(sample) for sample in FAMILY_A_CANONICAL_SAMPLE_VARIANTS]
