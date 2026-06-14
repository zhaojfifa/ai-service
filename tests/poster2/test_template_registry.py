from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.poster2.contracts import TemplateSpec
from app.services.poster2.pipeline import load_template
from app.services.poster2.template_registry import (
    FAMILY_A_CAMPAIGN_EXPLAINER,
    FAMILY_B_PRODUCT_SHEET_STORY,
    TemplateRegistryError,
    get_family_registry,
    get_template_registry,
    resolve_family_definition,
    resolve_template_metadata,
    validate_template_registration,
)


def _load_smoke_fixture() -> dict:
    path = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "family_a_registry_smoke.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _load_template_spec() -> TemplateSpec:
    path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "templates"
        / "specs"
        / "template_dual_v2.json"
    )
    return TemplateSpec.from_json(path)


def test_family_registry_exposes_a_and_b_definitions():
    registry = get_family_registry()
    assert FAMILY_A_CAMPAIGN_EXPLAINER in registry
    assert FAMILY_B_PRODUCT_SHEET_STORY in registry
    assert registry[FAMILY_A_CAMPAIGN_EXPLAINER].default_preferred_renderer == "puppeteer"
    assert registry[FAMILY_B_PRODUCT_SHEET_STORY].default_fallback_renderer == "pillow"


def test_resolve_template_metadata_for_family_a_smoke_fixture():
    fixture = _load_smoke_fixture()
    metadata = resolve_template_metadata(fixture["template_id"])
    assert metadata.template_family == fixture["expected_family"]
    assert metadata.family_mode == fixture["expected_family_mode"]
    assert metadata.preferred_renderer == fixture["expected_preferred_renderer"]
    assert metadata.fallback_renderer == fixture["expected_fallback_renderer"]
    assert list(metadata.minimum_deliverable_regions) == fixture["expected_minimum_deliverable_regions"]


def test_validate_template_registration_accepts_shipped_family_a_template():
    template = _load_template_spec()
    metadata = validate_template_registration(template)
    family = resolve_family_definition(metadata.template_family)
    assert metadata.template_id == "template_dual_v2"
    assert family.family_id == FAMILY_A_CAMPAIGN_EXPLAINER
    assert family.display_name == "Family A: Campaign Explainer"


def test_load_template_uses_registry_validation():
    template = load_template("template_dual_v2")
    metadata = resolve_template_metadata(template.template_id)
    assert template.version == metadata.template_version


def test_resolve_template_metadata_rejects_unknown_template():
    with pytest.raises(TemplateRegistryError):
        resolve_template_metadata("template_missing_v1")


def test_validate_template_registration_rejects_version_mismatch():
    template = _load_template_spec()
    template.version = "9.9.9"
    with pytest.raises(TemplateRegistryError):
        validate_template_registration(template)


def test_template_registry_snapshot_contains_family_a_template():
    registry = get_template_registry()
    assert set(registry) == {
        "template_dual_v2",
        "template_dual_v2_airy",
        "template_dual_v2_studio",
        "template_product_sheet_v1",
    }
