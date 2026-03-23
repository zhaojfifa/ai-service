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
    FeatureCalloutSpec,
    GalleryStripSpec,
    ImageSlotSpec,
    PosterSpec,
    RenderDebugArtifacts,
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
        assert spec.contract_version == "poster2.template.v1"
        assert spec.canvas_w == 1024
        assert spec.canvas_h == 1024
        assert isinstance(spec.logo_slot, ImageSlotSpec)
        assert isinstance(spec.brand_name_slot, TextSlotSpec)
        assert isinstance(spec.gallery_slot, GalleryStripSpec)
        # Legacy features_slot key → parsed as feature_callouts with anchor_radius=0
        assert len(spec.feature_callouts) == 1
        assert spec.feature_callouts[0].anchor_radius == 0
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
        assert spec.contract_version == "poster2.template_dual_v2.v1"
        assert len(spec.feature_callouts) == 4
        assert spec.gallery_slot.count == 4
        assert spec.version == "2.1.2"
        assert spec.gallery_slot.thumb_w == 196
        # Agent name slot has CTA pill style
        assert spec.agent_name_slot.bg_color == "#E8002A"
        assert spec.agent_name_slot.bg_radius == 24
        assert spec.subtitle_slot.y + spec.subtitle_slot.h <= spec.canvas_h - spec.safe_margin
        assert spec.gallery_slot.y + spec.gallery_slot.h <= spec.canvas_h - spec.safe_margin
        assert spec.scenario_slot is not None
        assert spec.scenario_slot.x == 96
        assert spec.product_slot.w == 300

    def test_gallery_slot_position_math(self):
        """Verify gallery item positions match template_dual_spec.json exactly."""
        real_path = (
            Path(__file__).resolve().parents[2]
            / "app" / "templates" / "specs" / "template_dual_v2.json"
        )
        spec = TemplateSpec.from_json(real_path)
        gs = spec.gallery_slot
        expected_x = [96, 308, 520, 732]
        for i, ex in enumerate(expected_x):
            computed = gs.x + i * (gs.thumb_w + gs.gap)
            assert computed == ex, (
                f"Gallery item {i}: expected x={ex}, got x={computed}"
            )

    def test_missing_json_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            TemplateSpec.from_json(tmp_path / "nonexistent.json")

    def test_feature_callouts_with_anchors(self):
        """feature_callouts key with anchor data is parsed into FeatureCalloutSpec."""
        d = {**MINIMAL_TEMPLATE_DICT}
        del d["features_slot"]
        d["feature_callouts"] = [
            {
                "anchor_x": 520, "anchor_y": 324,
                "anchor_radius": 7,
                "anchor_color": "#E8002A",
                "leader_color": "#E8002A",
                "leader_width": 2,
                "label_box": {
                    "x": 536, "y": 288, "w": 344, "h": 72,
                    "font_key": "feature", "font_size": 16, "color": "#1A1A1A",
                    "align": "left", "max_lines": 2, "line_height": 1.3, "auto_shrink": True,
                },
            }
        ]
        spec = TemplateSpec._from_dict(d)
        assert len(spec.feature_callouts) == 1
        fc = spec.feature_callouts[0]
        assert isinstance(fc, FeatureCalloutSpec)
        assert fc.anchor_x == 520
        assert fc.anchor_y == 324
        assert fc.anchor_radius == 7
        assert fc.anchor_color == "#E8002A"
        assert fc.label_box.x == 536
        assert fc.label_box.font_key == "feature"

    def test_agent_name_slot_cta_fields(self):
        """agent_name_slot with bg_color/bg_radius is parsed into TextSlotSpec."""
        d = {**MINIMAL_TEMPLATE_DICT}
        d["agent_name_slot"] = {
            **d["agent_name_slot"],
            "bg_color": "#E8002A",
            "bg_radius": 34,
        }
        spec = TemplateSpec._from_dict(d)
        assert spec.agent_name_slot.bg_color == "#E8002A"
        assert spec.agent_name_slot.bg_radius == 34

    def test_structured_template_assets_exist(self):
        base = Path(__file__).resolve().parents[2] / "app" / "templates_html"
        html_path = base / "template_dual_v2.html"
        css_path = base / "template_dual_v2.css"
        svg_path = base / "template_dual_v2.svg"
        slot_spec_path = base / "slot_spec.template_dual_v2.json"
        anchor_map_path = base / "anchor_map.template_dual_v2.json"

        assert html_path.exists()
        assert css_path.exists()
        assert svg_path.exists()
        assert slot_spec_path.exists()
        assert anchor_map_path.exists()

        slot_spec = json.loads(slot_spec_path.read_text(encoding="utf-8"))
        anchor_map = json.loads(anchor_map_path.read_text(encoding="utf-8"))
        assert slot_spec["template_contract_version"] == "poster2.template_dual_v2.v1"
        assert "layers" in slot_spec
        assert "layer_slots" in slot_spec
        assert "regions" in slot_spec
        assert "slot_contracts" in slot_spec
        assert "layer_states" in slot_spec
        assert "layer_contracts" in slot_spec
        assert "header_banner" in slot_spec["layers"]
        assert "background_base_layer" in slot_spec["layers"]
        assert "background_tone_layer" in slot_spec["layers"]
        assert "header_shell_layer" in slot_spec["layers"]
        assert "brand_logo_layer" in slot_spec["layers"]
        assert "brand_text_layer" in slot_spec["layers"]
        assert "agent_pill_layer" in slot_spec["layers"]
        assert "scenario_card_shell_layer" in slot_spec["layers"]
        assert "scenario_image_layer" in slot_spec["layers"]
        assert "product_card_shell_layer" in slot_spec["layers"]
        assert "product_image_layer" in slot_spec["layers"]
        assert "feature_callout_layer" in slot_spec["layers"]
        assert "title_layer" in slot_spec["layers"]
        assert "subtitle_layer" in slot_spec["layers"]
        assert "bottom_gallery" in slot_spec["layers"]
        assert "bottom_gallery_shell_layer" in slot_spec["layers"]
        assert "bottom_gallery_items_layer" in slot_spec["layers"]
        assert "bottom_tagline_layer" in slot_spec["layers"]
        assert "scenario" in slot_spec["layers"]
        assert "header_region" in slot_spec["regions"]
        assert "scenario_region" in slot_spec["regions"]
        assert "product_region" in slot_spec["regions"]
        assert "feature_region" in slot_spec["regions"]
        assert "bottom_region" in slot_spec["regions"]
        for slot_name in [
            "background_base_layer",
            "background_tone_layer",
            "header_shell_layer",
            "brand_logo_slot",
            "brand_text_slot",
            "agent_pill_slot",
            "scenario_card_shell_slot",
            "scenario_image_slot",
            "product_card_shell_slot",
            "product_image_slot",
            "feature_callout_slots",
            "title_box",
            "subtitle_box",
            "gallery_shell_slot",
            "gallery_item_slots",
            "tagline_box",
        ]:
            assert slot_name in slot_spec["slot_contracts"]
            slot_contract = slot_spec["slot_contracts"][slot_name]
            assert "slot_id" in slot_contract
            assert "region_id" in slot_contract
            assert "bounds" in slot_contract
            assert "visible_when" in slot_contract
            assert "source_binding" in slot_contract
            assert "fallback_rule" in slot_contract
            assert "collapse_rule" in slot_contract
        assert "brand_logo_slot" in slot_spec["layer_slots"]
        assert "scenario" in slot_spec["layer_states"]
        assert "state-safe-fill" in slot_spec["layer_states"]["scenario"]
        for layer_name in [
            "background_base_layer",
            "header_shell_layer",
            "brand_logo_layer",
            "brand_text_layer",
            "agent_pill_layer",
            "scenario_card_shell_layer",
            "scenario_image_layer",
            "product_card_shell_layer",
            "product_image_layer",
            "feature_callout_layer",
            "title_layer",
            "subtitle_layer",
            "bottom_gallery_shell_layer",
            "bottom_gallery_items_layer",
            "bottom_tagline_layer",
        ]:
            assert layer_name in slot_spec["layer_contracts"]
            contract = slot_spec["layer_contracts"][layer_name]
            assert "visible_when" in contract
            assert "bounds" in contract
            assert "fallback_rule" in contract
            assert "collapse_rule" in contract
        brand_logo_contract = slot_spec["layer_contracts"]["brand_logo_layer"]
        scenario_image_contract = slot_spec["layer_contracts"]["scenario_image_layer"]
        bottom_gallery_items_contract = slot_spec["layer_contracts"]["bottom_gallery_items_layer"]
        assert brand_logo_contract["visible_when"] == "logo.url exists"
        assert brand_logo_contract["max_items"] == 1
        assert brand_logo_contract["max_lines"] == 0
        assert scenario_image_contract["visible_when"] == "scenario_image.url exists or safe preset fill is resolved"
        assert scenario_image_contract["max_items"] == 1
        assert scenario_image_contract["max_lines"] == 0
        assert "background_base_layer must not substitute" in scenario_image_contract["fallback_rule"]
        assert bottom_gallery_items_contract["visible_when"] == "gallery_images.length > 0"
        assert bottom_gallery_items_contract["max_items"] == 4
        assert bottom_gallery_items_contract["max_lines"] == 0
        assert "ghost placeholders" in bottom_gallery_items_contract["fallback_rule"]
        assert "fallback-fill" in slot_spec["layer_contracts"]["bottom_gallery_shell_layer"]["visible_when"]
        assert slot_spec["layer_contracts"]["bottom_tagline_layer"]["visible_when"] == "operator tagline binding exists"
        assert slot_spec["slot_contracts"]["scenario_image_slot"]["fallback_rule"] == "safe_preset_fill_if_absent"
        assert slot_spec["slot_contracts"]["gallery_item_slots"]["collapse_rule"] == "hide_full_gallery_strip_when_empty"
        assert "protected_zones" in slot_spec
        assert len(slot_spec["slots"]["gallery"]) == 4
        assert len(anchor_map["feature_callouts"]) == 4


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
            template_contract_version="poster2.template.v1",
            engine_version="2.0.0",
            renderer_mode="auto",
            render_engine_used="pillow",
            foreground_renderer="poster2.pillow_layout",
            background_renderer="firefly-v3",
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
            debug_artifacts=RenderDebugArtifacts(
                background_layer_url="https://r2.example.com/bg.png",
                product_material_layer_url="https://r2.example.com/product-material.png",
                foreground_layer_url="https://r2.example.com/fg.png",
                final_composited_url="https://r2.example.com/final.png",
                renderer_metadata_url="https://r2.example.com/renderer-metadata.json",
                slot_structure_layer_url="https://r2.example.com/slot-structure.png",
                content_layer_url="https://r2.example.com/content-layer.png",
                text_layer_url="https://r2.example.com/text-layer.png",
                structure_overlay_url="https://r2.example.com/structure-overlay.png",
                slot_metadata_url="https://r2.example.com/slot-metadata.json",
            ),
        )
        d = m.to_dict()
        assert d["trace_id"] == "abc"
        assert d["background_seed"] == 42
        assert d["render_engine_used"] == "pillow"
        assert d["debug_artifacts"]["renderer_metadata_url"] == "https://r2.example.com/renderer-metadata.json"
        assert d["debug_artifacts"]["slot_metadata_url"] == "https://r2.example.com/slot-metadata.json"
        assert d["degraded"] is False
