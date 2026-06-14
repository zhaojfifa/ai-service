"""
Tests for the poster2 Composition Priority Layer (HX-POSTER2-COMPOSITION-PRIORITY-V1).

Locks the contract: closed-enum strategies, balanced = no-op, the bundle is
non-geometric (scenario/shadow/text vars only), product_hero uses the full product
geometry (== base), and base/airy are unaffected.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.schemas.poster2 import GeneratePosterV2Request
from app.services.poster2.composition import (
    COMPOSITION_CSS_VAR_WHITELIST,
    COMPOSITION_STRATEGIES,
    CompositionError,
    composition_css_vars,
    composition_report,
    normalize_composition_strategy,
)
from app.services.poster2.pipeline import load_template
from app.services.poster2.skills.control.family_a_control_surface_v1 import build_control_surface
from app.services.poster2.skills.structure.family_a_structure_surface_v1 import build_structure_surface
from app.services.poster2.template_behavior import resolve_template_behavior
from app.services.poster2.template_registry import (
    get_template_registry,
    is_campaign_explainer_template,
    resolve_template_metadata,
)

_ASSETS = Path(__file__).resolve().parents[2] / "app" / "templates_html"
_PROTECTED_REGIONS = (
    "header_region", "scenario_region", "product_region", "feature_region",
    "bottom_region", "title_band_region", "gallery_strip_region",
)


def _resolve(tid, strategy):
    return resolve_template_behavior(
        load_template(tid), feature_count=3, product_image_size=(640, 900),
        title_text="商用电炸炉 高效之选", subtitle_text="高效稳定 安全耐用",
        brand_name="厨匠", agent_name="顾问",
        gallery_requested_count=4, gallery_input_count_normalized=4, gallery_resolved_count=4,
        composition_strategy=strategy)


def _geometry(tid, strategy):
    return build_structure_surface(load_template(tid), resolved_behavior=_resolve(tid, strategy),
                                   layer_render_status={}, region_render_status={})


# ── strategy model ────────────────────────────────────────────────────────────


def test_strategy_enum_closed():
    assert COMPOSITION_STRATEGIES == ("balanced", "studio", "product_hero", "catalog_clean")


def test_balanced_is_no_op():
    assert composition_css_vars("balanced") == {}
    assert composition_css_vars(None) == {}
    assert composition_css_vars("") == {}


def test_unknown_strategy_raises():
    with pytest.raises(CompositionError):
        normalize_composition_strategy("cinematic")
    with pytest.raises(CompositionError):
        composition_css_vars("cinematic")


@pytest.mark.parametrize("strategy", COMPOSITION_STRATEGIES)
def test_every_strategy_only_emits_whitelisted_non_geometry_vars(strategy):
    css = composition_css_vars(strategy)
    assert set(css).issubset(COMPOSITION_CSS_VAR_WHITELIST)
    for key in COMPOSITION_CSS_VAR_WHITELIST:
        for bad in ("left", "top", "width", "height", "region", "anchor", "band", "shell-"):
            assert bad not in key


def test_product_hero_injects_scenario_and_lift():
    css = composition_css_vars("product_hero")
    assert "blur" in css["--scenario-image-treatment"]
    assert css["--product-primary-shadow"].startswith("drop-shadow(")


def test_report_shape():
    r = composition_report("product_hero")
    assert r["strategy"] == "product_hero"
    assert r["non_geometric"] is True and r["geometry_invariant"] is True
    assert set(r["css_var_keys"]) == set(composition_css_vars("product_hero"))
    assert composition_report("balanced")["css_var_keys"] == []


# ── non-geometric contract ────────────────────────────────────────────────────


def test_composition_is_non_geometric_on_base_template():
    g_bal = _geometry("template_dual_v2", "balanced")
    g_hero = _geometry("template_dual_v2", "product_hero")
    assert g_bal["region_bounds"] == g_hero["region_bounds"]
    assert g_bal["slot_bounds"] == g_hero["slot_bounds"]
    assert g_bal["visible_item_count"] == g_hero["visible_item_count"]


def test_protected_geometry_and_ownership_identical_across_variants():
    base = _geometry("template_dual_v2", "balanced")
    base_own = build_control_surface(_resolve("template_dual_v2", "balanced"))["ownership_guards"]
    for tid, strat in (("template_dual_v2_studio", "studio"),
                       ("template_dual_v2_product_hero", "product_hero")):
        ge = _geometry(tid, strat)
        for r in _PROTECTED_REGIONS:
            assert base["region_bounds"][r] == ge["region_bounds"][r], (tid, r)
        assert base["visible_item_count"] == ge["visible_item_count"], tid
        assert build_control_surface(_resolve(tid, strat))["ownership_guards"] == base_own, tid


def test_product_hero_uses_full_product_geometry_studio_floats():
    base = _geometry("template_dual_v2", "balanced")["slot_bounds"]["product_slot"]
    hero = _geometry("template_dual_v2_product_hero", "product_hero")["slot_bounds"]["product_slot"]
    studio = _geometry("template_dual_v2_studio", "studio")["slot_bounds"]["product_slot"]
    assert hero == base, "product_hero must keep the full (un-floated) product"
    assert studio != base, "studio floats the product"


# ── registry / variant / schema ───────────────────────────────────────────────


def test_product_hero_registered_and_member():
    meta = resolve_template_metadata("template_dual_v2_product_hero")
    assert meta.template_version == load_template("template_dual_v2_product_hero").version
    assert "template_dual_v2_product_hero" in get_template_registry()
    assert is_campaign_explainer_template("template_dual_v2_product_hero") is True


def test_product_hero_css_has_strong_title_non_css_assets_match_base():
    css = (_ASSETS / "template_dual_v2_product_hero.css").read_text(encoding="utf-8")
    assert "font-size: 52px" in css
    for base_name in ("template_dual_v2.html", "template_dual_v2.svg",
                      "slot_spec.template_dual_v2.json", "anchor_map.template_dual_v2.json"):
        hero_name = base_name.replace("template_dual_v2", "template_dual_v2_product_hero")
        assert (_ASSETS / base_name).read_bytes() == (_ASSETS / hero_name).read_bytes(), base_name


def test_request_schema_accepts_optional_composition_strategy():
    base = {"brand_name": "b", "agent_name": "a", "title": "t",
            "product_image": {"url": "https://x/p.png"}}
    assert GeneratePosterV2Request(**base).composition_strategy is None
    assert GeneratePosterV2Request(**base, composition_strategy="product_hero").composition_strategy == "product_hero"


def test_base_and_airy_unaffected_by_composition_default():
    # No composition_strategy -> balanced -> no css var overrides on base/airy.
    for tid in ("template_dual_v2", "template_dual_v2_airy"):
        b = _resolve(tid, None).css_vars
        assert "--scenario-image-treatment" not in b
