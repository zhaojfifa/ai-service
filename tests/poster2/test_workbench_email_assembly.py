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
    # ttt_html_header: clean dark bar + CUISTANCE wordmark + red filet + channel meta.
    # The header uses a CSS WORDMARK (not the logo image) and NO header-band background cover.
    assert "1f2329" in body["html"]            # dark bar
    assert "CUISTANCE" in body["html"]         # wordmark
    assert "CUISTANCE Europe" in body["html"]  # channel/campaign meta
    assert "https://r2.example/logo.png" not in body["html"]  # logo image NOT stretched into the header
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
