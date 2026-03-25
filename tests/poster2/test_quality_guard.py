from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image as PILImage

from app.services.poster2.contracts import AssetRef, PosterSpec, ResolvedAssets, StyleSpec, TemplateSpec
from app.services.poster2 import quality_guard as quality_guard_module
from app.services.poster2.quality_guard import (
    QualityGuardError,
    evaluate_deliverability,
    run_preflight_guard,
)
from app.services.poster2.template_registry import FAMILY_B_PRODUCT_SHEET_STORY, TemplateMetadata


def _load_template() -> TemplateSpec:
    p = (
        Path(__file__).resolve().parents[2]
        / "app" / "templates" / "specs" / "template_dual_v2.json"
    )
    return TemplateSpec.from_json(p)


def _family_a_spec(**overrides) -> PosterSpec:
    defaults = dict(
        brand_name="厨厨房",
        agent_name="智能顾问",
        title="测试标题",
        subtitle="测试副标题",
        features=("特性A", "特性B"),
        product_image=AssetRef(url="mock://product"),
        style=StyleSpec(seed=42),
    )
    defaults.update(overrides)
    return PosterSpec(**defaults)


def _family_a_assets() -> ResolvedAssets:
    return ResolvedAssets(product=PILImage.new("RGBA", (400, 600), (255, 0, 0, 255)))


def test_preflight_rejects_missing_required_input():
    template = _load_template()
    with pytest.raises(QualityGuardError) as excinfo:
        run_preflight_guard(template, _family_a_spec(title=""))
    assert excinfo.value.reason_code == "missing_required_input"


def test_family_a_deliverability_passes_when_required_structure_is_present():
    template = _load_template()
    report = evaluate_deliverability(
        template=template,
        spec=_family_a_spec(),
        assets=_family_a_assets(),
        layer_render_status={
            "title_layer": {"count": 1},
            "bottom_gallery_items_layer": {"count": 0},
        },
        region_render_status={
            "header_region": {"rendered": True},
            "scenario_region": {"rendered": False},
            "product_region": {"rendered": True},
            "feature_region": {"rendered": True},
            "bottom_region": {"rendered": True},
        },
        structure_evidence_source="renderer_derived",
        structure_evidence_complete=True,
    )
    assert report.structure_complete is True
    assert report.incomplete_structure is False
    assert report.deliverable is True
    assert report.structure_evidence_source == "renderer_derived"
    assert report.structure_evidence_complete is True


def test_family_b_deliverability_passes_when_minimum_regions_and_info_core_exist(monkeypatch):
    metadata = TemplateMetadata(
        template_id="family_b_template_v1",
        template_version="1.0.0",
        template_family=FAMILY_B_PRODUCT_SHEET_STORY,
        family_mode="product_sheet_core",
        preferred_renderer="puppeteer",
        fallback_renderer="pillow",
        allowed_fallback_reason_codes=("puppeteer_timeout",),
        minimum_deliverable_regions=("brand_banner_region", "hero_product_region"),
    )
    template = _load_template()
    template.template_id = metadata.template_id
    template.version = metadata.template_version
    monkeypatch.setattr(quality_guard_module, "resolve_template_metadata", lambda _template_id: metadata)
    report = evaluate_deliverability(
        template=template,
        spec=_family_a_spec(),
        assets=_family_a_assets(),
        layer_render_status={},
        region_render_status={},
        binding_inputs={
            "brand_name": "Brand",
            "hero_product_present": True,
            "spec_items": ["容量 2L"],
            "copy_text": "",
            "footer_brand_text": "",
            "cta_text": "",
        },
        structure_evidence_source="renderer_derived",
        structure_evidence_complete=True,
    )
    assert report.deliverable is True
    assert report.incomplete_structure is False


def test_family_b_deliverability_fails_when_minimum_regions_are_missing(monkeypatch):
    metadata = TemplateMetadata(
        template_id="family_b_template_v1",
        template_version="1.0.0",
        template_family=FAMILY_B_PRODUCT_SHEET_STORY,
        family_mode="product_sheet_core",
        preferred_renderer="puppeteer",
        fallback_renderer="pillow",
        allowed_fallback_reason_codes=("puppeteer_timeout",),
        minimum_deliverable_regions=("brand_banner_region", "hero_product_region"),
    )
    template = _load_template()
    template.template_id = metadata.template_id
    template.version = metadata.template_version
    monkeypatch.setattr(quality_guard_module, "resolve_template_metadata", lambda _template_id: metadata)
    report = evaluate_deliverability(
        template=template,
        spec=_family_a_spec(),
        assets=_family_a_assets(),
        layer_render_status={},
        region_render_status={},
        binding_inputs={
            "brand_name": "",
            "hero_product_present": False,
            "spec_items": [],
            "copy_text": "",
        },
        structure_evidence_source="pipeline_inferred",
        structure_evidence_complete=False,
    )
    assert report.structure_complete is False
    assert report.incomplete_structure is True
    assert report.deliverable is False
    assert "brand_banner_region" in report.missing_mandatory_regions
    assert report.structure_evidence_source == "pipeline_inferred"
    assert report.structure_evidence_complete is False
