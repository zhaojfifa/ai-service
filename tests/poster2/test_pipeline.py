"""
Integration tests for PosterPipeline — mocked I/O, real Pillow rendering.

All external dependencies are mocked:
  - FireflyBackgroundService (returns a solid-color background PNG)
  - AssetLoader (returns in-memory PIL Images)
  - r2_client.put_bytes (returns a fake URL)

Tests verify:
  1. Pipeline returns a valid RenderManifest.
  2. final_url and foreground_url are set.
  3. final_hash changes when spec changes (reproducibility).
  4. Missing product_image raises ValueError.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image as PILImage

from app.services.poster2.asset_loader import AssetLoader
from app.services.poster2.background import BackgroundResult, FireflyBackgroundService
from app.services.poster2.composer import Composer
from app.services.poster2.contracts import (
    AssetRef,
    PosterSpec,
    ResolvedAssets,
    StyleSpec,
    TemplateSpec,
)
from app.services.poster2.pipeline import PosterPipeline
from app.services.poster2.renderer import ForegroundResult, LayoutRenderer
from app.services.poster2.renderer_routing import RendererRoutingError


# ── Helpers ───────────────────────────────────────────────────────────────────

def _solid_png(w: int = 1024, h: int = 1024, color=(80, 80, 80)) -> bytes:
    img = PILImage.new("RGB", (w, h), color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


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


def _make_assets() -> ResolvedAssets:
    product = PILImage.new("RGBA", (400, 600), (200, 100, 50, 255))
    return ResolvedAssets(product=product)


def _load_template() -> TemplateSpec:
    p = (
        Path(__file__).resolve().parents[2]
        / "app" / "templates" / "specs" / "template_dual_v2.json"
    )
    return TemplateSpec.from_json(p)


def _load_template_with_feature_mode(feature_mode: str) -> TemplateSpec:
    t = _load_template()
    t.behavior_modes = replace(t.behavior_modes, feature_mode=feature_mode)
    return t


# ── Mock factories ─────────────────────────────────────────────────────────────

def _mock_bg_service(seed: int = 42) -> FireflyBackgroundService:
    svc = MagicMock(spec=FireflyBackgroundService)
    svc.generate = AsyncMock(return_value=BackgroundResult(
        url="https://r2.example.com/bg.png",
        key="poster2/bg/test_42.png",
        prompt_used="studio background, no text, no logo",
        seed_used=seed,
        model="firefly-v3",
        width=1024,
        height=1024,
    ))
    return svc


def _mock_loader(assets: ResolvedAssets | None = None) -> AssetLoader:
    loader = MagicMock(spec=AssetLoader)
    _assets = assets or _make_assets()
    loader.load = AsyncMock(return_value=_assets)

    bg_img = PILImage.new("RGB", (1024, 1024), (80, 80, 80))
    loader.load_url = AsyncMock(return_value=bg_img)
    return loader


def _mock_r2_put(url: str = "https://r2.example.com/final.png"):
    return MagicMock(return_value=url)


class _FakeDegradedRenderer:
    async def render(self, spec, poster, assets):
        image = PILImage.new("RGBA", (spec.canvas_w, spec.canvas_h), (0, 0, 0, 0))
        return ForegroundResult(
            image=image,
            png_bytes=_solid_png(),
            sha256="c" * 64,
            render_engine_used="pillow",
            foreground_renderer="poster2.pillow_layout",
            template_contract_version=spec.contract_version,
            degraded=True,
            degraded_reason="puppeteer_timeout",
            fallback_reason_code="puppeteer_timeout",
            fallback_reason_detail="puppeteer timed out",
            fallback_stage="navigation",
            layer_render_status={
                "title_layer": {"count": 1},
                "bottom_gallery_items_layer": {"count": 0},
                "brand_logo_layer": {"rendered": False, "count": 0},
                "brand_text_layer": {"rendered": True, "count": 1},
                "agent_name_text_layer": {"rendered": True, "count": 1},
                "scenario_image_layer": {"rendered": False, "count": 0},
                "product_image_layer": {"rendered": True, "count": 1},
                "feature_callout_layer": {"rendered": True, "count": 2},
            },
            region_render_status={
                "header_region": {"rendered": True, "count": 2},
                "scenario_region": {"rendered": False, "count": 0},
                "product_region": {"rendered": True, "count": 1},
                "feature_region": {"rendered": True, "count": 2},
                "bottom_region": {"rendered": True, "count": 1},
            },
        )


class _FakeDegradedIncompleteRenderer:
    async def render(self, spec, poster, assets):
        image = PILImage.new("RGBA", (spec.canvas_w, spec.canvas_h), (0, 0, 0, 0))
        return ForegroundResult(
            image=image,
            png_bytes=_solid_png(),
            sha256="e" * 64,
            render_engine_used="pillow",
            foreground_renderer="poster2.pillow_layout",
            template_contract_version=spec.contract_version,
            degraded=True,
            degraded_reason="puppeteer_timeout",
            fallback_reason_code="puppeteer_timeout",
            fallback_reason_detail="puppeteer timed out",
            fallback_stage="navigation",
            layer_render_status={
                "title_layer": {"count": 0},
                "bottom_gallery_items_layer": {"count": 0},
            },
            region_render_status={
                "header_region": {"rendered": True, "count": 2},
                "scenario_region": {"rendered": False, "count": 0},
                "product_region": {"rendered": True, "count": 1},
                "feature_region": {"rendered": True, "count": 2},
                "bottom_region": {"rendered": False, "count": 0},
            },
        )


class _FakeIncompleteRenderer:
    async def render(self, spec, poster, assets):
        image = PILImage.new("RGBA", (spec.canvas_w, spec.canvas_h), (0, 0, 0, 0))
        return ForegroundResult(
            image=image,
            png_bytes=_solid_png(),
            sha256="d" * 64,
            render_engine_used="puppeteer",
            foreground_renderer="poster2.puppeteer_structured",
            template_contract_version=spec.contract_version,
            layer_render_status={
                "title_layer": {"count": 0},
                "bottom_gallery_items_layer": {"count": 0},
            },
            region_render_status={
                "header_region": {"rendered": True, "count": 2},
                "scenario_region": {"rendered": False, "count": 0},
                "product_region": {"rendered": True, "count": 1},
                "feature_region": {"rendered": True, "count": 2},
                "bottom_region": {"rendered": False, "count": 0},
            },
        )


class _AsyncPillowRenderer:
    def __init__(self):
        self._renderer = LayoutRenderer()

    async def render(self, spec, poster, assets):
        return self._renderer.render(spec, poster, assets)


class _FakeInferredRenderer:
    async def render(self, spec, poster, assets):
        image = PILImage.new("RGBA", (spec.canvas_w, spec.canvas_h), (0, 0, 0, 0))
        return ForegroundResult(
            image=image,
            png_bytes=_solid_png(),
            sha256="f" * 64,
            render_engine_used="pillow",
            foreground_renderer="poster2.pillow_layout",
            template_contract_version=spec.contract_version,
        )


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestPosterPipelineRun:

    def _run(
        self,
        spec: PosterSpec,
        template: TemplateSpec | None = None,
        product_override: PILImage.Image | None = None,
    ):
        """Run the pipeline with all external I/O mocked."""
        template = template or _load_template()

        # Inject a fake put_bytes to avoid boto3/R2 dependency in tests
        _r2_urls = iter([
            "https://r2.example.com/fg.png",
            "https://r2.example.com/product-material.png",
            "https://r2.example.com/final.png",
            "https://r2.example.com/renderer-metadata.json",
        ])
        fake_put_bytes = MagicMock(side_effect=lambda key, data, **kw: next(_r2_urls))

        assets = _make_assets() if product_override is None else ResolvedAssets(product=product_override)

        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=fake_put_bytes,
        )
        return asyncio.run(pipeline.run(spec, template))

    def test_returns_manifest(self):
        manifest = self._run(_make_spec())
        assert manifest.trace_id
        assert manifest.final_url == "https://r2.example.com/final.png"
        assert manifest.foreground_url == "https://r2.example.com/fg.png"
        assert manifest.background_url == "https://r2.example.com/bg.png"
        assert manifest.debug_artifacts.product_material_layer_url == "https://r2.example.com/product-material.png"
        assert manifest.debug_artifacts.renderer_metadata_url == "https://r2.example.com/renderer-metadata.json"

    def test_manifest_hashes_set(self):
        manifest = self._run(_make_spec())
        assert len(manifest.final_hash) == 64  # SHA256 hex
        assert len(manifest.foreground_hash) == 64

    def test_background_metadata(self):
        manifest = self._run(_make_spec())
        assert manifest.background_seed == 42
        assert manifest.background_model == "firefly-v3"
        assert manifest.template_version == "2.1.4"
        assert manifest.template_contract_version == "poster2.template_dual_v2.v1"
        assert manifest.engine_version == "2.0.0"
        assert manifest.render_engine_used == "pillow"
        assert manifest.renderer_mode == "auto"
        assert manifest.foreground_renderer == "poster2.pillow_layout"
        assert manifest.background_renderer == "firefly-v3"
        assert manifest.debug_artifacts.background_layer_url == "https://r2.example.com/bg.png"
        assert manifest.debug_artifacts.foreground_layer_url == "https://r2.example.com/fg.png"
        assert manifest.debug_artifacts.final_composited_url == "https://r2.example.com/final.png"

    def test_timings_recorded(self):
        manifest = self._run(_make_spec())
        assert "load_and_bg_ms" in manifest.timings_ms
        assert "background_layer_ms" in manifest.timings_ms
        assert "product_material_layer_ms" in manifest.timings_ms
        assert "foreground_structure_layer_ms" in manifest.timings_ms
        assert "text_layer_ms" in manifest.timings_ms
        assert "renderer_ms" in manifest.timings_ms
        assert "compose_ms" in manifest.timings_ms
        assert "total_ms" in manifest.timings_ms

    def test_poster_spec_hash_in_manifest(self):
        manifest = self._run(_make_spec())
        assert manifest.poster_spec_hash  # non-empty

    def test_different_specs_different_fg_hash(self):
        """Different product image → different foreground hash (determinism check).
        Uses product image color difference since CJK text requires font files
        that may not be present in CI.
        """
        template = _load_template()

        red_product = PILImage.new("RGBA", (400, 600), (255, 0, 0, 255))
        blue_product = PILImage.new("RGBA", (400, 600), (0, 0, 255, 255))

        m1 = self._run(
            _make_spec(title="TitleA"),
            template,
            product_override=red_product,
        )
        m2 = self._run(
            _make_spec(title="TitleB"),
            template,
            product_override=blue_product,
        )
        assert m1.foreground_hash != m2.foreground_hash

    def test_same_spec_same_fg_hash(self):
        """Same spec → same foreground hash (reproducibility)."""
        template = _load_template()
        spec = _make_spec()
        m1 = self._run(spec, template)
        m2 = self._run(spec, template)
        assert m1.foreground_hash == m2.foreground_hash

    def test_not_degraded_by_default(self):
        manifest = self._run(_make_spec())
        assert manifest.degraded is False
        assert manifest.degraded_reason is None
        assert manifest.fallback_reason_code is None
        assert manifest.fallback_reason_detail is None
        assert manifest.structure_complete is True
        assert manifest.incomplete_structure is False
        assert manifest.deliverable is True
        assert manifest.structure_evidence_source == "renderer_derived"
        assert manifest.structure_evidence_complete is True

    def test_preflight_failure_rejects_invalid_input_before_rendering(self):
        template = _load_template()
        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(_make_assets()),
            put_bytes_fn=_mock_r2_put(),
        )
        with pytest.raises(ValueError) as excinfo:
            asyncio.run(pipeline.run(_make_spec(title=""), template))
        assert "title must not be empty after normalization" in str(excinfo.value)

    def test_resolved_inputs_in_manifest(self):
        manifest = self._run(_make_spec())
        ri = manifest.resolved_inputs
        assert ri["brand_name"] == "厨厨房"
        assert ri["title"] == "测试标题"

    def test_template_dual_v2_prefers_scenario_image_for_background(self):
        template = _load_template()
        bg_service = _mock_bg_service()
        scenario = PILImage.new("RGBA", (320, 600), (120, 160, 200, 255))
        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            scenario=scenario,
        )
        fake_put_bytes = MagicMock(
            side_effect=[
                "https://r2.example.com/fg.png",
                "https://r2.example.com/product-material.png",
                "https://r2.example.com/final.png",
                "https://r2.example.com/renderer-metadata.json",
            ]
        )
        pipeline = PosterPipeline(
            background_svc=bg_service,
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=fake_put_bytes,
        )

        with patch(
            "app.services.poster2.pipeline.build_template_dual_v2_background",
            new=AsyncMock(
                return_value=BackgroundResult(
                    url="https://r2.example.com/bg-scenario.png",
                    key="poster2/bg/scenario.png",
                    prompt_used="scenario_image_preferred",
                    seed_used=0,
                    model="scenario-image",
                    width=1024,
                    height=1024,
                )
            ),
        ) as scenario_bg:
            manifest = asyncio.run(pipeline.run(_make_spec(), template))

        assert manifest.background_model == "scenario-image"
        assert manifest.background_url == "https://r2.example.com/bg-scenario.png"
        assert bg_service.generate.await_count == 0
        assert scenario_bg.await_count == 1

    def test_renderer_metadata_includes_layer_render_status(self):
        template = _load_template()
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            if key.endswith(".json"):
                return "https://r2.example.com/renderer-metadata.json"
            if "product-material" in key:
                return "https://r2.example.com/product-material.png"
            if "/fg/" in key:
                return "https://r2.example.com/fg.png"
            return "https://r2.example.com/final.png"

        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            scenario=None,
            gallery=[],
        )
        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=fake_put_bytes,
        )

        manifest = asyncio.run(pipeline.run(_make_spec(), template))

        assert manifest.debug_artifacts.renderer_metadata_url == "https://r2.example.com/renderer-metadata.json"
        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        assert metadata["template_behavior"]["behavior_modes"]["hero_mode"] == "scenario_cover_product_contain"
        assert metadata["template_behavior"]["behavior_modes"]["feature_mode"] == "product_anchor_callouts"
        assert metadata["template_behavior"]["behavior_modes"]["product_annotation_mode"] == "product_anchor_callouts"
        assert metadata["template_behavior"]["behavior_modes"]["bottom_mode"] == "title_gallery_split"
        assert metadata["template_behavior"]["behavior_modes"]["bottom_layout_mode"] == "title_gallery_split"
        assert metadata["template_behavior"]["behavior_modes"]["product_geometry_mode"] == "single_primary_v1"
        assert metadata["template_behavior"]["behavior_modes"]["gallery_mode"] == "strip_local_visible_only"
        assert metadata["template_behavior"]["hero_policy"]["scenario_enabled"] is True
        assert metadata["template_behavior"]["hero_policy"]["product_fit"] == "contain"
        assert metadata["template_behavior"]["feature_policy"]["visible_item_count"] == 2
        assert metadata["template_behavior"]["feature_policy"]["connector_policy"] == "product_anchor_leader_line"
        assert metadata["template_behavior"]["bottom_policy"]["title_band_rendered"] is True
        assert metadata["template_behavior"]["bottom_policy"]["gallery_strip_rendered"] is False
        assert metadata["template_behavior"]["template_layout_policy"]["layout_density_mode"] == "balanced"
        assert metadata["template_behavior"]["beauty_tokens"]["shell_surface"] == "glass_light"
        layer_status = metadata["layer_render_status"]
        assert layer_status["brand_logo_layer"]["rendered"] is False
        assert layer_status["brand_logo_layer"]["reason_code"] == "logo_missing"
        assert layer_status["scenario_image_layer"]["rendered"] is False
        assert layer_status["scenario_image_layer"]["reason_code"] == "scenario_missing"
        assert layer_status["scenario_image_layer"]["source_binding"] is None
        assert layer_status["bottom_gallery_items_layer"]["rendered"] is False
        assert layer_status["bottom_gallery_items_layer"]["reason_code"] == "gallery_empty"
        assert layer_status["bottom_gallery_items_layer"]["count"] == 0
        assert layer_status["bottom_gallery_items_layer"]["count_visible"] == 0
        assert layer_status["bottom_gallery_items_layer"]["collapsed"] is True
        assert layer_status["bottom_tagline_layer"]["reason_code"] == "operator_tagline_unbound"
        region_status = metadata["region_render_status"]
        assert region_status["header_region"]["rendered"] is True
        assert region_status["header_region"]["count"] == 2
        assert region_status["scenario_region"]["rendered"] is False
        assert region_status["scenario_region"]["count"] == 0
        assert region_status["product_region"]["rendered"] is True
        assert region_status["product_region"]["count"] == 3
        assert region_status["feature_region"]["rendered"] is False
        assert region_status["feature_region"]["count"] == 0
        assert region_status["title_band_region"]["rendered"] is True
        assert region_status["gallery_strip_region"]["rendered"] is False
        assert region_status["bottom_region"]["collapsed"] is False
        completeness = metadata["region_completeness_status"]
        assert completeness["family_minimum_region_complete"] is True
        assert completeness["missing_mandatory_regions"] == []
        assert "header_region" in completeness["rendered_regions"]
        assert "gallery_strip_region" in completeness["collapsed_regions"]
        assert metadata["structure_complete"] is True
        assert metadata["incomplete_structure"] is False
        assert metadata["deliverable"] is True
        assert metadata["structure_evidence_source"] == "renderer_derived"
        assert metadata["structure_evidence_complete"] is True
        assert metadata["missing_required_slots"] == []
        assert metadata["missing_mandatory_regions"] == []
        geometry = metadata["geometry_evidence"]
        assert geometry["region_bounds"]["header_region"] == {"x": 72, "y": 56, "w": 880, "h": 104}
        assert geometry["region_bounds"]["scenario_region"] == {"x": 96, "y": 188, "w": 288, "h": 520}
        assert geometry["region_bounds"]["bottom_region"] == {"x": 96, "y": 640, "w": 832, "h": 168}
        assert geometry["region_bounds"]["title_band_region"] == {"x": 112, "y": 640, "w": 800, "h": 168}
        assert geometry["region_bounds"]["product_region"] == {"x": 456, "y": 188, "w": 300, "h": 540}
        assert geometry["slot_bounds"]["brand_name_slot"] == {"x": 244, "y": 88, "w": 416, "h": 36}
        assert geometry["slot_bounds"]["agent_name_slot"] == {"x": 684, "y": 96, "w": 228, "h": 18}
        assert geometry["slot_bounds"]["scenario_slot"] == {"x": 96, "y": 188, "w": 288, "h": 520}
        assert geometry["slot_bounds"]["product_slot"] == {"x": 456, "y": 188, "w": 300, "h": 540}
        assert geometry["slot_bounds"]["subtitle_slot"] == {"x": 152, "y": 752, "w": 720, "h": 28}
        assert geometry["visible_item_count"]["header_region"] == 2
        assert geometry["visible_item_count"]["scenario_region"] == 0
        assert geometry["visible_item_count"]["title_band_region"] == 2
        assert geometry["visible_item_count"]["product_region"] == 3
        feature_review = metadata["feature_contract_review"]
        assert feature_review["feature_mode"] == "product_anchor_callouts"
        assert feature_review["responsibility_owner"] == "product_region"
        assert feature_review["delegated_to_product_annotation"] is True
        assert feature_review["requested_feature_items"] == ["特性A", "特性B"]
        assert feature_review["sanitized_feature_items"] == ["特性A", "特性B"]
        assert feature_review["rendered_feature_items"] == []
        assert feature_review["behavior_policy"]["connector_policy"] == "product_anchor_leader_line"
        assert feature_review["behavior_policy"]["text_budget_policy"] == "anchor_fixed_budget"
        assert feature_review["behavior_policy"]["responsibility_policy"] == "delegated_to_product_annotation_region"
        assert feature_review["feature_slots"][0]["rendered"] is False
        assert feature_review["feature_slots"][0]["truncation_applied"] is False
        assert feature_review["feature_slots"][0]["reason_code"] == "delegated_to_product_annotation_region"
        hero_review = metadata["hero_contract_review"]
        assert hero_review["hero_mode"] == "scenario_cover_product_contain"
        assert hero_review["requested_product_source"] == "mock://product"
        assert hero_review["rendered_product_source"] == "mock://product"
        assert hero_review["scenario_safe_fill_applied"] is False
        assert hero_review["scenario_region"]["rendered"] is False
        assert hero_review["product_region"]["rendered"] is True
        assert hero_review["behavior_policy"]["scenario_render_policy"] == "scenario_optional_safe_fill_cover"
        assert hero_review["behavior_policy"]["product_render_policy"] == "product_contain_centered"
        product_review = metadata["product_contract_review"]
        assert product_review["product_annotation_owner"] == "product_region"
        assert product_review["product_geometry_mode"] == "single_primary_v1"
        header_review = metadata["header_contract_review"]
        assert header_review["requested_brand_text"] == "厨厨房"
        assert header_review["requested_agent_text"] == "智能顾问"
        assert header_review["sanitized_brand_text"] == "厨厨房"
        assert header_review["sanitized_agent_text"] == "智能顾问"
        assert header_review["rendered_brand_excerpt"] == "厨厨房"
        assert header_review["rendered_agent_excerpt"] == "智能顾问"
        assert header_review["brand_truncation_applied"] is False
        assert header_review["agent_truncation_applied"] is False
        assert header_review["behavior_policy"]["lane_layout_mode"] == "single_line"
        assert header_review["behavior_policy"]["brand_text_policy"] == "single_line_brand_lockup"
        assert header_review["brand_name_slot"]["rendered"] is True
        assert header_review["agent_name_slot"]["rendered"] is True
        bottom_review = metadata["bottom_contract_review"]
        assert bottom_review["bottom_mode"] == "title_gallery_split"
        assert bottom_review["gallery_mode"] == "strip_local_visible_only"
        assert bottom_review["requested_title_text"] == "测试标题"
        assert bottom_review["requested_subtitle_text"] == "测试副标题"
        assert bottom_review["sanitized_title_text"] == "测试标题"
        assert bottom_review["sanitized_subtitle_text"] == "测试副标题"
        assert bottom_review["rendered_title_excerpt"] == "测试标题"
        assert bottom_review["rendered_subtitle_excerpt"] == "测试副标题"
        assert bottom_review["title_truncation_applied"] is False
        assert bottom_review["subtitle_truncation_applied"] is False
        assert bottom_review["title_source"] == "request.title"
        assert bottom_review["subtitle_source"] == "request.subtitle"
        assert bottom_review["subtitle_slot"]["rendered"] is True
        assert bottom_review["gallery_slots"]["gallery_item_slot_1"]["rendered"] is False
        assert bottom_review["behavior_policy"]["title_band_sizing_mode"] == "standard"
        assert bottom_review["behavior_policy"]["subtitle_overflow_policy"] == "single_line_ellipsis_inside_expanded_split_title_band"
        assert bottom_review["behavior_policy"]["content_priority_policy"] == "expanded_balanced_text_and_gallery_priority"
        assert bottom_review["behavior_policy"]["layout_metrics"]["title_band_height"] == 168

    def test_bottom_contract_review_preserves_empty_subtitle_without_fallback_contamination(self):
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            return f"mock://{key}"

        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(),
            put_bytes_fn=fake_put_bytes,
        )

        asyncio.run(
            pipeline.run(
                _make_spec(subtitle="   "),
                _load_template(),
            )
        )

        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        bottom_review = metadata["bottom_contract_review"]

        assert bottom_review["requested_subtitle_text"] == "   "
        assert bottom_review["sanitized_subtitle_text"] == ""
        assert bottom_review["rendered_subtitle_excerpt"] == ""
        assert bottom_review["subtitle_truncation_applied"] is False
        assert bottom_review["subtitle_source"] == "request.subtitle"
        assert bottom_review["subtitle_slot"]["rendered"] is False
        assert bottom_review["subtitle_slot"]["reason_code"] == "subtitle_empty"

    def test_bottom_contract_review_exposes_text_truncation_chain_for_dense_pair_layout(self):
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            return f"mock://{key}"

        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            gallery=[PILImage.new("RGBA", (400, 200), (50, 100, 200, 255)) for _ in range(2)],
            gallery_status=[
                {"index": index, "url": f"mock://gallery-{index}", "resolved": True, "error_code": None}
                for index in range(2)
            ],
        )

        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=fake_put_bytes,
        )

        requested_title = "超长标题" * 12
        requested_subtitle = "这是一段更长的底部说明文案，用来验证请求值、规范化值和最终渲染摘录是否可以完整串起来供运营核对。"

        asyncio.run(
            pipeline.run(
                _make_spec(
                    title=requested_title,
                    subtitle=requested_subtitle,
                    gallery_images=tuple(AssetRef(url=f"mock://gallery-{index}") for index in range(2)),
                ),
                _load_template(),
            )
        )

        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        bottom_review = metadata["bottom_contract_review"]
        title_budget = bottom_review["behavior_policy"]["title_char_budget"]
        subtitle_budget = bottom_review["behavior_policy"]["subtitle_char_budget"]

        assert bottom_review["requested_title_text"] == requested_title
        assert bottom_review["requested_subtitle_text"] == requested_subtitle
        assert bottom_review["sanitized_title_text"] == requested_title
        assert bottom_review["sanitized_subtitle_text"] == requested_subtitle
        assert bottom_review["rendered_title_excerpt"] == requested_title[:title_budget]
        assert bottom_review["rendered_subtitle_excerpt"] == requested_subtitle[:subtitle_budget]
        assert bottom_review["title_truncation_applied"] is (
            bottom_review["rendered_title_excerpt"] != bottom_review["sanitized_title_text"]
        )
        assert bottom_review["subtitle_truncation_applied"] is (
            bottom_review["rendered_subtitle_excerpt"] != bottom_review["sanitized_subtitle_text"]
        )

    def test_renderer_metadata_keeps_gallery_visibility_geometry(self):
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            return f"mock://{key}"

        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            gallery=[PILImage.new("RGBA", (400, 200), (50, 100, 200, 255))],
            gallery_status=[
                {"index": 0, "url": "mock://gallery-0", "resolved": True, "error_code": None},
            ],
        )

        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=fake_put_bytes,
        )

        asyncio.run(
            pipeline.run(
                _make_spec(gallery_images=(AssetRef(url="mock://gallery-0"),)),
                _load_template(),
            )
        )

        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        gallery_status = metadata["gallery_items_status"]
        assert gallery_status
        assert gallery_status[0]["visible_in_strip"] is True
        assert gallery_status[0]["local_bounds"]["x"] == 272
        assert gallery_status[0]["local_bounds"]["y"] == 0
        geometry = metadata["geometry_evidence"]
        assert geometry["region_bounds"]["gallery_strip_region"] == {"x": 350, "y": 808, "w": 324, "h": 88}
        assert geometry["slot_bounds"]["gallery_slot"] == {"x": 368, "y": 818, "w": 288, "h": 68}
        assert geometry["visible_item_count"]["gallery_strip_region"] == 1

    def test_renderer_metadata_exposes_bottom_mode_gallery_only_review(self):
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            return f"mock://{key}"

        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            gallery=[PILImage.new("RGBA", (400, 200), (50, 100, 200, 255))],
            gallery_status=[
                {"index": 0, "url": "mock://gallery-0", "resolved": True, "error_code": None},
            ],
        )

        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=fake_put_bytes,
        )

        asyncio.run(
            pipeline.run(
                _make_spec(
                    gallery_images=(AssetRef(url="mock://gallery-0"),),
                    bottom_mode="gallery_only",
                    gallery_mode="supporting_packshots",
                ),
                _load_template(),
            )
        )

        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        assert metadata["template_behavior"]["behavior_modes"]["bottom_mode"] == "gallery_only"
        assert metadata["template_behavior"]["behavior_modes"]["gallery_mode"] == "supporting_packshots"
        assert metadata["bottom_contract_review"]["title_band_region"]["rendered"] is False
        assert metadata["bottom_contract_review"]["gallery_strip_region"]["rendered"] is True
        assert metadata["bottom_contract_review"]["subtitle_slot"]["reason_code"] == "suppressed_by_bottom_mode"
        assert metadata["bottom_contract_review"]["gallery_slots"]["gallery_item_slot_1"]["rendered"] is True
        assert metadata["bottom_contract_review"]["behavior_policy"]["title_band_growth_policy"] == "title_band_collapsed_without_title"
        assert metadata["bottom_contract_review"]["behavior_policy"]["content_priority_policy"] == "gallery_priority_without_title_band"
        assert metadata["bottom_contract_review"]["behavior_policy"]["peer_balance_policy"] == "gallery_strip_only"
        assert metadata["bottom_contract_review"]["behavior_policy"]["bottom_peer_balance_policy"] == "gallery_only_bottom_rebalance"
        assert metadata["bottom_contract_review"]["behavior_policy"]["gallery_distribution_policy"] == "single_packshot_focus"
        assert metadata["bottom_contract_review"]["behavior_policy"]["gallery_shell_frame_policy"] == "single_showcase_frame"
        assert metadata["bottom_contract_review"]["behavior_policy"]["gallery_strip_shift_policy"] == "single_gallery_centered_shift"
        assert metadata["bottom_contract_review"]["behavior_policy"]["gallery_aspect_policy"] == "single_packshot_aspect"
        assert metadata["bottom_contract_review"]["behavior_policy"]["bottom_text_emphasis_policy"] == "gallery_only_neutral_text"
        assert metadata["bottom_contract_review"]["gallery_slots"]["gallery_item_slot_1"]["local_bounds"] == {
            "x": 296,
            "y": 10,
            "w": 240,
            "h": 64,
        }

    def test_renderer_metadata_exposes_dense_bottom_behavior_policy(self):
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            return f"mock://{key}"

        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            gallery=[PILImage.new("RGBA", (400, 200), (50, 100, 200, 255)) for _ in range(4)],
            gallery_status=[
                {"index": index, "url": f"mock://gallery-{index}", "resolved": True, "error_code": None}
                for index in range(4)
            ],
        )

        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=fake_put_bytes,
        )

        asyncio.run(
            pipeline.run(
                _make_spec(
                    title="超长标题超长标题超长标题超长标题",
                    subtitle="这是一段更长的底部说明文案，用来验证 subtitle overflow、title band sizing 和 gallery peer balance 会不会进入 resolver 策略。",
                    gallery_images=tuple(AssetRef(url=f"mock://gallery-{index}") for index in range(4)),
                ),
                _load_template(),
            )
        )

        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        behavior = metadata["bottom_contract_review"]["behavior_policy"]
        geometry = metadata["geometry_evidence"]
        assert behavior["title_band_sizing_mode"] == "standard"
        assert behavior["title_band_growth_policy"] == "hold_growth_expanded_text_gallery_quad"
        assert behavior["subtitle_overflow_policy"] == "single_line_ellipsis_inside_expanded_split_title_band"
        assert behavior["content_priority_policy"] == "expanded_gallery_count_priority_with_text_preserved"
        assert behavior["peer_balance_policy"] == "expanded_gallery_preserved_with_full_title"
        assert behavior["bottom_peer_balance_policy"] == "expanded_quad_gallery_with_full_title"
        assert behavior["gallery_distribution_policy"] == "dense_quad"
        assert behavior["gallery_shell_frame_policy"] == "quad_strip_frame"
        assert behavior["gallery_strip_shift_policy"] == "tight_quad_shift"
        assert behavior["gallery_aspect_policy"] == "compact_quad_aspect"
        assert behavior["bottom_text_emphasis_policy"] == "expanded_quad_text_emphasis"
        assert behavior["subtitle_line_clamp"] == 1
        assert geometry["region_bounds"]["title_band_region"] == {"x": 112, "y": 640, "w": 800, "h": 168}
        assert geometry["region_bounds"]["gallery_strip_region"] == {"x": 96, "y": 808, "w": 832, "h": 68}
        assert geometry["slot_bounds"]["subtitle_slot"] == {"x": 152, "y": 751, "w": 720, "h": 28}

    def test_renderer_metadata_exposes_light_gallery_peer_growth_policy(self):
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            return f"mock://{key}"

        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            gallery=[PILImage.new("RGBA", (400, 200), (50, 100, 200, 255)) for _ in range(2)],
            gallery_status=[
                {"index": index, "url": f"mock://gallery-{index}", "resolved": True, "error_code": None}
                for index in range(2)
            ],
        )

        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=fake_put_bytes,
        )

        asyncio.run(
            pipeline.run(
                _make_spec(
                    title="超长标题超长标题超长标题超长标题",
                    subtitle="这是一段更长的底部说明文案，用来验证 subtitle overflow、title band sizing 和 gallery peer balance 会不会进入 resolver 策略。",
                    gallery_images=tuple(AssetRef(url=f"mock://gallery-{index}") for index in range(2)),
                ),
                _load_template(),
            )
        )

        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        behavior = metadata["bottom_contract_review"]["behavior_policy"]
        assert behavior["title_band_sizing_mode"] == "expanded"
        assert behavior["title_band_growth_policy"] == "grow_title_band_expanded_text_gallery_light_gallery"
        assert behavior["content_priority_policy"] == "expanded_text_priority_with_light_gallery"
        assert behavior["peer_balance_policy"] == "expanded_title_growth_with_light_gallery"
        assert behavior["bottom_peer_balance_policy"] == "expanded_copy_priority_spacious_gallery"
        assert behavior["gallery_distribution_policy"] == "balanced_pair"
        assert behavior["gallery_shell_frame_policy"] == "pair_showcase_frame"
        assert behavior["gallery_strip_shift_policy"] == "downshift_for_spacious_pair"
        assert behavior["gallery_aspect_policy"] == "spacious_pair_aspect"
        assert behavior["bottom_text_emphasis_policy"] == "expanded_copy_priority_strong_title"
        assert metadata["bottom_contract_review"]["gallery_strip_region"]["bounds"] == {"x": 208, "y": 832, "w": 608, "h": 100}
        assert metadata["bottom_contract_review"]["gallery_slots"]["gallery_item_slot_1"]["local_bounds"] == {
            "x": 128,
            "y": 10,
            "w": 280,
            "h": 80,
        }

    def test_renderer_metadata_exposes_triplet_gallery_balancing_policy(self):
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            return f"mock://{key}"

        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            gallery=[PILImage.new("RGBA", (400, 200), (50, 100, 200, 255)) for _ in range(3)],
            gallery_status=[
                {"index": index, "url": f"mock://gallery-{index}", "resolved": True, "error_code": None}
                for index in range(3)
            ],
        )

        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=fake_put_bytes,
        )

        asyncio.run(
            pipeline.run(
                _make_spec(
                    title="超长标题超长标题超长标题超长标题",
                    subtitle="这是一段更长的底部说明文案，用来明确触发 triplet gallery 的 mixed-content 行为。",
                    gallery_images=tuple(AssetRef(url=f"mock://gallery-{index}") for index in range(3)),
                ),
                _load_template(),
            )
        )

        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        behavior = metadata["bottom_contract_review"]["behavior_policy"]
        assert behavior["title_band_growth_policy"] == "temper_growth_expanded_text_gallery_triplet"
        assert behavior["bottom_peer_balance_policy"] == "expanded_triplet_gallery_and_copy_co_balance"
        assert behavior["gallery_distribution_policy"] == "balanced_triplet"
        assert behavior["gallery_shell_frame_policy"] == "triplet_balanced_frame"
        assert behavior["gallery_strip_shift_policy"] == "balanced_triplet_shift"
        assert behavior["gallery_aspect_policy"] == "balanced_triplet_aspect"
        assert behavior["gallery_spacing_policy"] == "balanced_triplet_spacing"
        assert behavior["bottom_text_emphasis_policy"] == "expanded_balanced_triplet_text_emphasis"
        assert metadata["bottom_contract_review"]["gallery_strip_region"]["bounds"] == {"x": 156, "y": 816, "w": 712, "h": 80}
        assert metadata["bottom_contract_review"]["gallery_slots"]["gallery_item_slot_1"]["local_bounds"] == {
            "x": 74,
            "y": 10,
            "w": 220,
            "h": 60,
        }

    @pytest.mark.parametrize(
        ("requested_count", "normalized_count", "resolved_count", "expected_policy"),
        [
            (1, 1, 1, "single_center_focus"),
            (2, 2, 2, "balanced_pair"),
            (3, 3, 3, "balanced_triplet"),
            (4, 4, 4, "dense_quad"),
        ],
    )
    def test_bottom_gallery_count_matrix_1_2_3_4_is_reviewable_end_to_end(
        self,
        requested_count,
        normalized_count,
        resolved_count,
        expected_policy,
    ):
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            return f"mock://{key}"

        gallery_assets = [PILImage.new("RGBA", (400, 200), (50, 100, 200, 255)) for _ in range(resolved_count)]
        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            gallery=gallery_assets,
            gallery_status=[
                {"index": index, "url": f"mock://gallery-{index}", "resolved": True, "error_code": None}
                for index in range(resolved_count)
            ],
        )

        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=fake_put_bytes,
        )

        manifest = asyncio.run(
            pipeline.run(
                _make_spec(
                    gallery_images=tuple(AssetRef(url=f"mock://gallery-{index}") for index in range(normalized_count)),
                    gallery_input_count_raw=requested_count,
                    gallery_input_count_normalized=normalized_count,
                    gallery_requested_count=requested_count,
                    gallery_autofill_applied=False,
                ),
                _load_template(),
            )
        )

        assert manifest.structure_complete is True
        assert manifest.deliverable is True

        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        bottom_review = metadata["bottom_contract_review"]

        assert bottom_review["gallery_input_count_raw"] == requested_count
        assert bottom_review["gallery_input_count_normalized"] == normalized_count
        assert bottom_review["gallery_requested_count"] == requested_count
        assert bottom_review["gallery_visible_count"] == resolved_count
        assert bottom_review["gallery_autofill_applied"] is False
        assert bottom_review["behavior_policy"]["gallery_distribution_policy"] == expected_policy

    def test_bottom_gallery_count_chain_preserves_requested_pair_with_single_real_input(self):
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            return f"mock://{key}"

        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            gallery=[PILImage.new("RGBA", (400, 200), (50, 100, 200, 255))],
            gallery_status=[
                {"index": 0, "url": "mock://gallery-0", "resolved": True, "error_code": None},
            ],
        )

        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=fake_put_bytes,
        )

        asyncio.run(
            pipeline.run(
                _make_spec(
                    gallery_images=(AssetRef(url="mock://gallery-0"),),
                    gallery_input_count_raw=2,
                    gallery_input_count_normalized=1,
                    gallery_requested_count=2,
                    gallery_autofill_applied=False,
                ),
                _load_template(),
            )
        )

        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        bottom_review = metadata["bottom_contract_review"]

        assert bottom_review["gallery_input_count_raw"] == 2
        assert bottom_review["gallery_input_count_normalized"] == 1
        assert bottom_review["gallery_requested_count"] == 2
        assert bottom_review["gallery_visible_count"] == 1
        assert bottom_review["behavior_policy"]["gallery_distribution_policy"] == "single_center_focus"
        assert bottom_review["gallery_slots"]["gallery_item_slot_1"]["rendered"] is True
        assert bottom_review["gallery_slots"]["gallery_item_slot_2"]["reason_code"] == "gallery_input_missing"

    def test_renderer_metadata_exposes_template_level_layout_policy_when_feature_and_bottom_are_both_dense(self):
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            return f"mock://{key}"

        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            gallery=[PILImage.new("RGBA", (400, 200), (50, 100, 200, 255)) for _ in range(4)],
            gallery_status=[
                {"index": index, "url": f"mock://gallery-{index}", "resolved": True, "error_code": None}
                for index in range(4)
            ],
        )

        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=fake_put_bytes,
        )

        asyncio.run(
            pipeline.run(
                _make_spec(
                    title="超长标题超长标题超长标题超长标题",
                    subtitle="这是一段更长的底部说明文案，用来验证 template-level priority 和 rebalance 是否已经从 bottom SOP 上升出来。",
                    features=("特性A", "特性B", "特性C", "特性D"),
                    gallery_images=tuple(AssetRef(url=f"mock://gallery-{index}") for index in range(4)),
                ),
                _load_template_with_feature_mode("count_driven_callout_stack"),
            )
        )

        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        template_layout = metadata["template_behavior"]["template_layout_policy"]
        layout_review = metadata["template_layout_review"]
        feature_policy = metadata["template_behavior"]["feature_policy"]

        assert template_layout["layout_density_mode"] == "multi_region_dense"
        assert template_layout["region_priority_policy"] == "bottom_and_feature_dual_density"
        assert template_layout["peer_rebalance_policy"] == "feature_compacts_before_template_reflow"
        assert layout_review["feature_region_response"]["start_strategy"] == "top_weighted_compact_region"
        assert feature_policy["box_h"] == 56
        assert feature_policy["gap"] == 10

    def test_header_contract_review_exposes_brand_only_mode_and_sanitized_text_chain(self):
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            return f"mock://{key}"

        template = _load_template()
        template.behavior_modes = replace(template.behavior_modes, header_mode="brand_only")
        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(),
            put_bytes_fn=fake_put_bytes,
        )

        asyncio.run(
            pipeline.run(
                _make_spec(brand_name="  厨厨房品牌馆  ", agent_name="  智能顾问  "),
                template,
            )
        )

        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        header_review = metadata["header_contract_review"]
        geometry = metadata["geometry_evidence"]

        assert header_review["header_mode"] == "brand_only"
        assert header_review["requested_brand_text"] == "  厨厨房品牌馆  "
        assert header_review["sanitized_brand_text"] == "厨厨房品牌馆"
        assert header_review["requested_agent_text"] == "  智能顾问  "
        assert header_review["sanitized_agent_text"] == "智能顾问"
        assert header_review["rendered_agent_excerpt"] == ""
        assert header_review["agent_name_slot"]["rendered"] is False
        assert header_review["agent_name_slot"]["reason_code"] == "suppressed_by_header_mode"
        assert header_review["behavior_policy"]["identity_zone_mode"] == "brand_only"
        assert geometry["region_bounds"]["header_region"] == {"x": 72, "y": 56, "w": 880, "h": 96}
        assert geometry["slot_bounds"]["brand_name_slot"] == {"x": 104, "y": 82, "w": 808, "h": 32}

    def test_hero_contract_review_exposes_single_product_focus_without_scenario_region_render(self):
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            return f"mock://{key}"

        template = _load_template()
        template.behavior_modes = replace(template.behavior_modes, hero_mode="single_product_focus")
        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(),
            put_bytes_fn=fake_put_bytes,
        )

        asyncio.run(
            pipeline.run(
                _make_spec(scenario_image=None),
                template,
            )
        )

        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        hero_review = metadata["hero_contract_review"]

        assert hero_review["hero_mode"] == "single_product_focus"
        assert hero_review["scenario_safe_fill_applied"] is False
        assert hero_review["scenario_slot"]["rendered"] is False
        assert hero_review["product_slot"]["rendered"] is True
        assert hero_review["behavior_policy"]["peer_layout_policy"] == "single_product_without_scenario_peer"
        assert hero_review["behavior_policy"]["product_anchor"] == "bottom"

    def test_product_contract_review_exposes_independent_annotation_contract(self):
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            return f"mock://{key}"

        template = _load_template()
        template.behavior_modes = replace(
            template.behavior_modes,
            feature_mode="product_anchor_callouts",
            product_annotation_mode="product_anchor_callouts",
        )
        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(),
            put_bytes_fn=fake_put_bytes,
        )

        asyncio.run(
            pipeline.run(
                _make_spec(features=(" 特性A ", " 特性B ", " 特性C ")),
                template,
            )
        )

        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        product_review = metadata["product_contract_review"]
        feature_review = metadata["feature_contract_review"]

        assert product_review["product_annotation_mode"] == "product_anchor_callouts"
        assert product_review["product_annotation_owner"] == "product_region"
        assert product_review["requested_product_source"] == "mock://product"
        assert product_review["product_canvas_shell_layer"]["rendered"] is True
        assert product_review["product_annotation_shell_layer"]["rendered"] is True
        assert product_review["product_annotation_items_layer"]["visible_item_count"] == 3
        assert product_review["behavior_policy"]["annotation_count_policy"] == "fixed_3_product_anchor_annotations"
        assert product_review["behavior_policy"]["annotation_connector_policy"] == "product_anchor_leader_line"
        assert product_review["annotation_slots"][0]["anchor_x"] == 764
        assert product_review["annotation_slots"][0]["rendered_excerpt"] == "特性A"
        assert feature_review["delegated_to_product_annotation"] is True
        assert feature_review["feature_region"]["rendered"] is False
        assert metadata["template_behavior"]["behavior_modes"]["product_annotation_mode"] == "product_anchor_callouts"

    def test_feature_contract_review_exposes_requested_sanitized_rendered_chain_with_empty_and_capped_items(self):
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            return f"mock://{key}"

        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(),
            put_bytes_fn=fake_put_bytes,
        )

        asyncio.run(
            pipeline.run(
                _make_spec(features=(" 特性A ", "   ", "超长特性文案超长特性文案超长特性文案超长特性文案超长特性文案", "特性D", "特性E")),
                _load_template_with_feature_mode("count_driven_callout_stack"),
            )
        )

        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        feature_review = metadata["feature_contract_review"]

        assert feature_review["requested_feature_items"] == [" 特性A ", "   ", "超长特性文案超长特性文案超长特性文案超长特性文案超长特性文案", "特性D", "特性E"]
        assert feature_review["sanitized_feature_items"] == ["特性A", "超长特性文案超长特性文案超长特性文案超长特性文案超长特性文案", "特性D", "特性E"]
        assert feature_review["feature_region"]["visible_item_count"] == 4
        assert feature_review["behavior_policy"]["char_budget"] == 24
        assert feature_review["feature_slots"][1]["sanitized_text"] == "超长特性文案超长特性文案超长特性文案超长特性文案超长特性文案"
        assert feature_review["feature_slots"][1]["truncation_applied"] is True
        assert feature_review["feature_slots"][4]["rendered"] is False

    def test_renderer_metadata_includes_explicit_fallback_fields(self):
        template = _load_template()
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            if key.endswith(".json"):
                return "https://r2.example.com/renderer-metadata.json"
            if "product-material" in key:
                return "https://r2.example.com/product-material.png"
            if "/fg/" in key:
                return "https://r2.example.com/fg.png"
            return "https://r2.example.com/final.png"

        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            scenario=None,
            gallery=[],
        )
        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_FakeDegradedRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=fake_put_bytes,
        )

        manifest = asyncio.run(pipeline.run(_make_spec(), template))

        assert manifest.degraded is True
        assert manifest.fallback_reason_code == "puppeteer_timeout"
        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        assert metadata["requested_renderer_mode"] == "auto"
        assert metadata["render_engine_used"] == "pillow"
        assert metadata["effective_renderer_mode"] == "pillow"
        assert metadata["degraded"] is True
        assert metadata["fallback_reason_code"] == "puppeteer_timeout"
        assert metadata["deliverable"] is True
        assert metadata["structure_evidence_source"] == "renderer_derived"
        assert metadata["structure_evidence_complete"] is True

    def test_fallback_result_requires_structure_recheck(self):
        template = _load_template()
        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_FakeDegradedIncompleteRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(_make_assets()),
            put_bytes_fn=_mock_r2_put(),
        )

        with pytest.raises(RendererRoutingError) as excinfo:
            asyncio.run(pipeline.run(_make_spec(), template))

        assert excinfo.value.reason_code == "fallback_incomplete_structure"

    def test_incomplete_structure_is_not_deliverable_even_when_image_exists(self):
        template = _load_template()
        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_FakeIncompleteRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(_make_assets()),
            put_bytes_fn=_mock_r2_put(),
        )
        manifest = asyncio.run(pipeline.run(_make_spec(), template))
        assert manifest.final_url == "https://r2.example.com/final.png"
        assert manifest.structure_complete is False
        assert manifest.incomplete_structure is True
        assert manifest.deliverable is False
        assert "title_band_region" in manifest.missing_mandatory_regions

    def test_inferred_only_structure_path_does_not_overclaim_deliverable(self):
        template = _load_template()
        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_FakeInferredRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(_make_assets()),
            put_bytes_fn=_mock_r2_put(),
        )

        manifest = asyncio.run(pipeline.run(_make_spec(), template))

        assert manifest.structure_evidence_source == "pipeline_inferred"
        assert manifest.structure_evidence_complete is False
        assert manifest.structure_complete is False
        assert manifest.incomplete_structure is True
        assert manifest.deliverable is False

    def test_scenario_contract_review_exposes_full_evidence_for_scenario_cover_mode(self):
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            return f"mock://{key}"

        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            scenario=PILImage.new("RGBA", (800, 600), (50, 100, 200, 255)),
        )
        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=fake_put_bytes,
        )

        bg_result = BackgroundResult(
            url="mock://bg", key="bg.png", prompt_used="scenario_image_preferred",
            seed_used=0, model="scenario_blurred", width=1024, height=1024,
        )
        with patch(
            "app.services.poster2.pipeline.build_template_dual_v2_background",
            new=AsyncMock(return_value=bg_result),
        ):
            asyncio.run(
                pipeline.run(
                    _make_spec(scenario_image=AssetRef(url="mock://scenario")),
                    _load_template(),
                )
            )

        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        review = metadata["scenario_contract_review"]

        # mode + policy
        assert review["hero_mode"] == "scenario_cover_product_contain"
        assert review["scenario_enabled"] is True
        assert review["scenario_render_policy"] == "scenario_optional_safe_fill_cover"

        # source chain
        assert review["requested_source"] == "mock://scenario"
        assert review["sanitized_source"] == "mock://scenario"
        assert review["rendered_source"] == "mock://scenario"
        assert review["safe_fill_applied"] is False
        assert review["source_binding"] == "request.scenario_image.url"

        # scenario_region bounds
        assert review["scenario_region"]["rendered"] is True
        assert review["scenario_region"]["bounds"] == {"x": 96, "y": 188, "w": 288, "h": 520}

        # scenario_slot
        assert review["scenario_slot"]["rendered"] is True
        assert review["scenario_slot"]["reason_code"] is None
        assert review["scenario_slot"]["bounds"] == {"x": 96, "y": 188, "w": 288, "h": 520}

        # behavior_policy
        bp = review["behavior_policy"]
        assert bp["scenario_render_policy"] == "scenario_optional_safe_fill_cover"
        assert bp["scenario_fit"] == "cover"
        assert bp["scenario_anchor"] == "center"
        assert bp["peer_layout_policy"] == "fixed_dual_hero_peer_regions"
        assert bp["layout_metrics"]["scenario_region_x"] == 96
        assert bp["layout_metrics"]["scenario_region_y"] == 188
        assert bp["layout_metrics"]["scenario_region_w"] == 288
        assert bp["layout_metrics"]["scenario_region_h"] == 520

        # parity note is present
        assert "evidence_source" in review
        assert "renderer_path_parity" in review

    def test_scenario_contract_review_exposes_disabled_policy_for_single_product_focus(self):
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            return f"mock://{key}"

        template = _load_template()
        template.behavior_modes = replace(template.behavior_modes, hero_mode="single_product_focus")
        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=_AsyncPillowRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(),
            put_bytes_fn=fake_put_bytes,
        )

        asyncio.run(
            pipeline.run(
                _make_spec(scenario_image=None),
                template,
            )
        )

        metadata_key = next(key for key in stored_payloads if key.endswith(".json"))
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        review = metadata["scenario_contract_review"]

        # mode + policy
        assert review["hero_mode"] == "single_product_focus"
        assert review["scenario_enabled"] is False
        assert review["scenario_render_policy"] == "scenario_disabled"

        # source chain: no scenario image was supplied
        assert review["requested_source"] is None
        assert review["sanitized_source"] is None
        assert review["safe_fill_applied"] is False

        # scenario_region not rendered
        assert review["scenario_region"]["rendered"] is False
        assert review["scenario_region"]["bounds"]["x"] == 96  # bounds still present from layout_metrics

        # scenario_slot not rendered; Pillow emits reason_code="scenario_missing" for disabled+absent
        assert review["scenario_slot"]["rendered"] is False
        assert review["scenario_slot"]["reason_code"] == "scenario_missing"

        # behavior_policy
        bp = review["behavior_policy"]
        assert bp["scenario_render_policy"] == "scenario_disabled"
        assert bp["peer_layout_policy"] == "single_product_without_scenario_peer"


# ── Family A Structural Closeout Tests ───────────────────────────────────────

def _run_pipeline_with_stored_metadata(template, spec, assets: ResolvedAssets | None = None):
    """Run the pipeline and return the parsed renderer metadata payload."""
    stored_payloads: dict[str, bytes] = {}

    def fake_put_bytes(key, data, **kwargs):
        stored_payloads[key] = data
        return f"mock://{key}"

    pipeline = PosterPipeline(
        background_svc=_mock_bg_service(),
        renderer=_AsyncPillowRenderer(),
        composer=Composer(),
        asset_loader=_mock_loader(assets or ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
        )),
        put_bytes_fn=fake_put_bytes,
    )
    manifest = asyncio.run(pipeline.run(spec, template))
    metadata_key = next(k for k in stored_payloads if "metadata" in k)
    metadata = json.loads(stored_payloads[metadata_key])
    return manifest, metadata


class TestBottomStructuralExpansion:
    """Scope A: text_only_expanded and text_gallery_expanded resolve with materially larger capacity."""

    def test_text_only_expanded_resolves_with_larger_text_capacity_than_frozen_baseline(self):
        template = _load_template()
        template.behavior_modes = replace(template.behavior_modes, bottom_mode="text_only_expanded")
        spec = _make_spec(
            title="Upgrade your kitchen with ChefCraft",
            subtitle="April 24 we'll start using GitHub Copilot interaction",
        )
        manifest, metadata = _run_pipeline_with_stored_metadata(template, spec)
        review = metadata["bottom_contract_review"]

        # Shell starts higher than frozen baseline
        assert review["behavior_policy"]["layout_metrics"]["bottom_shell_top"] == 656
        # Title budget materially larger than frozen baseline max (36–44 chars)
        assert review["behavior_policy"]["title_char_budget"] >= 52
        # Subtitle budget materially larger than frozen baseline max (28 chars)
        assert review["behavior_policy"]["subtitle_char_budget"] >= 44
        # No gallery strip in text_only_expanded mode
        assert review["behavior_policy"]["layout_metrics"]["gallery_shell_height"] == 0

    def test_text_gallery_expanded_shell_top_is_640(self):
        """Shell geometry is the structural guarantee — test it via pipeline."""
        template = _load_template()
        template.behavior_modes = replace(template.behavior_modes, bottom_mode="text_gallery_expanded")
        spec = _make_spec(
            title="Upgrade your kitchen with ChefCraft",
            subtitle="April 24 we'll start using GitHub Copilot interaction",
        )
        manifest, metadata = _run_pipeline_with_stored_metadata(template, spec)
        review = metadata["bottom_contract_review"]

        # Shell starts higher than frozen baseline
        assert review["behavior_policy"]["layout_metrics"]["bottom_shell_top"] == 640
        # title budget is materially larger than the frozen baseline dense-quad minimum (20)
        assert review["behavior_policy"]["title_char_budget"] >= 44

    def test_text_gallery_expanded_resolver_dense_quad_title_budget_not_twenty(self):
        """Resolver-level test: dense-quad text_gallery_expanded must not revert to title_char_budget=20."""
        from app.services.poster2.template_behavior import resolve_bottom_behavior
        policy = resolve_bottom_behavior(
            "text_gallery_expanded",
            gallery_mode="strip_local_visible_only",
            title_text="Upgrade your kitchen with ChefCraft",
            subtitle_text="April 24 we'll start using GitHub Copilot interaction",
            requested_gallery_count=4,
            normalized_gallery_count=4,
            resolved_gallery_count=4,
            max_items=4,
        )
        # Dense-quad in expanded mode must never assign title_char_budget=20
        assert policy.title_char_budget >= 44
        # Full title (35 chars) must survive the budget
        from app.services.poster2.pipeline import _apply_text_budget
        rendered = _apply_text_budget("Upgrade your kitchen with ChefCraft", policy.title_char_budget)
        assert rendered == "Upgrade your kitchen with ChefCraft"

    def test_frozen_baseline_modes_still_resolve_unchanged(self):
        """Existing modes must not be affected by the expanded mode additions."""
        template = _load_template()
        template.behavior_modes = replace(template.behavior_modes, bottom_mode="title_gallery_split")
        spec = _make_spec(title="Short title", subtitle="Short sub")
        manifest, metadata = _run_pipeline_with_stored_metadata(template, spec)
        review = metadata["bottom_contract_review"]

        # Frozen baseline shell top (title_gallery_split now uses y=640 via expanded geometry)
        assert review["behavior_policy"]["layout_metrics"]["bottom_shell_top"] == 640
        assert review["bottom_layout_mode"] == "title_gallery_split"
        assert review["bottom_mode"] == "title_gallery_split"

    def test_bottom_contract_review_exposes_requested_effective_and_override_reason(self):
        template = _load_template()
        spec = _make_spec(bottom_mode="title_only")
        _, metadata = _run_pipeline_with_stored_metadata(template, spec)
        review = metadata["bottom_contract_review"]

        assert review["requested_bottom_mode"] == "title_only"
        assert review["effective_bottom_mode"] == "text_only_expanded"  # alias applied
        assert review["bottom_mode_override_reason"] == "legacy_alias_canonicalized"
        assert review["bottom_mode"] == "text_only_expanded"
        assert review["bottom_layout_mode"] == "text_only_expanded"
        assert review["gallery_strip_region"]["rendered"] is False

    def test_legacy_expanded_request_is_canonicalized_into_semantic_bottom_mode(self):
        template = _load_template()
        spec = _make_spec(bottom_mode="text_gallery_expanded")
        _, metadata = _run_pipeline_with_stored_metadata(template, spec)
        review = metadata["bottom_contract_review"]

        assert review["requested_bottom_mode"] == "text_gallery_expanded"
        assert review["effective_bottom_mode"] == "text_gallery_expanded"  # now a canonical mode
        assert review["bottom_layout_mode"] == "text_gallery_expanded"
        assert review["bottom_mode_override_reason"] == "request_override_applied"


class TestProductLayoutContract:
    """Scope B: product_layout_mode exposes named slot contract surfaces."""

    def test_single_primary_mode_is_backward_compatible_default(self):
        template = _load_template()
        # Default mode from template spec — single_primary
        spec = _make_spec()
        manifest, metadata = _run_pipeline_with_stored_metadata(template, spec)
        review = metadata["product_contract_review"]

        assert review["product_layout_mode"] == "single_primary"
        primary = review["product_primary_slot"]
        assert primary["x"] == 456
        assert primary["y"] == 188
        assert primary["w"] == 300
        assert primary["h"] == 540
        assert review["product_secondary_slot"] is None
        assert review["product_secondary_slot_rendered"] is False
        assert review["product_secondary_asset_policy"] == "secondary_absent_collapsed"

    def test_primary_secondary_dual_exposes_named_slots(self):
        template = _load_template()
        spec = _make_spec(product_secondary_image=AssetRef(url="mock://product-secondary"))
        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            product_secondary=PILImage.new("RGBA", (320, 320), (50, 120, 220, 255)),
        )
        manifest, metadata = _run_pipeline_with_stored_metadata(template, spec, assets=assets)
        review = metadata["product_contract_review"]

        assert review["product_layout_mode"] == "primary_secondary_dual"
        assert review["product_layout_mode_reason"] == "auto_promoted_by_secondary_asset"

        primary = review["product_primary_slot"]
        assert primary["x"] == 456
        assert primary["y"] == 188
        assert primary["w"] == 300
        assert primary["h"] == 310

        secondary = review["product_secondary_slot"]
        assert secondary is not None
        assert secondary["x"] == 456
        assert secondary["y"] == 518
        assert secondary["w"] == 300
        assert secondary["h"] == 210

        assert review["product_secondary_slot_rendered"] is True
        assert review["product_secondary_asset_policy"] == "secondary_present"
        assert review["product_secondary_image_layer"]["rendered"] is True
        assert review["product_secondary_image_layer"]["bounds"] == {
            "x": 456,
            "y": 518,
            "w": 300,
            "h": 210,
        }
        assert metadata["geometry_evidence"]["slot_bounds"]["product_slot"] == {
            "x": 456,
            "y": 188,
            "w": 300,
            "h": 310,
        }
        assert metadata["geometry_evidence"]["slot_bounds"]["product_primary_slot"] == {
            "x": 456,
            "y": 188,
            "w": 300,
            "h": 310,
        }
        assert metadata["geometry_evidence"]["slot_bounds"]["product_secondary_slot"] == {
            "x": 456,
            "y": 518,
            "w": 300,
            "h": 210,
        }

    def test_annotation_mode_unaffected_by_dual_product_layout(self):
        """product_annotation_mode must remain live regardless of product_layout_mode."""
        template = _load_template()
        spec = _make_spec(
            features=("Feat A", "Feat B", "Feat C"),
            product_secondary_image=AssetRef(url="mock://product-secondary"),
        )
        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            product_secondary=PILImage.new("RGBA", (320, 320), (50, 120, 220, 255)),
        )
        manifest, metadata = _run_pipeline_with_stored_metadata(template, spec, assets=assets)
        review = metadata["product_contract_review"]

        # annotation_mode field must be present and valid
        assert review["product_annotation_mode"] in ("product_anchor_callouts", "none", "right_stack_mirror")
        # product_layout_mode is still dual
        assert review["product_layout_mode"] == "primary_secondary_dual"


class TestTextLayerEvidence:
    """Scope C: title_text_layer, subtitle_text_layer, header_text_layer are emitted per generation."""

    def test_title_text_layer_emitted_with_correct_structure(self):
        template = _load_template()
        spec = _make_spec(title="Full title text here", subtitle="Supporting subtitle copy")
        manifest, metadata = _run_pipeline_with_stored_metadata(template, spec)
        layer = metadata["title_text_layer"]

        assert layer["layer_id"] == "title_text_layer"
        assert "rendered" in layer
        assert "slot_bounds" in layer
        bounds = layer["slot_bounds"]
        assert "x" in bounds and "y" in bounds and "w" in bounds and "h" in bounds
        assert "requested_text" in layer
        assert "sanitized_text" in layer
        assert "rendered_excerpt" in layer
        assert "truncation_applied" in layer
        assert "line_clamp" in layer
        assert "char_budget" in layer
        assert layer["owner_region"] == "title_band_region"
        # Manifest also exposes these
        assert manifest.title_text_layer["layer_id"] == "title_text_layer"

    def test_subtitle_text_layer_emitted_with_correct_structure(self):
        template = _load_template()
        spec = _make_spec(title="Title", subtitle="Subtitle text here")
        manifest, metadata = _run_pipeline_with_stored_metadata(template, spec)
        layer = metadata["subtitle_text_layer"]

        assert layer["layer_id"] == "subtitle_text_layer"
        assert "rendered" in layer
        assert "slot_bounds" in layer
        assert "requested_text" in layer
        assert "sanitized_text" in layer
        assert "rendered_excerpt" in layer
        assert "truncation_applied" in layer
        assert layer["owner_region"] == "title_band_region"
        assert manifest.subtitle_text_layer["layer_id"] == "subtitle_text_layer"

    def test_header_text_layer_emitted_with_brand_and_agent_slots(self):
        template = _load_template()
        spec = _make_spec(brand_name="ChefCraft", agent_name="SmartKitchen Advisor")
        manifest, metadata = _run_pipeline_with_stored_metadata(template, spec)
        layer = metadata["header_text_layer"]

        assert layer["layer_id"] == "header_text_layer"
        assert "rendered" in layer
        assert layer["owner_region"] == "header_region"

        brand_slot = layer["brand_text_slot"]
        assert brand_slot["requested_text"] == "ChefCraft"
        assert "truncation_applied" in brand_slot
        assert "slot_bounds" in brand_slot
        assert brand_slot["slot_bounds"]["x"] == 244

        agent_slot = layer["agent_text_slot"]
        assert agent_slot["requested_text"] == "SmartKitchen Advisor"
        assert "truncation_applied" in agent_slot
        assert manifest.header_text_layer["layer_id"] == "header_text_layer"

    def test_title_text_layer_truncation_applied_flag_reflects_actual_truncation(self):
        template = _load_template()
        template.behavior_modes = replace(template.behavior_modes, bottom_mode="title_gallery_split")
        # Very long title that will be truncated under dense-quad budget
        long_title = "A" * 50
        spec = _make_spec(
            title=long_title,
            subtitle="B" * 50,
            gallery_images=(
                AssetRef(url="mock://g1"),
                AssetRef(url="mock://g2"),
                AssetRef(url="mock://g3"),
                AssetRef(url="mock://g4"),
            ),
            gallery_requested_count=4,
            gallery_input_count_normalized=4,
        )
        manifest, metadata = _run_pipeline_with_stored_metadata(template, spec)
        layer = metadata["title_text_layer"]

        if layer["rendered"]:
            # If rendered, truncation_applied must be True since title (50 chars) > any budget
            from app.services.poster2.pipeline import _apply_text_budget
            expected_excerpt = _apply_text_budget(long_title, layer["char_budget"])
            assert layer["rendered_excerpt"] == expected_excerpt
            assert layer["truncation_applied"] is (len(expected_excerpt) < len(long_title))


# ---------------------------------------------------------------------------
# PR-2: Bottom mode boundary freeze and mode-aware completeness diagnostics
# ---------------------------------------------------------------------------

class TestBottomModeBoundaryAndCompleteness:
    """PR-2: Freeze bottom mode boundaries and completeness rules.

    Validates:
    - per-mode collapsed-by-design regions do not appear in missing_mandatory_regions
    - bottom_mode_region_contract is emitted with correct frozen rules per mode
    - no silent fallback: unknown modes conservatively require title_band_region
    - diagnostics (requested_bottom_mode / effective_bottom_mode / bottom_layout_mode /
      override reason) are always present
    """

    def _run(self, bottom_mode: str, **spec_overrides):
        template = _load_template()
        template.behavior_modes = replace(template.behavior_modes, bottom_mode=bottom_mode)
        spec = _make_spec(**spec_overrides)
        return _run_pipeline_with_stored_metadata(template, spec)

    # --- gallery_only: title_band collapsed_by_design ---------------------------

    def test_gallery_only_title_band_absent_is_not_missing_mandatory(self):
        """gallery_only mode: title_band_region absence must not be a structure failure."""
        _, metadata = self._run(
            "gallery_only",
            title="Test Title",
            gallery_images=(AssetRef(url="mock://g1"),),
            gallery_requested_count=1,
            gallery_input_count_normalized=1,
        )
        assert "title_band_region" not in metadata["missing_mandatory_regions"]
        assert metadata["structure_complete"] is True
        assert metadata["deliverable"] is True

    def test_gallery_only_bottom_mode_region_contract_marks_title_band_collapsed(self):
        _, metadata = self._run(
            "gallery_only",
            title="Test Title",
            gallery_images=(AssetRef(url="mock://g1"),),
            gallery_requested_count=1,
            gallery_input_count_normalized=1,
        )
        contract = metadata["bottom_contract_review"]["bottom_mode_region_contract"]
        assert contract["title_band_region_collapsed_by_mode"] is True
        assert contract["gallery_strip_region_collapsed_by_mode"] is False
        assert contract["title_band_region_required"] is False
        assert "title_band_region" in contract["collapsed_by_design_regions"]

    # --- text_only_expanded: gallery_strip collapsed_by_design ------------------

    def test_text_only_expanded_gallery_strip_absent_is_not_missing_mandatory(self):
        """text_only_expanded mode: gallery_strip_region absence must not fail structure."""
        _, metadata = self._run("text_only_expanded", title="Test Title")
        assert "gallery_strip_region" not in metadata["missing_mandatory_regions"]
        assert metadata["structure_complete"] is True
        assert metadata["deliverable"] is True

    def test_text_only_expanded_bottom_mode_region_contract_marks_gallery_strip_collapsed(self):
        _, metadata = self._run("text_only_expanded", title="Test Title")
        contract = metadata["bottom_contract_review"]["bottom_mode_region_contract"]
        assert contract["gallery_strip_region_collapsed_by_mode"] is True
        assert contract["title_band_region_collapsed_by_mode"] is False
        assert contract["title_band_region_required"] is True
        assert "gallery_strip_region" in contract["collapsed_by_design_regions"]

    # --- title_gallery_split: title_band required --------------------------------

    def test_title_gallery_split_bottom_mode_region_contract_requires_title_band(self):
        _, metadata = self._run("title_gallery_split", title="Test Title")
        contract = metadata["bottom_contract_review"]["bottom_mode_region_contract"]
        assert contract["title_band_region_required"] is True
        assert contract["title_band_region_collapsed_by_mode"] is False
        assert contract["gallery_strip_region_collapsed_by_mode"] is False
        assert contract["collapsed_by_design_regions"] == []

    # --- text_gallery_expanded: title_band required ------------------------------

    def test_text_gallery_expanded_bottom_mode_region_contract_requires_title_band(self):
        _, metadata = self._run("text_gallery_expanded", title="Test Title")
        contract = metadata["bottom_contract_review"]["bottom_mode_region_contract"]
        assert contract["title_band_region_required"] is True
        assert contract["title_band_region_collapsed_by_mode"] is False
        assert contract["gallery_strip_region_collapsed_by_mode"] is False
        assert contract["collapsed_by_design_regions"] == []

    # --- diagnostics always present -----------------------------------------------

    def test_bottom_contract_review_always_exposes_full_diagnostic_fields(self):
        """requested_bottom_mode / effective_bottom_mode / bottom_layout_mode / reason always present."""
        mode_kwargs = {
            "title_gallery_split":   {"title": "Test Title"},
            "text_gallery_expanded": {"title": "Test Title"},
            "text_only_expanded":    {"title": "Test Title"},
            "gallery_only":          {
                "title": "",  # gallery_only: title band collapsed by design; title not required
                "gallery_images": (AssetRef(url="mock://g1"),),
                "gallery_requested_count": 1,
                "gallery_input_count_normalized": 1,
            },
        }
        for mode, kwargs in mode_kwargs.items():
            _, metadata = self._run(mode, **kwargs)
            review = metadata["bottom_contract_review"]
            assert "requested_bottom_mode" in review, f"missing requested_bottom_mode for mode={mode}"
            assert "effective_bottom_mode" in review, f"missing effective_bottom_mode for mode={mode}"
            assert "bottom_layout_mode" in review, f"missing bottom_layout_mode for mode={mode}"
            assert "bottom_mode_override_reason" in review, f"missing bottom_mode_override_reason for mode={mode}"
            assert review["effective_bottom_mode"] == mode, f"effective mode mismatch for mode={mode}"
            assert review["bottom_layout_mode"] == mode, f"layout mode must mirror effective mode for mode={mode}"
            assert review["bottom_mode_region_contract"]["effective_bottom_mode"] == mode

    def test_title_only_alias_canonicalized_to_text_only_expanded_with_explicit_diagnostics(self):
        """title_only is a known alias; must be canonicalized explicitly with diagnostics, no silent drop."""
        _, metadata = self._run("title_gallery_split")  # use title_gallery_split as base
        # Now use title_only as an override in the spec directly
        template = _load_template()
        template.behavior_modes = replace(template.behavior_modes, bottom_mode="title_gallery_split")
        spec = _make_spec(bottom_mode="title_only", title="Test Title")
        _, metadata = _run_pipeline_with_stored_metadata(template, spec)
        review = metadata["bottom_contract_review"]
        assert review["requested_bottom_mode"] == "title_only"
        assert review["effective_bottom_mode"] == "text_only_expanded"
        assert review["bottom_mode_remapped"] is True
        assert review["bottom_mode_alias"] == "title_only → text_only_expanded"
        assert review["bottom_mode_override_reason"] == "legacy_alias_canonicalized"


class TestBottomModeStabilization:
    """Task-1: text_gallery_expanded and gallery_only reach the same health bar as text_only_expanded.

    Health bar: degraded=False, structure_complete=True, deliverable=True,
    all four diagnostic fields present, no silent fallback.
    """

    def _run_gallery_only(self, *, with_title: bool, gallery_count: int = 1):
        """Run gallery_only with or without a title; always provides gallery assets."""
        template = _load_template()
        template.behavior_modes = replace(template.behavior_modes, bottom_mode="gallery_only")
        gallery_images = tuple(AssetRef(url=f"mock://g{i}") for i in range(gallery_count))
        spec = _make_spec(
            title="Title" if with_title else "",
            subtitle="",
            bottom_mode="gallery_only",
            gallery_images=gallery_images,
        )
        gallery_assets = [PILImage.new("RGBA", (200, 200), (100, 100, 200, 255)) for _ in range(gallery_count)]
        gallery_status = [
            {"index": i, "url": f"mock://g{i}", "resolved": True, "error_code": None}
            for i in range(gallery_count)
        ]
        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            gallery=gallery_assets,
            gallery_status=gallery_status,
        )
        return _run_pipeline_with_stored_metadata(template, spec, assets)

    def _run_text_gallery_expanded(self, *, gallery_count: int):
        template = _load_template()
        template.behavior_modes = replace(template.behavior_modes, bottom_mode="text_gallery_expanded")
        gallery_images = tuple(AssetRef(url=f"mock://g{i}") for i in range(gallery_count))
        spec = _make_spec(
            title="Upgrade your kitchen with ChefCraft",
            subtitle="Fresh ingredients, great results",
            bottom_mode="text_gallery_expanded",
            gallery_images=gallery_images,
        )
        gallery_assets = [PILImage.new("RGBA", (200, 200), (100, 100, 200, 255)) for _ in range(gallery_count)]
        gallery_status = [
            {"index": i, "url": f"mock://g{i}", "resolved": True, "error_code": None}
            for i in range(gallery_count)
        ]
        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            gallery=gallery_assets,
            gallery_status=gallery_status,
        ) if gallery_count > 0 else None
        return _run_pipeline_with_stored_metadata(template, spec, assets)

    # --- gallery_only without title: full health ---

    def test_gallery_only_deliverable_without_title(self):
        """gallery_only with no title must still be deliverable (title band is collapsed by design)."""
        _, metadata = self._run_gallery_only(with_title=False)
        assert metadata["degraded"] is False
        assert metadata["structure_complete"] is True
        assert metadata["deliverable"] is True
        assert "title_slot" not in metadata["missing_required_slots"]

    def test_gallery_only_title_slot_not_in_missing_required_when_absent(self):
        """title_slot must be excused for gallery_only even when spec.title is empty."""
        _, metadata = self._run_gallery_only(with_title=False)
        slot_status = metadata["slot_binding_status"]
        assert "title_slot" not in slot_status.get("missing_required_slots", [])

    def test_gallery_only_diagnostics_all_present_without_title(self):
        """All four bottom diagnostic fields must be present in gallery_only with no title."""
        _, metadata = self._run_gallery_only(with_title=False)
        review = metadata["bottom_contract_review"]
        assert review["requested_bottom_mode"] == "gallery_only"
        assert review["effective_bottom_mode"] == "gallery_only"
        assert review["bottom_layout_mode"] == "gallery_only"
        assert "bottom_mode_override_reason" in review

    # --- gallery_only geometry fix ---

    def test_gallery_only_gallery_shell_top_equals_bottom_shell_top(self):
        """gallery_shell_top must equal bottom_shell_top for gallery_only (not hardcoded 888)."""
        from app.services.poster2.template_behavior import resolve_bottom_behavior
        policy = resolve_bottom_behavior(
            "gallery_only",
            gallery_mode="strip_local_visible_only",
            title_text="",
            subtitle_text="",
            requested_gallery_count=1,
            normalized_gallery_count=1,
            resolved_gallery_count=1,
            max_items=4,
        )
        bottom_shell_top = policy.layout_metrics["bottom_shell_top"]
        gallery_shell_top = policy.layout_metrics["gallery_shell_top"]
        assert gallery_shell_top == bottom_shell_top, (
            f"gallery_shell_top ({gallery_shell_top}) must equal bottom_shell_top ({bottom_shell_top})"
        )

    def test_gallery_only_gallery_items_render_inside_bottom_shell(self):
        """Gallery items must have absolute y within the bottom shell bounds."""
        from app.services.poster2.template_behavior import resolve_bottom_behavior
        policy = resolve_bottom_behavior(
            "gallery_only",
            gallery_mode="strip_local_visible_only",
            title_text="",
            subtitle_text="",
            requested_gallery_count=2,
            normalized_gallery_count=2,
            resolved_gallery_count=2,
            max_items=4,
        )
        shell_top = policy.layout_metrics["bottom_shell_top"]
        shell_height = policy.layout_metrics["bottom_shell_height"]
        shell_bottom = shell_top + shell_height
        for slot in policy.gallery_slot_states:
            if slot["rendered"] and slot.get("bounds"):
                item_y = slot["bounds"]["y"]
                item_bottom = item_y + slot["bounds"]["h"]
                assert item_y >= shell_top, f"gallery item y={item_y} is above shell_top={shell_top}"
                assert item_bottom <= shell_bottom + 4, (
                    f"gallery item bottom={item_bottom} exceeds shell_bottom={shell_bottom}"
                )

    # --- text_gallery_expanded: full health ---

    def test_text_gallery_expanded_deliverable_with_title_and_no_gallery(self):
        """text_gallery_expanded with title but no gallery items must be deliverable."""
        _, metadata = self._run_text_gallery_expanded(gallery_count=0)
        assert metadata["degraded"] is False
        assert metadata["structure_complete"] is True
        assert metadata["deliverable"] is True

    def test_text_gallery_expanded_deliverable_with_title_and_gallery(self):
        """text_gallery_expanded with title and 4 gallery items must be deliverable."""
        _, metadata = self._run_text_gallery_expanded(gallery_count=4)
        assert metadata["degraded"] is False
        assert metadata["structure_complete"] is True
        assert metadata["deliverable"] is True

    def test_text_gallery_expanded_diagnostics_all_present(self):
        """All four bottom diagnostic fields must be present in text_gallery_expanded."""
        _, metadata = self._run_text_gallery_expanded(gallery_count=2)
        review = metadata["bottom_contract_review"]
        assert review["requested_bottom_mode"] == "text_gallery_expanded"
        assert review["effective_bottom_mode"] == "text_gallery_expanded"
        assert review["bottom_layout_mode"] == "text_gallery_expanded"
        assert "bottom_mode_override_reason" in review


class TestProductOwnerSurfaceFreeze:
    """PR-3: product owner surfaces and dual-image geometry are frozen contracts."""

    EXPECTED_OWNER_SURFACES = {
        "product_canvas_shell_layer",
        "product_primary_slot",
        "product_secondary_slot",
        "product_image_layer",
        "product_secondary_image_layer",
        "product_annotation_shell_layer",
        "product_annotation_items_layer",
    }

    def test_owner_surfaces_constant_is_frozen(self):
        """_FROZEN_PRODUCT_OWNER_SURFACES must be a frozenset with exactly the 7 surfaces."""
        from app.services.poster2.template_behavior import _FROZEN_PRODUCT_OWNER_SURFACES
        assert isinstance(_FROZEN_PRODUCT_OWNER_SURFACES, frozenset)
        assert _FROZEN_PRODUCT_OWNER_SURFACES == self.EXPECTED_OWNER_SURFACES

    def test_annotation_owner_slot_constant(self):
        """_PRODUCT_ANNOTATION_OWNER_SLOT must always be product_primary_slot."""
        from app.services.poster2.template_behavior import _PRODUCT_ANNOTATION_OWNER_SLOT
        assert _PRODUCT_ANNOTATION_OWNER_SLOT == "product_primary_slot"

    def test_product_contract_review_lists_all_owner_surfaces(self):
        """product_contract_review must expose owner_surfaces with all 7 frozen surfaces."""
        template = _load_template()
        spec = _make_spec()
        _, metadata = _run_pipeline_with_stored_metadata(template, spec)
        review = metadata["product_contract_review"]

        assert "owner_surfaces" in review
        assert set(review["owner_surfaces"]) == self.EXPECTED_OWNER_SURFACES

    def test_annotation_owner_slot_in_contract_review(self):
        """product_contract_review must expose annotation_owner_slot = product_primary_slot."""
        template = _load_template()
        spec = _make_spec()
        _, metadata = _run_pipeline_with_stored_metadata(template, spec)
        review = metadata["product_contract_review"]

        assert review["annotation_owner_slot"] == "product_primary_slot"

    def test_secondary_slot_annotation_ownership_is_false(self):
        """product_contract_review must assert secondary_slot_annotation_ownership = False."""
        template = _load_template()
        spec = _make_spec(product_secondary_image=AssetRef(url="mock://product-secondary"))
        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            product_secondary=PILImage.new("RGBA", (320, 320), (50, 120, 220, 255)),
        )
        _, metadata = _run_pipeline_with_stored_metadata(template, spec, assets=assets)
        review = metadata["product_contract_review"]

        assert review["secondary_slot_annotation_ownership"] is False
        # Even in dual mode, annotation owner is still primary slot
        assert review["annotation_owner_slot"] == "product_primary_slot"

    def test_geometry_frozen_flag_in_contract_review(self):
        """product_contract_review must expose geometry_frozen = True."""
        template = _load_template()
        spec = _make_spec()
        _, metadata = _run_pipeline_with_stored_metadata(template, spec)
        review = metadata["product_contract_review"]

        assert review["geometry_frozen"] is True

    def test_v2_geometry_constants_are_final(self):
        """Dual-mode slot bounds must match the frozen primary_secondary_dual_v2 values."""
        from app.services.poster2.template_behavior import (
            _PRODUCT_DUAL_PRIMARY_SLOT,
            _PRODUCT_DUAL_SECONDARY_SLOT,
            _PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT,
        )
        # Primary slot: upper 310px of product region
        assert _PRODUCT_DUAL_PRIMARY_SLOT == {"x": 456, "y": 188, "w": 300, "h": 310}
        # Secondary slot: 210px, 20px gap below primary (y=518)
        assert _PRODUCT_DUAL_SECONDARY_SLOT == {"x": 456, "y": 518, "w": 300, "h": 210}
        # Single-primary fallback: full 540px product region
        assert _PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT == {"x": 456, "y": 188, "w": 300, "h": 540}
        # Verify no vertical overlap: primary bottom (188+310=498) < secondary top (518)
        assert _PRODUCT_DUAL_PRIMARY_SLOT["y"] + _PRODUCT_DUAL_PRIMARY_SLOT["h"] < _PRODUCT_DUAL_SECONDARY_SLOT["y"]

    def test_single_primary_activates_when_no_secondary_asset(self):
        """single_primary mode when secondary asset is absent (runtime freeze rule)."""
        template = _load_template()
        spec = _make_spec()  # no product_secondary_image
        _, metadata = _run_pipeline_with_stored_metadata(template, spec)
        review = metadata["product_contract_review"]

        assert review["product_layout_mode"] == "single_primary"
        assert review["product_secondary_slot"] is None
        assert review["product_secondary_slot_rendered"] is False
        assert review["geometry_frozen"] is True

    def test_primary_secondary_dual_activates_when_secondary_asset_present(self):
        """primary_secondary_dual activates automatically when secondary asset exists (runtime freeze rule)."""
        template = _load_template()
        spec = _make_spec(product_secondary_image=AssetRef(url="mock://product-secondary"))
        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            product_secondary=PILImage.new("RGBA", (320, 320), (50, 120, 220, 255)),
        )
        _, metadata = _run_pipeline_with_stored_metadata(template, spec, assets=assets)
        review = metadata["product_contract_review"]

        assert review["product_layout_mode"] == "primary_secondary_dual"
        assert review["product_geometry_mode"] == "primary_secondary_dual_v2"
        assert review["geometry_frozen"] is True
        assert review["product_secondary_slot_rendered"] is True
        assert review["secondary_slot_annotation_ownership"] is False


# ---------------------------------------------------------------------------
# Task-2: Final product region geometry from v2 healthy baseline
# ---------------------------------------------------------------------------

class TestTask2FinalProductGeometry:
    """Task-2: product region geometry finalized from primary_secondary_dual_v2 healthy baseline.

    Lane model: external right lane — annotation labels (x=784+) sit outside the
    product region right boundary (x=756). Image-slot sizing is fully independent
    of label_bounds.

    Frozen geometry:
    - product_region outer shell: {x:456, y:188, w:300, h:540}
    - product_primary_slot:       {x:456, y:188, w:300, h:310}  (unchanged)
    - product_secondary_slot:     {x:456, y:518, w:300, h:210}  (gap: 20px)
    - single_primary fallback:    {x:456, y:188, w:300, h:540}
    """

    def test_product_region_outer_shell_enlarged_to_540(self):
        """product_region h must be 540 (up from 520)."""
        from app.services.poster2.template_behavior import _PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT
        assert _PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT["h"] == 540

    def test_primary_secondary_gap_is_20px(self):
        """Gap between primary bottom and secondary top must be 20px."""
        from app.services.poster2.template_behavior import (
            _PRODUCT_DUAL_PRIMARY_SLOT,
            _PRODUCT_DUAL_SECONDARY_SLOT,
        )
        primary_bottom = _PRODUCT_DUAL_PRIMARY_SLOT["y"] + _PRODUCT_DUAL_PRIMARY_SLOT["h"]
        secondary_top = _PRODUCT_DUAL_SECONDARY_SLOT["y"]
        assert secondary_top - primary_bottom == 20

    def test_secondary_slot_h_enlarged_to_210(self):
        """product_secondary_slot h must be 210 (up from 202)."""
        from app.services.poster2.template_behavior import _PRODUCT_DUAL_SECONDARY_SLOT
        assert _PRODUCT_DUAL_SECONDARY_SLOT["h"] == 210

    def test_secondary_slot_y_updated(self):
        """product_secondary_slot y must be 518 (updated for 20px gap)."""
        from app.services.poster2.template_behavior import _PRODUCT_DUAL_SECONDARY_SLOT
        assert _PRODUCT_DUAL_SECONDARY_SLOT["y"] == 518

    def test_annotation_lane_is_external_label_bounds_outside_product_region(self):
        """Annotation label x=784 must be outside product_region right boundary (x+w=756)."""
        from app.services.poster2.template_behavior import _PRODUCT_DUAL_PRIMARY_SLOT
        product_right = _PRODUCT_DUAL_PRIMARY_SLOT["x"] + _PRODUCT_DUAL_PRIMARY_SLOT["w"]  # 756
        label_x = 784  # frozen in template spec
        assert label_x > product_right, (
            f"label_x ({label_x}) must be outside product right boundary ({product_right})"
        )

    def test_annotation_ownership_unchanged(self):
        """annotation_owner_slot must remain product_primary_slot after geometry change."""
        from app.services.poster2.template_behavior import _PRODUCT_ANNOTATION_OWNER_SLOT
        assert _PRODUCT_ANNOTATION_OWNER_SLOT == "product_primary_slot"

    def test_primary_slot_unchanged(self):
        """primary slot dimensions must be unchanged by Task-2 geometry decision."""
        from app.services.poster2.template_behavior import _PRODUCT_DUAL_PRIMARY_SLOT
        assert _PRODUCT_DUAL_PRIMARY_SLOT == {"x": 456, "y": 188, "w": 300, "h": 310}

    def test_geometry_is_internally_consistent(self):
        """primary h + gap + secondary h must equal product_region h."""
        from app.services.poster2.template_behavior import (
            _PRODUCT_DUAL_PRIMARY_SLOT,
            _PRODUCT_DUAL_SECONDARY_SLOT,
            _PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT,
        )
        gap = _PRODUCT_DUAL_SECONDARY_SLOT["y"] - (
            _PRODUCT_DUAL_PRIMARY_SLOT["y"] + _PRODUCT_DUAL_PRIMARY_SLOT["h"]
        )
        total = _PRODUCT_DUAL_PRIMARY_SLOT["h"] + gap + _PRODUCT_DUAL_SECONDARY_SLOT["h"]
        assert total == _PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT["h"]


# ---------------------------------------------------------------------------
# PR-4: Text ownership freeze and feature delegation
# ---------------------------------------------------------------------------

class TestTextOwnershipFreeze:
    """PR-4: text layer owner surfaces and feature delegation are frozen contracts.

    Validates:
    - _TEXT_LAYER_OWNER_MAP declares canonical owner_region for each text layer
    - _FROZEN_PRODUCT_ANNOTATION_SLOT_IDS names exactly the 3 annotation slots
    - _PRODUCT_ANNOTATION_TEXT_OWNER_REGION is product_region
    - each text layer emits owner_region from the frozen constant (not inlined)
    - each text layer emits ownership_frozen = True
    - when annotation active: feature_view_mode = delegated_diagnostic
    - when annotation active: no dual ownership; feature_region visible_item_count = 0
    - product_annotation_contract_review emits annotation_text_owner_region + slot IDs
    """

    def test_text_layer_owner_map_constant_shape(self):
        """_TEXT_LAYER_OWNER_MAP must declare all three text layers with correct owners."""
        from app.services.poster2.template_behavior import _TEXT_LAYER_OWNER_MAP
        assert isinstance(_TEXT_LAYER_OWNER_MAP, dict)
        assert _TEXT_LAYER_OWNER_MAP["header_text_layer"] == "header_region"
        assert _TEXT_LAYER_OWNER_MAP["title_text_layer"] == "title_band_region"
        assert _TEXT_LAYER_OWNER_MAP["subtitle_text_layer"] == "title_band_region"

    def test_frozen_annotation_slot_ids_constant(self):
        """_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS must be a tuple of exactly 3 slot IDs."""
        from app.services.poster2.template_behavior import _FROZEN_PRODUCT_ANNOTATION_SLOT_IDS
        assert isinstance(_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS, tuple)
        assert len(_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS) == 3
        assert _FROZEN_PRODUCT_ANNOTATION_SLOT_IDS == (
            "product_annotation_slot_1",
            "product_annotation_slot_2",
            "product_annotation_slot_3",
        )

    def test_product_annotation_text_owner_region_constant(self):
        """_PRODUCT_ANNOTATION_TEXT_OWNER_REGION must be product_region."""
        from app.services.poster2.template_behavior import _PRODUCT_ANNOTATION_TEXT_OWNER_REGION
        assert _PRODUCT_ANNOTATION_TEXT_OWNER_REGION == "product_region"

    def test_title_text_layer_ownership_frozen(self):
        """title_text_layer must emit owner_region from frozen map and ownership_frozen = True."""
        template = _load_template()
        spec = _make_spec(title="Test title", subtitle="Test subtitle")
        _, metadata = _run_pipeline_with_stored_metadata(template, spec)
        layer = metadata["title_text_layer"]
        assert layer["owner_region"] == "title_band_region"
        assert layer["ownership_frozen"] is True

    def test_subtitle_text_layer_ownership_frozen(self):
        """subtitle_text_layer must emit owner_region from frozen map and ownership_frozen = True."""
        template = _load_template()
        spec = _make_spec(title="Test title", subtitle="Test subtitle")
        _, metadata = _run_pipeline_with_stored_metadata(template, spec)
        layer = metadata["subtitle_text_layer"]
        assert layer["owner_region"] == "title_band_region"
        assert layer["ownership_frozen"] is True

    def test_header_text_layer_ownership_frozen(self):
        """header_text_layer must emit owner_region from frozen map and ownership_frozen = True."""
        template = _load_template()
        spec = _make_spec(brand_name="TestBrand", agent_name="TestAgent")
        _, metadata = _run_pipeline_with_stored_metadata(template, spec)
        layer = metadata["header_text_layer"]
        assert layer["owner_region"] == "header_region"
        assert layer["ownership_frozen"] is True

    def test_feature_view_mode_is_delegated_diagnostic_when_annotation_active(self):
        """When product_annotation_mode is active, feature_contract_review must have
        feature_view_mode = delegated_diagnostic and feature_region visible_item_count = 0."""
        template = _load_template()
        spec = _make_spec(features=("Feature 1", "Feature 2", "Feature 3"))
        _, metadata = _run_pipeline_with_stored_metadata(template, spec)
        feature_review = metadata["feature_contract_review"]
        # Template default is product_anchor_callouts → annotation active
        assert feature_review["delegated_to_product_annotation"] is True
        assert feature_review["feature_view_mode"] == "delegated_diagnostic"
        assert feature_review["feature_region"]["visible_item_count"] == 0

    def test_feature_view_mode_is_owner_when_annotation_not_active(self):
        """When annotation is not active, feature_view_mode must be owner."""
        template = _load_template()
        template.behavior_modes = replace(
            template.behavior_modes, feature_mode="count_driven_callout_stack"
        )
        spec = _make_spec(features=("Feature 1", "Feature 2"))
        _, metadata = _run_pipeline_with_stored_metadata(template, spec)
        feature_review = metadata["feature_contract_review"]
        assert feature_review["delegated_to_product_annotation"] is False
        assert feature_review["feature_view_mode"] == "owner"

    def test_no_dual_ownership_when_annotation_active(self):
        """When annotation is active, feature_region must not claim rendered ownership."""
        template = _load_template()
        spec = _make_spec(features=("Feature 1", "Feature 2"))
        _, metadata = _run_pipeline_with_stored_metadata(template, spec)
        feature_review = metadata["feature_contract_review"]
        annotation_review = metadata["product_annotation_contract_review"]
        # feature_region does not render; product_region is sole owner
        assert feature_review["feature_region"]["visible_item_count"] == 0
        assert annotation_review["annotation_active"] is True
        assert annotation_review["annotation_text_owner_region"] == "product_region"
        # No duplicate rendered evidence: feature_contract_review has empty rendered_feature_items
        assert feature_review["rendered_feature_items"] == []

    def test_annotation_contract_review_emits_frozen_slot_ids(self):
        """product_annotation_contract_review must expose annotation_slot_ids from frozen constant."""
        template = _load_template()
        spec = _make_spec(features=("Feature 1", "Feature 2", "Feature 3"))
        _, metadata = _run_pipeline_with_stored_metadata(template, spec)
        review = metadata["product_annotation_contract_review"]
        assert review["annotation_active"] is True
        assert review["annotation_slot_ids"] == [
            "product_annotation_slot_1",
            "product_annotation_slot_2",
            "product_annotation_slot_3",
        ]
        assert review["annotation_text_owner_region"] == "product_region"
        assert review["ownership_frozen"] is True


class TestPostFreezeTextCapacity:
    """PR-5: post-freeze text capacity optimizations.

    Validates that char_budget floors are raised to match the expanded shell
    geometry (title_gallery_split at y=640 = 384px; product annotation label
    box w=144; header agent slot w=228).  All assertions are floor checks so
    future upward tuning does not break them.
    """

    # --- title_gallery_split (text_gallery_expanded) capacity ---

    def test_title_gallery_split_dense_quad_title_budget_raised(self):
        """Dense-quad title_gallery_split must reach title_char_budget >= 52."""
        from app.services.poster2.template_behavior import resolve_bottom_behavior
        policy = resolve_bottom_behavior(
            "title_gallery_split",
            gallery_mode="strip_local_visible_only",
            title_text="Upgrade your kitchen with ChefCraft Pro",
            subtitle_text="Available in stores from April 24th",
            requested_gallery_count=4,
            normalized_gallery_count=4,
            resolved_gallery_count=4,
            max_items=4,
        )
        assert policy.title_char_budget >= 52
        assert policy.subtitle_char_budget >= 44

    def test_title_gallery_split_triplet_title_budget_raised(self):
        """Triplet title_gallery_split must reach title_char_budget >= 60."""
        from app.services.poster2.template_behavior import resolve_bottom_behavior
        policy = resolve_bottom_behavior(
            "title_gallery_split",
            gallery_mode="strip_local_visible_only",
            title_text="Upgrade your kitchen with ChefCraft Pro",
            subtitle_text="Available in stores from April 24th",
            requested_gallery_count=3,
            normalized_gallery_count=3,
            resolved_gallery_count=3,
            max_items=4,
        )
        assert policy.title_char_budget >= 60
        assert policy.subtitle_char_budget >= 52

    def test_title_gallery_split_light_gallery_title_budget_raised(self):
        """Light-gallery (1-2 items) title_gallery_split must reach title_char_budget >= 72."""
        from app.services.poster2.template_behavior import resolve_bottom_behavior
        policy = resolve_bottom_behavior(
            "title_gallery_split",
            gallery_mode="strip_local_visible_only",
            title_text="Upgrade your kitchen with ChefCraft Pro",
            subtitle_text="Available in stores from April 24th",
            requested_gallery_count=2,
            normalized_gallery_count=2,
            resolved_gallery_count=2,
            max_items=4,
        )
        assert policy.title_char_budget >= 72
        assert policy.subtitle_char_budget >= 56

    def test_title_gallery_split_compact_title_budget_raised(self):
        """Compact title_gallery_split (short title, no subtitle) must reach title_char_budget >= 52."""
        from app.services.poster2.template_behavior import resolve_bottom_behavior
        policy = resolve_bottom_behavior(
            "title_gallery_split",
            gallery_mode="strip_local_visible_only",
            title_text="Short",
            subtitle_text=None,
            requested_gallery_count=2,
            normalized_gallery_count=2,
            resolved_gallery_count=2,
            max_items=4,
        )
        assert policy.title_char_budget >= 52

    # --- product annotation capacity ---

    def test_product_annotation_char_budget_raised_three_items(self):
        """product_anchor_callouts with 3 items must reach char_budget >= 28."""
        from app.services.poster2.template_behavior import resolve_product_behavior, resolve_hero_behavior
        from app.services.poster2.contracts import TemplateSpec
        template = _load_template()
        hero = resolve_hero_behavior("scenario_cover_product_contain")
        policy = resolve_product_behavior(
            template,
            annotation_mode="product_anchor_callouts",
            product_layout_mode="single_primary",
            has_product_secondary_asset=False,
            requested_feature_count=3,
            hero_policy=hero,
        )
        assert policy.char_budget >= 28

    def test_product_annotation_char_budget_raised_two_items(self):
        """product_anchor_callouts with 2 items must reach char_budget >= 34."""
        from app.services.poster2.template_behavior import resolve_product_behavior, resolve_hero_behavior
        template = _load_template()
        hero = resolve_hero_behavior("scenario_cover_product_contain")
        policy = resolve_product_behavior(
            template,
            annotation_mode="product_anchor_callouts",
            product_layout_mode="single_primary",
            has_product_secondary_asset=False,
            requested_feature_count=2,
            hero_policy=hero,
        )
        assert policy.char_budget >= 34

    def test_product_annotation_char_budget_raised_one_item(self):
        """product_anchor_callouts with 1 item must reach char_budget >= 40."""
        from app.services.poster2.template_behavior import resolve_product_behavior, resolve_hero_behavior
        template = _load_template()
        hero = resolve_hero_behavior("scenario_cover_product_contain")
        policy = resolve_product_behavior(
            template,
            annotation_mode="product_anchor_callouts",
            product_layout_mode="single_primary",
            has_product_secondary_asset=False,
            requested_feature_count=1,
            hero_policy=hero,
        )
        assert policy.char_budget >= 40

    # --- header agent capacity ---

    def test_header_agent_char_budget_raised_identity_left_agent_right(self):
        """identity_left_agent_right agent_char_budget must reach >= 28."""
        from app.services.poster2.template_behavior import resolve_header_behavior
        policy = resolve_header_behavior(
            "identity_left_agent_right",
            brand_name="TestBrand",
            agent_name="Agent Name That Is Longer",
        )
        assert policy.agent_char_budget >= 28

    def test_header_agent_char_budget_raised_brand_block_two_line(self):
        """brand_block_two_line agent_char_budget must reach >= 28."""
        from app.services.poster2.template_behavior import resolve_header_behavior
        policy = resolve_header_behavior(
            "brand_block_two_line",
            brand_name="TestBrand",
            agent_name="Agent Name That Is Longer",
        )
        assert policy.agent_char_budget >= 28

    def test_header_agent_budget_truncates_longer_name_at_new_floor(self):
        """Agent name longer than 28 chars must be truncated at the new budget floor."""
        from app.services.poster2.pipeline import _apply_text_budget
        from app.services.poster2.template_behavior import resolve_header_behavior
        policy = resolve_header_behavior(
            "identity_left_agent_right",
            brand_name="TestBrand",
            agent_name="A" * 40,
        )
        excerpt = _apply_text_budget("A" * 40, policy.agent_char_budget)
        assert len(excerpt) == policy.agent_char_budget
class TestProductImageContract:
    """PR-7: Product image contract — bounds and fit authoritative from product_policy.

    Verifies that:
    - product_policy.product_primary_image_fit is declared and correct
    - product_contract_review exposes product_primary_image_fit
    - product_annotation_contract_review product_region.bounds come from product_policy
    - renderer uses product_policy.product_primary_slot bounds for single_primary
    """

    def test_resolve_product_behavior_declares_product_primary_image_fit(self):
        """resolve_product_behavior must set product_primary_image_fit from hero_policy."""
        from app.services.poster2.template_behavior import (
            resolve_product_behavior, resolve_hero_behavior
        )
        template = _load_template()
        hero = resolve_hero_behavior("scenario_cover_product_contain")
        policy = resolve_product_behavior(
            template,
            annotation_mode="none",
            product_layout_mode="single_primary",
            has_product_secondary_asset=False,
            requested_feature_count=0,
            hero_policy=hero,
        )
        assert policy.product_primary_image_fit == "contain"
        assert policy.product_primary_image_fit == hero.product_fit

    def test_product_primary_image_fit_present_in_product_contract_review(self):
        """product_contract_review must expose product_primary_image_fit at root level."""
        template = _load_template()
        spec = _make_spec()
        _, metadata = _run_pipeline_with_stored_metadata(template, spec)
        review = metadata["product_contract_review"]

        assert "product_primary_image_fit" in review
        assert review["product_primary_image_fit"] == "contain"

    def test_annotation_contract_review_product_region_bounds_from_product_policy(self):
        """product_annotation_contract_review product_region.bounds must come from product_policy, not hero_policy."""
        from app.services.poster2.template_behavior import (
            resolve_product_behavior, resolve_hero_behavior,
        )
        template = _load_template()
        spec = _make_spec(features=("卖点A", "卖点B", "卖点C"))
        _, metadata = _run_pipeline_with_stored_metadata(template, spec)
        annotation_review = metadata["product_annotation_contract_review"]
        hero = resolve_hero_behavior("scenario_cover_product_contain")
        product_policy = resolve_product_behavior(
            template,
            annotation_mode="product_anchor_callouts",
            product_layout_mode="single_primary",
            has_product_secondary_asset=False,
            requested_feature_count=3,
            hero_policy=hero,
        )

        bounds = annotation_review["product_region"]["bounds"]
        assert bounds == {
            "x": int(product_policy.layout_metrics["product_region_x"]),
            "y": int(product_policy.layout_metrics["product_region_y"]),
            "w": int(product_policy.layout_metrics["product_region_w"]),
            "h": int(product_policy.layout_metrics["product_region_h"]),
        }

    def test_product_primary_slot_bounds_match_single_primary_constant(self):
        """In single_primary mode, product_primary_slot must match _PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT."""
        from app.services.poster2.template_behavior import (
            _PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT,
            resolve_product_behavior, resolve_hero_behavior,
        )
        template = _load_template()
        hero = resolve_hero_behavior("scenario_cover_product_contain")
        policy = resolve_product_behavior(
            template,
            annotation_mode="none",
            product_layout_mode="single_primary",
            has_product_secondary_asset=False,
            requested_feature_count=0,
            hero_policy=hero,
        )
        assert policy.product_primary_slot == _PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT
        assert policy.product_primary_slot["x"] == 456
        assert policy.product_primary_slot["y"] == 188
        assert policy.product_primary_slot["w"] == _PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT["w"]
        assert policy.product_primary_slot["h"] == _PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT["h"]

    def test_product_primary_image_fit_consistent_with_hero_fit_for_both_hero_modes(self):
        """product_primary_image_fit must equal hero_policy.product_fit for both hero modes."""
        from app.services.poster2.template_behavior import (
            resolve_product_behavior, resolve_hero_behavior
        )
        template = _load_template()
        for hero_mode in ("scenario_cover_product_contain", "single_product_focus"):
            hero = resolve_hero_behavior(hero_mode)
            policy = resolve_product_behavior(
                template,
                annotation_mode="none",
                product_layout_mode="single_primary",
                has_product_secondary_asset=False,
                requested_feature_count=0,
                hero_policy=hero,
            )
            assert policy.product_primary_image_fit == hero.product_fit, f"Mismatch for hero_mode={hero_mode}"
            assert policy.product_primary_image_fit == "contain"
