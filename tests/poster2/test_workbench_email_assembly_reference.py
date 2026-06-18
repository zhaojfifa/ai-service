"""PR-3R — assert the assembled email matches the extracted reference grammar.

600px table-safe shell + Email Banner Module + red filet + selected body visual + CTA + footer/legal placeholder.
Reuses the PR-2/PR-3 fakes (no real render). No /api/v2/email/send touched.
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


def _preview_html(client):
    wb = _make_workbench(client)
    client.patch(
        f"/api/v2/workbench/{wb}",
        json={"email_banner": {
            "logo": {"url": "https://r2.example/logo.png"},
            "channel_name": "CUISTANCE Europe",
            "campaign_label": "Nouveauté",
        }},
    )
    _gen(client, wb, "affiche")
    client.patch(f"/api/v2/workbench/{wb}/selected-visual", json={"selected_email_body_visual": "affiche"})
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    return body, body["html"]


def test_assembly_has_600px_table_safe_shell(client):
    _, html = _preview_html(client)
    assert 'width="600"' in html
    assert "max-width:600px" in html
    assert "<table" in html and 'role="presentation"' in html


def test_assembly_has_email_banner_module(client):
    _, html = _preview_html(client)
    assert "#1f2329" in html or "1f2329" in html  # dark brand header
    assert "https://r2.example/logo.png" in html
    assert "CUISTANCE Europe" in html


def test_assembly_has_red_filet_divider(client):
    _, html = _preview_html(client)
    # explicit red accent divider/filet
    assert "background:#E1002A" in html
    assert "height:3px" in html


def test_assembly_has_selected_body_visual(client):
    body, html = _preview_html(client)
    assert body["body_visual"]["url"] == "https://example.com/affiche.png"
    assert "https://example.com/affiche.png" in html


def test_assembly_has_cta(client):
    body, html = _preview_html(client)
    assert body["cta_label"] == "Nous contacter"
    assert "Nous contacter" in html


def test_assembly_has_footer_and_legal_placeholder(client):
    _, html = _preview_html(client)
    assert "Se désabonner" in html  # legal/unsubscribe placeholder (non-functional href="#")
    assert "contact professionnel" in html


def test_assembly_has_no_third_party_tracking(client):
    _, html = _preview_html(client)
    lowered = html.lower()
    for forbidden in ("<script", "list-manage", "mcusercontent", "campaign-image", "zoho", "mailchimp", "track"):
        assert forbidden not in lowered
