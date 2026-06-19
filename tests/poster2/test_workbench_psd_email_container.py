"""PSD email container (cuistance_email_container_psd_v1) — additive preview evidence.

The deterministic email assembly is tagged as the PSD-derived email container and exposes container evidence
(format mapping, header_source, legacy_truth_rejected, workbench_truth_used). Business facts come ONLY from
Workbench; no old gas/Technitalia fact may appear in the assembled email. Reuses the PR-2/PR-3 fakes (no real render).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.poster2.test_workbench_candidates import _boom, _fake_affiche, _gen, _make_workbench
from tests.poster2.test_api import _FakePoster2Pipeline

# legacy facts from 产品海报.psd that must NEVER appear in the assembled CUISTANCE email
LEGACY_FACTS = ["LES RÉCHAUDS GAZ", "XR 144", "BRULEUR", "Technitalia", "Codimatel", "01 41 53", "kaly@", "COUP DE COEUR"]


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


def _preview(client, wb):
    client.patch(f"/api/v2/workbench/{wb}", json={"email_banner": {
        "logo": {"url": "https://r2.example/logo.png"}, "channel_name": "CUISTANCE Europe",
        "campaign_label": "Nouveauté", "selected_banner_ref": "option_1"}})
    client.patch(f"/api/v2/workbench/{wb}/selected-visual", json={"selected_email_body_visual": "affiche"})
    return client.post(f"/api/v2/workbench/{wb}/email/preview")


def test_preview_exposes_psd_email_container(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    r = _preview(client, wb)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email_container_template_id"] == "cuistance_email_container_psd_v1"
    assert body["email_fill_format"] == "campaign_poster_email"  # affiche default
    ec = body["email_container"]
    assert ec["uses_current_selected_visual"] is True
    # header is now the ttt.html-style clean bar (PSD dark-header overlay distortion closed)
    assert body["email_header_source"] == "ttt_html_header"
    assert ec["email_header_source"] == "ttt_html_header"
    assert ec["header_source"] == "ttt_html_header"
    assert ec["header_visual_mode"] == "css_dark_bar_wordmark"
    assert ec["uses_header_band_cover"] is False
    assert ec["logo_not_stretched"] is True and ec["logo_not_clipped"] is True
    assert ec["header_only"] is True
    assert ec["no_body_content_in_header"] is True
    assert ec["no_product_visual_in_header"] is True
    assert ec["no_cta_in_header"] is True
    assert ec["no_footer_in_header"] is True
    assert ec["psd_header_logo_fit_known_issue_closed"] is True
    assert ec["legacy_truth_rejected"] is True
    assert ec["workbench_truth_used"] is True
    assert ec["body_visual_poster_key"] == body["body_visual"]["poster_key"]


def test_frontend_has_full_preview_modal():
    from pathlib import Path
    html = Path("frontend/cuistance_trial.html").read_text(encoding="utf-8")
    assert "btn-full-preview" in html
    assert "打开完整预览" in html
    # full preview = in-page modal (not popup-blockable) with iframe srcdoc + a Blob new-tab backup link
    assert "fullPreviewModal" in html and "fullPreviewFrame" in html
    assert "srcdoc" in html and "createObjectURL" in html


def test_frontend_step1_banner_selection_removed():
    from pathlib import Path
    html = Path("frontend/cuistance_trial.html").read_text(encoding="utf-8")
    # Step 1 no longer collects a banner skin; Step 3 has no header-band option picker
    assert 'id="slot-banner"' not in html
    assert 'id="bannerOptions"' not in html
    # header is the clean ttt wordmark, not a header-band cover
    assert "ttt-header-preview" in html and "ttt-wordmark" in html


def test_assembled_email_has_no_legacy_gas_truth(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    html = _preview(client, wb).json()["html"]
    for fact in LEGACY_FACTS:
        assert fact.lower() not in html.lower(), f"legacy fact leaked into email: {fact}"


# ---- email body visual variant (no inner poster banner) ----
import base64
import io as _io
from PIL import Image as _Image
from app.services.email.attachments import derive_email_body_visual, EMAIL_CAMPAIGN_COMPOSITE_HEADER_CROP_RATIO


def _real_png_data_url(w, h):
    im = _Image.new("RGB", (w, h), (30, 30, 30))
    buf = _io.BytesIO(); im.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def test_derive_email_body_visual_crops_composite_banner(tmp_path, monkeypatch):
    # poster_record is NOT persisted in this unit test; derive should still return the cropped variant
    monkeypatch.setattr("app.services.poster_records.save_poster_record", lambda r: r)
    monkeypatch.setattr("app.services.email.attachments.put_bytes", lambda *a, **k: None)  # force local/data-url path
    h = 1754
    record = {
        "poster_key": "p2_unit_crop",
        "template_id": "email_campaign_composite_v1",
        "final_poster": {"filename": "x.png", "media_type": "image/png", "url": _real_png_data_url(1240, h)},
        "render_result": {"template_id": "email_campaign_composite_v1"},
    }
    ev = derive_email_body_visual(record)
    assert ev["variant"] == "email_embedded_no_header"
    assert ev["contains_own_banner"] is False
    assert ev["cropped"] is True
    assert ev["crop_top_px"] == round(h * EMAIL_CAMPAIGN_COMPOSITE_HEADER_CROP_RATIO) == 130
    # the derived image is shorter than the source by exactly the banner height
    src = base64.b64decode(ev["url"].split(",", 1)[1])
    with _Image.open(_io.BytesIO(src)) as out:
        assert out.size[1] == h - 130
    # standalone poster URL is preserved separately on the record
    assert record["final_poster"]["url"].startswith("data:image/png")


def _fake_affiche_real_png():
    from fastapi.responses import JSONResponse
    from app.services.poster_records import create_poster_record, generate_poster_key
    async def _fake(request_id, spec, payload):
        pk = generate_poster_key()
        url = _real_png_data_url(1240, 1754)
        body = {"poster_key": pk, "trace_id": "t", "template_id": "email_campaign_composite_v1",
                "final_url": url, "render_engine_used": "chromium", "degraded": False, "structure_complete": True,
                "email_campaign_composite_contract_review": {"structure_complete": True, "callout_count": 3}}
        create_poster_record(poster_key=pk, request_snapshot={"template_id": payload.template_id},
                             render_result=body, final_poster={"filename": f"{pk}.png", "media_type": "image/png", "url": url})
        return JSONResponse(content=body)
    return _fake


def test_preview_uses_no_header_body_visual_variant(client, monkeypatch):
    monkeypatch.setattr("app.main._generate_email_campaign_composite_v1", _fake_affiche_real_png())
    monkeypatch.setattr("app.services.email.attachments.put_bytes", lambda *a, **k: None)  # local/data-url derive
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    _preview(client, wb)
    body = client.post(f"/api/v2/workbench/{wb}/email/preview").json()
    assert body["body_visual_variant"] == "email_embedded_no_header"
    assert body["body_visual_contains_own_banner"] is False
    assert body["email_body_visual_contract_pass"] is True
    # standalone poster preserved separately from the embedded body visual
    assert body["standalone_poster_url"]
    assert body["email_body_visual_url"]
    assert body["standalone_poster_url"] != body["email_body_visual_url"]
    # Step3 email body slot uses the email body visual (NOT the standalone poster url)
    assert body["body_visual"]["url"] == body["email_body_visual_url"]
    # campaign_poster_email + ttt_html_header => embedded body must not contain its own banner
    assert body["email_fill_format"] == "campaign_poster_email"
    assert body["email_header_source"] == "ttt_html_header"
