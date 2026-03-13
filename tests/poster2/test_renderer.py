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

import json
from pathlib import Path

import pytest
from PIL import Image as PILImage

from app.services.poster2.contracts import (
    AssetRef,
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
    _apply_radius,
    _fit_image,
    _wrap_text,
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


# ── Gallery strip position test ───────────────────────────────────────────────

class TestGalleryPositions:
    """Verify computed gallery item x-positions match template_dual_spec.json."""

    def test_four_item_positions(self):
        template = _load_real_template()
        gs = template.gallery_slot
        expected = [112, 304, 496, 688]
        for i, ex_x in enumerate(expected):
            computed = gs.x + i * (gs.thumb_w + gs.gap)
            assert computed == ex_x, (
                f"Gallery item {i}: expected x={ex_x}, got x={computed}"
            )
