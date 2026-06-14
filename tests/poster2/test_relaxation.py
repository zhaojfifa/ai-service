"""
Tests for the poster2 Visual Relaxation Layer.

Covers the closed-enum preset model, the "none = byte-identical baseline"
invariant, the airy variant wiring, and the load-bearing contract guarantee:
a relaxation preset is NON-geometric (region/slot boundaries + ownership are
identical for none vs airy).
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from app.services.poster2.contracts import TemplateSpec
from app.services.poster2.pipeline import load_template
from app.services.poster2.quality_guard import QualityGuardError, assert_relaxation_non_geometric
from app.services.poster2.relaxation import (
    DEFAULT_RELAXATION_PRESET,
    RELAXATION_BASELINE_CSS_VARS,
    RELAXATION_CSS_VAR_WHITELIST,
    RELAXATION_PRESETS,
    RelaxationError,
    normalize_relaxation_preset,
    relaxation_css_vars,
    relaxation_report,
)
from app.services.poster2.skills.control.family_a_control_surface_v1 import build_control_surface
from app.services.poster2.skills.structure.family_a_structure_surface_v1 import (
    build_structure_surface,
)
from app.services.poster2.template_behavior import resolve_template_behavior
from app.services.poster2.template_registry import (
    get_template_registry,
    is_campaign_explainer_template,
    resolve_template_metadata,
)

_REPO = Path(__file__).resolve().parents[2]
_SPECS = _REPO / "app" / "templates" / "specs"
_ASSETS = _REPO / "app" / "templates_html"


def _resolve(spec: TemplateSpec):
    return resolve_template_behavior(
        spec,
        feature_count=3,
        product_image_size=(600, 900),
        title_text="商用电炸炉",
        subtitle_text="高效稳定 安全耐用",
        brand_name="Brand",
        agent_name="Agent",
        gallery_requested_count=4,
        gallery_input_count_normalized=4,
        gallery_resolved_count=4,
    )


def _geometry(spec: TemplateSpec) -> dict:
    behavior = _resolve(spec)
    return build_structure_surface(
        spec,
        resolved_behavior=behavior,
        layer_render_status={},
        region_render_status={},
    )


# ── preset model ──────────────────────────────────────────────────────────────


def test_preset_enum_is_closed_and_expected():
    assert RELAXATION_PRESETS == ("none", "airy", "premium_soft", "dense_safe")
    assert DEFAULT_RELAXATION_PRESET == "none"


def test_none_emits_zero_vars():
    assert relaxation_css_vars("none") == {}


def test_normalize_empty_and_none_default_to_none():
    assert normalize_relaxation_preset(None) == "none"
    assert normalize_relaxation_preset("") == "none"
    assert normalize_relaxation_preset("airy") == "airy"


def test_unknown_preset_raises():
    with pytest.raises(RelaxationError):
        normalize_relaxation_preset("sparkly")
    with pytest.raises(RelaxationError):
        relaxation_css_vars("sparkly")


@pytest.mark.parametrize("preset", RELAXATION_PRESETS)
def test_every_preset_only_emits_whitelisted_non_geometry_vars(preset):
    css_vars = relaxation_css_vars(preset)
    assert set(css_vars).issubset(RELAXATION_CSS_VAR_WHITELIST)
    # Defense in depth: the whitelist must not contain any geometry-bearing key.
    for key in RELAXATION_CSS_VAR_WHITELIST:
        assert "shell-left" not in key and "shell-top" not in key
        assert "shell-width" not in key and "shell-height" not in key
        assert "region" not in key and "anchor" not in key and "band" not in key


def test_airy_values():
    css_vars = relaxation_css_vars("airy")
    assert css_vars["--title-stack-gap"] == "14px"
    assert css_vars["--product-primary-shadow"].startswith("drop-shadow(")
    assert (
        css_vars["--product-primary-shadow"]
        != RELAXATION_BASELINE_CSS_VARS["--product-primary-shadow"]
    )


def test_dense_safe_stays_above_floor():
    css_vars = relaxation_css_vars("dense_safe")
    assert int(css_vars["--title-stack-gap"].replace("px", "")) > 0
    assert "drop-shadow(" in css_vars["--product-primary-shadow"]


def test_relaxation_report_shape():
    report = relaxation_report("airy")
    assert report["preset"] == "airy"
    assert report["non_geometric"] is True
    assert report["geometry_invariant"] is True
    assert report["pillow_compatible"] is False
    assert report["applies_to_engine"] == "puppeteer"
    assert set(report["css_var_keys"]) == set(relaxation_css_vars("airy"))
    assert relaxation_report("none")["css_var_keys"] == []


def test_baseline_constants_match_stylesheet_defaults():
    css = (_ASSETS / "template_dual_v2.css").read_text(encoding="utf-8")
    for key, value in RELAXATION_BASELINE_CSS_VARS.items():
        assert f"{key}: {value};" in css, f"{key} default drifted from stylesheet"


# ── template wiring ───────────────────────────────────────────────────────────


def test_base_template_is_none_airy_template_is_airy():
    base = load_template("template_dual_v2")
    airy = load_template("template_dual_v2_airy")
    assert base.behavior_modes.relaxation_preset == "none"
    assert airy.behavior_modes.relaxation_preset == "airy"
    assert _resolve(base).relaxation_preset == "none"
    assert _resolve(airy).relaxation_preset == "airy"


def test_none_leaves_relaxation_vars_at_stylesheet_default():
    # The baseline (none) does NOT inject --product-primary-shadow (it stays the
    # stylesheet default) and keeps the resolver default title-stack-gap, so the
    # render is byte-identical.
    base_vars = _resolve(load_template("template_dual_v2")).css_vars
    assert "--product-primary-shadow" not in base_vars
    assert base_vars.get("--title-stack-gap") == "8px"


def test_airy_injects_relaxation_overrides():
    airy_vars = _resolve(load_template("template_dual_v2_airy")).css_vars
    assert airy_vars["--title-stack-gap"] == "14px"
    assert airy_vars["--product-primary-shadow"].startswith("drop-shadow(")


# ── the load-bearing contract: relaxation is non-geometric ───────────────────


def test_geometry_evidence_identical_none_vs_airy():
    base_geo = _geometry(load_template("template_dual_v2"))
    airy_geo = _geometry(load_template("template_dual_v2_airy"))
    assert base_geo["region_bounds"] == airy_geo["region_bounds"]
    assert base_geo["slot_bounds"] == airy_geo["slot_bounds"]
    # And the quality-guard differential validator agrees.
    proof = assert_relaxation_non_geometric(base_geo, airy_geo, preset_id="airy")
    assert proof["geometry_invariant"] is True


def test_ownership_identical_none_vs_airy():
    base_ctrl = build_control_surface(_resolve(load_template("template_dual_v2")))
    airy_ctrl = build_control_surface(_resolve(load_template("template_dual_v2_airy")))
    assert base_ctrl["ownership_guards"] == airy_ctrl["ownership_guards"]
    # Product annotation + bottom ownership unchanged.
    assert base_ctrl["ownership_guards"]["product_annotation_owner_region"] == "product_region"
    assert base_ctrl["ownership_guards"]["title_owner_region"] == "title_band_region"


def test_validator_raises_on_synthetic_geometry_drift():
    base = {"region_bounds": {"product_region": {"x": 456, "y": 188, "w": 472, "h": 540}},
            "slot_bounds": {}}
    drifted = {"region_bounds": {"product_region": {"x": 456, "y": 188, "w": 500, "h": 540}},
               "slot_bounds": {}}
    with pytest.raises(QualityGuardError) as exc:
        assert_relaxation_non_geometric(base, drifted, preset_id="airy")
    assert exc.value.reason_code == "relaxation_geometry_drift"


# ── variant reuses the base shell verbatim ───────────────────────────────────


def _spec_dict_without_variant_identity(spec: TemplateSpec) -> dict:
    d = dataclasses.asdict(spec)
    d.pop("template_id", None)
    d.pop("version", None)
    d.get("behavior_modes", {}).pop("relaxation_preset", None)
    return d


def test_airy_spec_geometry_identical_to_base_spec():
    base = _spec_dict_without_variant_identity(load_template("template_dual_v2"))
    airy = _spec_dict_without_variant_identity(load_template("template_dual_v2_airy"))
    assert base == airy, "airy spec must differ ONLY by id/version/relaxation_preset"


@pytest.mark.parametrize(
    "base_name",
    [
        "template_dual_v2.html",
        "template_dual_v2.css",
        "template_dual_v2.svg",
        "slot_spec.template_dual_v2.json",
        "anchor_map.template_dual_v2.json",
    ],
)
def test_airy_render_assets_are_byte_identical_copies(base_name):
    airy_name = base_name.replace("template_dual_v2", "template_dual_v2_airy")
    assert (_ASSETS / base_name).read_bytes() == (_ASSETS / airy_name).read_bytes()


# ── registry ─────────────────────────────────────────────────────────────────


def test_airy_registered_with_matching_version():
    meta = resolve_template_metadata("template_dual_v2_airy")
    spec = load_template("template_dual_v2_airy")
    assert meta.template_version == spec.version
    assert meta.template_family == resolve_template_metadata("template_dual_v2").template_family


def test_campaign_explainer_membership():
    assert is_campaign_explainer_template("template_dual_v2") is True
    assert is_campaign_explainer_template("template_dual_v2_airy") is True
    assert is_campaign_explainer_template("template_product_sheet_v1") is False
    assert is_campaign_explainer_template("nonexistent") is False


def test_registry_contains_airy():
    assert "template_dual_v2_airy" in get_template_registry()
