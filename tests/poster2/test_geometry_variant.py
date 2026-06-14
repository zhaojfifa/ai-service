"""
Tests for the template_dual_v2_studio geometry style variant
(HX-POSTER2-STYLE-VARIANT-V1).

The variant changes BOUNDED geometry (the product image floats inside its
unchanged card) plus typography/surface via its own spec + CSS. These tests lock
the contract: protected region bounds, ownership, the 3 annotation slots, and the
bottom geometry stay identical to the base; base/airy are unaffected.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

from app.services.poster2.contracts import TemplateSpec
from app.services.poster2.pipeline import load_template
from app.services.poster2.skills.control.family_a_control_surface_v1 import build_control_surface
from app.services.poster2.skills.structure.family_a_structure_surface_v1 import build_structure_surface
from app.services.poster2.template_behavior import resolve_template_behavior
from app.services.poster2.template_registry import (
    get_template_registry,
    is_campaign_explainer_template,
    resolve_template_metadata,
)

_REPO = Path(__file__).resolve().parents[2]
_ASSETS = _REPO / "app" / "templates_html"
_PROTECTED_REGIONS = (
    "header_region", "scenario_region", "product_region", "feature_region",
    "bottom_region", "title_band_region", "gallery_strip_region",
)


def _resolve(spec: TemplateSpec):
    return resolve_template_behavior(
        spec, feature_count=3, product_image_size=(640, 900),
        title_text="商用电炸炉 高效之选", subtitle_text="高效稳定 安全耐用",
        brand_name="厨匠", agent_name="顾问",
        gallery_requested_count=4, gallery_input_count_normalized=4, gallery_resolved_count=4)


def _geometry(spec: TemplateSpec):
    return build_structure_surface(spec, resolved_behavior=_resolve(spec),
                                   layer_render_status={}, region_render_status={})


# ── registry / membership ─────────────────────────────────────────────────────


def test_studio_registered_with_matching_version():
    meta = resolve_template_metadata("template_dual_v2_studio")
    spec = load_template("template_dual_v2_studio")
    assert meta.template_version == spec.version
    assert meta.template_family == resolve_template_metadata("template_dual_v2").template_family
    assert "template_dual_v2_studio" in get_template_registry()


def test_studio_is_campaign_explainer_member():
    assert is_campaign_explainer_template("template_dual_v2_studio") is True


def test_geometry_profile_defaults_for_base_and_airy():
    assert load_template("template_dual_v2").behavior_modes.geometry_profile == "default"
    assert load_template("template_dual_v2_airy").behavior_modes.geometry_profile == "default"
    assert load_template("template_dual_v2_studio").behavior_modes.geometry_profile == "studio_breathing_v1"


# ── the bounded geometry delta ────────────────────────────────────────────────


def test_studio_floats_product_image_only():
    base = _resolve(load_template("template_dual_v2"))
    studio = _resolve(load_template("template_dual_v2_studio"))
    # product IMAGE slot shrinks/centres...
    assert studio.product_policy.product_primary_slot != base.product_policy.product_primary_slot
    assert studio.product_policy.product_primary_slot == {"x": 474, "y": 224, "w": 264, "h": 468}


def test_studio_protected_region_bounds_identical_to_base():
    base_geo = _geometry(load_template("template_dual_v2"))
    studio_geo = _geometry(load_template("template_dual_v2_studio"))
    for region in _PROTECTED_REGIONS:
        assert base_geo["region_bounds"][region] == studio_geo["region_bounds"][region], region
    # gallery visible count + all per-region counts unchanged (bottom SOP intact)
    assert base_geo["visible_item_count"] == studio_geo["visible_item_count"]


def test_studio_only_product_image_slot_changes():
    base_geo = _geometry(load_template("template_dual_v2"))
    studio_geo = _geometry(load_template("template_dual_v2_studio"))
    product_image_slots = {"product_slot", "product_primary_slot"}
    changed = {
        k for k in set(base_geo["slot_bounds"]) | set(studio_geo["slot_bounds"])
        if base_geo["slot_bounds"].get(k) != studio_geo["slot_bounds"].get(k)
    }
    assert changed and changed.issubset(product_image_slots), f"unexpected slot changes: {changed}"


def test_studio_ownership_and_annotation_preserved():
    base_ctrl = build_control_surface(_resolve(load_template("template_dual_v2")))
    studio_ctrl = build_control_surface(_resolve(load_template("template_dual_v2_studio")))
    assert base_ctrl["ownership_guards"] == studio_ctrl["ownership_guards"]
    assert studio_ctrl["ownership_guards"]["product_annotation_owner_region"] == "product_region"
    assert studio_ctrl["ownership_guards"]["title_owner_region"] == "title_band_region"


# ── variant assets: only the CSS differs ─────────────────────────────────────


def test_studio_non_css_assets_are_byte_identical_to_base():
    for base_name in (
        "template_dual_v2.html", "template_dual_v2.svg",
        "slot_spec.template_dual_v2.json", "anchor_map.template_dual_v2.json",
    ):
        studio_name = base_name.replace("template_dual_v2", "template_dual_v2_studio")
        assert (_ASSETS / base_name).read_bytes() == (_ASSETS / studio_name).read_bytes(), base_name


def test_studio_css_differs_from_base():
    base_css = (_ASSETS / "template_dual_v2.css").read_text(encoding="utf-8")
    studio_css = (_ASSETS / "template_dual_v2_studio.css").read_text(encoding="utf-8")
    assert base_css != studio_css
    assert "font-size: 52px" in studio_css  # stronger title


def _spec_dict_without_variant_identity(spec: TemplateSpec) -> dict:
    d = dataclasses.asdict(spec)
    for k in ("template_id", "version"):
        d.pop(k, None)
    d.get("behavior_modes", {}).pop("geometry_profile", None)
    # title/subtitle font sizes are intentional typography deltas
    for slot in ("title_slot", "subtitle_slot"):
        if isinstance(d.get(slot), dict):
            d[slot].pop("font_size", None)
            d[slot].pop("line_height", None)
    return d


def test_studio_spec_differs_only_by_allowed_fields():
    base = _spec_dict_without_variant_identity(load_template("template_dual_v2"))
    studio = _spec_dict_without_variant_identity(load_template("template_dual_v2_studio"))
    assert base == studio, "studio spec must differ only by id/version/geometry_profile/title typography"
