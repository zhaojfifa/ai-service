"""POSTER2-EMAIL-PACKAGE-CANDIDATE-PERSISTENCE-V1 — both route packages coexist + send-time selection + staleness.

Reuses the PR-2/PR-3 fakes (no real render, no real email). A fake resend provider yields a 'sent' status when a
real send is exercised; inline_only yields 'skipped'.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.main import app
from app.services.email.providers import EmailDeliveryResult
from app.services.workbench_records import load_workbench_record
from tests.poster2.test_workbench_candidates import _boom, _fake_affiche, _gen, _make_workbench
from tests.poster2.test_api import _FakePoster2Pipeline


class _FakeSentProvider:
    name = "resend"

    def send(self, *, recipient, subject, preview_text, html, text, attachments=None):
        return EmailDeliveryResult(provider="resend", status="sent", provider_message_id=f"msg_{recipient[:3]}")


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
    for var in ("EMAIL_COPY_OPTIMIZER", "GEMINI_API_KEY", "GOOGLE_API_KEY",
                "EMAIL_ATTACHMENT_ENABLED", "EMAIL_ATTACHMENT_BUILD_ON_PREVIEW", "EMAIL_ATTACHMENT_DEFAULT_TYPES"):
        monkeypatch.delenv(var, raising=False)
    from app.config import get_settings
    get_settings.cache_clear()
    return TestClient(app)


def _select(client, wb, route):
    return client.patch(f"/api/v2/workbench/{wb}/selected-visual", json={"selected_email_body_visual": route})


def _packages(client, wb):
    return client.get(f"/api/v2/workbench/{wb}/email/packages").json()["email_package_candidates"]


def _both(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    _gen(client, wb, "fiche")
    return wb


# 1 + 2
def test_both_packages_coexist_and_retained(client):
    wb = _both(client)
    pc = _packages(client, wb)
    assert pc["fiche"]["status"] == "ready"
    assert pc["affiche"]["status"] == "ready"
    assert pc["fiche"]["package_type"] == "fiche"
    assert pc["affiche"]["package_type"] == "affiche"


# 3 — switching selection does not erase the other package
def test_switching_selection_keeps_both_packages(client):
    wb = _both(client)
    _select(client, wb, "fiche")
    pc = _packages(client, wb)
    assert pc["fiche"]["status"] == "ready" and pc["affiche"]["status"] == "ready"
    _select(client, wb, "affiche")
    pc = _packages(client, wb)
    assert pc["fiche"]["status"] == "ready" and pc["affiche"]["status"] == "ready"  # fiche still there


# 4 — fiche package preserves supporting-media diagnostics
def test_fiche_package_preserves_supporting_media(client):
    wb = _make_workbench(client)
    client.patch(f"/api/v2/workbench/{wb}", json={"product_assets": {
        "product_images": [{"url": "https://r2.example/p1.png"}, {"url": "https://r2.example/p2.png"}],
        "gallery_images": [{"url": "https://r2.example/g1.png"}, {"url": "https://r2.example/g2.png"}, {"url": "https://r2.example/g3.png"}]}})
    _gen(client, wb, "fiche")
    pc = _packages(client, wb)
    f = pc["fiche"]
    assert f["uses_poster_generation"] is False and f["generated_from"] == "workbench_truth"
    assert f["supporting_media_count"] == 3 and f["product_image_count"] == 2 and f["gallery_image_count"] == 3
    assert f["container_visual_variant"] == "ttt_product_sheet_container"


# 5 — affiche package preserves poster_key
def test_affiche_package_preserves_poster_key(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    a = _packages(client, wb)["affiche"]
    assert a["poster_key"]
    assert a["container_visual_variant"] == "ttt2_campaign_container"
    assert "available_attachment_types" in a


# 6 — send sends the selected package + reports sent_package_type
def test_send_reports_sent_package_type(client, monkeypatch):
    monkeypatch.setattr(main, "get_email_provider", lambda mode: _FakeSentProvider())
    wb = _both(client)
    _select(client, wb, "fiche")
    r = client.post(f"/api/v2/workbench/{wb}/email/send",
                    json={"recipients": ["a@x.com"], "mode": "real", "confirm_send": True,
                          "delivery_mode": "resend", "selected_email_package": "fiche"})
    assert r.status_code == 200
    b = r.json()
    assert b["sent_package_type"] == "fiche"
    assert b["selected_email_body_visual"] == "fiche"
    assert b["container_visual_variant"] == "ttt_product_sheet_container"
    assert b["real_email_sent"] is True
    assert b["attempts"][0]["provider_message_id"]


# 7 — explicit package mismatch is rejected
def test_send_rejects_package_mismatch(client):
    wb = _both(client)
    _select(client, wb, "fiche")
    r = client.post(f"/api/v2/workbench/{wb}/email/send",
                    json={"recipients": ["a@x.com"], "confirm_send": True, "selected_email_package": "affiche"})
    assert r.status_code == 422
    assert r.json()["detail"] == "selected_package_mismatch"


# 8 — staleness: changing content after generation marks the package maybe_stale
def test_staleness_maybe_stale_after_content_change(client):
    wb = _make_workbench(client)
    _gen(client, wb, "fiche")
    assert _packages(client, wb)["fiche"]["staleness_status"] == "fresh"
    # change product truth AFTER the candidate was generated
    client.patch(f"/api/v2/workbench/{wb}", json={"product_truth": {"product_name": "Nouveau", "reference": "NX1"}})
    pc = _packages(client, wb)["fiche"]
    assert pc["staleness_status"] == "maybe_stale"
    assert pc["is_stale"] is True
    assert pc["stale_reason"] == "content_changed_after_generation"


# 9 — inline_only (preview-only) is never a real send
def test_inline_only_send_is_not_real(client):
    wb = _both(client)
    _select(client, wb, "affiche")
    r = client.post(f"/api/v2/workbench/{wb}/email/send",
                    json={"recipients": ["a@x.com"], "mode": "test", "confirm_send": True, "delivery_mode": "inline_only"})
    b = r.json()
    assert b["real_email_sent"] is False
    assert b["sent_package_type"] == "affiche"
    assert b["attempts"][0]["status"] == "skipped"


# ---- POSTER2-EMAIL-PACKAGE-SEND-BINDING-HOTFIX-V1 ----
def test_send_affiche_binds_to_affiche(client, monkeypatch):
    monkeypatch.setattr(main, "get_email_provider", lambda mode: _FakeSentProvider())
    wb = _both(client)
    _select(client, wb, "affiche")
    r = client.post(f"/api/v2/workbench/{wb}/email/send",
                    json={"recipients": ["a@x.com"], "mode": "real", "confirm_send": True,
                          "delivery_mode": "resend", "selected_email_package": "affiche"})
    assert r.status_code == 200
    b = r.json()
    assert b["sent_package_type"] == "affiche"
    assert b["selected_email_body_visual"] == "affiche"
    assert b["email_fill_format"] == "campaign_poster_email"
    assert b["container_visual_variant"] == "ttt2_campaign_container"
    assert b["body_visual_poster_key"]            # affiche carries a poster_key (NOT the fiche body)
    assert b["real_email_sent"] is True


def test_send_fiche_binds_to_fiche(client, monkeypatch):
    monkeypatch.setattr(main, "get_email_provider", lambda mode: _FakeSentProvider())
    wb = _both(client)
    _select(client, wb, "fiche")
    r = client.post(f"/api/v2/workbench/{wb}/email/send",
                    json={"recipients": ["a@x.com"], "mode": "real", "confirm_send": True,
                          "delivery_mode": "resend", "selected_email_package": "fiche"})
    assert r.status_code == 200
    b = r.json()
    assert b["sent_package_type"] == "fiche"
    assert b["selected_email_body_visual"] == "fiche"
    assert b["email_fill_format"] == "product_sheet_email"
    assert b["container_visual_variant"] == "ttt_product_sheet_container"
    assert b["body_visual_poster_key"] is None    # fiche has NO poster_key (does not use the affiche poster)


def test_explicit_package_is_authoritative_over_legacy(client, monkeypatch):
    # the explicit selected_email_package drives resolution; the response container proves the right body was sent
    monkeypatch.setattr(main, "get_email_provider", lambda mode: _FakeSentProvider())
    wb = _both(client)
    _select(client, wb, "affiche")
    aff = client.post(f"/api/v2/workbench/{wb}/email/send",
                      json={"recipients": ["a@x.com"], "mode": "real", "confirm_send": True,
                            "delivery_mode": "resend", "selected_email_package": "affiche"}).json()
    _select(client, wb, "fiche")
    fic = client.post(f"/api/v2/workbench/{wb}/email/send",
                      json={"recipients": ["a@x.com"], "mode": "real", "confirm_send": True,
                            "delivery_mode": "resend", "selected_email_package": "fiche"}).json()
    assert aff["container_visual_variant"] == "ttt2_campaign_container" and aff["body_visual_poster_key"]
    assert fic["container_visual_variant"] == "ttt_product_sheet_container" and fic["body_visual_poster_key"] is None


def test_send_response_includes_container_visual_variant(client):
    wb = _both(client)
    _select(client, wb, "affiche")
    b = client.post(f"/api/v2/workbench/{wb}/email/send",
                    json={"recipients": ["a@x.com"], "confirm_send": True, "delivery_mode": "inline_only",
                          "selected_email_package": "affiche"}).json()
    assert b["container_visual_variant"] == "ttt2_campaign_container"
    assert b["real_email_sent"] is False          # inline_only is never a real send
