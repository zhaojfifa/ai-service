from __future__ import annotations

import asyncio
import json
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from PIL import Image as PILImage

from app.services.poster2.asset_loader import AssetLoader
from app.services.poster2.background import BackgroundResult, FireflyBackgroundService
from app.services.poster2.composer import Composer
from app.services.poster2.contracts import AssetRef, PosterSpec, ResolvedAssets, StyleSpec, TemplateSpec
from app.services.poster2.pipeline import PosterPipeline
from app.services.poster2.renderer import LayoutRenderer
from app.services.poster2.slot_contracts import (
    evaluate_slot_bindings,
    resolve_slot_contracts,
    resolve_slot_contracts_for_template,
)
from app.services.poster2.template_registry import (
    FAMILY_A_CAMPAIGN_EXPLAINER,
    FAMILY_B_PRODUCT_SHEET_STORY,
    TemplateMetadata,
    resolve_template_metadata,
)


def _load_template() -> TemplateSpec:
    path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "templates"
        / "specs"
        / "template_dual_v2.json"
    )
    return TemplateSpec.from_json(path)


def _make_spec(**overrides) -> PosterSpec:
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


def _make_assets(
    *,
    with_logo: bool = False,
    gallery_count: int = 0,
    with_scenario: bool = False,
) -> ResolvedAssets:
    product = PILImage.new("RGBA", (400, 600), (200, 100, 50, 255))
    logo = PILImage.new("RGBA", (120, 60), (255, 255, 255, 255)) if with_logo else None
    scenario = PILImage.new("RGBA", (288, 520), (120, 160, 200, 255)) if with_scenario else None
    gallery = [
        PILImage.new("RGBA", (196, 72), (20 + idx, 40 + idx, 60 + idx, 255))
        for idx in range(gallery_count)
    ]
    return ResolvedAssets(product=product, logo=logo, scenario=scenario, gallery=gallery)


def test_family_a_slot_contracts_resolve_expected_required_slots():
    contracts = resolve_slot_contracts_for_template("template_dual_v2", template=_load_template())
    assert contracts.template_family == FAMILY_A_CAMPAIGN_EXPLAINER
    assert contracts.slots["product_image_slot"].required is True
    assert contracts.slots["title_slot"].required is True
    assert contracts.slots["gallery_item_slot[]"].count_max == 4
    assert contracts.slots["feature_item_slot[]"].is_array is True


def test_family_a_slot_binding_report_passes_required_slots_and_collapses_optional():
    metadata = resolve_template_metadata("template_dual_v2")
    report = evaluate_slot_bindings(
        metadata,
        _load_template(),
        _make_spec(subtitle="", features=()),
        _make_assets(),
    )
    assert "product_image_slot" in report.rendered_required_slots
    assert "title_slot" in report.rendered_required_slots
    assert "subtitle_slot" in report.collapsed_optional_slots
    assert "feature_item_slot[]" in report.collapsed_optional_slots
    assert report.missing_required_slots == []


def test_family_a_slot_binding_report_surfaces_missing_required_slots():
    metadata = resolve_template_metadata("template_dual_v2")
    assets = ResolvedAssets(product=None)  # type: ignore[arg-type]
    report = evaluate_slot_bindings(
        metadata,
        _load_template(),
        _make_spec(title=""),
        assets,
    )
    assert "product_image_slot" in report.missing_required_slots
    assert "title_slot" in report.missing_required_slots
    assert "product_region fails when product_image is missing" in report.slot_violation_reasons["product_image_slot"]
    assert "title_band_region fails when title is missing" in report.slot_violation_reasons["title_slot"]


def test_family_b_slot_binding_report_surfaces_required_and_information_core_failures():
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
    template = _load_template()
    spec = _make_spec(brand_name="")
    assets = _make_assets()
    report = evaluate_slot_bindings(
        metadata,
        template,
        spec,
        assets,
        binding_inputs={"spec_items": [], "copy_text": ""},
    )
    assert "brand_text_slot" in report.missing_required_slots
    assert "family_b_information_core" in report.slot_violation_reasons


def test_family_b_slot_binding_report_accepts_required_slots_and_optional_arrays():
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
    template = _load_template()
    spec = _make_spec()
    assets = _make_assets()
    report = evaluate_slot_bindings(
        metadata,
        template,
        spec,
        assets,
        binding_inputs={
            "spec_items": ["容量 2L", "功率 800W"],
            "supporting_images": ["img1", "img2"],
            "copy_text": "",
            "cta_text": "",
        },
    )
    assert "brand_text_slot" in report.rendered_required_slots
    assert "product_image_slot" in report.rendered_required_slots
    assert "cta_slot" in report.collapsed_optional_slots
    assert "family_b_information_core" not in report.slot_violation_reasons


def test_pipeline_metadata_includes_slot_binding_status():
    template = _load_template()
    spec = _make_spec(subtitle="", features=())
    bg_service = MagicMock(spec=FireflyBackgroundService)
    bg_service.generate = AsyncMock(
        return_value=BackgroundResult(
            url="https://r2.example.com/bg.png",
            key="poster2/bg/test_42.png",
            prompt_used="studio background, no text, no logo",
            seed_used=42,
            model="firefly-v3",
            width=1024,
            height=1024,
        )
    )
    loader = MagicMock(spec=AssetLoader)
    loader.load = AsyncMock(return_value=_make_assets())
    loader.load_url = AsyncMock(return_value=PILImage.new("RGB", (1024, 1024), (80, 80, 80)))
    captured: dict[str, bytes] = {}
    urls = iter([
        "https://r2.example.com/fg.png",
        "https://r2.example.com/product-material.png",
        "https://r2.example.com/final.png",
        "https://r2.example.com/renderer-metadata.json",
    ])

    def fake_put(key, data, **kwargs):
        captured[key] = data
        return next(urls)

    pipeline = PosterPipeline(
        background_svc=bg_service,
        renderer=LayoutRenderer(),
        composer=Composer(),
        asset_loader=loader,
        put_bytes_fn=fake_put,
    )
    asyncio.run(pipeline.run(spec, template))
    metadata_key = next(key for key in captured if key.startswith("poster2/debug/metadata/"))
    payload = json.loads(captured[metadata_key].decode("utf-8"))
    assert "slot_binding_status" in payload
    status = payload["slot_binding_status"]
    assert "rendered_required_slots" in status
    assert "missing_required_slots" in status
    assert "collapsed_optional_slots" in status
    assert "slot_violation_reasons" in status
