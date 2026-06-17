"""Additive R2 hosting-bridge tests for email_campaign_composite_v1.

When R2 is configured, the generate endpoint must host the poster and return an HTTPS final_url
(not a data: URL); when R2 is unconfigured it must fall back to the inline data: URL. AssetLoader and
the r2_client.put_bytes bridge are mocked (no network / no real R2 / no secrets).
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


def _img(p, fb=(200, 200, 200)):
    return Image.open(p).convert("RGB") if Path(p).exists() else Image.new("RGB", (400, 400), fb)


class _FakeAssetLoader:
    async def load(self, spec):
        return SimpleNamespace(
            logo=_img(_PKG / "cuistance_logo_assets/cuistance_logo_01.jpg", (250, 250, 250)),
            product=_img(_PKG / "cuistance_product_assets/fryer_产品图.jpg"),
            gallery=[_img(_PKG / "cuistance_gallery_assets/Electric Fryer1.jpg")],
            scenario=None,
        )


def _post(client):
    return client.post("/api/v2/generate-poster", json={
        "brand_name": "CUISTANCE", "agent_name": "CUISTANCE", "title": "Les Friteuses Électriques",
        "product_image": {"url": "https://example.test/fryer.png"},
        "template_id": "email_campaign_composite_v1", "renderer_mode": "puppeteer",
    })


@pytest.fixture(autouse=True)
def _isolate(monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.poster2.asset_loader.AssetLoader", _FakeAssetLoader)
    monkeypatch.setattr("app.services.poster_records.POSTER_RECORD_DIR", tmp_path / "records")


def test_hosts_on_r2_when_configured(monkeypatch):
    hosted = "https://r2.example.test/poster2/email_campaign_composite/x/poster.png"
    monkeypatch.setattr("app.services.r2_client.put_bytes", lambda key, data, content_type="": hosted)
    body = _post(TestClient(app)).json()
    assert body["final_url"] == hosted
    assert not body["final_url"].startswith("data:")
    assert body["email_campaign_composite_contract_review"]["poster_hosting"] == "r2"


def test_falls_back_to_data_url_when_r2_unconfigured(monkeypatch):
    monkeypatch.setattr("app.services.r2_client.put_bytes", lambda key, data, content_type="": None)
    body = _post(TestClient(app)).json()
    assert body["final_url"].startswith("data:image/png;base64,")
    assert body["email_campaign_composite_contract_review"]["poster_hosting"] == "inline_data_url"
