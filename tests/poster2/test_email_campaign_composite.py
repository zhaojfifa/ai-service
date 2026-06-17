"""Tests for the additive campaign-composite family (email_campaign_composite_v1).

Covers registry registration, the Family A/B/Catalog-Hero no-change guard, the 6 runtime-contract
regions, deterministic business-truth fields, the forbidden unsupported 0–200°C thermostat default, the
no-target-business-leakage gate, operator-gated (non-AI) substrate provenance, and an offline
(Chromium-free) render artifact.
"""
import json
from pathlib import Path

from PIL import Image

from app.services.poster2 import email_campaign_composite as ecc
from app.services.poster2.template_registry import (
    CAMPAIGN_COMPOSITE_PORTRAIT,
    CATALOG_HERO_PORTRAIT,
    FAMILY_A_CAMPAIGN_EXPLAINER,
    FAMILY_B_PRODUCT_SHEET_STORY,
    get_family_registry,
    get_template_registry,
    is_catalog_hero_template,
    is_email_campaign_composite_template,
    resolve_template_metadata,
)

_REPO = Path(__file__).resolve().parents[2]
_SPEC = _REPO / "app/templates/specs/email_campaign_composite_v1.json"


def _product():
    return Image.new("RGB", (400, 500), (200, 203, 208))


def _inputs(**over):
    base = dict(product=_product(), logo=Image.new("RGB", (400, 80), (250, 250, 250)),
                gallery_images=[_product(), _product(), _product()])
    base.update(over)
    return ecc.resolve_inputs(**base)


# ---------------------------------------------------------------------- registration ----
def test_family_and_template_registered():
    families, templates = get_family_registry(), get_template_registry()
    assert CAMPAIGN_COMPOSITE_PORTRAIT in families
    assert "email_campaign_composite_v1" in templates
    meta = resolve_template_metadata("email_campaign_composite_v1")
    assert meta.template_family == CAMPAIGN_COMPOSITE_PORTRAIT
    assert meta.template_version == "1.0.0"
    assert is_email_campaign_composite_template("email_campaign_composite_v1")
    assert not is_email_campaign_composite_template("template_dual_v2")
    assert not is_email_campaign_composite_template("catalog_hero_v1")
    # cross-family isolation
    assert not is_catalog_hero_template("email_campaign_composite_v1")


def test_existing_families_unchanged():
    families = get_family_registry()
    assert FAMILY_A_CAMPAIGN_EXPLAINER in families and FAMILY_B_PRODUCT_SHEET_STORY in families
    assert CATALOG_HERO_PORTRAIT in families
    assert families[FAMILY_A_CAMPAIGN_EXPLAINER].default_preferred_renderer == "puppeteer"
    assert families[FAMILY_B_PRODUCT_SHEET_STORY].default_fallback_renderer == "pillow"
    # the four Family A + Family B + catalog_hero template ids are still present and unchanged
    t = get_template_registry()
    for tid in ("template_dual_v2", "template_product_sheet_v1", "catalog_hero_v1"):
        assert tid in t


def test_spec_version_matches_registry():
    spec = json.loads(_SPEC.read_text(encoding="utf-8"))
    assert spec["template_id"] == "email_campaign_composite_v1"
    assert spec["version"] == resolve_template_metadata("email_campaign_composite_v1").template_version


# ------------------------------------------------------------------------- regions ----
def test_six_runtime_contract_regions_exist():
    expected = ("banner_region", "campaign_visual_region", "truth_overlay_region",
                "restated_band_region", "gallery_region", "footer_region")
    assert ecc.RUNTIME_CONTRACT_REGIONS == expected
    review = ecc.build_contract_review(_inputs(), engine="pillow_fallback", degraded=True)
    assert tuple(review["regions"]) == expected
    spec = json.loads(_SPEC.read_text(encoding="utf-8"))
    for r in expected:
        assert r in spec["_runtime_contract_regions"]


# -------------------------------------------------------------------- business truth ----
def test_business_truth_is_deterministic_cuistance():
    lock = ecc.business_truth_lock(_inputs())
    assert lock["brand"] == "CUISTANCE"
    assert lock["product_ref"] == "EF132V"
    assert lock["product_ref_owner_review"] is True
    f = lock["fields"]
    assert f["title"] == "Les Friteuses Électriques"
    assert "commercial@cuistance.eu" in f["contact"]
    assert "EF132V" in f["spec_row"]
    assert len(f["callouts"]) == 3


def test_no_unsupported_0_200C_default():
    lock = ecc.business_truth_lock(_inputs())
    assert lock["thermostat_uses_unsupported_0_200C"] is False
    assert any("190" in c for c in lock["fields"]["callouts"])
    assert all("0–200" not in c and "0-200" not in c for c in lock["fields"]["callouts"])


def test_unsupported_0_200C_is_detected_if_injected():
    bad = ecc.business_truth_lock(_inputs(callouts=["X", "Thermostat réglable 0–200°C", "Y"]))
    assert bad["thermostat_uses_unsupported_0_200C"] is True
    review = ecc.build_contract_review(_inputs(callouts=["X", "Thermostat réglable 0–200°C", "Y"]),
                                       engine="pillow_fallback", degraded=True)
    assert review["structure_complete"] is False  # gate refuses the unsupported spec


def test_no_target_business_leakage_default_and_detected():
    assert ecc.business_truth_lock(_inputs())["leakage_clean"] is True
    leaked = ecc.business_truth_lock(_inputs(title="Les Réchauds Gaz Technitalia"))
    assert leaked["leakage_clean"] is False
    assert leaked["target_business_leakage_tokens"]


# ------------------------------------------------------------- substrate operator-gated ----
def test_substrate_is_operator_gated_never_ai_truth():
    no_sub = _inputs()
    assert no_sub.substrate_source == "absent"
    with_sub = _inputs(substrate_image=Image.new("RGB", (300, 600), (180, 90, 30)))
    assert with_sub.substrate_source == "operator_upload"
    review = ecc.build_contract_review(with_sub, engine="pillow_fallback", degraded=True)
    assert review["ai_runtime_asset_used"] is False
    assert review["business_truth"]["ai_substrate_is_truth"] is False


def test_callout_ceiling_is_three():
    inp = _inputs(callouts=["a", "b", "c", "d", "e"])
    assert len(inp.callout_labels) == 3
    assert ecc.MAX_CALLOUTS == 3


# ----------------------------------------------------------------- offline render ----
def test_offline_render_produces_artifact():
    """Chromium-free fallback must always produce a full-canvas artifact (deliverable offline)."""
    img = ecc.render_pillow_fallback(_inputs())
    assert isinstance(img, Image.Image)
    assert img.size == (ecc.CANVAS_W, ecc.CANVAS_H)
    # sync render() returns a result with a contract review and a structure-complete case001.
    # Chromium renders at device_scale_factor=2 (2x); the Pillow fallback at 1x — accept either.
    res = ecc.render(_inputs())
    w, h = res.image.size
    assert (w, h) in {(ecc.CANVAS_W, ecc.CANVAS_H), (ecc.CANVAS_W * 2, ecc.CANVAS_H * 2)}
    assert abs(w / h - ecc.CANVAS_W / ecc.CANVAS_H) < 0.01
    assert res.contract_review["structure_complete"] is True
    assert res.contract_review["callout_count"] == 3


def test_missing_product_marks_incomplete():
    review = ecc.build_contract_review(ecc.resolve_inputs(product=None), engine="pillow_fallback", degraded=True)
    assert "product_slot" in review["missing_required_slots"]
    assert review["structure_complete"] is False
