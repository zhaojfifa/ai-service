"""PR-4 — manual multi-recipient confirmed send + evidence.

Sends the deterministic PR-3S email package (consumes the same assembly as preview; no reconstruction).
Reuses PR-2/PR-3 fakes (no real render, no real email). A fake resend provider is used where a 'sent' status
is needed; inline_only yields 'skipped' (preview_only).
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
    for var in (
        "EMAIL_COPY_OPTIMIZER", "GEMINI_API_KEY", "GOOGLE_API_KEY",
        "EMAIL_ATTACHMENT_ENABLED", "EMAIL_ATTACHMENT_BUILD_ON_PREVIEW", "EMAIL_ATTACHMENT_DEFAULT_TYPES",
    ):
        monkeypatch.delenv(var, raising=False)
    from app.config import get_settings

    get_settings.cache_clear()
    return TestClient(app)


def _ready(client, candidate_type="affiche"):
    wb = _make_workbench(client)
    _gen(client, wb, candidate_type)
    client.patch(f"/api/v2/workbench/{wb}/selected-visual", json={"selected_email_body_visual": candidate_type})
    return wb


def _send(client, wb, **body):
    payload = {"recipients": ["a@x.com"], "mode": "test", "confirm_send": True}
    payload.update(body)
    return client.post(f"/api/v2/workbench/{wb}/email/send", json=payload)


# 1
def test_send_fails_when_no_selection(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")  # not selected
    r = _send(client, wb)
    assert r.status_code == 422
    assert r.json()["detail"] == "no_selected_email_body_visual"


# 2
def test_send_fails_when_selected_candidate_not_ready(client):
    wb = _make_workbench(client)
    from app.services.workbench_records import load_workbench_record, save_workbench_record

    rec = load_workbench_record(wb)
    rec["selected_email_body_visual"] = "fiche"  # no fiche candidate -> not ready
    save_workbench_record(rec)
    r = _send(client, wb)
    assert r.status_code == 422
    assert r.json()["detail"] == "selected_candidate_not_ready"


# 3
def test_send_fails_when_email_body_plan_cannot_be_built(client, monkeypatch):
    wb = _ready(client)

    def _boom_assembly(*a, **k):
        raise RuntimeError("plan build failed")

    monkeypatch.setattr(main, "build_email_assembly", _boom_assembly)
    r = _send(client, wb)
    assert r.status_code == 422
    assert r.json()["detail"] == "email_body_plan_unavailable"


# 4
def test_send_fails_when_recipients_empty(client):
    wb = _ready(client)
    r = _send(client, wb, recipients=[])
    assert r.status_code == 422
    assert r.json()["detail"] == "recipients_required"


# 5
def test_send_fails_when_confirm_send_false(client):
    wb = _ready(client)
    r = _send(client, wb, confirm_send=False)
    assert r.status_code == 422
    assert r.json()["detail"] == "confirm_send_required"


# 6
def test_valid_recipients_produce_send_attempts(client):
    wb = _ready(client)
    r = _send(client, wb, recipients=["a@x.com", "b@y.com"])
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert len(body["attempts"]) == 2
    # inline_only -> skipped (preview_only), evidence still recorded
    assert body["skipped_count"] == 2
    persisted = load_workbench_record(wb)["send_attempts"]
    assert len(persisted) == 2


# 7
def test_mixed_valid_invalid_recipients_isolate_failures(client, monkeypatch):
    monkeypatch.setattr(main, "get_email_provider", lambda mode: _FakeSentProvider())
    wb = _ready(client)
    r = _send(client, wb, recipients=["good@x.com", "bad@@", "also@y.com"], delivery_mode="resend")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    assert body["sent_count"] == 2
    assert body["failed_count"] == 1
    by_recipient = {a["recipient"]: a for a in body["attempts"]}
    assert by_recipient["good@x.com"]["status"] == "sent"
    assert by_recipient["also@y.com"]["status"] == "sent"
    assert by_recipient["bad@@"]["status"] == "error"
    assert by_recipient["bad@@"]["error_code"] == "invalid_recipient"


# 8
def test_duplicate_recipients_handled_deterministically(client, monkeypatch):
    monkeypatch.setattr(main, "get_email_provider", lambda mode: _FakeSentProvider())
    wb = _ready(client)
    r = _send(client, wb, recipients=["dup@x.com", "DUP@x.com", "dup@x.com", "other@y.com"], delivery_mode="resend")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2  # unique only
    assert body["deduplicated_count"] == 2
    assert sorted(a["recipient"] for a in body["attempts"]) == ["dup@x.com", "other@y.com"]


# 9
def test_attempts_include_selected_visual_and_poster_key(client):
    wb = _ready(client, "affiche")
    affiche_pk = load_workbench_record(wb)["poster_candidates"]["affiche"]["poster_key"]
    body = _send(client, wb, recipients=["a@x.com"]).json()
    attempt = body["attempts"][0]
    assert attempt["selected_email_body_visual"] == "affiche"
    assert attempt["body_visual_poster_key"] == affiche_pk


# 10
def test_attempts_include_layout_type(client):
    wb = _ready(client)
    attempt = _send(client, wb, recipients=["a@x.com"]).json()["attempts"][0]
    assert attempt["layout_type"] == "single_product_promo"


# 11
def test_attempts_include_subject_and_timestamp(client):
    wb = _ready(client)
    attempt = _send(client, wb, recipients=["a@x.com"]).json()["attempts"][0]
    assert "subject" in attempt and attempt["subject"]
    assert attempt["at"]  # ISO timestamp present


def test_real_mode_still_requires_confirmation(client):
    wb = _ready(client)
    r = _send(client, wb, mode="real", confirm_send=False)
    assert r.status_code == 422
    assert r.json()["detail"] == "confirm_send_required"


def test_send_unknown_workbench_404(client):
    r = client.post("/api/v2/workbench/wb_missing/email/send",
                    json={"recipients": ["a@x.com"], "confirm_send": True})
    assert r.status_code == 404


def test_real_mode_marks_workbench_sent(client, monkeypatch):
    monkeypatch.setattr(main, "get_email_provider", lambda mode: _FakeSentProvider())
    wb = _ready(client)
    r = _send(client, wb, mode="real", recipients=["a@x.com"], delivery_mode="resend")
    assert r.status_code == 200
    assert r.json()["sent_count"] == 1
    assert load_workbench_record(wb)["status"] == "sent"
