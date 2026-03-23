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
from app.services.poster2.renderer import LayoutRenderer


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
        def fake_put_bytes(key, data, **kw):
            if "/fg/" in key:
                return "https://r2.example.com/fg.png"
            if "product-material" in key:
                return "https://r2.example.com/product-material.png"
            if "slot-structure" in key:
                return "https://r2.example.com/slot-structure.png"
            if "content-layer" in key:
                return "https://r2.example.com/content-layer.png"
            if "text-layer" in key:
                return "https://r2.example.com/text-layer.png"
            if "structure-overlay" in key:
                return "https://r2.example.com/structure-overlay.png"
            if "slot-metadata" in key:
                return "https://r2.example.com/slot-metadata.json"
            if "debug/metadata" in key:
                return "https://r2.example.com/renderer-metadata.json"
            return "https://r2.example.com/final.png"

        assets = _make_assets() if product_override is None else ResolvedAssets(product=product_override)

        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=LayoutRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=MagicMock(side_effect=fake_put_bytes),
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
        assert manifest.debug_artifacts.slot_structure_layer_url == "https://r2.example.com/slot-structure.png"
        assert manifest.debug_artifacts.content_layer_url == "https://r2.example.com/content-layer.png"
        assert manifest.debug_artifacts.text_layer_url == "https://r2.example.com/text-layer.png"
        assert manifest.debug_artifacts.structure_overlay_url == "https://r2.example.com/structure-overlay.png"
        assert manifest.debug_artifacts.slot_metadata_url == "https://r2.example.com/slot-metadata.json"

    def test_manifest_hashes_set(self):
        manifest = self._run(_make_spec())
        assert len(manifest.final_hash) == 64  # SHA256 hex
        assert len(manifest.foreground_hash) == 64

    def test_background_metadata(self):
        manifest = self._run(_make_spec())
        assert manifest.background_seed == 42
        assert manifest.background_model == "firefly-v3"
        assert manifest.template_version == "2.1.2"
        assert manifest.template_contract_version == "poster2.template_dual_v2.v1"
        assert manifest.engine_version == "2.0.0"
        assert manifest.render_engine_used == "pillow"
        assert manifest.renderer_mode == "auto"
        assert manifest.foreground_renderer == "poster2.pillow_layout"
        assert manifest.background_renderer == "firefly-v3"
        assert manifest.debug_artifacts.background_layer_url == "https://r2.example.com/bg.png"
        assert manifest.debug_artifacts.foreground_layer_url == "https://r2.example.com/fg.png"
        assert manifest.debug_artifacts.final_composited_url == "https://r2.example.com/final.png"
        assert manifest.debug_artifacts.slot_structure_layer_url == "https://r2.example.com/slot-structure.png"
        assert manifest.debug_artifacts.content_layer_url == "https://r2.example.com/content-layer.png"
        assert manifest.debug_artifacts.text_layer_url == "https://r2.example.com/text-layer.png"
        assert manifest.debug_artifacts.structure_overlay_url == "https://r2.example.com/structure-overlay.png"
        assert manifest.debug_artifacts.slot_metadata_url == "https://r2.example.com/slot-metadata.json"

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
            side_effect=lambda key, data, **kw: (
                "https://r2.example.com/fg.png" if "/fg/" in key else
                "https://r2.example.com/product-material.png" if "product-material" in key else
                "https://r2.example.com/slot-structure.png" if "slot-structure" in key else
                "https://r2.example.com/content-layer.png" if "content-layer" in key else
                "https://r2.example.com/text-layer.png" if "text-layer" in key else
                "https://r2.example.com/structure-overlay.png" if "structure-overlay" in key else
                "https://r2.example.com/slot-metadata.json" if "slot-metadata" in key else
                "https://r2.example.com/renderer-metadata.json" if "debug/metadata" in key else
                "https://r2.example.com/final.png"
            )
        )
        pipeline = PosterPipeline(
            background_svc=bg_service,
            renderer=LayoutRenderer(),
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
            if "product-material" in key:
                return "https://r2.example.com/product-material.png"
            if "slot-structure" in key:
                return "https://r2.example.com/slot-structure.png"
            if "content-layer" in key:
                return "https://r2.example.com/content-layer.png"
            if "text-layer" in key:
                return "https://r2.example.com/text-layer.png"
            if "structure-overlay" in key:
                return "https://r2.example.com/structure-overlay.png"
            if "/fg/" in key:
                return "https://r2.example.com/fg.png"
            if "slot-metadata" in key:
                return "https://r2.example.com/slot-metadata.json"
            if "debug/metadata" in key:
                return "https://r2.example.com/renderer-metadata.json"
            return "https://r2.example.com/final.png"

        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            scenario=None,
            gallery=[],
        )
        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=LayoutRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=fake_put_bytes,
        )

        manifest = asyncio.run(pipeline.run(_make_spec(), template))

        assert manifest.debug_artifacts.renderer_metadata_url == "https://r2.example.com/renderer-metadata.json"
        metadata_key = next(key for key in stored_payloads if "debug/metadata" in key)
        metadata = json.loads(stored_payloads[metadata_key].decode("utf-8"))
        layer_status = metadata["layer_render_status"]
        assert layer_status["brand_logo_layer"]["rendered"] is False
        assert layer_status["brand_logo_layer"]["reason_code"] == "logo_missing"
        assert layer_status["scenario_image_layer"]["rendered"] is True
        assert layer_status["scenario_image_layer"]["reason_code"] == "safe_preset_fill"
        assert layer_status["scenario_image_layer"]["source_binding"] == "safe_preset_image"
        assert layer_status["bottom_gallery_items_layer"]["rendered"] is False
        assert layer_status["bottom_gallery_items_layer"]["reason_code"] == "gallery_empty"
        assert layer_status["bottom_gallery_items_layer"]["count"] == 0
        assert layer_status["bottom_tagline_layer"]["reason_code"] == "operator_tagline_unbound"
        assert metadata["artifact_urls"]["slot_structure_layer_url"] == "https://r2.example.com/slot-structure.png"
        assert metadata["artifact_urls"]["slot_metadata_url"] == "https://r2.example.com/slot-metadata.json"
        slot_metadata_key = next(key for key in stored_payloads if "slot-metadata" in key)
        slot_metadata = json.loads(stored_payloads[slot_metadata_key].decode("utf-8"))
        brand_logo_slot = slot_metadata["regions"]["header_region"]["brand_logo_slot"]
        assert brand_logo_slot["expected"] is False
        assert brand_logo_slot["bound"] is False
        assert brand_logo_slot["rendered"] is False
        assert brand_logo_slot["mode"] == "hidden"
        assert brand_logo_slot["reason"] == "logo_not_bound"

        scenario_slot = slot_metadata["regions"]["scenario_region"]["scenario_image_slot"]
        assert scenario_slot["expected"] is True
        assert scenario_slot["bound"] is False
        assert scenario_slot["rendered"] is True
        assert scenario_slot["mode"] == "safe-preset-fill"
        assert scenario_slot["reason"] == "scenario_image_missing"

        gallery_slots = slot_metadata["regions"]["bottom_region"]["gallery_item_slots"]
        assert gallery_slots["expected"] is False
        assert gallery_slots["bound"] is False
        assert gallery_slots["rendered"] is False
        assert gallery_slots["mode"] == "hide"
        assert gallery_slots["reason"] == "gallery_hidden_no_assets"

    def test_slot_metadata_marks_gallery_fallback_fill_when_partial_assets_exist(self):
        template = _load_template()
        stored_payloads: dict[str, bytes] = {}

        def fake_put_bytes(key, data, **kwargs):
            stored_payloads[key] = data
            if "product-material" in key:
                return "https://r2.example.com/product-material.png"
            if "slot-structure" in key:
                return "https://r2.example.com/slot-structure.png"
            if "content-layer" in key:
                return "https://r2.example.com/content-layer.png"
            if "text-layer" in key:
                return "https://r2.example.com/text-layer.png"
            if "structure-overlay" in key:
                return "https://r2.example.com/structure-overlay.png"
            if "/fg/" in key:
                return "https://r2.example.com/fg.png"
            if "slot-metadata" in key:
                return "https://r2.example.com/slot-metadata.json"
            if "debug/metadata" in key:
                return "https://r2.example.com/renderer-metadata.json"
            return "https://r2.example.com/final.png"

        spec = _make_spec(gallery_images=(AssetRef(url="mock://gallery-1"),))
        assets = ResolvedAssets(
            product=PILImage.new("RGBA", (400, 600), (200, 100, 50, 255)),
            gallery=[PILImage.new("RGBA", (176, 104), (120, 160, 200, 255))],
        )
        pipeline = PosterPipeline(
            background_svc=_mock_bg_service(),
            renderer=LayoutRenderer(),
            composer=Composer(),
            asset_loader=_mock_loader(assets),
            put_bytes_fn=fake_put_bytes,
        )

        asyncio.run(pipeline.run(spec, template))

        slot_metadata_key = next(key for key in stored_payloads if "slot-metadata" in key)
        slot_metadata = json.loads(stored_payloads[slot_metadata_key].decode("utf-8"))
        gallery_slots = slot_metadata["regions"]["bottom_region"]["gallery_item_slots"]
        assert gallery_slots["expected"] is True
        assert gallery_slots["bound"] is True
        assert gallery_slots["rendered"] is True
        assert gallery_slots["mode"] == "fallback-fill"
        assert gallery_slots["reason"] == "gallery_partial_fill"
        assert gallery_slots["count"] == 1
