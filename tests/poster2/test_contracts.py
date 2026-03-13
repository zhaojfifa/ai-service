"""
Unit tests for contracts.py — TemplateSpec JSON loading and dataclass invariants.
No network, no AI, no R2 required.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.services.poster2.contracts import (
    AssetRef,
    GalleryStripSpec,
    ImageSlotSpec,
    PosterSpec,
    RenderManifest,
    StyleSpec,
    TemplateSpec,
    TextSlotSpec,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

MINIMAL_TEMPLATE_DICT = {
    "template_id": "test_tmpl",
    "version": "1.0.0",
    "canvas_w": 1024,
    "canvas_h": 1024,
    "safe_margin": 48,
    "background_prompt_hint": "clean studio",
    "logo_slot": {"x": 0, "y": 0, "w": 100, "h": 50},
    "brand_name_slot": {
        "x": 110, "y": 0, "w": 300, "h": 50,
        "font_key": "brand_bold", "font_size": 28, "color": "#000",
        "align": "left", "max_lines": 1, "line_height": 1.2, "auto_shrink": True,
    },
    "agent_name_slot": {
        "x": 700, "y": 0, "w": 200, "h": 50,
        "font_key": "brand_regular", "font_size": 20, "color": "#000",
        "align": "right", "max_lines": 1, "line_height": 1.2, "auto_shrink": True,
    },
    "title_slot": {
        "x": 50, "y": 800, "w": 900, "h": 80,
        "font_key": "brand_bold", "font_size": 40, "color": "#E8002A",
        "align": "center", "max_lines": 2, "line_height": 1.15, "auto_shrink": True,
    },
    "subtitle_slot": {
        "x": 50, "y": 900, "w": 900, "h": 30,
        "font_key": "brand_regular", "font_size": 20, "color": "#E8002A",
        "align": "center", "max_lines": 1, "line_height": 1.2, "auto_shrink": True,
    },
    "product_slot": {"x": 500, "y": 200, "w": 400, "h": 600},
    "gallery_slot": {"x": 50, "y": 880, "w": 900, "h": 100, "thumb_w": 200},
    "features_slot": [
        {
            "x": 50, "y": 300, "w": 200, "h": 60,
            "font_key": "feature", "font_size": 16, "color": "#000",
            "align": "left", "max_lines": 2, "line_height": 1.3, "auto_shrink": True,
        }
    ],
}


@pytest.fixture
def template_json_file(tmp_path: Path) -> Path:
    p = tmp_path / "test_tmpl.json"
    p.write_text(json.dumps(MINIMAL_TEMPLATE_DICT), encoding="utf-8")
    return p


# ── TemplateSpec loading ──────────────────────────────────────────────────────

class TestTemplateSpecLoading:

    def test_from_dict_roundtrip(self):
        spec = TemplateSpec._from_dict(MINIMAL_TEMPLATE_DICT)
        assert spec.template_id == "test_tmpl"
        assert spec.version == "1.0.0"
        assert spec.canvas_w == 1024
        assert spec.canvas_h == 1024
        assert isinstance(spec.logo_slot, ImageSlotSpec)
        assert isinstance(spec.brand_name_slot, TextSlotSpec)
        assert isinstance(spec.gallery_slot, GalleryStripSpec)
        assert len(spec.features_slot) == 1
        assert spec.scenario_slot is None  # optional, not in minimal dict

    def test_from_json_file(self, template_json_file: Path):
        spec = TemplateSpec.from_json(template_json_file)
        assert spec.template_id == "test_tmpl"

    def test_real_template_dual_v2_loads(self):
        """Smoke test: the shipped template_dual_v2.json must parse without errors."""
        real_path = (
            Path(__file__).resolve().parents[2]
            / "app" / "templates" / "specs" / "template_dual_v2.json"
        )
        assert real_path.exists(), f"template_dual_v2.json missing at {real_path}"
        spec = TemplateSpec.from_json(real_path)
        assert spec.canvas_w == 1024
        assert spec.canvas_h == 1024
        assert len(spec.features_slot) == 4
        assert spec.gallery_slot.count == 4
        assert spec.gallery_slot.thumb_w == 176

    def test_gallery_slot_position_math(self):
        """Verify gallery item positions match template_dual_spec.json exactly."""
        real_path = (
            Path(__file__).resolve().parents[2]
            / "app" / "templates" / "specs" / "template_dual_v2.json"
        )
        spec = TemplateSpec.from_json(real_path)
        gs = spec.gallery_slot
        expected_x = [112, 304, 496, 688]  # from template_dual_spec.json
        for i, ex in enumerate(expected_x):
            computed = gs.x + i * (gs.thumb_w + gs.gap)
            assert computed == ex, (
                f"Gallery item {i}: expected x={ex}, got x={computed}"
            )

    def test_missing_json_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            TemplateSpec.from_json(tmp_path / "nonexistent.json")


# ── PosterSpec immutability ───────────────────────────────────────────────────

class TestPosterSpec:

    def _make_spec(self, **overrides):
        defaults = dict(
            brand_name="厨厨房",
            agent_name="智能顾问",
            title="烹饪更智慧",
            subtitle="系列产品",
            features=("特性A", "特性B"),
            product_image=AssetRef(url="https://example.com/p.png"),
        )
        defaults.update(overrides)
        return PosterSpec(**defaults)

    def test_basic_creation(self):
        spec = self._make_spec()
        assert spec.brand_name == "厨厨房"
        assert isinstance(spec.style, StyleSpec)

    def test_frozen(self):
        spec = self._make_spec()
        with pytest.raises((AttributeError, TypeError)):
            spec.brand_name = "other"  # type: ignore[misc]

    def test_custom_style(self):
        spec = self._make_spec(
            style=StyleSpec(prompt="warm kitchen", seed=42)
        )
        assert spec.style.seed == 42
        assert spec.style.prompt == "warm kitchen"

    def test_gallery_images_tuple(self):
        spec = self._make_spec(
            gallery_images=(
                AssetRef(url="https://x.com/1.png"),
                AssetRef(url="https://x.com/2.png"),
            )
        )
        assert len(spec.gallery_images) == 2


# ── RenderManifest ────────────────────────────────────────────────────────────

class TestRenderManifest:

    def test_to_dict(self):
        m = RenderManifest(
            trace_id="abc",
            template_id="t",
            template_version="1.0",
            engine_version="2.0.0",
            poster_spec_hash="deadbeef",
            resolved_inputs={"brand_name": "厨厨房"},
            background_url="https://r2.example.com/bg.png",
            background_prompt="studio",
            background_seed=42,
            background_model="firefly-v3",
            foreground_url="https://r2.example.com/fg.png",
            foreground_hash="aabbcc",
            final_url="https://r2.example.com/final.png",
            final_hash="ddeeff",
            timings_ms={"total_ms": 3200},
        )
        d = m.to_dict()
        assert d["trace_id"] == "abc"
        assert d["background_seed"] == 42
        assert d["degraded"] is False
