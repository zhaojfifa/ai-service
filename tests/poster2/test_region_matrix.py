from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.poster2.region_matrix import (
    RegionMatrixResolverError,
    resolve_region_matrix,
    resolve_region_matrix_for_template,
)
from app.services.poster2.template_registry import (
    FAMILY_A_CAMPAIGN_EXPLAINER,
    FAMILY_B_PRODUCT_SHEET_STORY,
    TemplateMetadata,
)


def _load_family_a_smoke_fixture() -> dict:
    path = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "family_a_region_matrix_smoke.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_family_a_region_matrix_smoke_fixture_resolves_expected_regions():
    fixture = _load_family_a_smoke_fixture()
    resolved = resolve_region_matrix_for_template(fixture["template_id"])
    assert resolved.template_family == fixture["expected_family"]
    assert list(resolved.region_order) == fixture["expected_region_order"]
    assert list(resolved.mandatory_regions) == fixture["expected_mandatory_regions"]
    assert list(resolved.collapsible_regions) == fixture["expected_collapsible_regions"]


def test_family_a_region_matrix_uses_slot_spec_bounds():
    resolved = resolve_region_matrix_for_template("template_dual_v2")
    assert resolved.regions["header_region"].x == 72
    assert resolved.regions["scenario_region"].w == 288
    assert resolved.regions["product_region"].h == 520
    assert resolved.regions["title_band_region"].y == 728
    assert resolved.regions["gallery_strip_region"].h == 72


def test_family_a_region_matrix_marks_expected_structural_semantics():
    resolved = resolve_region_matrix_for_template("template_dual_v2")
    assert resolved.template_family == FAMILY_A_CAMPAIGN_EXPLAINER
    assert resolved.regions["header_region"].mandatory is True
    assert resolved.regions["scenario_region"].collapsible is True
    assert resolved.regions["product_region"].minimum_success_conditions == (
        "product_image_slot must render once",
        "product image must not distort",
    )
    assert "ghost connectors" in resolved.regions["feature_region"].replacement_rules[0]
    assert "title_band_region" in resolved.regions["gallery_strip_region"].replacement_rules[0]


def test_family_b_region_matrix_resolves_family_level_baseline():
    metadata = TemplateMetadata(
        template_id="template_sheet_story_v1",
        template_version="1.0.0",
        template_family=FAMILY_B_PRODUCT_SHEET_STORY,
        family_mode="product_sheet_simple",
        preferred_renderer="puppeteer",
        fallback_renderer="pillow",
        allowed_fallback_reason_codes=("puppeteer_timeout",),
        minimum_deliverable_regions=("brand_banner_region", "hero_product_region"),
    )
    resolved = resolve_region_matrix(metadata)
    assert resolved.mandatory_regions == ("brand_banner_region", "hero_product_region")
    assert resolved.regions["cta_region"].collapsible is True
    assert resolved.regions["copy_region"].status == "conditional_mandatory"


def test_region_matrix_rejects_unknown_template_id():
    with pytest.raises(Exception):
        resolve_region_matrix_for_template("template_unknown_v1")


def test_region_matrix_rejects_missing_slot_spec_for_family_a():
    metadata = TemplateMetadata(
        template_id="template_family_a_missing_spec",
        template_version="1.0.0",
        template_family=FAMILY_A_CAMPAIGN_EXPLAINER,
        family_mode="campaign_explainer_core",
        preferred_renderer="puppeteer",
        fallback_renderer="pillow",
        allowed_fallback_reason_codes=("puppeteer_timeout",),
        minimum_deliverable_regions=("header_region", "product_region", "title_band_region"),
    )
    with pytest.raises(RegionMatrixResolverError):
        resolve_region_matrix(metadata)
