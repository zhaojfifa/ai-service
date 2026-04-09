from __future__ import annotations

import importlib
import json
from pathlib import Path

from app.services.poster2.skills.registry import (
    get_family_skills,
    get_poster2_skill_registry,
    load_skill_implementation,
)
from app.services.poster2.template_registry import FAMILY_A_CAMPAIGN_EXPLAINER, FAMILY_B_PRODUCT_SHEET_STORY


ROOT = Path(__file__).resolve().parents[3]


def _load_fixture() -> dict:
    path = ROOT / "tests" / "poster2" / "fixtures" / "skills" / "family_a_skills_registry_v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_family_a_skill_registry_matches_fixture():
    fixture = _load_fixture()
    registry = get_poster2_skill_registry()

    assert {skill.family_id for skill in registry} == {fixture["family_id"]}
    assert {skill.anchor_template_id for skill in registry} == {fixture["anchor_template_id"]}
    assert sorted(skill.layer for skill in registry) == fixture["allowed_layers"]
    assert [
        {"skill_id": skill.skill_id, "layer": skill.layer, "status": skill.status}
        for skill in registry
    ] == fixture["skills"]


def test_family_a_skill_registry_is_family_scoped_only():
    registry = get_poster2_skill_registry()

    assert registry
    assert all(skill.family_id == FAMILY_A_CAMPAIGN_EXPLAINER for skill in registry)
    assert all(skill.anchor_template_id == "template_dual_v2" for skill in registry)
    assert all("template_product_sheet_v1" not in skill.notes for skill in registry)
    assert FAMILY_B_PRODUCT_SHEET_STORY not in {skill.family_id for skill in registry}


def test_skill_storage_paths_exist_and_are_formal():
    registry = get_poster2_skill_registry()

    assert (ROOT / "app" / "services" / "poster2" / "skills" / "structure").is_dir()
    assert (ROOT / "app" / "services" / "poster2" / "skills" / "control").is_dir()
    assert (ROOT / "app" / "services" / "poster2" / "skills" / "beautification").is_dir()
    assert (ROOT / "app" / "services" / "poster2" / "skills" / "evidence").is_dir()
    assert (ROOT / "tests" / "poster2" / "skills").is_dir()
    assert (ROOT / "tests" / "poster2" / "fixtures" / "skills").is_dir()

    for skill in registry:
        assert (ROOT / skill.doc_path).exists()
        assert (ROOT / skill.fixtures_path).exists()
        assert (ROOT / skill.tests_path).is_dir()


def test_get_family_skills_returns_registered_family_a_only():
    family_skills = get_family_skills(FAMILY_A_CAMPAIGN_EXPLAINER)

    assert family_skills == get_poster2_skill_registry()
    assert get_family_skills(FAMILY_B_PRODUCT_SHEET_STORY) == ()


def test_registry_entries_resolve_to_callable_implementations():
    for skill in get_poster2_skill_registry():
        module = importlib.import_module(skill.entry_module)
        implementation = load_skill_implementation(skill.skill_id)

        assert hasattr(module, skill.entry_symbol)
        assert callable(implementation)
