from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.poster2.region_matrix import (
    evaluate_region_completeness,
    RegionMatrixResolverError,
    resolve_region_matrix,
    resolve_region_matrix_for_template,
)
from app.services.poster2.template_registry import (
    FAMILY_A_CAMPAIGN_EXPLAINER,
    FAMILY_B_PRODUCT_SHEET_STORY,
    TemplateMetadata,
    resolve_template_metadata,
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


def test_family_a_region_completeness_passes_when_mandatory_regions_render():
    metadata = resolve_template_metadata("template_dual_v2")
    report = evaluate_region_completeness(
        metadata,
        layer_status={
            "title_layer": {"count": 1},
            "bottom_gallery_items_layer": {"count": 0},
        },
        region_status={
            "header_region": {"rendered": True},
            "scenario_region": {"rendered": False},
            "product_region": {"rendered": True},
            "feature_region": {"rendered": False},
            "bottom_region": {"rendered": False},
        },
    )
    assert report.family_minimum_region_complete is True
    assert report.missing_mandatory_regions == []
    assert "header_region" in report.rendered_regions
    assert "scenario_region" in report.collapsed_regions


def test_family_a_region_completeness_fails_when_title_band_missing():
    metadata = resolve_template_metadata("template_dual_v2")
    report = evaluate_region_completeness(
        metadata,
        layer_status={
            "title_layer": {"count": 0},
            "bottom_gallery_items_layer": {"count": 0},
        },
        region_status={
            "header_region": {"rendered": True},
            "scenario_region": {"rendered": False},
            "product_region": {"rendered": True},
            "feature_region": {"rendered": False},
            "bottom_region": {"rendered": False},
        },
    )
    assert report.family_minimum_region_complete is False
    assert "title_band_region" in report.missing_mandatory_regions
    assert "mandatory_region_missing" in report.region_violation_reasons["title_band_region"]


def test_family_b_region_completeness_passes_when_mandatory_regions_render():
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
    report = evaluate_region_completeness(
        metadata,
        binding_inputs={
            "brand_name": "Brand",
            "hero_product_present": True,
        },
    )
    assert report.family_minimum_region_complete is True
    assert report.missing_mandatory_regions == []


def test_family_b_region_completeness_fails_when_hero_product_missing():
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
    report = evaluate_region_completeness(
        metadata,
        binding_inputs={
            "brand_name": "Brand",
            "hero_product_present": False,
        },
    )
    assert report.family_minimum_region_complete is False
    assert "hero_product_region" in report.missing_mandatory_regions
