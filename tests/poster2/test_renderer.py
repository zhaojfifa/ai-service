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
    _safe_preset_scenario_data_url,
    load_structured_slot_spec,
    render_content_debug_layer,
    render_slot_structure_debug_layer,
    render_structure_overlay_debug_layer,
    render_text_debug_layer,
)


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

    def test_real_template_agent_slot_has_pill(self):
        """Real template: agent_name_slot has bg_color and bg_radius set."""
        template = _load_real_template()
        slot = template.agent_name_slot
        assert slot.bg_color == "#E8002A"
        assert slot.bg_radius == 24
        assert slot.color == "#FFFFFF"


class TestStructuredGalleryMarkup:

    def test_partial_gallery_is_deterministically_filled(self):
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

        assert layer_class == "state-fallback-fill"
        assert markup.count("gallery-item") == 4
        assert markup.count('src="a.png"') == 2
        assert markup.count('src="b.png"') == 2

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


class TestStructuredDebugLayers:

    def test_slot_structure_debug_layer_renders(self):
        template = _load_real_template()
        slot_spec = load_structured_slot_spec(template.template_id)
        result = render_slot_structure_debug_layer(template, slot_spec)
        assert result.render_engine_used == "debug"
        assert result.foreground_renderer == "poster2.debug_slot_structure"
        assert len(result.png_bytes) > 1000

    def test_content_debug_layer_renders_safe_preset_scenario(self):
        template = _load_real_template()
        assets = _minimal_assets(scenario=None)
        result = render_content_debug_layer(template, assets)
        assert result.foreground_renderer == "poster2.debug_content_layer"
        assert len(result.png_bytes) > 1000

    def test_text_debug_layer_renders_text_only_pass(self):
        template = _load_real_template()
        result = render_text_debug_layer(template, _minimal_spec())
        assert result.foreground_renderer == "poster2.debug_text_layer"
        assert len(result.png_bytes) > 1000

    def test_structure_overlay_debug_layer_renders_metadata_annotations(self):
        template = _load_real_template()
        slot_spec = load_structured_slot_spec(template.template_id)
        slot_metadata = {
            "regions": {
                "header_region": {
                    "brand_logo_slot": {
                        "rendered": False,
                        "reason": "logo_not_bound",
                        "bounds": [104, 74, 120, 64],
                    }
                }
            }
        }
        result = render_structure_overlay_debug_layer(template, slot_spec, slot_metadata)
        assert result.foreground_renderer == "poster2.debug_structure_overlay"
        assert len(result.png_bytes) > 1000
