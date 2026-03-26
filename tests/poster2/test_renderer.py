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
import json
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
    _safe_preset_scenario_data_url,
    _visible_gallery_item_count,
    _prepare_gallery_urls,
)
from app.services.poster2.renderer_routing import RendererRoutingError, resolve_renderer_routing
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
    """Verify computed gallery item x-positions match template_dual_spec.json."""

    def test_four_item_positions(self):
        template = _load_real_template()
        gs = template.gallery_slot
        expected = [96, 308, 520, 732]
        for i, ex_x in enumerate(expected):
            computed = gs.x + i * (gs.thumb_w + gs.gap)
            assert computed == ex_x, (
                f"Gallery item {i}: expected x={ex_x}, got x={computed}"
            )

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

        markup, layer_class = renderer._gallery_markup(
            slot_spec,
            ["data:image/png;base64,a", "data:image/png;base64,b"],
        )

        assert layer_class == "state-show"
        assert 'left:0px;top:0px;width:196px;height:56px;' in markup
        assert 'left:212px;top:0px;width:196px;height:56px;' in markup

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

        markup, layer_class = renderer._gallery_markup(slot_spec, ["a.png", "b.png"])

        assert layer_class == "state-show"
        assert markup.count("gallery-item") == 2
        assert markup.count('src="a.png"') == 1
        assert markup.count('src="b.png"') == 1

    def test_empty_gallery_hides_bottom_layer(self):
        renderer = PuppeteerStructuredRenderer()
        slot_spec = {"slots": {"gallery": [{"x": 0, "y": 0, "w": 10, "h": 10}]}}

        markup, layer_class = renderer._gallery_markup(slot_spec, [])

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

        markup, layer_class = renderer._gallery_markup(slot_spec, ["a.png", "b.png"])

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

        markup, layer_class = renderer._feature_markup(anchor_map, ("One",))

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

        markup, layer_class = renderer._feature_markup(anchor_map, ("One", " ", "Three"))

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

        markup, layer_class = renderer._feature_markup(anchor_map, ("One", "Two", "Three", "Four"))

        assert layer_class == "state-show feature-mode-4"
        assert markup.count('class="feature-callout feature-mode-box-4"') == 4
        assert markup.count("connector-policy-dense_quad") == 4

    def test_feature_markup_hides_when_empty(self):
        renderer = PuppeteerStructuredRenderer()

        markup, layer_class = renderer._feature_markup({"feature_callouts": []}, ())

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
        assert "layer-hero-peer-region state-safe-fill state-fit-cover state-anchor-center" in html_payload
        assert "scenario-fit-cover" in html_payload
        assert "layer layer-product-content state-fit-contain state-anchor-bottom" in html_payload
        assert "product-fit-contain" in html_payload
        assert 'data-region="title_band_region"' in html_payload
        assert 'data-region="feature_region"' in html_payload
        assert "__SVG_OVERLAY__" not in html_payload

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

        assert "layer-hero-peer-region state-real state-fit-cover state-anchor-center" in html_payload
        assert "region-shell-scenario state-real" in html_payload
        assert "layer layer-product layer-hero-peer-region state-fit-contain state-anchor-bottom" in html_payload

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
        assert "object-position: center bottom;" in css_template
        assert ".layer-feature-callouts.feature-mode-1 .feature-callout" in css_template
        assert ".layer-feature-callouts.feature-mode-4 .feature-callout" in css_template


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
        return True

    async def wait_for_function(self, expr, **kwargs):
        self.ready_checks.append((expr, kwargs))

    async def wait_for_timeout(self, timeout_ms):
        self.wait_timeouts.append(timeout_ms)


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
