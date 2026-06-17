"""Tests for the additive portrait catalog-hero family (catalog_hero_v1).

Covers registry registration, the Family A/B no-change guard, portrait canvas, frozen
annotation count, owner-gated food hero, the 12-dimension grammar profile, display-only
CTA, the published selector registry entry, and the Chromium-free Pillow fallback.
"""
import json
from pathlib import Path

from PIL import Image

from app.services.poster2 import catalog_hero as ch
from app.services.poster2.contracts import TemplateSpec
from app.services.poster2.template_registry import (
    CATALOG_HERO_PORTRAIT,
    FAMILY_A_CAMPAIGN_EXPLAINER,
    FAMILY_B_PRODUCT_SHEET_STORY,
    get_family_registry,
    get_template_registry,
    is_campaign_explainer_template,
    is_catalog_hero_template,
    resolve_template_metadata,
)

_REPO = Path(__file__).resolve().parents[2]
_SPEC = _REPO / "app/templates/specs/catalog_hero_v1.json"


def _product():
    return Image.new("RGB", (400, 500), (200, 203, 208))


def _inputs(*, with_food=True, features=("a", "b", "c", "d", "e")):
    return ch.CatalogHeroInputs(
        brand_name="BRAND",
        partner_name="PARTNER",
        title="Demo Title Here",
        subtitle="A strapline",
        sku_text="SKU-1",
        features=tuple(features),
        cta_label="Contact",
        cta_email="x@example.test",
        product=_product(),
        food_hero=Image.new("RGB", (300, 600), (200, 120, 40)) if with_food else None,
        food_hero_source="operator_upload" if with_food else "absent",
        gallery=(_product(), _product()),
    )


# --------------------------------------------------------------------- registration ----
def test_catalog_hero_family_registered():
    families = get_family_registry()
    templates = get_template_registry()
    assert CATALOG_HERO_PORTRAIT in families
    assert "catalog_hero_v1" in templates
    meta = resolve_template_metadata("catalog_hero_v1")
    assert meta.template_family == CATALOG_HERO_PORTRAIT
    assert meta.template_version == "1.0.0"
    assert is_catalog_hero_template("catalog_hero_v1")
    assert not is_catalog_hero_template("template_dual_v2")
    assert not is_catalog_hero_template("template_product_sheet_v1")


def test_existing_families_unchanged():
    """Family A/B definitions + template metadata must be byte-identical to the frozen
    expectation — the new family is additive only."""
    families = get_family_registry()
    a = families[FAMILY_A_CAMPAIGN_EXPLAINER]
    b = families[FAMILY_B_PRODUCT_SHEET_STORY]
    assert a.default_preferred_renderer == "puppeteer"
    assert a.default_fallback_renderer == "pillow"
    assert b.default_preferred_renderer == "puppeteer"
    assert b.default_fallback_renderer == "pillow"

    templates = get_template_registry()
    a_meta = templates["template_dual_v2"]
    assert a_meta.template_family == FAMILY_A_CAMPAIGN_EXPLAINER
    assert a_meta.template_version == "2.1.6"
    assert a_meta.minimum_deliverable_regions == ("header_region", "product_region", "title_band_region")
    b_meta = templates["template_product_sheet_v1"]
    assert b_meta.template_family == FAMILY_B_PRODUCT_SHEET_STORY
    assert b_meta.template_version == "1.0.0"
    assert b_meta.minimum_deliverable_regions == ("logo_banner_region", "top_copy_region", "product_hero_region")

    # Family A lineage membership predicate is unchanged (new family is NOT a campaign explainer)
    assert is_campaign_explainer_template("template_dual_v2")
    assert not is_campaign_explainer_template("catalog_hero_v1")


# ------------------------------------------------------------------------- portrait -----
def test_catalog_hero_canvas_is_portrait():
    spec = TemplateSpec.from_json(_SPEC)
    assert spec.canvas_w < spec.canvas_h           # portrait
    assert (spec.canvas_w, spec.canvas_h) == (ch.CANVAS_W, ch.CANVAS_H)
    assert spec.canvas_w / spec.canvas_h < 0.8     # ≈ 0.707 reference proportion


# ------------------------------------------------------------------ frozen annotation ---
def test_catalog_hero_annotation_count_frozen():
    assert ch.CATALOG_HERO_MAX_ANNOTATIONS == 3
    inp = _inputs(features=("a", "b", "c", "d", "e"))
    assert len(inp.annotation_labels) == 3         # clamped
    cr = ch.build_contract_review(inp, food_rendered=True, engine="pillow_fallback", degraded=True)
    ann = cr["annotation_contract"]
    assert ann["max_slots"] == 3
    assert ann["requested_feature_count"] == 5
    assert ann["rendered_annotation_count"] == 3
    assert ann["annotation_clamp_applied"] is True
    assert ann["annotation_slot_ids"] == [
        "product_annotation_slot_1", "product_annotation_slot_2", "product_annotation_slot_3",
    ]


# ----------------------------------------------------------------- owner-gated food -----
def test_food_hero_owner_gated():
    # present -> operator_upload + dual co-anchor
    cr_food = ch.build_contract_review(_inputs(with_food=True), food_rendered=True,
                                       engine="chromium", degraded=False)
    assert cr_food["food_hero_slot"]["rendered"] is True
    assert cr_food["food_hero_slot"]["source"] == "operator_upload"
    assert cr_food["food_hero_slot"]["composition_mode"] == "dual_co_anchor"
    assert cr_food["food_hero_slot"]["owner_gated"] is True

    # absent -> graceful degrade to product_led, never AI
    inp = _inputs(with_food=False)
    cr_none = ch.build_contract_review(inp, food_rendered=False, engine="chromium", degraded=False)
    assert cr_none["food_hero_slot"]["rendered"] is False
    assert cr_none["food_hero_slot"]["source"] == "absent"
    assert cr_none["food_hero_slot"]["composition_mode"] == "product_led"


def test_no_runtime_ai_asset():
    cr = ch.build_contract_review(_inputs(), food_rendered=True, engine="chromium", degraded=False)
    assert cr["ai_runtime_asset_used"] is False
    # resolve_inputs only ever sets operator_upload | absent (never ai_generated)
    assert ch.resolve_inputs(
        brand_name="b", agent_name="", title="t", subtitle="", sku_text="",
        features=[], cta_label="", cta_email="", logo=None, product=_product(),
        scenario_image=None, gallery_images=[],
    ).food_hero_source == "absent"


# ------------------------------------------------------------------- grammar profile ----
def test_grammar_profile_has_12_dimensions():
    gp = ch.build_grammar_profile(_inputs(), food_rendered=True)
    assert gp["profile_id"] == "catalog_hero_v1"
    assert len(gp["dimensions"]) == 12
    assert gp["dimensions"]["1_composition_archetype"] == "editorial_catalog_hero"
    assert gp["dimensions"]["9_evidence_annotation"]["contract_nodes"] == 3
    # focal model reflects the food co-anchor
    assert gp["dimensions"]["2_focal_hierarchy"]["model"] == "dual_co_anchor"
    assert ch.build_grammar_profile(_inputs(with_food=False), food_rendered=False)[
        "dimensions"]["2_focal_hierarchy"]["model"] == "product_led"


# ------------------------------------------------------------------------ CTA / core ----
def test_cta_display_only():
    cr = ch.build_contract_review(_inputs(), food_rendered=True, engine="chromium", degraded=False)
    cta = cr["on_poster_cta_text"]
    assert cta["render_kind"] == "display_text_only"
    assert cta["cta_action_bound"] is False
    assert cta["stage3_send_untouched"] is True


def test_structure_complete_requires_core():
    full = ch.build_contract_review(_inputs(), food_rendered=True, engine="chromium", degraded=False)
    assert full["structure_complete"] is True
    no_product = ch.CatalogHeroInputs(brand_name="B", title="T", product=None)
    cr = ch.build_contract_review(no_product, food_rendered=False, engine="pillow_fallback", degraded=True)
    assert cr["structure_complete"] is False
    assert "product_image_slot" in cr["missing_required_slots"]


# ------------------------------------------------------------------------- selector -----
def test_selector_registry_includes_catalog_hero():
    for rel in ("frontend/templates/registry.json", "docs/templates/registry.json"):
        data = json.loads((_REPO / rel).read_text(encoding="utf-8"))
        ids = [e["id"] for e in data]
        assert "catalog_hero_v1" in ids, f"{rel} missing catalog_hero_v1"


# ------------------------------------------------------------------ pillow fallback -----
def test_pillow_fallback_renders_portrait():
    img = ch.render_pillow_fallback(_inputs(with_food=True), food_rendered=True)
    assert img.size == (ch.CANVAS_W, ch.CANVAS_H)
    assert img.width < img.height
    # non-trivial: not a blank canvas
    assert img.getextrema() != ((255, 255), (255, 255), (255, 255))
