from __future__ import annotations

from pathlib import Path

from app.services.poster2.contracts import AssetRef, PosterSpec, StyleSpec, TemplateSpec
from app.services.poster2.family_a_runtime import (
    build_family_a_control_surface,
    build_family_a_structure_surface,
    filter_family_a_visible_truth_evidence,
)
from app.services.poster2.skills.control.family_a_control_surface_v1 import build_control_surface
from app.services.poster2.skills.beautification.family_a_beautification_freeze_pack_v1 import (
    build_beautification_freeze_pack,
)
from app.services.poster2.skills.evidence.family_a_evidence_surface_v1 import build_evidence_surface
from app.services.poster2.skills.registry import load_skill_implementation
from app.services.poster2.skills.structure.family_a_structure_surface_v1 import build_structure_surface
from app.services.poster2.template_behavior import resolve_template_behavior


ROOT = Path(__file__).resolve().parents[3]


def _load_template() -> TemplateSpec:
    return TemplateSpec.from_json(
        ROOT / "app" / "templates" / "specs" / "template_dual_v2.json"
    )


def _make_spec(**overrides) -> PosterSpec:
    defaults = dict(
        brand_name="ChefCraft",
        agent_name="Starlight",
        title="Family A skill extraction",
        subtitle="Support copy stays visible",
        features=("Feature A", "Feature B", "Feature C"),
        product_image=AssetRef(url="mock://product"),
        product_secondary_image=AssetRef(url="mock://secondary"),
        scenario_image=AssetRef(url="mock://scenario"),
        gallery_images=(
            AssetRef(url="mock://gallery-1"),
            AssetRef(url="mock://gallery-2"),
            AssetRef(url="mock://gallery-3"),
        ),
        style=StyleSpec(seed=42),
    )
    defaults.update(overrides)
    return PosterSpec(**defaults)


def _resolve_behavior(template: TemplateSpec, spec: PosterSpec):
    return resolve_template_behavior(
        template,
        feature_count=len(spec.features),
        title_text=spec.title,
        subtitle_text=spec.subtitle,
        brand_name=spec.brand_name,
        gallery_requested_count=len(spec.gallery_images),
        gallery_input_count_normalized=len(spec.gallery_images),
        gallery_resolved_count=len(spec.gallery_images),
        bottom_mode=spec.bottom_mode,
        gallery_mode=spec.gallery_mode,
        agent_name=spec.agent_name,
        has_product_secondary_asset=spec.product_secondary_image is not None,
    )


def test_family_a_structure_skill_matches_oracle_runtime_surface():
    template = _load_template()
    spec = _make_spec()
    resolved_behavior = _resolve_behavior(template, spec)
    layer_render_status = {"bottom_gallery_items_layer": {"count_visible": 3}}
    region_render_status = {
        "header_region": {"count": 3},
        "scenario_region": {"count": 1},
        "product_region": {"count": 2},
        "feature_region": {"count": 3},
        "title_band_region": {"count": 2},
        "bottom_region": {"count": 5},
    }

    expected = build_family_a_structure_surface(
        template,
        resolved_behavior=resolved_behavior,
        layer_render_status=layer_render_status,
        region_render_status=region_render_status,
    )
    implementation = load_skill_implementation("family_a_structure_surface_v1")

    actual = implementation(
        template,
        resolved_behavior=resolved_behavior,
        layer_render_status=layer_render_status,
        region_render_status=region_render_status,
    )

    assert actual == expected
    assert actual == build_structure_surface(
        template,
        resolved_behavior=resolved_behavior,
        layer_render_status=layer_render_status,
        region_render_status=region_render_status,
    )


def test_family_a_control_skill_matches_oracle_runtime_surface():
    template = _load_template()
    spec = _make_spec(product_secondary_image=None)
    resolved_behavior = _resolve_behavior(template, spec)

    implementation = load_skill_implementation("family_a_control_surface_v1")

    assert implementation(resolved_behavior) == build_family_a_control_surface(resolved_behavior)
    assert build_control_surface(resolved_behavior)["mode_surface"] == {
        "header_mode": "identity_left_agent_right",
        "hero_mode": "scenario_cover_product_contain",
        "feature_mode": "product_anchor_callouts",
        "product_annotation_mode": "product_anchor_callouts",
        "bottom_mode": "title_gallery_split",
        "gallery_mode": "strip_local_visible_only",
        "product_layout_mode": "single_primary",
        "secondary_product_mode": "inset_hidden_no_reserve",
    }


def test_family_a_evidence_skill_filters_visible_truth_and_carries_family_a_guards():
    visible_truth_evidence = {
        "header_region": {"rendered": True},
        "product_region": {"rendered": True},
        "logo_banner_region": {"rendered": True},
        "description_region": {"rendered": True},
    }

    implementation = load_skill_implementation("family_a_evidence_surface_v1")
    actual = implementation(visible_truth_evidence)

    assert actual["filtered_visible_truth_evidence"] == filter_family_a_visible_truth_evidence(visible_truth_evidence)
    assert sorted(actual["filtered_visible_truth_evidence"].keys()) == ["header_region", "product_region"]
    assert "logo_banner_region" in actual["forbidden_cross_family_keys"]
    assert actual["canonical_sample_variants"][0]["sample_id"] == "annotation_triplet_gallery_triplet_subtitle_present"


def test_family_a_beautification_skill_matches_frozen_pack_and_resolver_consumption():
    implementation = load_skill_implementation("family_a_beautification_freeze_pack_v1")
    pack = implementation(
        shell_surface="campaign_frozen_panel",
        shell_border="clean_frame",
        shell_shadow="medium",
        accent_tone="warm_red",
        text_emphasis="campaign_frozen",
    )

    assert pack == build_beautification_freeze_pack(
        shell_surface="campaign_frozen_panel",
        shell_border="clean_frame",
        shell_shadow="medium",
        accent_tone="warm_red",
        text_emphasis="campaign_frozen",
    )
    assert pack["beauty_tokens"].shell_surface == "campaign_frozen_panel"
    assert pack["accent_color"] == "#C63A2D"
    assert pack["text_colors"]["subtitle"] == "#5A6168"
    assert pack["css_vars"]["--annotation-card-surface"].startswith("linear-gradient")
    assert pack["css_vars"]["--gallery-item-border"] == "1px solid rgba(214, 218, 221, 0.86)"

    template = _load_template()
    spec = _make_spec(product_secondary_image=None)
    resolved_behavior = _resolve_behavior(template, spec)

    assert resolved_behavior.beauty_tokens == pack["beauty_tokens"]
    assert resolved_behavior.accent_color == pack["accent_color"]
    assert resolved_behavior.css_vars["--annotation-card-surface"] == pack["css_vars"]["--annotation-card-surface"]
    assert resolved_behavior.css_vars["--title-band-top-rule"] == pack["css_vars"]["--title-band-top-rule"]
