from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal

from app.services.poster2.template_registry import FAMILY_A_CAMPAIGN_EXPLAINER

SkillLayer = Literal["structure", "control", "beautification", "evidence"]
SkillStatus = Literal["registered", "anchored", "frozen"]


@dataclass(frozen=True)
class Poster2SkillRegistration:
    skill_id: str
    display_name: str
    family_id: str
    layer: SkillLayer
    anchor_template_id: str
    status: SkillStatus
    entry_module: str
    doc_path: str
    tests_path: str
    fixtures_path: str
    acceptance_gate: str
    forbidden_mutations: tuple[str, ...]
    depends_on: tuple[str, ...] = ()
    notes: str = ""

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


_FAMILY_A_ANCHORED_SKILLS: tuple[Poster2SkillRegistration, ...] = (
    Poster2SkillRegistration(
        skill_id="family_a_structure_surface_v1",
        display_name="Family A Structure Surface v1",
        family_id=FAMILY_A_CAMPAIGN_EXPLAINER,
        layer="structure",
        anchor_template_id="template_dual_v2",
        status="anchored",
        entry_module="app.services.poster2.family_a_runtime",
        doc_path="docs/poster2/skill_rules_and_storage_v1.md",
        tests_path="tests/poster2/skills",
        fixtures_path="tests/poster2/fixtures/skills/family_a_skills_registry_v1.json",
        acceptance_gate="family_a_rebaseline_and_isolation_accepted",
        forbidden_mutations=(
            "no_geometry_changes",
            "no_ownership_changes",
            "no_cross_family_structure_merge",
        ),
        notes="Anchors Family A region order, slot contract, and structure surface entry.",
    ),
    Poster2SkillRegistration(
        skill_id="family_a_control_surface_v1",
        display_name="Family A Control Surface v1",
        family_id=FAMILY_A_CAMPAIGN_EXPLAINER,
        layer="control",
        anchor_template_id="template_dual_v2",
        status="anchored",
        entry_module="app.services.poster2.family_a_runtime",
        doc_path="docs/poster2/skill_rules_and_storage_v1.md",
        tests_path="tests/poster2/skills",
        fixtures_path="tests/poster2/fixtures/skills/family_a_skills_registry_v1.json",
        acceptance_gate="family_a_rebaseline_and_isolation_accepted",
        forbidden_mutations=(
            "no_behavior_mode_rewrite",
            "no_count_driven_right_stack_return",
            "no_cross_family_control_merge",
        ),
        depends_on=("family_a_structure_surface_v1",),
        notes="Anchors Family A header/hero/feature/bottom/gallery/product-layout mode surfaces.",
    ),
    Poster2SkillRegistration(
        skill_id="family_a_beautification_freeze_pack_v1",
        display_name="Family A Beautification Freeze Pack v1",
        family_id=FAMILY_A_CAMPAIGN_EXPLAINER,
        layer="beautification",
        anchor_template_id="template_dual_v2",
        status="frozen",
        entry_module="app.services.poster2.renderer",
        doc_path="docs/poster2/template_a_beautification_freeze_status_v1.md",
        tests_path="tests/poster2/skills",
        fixtures_path="tests/poster2/fixtures/skills/family_a_skills_registry_v1.json",
        acceptance_gate="family_a_freeze_and_puppeteer_acceptance_complete",
        forbidden_mutations=(
            "no_geometry_changes",
            "no_ownership_changes",
            "no_behavior_changes",
        ),
        depends_on=("family_a_structure_surface_v1", "family_a_control_surface_v1"),
        notes="Bounded Family A visual freeze pack only; renderer consumes pre-accepted truth.",
    ),
    Poster2SkillRegistration(
        skill_id="family_a_evidence_surface_v1",
        display_name="Family A Evidence Surface v1",
        family_id=FAMILY_A_CAMPAIGN_EXPLAINER,
        layer="evidence",
        anchor_template_id="template_dual_v2",
        status="anchored",
        entry_module="app.services.poster2.family_a_runtime",
        doc_path="docs/poster2/family_isolation_rules_v1.md",
        tests_path="tests/poster2/skills",
        fixtures_path="tests/poster2/fixtures/skills/family_a_skills_registry_v1.json",
        acceptance_gate="family_a_rebaseline_and_isolation_accepted",
        forbidden_mutations=(
            "no_cross_family_evidence_schema",
            "no_dom_only_truth",
            "no_renderer_defined_contract_truth",
        ),
        depends_on=("family_a_structure_surface_v1", "family_a_control_surface_v1"),
        notes="Anchors Family A visible-truth, bounds, and diagnostics whitelist behavior.",
    ),
)


def get_poster2_skill_registry() -> tuple[Poster2SkillRegistration, ...]:
    return _FAMILY_A_ANCHORED_SKILLS


def get_family_skills(family_id: str) -> tuple[Poster2SkillRegistration, ...]:
    return tuple(skill for skill in _FAMILY_A_ANCHORED_SKILLS if skill.family_id == family_id)


def get_skill_registry_payload() -> list[dict[str, object]]:
    return [skill.as_dict() for skill in _FAMILY_A_ANCHORED_SKILLS]
