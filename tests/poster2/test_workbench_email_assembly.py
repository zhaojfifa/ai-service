"""PR-3 — Email Banner Module + Email Assembly preview.

Assembles the email preview at the email level (banner + deterministically-selected body visual) by reusing the
existing draft path. Reuses the PR-2 candidate fakes (no real render).
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.workbench_records import load_workbench_record, save_workbench_record
from tests.poster2.test_workbench_candidates import _boom, _fake_affiche, _gen, _make_workbench
from tests.poster2.test_api import _FakePoster2Pipeline


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.workbench_records.WORKBENCH_RECORD_DIR", tmp_path / "wb")
    monkeypatch.setattr("app.services.workbench_records.put_bytes", lambda *a, **k: None)
    monkeypatch.setattr("app.services.workbench_records.get_bytes", _boom)
    monkeypatch.setattr("app.services.poster_records.POSTER_RECORD_DIR", tmp_path / "pr")
    monkeypatch.setattr("app.services.poster_records.put_bytes", lambda *a, **k: None)
    monkeypatch.setattr("app.services.poster_records.get_bytes", _boom)
    monkeypatch.setattr("app.main._generate_email_campaign_composite_v1", _fake_affiche())
    monkeypatch.setattr("app.main._get_poster2_pipeline", lambda: _FakePoster2Pipeline())
    for var in (
        "EMAIL_COPY_OPTIMIZER", "GEMINI_API_KEY", "GOOGLE_API_KEY",
        "EMAIL_ATTACHMENT_ENABLED", "EMAIL_ATTACHMENT_BUILD_ON_PREVIEW", "EMAIL_ATTACHMENT_DEFAULT_TYPES",
    ):
        monkeypatch.delenv(var, raising=False)
    from app.config import get_settings

    get_settings.cache_clear()
    return TestClient(app)


def _select(client, wb, candidate_type):
    return client.patch(f"/api/v2/workbench/{wb}/selected-visual", json={"selected_email_body_visual": candidate_type})


def _set_banner_meta(client, wb):
    client.patch(
        f"/api/v2/workbench/{wb}",
        json={"email_banner": {
            "logo": {"url": "https://r2.example/logo.png", "key": "logo/logo.png"},
            "channel_name": "CUISTANCE Europe",
            "campaign_label": "Nouveauté",
            "selected_banner_ref": "banner_option_01",
        }},
    )


# 1
def test_preview_selected_affiche_uses_affiche_poster_key(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    _select(client, wb, "affiche")
    affiche_pk = client.get(f"/api/v2/workbench/{wb}").json()["poster_candidates"]["affiche"]["poster_key"]
    r = client.post(f"/api/v2/workbench/{wb}/email/preview")
    assert r.status_code == 200
    body = r.json()
    assert body["selected_email_body_visual"] == "affiche"
    assert body["body_visual"]["candidate_type"] == "affiche"
    assert body["body_visual"]["poster_key"] == affiche_pk


# 2
def test_preview_selected_fiche_uses_fiche_poster_key(client):
    # fiche = product_sheet_email built from workbench truth (no poster generation / no poster_key)
    wb = _make_workbench(client)
    _gen(client, wb, "fiche")
    _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["selected_email_body_visual"] == "fiche"
    assert body["email_fill_format"] == "product_sheet_email"
    assert body["fiche_uses_poster_generation"] is False
    assert body["fiche_generated_from"] == "workbench_truth"
    assert body["product_sheet_email_contract_pass"] is True
    # body visual is the product image (NOT a generated poster), and there is no poster_key
    assert body["body_visual"]["candidate_type"] == "fiche"
    assert body["body_visual"]["poster_key"] in (None, "")
    assert body["body_visual"]["url"] == "https://r2.example/p1.png"


# 3
def test_preview_fails_when_no_selection(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")  # generated but NOT selected
    r = client.post(f"/api/v2/workbench/{wb}/email/preview")
    assert r.status_code == 422
    assert r.json()["detail"] == "no_selected_email_body_visual"


# 4
def test_preview_fails_when_selected_candidate_has_no_poster_key(client):
    wb = _make_workbench(client)
    # craft a corrupt state: selection points to a candidate with no poster_key (bypasses the select guard)
    rec = load_workbench_record(wb)
    rec["selected_email_body_visual"] = "fiche"
    save_workbench_record(rec)
    r = client.post(f"/api/v2/workbench/{wb}/email/preview")
    assert r.status_code == 422
    assert r.json()["detail"] == "selected_candidate_not_ready"


# 5
def test_preview_includes_email_banner_module(client):
    wb = _make_workbench(client)
    _set_banner_meta(client, wb)
    _gen(client, wb, "affiche")
    _select(client, wb, "affiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["banner"]["logo_url"] == "https://r2.example/logo.png"  # banner metadata still carries the logo
    assert body["banner"]["channel_name"] == "CUISTANCE Europe"
    assert body["banner"]["campaign_label"] == "Nouveauté"
    assert body["banner"]["selected_banner_ref"] == "banner_option_01"
    # ttt header: dark bar + red filet + channel meta. When a logo exists, the DEFAULT now prefers the logo banner.
    assert "1f2329" in body["html"]            # dark bar
    assert "CUISTANCE" in body["html"]         # brand (logo alt or wordmark)
    assert "CUISTANCE Europe" in body["html"]  # channel/campaign meta
    assert body["header_variant"] == "ttt_logo_banner"          # logo present -> logo banner by default
    assert body["header_logo_used"] is True
    assert "https://r2.example/logo.png" in body["html"]        # the logo IS the header brand element now
    assert "background-image" not in body["html"].split("selected_body_visual")[0]  # no header-band cover


# 6
def test_preview_includes_selected_final_poster_url(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    _select(client, wb, "affiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["body_visual"]["url"] == "https://example.com/affiche.png"
    assert "https://example.com/affiche.png" in body["html"]


# 7
def test_switching_selected_visual_changes_preview_body(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    _gen(client, wb, "fiche")
    _select(client, wb, "affiche")
    a = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert a["body_visual"]["candidate_type"] == "affiche"
    assert a["body_visual"]["url"] == "https://example.com/affiche.png"
    _select(client, wb, "fiche")
    f = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert f["body_visual"]["candidate_type"] == "fiche"
    assert f["body_visual"]["url"] == "https://r2.example/p1.png"  # fiche embeds the product image (no poster)


# 8
def test_gemini_cannot_alter_technical_parameters(client, monkeypatch):
    wb = _make_workbench(client, with_thermostat=True)
    _gen(client, wb, "affiche")
    _select(client, wb, "affiche")

    captured = {}

    def _fake_optimize(self, canonical_input):
        captured["input"] = canonical_input
        return {
            "subject": "CUISTANCE | Friteuse",
            "preview_text": "Deux cuves inox amovibles",
            "html": "<p>Deux cuves inox amovibles</p>",
            "text": "Deux cuves inox amovibles",
            "summary_points": ["Deux cuves inox amovibles"],
            "tone": "marketing_clean",
            "generated_at": "2026-06-18T00:00:00+00:00",
        }

    monkeypatch.setenv("EMAIL_COPY_OPTIMIZER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.email.gemini_optimizer.GeminiEmailCopyOptimizer.optimize", _fake_optimize
    )
    from app.config import get_settings

    get_settings.cache_clear()

    r = client.post(f"/api/v2/workbench/{wb}/email/preview")
    assert r.status_code == 200
    # the canonical input handed to Gemini NEVER contains technical parameters
    assert "parameters" not in captured["input"]
    assert "190" not in json.dumps(captured["input"], ensure_ascii=False)
    # the workbench technical parameters are unchanged after preview
    params = client.get(f"/api/v2/workbench/{wb}").json()["product_truth"]["parameters"]
    assert params[0]["key"] == "thermostat"
    assert params[0]["value"] == "jusqu'à 190°C"


# 9
def test_190c_remains_ordinary_param_and_no_thermostat_previews(client):
    # thermostat 190°C product previews fine and keeps the value...
    wb = _make_workbench(client, with_thermostat=True)
    _gen(client, wb, "fiche")
    _select(client, wb, "fiche")
    assert client.post(f"/api/v2/workbench/{wb}/email/preview").status_code == 200
    # ...and a product with NO thermostat row previews equally (190°C is not a platform rule)
    wb2 = _make_workbench(client, with_thermostat=False)
    _gen(client, wb2, "fiche")
    _select(client, wb2, "fiche")
    assert client.post(f"/api/v2/workbench/{wb2}/email/preview").status_code == 200


def test_preview_reports_transitional_body_banner_flag(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    _select(client, wb, "affiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    # affiche body visual still carries its own composite banner today (documented transitional state)
    assert body["body_visual_contains_own_banner"] is True


def test_preview_unknown_workbench_404(client):
    r = client.post("/api/v2/workbench/wb_missing/email/preview")
    assert r.status_code == 404


def test_preview_intro_derives_from_description(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    _select(client, wb, "affiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["intro"] == "Deux cuves inox amovibles, construction robuste."
    assert body["cta_label"] == "Nous contacter"


# --- FICHE SELECTION / PREVIEW TRUTH (selection PATCH -> GET-confirm -> product_sheet_email preview) ---

def test_fiche_select_patch_is_get_confirmed(client):
    # generate affiche, select it (selected=affiche), then generate+select fiche -> backend GET confirms fiche wins
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    _select(client, wb, "affiche")
    assert client.get(f"/api/v2/workbench/{wb}").json()["selected_email_body_visual"] == "affiche"
    _gen(client, wb, "fiche")
    r = _select(client, wb, "fiche")
    assert r.status_code == 200
    assert client.get(f"/api/v2/workbench/{wb}").json()["selected_email_body_visual"] == "fiche"  # truth flipped


def test_preview_after_fiche_select_uses_fiche_not_affiche(client):
    # with fiche selected (after affiche was previously selected) the preview is product_sheet_email built from fiche
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    _select(client, wb, "affiche")
    _gen(client, wb, "fiche")
    _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["selected_email_body_visual"] == "fiche"
    assert body["email_fill_format"] == "product_sheet_email"
    assert body["body_visual"]["candidate_type"] == "fiche"           # preview uses fiche...
    assert body["body_visual"]["url"] == "https://r2.example/p1.png"  # ...the product image, NOT the affiche poster
    assert body["body_visual"]["url"] != "https://example.com/affiche.png"
    assert body["fiche_uses_poster_generation"] is False
    assert body["product_sheet_email_contract_pass"] is True


def test_preview_rejects_fill_format_mismatch(client):
    # selected body = affiche, but client asserts product_sheet_email -> 422 (never silently preview affiche as sheet)
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    _select(client, wb, "affiche")
    r = client.post(f"/api/v2/workbench/{wb}/email/preview", json={"email_fill_format": "product_sheet_email"})
    assert r.status_code == 422
    assert r.json()["detail"] == "email_fill_format_mismatch"


def test_preview_accepts_matching_fill_format_assertion(client):
    # selected body = fiche AND client asserts product_sheet_email -> matches -> 200
    wb = _make_workbench(client)
    _gen(client, wb, "fiche")
    _select(client, wb, "fiche")
    r = client.post(f"/api/v2/workbench/{wb}/email/preview", json={"email_fill_format": "product_sheet_email"})
    assert r.status_code == 200
    assert r.json()["email_fill_format"] == "product_sheet_email"
    # affiche selected + matching campaign_poster_email assertion also passes
    wb2 = _make_workbench(client)
    _gen(client, wb2, "affiche")
    _select(client, wb2, "affiche")
    r2 = client.post(f"/api/v2/workbench/{wb2}/email/preview", json={"email_fill_format": "campaign_poster_email"})
    assert r2.status_code == 200
    assert r2.json()["email_fill_format"] == "campaign_poster_email"


# ---- POSTER2-EMAIL-CONTAINER-TRIAL-CLOSURE-V1: container flexibility + fillability diagnostics ----
def test_preview_exposes_container_profile_and_modes_affiche(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    _select(client, wb, "affiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["container_profile"] == "single_product_campaign_email"
    # header_variant now reports the brand-element variant; the header source stays ttt_html_header
    assert body["header_variant"] == "ttt_logo_banner"
    assert body["email_header_source"] == "ttt_html_header"
    assert body["spec_display_mode"] == "in_visual"           # affiche specs baked into the visual
    assert body["body_visual_mode"]                            # variant present
    assert body["preview_ready"] is True
    assert body["missing_required_fields"] == []
    assert body["filled_subject"] is True and body["filled_cta"] is True
    assert body["send_hold"] is True and body["real_email_sent"] is False


def test_preview_exposes_container_profile_fiche(client):
    wb = _make_workbench(client)   # has a confirmed parameter -> spec list populated
    _gen(client, wb, "fiche")
    _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["container_profile"] == "single_product_sheet_email"
    assert body["spec_display_mode"] == "spec_list"           # confirmed parameters -> populated spec list
    assert body["body_visual_mode"] == "product_image"
    assert body["preview_ready"] is True
    assert body["missing_required_fields"] == []
    assert body["send_hold"] is True and body["real_email_sent"] is False


def test_preview_fiche_missing_product_image_surfaces_not_blocks(client):
    # exposes a clear missing status (NO silent wrong fallback) but still returns 200 (preview, not send)
    wb = _make_workbench(client)
    _gen(client, wb, "fiche")
    _select(client, wb, "fiche")
    rec = load_workbench_record(wb)
    rec["product_assets"]["product_images"] = []     # remove the product image after the candidate was ready
    rec["product_truth"]["product_name"] = ""        # and clear identity
    rec["product_truth"]["reference"] = ""
    save_workbench_record(rec)
    r = client.post(f"/api/v2/workbench/{wb}/email/preview")
    assert r.status_code == 200                       # surfaced, not hard-blocked
    body = r.json()
    assert body["preview_ready"] is False
    assert "product_image" in body["missing_required_fields"]
    assert "product_identity" in body["missing_required_fields"]


def test_preview_fiche_empty_spec_marks_spec_list_empty(client):
    # a fiche whose only confirmed param is removed -> spec_display_mode flags the empty list (advisory)
    wb = _make_workbench(client)
    _gen(client, wb, "fiche")
    _select(client, wb, "fiche")
    rec = load_workbench_record(wb)
    rec["product_truth"]["parameters"] = []
    save_workbench_record(rec)
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["spec_display_mode"] == "spec_list_empty"
    assert body["preview_ready"] is True              # identity + image still present -> still previewable


def test_preview_rejects_container_profile_mismatch(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    _select(client, wb, "affiche")
    bad = client.post(f"/api/v2/workbench/{wb}/email/preview",
                      json={"container_profile": "single_product_sheet_email"})
    assert bad.status_code == 422
    assert bad.json()["detail"] == "container_profile_mismatch"
    ok = client.post(f"/api/v2/workbench/{wb}/email/preview",
                     json={"container_profile": "single_product_campaign_email"})
    assert ok.status_code == 200
    assert ok.json()["container_profile"] == "single_product_campaign_email"


# ---- POSTER2-EMAIL-CONTAINER-STRUCTURE-FIRST-FILLABILITY-FIX-V1: supporting_media_strip ----
def _wb_with_media(client):
    """Workbench with 2 product images (views of ONE product) + 3 gallery images + 1 atmosphere."""
    wb = _make_workbench(client)  # 2 product images + 1 confirmed param
    client.patch(
        f"/api/v2/workbench/{wb}",
        json={"product_assets": {
            "product_images": [{"url": "https://r2.example/p1.png"}, {"url": "https://r2.example/p2.png"}],
            "gallery_images": [{"url": "https://r2.example/g1.png"}, {"url": "https://r2.example/g2.png"},
                               {"url": "https://r2.example/g3.png"}],
            "atmosphere": {"url": "https://r2.example/atmo.png", "is_truth": False},
        }},
    )
    return wb


def test_fiche_container_includes_supporting_media_strip_module(client):
    wb = _wb_with_media(client)
    _gen(client, wb, "fiche")
    _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    keys = [m["key"] for m in body["container_modules"]]
    assert "supporting_media_strip" in keys
    strip = next(m for m in body["container_modules"] if m["key"] == "supporting_media_strip")
    assert strip["present"] is True
    # ordered after the primary visual, before product_description
    assert keys.index("selected_body_visual") < keys.index("supporting_media_strip") < keys.index("product_description")


def test_fiche_two_product_images_three_gallery_renders_three_supporting(client):
    wb = _wb_with_media(client)
    _gen(client, wb, "fiche")
    _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["supporting_media_strip_present"] is True
    assert body["supporting_media_count"] == 3                 # capped at 3 (p2 + g1 + g2)
    assert body["product_image_count"] == 2
    assert body["gallery_image_count"] == 3
    # primary visual stays product_images[0]; the strip never replaces it
    assert body["primary_product_visual_present"] is True
    assert body["body_visual"]["url"] == "https://r2.example/p1.png"
    # rendered strip: p2 + g1 + g2 present, g3 dropped by the max-3 cap
    assert "Vues produit" in body["html"]
    assert "p2.png" in body["html"] and "g1.png" in body["html"] and "g2.png" in body["html"]
    assert "g3.png" not in body["html"]


def test_fiche_supporting_media_roles_views_then_gallery(client):
    wb = _wb_with_media(client)
    _gen(client, wb, "fiche")
    _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    # product_images[1..] are SAME-product views (priority), gallery images are supporting visuals
    assert body["supporting_media_sources"] == ["same_product_view", "supporting_visual", "supporting_visual"]


def test_fiche_atmosphere_present_but_not_used(client):
    wb = _wb_with_media(client)
    _gen(client, wb, "fiche")
    _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["atmosphere_present"] is True
    assert body["atmosphere_used_in_fiche"] is False
    assert "atmo.png" not in body["html"]            # atmosphere never enters the Fiche body


def test_fiche_no_supporting_media_only_primary(client):
    wb = _make_workbench(client, two_images=False)   # single product image, default 1 gallery
    client.patch(f"/api/v2/workbench/{wb}", json={"product_assets": {
        "product_images": [{"url": "https://r2.example/p1.png"}], "gallery_images": []}})
    _gen(client, wb, "fiche")
    _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["supporting_media_strip_present"] is False
    assert body["supporting_media_count"] == 0
    assert "Vues produit" not in body["html"]


def test_affiche_has_no_supporting_media_strip(client):
    wb = _wb_with_media(client)
    _gen(client, wb, "affiche")
    _select(client, wb, "affiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["supporting_media_strip_present"] is False
    assert body["supporting_media_count"] == 0
    keys = [m["key"] for m in body["container_modules"]]
    assert "supporting_media_strip" in keys           # structural module exists...
    strip = next(m for m in body["container_modules"] if m["key"] == "supporting_media_strip")
    assert strip["present"] is False                  # ...but is not rendered for affiche
    assert "Vues produit" not in body["html"]
    assert body["real_email_sent"] is False


def test_selected_email_body_visual_persists(client):
    # Fiche selection persists as workbench truth across preview
    wb = _wb_with_media(client)
    _gen(client, wb, "fiche")
    _select(client, wb, "fiche")
    client.post(f"/api/v2/workbench/{wb}/email/preview")
    assert client.get(f"/api/v2/workbench/{wb}").json()["selected_email_body_visual"] == "fiche"
    # Affiche selection persists too
    wb2 = _make_workbench(client)
    _gen(client, wb2, "affiche")
    _select(client, wb2, "affiche")
    client.post(f"/api/v2/workbench/{wb2}/email/preview")
    assert client.get(f"/api/v2/workbench/{wb2}").json()["selected_email_body_visual"] == "affiche"


# ---- POSTER2-CUISTANCE-TRIAL-SEND-MAINLINE-ALIGN-AND-BANNER-FLEX-V1: replaceable header ----
def _patch_banner(client, wb, **fields):
    client.patch(f"/api/v2/workbench/{wb}", json={"email_banner": fields})


def test_header_default_prefers_logo_banner_when_logo_exists(client):
    # POLISH: when a valid email_banner.logo exists, the DEFAULT header is the ttt logo banner (not text wordmark)
    wb = _make_workbench(client)
    _set_banner_meta(client, wb)   # sets logo + channel + campaign, NO header_variant
    _gen(client, wb, "fiche"); _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["header_variant"] == "ttt_logo_banner"
    assert body["banner_source"] == "uploaded_logo"
    assert body["header_logo_used"] is True
    assert body["header_logo_missing_fallback"] is False
    assert body["email_header_source"] == "ttt_html_header"
    header_region = body["html"].split("E1002A")[0]   # up to the red filet (end of header bar)
    assert "https://r2.example/logo.png" in header_region   # the logo IS the header brand element


def test_header_no_logo_falls_back_to_wordmark(client):
    # POLISH: with NO logo, the default header falls back to the text wordmark and flags the fallback
    wb = _make_workbench(client)
    client.patch(f"/api/v2/workbench/{wb}", json={"email_banner": {"channel_name": "CUISTANCE Europe"}})  # no logo
    _gen(client, wb, "fiche"); _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["header_variant"] == "css_dark_bar_wordmark"
    assert body["banner_source"] == "wordmark_fallback"
    assert body["header_logo_used"] is False
    assert body["header_logo_missing_fallback"] is True
    header_region = body["html"].split("E1002A")[0]
    assert "CUISTANCE" in header_region            # css wordmark text
    assert "https://r2.example/logo.png" not in header_region


def test_header_logo_image_bar_uses_email_banner_logo(client):
    wb = _make_workbench(client)
    _patch_banner(client, wb, logo={"url": "https://r2.example/brandlogo.png"},
                  channel_name="CUISTANCE Europe", campaign_label="Nouveauté", header_variant="logo_image_bar")
    _gen(client, wb, "fiche"); _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["header_variant"] == "logo_image_bar"
    assert body["header_logo_used"] is True
    assert body["header_logo_url"] == "https://r2.example/brandlogo.png"
    assert body["header_logo_missing_fallback"] is False
    header_region = body["html"].split("E1002A")[0]
    assert "https://r2.example/brandlogo.png" in header_region   # logo image is the header brand element


def test_header_logo_image_bar_falls_back_when_no_logo(client):
    wb = _make_workbench(client)
    _patch_banner(client, wb, channel_name="CUISTANCE Europe", header_variant="logo_image_bar")  # NO logo asset
    _gen(client, wb, "fiche"); _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["header_variant"] == "css_dark_bar_wordmark"     # fell back to wordmark
    assert body["header_logo_used"] is False
    assert body["header_logo_missing_fallback"] is True


def test_header_never_uses_product_gallery_atmosphere_as_logo(client):
    wb = _wb_with_media(client)   # 2 product images + 3 gallery + atmosphere
    _patch_banner(client, wb, logo={"url": "https://r2.example/brandlogo.png"},
                  channel_name="C", header_variant="logo_image_bar")
    _gen(client, wb, "fiche"); _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["header_logo_url"] == "https://r2.example/brandlogo.png"
    header_region = body["html"].split("E1002A")[0]   # header bar only
    assert "brandlogo.png" in header_region
    for forbidden in ["p1.png", "p2.png", "g1.png", "g2.png", "g3.png", "atmo.png"]:
        assert forbidden not in header_region
    # Fiche container regression still intact alongside the logo header
    assert body["supporting_media_strip_present"] is True
    assert body["supporting_media_count"] == 3
    assert body["atmosphere_used_in_fiche"] is False


# ---- POSTER2-CUISTANCE-DEEP-CONTAINER-MIGRATION-V1: ttt / ttt2 containers ----
def test_fiche_default_container_is_ttt_product_sheet(client):
    wb = _make_workbench(client)
    _gen(client, wb, "fiche"); _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["container_visual_variant"] == "ttt_product_sheet_container"
    assert body["banner_replaceable"] is True
    assert body["banner_source"] == "uploaded_logo"
    # ttt grammar markers: dark header, red filet, serif headline, rounded red CTA, dark footer
    html = body["html"]
    assert "#1f2329" in html and "background:#E1002A" in html
    assert "Georgia" in html and "df3004" in html
    assert "CONTACT" in html and "cuistance-europe.com" in html


def test_affiche_default_container_is_ttt2_campaign(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche"); _select(client, wb, "affiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["container_visual_variant"] == "ttt2_campaign_container"
    # affiche container does NOT render the structured fiche spec block (the poster carries the specs)
    assert body["spec_display_mode"] == "in_visual"
    assert "Tarif = Nous contacter" not in body["html"]          # fiche-only spec block marker
    assert body["supporting_media_strip_present"] is False
    # the email header is separate from the body visual (no double header): header bar precedes the body image
    html = body["html"]
    assert html.index("#1f2329") < html.index("background:#E1002A")  # dark header + filet come first


def test_container_banner_source_diagnostics(client):
    wb = _make_workbench(client)
    _patch_banner(client, wb, logo={"url": "https://r2.example/brandlogo.png"}, header_variant="logo_image_bar")
    _gen(client, wb, "fiche"); _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["banner_source"] == "uploaded_logo"
    assert body["banner_replaceable"] is True
    assert body["header_logo_used"] is True


def test_fiche_product_replacement_fills_ttt_container(client):
    wb = _make_workbench(client)
    # replace the product truth + image -> the container must reflect the NEW product, no stale facts
    client.patch(f"/api/v2/workbench/{wb}", json={"product_truth": {
        "product_name": "Trancheuse à jambon", "reference": "TJ250",
        "description": "Lame inox 250 mm, affûtage intégré.",
        "parameters": [{"key": "power", "label": "Puissance", "value": "180 W", "state": "confirmed"}]}})
    client.patch(f"/api/v2/workbench/{wb}", json={"product_assets": {
        "product_images": [{"url": "https://r2.example/tj250.png"}]}})
    _gen(client, wb, "fiche"); _select(client, wb, "fiche")
    html = client.post(f"/api/v2/workbench/{wb}/email/preview").json()["html"]
    assert "Trancheuse à jambon" in html and "TJ250" in html
    assert "Lame inox 250 mm" in html and "180 W" in html
    assert "https://r2.example/tj250.png" in html
    assert "Friteuse" not in html and "EF132V" not in html      # the previous product does NOT leak


def test_container_has_no_mailchimp_tracking_or_stale_facts(client):
    wb = _wb_with_media(client)
    for ct in ("fiche", "affiche"):
        _gen(client, wb, ct); _select(client, wb, ct)
        html = client.post(f"/api/v2/workbench/{wb}/email/preview").json()["html"].lower()
        for forbidden in ("list-manage", "mcusercontent", "campaign-image", "mailchimp", "/track",
                          "coupe-frites", "1210025", "les réchauds gaz"):
            assert forbidden not in html


# ---- POSTER2-CUISTANCE-BANNER-HEADER-POLISH-V1 ----
def test_ttt_logo_banner_renders_logo_and_filet(client):
    wb = _make_workbench(client)
    _patch_banner(client, wb, logo={"url": "https://r2.example/brandlogo.png"},
                  channel_name="CUISTANCE Europe", header_variant="ttt_logo_banner")
    _gen(client, wb, "fiche"); _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["header_variant"] == "ttt_logo_banner"
    assert body["banner_source"] == "uploaded_logo"
    assert body["header_logo_used"] is True
    header_region = body["html"].split("E1002A")[0]
    assert "https://r2.example/brandlogo.png" in header_region   # logo image in the banner
    assert "background:#E1002A" in body["html"]                  # red filet preserved


def test_header_never_uses_poster_or_assets_as_logo_affiche(client):
    wb = _wb_with_media(client)   # 2 product images + 3 gallery + atmosphere
    _patch_banner(client, wb, logo={"url": "https://r2.example/brandlogo.png"},
                  channel_name="CUISTANCE Europe", header_variant="ttt_logo_banner")
    _gen(client, wb, "affiche"); _select(client, wb, "affiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    header_region = body["html"].split("E1002A")[0]              # header bar only
    assert "https://r2.example/brandlogo.png" in header_region   # only the email_banner.logo
    poster_url = body["body_visual"]["url"] or "ZZZ_NONE"
    for forbidden in (poster_url, "p1.png", "p2.png", "g1.png", "g2.png", "g3.png", "atmo.png"):
        assert forbidden not in header_region                   # never poster/product/gallery/atmosphere as logo


# ---- POSTER2-CUISTANCE-BANNER-COMPOSITE-MODULE-FIX-V1 ----
def test_banner_is_composite_module_with_lockup(client):
    wb = _make_workbench(client)
    _patch_banner(client, wb, logo={"url": "https://r2.example/brandlogo.png"},
                  channel_name="CUISTANCE Europe", campaign_label="Nouveauté")
    _gen(client, wb, "fiche"); _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["banner_variant"] == "brand_standard_header"      # fiche default product variant
    assert body["banner_composite_used"] is True
    assert body["banner_source"] == "uploaded_logo"
    assert body["banner_background_mode"] == "dark_plate"
    assert body["banner_filet_used"] is True
    assert body["banner_logo_url"] == "https://r2.example/brandlogo.png"
    # composite lockup: logo + channel line + campaign tag + red filet (not just a logo flag)
    header_region = body["html"].split("E1002A")[0]
    assert "https://r2.example/brandlogo.png" in header_region        # logo
    assert "CUISTANCE Europe" in header_region                        # channel line
    assert "Nouveaut" in header_region                                # campaign tag
    assert "background:#E1002A" in body["html"]                       # red filet


def test_banner_light_plate_contrast_for_dark_logo(client):
    wb = _make_workbench(client)
    _patch_banner(client, wb, logo={"url": "https://r2.example/darklogo.png"},
                  channel_name="C", banner_logo_contrast_mode="light_plate")
    _gen(client, wb, "fiche"); _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["banner_logo_contrast_mode"] == "light_plate"
    # the dark logo sits on a subtle white plate so it is never invisible dark-on-dark
    assert "background:#ffffff;padding:9px 16px;border-radius:10px" in body["html"]
    assert body["header_logo_used"] is True


def test_banner_no_logo_falls_back_to_wordmark(client):
    wb = _make_workbench(client)
    client.patch(f"/api/v2/workbench/{wb}", json={"email_banner": {"channel_name": "CUISTANCE Europe"}})  # no logo
    _gen(client, wb, "fiche"); _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["banner_variant"] == "text_fallback_header"
    assert body["banner_source"] == "wordmark_fallback"
    assert body["banner_composite_used"] is False
    assert body["header_logo_used"] is False
    assert body["header_logo_missing_fallback"] is True


def test_banner_never_uses_product_gallery_atmosphere_poster_as_logo(client):
    wb = _wb_with_media(client)   # 2 product + 3 gallery + atmosphere
    _patch_banner(client, wb, logo={"url": "https://r2.example/brandlogo.png"},
                  channel_name="C", banner_logo_contrast_mode="light_plate")
    _gen(client, wb, "affiche"); _select(client, wb, "affiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    header_region = body["html"].split("E1002A")[0]
    assert "https://r2.example/brandlogo.png" in header_region        # only the email_banner.logo
    poster_url = body["body_visual"]["url"] or "ZZZ_NONE"
    for forbidden in (poster_url, "p1.png", "p2.png", "g1.png", "g2.png", "g3.png", "atmo.png"):
        assert forbidden not in header_region
    assert body["banner_composite_used"] is True


# ---- POSTER2-BANNER-PRODUCT-SPEC-AND-DESIGN-REVIEW-V1: route-specific product banner defaults ----
def test_fiche_defaults_to_brand_standard_header(client):
    wb = _make_workbench(client)
    _patch_banner(client, wb, logo={"url": "https://r2.example/brandlogo.png"}, channel_name="CUISTANCE Europe")
    _gen(client, wb, "fiche"); _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["banner_variant"] == "brand_standard_header"
    assert body["banner_composite_used"] is True
    assert body["banner_source"] == "uploaded_logo"


def test_affiche_defaults_to_campaign_poster_header(client):
    wb = _make_workbench(client)
    _patch_banner(client, wb, logo={"url": "https://r2.example/brandlogo.png"}, channel_name="CUISTANCE Europe")
    _gen(client, wb, "affiche"); _select(client, wb, "affiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["banner_variant"] == "campaign_poster_header"
    assert body["banner_composite_used"] is True
    # the campaign header must not duplicate the spec block or add a double header
    assert "Tarif = Nous contacter" not in body["html"]
    assert body["supporting_media_strip_present"] is False


def test_missing_logo_defaults_to_text_fallback_header(client):
    wb = _make_workbench(client)
    client.patch(f"/api/v2/workbench/{wb}", json={"email_banner": {"channel_name": "CUISTANCE Europe"}})
    _gen(client, wb, "fiche"); _select(client, wb, "fiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["banner_variant"] == "text_fallback_header"
    assert body["banner_source"] == "wordmark_fallback"
    assert body["header_logo_missing_fallback"] is True
    assert body["banner_composite_used"] is False
