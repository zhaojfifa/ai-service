"""
Unit tests for LayoutRenderer — deterministic Pillow rendering.

Key properties tested:
  1. Same inputs → bit-identical PNG bytes (determinism invariant).
  2. Output is RGBA with correct canvas size.
  3. Text slots handle empty strings, long strings, and auto_shrink.
  4. Image slots respect fit modes (contain / cover).
  5. Gallery strip positions match template spec exactly.
  6. Missing optional assets (logo, scenario, gallery) are gracefully skipped.

No network, no AI, no R2 calls.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image as PILImage

from app.services.poster2.contracts import (
    AssetRef,
    FeatureCalloutSpec,
    GalleryStripSpec,
    ImageSlotSpec,
    PosterSpec,
    ResolvedAssets,
    StyleSpec,
    TemplateSpec,
    TextSlotSpec,
)
from app.services.poster2.renderer import (
    LayoutRenderer,
    PuppeteerStructuredRenderer,
    RendererSelector,
    PuppeteerFailureInfo,
    _apply_radius,
    _wrap_text,
    _draw_pill_bg,
    _fit_image,
    ForegroundResult,
    _build_puppeteer_failure_info,
    _normalized_feature_texts,
    _resolve_feature_mode,
    _resolve_feature_callout_layout,
    _resolve_feature_callout_map,
    _product_slot,
    _product_secondary_slot,
    _safe_preset_scenario_data_url,
    _template_b_material_slots,
    _visible_gallery_item_count,
    _apply_family_a_fryer_gallery_captions,
    _prepare_gallery_urls,
)
from app.services.poster2.renderer_routing import RendererRoutingError, resolve_renderer_routing
from app.services.poster2.template_behavior import (
    resolve_bottom_behavior,
    resolve_feature_behavior,
    resolve_template_behavior,
)
from app.services.poster2.template_registry import FAMILY_B_PRODUCT_SHEET_STORY, TemplateMetadata


# ── Helpers ───────────────────────────────────────────────────────────────────

def solid_image(w: int, h: int, color=(200, 100, 50, 255)) -> PILImage.Image:
    """Create a solid-color RGBA image for testing."""
    img = PILImage.new("RGBA", (w, h), color)
    return img


def _load_real_template() -> TemplateSpec:
    p = (
        Path(__file__).resolve().parents[2]
        / "app" / "templates" / "specs" / "template_dual_v2.json"
    )
    return TemplateSpec.from_json(p)


def _load_template_b_template() -> TemplateSpec:
    p = (
        Path(__file__).resolve().parents[2]
        / "app" / "templates" / "specs" / "template_product_sheet_v1.json"
    )
    return TemplateSpec.from_json(p)


def _minimal_spec(**overrides) -> PosterSpec:
    defaults = dict(
        brand_name="厨厨房",
        agent_name="智能厨房顾问",
        title="烹饪更智慧，生活更美味",
        subtitle="系列产品",
        features=("智能温控", "语音操控", "节能环保"),
        product_image=AssetRef(url="mock://product"),
    )
    defaults.update(overrides)
    return PosterSpec(**defaults)


def _minimal_assets(**overrides) -> ResolvedAssets:
    defaults = dict(
        product=solid_image(400, 600),
    )
    defaults.update(overrides)
    return ResolvedAssets(**defaults)


def _load_fixture(name: str) -> dict:
    path = Path(__file__).resolve().parent / "fixtures" / name
    return json.loads(path.read_text(encoding="utf-8"))


# ── Determinism ───────────────────────────────────────────────────────────────

class TestDeterminism:
    """Same inputs MUST produce bit-identical PNG output."""

    def test_identical_runs(self):
        template = _load_real_template()
        spec = _minimal_spec()
        assets = _minimal_assets()

        renderer = LayoutRenderer()
        r1 = renderer.render(template, spec, assets)
        r2 = renderer.render(template, spec, assets)

        assert r1.sha256 == r2.sha256, "Renderer is not deterministic!"
        assert r1.png_bytes == r2.png_bytes

    def test_different_title_changes_hash(self):
        template = _load_real_template()
        renderer = LayoutRenderer()

        r1 = renderer.render(template, _minimal_spec(title="AAA"), _minimal_assets())
        r2 = renderer.render(template, _minimal_spec(title="BBB"), _minimal_assets())

        assert r1.sha256 != r2.sha256


# ── Canvas output ─────────────────────────────────────────────────────────────

class TestCanvasOutput:

    def test_output_size_matches_template(self):
        template = _load_real_template()
        result = LayoutRenderer().render(template, _minimal_spec(), _minimal_assets())
        assert result.image.size == (template.canvas_w, template.canvas_h)

    def test_output_mode_is_rgba(self):
        template = _load_real_template()
        result = LayoutRenderer().render(template, _minimal_spec(), _minimal_assets())
        assert result.image.mode == "RGBA"

    def test_png_bytes_not_empty(self):
        template = _load_real_template()
        result = LayoutRenderer().render(template, _minimal_spec(), _minimal_assets())
        assert len(result.png_bytes) > 1000  # real PNG, not empty

    def test_pillow_draws_header_shell_surface(self):
        template = _load_real_template()
        result = LayoutRenderer().render(template, _minimal_spec(), _minimal_assets())

        assert result.image.getpixel((80, 70))[3] > 0

    def test_pillow_beauty_tokens_change_shell_presentation(self):
        template = _load_real_template()
        baseline = LayoutRenderer().render(template, _minimal_spec(), _minimal_assets())
        template.beauty_tokens = replace(
            template.beauty_tokens,
            shell_surface="panel_dark_soft",
            shell_border="clean_frame",
            shell_shadow="medium",
            accent_tone="cool_blue",
            text_emphasis="high_contrast",
        )

        alternate = LayoutRenderer().render(template, _minimal_spec(), _minimal_assets())

        assert baseline.image.getpixel((80, 70)) != alternate.image.getpixel((80, 70))


class TestTemplateBIndustrialSheet:

    def test_template_b_pillow_renderer_draws_sheet_background_and_dark_header(self):
        template = _load_template_b_template()
        spec = _minimal_spec(
            brand_name="KitchenWorks",
            agent_name="Dealer Team",
            title="Integrated Workstation Sink",
            subtitle="Precision-fitted accessories",
            features=(),
            template_id="template_product_sheet_v1",
            product_secondary_image=AssetRef(url="mock://product-secondary"),
            logo=AssetRef(url="mock://logo"),
            materials_images=(AssetRef(url="mock://mat-1"), AssetRef(url="mock://mat-2")),
            description_title="Crafted for daily production kitchens",
            description_body="Spec-sheet copy.",
            sku_text="KW-2401",
        )
        assets = ResolvedAssets(
            product=solid_image(400, 600, (220, 180, 150, 255)),
            product_secondary=solid_image(320, 320, (160, 160, 160, 255)),
            logo=solid_image(240, 128, (20, 20, 20, 255)),
            materials=[solid_image(160, 80, (120, 120, 120, 255)), solid_image(160, 80, (180, 170, 160, 255))],
        )

        result = LayoutRenderer().render(template, spec, assets)

        assert result.image.getpixel((8, 8))[3] == 255
        assert sum(result.image.getpixel((120, 84))[:3]) < 120
        assert result.image.getpixel((512, 520))[3] == 255

    def test_template_b_material_slots_center_and_enlarge_sparse_materials(self):
        template = _load_template_b_template()

        slots = _template_b_material_slots(template.materials_slot, 2)

        assert len(slots) == 2
        assert slots[0].x > template.materials_slot.x
        assert slots[0].w > template.materials_slot.thumb_w
        assert slots[1].x + slots[1].w < template.materials_slot.x + template.materials_slot.w


class TestFamilyAVisualRebaseline:

    def test_family_a_visual_smoke_hashes_match_fixture(self):
        fixture = _load_fixture("family_a_visual_smoke.json")
        template = _load_real_template()
        spec = _minimal_spec()
        assets = _minimal_assets()

        result = LayoutRenderer().render(template, spec, assets)
        assert result.sha256 == fixture["pillow_sha256"]

        renderer = PuppeteerStructuredRenderer()
        html_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.html"
        ).read_text(encoding="utf-8")
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")
        slot_spec = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "slot_spec.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        anchor_map = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "anchor_map.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        html_payload = renderer._build_html(
            html_template=html_template,
            css_template=css_template,
            svg_overlay="",
            poster=spec,
            asset_urls={
                "logo": "",
                "scenario": _safe_preset_scenario_data_url(),
                "scenario_is_real": False,
                "product": "data:image/png;base64,abc",
                "product_secondary": "",
                "gallery": [],
                "materials": [],
            },
            slot_spec=slot_spec,
            anchor_map=anchor_map,
            spec=template,
        )
        assert hashlib.sha256(html_payload.encode("utf-8")).hexdigest() == fixture["structured_html_sha256"]


# ── Optional assets ───────────────────────────────────────────────────────────

class TestOptionalAssets:

    def test_no_logo(self):
        template = _load_real_template()
        assets = _minimal_assets(logo=None)
        result = LayoutRenderer().render(template, _minimal_spec(), assets)
        assert result.image.size == (1024, 1024)

    def test_no_scenario(self):
        template = _load_real_template()
        assets = _minimal_assets(scenario=None)
        result = LayoutRenderer().render(template, _minimal_spec(), assets)
        assert result.image is not None

    def test_no_gallery(self):
        template = _load_real_template()
        assets = _minimal_assets(gallery=[])
        result = LayoutRenderer().render(template, _minimal_spec(), assets)
        assert result.image is not None

    def test_with_all_assets(self):
        template = _load_real_template()
        assets = _minimal_assets(
            logo=solid_image(136, 80, (255, 255, 255, 255)),
            scenario=solid_image(320, 600, (100, 150, 200, 255)),
            gallery=[solid_image(176, 104) for _ in range(4)],
        )
        result = LayoutRenderer().render(template, _minimal_spec(), assets)
        assert result.image.size == (1024, 1024)

    def test_single_product_focus_hero_mode_skips_scenario_render(self):
        template = _load_real_template()
        template.behavior_modes = replace(
            template.behavior_modes,
            hero_mode="single_product_focus",
        )
        assets = _minimal_assets(
            scenario=solid_image(320, 600, (100, 150, 200, 255)),
        )

        result = LayoutRenderer().render(template, _minimal_spec(), assets)

        assert result.image.getpixel((120, 220))[3] == 0
        assert result.region_render_status["scenario_region"]["rendered"] is False
        assert result.region_render_status["product_region"]["rendered"] is True

    def test_primary_secondary_dual_renders_secondary_product_slot_in_pillow(self):
        template = _load_real_template()
        spec = _minimal_spec(product_secondary_image=AssetRef(url="mock://product-secondary"))
        assets = _minimal_assets(
            product=solid_image(400, 600, (220, 80, 40, 255)),
            product_secondary=solid_image(320, 320, (40, 120, 220, 255)),
        )

        result = LayoutRenderer().render(template, spec, assets)

        assert result.image.getpixel((606, 300))[:3] == (220, 80, 40)
        assert result.image.getpixel((606, 600))[:3] == (40, 120, 220)
        assert result.layer_render_status["product_secondary_image_layer"]["rendered"] is True
        assert result.region_render_status["product_region"]["count"] == 5
        assert result.region_render_status["feature_region"]["count"] == 0


# ── Feature slots ─────────────────────────────────────────────────────────────

class TestFeatureSlots:

    def test_fewer_features_than_slots(self):
        """Only 2 features provided for 4 slots — must not raise."""
        template = _load_real_template()
        spec = _minimal_spec(features=("特性A", "特性B"))
        result = LayoutRenderer().render(template, spec, _minimal_assets())
        assert result.image is not None

    def test_empty_features(self):
        template = _load_real_template()
        spec = _minimal_spec(features=())
        result = LayoutRenderer().render(template, spec, _minimal_assets())
        assert result.image is not None


# ── Image fit utilities ───────────────────────────────────────────────────────

class TestFitImage:

    def test_contain_does_not_exceed_bounds(self):
        img = solid_image(800, 400)
        fitted = _fit_image(img, 300, 300, "contain")
        assert fitted.width <= 300
        assert fitted.height <= 300

    def test_cover_fills_bounds(self):
        img = solid_image(200, 100)
        fitted = _fit_image(img, 300, 300, "cover")
        assert fitted.width == 300
        assert fitted.height == 300

    def test_fill_stretches_to_bounds(self):
        img = solid_image(50, 200)
        fitted = _fit_image(img, 400, 400, "fill")
        assert fitted.size == (400, 400)

    def test_contain_preserves_aspect_ratio(self):
        img = solid_image(800, 400)  # 2:1 ratio
        fitted = _fit_image(img, 200, 200, "contain")
        # width should be 200, height should be 100 (maintains 2:1)
        assert fitted.width == 200
        assert fitted.height == 100

    def test_cover_output_is_rgba(self):
        img = solid_image(100, 100)
        fitted = _fit_image(img, 50, 50, "cover")
        assert fitted.mode == "RGBA"

    def test_product_anchor_bottom_keeps_contained_image_low_in_slot(self):
        canvas = PILImage.new("RGBA", (120, 120), (0, 0, 0, 0))
        product = solid_image(40, 40, (255, 0, 0, 255))
        slot = ImageSlotSpec(
            x=10,
            y=10,
            w=100,
            h=100,
            fit="contain",
            align_x="center",
            align_y="end",
            pad_top=20,
            pad_right=10,
            pad_bottom=8,
            pad_left=10,
        )

        LayoutRenderer()._draw_product(canvas, slot, product)

        assert canvas.getpixel((60, 24))[3] == 0
        assert canvas.getpixel((60, 96))[3] == 255


# ── Radius / shadow utilities ─────────────────────────────────────────────────

class TestImageEffects:

    def test_radius_produces_transparent_corners(self):
        img = solid_image(100, 100, (255, 0, 0, 255))
        result = _apply_radius(img, radius=20)
        # Top-left corner (0,0) should be transparent
        assert result.mode == "RGBA"
        pixel = result.getpixel((0, 0))
        assert pixel[3] == 0, "Corner should be transparent after radius"

    def test_radius_preserves_center(self):
        img = solid_image(100, 100, (255, 0, 0, 255))
        result = _apply_radius(img, radius=10)
        center = result.getpixel((50, 50))
        assert center[3] == 255, "Center should remain opaque"


# ── Text wrap utility ─────────────────────────────────────────────────────────

class TestWrapText:

    def _draw_stub(self):
        """Minimal ImageDraw stub to measure text."""
        from PIL import ImageDraw, ImageFont
        img = PILImage.new("RGBA", (1000, 100))
        return ImageDraw.Draw(img), ImageFont.load_default()

    def test_short_text_single_line(self):
        draw, font = self._draw_stub()
        lines = _wrap_text(draw, "Hello", font, max_width=500, max_lines=3)
        assert len(lines) == 1
        assert lines[0] == "Hello"

    def test_empty_string(self):
        draw, font = self._draw_stub()
        lines = _wrap_text(draw, "", font, max_width=500, max_lines=2)
        assert lines == []

    def test_max_lines_respected(self):
        draw, font = self._draw_stub()
        # Very narrow width forces many breaks; max_lines=2 should cap output
        long_text = " ".join(["word"] * 20)
        lines = _wrap_text(draw, long_text, font, max_width=40, max_lines=2)
        assert len(lines) <= 2


class _FakePuppeteerRenderer:
    def __init__(self, result: ForegroundResult | None = None, exc: Exception | None = None):
        self._result = result
        self._exc = exc

    async def render(self, spec, poster, assets):
        if self._exc:
            raise self._exc
        return self._result


class TestRendererSelector:

    def test_auto_uses_family_preferred_renderer_for_family_a(self):
        template = _load_real_template()
        expected = ForegroundResult(
            image=solid_image(1024, 1024),
            png_bytes=b"png",
            sha256="a" * 64,
            render_engine_used="puppeteer",
            foreground_renderer="poster2.puppeteer_structured",
            template_contract_version="poster2.template_dual_v2.v1",
        )
        selector = RendererSelector(
            pillow_renderer=LayoutRenderer(),
            puppeteer_renderer=_FakePuppeteerRenderer(result=expected),
        )

        result = asyncio.run(
            selector.render(
                template,
                _minimal_spec(renderer_mode="auto"),
                _minimal_assets(),
            )
        )

        assert result.render_engine_used == "puppeteer"
        assert result.foreground_renderer == "poster2.puppeteer_structured"

    def test_prefers_requested_puppeteer_renderer(self):
        template = _load_real_template()
        expected = ForegroundResult(
            image=solid_image(1024, 1024),
            png_bytes=b"png",
            sha256="x" * 64,
            render_engine_used="puppeteer",
            foreground_renderer="poster2.puppeteer_structured",
            template_contract_version="poster2.template_dual_v2.v1",
        )
        selector = RendererSelector(
            pillow_renderer=LayoutRenderer(),
            puppeteer_renderer=_FakePuppeteerRenderer(result=expected),
        )

        result = asyncio.run(
            selector.render(
                template,
                _minimal_spec(renderer_mode="puppeteer"),
                _minimal_assets(),
            )
        )
        assert result.render_engine_used == "puppeteer"
        assert result.foreground_renderer == "poster2.puppeteer_structured"

    def test_falls_back_to_pillow_when_puppeteer_fails(self):
        template = _load_real_template()
        selector = RendererSelector(
            pillow_renderer=LayoutRenderer(),
            puppeteer_renderer=_FakePuppeteerRenderer(exc=RuntimeError("browser missing")),
        )

        result = asyncio.run(
            selector.render(
                template,
                _minimal_spec(renderer_mode="puppeteer"),
                _minimal_assets(),
            )
        )
        assert result.render_engine_used == "pillow"
        assert result.degraded is True
        assert result.degraded_reason == "puppeteer_unknown_error"
        assert result.fallback_reason_code == "puppeteer_unknown_error"
        assert result.fallback_exception_class == "RuntimeError"
        assert result.fallback_stage == "unknown"

    def test_missing_required_input_does_not_fallback(self):
        template = _load_real_template()
        selector = RendererSelector(
            pillow_renderer=LayoutRenderer(),
            puppeteer_renderer=_FakePuppeteerRenderer(exc=RuntimeError("browser missing")),
        )

        with pytest.raises(RendererRoutingError) as excinfo:
            asyncio.run(
                selector.render(
                    template,
                    _minimal_spec(renderer_mode="puppeteer", title=""),
                    _minimal_assets(),
                )
            )

        assert excinfo.value.failure_type == "contract_input_failure"
        assert excinfo.value.reason_code == "missing_required_input"

    def test_resolve_renderer_routing_uses_family_metadata_for_family_b(self):
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

        route = resolve_renderer_routing(metadata, "auto")

        assert route.preferred_renderer == "puppeteer"
        assert route.effective_renderer_mode == "puppeteer"
        assert route.fallback_renderer == "pillow"

    def test_launch_failure_maps_to_browser_launch_failed(self):
        failure = _build_puppeteer_failure_info(
            RuntimeError("BrowserType.launch: target closed"),
            stage="browser_launch",
        )
        assert failure.reason_code == "puppeteer_browser_launch_failed"

    def test_timeout_maps_to_timeout_reason(self):
        failure = _build_puppeteer_failure_info(
            TimeoutError("operation timeout while rendering"),
            stage="navigation",
        )
        assert failure.reason_code == "puppeteer_timeout"

    def test_template_render_failure_maps_correctly(self):
        failure = _build_puppeteer_failure_info(
            FileNotFoundError("template missing"),
            stage="template_render",
        )
        assert failure.reason_code == "puppeteer_template_render_failed"

    def test_missing_chromium_maps_correctly(self):
        failure = _build_puppeteer_failure_info(
            RuntimeError("Executable doesn't exist at /cache/chromium and playwright install is required"),
            stage="browser_launch",
        )
        assert failure.reason_code == "puppeteer_missing_chromium"

    def test_generic_error_is_classified_as_unknown(self):
        failure = _build_puppeteer_failure_info(
            Exception("generic failure"),
            stage="unknown",
        )
        assert failure.reason_code == "puppeteer_unknown_error"


# ── Gallery strip position test ───────────────────────────────────────────────

class TestGalleryPositions:
    """Verify gallery strip distribution is resolver-driven instead of fixed 4-up slots."""

    def test_four_item_positions(self):
        template = _load_real_template()
        resolved = resolve_template_behavior(
            template,
            title_text="标题",
            subtitle_text="副标题",
            gallery_requested_count=4,
            gallery_resolved_count=4,
        )

        gallery_layouts = resolved.bottom_policy.layout_metrics["gallery_item_layouts"]

        assert resolved.bottom_policy.gallery_distribution_policy == "dense_quad"
        assert resolved.bottom_policy.content_priority_policy == "expanded_balanced_text_and_gallery_priority"
        assert [item["x"] for item in gallery_layouts] == [106, 314, 522, 730]
        assert [item["w"] for item in gallery_layouts] == [188, 188, 188, 188]
        assert [item["h"] for item in gallery_layouts] == [60, 60, 60, 60]  # PR-7C: item height 52→60

    def test_two_item_distribution_recenters_gallery_strip(self):
        template = _load_real_template()
        resolved = resolve_template_behavior(
            template,
            title_text="标题",
            subtitle_text="这是一段更长的底部说明文案，用来明确触发 bottom peer layout 的 dense subtitle 行为。",
            gallery_requested_count=2,
            gallery_resolved_count=2,
        )

        gallery_layouts = resolved.bottom_policy.layout_metrics["gallery_item_layouts"]

        assert resolved.bottom_policy.gallery_distribution_policy == "balanced_pair"
        assert resolved.bottom_policy.content_priority_policy == "expanded_text_priority_with_light_gallery"
        assert resolved.bottom_policy.peer_balance_policy == "expanded_title_growth_with_light_gallery"
        assert resolved.bottom_policy.title_band_growth_policy == "grow_title_band_expanded_text_gallery_light_gallery"
        assert resolved.bottom_policy.gallery_strip_shift_policy == "downshift_for_spacious_pair"
        assert resolved.bottom_policy.gallery_aspect_policy == "spacious_pair_aspect"
        assert resolved.bottom_policy.gallery_spacing_policy == "relaxed_pair_spacing"
        assert resolved.bottom_policy.gallery_shell_frame_policy == "pair_showcase_frame"
        assert resolved.bottom_policy.bottom_text_emphasis_policy == "expanded_copy_priority_strong_title"
        assert [item["x"] for item in gallery_layouts] == [224, 520]
        assert [item["w"] for item in gallery_layouts] == [280, 280]
        assert [item["y"] for item in gallery_layouts] == [930, 930]  # PR-7B-final: gallery_shell_top=920, inner_pad=10 → 930
        assert [item["h"] for item in gallery_layouts] == [80, 80]

    def test_three_item_distribution_uses_balanced_triplet_layout(self):
        template = _load_real_template()
        resolved = resolve_template_behavior(
            template,
            title_text="超长标题超长标题超长标题超长标题",
            subtitle_text="这是一段更长的底部说明文案，用来明确触发 triplet gallery 的 mixed-content 行为。",
            gallery_requested_count=3,
            gallery_resolved_count=3,
        )

        gallery_layouts = resolved.bottom_policy.layout_metrics["gallery_item_layouts"]

        assert resolved.bottom_policy.gallery_distribution_policy == "balanced_triplet"
        assert resolved.bottom_policy.title_band_growth_policy == "temper_growth_expanded_text_gallery_triplet"
        assert resolved.bottom_policy.gallery_strip_shift_policy == "balanced_triplet_shift"
        assert resolved.bottom_policy.gallery_aspect_policy == "balanced_triplet_aspect"
        assert resolved.bottom_policy.gallery_spacing_policy == "balanced_triplet_spacing"
        assert resolved.bottom_policy.gallery_shell_frame_policy == "triplet_balanced_frame"
        assert resolved.bottom_policy.bottom_text_emphasis_policy == "expanded_balanced_triplet_text_emphasis"
        assert [item["x"] for item in gallery_layouts] == [170, 402, 634]
        assert [item["w"] for item in gallery_layouts] == [220, 220, 220]
        assert [item["h"] for item in gallery_layouts] == [60, 60, 60]

    def test_gallery_markup_uses_strip_local_coordinates(self):
        renderer = PuppeteerStructuredRenderer()
        slot_spec = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "slot_spec.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        template = _load_real_template()
        resolved = resolve_template_behavior(
            template,
            title_text="标题",
            subtitle_text="副标题",
            gallery_requested_count=2,
            gallery_resolved_count=2,
        )

        markup, layer_class = renderer._gallery_markup(
            slot_spec,
            ["data:image/png;base64,a", "data:image/png;base64,b"],
            resolved.bottom_policy,
        )

        assert layer_class == "state-show"
        assert 'left:128px;top:10px;width:280px;height:80px;' in markup
        assert 'left:424px;top:10px;width:280px;height:80px;' in markup

    def test_visible_gallery_item_count_checks_intersection_with_strip_bounds(self):
        slot_spec = {
            "layers": {"bottom_gallery_items_layer": {"x": 96, "y": 896, "w": 832, "h": 56}},
            "slots": {
                "gallery": [
                    {"x": 96, "y": 896, "w": 196, "h": 56},
                    {"x": 1200, "y": 896, "w": 196, "h": 56},
                ]
            },
        }

        assert _visible_gallery_item_count(slot_spec, 2) == 1


# ── Feature callout rendering ─────────────────────────────────────────────────

class TestFeatureCallouts:
    """Verify feature callout dots and leader lines are rendered by Pillow."""

    def _make_callout(
        self, anchor_x=200, anchor_y=300, anchor_radius=7, text_x=220, text_y=280
    ) -> FeatureCalloutSpec:
        label_box = TextSlotSpec(
            x=text_x, y=text_y, w=200, h=60,
            font_key="feature", font_size=16, color="#1A1A1A",
        )
        return FeatureCalloutSpec(
            label_box=label_box,
            anchor_x=anchor_x,
            anchor_y=anchor_y,
            anchor_radius=anchor_radius,
            anchor_color="#E8002A",
            leader_color="#E8002A",
            leader_width=2,
        )

    def test_anchor_dot_pixels_written(self):
        """Pixels at the anchor dot center should be non-transparent after render."""
        canvas = PILImage.new("RGBA", (500, 500), (0, 0, 0, 0))
        renderer = LayoutRenderer()
        from PIL import ImageDraw
        draw = ImageDraw.Draw(canvas)
        callout = self._make_callout(anchor_x=200, anchor_y=200, anchor_radius=7)
        renderer._draw_feature_callout(draw, canvas, callout, "Test feature")
        # Center of anchor dot must be opaque red
        pixel = canvas.getpixel((200, 200))
        assert pixel[3] > 0, "Anchor dot center should be visible"
        assert pixel[0] > 150, "Anchor dot should be reddish (#E8002A)"

    def test_anchor_radius_zero_skips_dot(self):
        """anchor_radius=0 → no dot or leader line drawn; text still renders."""
        canvas = PILImage.new("RGBA", (500, 500), (0, 0, 0, 0))
        renderer = LayoutRenderer()
        from PIL import ImageDraw
        draw = ImageDraw.Draw(canvas)
        label_box = TextSlotSpec(
            x=50, y=50, w=300, h=60,
            font_key="feature", font_size=16, color="#1A1A1A",
        )
        callout = FeatureCalloutSpec(
            label_box=label_box,
            anchor_x=10,
            anchor_y=10,
            anchor_radius=0,  # disabled
        )
        renderer._draw_feature_callout(draw, canvas, callout, "No dot")
        # Pixel at expected anchor location should still be transparent
        pixel = canvas.getpixel((10, 10))
        assert pixel[3] == 0, "No anchor dot should be drawn when anchor_radius=0"

    def test_callouts_skip_empty_text(self):
        """Empty feature string → callout is skipped entirely (no crash)."""
        template = _load_real_template()
        spec = _minimal_spec(features=())  # no features at all
        result = LayoutRenderer().render(template, spec, _minimal_assets())
        assert result.image is not None

    def test_real_template_callout_anchors(self):
        """Real template: feature callouts have anchor_radius > 0 and correct coords."""
        template = _load_real_template()
        assert len(template.feature_callouts) == 4
        for fc in template.feature_callouts:
            assert fc.anchor_radius == 7
            assert fc.anchor_x == 764
            assert fc.anchor_color == "#E8002A"


# ── CTA pill button rendering ─────────────────────────────────────────────────

class TestCtaPillRendering:
    """Verify the agent CTA pill (rounded-rect background) is drawn correctly."""

    def test_pill_bg_pixels_filled(self):
        """After drawing pill bg, pixels inside the slot should have correct color."""
        from PIL import ImageDraw
        canvas = PILImage.new("RGBA", (400, 200), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        slot = TextSlotSpec(
            x=50, y=50, w=200, h=60,
            font_key="brand_regular", font_size=20, color="#FFFFFF",
            bg_color="#E8002A", bg_radius=30,
        )
        _draw_pill_bg(draw, slot)
        # Center of pill should be red and opaque
        cx, cy = 50 + 100, 50 + 30
        pixel = canvas.getpixel((cx, cy))
        assert pixel[3] == 255, "Pill center must be fully opaque"
        assert pixel[0] > 200, "Pill center should be red"

    def test_real_template_agent_slot_is_plain_secondary_text(self):
        """Real template: agent_name_slot is plain secondary text, not a pill."""
        template = _load_real_template()
        slot = template.agent_name_slot
        assert slot.bg_color == "transparent"
        assert slot.bg_radius == 0
        assert slot.color == "#6F5757"


class TestStructuredGalleryMarkup:

    def test_partial_gallery_renders_only_actual_items(self):
        renderer = PuppeteerStructuredRenderer()
        slot_spec = {
            "slots": {
                "gallery": [
                    {"x": 0, "y": 0, "w": 10, "h": 10},
                    {"x": 12, "y": 0, "w": 10, "h": 10},
                    {"x": 24, "y": 0, "w": 10, "h": 10},
                    {"x": 36, "y": 0, "w": 10, "h": 10},
                ]
            }
        }
        template = _load_real_template()
        resolved = resolve_template_behavior(
            template,
            title_text="标题",
            subtitle_text="副标题",
            gallery_requested_count=2,
            gallery_resolved_count=2,
        )

        markup, layer_class = renderer._gallery_markup(slot_spec, ["a.png", "b.png"], resolved.bottom_policy)

        assert layer_class == "state-show"
        assert markup.count("gallery-item") == 2
        assert markup.count('src="a.png"') == 1
        assert markup.count('src="b.png"') == 1

    def test_empty_gallery_hides_bottom_layer(self):
        renderer = PuppeteerStructuredRenderer()
        slot_spec = {"slots": {"gallery": [{"x": 0, "y": 0, "w": 10, "h": 10}]}}
        template = _load_real_template()
        resolved = resolve_template_behavior(template, title_text="标题", gallery_requested_count=0, gallery_resolved_count=0)

        markup, layer_class = renderer._gallery_markup(slot_spec, [], resolved.bottom_policy)

        assert markup == ""
        assert layer_class == "state-hidden"

    def test_full_gallery_marks_show_state(self):
        renderer = PuppeteerStructuredRenderer()
        slot_spec = {
            "slots": {
                "gallery": [
                    {"x": 0, "y": 0, "w": 10, "h": 10},
                    {"x": 12, "y": 0, "w": 10, "h": 10},
                ]
            }
        }
        template = _load_real_template()
        resolved = resolve_template_behavior(
            template,
            title_text="标题",
            subtitle_text="副标题",
            gallery_requested_count=2,
            gallery_resolved_count=2,
        )

        markup, layer_class = renderer._gallery_markup(slot_spec, ["a.png", "b.png"], resolved.bottom_policy)

        assert layer_class == "state-show"
        assert markup.count("gallery-item") == 2

    def test_feature_markup_collapses_cleanly(self):
        renderer = PuppeteerStructuredRenderer()
        anchor_map = {
            "feature_callouts": [
                {"anchor_x": 10, "anchor_y": 20, "label_box": {"x": 30, "y": 0, "w": 60, "h": 40}},
                {"anchor_x": 10, "anchor_y": 70, "label_box": {"x": 30, "y": 50, "w": 60, "h": 40}},
            ]
        }

        markup, layer_class = renderer._feature_markup(
            anchor_map,
            ("One",),
            feature_policy=resolve_feature_behavior(
                "count_driven_callout_stack",
                requested_count=1,
                max_items=4,
            ),
        )

        assert layer_class == "state-show feature-mode-1"
        assert markup.count('class="feature-callout feature-mode-box-1"') == 1
        assert markup.count("feature-callout-connector") == 1
        assert markup.count("feature-callout-marker") == 1

    def test_feature_markup_ignores_blank_items_and_uses_real_count_mode(self):
        renderer = PuppeteerStructuredRenderer()
        anchor_map = {
            "feature_callouts": [
                {"anchor_x": 10, "anchor_y": 20, "label_box": {"x": 30, "y": 0, "w": 60, "h": 40}},
                {"anchor_x": 10, "anchor_y": 70, "label_box": {"x": 30, "y": 50, "w": 60, "h": 40}},
                {"anchor_x": 10, "anchor_y": 120, "label_box": {"x": 30, "y": 100, "w": 60, "h": 40}},
            ]
        }

        markup, layer_class = renderer._feature_markup(
            anchor_map,
            ("One", " ", "Three"),
            feature_policy=resolve_feature_behavior(
                "count_driven_callout_stack",
                requested_count=2,
                max_items=4,
            ),
        )

        assert layer_class == "state-show feature-mode-2"
        assert markup.count('class="feature-callout feature-mode-box-2"') == 2
        assert markup.count("feature-callout-connector") == 2
        assert markup.count("feature-callout-marker") == 2
        assert "feature-mode-box-2" in markup
        assert "connector-policy-balanced_pair" in markup

    def test_feature_markup_uses_dense_mode_for_four_real_items(self):
        renderer = PuppeteerStructuredRenderer()
        anchor_map = {
            "feature_callouts": [
                {"anchor_x": 10, "anchor_y": 20, "label_box": {"x": 30, "y": 0, "w": 60, "h": 40}},
                {"anchor_x": 10, "anchor_y": 70, "label_box": {"x": 30, "y": 50, "w": 60, "h": 40}},
                {"anchor_x": 10, "anchor_y": 120, "label_box": {"x": 30, "y": 100, "w": 60, "h": 40}},
                {"anchor_x": 10, "anchor_y": 170, "label_box": {"x": 30, "y": 150, "w": 60, "h": 40}},
            ]
        }

        markup, layer_class = renderer._feature_markup(
            anchor_map,
            ("One", "Two", "Three", "Four"),
            feature_policy=resolve_feature_behavior(
                "count_driven_callout_stack",
                requested_count=4,
                max_items=4,
            ),
        )

        assert layer_class == "state-show feature-mode-4"
        assert markup.count('class="feature-callout feature-mode-box-4"') == 4
        assert markup.count("connector-policy-dense_quad") == 4

    def test_feature_markup_hides_when_empty(self):
        renderer = PuppeteerStructuredRenderer()

        markup, layer_class = renderer._feature_markup(
            {"feature_callouts": []},
            (),
            feature_policy=resolve_feature_behavior(
                "count_driven_callout_stack",
                requested_count=0,
                max_items=4,
            ),
        )

        assert markup == ""
        assert layer_class == "state-hidden feature-mode-0"

    def test_normalized_feature_texts_filter_blank_entries(self):
        assert _normalized_feature_texts((" One ", "", "  ", "Two")) == ["One", "Two"]

    def test_resolve_feature_callout_layout_centers_single_feature(self):
        template = _load_real_template()

        resolved = _resolve_feature_callout_layout(template.feature_callouts, ("One",))

        assert len(resolved) == 1
        callout, text = resolved[0]
        assert text == "One"
        assert callout.label_box.h == 80
        assert callout.label_box.y == 356
        assert callout.anchor_y == 396

    def test_resolve_feature_callout_layout_balances_two_feature_mode(self):
        template = _load_real_template()

        resolved = _resolve_feature_callout_layout(template.feature_callouts, ("One", "Two"))

        assert len(resolved) == 2
        assert [item[0].label_box.y for item in resolved] == [311, 405]
        assert all(item[0].label_box.h == 76 for item in resolved)

    def test_resolve_feature_callout_layout_uses_compact_three_feature_mode(self):
        template = _load_real_template()

        resolved = _resolve_feature_callout_layout(template.feature_callouts, ("One", "Two", "Three"))

        assert len(resolved) == 3
        assert [item[0].label_box.y for item in resolved] == [272, 360, 448]
        assert all(item[0].label_box.h == 72 for item in resolved)

    def test_resolve_feature_callout_layout_uses_dense_four_feature_mode(self):
        template = _load_real_template()

        resolved = _resolve_feature_callout_layout(template.feature_callouts, ("One", "Two", "Three", "Four"))

        assert len(resolved) == 4
        assert [item[0].label_box.y for item in resolved] == [258, 330, 402, 474]
        assert all(item[0].label_box.h == 60 for item in resolved)

    def test_resolve_feature_callout_map_matches_three_feature_mode_geometry(self):
        anchor_map = {
            "feature_callouts": [
                {"anchor_x": 764, "anchor_y": 250, "label_box": {"x": 784, "y": 216, "w": 144, "h": 60}},
                {"anchor_x": 764, "anchor_y": 350, "label_box": {"x": 784, "y": 316, "w": 144, "h": 60}},
                {"anchor_x": 764, "anchor_y": 450, "label_box": {"x": 784, "y": 416, "w": 144, "h": 60}},
                {"anchor_x": 764, "anchor_y": 550, "label_box": {"x": 784, "y": 516, "w": 144, "h": 60}},
            ]
        }

        resolved = _resolve_feature_callout_map(anchor_map, ("One", "Two", "Three"))

        assert len(resolved) == 3
        assert [item[0]["label_box"]["y"] for item in resolved] == [272, 360, 448]
        assert [item[0]["anchor_y"] for item in resolved] == [308, 396, 484]

    def test_resolve_feature_callout_map_keeps_fixed_product_anchor_geometry(self):
        anchor_map = {
            "feature_callouts": [
                {"anchor_x": 764, "anchor_y": 250, "label_box": {"x": 784, "y": 216, "w": 176, "h": 76}},
                {"anchor_x": 764, "anchor_y": 350, "label_box": {"x": 784, "y": 316, "w": 176, "h": 76}},
                {"anchor_x": 764, "anchor_y": 450, "label_box": {"x": 784, "y": 416, "w": 176, "h": 76}},
                {"anchor_x": 764, "anchor_y": 550, "label_box": {"x": 784, "y": 516, "w": 144, "h": 60}},
            ]
        }
        feature_policy = resolve_feature_behavior(
            "product_anchor_callouts",
            requested_count=3,
            max_items=4,
        )

        resolved = _resolve_feature_callout_map(anchor_map, ("Fast Heat-Up", "Precise Thermostat Control", "Stainless Steel Body"), feature_policy=feature_policy)

        assert len(resolved) == 3
        assert [item[0]["label_box"]["y"] for item in resolved] == [216, 316, 416]
        assert [item[0]["label_box"]["w"] for item in resolved] == [176, 176, 176]
        assert [item[0]["label_box"]["h"] for item in resolved] == [76, 76, 76]
        assert [item[0]["anchor_y"] for item in resolved] == [250, 350, 450]

    def test_resolve_feature_callout_map_uses_fryer_variant_annotation_bounds(self):
        anchor_map = {
            "feature_callouts": [
                {"anchor_x": 764, "anchor_y": 250, "label_box": {"x": 784, "y": 216, "w": 176, "h": 76}},
                {"anchor_x": 764, "anchor_y": 350, "label_box": {"x": 784, "y": 316, "w": 176, "h": 76}},
                {"anchor_x": 764, "anchor_y": 450, "label_box": {"x": 784, "y": 416, "w": 176, "h": 76}},
                {"anchor_x": 764, "anchor_y": 550, "label_box": {"x": 784, "y": 516, "w": 144, "h": 60}},
            ]
        }
        template = _load_real_template()
        hero = resolve_template_behavior(
            template,
            feature_count=3,
            title_text="Power Up Your Fry Station",
            subtitle_text="Fast heating, precise control, and durable stainless steel construction for everyday commercial use.",
            brand_name="ChefCraft",
            gallery_requested_count=4,
            gallery_input_count_normalized=4,
            gallery_resolved_count=4,
            bottom_mode="title_gallery_split",
            gallery_mode="strip_local_visible_only",
            agent_name="Commercial Electric Fryer Series",
            has_product_secondary_asset=False,
        )

        resolved = _resolve_feature_callout_map(
            anchor_map,
            ("Fast Heat-Up", "Precise Thermostat Control", "Stainless Steel Body"),
            feature_policy=hero.feature_policy,
            product_policy=hero.product_policy,
        )

        assert len(resolved) == 3
        assert [item[0]["label_box"]["x"] for item in resolved] == [796, 796, 796]
        assert [item[0]["label_box"]["w"] for item in resolved] == [176, 176, 176]
        assert [item[0]["label_box"]["h"] for item in resolved] == [76, 76, 76]
        assert [item[0]["anchor_x"] for item in resolved] == [736, 736, 736]

    def test_resolve_feature_behavior_supports_second_feature_mode(self):
        resolved = resolve_feature_behavior(
            "uniform_callout_stack",
            requested_count=3,
            max_items=4,
        )

        assert resolved.mode == "uniform_callout_stack"
        assert resolved.visible_item_count == 3
        assert resolved.connector_policy == "uniform_stack"
        assert resolved.box_policy == "uniform_compact_stack"
        assert resolved.box_h == 68

    def test_resolve_feature_callout_layout_uses_uniform_feature_mode(self):
        template = _load_real_template()
        feature_policy = resolve_feature_behavior(
            "uniform_callout_stack",
            requested_count=3,
            max_items=len(template.feature_callouts),
        )

        resolved = _resolve_feature_callout_layout(
            template.feature_callouts,
            ("One", "Two", "Three"),
            feature_policy=feature_policy,
        )

        assert len(resolved) == 3
        assert [item[0].label_box.y for item in resolved] == [282, 362, 442]
        assert all(item[0].label_box.h == 68 for item in resolved)

    def test_feature_markup_uses_uniform_mode_policy(self):
        renderer = PuppeteerStructuredRenderer()
        anchor_map = {
            "feature_callouts": [
                {"anchor_x": 10, "anchor_y": 20, "label_box": {"x": 30, "y": 0, "w": 60, "h": 40}},
                {"anchor_x": 10, "anchor_y": 70, "label_box": {"x": 30, "y": 50, "w": 60, "h": 40}},
                {"anchor_x": 10, "anchor_y": 120, "label_box": {"x": 30, "y": 100, "w": 60, "h": 40}},
            ]
        }

        markup, layer_class = renderer._feature_markup(
            anchor_map,
            ("One", "Two", "Three"),
            feature_policy=resolve_feature_behavior(
                "uniform_callout_stack",
                requested_count=3,
                max_items=4,
            ),
        )

        assert layer_class == "state-show feature-mode-3"
        assert markup.count("connector-policy-uniform_stack") == 3

    def test_resolve_feature_mode_clamps_to_supported_range(self):
        assert _resolve_feature_mode(0)[0] == 1
        assert _resolve_feature_mode(2)[0] == 2
        assert _resolve_feature_mode(5)[0] == 4

    def test_prepare_gallery_urls_caps_and_resizes(self):
        slot_spec = {
            "slots": {
                "gallery": [{"w": 196, "h": 56, "fit": "cover"}],
            },
        }
        images = [solid_image(800, 400) for _ in range(6)]
        urls, status = _prepare_gallery_urls(
            images,
            [{"index": i, "url": f"mock://g{i}", "resolved": True, "error_code": None} for i in range(6)],
            slot_spec,
        )
        assert len(urls) == 4
        assert len(status) == 4
        assert all(url.startswith("data:image/png;base64,") for url in urls)

    def test_render_with_agent_cta(self):
        """Full render with agent name should not raise and produce valid output."""
        template = _load_real_template()
        spec = _minimal_spec(agent_name="智能顾问")
        result = LayoutRenderer().render(template, spec, _minimal_assets())
        assert result.image.mode == "RGBA"
        assert result.image.size == (1024, 1024)


class TestStructuredScenarioLayer:

    def test_template_behavior_resolver_uses_template_metadata(self):
        template = _load_real_template()

        resolved = resolve_template_behavior(template)

        assert resolved.hero_mode == "scenario_cover_product_contain"
        assert resolved.feature_mode == "product_anchor_callouts"
        assert resolved.beauty_tokens.shell_surface == "campaign_frozen_panel"
        assert resolved.css_vars["--accent-tone"] == "#C63A2D"
        assert resolved.hero_policy.scenario_enabled is True
        assert resolved.feature_policy.mode == "product_anchor_callouts"
        assert resolved.bottom_policy.mode == "title_gallery_split"
        assert resolved.bottom_policy.gallery_mode == "strip_local_visible_only"

    def test_template_behavior_resolver_supports_second_hero_mode(self):
        template = _load_real_template()
        template.behavior_modes = replace(
            template.behavior_modes,
            hero_mode="single_product_focus",
        )

        resolved = resolve_template_behavior(template)

        assert resolved.hero_mode == "single_product_focus"
        assert resolved.hero_policy.scenario_enabled is False
        assert resolved.hero_policy.product_anchor == "bottom"

    def test_template_behavior_resolver_supports_second_feature_mode(self):
        template = _load_real_template()
        template.behavior_modes = replace(
            template.behavior_modes,
            feature_mode="uniform_callout_stack",
        )

        resolved = resolve_template_behavior(template, feature_count=3)

        assert resolved.feature_mode == "uniform_callout_stack"
        assert resolved.feature_policy.connector_policy == "uniform_stack"
        assert resolved.feature_policy.box_policy == "uniform_compact_stack"

    def test_template_behavior_resolver_supports_product_annotation_mode(self):
        template = _load_real_template()
        template.behavior_modes = replace(
            template.behavior_modes,
            product_annotation_mode="product_anchor_callouts",
        )

        resolved = resolve_template_behavior(template, feature_count=3)

        assert resolved.product_annotation_mode == "product_anchor_callouts"
        assert resolved.product_policy.annotation_count_policy == "fixed_3_product_anchor_annotations"
        assert resolved.product_policy.visible_annotation_count == 3
        assert resolved.product_policy.annotation_items[0]["anchor_x"] == 764

    def test_template_behavior_resolver_supports_expanded_beauty_presets(self):
        template = _load_real_template()
        template.beauty_tokens = replace(
            template.beauty_tokens,
            shell_surface="panel_dark_soft",
            shell_border="clean_frame",
            shell_shadow="medium",
            accent_tone="cool_blue",
            text_emphasis="editorial_soft",
        )

        resolved = resolve_template_behavior(template, feature_count=2)

        assert resolved.beauty_tokens.shell_surface == "panel_dark_soft"
        assert resolved.css_vars["--shell-surface-header"].startswith("linear-gradient")
        assert resolved.css_vars["--shell-shadow-main"] == "0 22px 42px rgba(26, 18, 18, 0.16)"
        assert resolved.accent_color == "#2D6CDF"
        assert resolved.text_colors["subtitle"] == "#8A7A84"

    def test_template_behavior_resolver_rejects_unknown_hero_mode(self):
        template = _load_real_template()
        template.behavior_modes = replace(
            template.behavior_modes,
            hero_mode="hero_mode_missing",
        )

        with pytest.raises(ValueError, match="Unsupported hero_mode"):
            resolve_template_behavior(template)

    def test_template_behavior_resolver_supports_bottom_mode_overrides(self):
        template = _load_real_template()

        resolved = resolve_template_behavior(
            template,
            title_text="测试标题",
            subtitle_text="副标题",
            gallery_requested_count=3,
            gallery_resolved_count=3,
            bottom_mode="title_only",
            gallery_mode="supporting_packshots",
        )

        assert resolved.bottom_policy.mode == "text_only_expanded"  # title_only alias
        assert resolved.bottom_policy.gallery_mode == "supporting_packshots"
        assert resolved.bottom_policy.title_band_rendered is True
        assert resolved.bottom_policy.gallery_strip_rendered is False
        assert resolved.bottom_policy.subtitle_slot_rendered is True
        assert resolved.bottom_policy.title_band_sizing_mode == "standard"
        assert resolved.bottom_policy.bottom_layout_mode == "text_only_expanded"
        assert resolved.bottom_policy.subtitle_overflow_policy == "single_line_ellipsis_inside_expanded_title_band"

    def test_template_behavior_resolver_promotes_bottom_into_behavior_policy(self):
        template = _load_real_template()

        resolved = resolve_template_behavior(
            template,
            title_text="超长标题超长标题超长标题超长标题",
            subtitle_text="这是一段更长的底部说明文案，用来验证 subtitle overflow、title band sizing 和 gallery peer balance 会不会进入 resolver 策略。",
            gallery_requested_count=2,
            gallery_resolved_count=2,
            bottom_mode="title_gallery_split",
            gallery_mode="strip_local_visible_only",
        )

        assert resolved.bottom_policy.title_band_sizing_mode == "expanded"
        assert resolved.bottom_policy.bottom_layout_mode == "title_gallery_split"
        assert resolved.bottom_policy.title_band_growth_policy == "grow_title_band_expanded_text_gallery_light_gallery"
        assert resolved.bottom_policy.subtitle_overflow_policy == "two_line_clamp_inside_expanded_split_title_band"
        assert resolved.bottom_policy.content_priority_policy == "expanded_text_priority_with_light_gallery"
        assert resolved.bottom_policy.peer_balance_policy == "expanded_title_growth_with_light_gallery"
        assert resolved.bottom_policy.bottom_peer_balance_policy == "expanded_copy_priority_spacious_gallery"
        assert resolved.bottom_policy.gallery_distribution_policy == "balanced_pair"
        assert resolved.bottom_policy.gallery_shell_frame_policy == "pair_showcase_frame"
        assert resolved.bottom_policy.gallery_strip_shift_policy == "downshift_for_spacious_pair"
        assert resolved.bottom_policy.gallery_aspect_policy == "spacious_pair_aspect"
        assert resolved.bottom_policy.bottom_text_emphasis_policy == "expanded_copy_priority_strong_title"
        assert resolved.bottom_policy.title_line_clamp == 2
        assert resolved.bottom_policy.subtitle_line_clamp == 2
        assert resolved.bottom_policy.layout_metrics["title_band_height"] == 192
        assert resolved.bottom_policy.layout_metrics["gallery_shell_top"] == 920  # PR-7B-final: 728+192=920
        assert resolved.bottom_policy.layout_metrics["gallery_shell_x"] == 208
        assert resolved.bottom_policy.layout_metrics["gallery_shell_w"] == 608
        assert resolved.bottom_policy.layout_metrics["gallery_items_height"] == 80
        assert resolved.css_vars["--gallery-shell-left"] == "208px"
        assert resolved.css_vars["--gallery-shell-width"] == "608px"
        assert resolved.css_vars["--gallery-shell-radius"] == "24px"
        assert resolved.css_vars["--bottom-title-letter-spacing"] == "0.012em"
        assert resolved.css_vars["--title-band-height"] == "192px"
        assert resolved.css_vars["--subtitle-line-clamp"] == "2"

    def test_template_behavior_resolver_limits_title_growth_when_gallery_is_dense(self):
        template = _load_real_template()

        resolved = resolve_template_behavior(
            template,
            title_text="超长标题超长标题超长标题超长标题",
            subtitle_text="这是一段更长的底部说明文案，用来验证 subtitle overflow、title band sizing 和 gallery peer balance 会不会进入 resolver 策略。",
            gallery_requested_count=4,
            gallery_resolved_count=4,
            bottom_mode="title_gallery_split",
            gallery_mode="strip_local_visible_only",
        )

        assert resolved.bottom_policy.title_band_sizing_mode == "standard"
        assert resolved.bottom_policy.bottom_layout_mode == "title_gallery_split"
        assert resolved.bottom_policy.title_band_growth_policy == "hold_growth_expanded_text_gallery_quad"
        assert resolved.bottom_policy.content_priority_policy == "expanded_gallery_count_priority_with_text_preserved"
        assert resolved.bottom_policy.peer_balance_policy == "expanded_gallery_preserved_with_full_title"
        assert resolved.bottom_policy.bottom_peer_balance_policy == "expanded_quad_gallery_with_full_title"
        assert resolved.bottom_policy.gallery_distribution_policy == "dense_quad"
        assert resolved.bottom_policy.gallery_shell_frame_policy == "quad_strip_frame"
        assert resolved.bottom_policy.gallery_strip_shift_policy == "tight_quad_shift"
        assert resolved.bottom_policy.gallery_aspect_policy == "compact_quad_aspect"
        assert resolved.bottom_policy.bottom_text_emphasis_policy == "expanded_quad_text_emphasis"
        assert resolved.bottom_policy.title_line_clamp == 2
        assert resolved.bottom_policy.subtitle_line_clamp == 2
        assert resolved.bottom_policy.layout_metrics["title_band_height"] == 176  # PR-7C: 168→176
        assert resolved.bottom_policy.layout_metrics["gallery_shell_top"] == 904  # PR-7C: 728+176=904
        assert resolved.bottom_policy.layout_metrics["gallery_items_height"] == 60  # PR-7C: 52→60

    def test_template_behavior_resolver_promotes_dense_feature_and_bottom_into_template_policy(self):
        template = _load_real_template()
        template.behavior_modes = replace(template.behavior_modes, feature_mode="count_driven_callout_stack")

        resolved = resolve_template_behavior(
            template,
            feature_count=4,
            title_text="超长标题超长标题超长标题超长标题",
            subtitle_text="这是一段更长的底部说明文案，用来验证 template-level priority 和 rebalance 是否已经从 bottom SOP 上升出来。",
            gallery_requested_count=4,
            gallery_resolved_count=4,
        )

        assert resolved.template_layout_policy.layout_density_mode == "multi_region_dense"
        assert resolved.template_layout_policy.region_priority_policy == "bottom_and_feature_dual_density"
        assert resolved.template_layout_policy.peer_rebalance_policy == "feature_compacts_before_template_reflow"
        assert resolved.template_layout_policy.content_priority_policy == "bottom_copy_first_feature_stack_second"
        assert resolved.feature_policy.start_strategy == "top_weighted_compact_region"
        assert resolved.feature_policy.box_h == 56
        assert resolved.feature_policy.gap == 10

    def test_template_behavior_resolver_keeps_bottom_dense_case_local_when_feature_is_light(self):
        template = _load_real_template()
        template.behavior_modes = replace(template.behavior_modes, feature_mode="count_driven_callout_stack")

        resolved = resolve_template_behavior(
            template,
            feature_count=2,
            title_text="超长标题超长标题超长标题超长标题",
            subtitle_text="这是一段更长的底部说明文案，用来验证 bottom 仍可以作为 local behavior 先自行响应。",
            gallery_requested_count=2,
            gallery_resolved_count=2,
        )

        assert resolved.template_layout_policy.layout_density_mode == "bottom_dense"
        assert resolved.template_layout_policy.peer_rebalance_policy == "bottom_local_rebalance_only"
        assert resolved.feature_policy.start_strategy == "centered_in_region"

    def test_template_behavior_resolver_rejects_unknown_bottom_mode(self):
        template = _load_real_template()

        with pytest.raises(ValueError, match="Unsupported bottom_mode"):
            resolve_template_behavior(template, bottom_mode="unknown_bottom_mode")

    def test_safe_preset_scenario_url_is_non_empty(self):
        data_url = _safe_preset_scenario_data_url()
        assert data_url.startswith("data:image/png;base64,")

    def test_template_html_marks_safe_fill_when_scenario_missing(self):
        renderer = PuppeteerStructuredRenderer()
        template = _load_real_template()
        html_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.html"
        ).read_text(encoding="utf-8")
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")
        slot_spec = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "slot_spec.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        anchor_map = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "anchor_map.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )

        html_payload = renderer._build_html(
            html_template=html_template,
            css_template=css_template,
            svg_overlay="",
            poster=_minimal_spec(),
            asset_urls={
                "logo": "",
                "scenario": _safe_preset_scenario_data_url(),
                "scenario_is_real": False,
                "product": "data:image/png;base64,abc",
                "gallery": [],
            },
            slot_spec=slot_spec,
            anchor_map=anchor_map,
            spec=template,
        )

        assert "state-safe-fill" in html_payload
        assert "hero-mode-scenario-cover-product-contain" in html_payload
        assert "--accent-tone: #C63A2D" in html_payload
        assert "layer-hero-peer-region state-safe-fill state-fit-cover state-anchor-center hero-mode-scenario-cover-product-contain" in html_payload
        assert "scenario-fit-cover" in html_payload
        assert "layer layer-product-content state-fit-contain state-anchor-center hero-mode-scenario-cover-product-contain" in html_payload
        assert "product-fit-contain" in html_payload
        assert 'data-region="title_band_region"' in html_payload
        assert 'data-region="feature_region"' in html_payload
        assert "__SVG_OVERLAY__" not in html_payload

    def test_template_html_hides_title_band_when_gallery_only(self):
        renderer = PuppeteerStructuredRenderer()
        template = _load_real_template()
        html_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.html"
        ).read_text(encoding="utf-8")
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")
        slot_spec = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "slot_spec.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        anchor_map = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "anchor_map.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        poster = _minimal_spec(
            gallery_images=(
                AssetRef(url="mock://gallery-1"),
                AssetRef(url="mock://gallery-2"),
            ),
            bottom_mode="gallery_only",
        )

        html_payload = renderer._build_html(
            html_template=html_template,
            css_template=css_template,
            svg_overlay="",
            poster=poster,
            asset_urls={
                "logo": "",
                "scenario": _safe_preset_scenario_data_url(),
                "scenario_is_real": False,
                "product": "data:image/png;base64,abc",
                "gallery": ["data:image/png;base64,g1", "data:image/png;base64,g2"],
            },
            slot_spec=slot_spec,
            anchor_map=anchor_map,
            spec=template,
        )

        assert "state-gallery-only" in html_payload
        assert "layer-title-band-region-shell state-hidden" in html_payload
        assert "layer-subtitle state-hidden" in html_payload

    def test_template_html_marks_real_scenario_when_asset_exists(self):
        renderer = PuppeteerStructuredRenderer()
        template = _load_real_template()
        html_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.html"
        ).read_text(encoding="utf-8")
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")
        slot_spec = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "slot_spec.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        anchor_map = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "anchor_map.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )

        html_payload = renderer._build_html(
            html_template=html_template,
            css_template=css_template,
            svg_overlay="",
            poster=_minimal_spec(),
            asset_urls={
                "logo": "",
                "scenario": "data:image/png;base64,real",
                "scenario_is_real": True,
                "product": "data:image/png;base64,abc",
                "gallery": [],
            },
            slot_spec=slot_spec,
            anchor_map=anchor_map,
            spec=template,
        )

        assert "layer-hero-peer-region state-real state-fit-cover state-anchor-center hero-mode-scenario-cover-product-contain" in html_payload
        assert "region-shell-scenario state-real" in html_payload
        assert "layer layer-product layer-hero-peer-region state-fit-contain state-anchor-center hero-mode-scenario-cover-product-contain" in html_payload
        assert 'data-layer="product_card_shell_layer"' in html_payload
        assert 'data-layer="product_canvas_shell_layer"' in html_payload

    def test_template_html_hides_scenario_for_single_product_focus(self):
        renderer = PuppeteerStructuredRenderer()
        template = _load_real_template()
        template.behavior_modes = replace(
            template.behavior_modes,
            hero_mode="single_product_focus",
        )
        html_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.html"
        ).read_text(encoding="utf-8")
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")
        slot_spec = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "slot_spec.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        anchor_map = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "anchor_map.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )

        html_payload = renderer._build_html(
            html_template=html_template,
            css_template=css_template,
            svg_overlay="",
            poster=_minimal_spec(),
            asset_urls={
                "logo": "",
                "scenario": "data:image/png;base64,real",
                "scenario_is_real": True,
                "product": "data:image/png;base64,abc",
                "gallery": [],
            },
            slot_spec=slot_spec,
            anchor_map=anchor_map,
            spec=template,
        )

        assert "hero-mode-single-product-focus" in html_payload
        assert 'class="layer layer-scenario layer-hero-peer-region state-hidden hero-mode-single-product-focus"' in html_payload
        assert 'class="layer layer-product layer-hero-peer-region state-fit-contain state-anchor-bottom hero-mode-single-product-focus"' in html_payload

    def test_template_html_exposes_expanded_beauty_css_vars(self):
        renderer = PuppeteerStructuredRenderer()
        template = _load_real_template()
        template.beauty_tokens = replace(
            template.beauty_tokens,
            shell_surface="panel_clean",
            shell_border="clean_frame",
            shell_shadow="medium",
            accent_tone="brand_gold",
            text_emphasis="high_contrast",
        )
        html_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.html"
        ).read_text(encoding="utf-8")
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")
        slot_spec = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "slot_spec.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        anchor_map = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "anchor_map.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )

        html_payload = renderer._build_html(
            html_template=html_template,
            css_template=css_template,
            svg_overlay="",
            poster=_minimal_spec(),
            asset_urls={
                "logo": "",
                "scenario": _safe_preset_scenario_data_url(),
                "scenario_is_real": False,
                "product": "data:image/png;base64,abc",
                "gallery": [],
            },
            slot_spec=slot_spec,
            anchor_map=anchor_map,
            spec=template,
        )

        assert "--accent-tone: #C69214" in html_payload
        assert "--text-color-brand: #111111" in html_payload
        assert "--shell-surface-gallery-strip: rgba(255, 255, 255, 0.84)" in html_payload

    def test_template_css_exposes_peer_region_fit_policies(self):
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")

        assert ".layer-hero-peer-region" in css_template
        assert "--product-content-pad-top: 24px;" in css_template
        assert "--product-content-pad-bottom: 10px;" in css_template
        assert ".layer-product-content.state-anchor-bottom {" in css_template
        assert "align-items: flex-end;" in css_template
        assert ".scenario-fit-cover img" in css_template
        assert "object-fit: cover;" in css_template
        assert ".product-fit-contain img" in css_template
        assert "object-fit: contain;" in css_template
        assert "object-position: center center;" in css_template
        assert ".layer-feature-callouts.feature-mode-1 .feature-callout" in css_template
        assert ".layer-feature-callouts.feature-mode-4 .feature-callout" in css_template

    def test_template_css_exposes_visual_polish_phase1_without_geometry_tokens_drift(self):
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")

        assert "--scenario-image-treatment: saturate(0.88) brightness(0.94);" in css_template
        assert "--product-primary-shadow: drop-shadow(0 18px 30px rgba(0, 0, 0, 0.20));" in css_template
        assert "--product-secondary-opacity: 0.72;" in css_template
        assert "--gallery-shell-backdrop-blur: blur(12px);" in css_template
        assert ".layer-scenario-content.state-real .slot-scenario img {" in css_template
        assert ".layer-product-secondary-image {" in css_template
        assert ".product-secondary-fit-contain img {" in css_template
        assert ".product-annotation-mode-product_anchor_callouts .feature-callout {" in css_template
        assert ".region-shell-title-band {" in css_template
        assert ".region-shell-gallery-strip {" in css_template
        assert "backdrop-filter: var(--gallery-shell-backdrop-blur);" in css_template
        assert "--title-band-top: 728px;" in css_template
        assert "--gallery-shell-left: 96px;" in css_template
        assert "--title-band-width: 800px;" in css_template

    def test_template_css_exposes_family_a_product_region_observability_freeze_tokens(self):
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")

        assert "--product-shell-outline:" in css_template
        assert "--product-shell-glow:" in css_template
        assert "--annotation-card-inset:" in css_template
        assert "--annotation-leader-gradient:" in css_template
        assert "--annotation-marker-core-shadow:" in css_template
        assert "--annotation-label-letter-spacing:" in css_template
        assert "var(--product-shell-outline)," in css_template
        assert "var(--product-shell-glow);" in css_template
        assert "background: var(--annotation-leader-gradient);" in css_template
        assert "var(--annotation-marker-core-shadow);" in css_template

    def test_template_css_exposes_family_a_bottom_region_practical_closure_tokens(self):
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")

        assert "--bottom-shell-outline:" in css_template
        assert "--bottom-shell-glow:" in css_template
        assert "--title-band-inset:" in css_template
        assert "--title-band-outline:" in css_template
        assert "--subtitle-support-kicker:" in css_template
        assert "--gallery-shell-inset:" in css_template
        assert "--gallery-shell-outline:" in css_template
        assert "--gallery-item-inset:" in css_template
        assert ".text-subtitle::before" in css_template
        assert "var(--bottom-shell-outline)" in css_template
        assert "var(--gallery-shell-outline)" in css_template


class TestHeaderAndTitleBandLayoutControl:

    def test_template_html_uses_header_and_title_band_layout_wrappers(self):
        html_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.html"
        ).read_text(encoding="utf-8")

        assert 'class="layer-header-layout"' in html_template
        assert 'class="layer layer-header-identity-zone" data-slot="header_identity_zone_slot"' in html_template
        assert 'class="layer layer-brand-logo"' in html_template
        assert 'class="layer layer-brand-text"' in html_template
        assert 'class="layer layer-header-agent-zone" data-slot="header_agent_zone_slot"' in html_template
        assert 'class="layer layer-agent-name-text __AGENT_TEXT_CLASS__"' in html_template
        assert 'class="layer-title-band-layout"' in html_template

    def test_template_css_locks_header_width_budget_and_title_band_overflow_policy(self):
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")

        assert "--header-inner-left: 104px;" in css_template
        assert "--header-inner-right: 112px;" in css_template
        assert "--header-side-width: 228px;" in css_template
        assert "--header-logo-gap: 20px;" in css_template
        assert ".layer-header-layout {" in css_template
        assert "display: grid;" in css_template
        assert "grid-template-columns: minmax(0, 1fr) minmax(0, var(--header-side-width));" in css_template
        assert ".layer-header-identity-zone {" in css_template
        assert "grid-column: 1;" in css_template
        assert "justify-self: start;" in css_template
        assert "display: flex;" in css_template
        assert "gap: var(--header-logo-gap);" in css_template
        assert ".layer-header-agent-zone {" in css_template
        assert "grid-column: 2;" in css_template
        assert "justify-self: end;" in css_template
        assert ".layer-agent-name-text {" in css_template
        assert ".slot-agent-name-text {" in css_template
        assert ".text-agent-secondary {" in css_template
        assert ".header-agent-wrap .text-agent-secondary {" in css_template
        assert ".layer-header-banner.state-logo-empty {" in css_template
        assert ".layer-header-banner.state-logo-empty .layer-brand-logo" in css_template
        assert ".slot-title:empty," in css_template
        assert ".slot-subtitle:empty" in css_template

    def test_build_html_keeps_header_in_three_lanes_and_title_inside_title_band(self):
        renderer = PuppeteerStructuredRenderer()
        template = _load_real_template()
        html_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.html"
        ).read_text(encoding="utf-8")
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")
        slot_spec = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "slot_spec.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        anchor_map = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "anchor_map.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )

        html_payload = renderer._build_html(
            html_template=html_template,
            css_template=css_template,
            svg_overlay="",
            poster=_minimal_spec(subtitle=""),
            asset_urls={
                "logo": "data:image/png;base64,abc",
                "scenario": _safe_preset_scenario_data_url(),
                "scenario_is_real": False,
                "product": "data:image/png;base64,abc",
                "gallery": [],
            },
            slot_spec=slot_spec,
            anchor_map=anchor_map,
            spec=template,
        )

        assert 'class="layer-header-layout"' in html_payload
        assert 'class="layer layer-header-identity-zone" data-slot="header_identity_zone_slot"' in html_payload
        assert 'class="layer layer-brand-logo"' in html_payload
        assert 'class="layer layer-header-agent-zone" data-slot="header_agent_zone_slot"' in html_payload
        assert 'class="layer layer-agent-name-text state-show"' in html_payload
        assert "header-agent-wrap" in html_payload
        assert "--header-agent-line-clamp: 2" in html_payload
        assert 'class="layer-title-band-layout"' in html_payload
        assert 'data-region="title_band_region"' in html_payload

    def test_build_html_collapses_secondary_agent_text_when_empty(self):
        renderer = PuppeteerStructuredRenderer()
        template = _load_real_template()
        html_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.html"
        ).read_text(encoding="utf-8")
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")
        slot_spec = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "slot_spec.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        anchor_map = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "anchor_map.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )

        html_payload = renderer._build_html(
            html_template=html_template,
            css_template=css_template,
            svg_overlay="",
            poster=_minimal_spec(agent_name=""),
            asset_urls={
                "logo": "data:image/png;base64,abc",
                "scenario": _safe_preset_scenario_data_url(),
                "scenario_is_real": False,
                "product": "data:image/png;base64,abc",
                "gallery": [],
            },
            slot_spec=slot_spec,
            anchor_map=anchor_map,
            spec=template,
        )

        assert 'class="layer layer-header-identity-zone" data-slot="header_identity_zone_slot"' in html_payload
        assert 'class="layer layer-header-agent-zone" data-slot="header_agent_zone_slot"' in html_payload
        assert 'class="layer layer-agent-name-text state-hidden"' in html_payload


class TestFamilyAwareStructuredHtmlRouting:

    def test_family_a_render_asset_builder_keeps_a_semantics_only(self):
        renderer = PuppeteerStructuredRenderer()
        template = _load_real_template()
        behavior = resolve_template_behavior(
            template,
            feature_count=3,
            brand_name="厨厨房",
            agent_name="智能厨房顾问",
            gallery_requested_count=2,
            gallery_input_count_normalized=2,
            gallery_resolved_count=2,
        )
        slot_spec = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "slot_spec.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        assets = ResolvedAssets(
            product=solid_image(400, 600),
            scenario=solid_image(320, 600),
            gallery=[solid_image(176, 104), solid_image(176, 104)],
            gallery_status=[{"resolved": True}, {"resolved": True}],
            materials=[solid_image(160, 80)],
        )

        asset_urls, gallery_items_status = renderer._build_render_asset_urls(
            spec=template,
            assets=assets,
            slot_spec=slot_spec,
            behavior=behavior,
        )

        assert asset_urls["scenario"]
        assert asset_urls["gallery"]
        assert asset_urls["materials"] == []
        assert len(gallery_items_status) == 2

    def test_fryer_dense_quad_gallery_markup_emits_semantic_captions(self):
        renderer = PuppeteerStructuredRenderer()
        bottom_policy = resolve_bottom_behavior(
            "title_gallery_split",
            gallery_mode="strip_local_visible_only",
            title_text="Power Up Your Fry Station",
            subtitle_text="Fast heating, precise control, and durable stainless steel construction for everyday commercial use.",
            requested_gallery_count=4,
            normalized_gallery_count=4,
            resolved_gallery_count=4,
            max_items=4,
            commercial_fryer_variant=True,
        )

        markup, layer_class = renderer._gallery_markup(
            {},
            ["mock://g0", "mock://g1", "mock://g2", "mock://g3"],
            _apply_family_a_fryer_gallery_captions(
                [{"index": idx, "caption": ""} for idx in range(4)],
                bottom_policy,
            ),
            bottom_policy,
        )

        assert layer_class == "state-show"
        assert "Basket Detail" in markup
        assert "Single Tank" in markup
        assert "Lid Detail" in markup
        assert "Dual Tank" in markup

    def test_fryer_caption_helper_leaves_non_fryer_gallery_status_unchanged(self):
        bottom_policy = resolve_bottom_behavior(
            "title_gallery_split",
            gallery_mode="strip_local_visible_only",
            title_text="Upgrade your kitchen with ChefCraft Pro",
            subtitle_text="Available in stores from April 24th",
            requested_gallery_count=4,
            normalized_gallery_count=4,
            resolved_gallery_count=4,
            max_items=4,
            commercial_fryer_variant=False,
        )

        status = _apply_family_a_fryer_gallery_captions(
            [{"index": idx, "caption": ""} for idx in range(4)],
            bottom_policy,
        )

        assert all(not item.get("caption") for item in status)

    def test_family_b_render_asset_builder_keeps_b_semantics_only(self):
        renderer = PuppeteerStructuredRenderer()
        template = _load_template_b_template()
        behavior = resolve_template_behavior(
            template,
            feature_count=0,
            brand_name="KitchenWorks",
            agent_name="Dealer Team",
            has_product_secondary_asset=True,
            materials_count=2,
            title_text="Integrated Workstation Sink",
            subtitle_text="Precision-fitted accessories",
            description_title="Spec block",
            description_body="Short body",
            sku_text="KW-2401",
        )
        slot_spec = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "slot_spec.template_product_sheet_v1.json"
            ).read_text(encoding="utf-8")
        )
        assets = ResolvedAssets(
            product=solid_image(400, 600),
            product_secondary=solid_image(320, 320),
            scenario=solid_image(320, 600),
            gallery=[solid_image(176, 104)],
            gallery_status=[{"resolved": True}],
            materials=[solid_image(160, 80), solid_image(160, 80)],
        )

        asset_urls, gallery_items_status = renderer._build_render_asset_urls(
            spec=template,
            assets=assets,
            slot_spec=slot_spec,
            behavior=behavior,
        )

        assert asset_urls["scenario"] == ""
        assert asset_urls["gallery"] == []
        assert len(asset_urls["materials"]) == 2
        assert gallery_items_status == []

    def test_template_a_html_dispatch_does_not_emit_template_b_region_shells(self):
        renderer = PuppeteerStructuredRenderer()
        template = _load_real_template()
        html_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.html"
        ).read_text(encoding="utf-8")
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")
        slot_spec = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "slot_spec.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        anchor_map = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "anchor_map.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )

        html_payload = renderer._build_html(
            html_template=html_template,
            css_template=css_template,
            svg_overlay="",
            poster=_minimal_spec(),
            asset_urls={
                "logo": "",
                "scenario": _safe_preset_scenario_data_url(),
                "scenario_is_real": False,
                "product": "data:image/png;base64,abc",
                "product_secondary": "",
                "gallery": [],
                "materials": [],
            },
            slot_spec=slot_spec,
            anchor_map=anchor_map,
            spec=template,
        )

        assert 'data-region="title_band_region"' in html_payload
        assert 'data-region="gallery_strip_region"' in html_payload
        assert 'data-region="logo_banner_region"' not in html_payload
        assert 'data-region="top_copy_region"' not in html_payload
        assert 'data-region="description_region"' not in html_payload

    def test_template_a_html_keeps_product_slots_in_absolute_product_region_coordinates(self):
        renderer = PuppeteerStructuredRenderer()
        template = _load_real_template()
        behavior = resolve_template_behavior(
            template,
            feature_count=3,
            title_text="烹饪更智慧，生活更美味",
            subtitle_text="系列产品",
            brand_name="厨厨房",
            gallery_requested_count=0,
            gallery_input_count_normalized=0,
            gallery_resolved_count=0,
            agent_name="智能厨房顾问",
            has_product_secondary_asset=True,
        )
        html_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.html"
        ).read_text(encoding="utf-8")
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")
        slot_spec = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "slot_spec.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        anchor_map = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "anchor_map.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )

        html_payload = renderer._build_html(
            html_template=html_template,
            css_template=css_template,
            svg_overlay="",
            poster=_minimal_spec(product_secondary_image=AssetRef(url="mock://product-secondary")),
            asset_urls={
                "logo": "",
                "scenario": _safe_preset_scenario_data_url(),
                "scenario_is_real": False,
                "product": "data:image/png;base64,abc",
                "product_secondary": "data:image/png;base64,def",
                "gallery": [],
                "materials": [],
            },
            slot_spec=slot_spec,
            anchor_map=anchor_map,
            spec=template,
            behavior=behavior,
        )

        product_slot = _product_slot(slot_spec, behavior.hero_policy, behavior.product_policy)
        secondary_slot = _product_secondary_slot(slot_spec, behavior.product_policy)
        assert (
            f"left:{product_slot['x']}px;top:{product_slot['y']}px;"
            f"width:{product_slot['w']}px;height:{product_slot['h']}px"
        ) in html_payload
        assert (
            f"left:{secondary_slot['x']}px;top:{secondary_slot['y']}px;"
            f"width:{secondary_slot['w']}px;height:{secondary_slot['h']}px"
        ) in html_payload

    def test_template_b_html_dispatch_does_not_emit_template_a_bottom_or_feature_regions(self):
        renderer = PuppeteerStructuredRenderer()
        template = _load_template_b_template()
        html_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_product_sheet_v1.html"
        ).read_text(encoding="utf-8")
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_product_sheet_v1.css"
        ).read_text(encoding="utf-8")
        slot_spec = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "slot_spec.template_product_sheet_v1.json"
            ).read_text(encoding="utf-8")
        )

        html_payload = renderer._build_html(
            html_template=html_template,
            css_template=css_template,
            svg_overlay="",
            poster=_minimal_spec(
                brand_name="KitchenWorks",
                agent_name="Dealer Team",
                title="Integrated Workstation Sink",
                subtitle="Precision-fitted accessories",
                features=(),
                template_id="template_product_sheet_v1",
                sku_text="KW-2401",
                description_title="Spec block",
                description_body="Short body",
            ),
            asset_urls={
                "logo": "data:image/png;base64,logo",
                "scenario": "",
                "scenario_is_real": False,
                "product": "data:image/png;base64,abc",
                "product_secondary": "",
                "gallery": ["data:image/png;base64,wrong"],
                "materials": ["data:image/png;base64,mat"],
            },
            slot_spec=slot_spec,
            anchor_map={},
            spec=template,
        )

        assert 'data-region="logo_banner_region"' in html_payload
        assert 'data-region="top_copy_region"' in html_payload
        assert 'data-region="materials_strip_region"' in html_payload
        assert 'data-region="product_hero_region"' in html_payload
        assert 'data-region="description_region"' in html_payload
        assert 'data-region="feature_region"' not in html_payload
        assert 'data-region="title_band_region"' not in html_payload
        assert 'data-region="gallery_strip_region"' not in html_payload
        assert "data:image/png;base64,wrong" not in html_payload


class TestBottomSplitBehavior:

    def _render_html_payload(self, *, title: str, subtitle: str, gallery: list[str]) -> str:
        renderer = PuppeteerStructuredRenderer()
        template = _load_real_template()
        html_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.html"
        ).read_text(encoding="utf-8")
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")
        slot_spec = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "slot_spec.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        anchor_map = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "anchor_map.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        return renderer._build_html(
            html_template=html_template,
            css_template=css_template,
            svg_overlay="",
            poster=_minimal_spec(title=title, subtitle=subtitle),
            asset_urls={
                "logo": "",
                "scenario": _safe_preset_scenario_data_url(),
                "scenario_is_real": False,
                "product": "data:image/png;base64,abc",
                "gallery": gallery,
            },
            slot_spec=slot_spec,
            anchor_map=anchor_map,
            spec=template,
        )

    def test_bottom_split_title_only_keeps_title_band_and_hides_gallery_strip(self):
        html_payload = self._render_html_payload(title="Main title", subtitle="", gallery=[])
        assert "layer-bottom-region state-show state-title-only" in html_payload
        assert "layer-title-band-region-shell state-show" in html_payload
        assert "layer-title-subtitle state-show" in html_payload
        assert "layer-gallery-strip-region-shell state-hidden" in html_payload
        assert "layer-bottom-gallery-items state-hidden" in html_payload

    def test_bottom_split_gallery_only_hides_title_band_and_keeps_gallery_strip(self):
        html_payload = self._render_html_payload(
            title="",
            subtitle="",
            gallery=["data:image/png;base64,a", "data:image/png;base64,b"],
        )
        assert "layer-bottom-region state-show state-gallery-only" in html_payload
        assert "layer-title-band-region-shell state-hidden" in html_payload
        assert "layer-title-subtitle state-hidden" in html_payload
        assert "layer-gallery-strip-region-shell state-show" in html_payload
        assert "layer-bottom-gallery-items state-show" in html_payload

    def test_bottom_split_title_and_gallery_show_both_regions(self):
        html_payload = self._render_html_payload(
            title="Main title",
            subtitle="Sub title",
            gallery=["data:image/png;base64,a"],
        )
        assert "layer-bottom-region state-show state-title-gallery" in html_payload
        assert "layer-title-band-region-shell state-show" in html_payload
        assert "layer-title-subtitle state-show" in html_payload
        assert "layer-gallery-strip-region-shell state-show" in html_payload
        assert "layer-bottom-gallery-items state-show" in html_payload

    def test_bottom_split_dense_copy_uses_resolved_bottom_behavior_vars(self):
        html_payload = self._render_html_payload(
            title="超长标题超长标题超长标题超长标题",
            subtitle="这是一段更长的底部说明文案，用来验证 subtitle overflow、title band sizing 和 gallery peer balance 会不会进入 resolver 策略。",
            gallery=[
                "data:image/png;base64,a",
                "data:image/png;base64,b",
            ],
        )

        assert "--title-band-height: 192px" in html_payload
        assert "--title-line-clamp:" in html_payload
        assert "--subtitle-line-clamp: 2" in html_payload
        assert "--title-stack-gap: 8px" in html_payload
        assert "--gallery-shell-left: 96px" in html_payload
        assert "--gallery-shell-width: 832px" in html_payload

    def test_bottom_split_dense_quad_limits_title_growth_and_keeps_quad_distribution(self):
        html_payload = self._render_html_payload(
            title="超长标题超长标题超长标题超长标题",
            subtitle="这是一段更长的底部说明文案，用来验证 subtitle overflow、title band sizing 和 gallery peer balance 会不会进入 resolver 策略。",
            gallery=[
                "data:image/png;base64,a",
                "data:image/png;base64,b",
                "data:image/png;base64,c",
                "data:image/png;base64,d",
            ],
        )

        assert "--title-band-height: 176px" in html_payload  # PR-7C: 168→176
        assert "--subtitle-line-clamp: 2" in html_payload
        assert "--title-stack-gap: 8px" in html_payload  # PR-7C: 6→8
        assert "--gallery-shell-left: 96px" in html_payload
        assert "--gallery-shell-width: 832px" in html_payload
        assert "left:10px;top:8px;width:188px;height:60px;" in html_payload
        assert "left:634px;top:8px;width:188px;height:60px;" in html_payload

    def test_text_only_expanded_html_keeps_full_width_text_layer_vars(self):
        html_payload = self._render_html_payload(
            title="Main title",
            subtitle="Supporting subtitle copy",
            gallery=[],
        )

        assert "layer-bottom-region state-show state-title-only" in html_payload
        assert "--title-band-left: 96px" in html_payload
        assert "--title-band-width: 832px" in html_payload

    def test_text_only_expanded_html_keeps_subtitle_visible_while_gallery_stays_collapsed(self):
        html_payload = self._render_html_payload(
            title="Main title",
            subtitle="Supporting subtitle copy",
            gallery=[],
        )

        assert "layer-title-subtitle state-show" in html_payload
        assert "layer-subtitle state-show" in html_payload
        assert "layer-gallery-strip-region-shell state-hidden" in html_payload
        assert "layer-bottom-gallery-items state-hidden" in html_payload

    def test_template_css_exposes_independent_bottom_split_state_tokens(self):
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")

        assert "--bottom-shell-top: 728px;" in css_template
        assert "--bottom-shell-height: 232px;" in css_template
        assert "--gallery-items-top: 896px;" in css_template
        assert ".layer-bottom-region.state-title-only {" in css_template
        assert ".layer-bottom-region.state-gallery-only {" in css_template
        assert ".layer-bottom-region.state-title-gallery {" in css_template
        assert ".layer-bottom-gallery-items {" in css_template
        assert "top: var(--gallery-items-top);" in css_template
        assert "--title-stack-gap: 8px;" in css_template
        assert "-webkit-line-clamp: var(--title-line-clamp);" in css_template
        assert "-webkit-line-clamp: var(--subtitle-line-clamp);" in css_template

    def test_header_brand_only_mode_uses_resolved_header_behavior_vars(self):
        template = _load_real_template()
        template.behavior_modes = replace(template.behavior_modes, header_mode="brand_only")

        resolved = resolve_template_behavior(
            template,
            brand_name="厨厨房品牌馆",
            agent_name="智能顾问",
        )

        assert resolved.header_policy.identity_zone_mode == "brand_only"
        assert resolved.header_policy.agent_pill_visible is False
        assert resolved.header_policy.layout_metrics["header_banner_height"] == 96
        assert resolved.css_vars["--header-side-width"] == "0px"
        assert resolved.css_vars["--header-logo-width"] == "0px"

    def test_header_two_line_mode_emits_two_line_brand_class_and_vars_in_html(self):
        template = _load_real_template()
        template.behavior_modes = replace(template.behavior_modes, header_mode="brand_block_two_line")

        renderer = PuppeteerStructuredRenderer()
        poster = _minimal_spec(
            brand_name="这是一个需要两行显示的品牌名称示例",
            agent_name="智能顾问",
        )
        html_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.html"
        ).read_text(encoding="utf-8")
        css_template = (
            Path(__file__).resolve().parents[2] / "app" / "templates_html" / "template_dual_v2.css"
        ).read_text(encoding="utf-8")
        slot_spec = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "slot_spec.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        anchor_map = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "app"
                / "templates_html"
                / "anchor_map.template_dual_v2.json"
            ).read_text(encoding="utf-8")
        )
        behavior = resolve_template_behavior(
            template,
            brand_name=poster.brand_name,
            agent_name=poster.agent_name,
        )
        html_payload = renderer._build_html(
            html_template=html_template,
            css_template=css_template,
            svg_overlay="",
            poster=poster,
            asset_urls={
                "logo": "data:image/png;base64,abc",
                "scenario": _safe_preset_scenario_data_url(),
                "scenario_is_real": False,
                "product": "data:image/png;base64,abc",
                "gallery": [],
            },
            slot_spec=slot_spec,
            anchor_map=anchor_map,
            spec=template,
            behavior=behavior,
        )

        # PR-7A: class uses hyphens (css_mode_class replaces _ with -); CSS selector
        # previously used underscores (.header-mode-brand_block_two_line) but that
        # hardcoded rule was replaced by .header-brand-wrap in PR-7A.
        assert "header-mode-brand-block-two-line" in html_payload
        assert "header-brand-wrap" in html_payload
        assert "--header-brand-line-clamp: 2" in html_payload
        assert "--header-banner-height: 120px" in html_payload
        assert "--header-inner-height: 72px" in html_payload

    def test_single_product_focus_uses_resolved_product_anchor_and_hides_scenario(self):
        template = _load_real_template()
        template.behavior_modes = replace(template.behavior_modes, hero_mode="single_product_focus")

        resolved = resolve_template_behavior(
            template,
            brand_name="厨厨房",
            agent_name="智能顾问",
        )

        assert resolved.hero_policy.scenario_enabled is False
        assert resolved.hero_policy.product_anchor == "bottom"
        assert resolved.hero_policy.product_render_policy == "product_contain_bottom_weighted"
        assert resolved.hero_policy.peer_layout_policy == "single_product_without_scenario_peer"


class _FakeLocator:
    def __init__(self):
        self.wait_calls = []

    async def wait_for(self, **kwargs):
        self.wait_calls.append(kwargs)


class _FakePage:
    def __init__(self):
        self.locator_obj = _FakeLocator()
        self.ready_checks = []
        self.wait_timeouts = []
        self.evaluations = []

    def locator(self, selector):
        assert selector == "#poster-root"
        return self.locator_obj

    async def evaluate(self, expr):
        self.evaluations.append(expr)
        assert hero.product_policy.annotation_items[0]["label_bounds"] == {"x": 796, "y": 220, "w": 176, "h": 76}
        assert hero.product_policy.annotation_items[1]["label_bounds"] == {"x": 796, "y": 316, "w": 176, "h": 76}
        assert hero.product_policy.annotation_items[2]["label_bounds"] == {"x": 796, "y": 412, "w": 176, "h": 76}

    async def wait_for_function(self, expr, **kwargs):
        self.ready_checks.append((expr, kwargs))

    async def wait_for_timeout(self, timeout_ms):
        self.wait_timeouts.append(timeout_ms)


class TestProductShellBoundaryClosure:
    """PR-1: product_card_shell_layer CSS height must match contract h=540.

    The shared .region-shell-scenario, .region-shell-product rule sets height: 520px.
    The .region-shell-product override must explicitly set height: 540px so the outer
    shell bottom edge (y=728) aligns with the canvas shell and secondary slot bottom.

    Frozen boundary:
    - product_card_shell_layer (outer shell): left=456, top=188, width=472, height=540
    - product_canvas_shell_layer (image canvas): left=456, top=188, width=300, height=540
    """

    @staticmethod
    def _read_css() -> str:
        return (
            Path(__file__).resolve().parents[2]
            / "app"
            / "templates_html"
            / "template_dual_v2.css"
        ).read_text(encoding="utf-8")

    def test_product_card_shell_css_uses_product_shell_vars(self):
        """region-shell-product override must bind to product shell CSS vars."""
        import re
        css = self._read_css()
        match = re.search(
            r"\.region-shell-product\s*\{([^}]*)\}",
            css,
        )
        assert match, ".region-shell-product override block not found in CSS"
        block = match.group(1)
        assert "left: var(--product-shell-left);" in block
        assert "width: var(--product-shell-width);" in block
        assert "height: var(--product-shell-height);" in block

    def test_product_canvas_shell_css_uses_product_canvas_vars(self):
        """region-shell-product-canvas must bind to product canvas CSS vars."""
        import re
        css = self._read_css()
        match = re.search(r"\.region-shell-product-canvas\s*\{([^}]*)\}", css)
        assert match, ".region-shell-product-canvas block not found in CSS"
        block = match.group(1)
        assert "left: var(--product-canvas-left);" in block
        assert "width: var(--product-canvas-width);" in block
        assert "height: var(--product-canvas-height);" in block

    def test_product_card_shell_layer_present_in_html(self):
        """HTML must mark the outer product shell with data-layer=product_card_shell_layer."""
        html = (
            Path(__file__).resolve().parents[2]
            / "app"
            / "templates_html"
            / "template_dual_v2.html"
        ).read_text(encoding="utf-8")
        assert 'data-layer="product_card_shell_layer"' in html
        assert 'data-layer="product_canvas_shell_layer"' in html

    def test_root_css_declares_default_product_shell_metrics(self):
        """Template CSS must declare fallback product shell metrics for non-fryer renders."""
        import re
        css = self._read_css()
        root_match = re.search(r"#poster-root\s*\{([^}]*)\}", css)
        assert root_match, "#poster-root block not found"
        root_block = root_match.group(1)
        assert "--product-shell-left: 456px;" in root_block
        assert "--product-shell-top: 188px;" in root_block
        assert "--product-shell-height: 540px;" in root_block
        assert "--product-canvas-left: 456px;" in root_block
        assert "--product-canvas-top: 188px;" in root_block
        assert "--product-canvas-height: 540px;" in root_block


class TestPuppeteerHardening:

    def test_stabilize_page_waits_for_root_and_layout_flush(self):
        renderer = PuppeteerStructuredRenderer(
            render_timeout_ms=1234,
            font_ready_grace_ms=100,
        )
        page = _FakePage()

        asyncio.run(renderer._stabilize_page_for_screenshot(page))

        assert page.locator_obj.wait_calls == [{"state": "visible", "timeout": 1234}]
        assert page.evaluations
        assert page.ready_checks[0][1]["timeout"] == 1234
        assert page.wait_timeouts == [32]
