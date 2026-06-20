"""PR-3S — Email Body Plan: the preview returns a deterministic plan and the selected visual enters ONLY via
the planned selected_body_visual slot. Reuses PR-2/PR-3 fakes (no real render). Does not touch send.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
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


def _prepare(client, candidate_type):
    wb = _make_workbench(client)
    _gen(client, wb, candidate_type)
    client.patch(f"/api/v2/workbench/{wb}/selected-visual", json={"selected_email_body_visual": candidate_type})
    return wb


# 1
def test_preview_includes_email_body_plan(client):
    wb = _prepare(client, "affiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert "email_body_plan" in body
    assert isinstance(body["email_body_plan"], dict)


# 2
def test_layout_type_is_single_product_promo(client):
    wb = _prepare(client, "affiche")
    plan = client.post(f"/api/v2/workbench/{wb}/email/preview").json()["email_body_plan"]
    assert plan["layout_type"] == "single_product_promo"


# 3
def test_container_width_is_600(client):
    wb = _prepare(client, "affiche")
    plan = client.post(f"/api/v2/workbench/{wb}/email/preview").json()["email_body_plan"]
    assert plan["container_width"] == 600


# 4
def test_module_order_banner_before_body_visual(client):
    wb = _prepare(client, "affiche")
    plan = client.post(f"/api/v2/workbench/{wb}/email/preview").json()["email_body_plan"]
    keys = [m["key"] for m in plan["modules"]]
    # supporting_media_strip is a STRUCTURAL module (between primary visual and description); present=False for affiche
    assert keys == [
        "email_banner", "title_intro", "selected_body_visual", "supporting_media_strip",
        "product_description", "cta", "contact_footer", "legal_footer",
    ]
    assert keys.index("email_banner") < keys.index("selected_body_visual")
    assert keys.index("selected_body_visual") < keys.index("supporting_media_strip") < keys.index("product_description")
    # module order entries carry their position
    assert [m["order"] for m in plan["modules"]] == [1, 2, 3, 4, 5, 6, 7, 8]
    # affiche poster carries its own views -> the strip module is present in structure but not rendered
    strip = next(m for m in plan["modules"] if m["key"] == "supporting_media_strip")
    assert strip["present"] is False


# 5
def test_slot_resolves_affiche_poster_key(client):
    wb = _prepare(client, "affiche")
    affiche_pk = client.get(f"/api/v2/workbench/{wb}").json()["poster_candidates"]["affiche"]["poster_key"]
    plan = client.post(f"/api/v2/workbench/{wb}/email/preview").json()["email_body_plan"]
    slot = plan["selected_body_visual_slot"]
    assert slot["candidate_type"] == "affiche"
    assert slot["poster_key"] == affiche_pk
    assert slot["source"] == "workbench.selected_email_body_visual"


# 6
def test_slot_resolves_fiche_poster_key(client):
    wb = _prepare(client, "fiche")
    fiche_pk = client.get(f"/api/v2/workbench/{wb}").json()["poster_candidates"]["fiche"]["poster_key"]
    plan = client.post(f"/api/v2/workbench/{wb}/email/preview").json()["email_body_plan"]
    assert plan["selected_body_visual_slot"]["candidate_type"] == "fiche"
    assert plan["selected_body_visual_slot"]["poster_key"] == fiche_pk


# 7
def test_final_poster_url_comes_from_poster_record(client):
    wb = _prepare(client, "affiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    slot = body["email_body_plan"]["selected_body_visual_slot"]
    # the affiche fake stored final_poster.url = https://example.com/affiche.png in the poster_record
    assert slot["final_poster_url"] == "https://example.com/affiche.png"
    assert body["body_visual"]["url"] == "https://example.com/affiche.png"


# 8
def test_html_contains_selected_visual_in_slot(client):
    wb = _prepare(client, "affiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    html = body["html"]
    # the selected visual appears via the planned slot (single occurrence of the final poster url)
    assert html.count("https://example.com/affiche.png") == 1
    # banner module precedes the body visual in the assembled html
    assert html.index("#1f2329") < html.index("https://example.com/affiche.png")


# 9
def test_cta_defaults_to_nous_contacter(client):
    wb = _prepare(client, "affiche")
    plan = client.post(f"/api/v2/workbench/{wb}/email/preview").json()["email_body_plan"]
    assert plan["cta"]["label"] == "Nous contacter"
    assert "href" in plan["cta"]


# 10
def test_legal_footer_module_present(client):
    wb = _prepare(client, "affiche")
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    keys = {m["key"]: m["present"] for m in body["email_body_plan"]["modules"]}
    assert keys["legal_footer"] is True
    assert keys["contact_footer"] is True
    assert "Se désabonner" in body["html"]


def test_preview_still_fails_when_no_selection(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")  # not selected
    r = client.post(f"/api/v2/workbench/{wb}/email/preview")
    assert r.status_code == 422
    assert r.json()["detail"] == "no_selected_email_body_visual"
