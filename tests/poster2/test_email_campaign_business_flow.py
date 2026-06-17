"""Isolated business-flow test: INPUT MATERIALS -> GENERATE POSTER -> EMAIL PREVIEW -> SEND ADAPTER.

Exercises the real endpoints (generate / email preview / email send) for email_campaign_composite_v1 with
case001 CUISTANCE materials (AssetLoader mocked; no network/AI/secrets). Verifies deterministic truth and
the email send adapter behavior for both delivery modes (inline_only success; resend reports its blocker
cleanly when unconfigured). Sends a LEAN body (the full poster data: URL exceeds the body guard by design).
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

_REPO = Path(__file__).resolve().parents[2]
_PKG = _REPO / "docs/poster2/assets/sop_source_materialization_v1/cuistance_our_product_truth_pack"
_SUB = _REPO / "docs/poster2/assets/case001_campaign_explainer_heavy_v1/raw_substrate_01_fries_hero.png"

CALLOUTS = ["2 cuves inox amovibles", "Thermostat réglable jusqu'à 190°C", "Construction inox / usage professionnel"]
STRAPLINE = "Cuisson professionnelle, croustillant maîtrisé"
CONTACT = "commercial@cuistance.eu · +33 (0)1 71 84 11 20 · cuistance-europe.com"


def _img(p, fb=(200, 200, 200)):
    return Image.open(p).convert("RGB") if Path(p).exists() else Image.new("RGB", (400, 400), fb)


class _FakeAssetLoader:
    async def load(self, spec):
        return SimpleNamespace(
            logo=_img(_PKG / "cuistance_logo_assets/cuistance_logo_01.jpg", (250, 250, 250)),
            product=_img(_PKG / "cuistance_product_assets/fryer_产品图.jpg"),
            gallery=[_img(_PKG / "cuistance_gallery_assets/Electric Fryer1.jpg")],
            scenario=_img(_SUB, (180, 90, 30)),
        )


@pytest.fixture(autouse=True)
def _isolate(monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.poster2.asset_loader.AssetLoader", _FakeAssetLoader)
    monkeypatch.setattr("app.services.poster_records.POSTER_RECORD_DIR", tmp_path / "records")


def _generate(client):
    return client.post("/api/v2/generate-poster", json={
        "brand_name": "CUISTANCE", "agent_name": "CUISTANCE",
        "title": "Les Friteuses Électriques", "subtitle": STRAPLINE, "features": CALLOUTS,
        "product_image": {"url": "https://example.test/fryer.png"},
        "scenario_image": {"url": "https://example.test/substrate.png"},
        "template_id": "email_campaign_composite_v1", "renderer_mode": "puppeteer",
    })


def _lean_send_body(poster_key, mode):
    return {
        "poster_key": poster_key, "recipient": "owner@example.com", "delivery_mode": mode,
        "subject": "CUISTANCE | Les Friteuses Électriques", "preview_text": STRAPLINE,
        "html": "<p>Les Friteuses Électriques</p><ul>" + "".join(f"<li>{c}</li>" for c in CALLOUTS) + "</ul>",
        "text": "Les Friteuses Électriques\n- " + "\n- ".join(CALLOUTS) + f"\n{CONTACT}",
    }


def test_business_flow_input_generate_preview_send():
    client = TestClient(app)

    # 1+2: input materials -> generate poster
    gen = _generate(client)
    assert gen.status_code == 200, gen.text
    gbody = gen.json()
    assert gbody["template_id"] == "email_campaign_composite_v1"
    review = gbody["email_campaign_composite_contract_review"]
    assert review["structure_complete"] is True
    assert review["callout_count"] == 3
    truth = review["business_truth"]
    assert truth["brand"] == "CUISTANCE"
    assert truth["leakage_clean"] is True
    assert truth["thermostat_uses_unsupported_0_200C"] is False
    assert truth["ai_substrate_is_truth"] is False
    assert truth["substrate_source"] == "operator_upload"
    poster_key = gbody["poster_key"]
    assert gbody["final_url"].startswith("data:image/png;base64,")

    # 3a: email preview (deterministic, CUISTANCE)
    prev = client.post("/api/v2/email/preview", json={"poster_key": poster_key})
    assert prev.status_code == 200, prev.text
    pbody = prev.json()
    assert "CUISTANCE" in pbody["subject"]
    blob = (pbody["subject"] + pbody["text"]).lower()
    assert "technitalia" not in blob and "codimatel" not in blob and "réchaud" not in blob

    # 3b: send adapter — inline_only succeeds (path proven); resend reports its blocker cleanly
    inline = client.post("/api/v2/email/send", json=_lean_send_body(poster_key, "inline_only"))
    assert inline.status_code == 200, inline.text
    assert inline.json()["status"] == "preview_only"

    resend = client.post("/api/v2/email/send", json=_lean_send_body(poster_key, "resend"))
    assert resend.status_code == 200, resend.text
    rstatus = resend.json()["status"]
    # unconfigured -> clean error; configured -> sent. Either is a valid adapter outcome.
    assert rstatus in {"error", "sent"}
    if rstatus == "error":
        assert "configured" in (resend.json().get("error") or "").lower()
