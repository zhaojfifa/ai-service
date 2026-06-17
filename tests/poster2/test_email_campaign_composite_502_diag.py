"""Regression: email_campaign_composite_v1 generate failures return JSON (never HTML 502), and a Chromium
render failure falls back to Pillow (200 degraded) instead of hanging the worker.

Guards against the remote 502 -> frontend "Unexpected token '<'" (HTML parsed as JSON).
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.poster2 import email_campaign_composite as ecc

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
    }, headers={"X-Request-ID": "diag-req-1"})


@pytest.fixture(autouse=True)
def _isolate(monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.poster2.asset_loader.AssetLoader", _FakeAssetLoader)
    monkeypatch.setattr("app.services.poster_records.POSTER_RECORD_DIR", tmp_path / "records")


def test_render_failure_returns_json_not_html(monkeypatch):
    async def _boom(inputs, request_id=None):
        raise RuntimeError("simulated render crash")
    monkeypatch.setattr(ecc, "render_async", _boom)

    resp = _post(TestClient(app))
    assert resp.status_code == 500
    # must be JSON (no HTML -> no "Unexpected token '<'")
    assert resp.headers.get("content-type", "").startswith("application/json")
    body = resp.json()  # would raise if HTML
    assert body["ok"] is False
    assert body["stage"] == "render"
    assert body["error_type"] == "RuntimeError"
    assert body["request_id"] == "diag-req-1"
    assert "message" in body


def test_chromium_failure_falls_back_to_pillow_200(monkeypatch):
    # force the chromium path to fail; render_async must catch and return a pillow (degraded) result
    async def _boom_chromium(html):
        raise RuntimeError("simulated chromium OOM/timeout")
    monkeypatch.setattr(ecc, "_chromium_render", _boom_chromium)

    resp = _post(TestClient(app))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["template_id"] == "email_campaign_composite_v1"
    assert body["render_engine_used"] == "pillow_fallback"
    assert body["degraded"] is True
    rev = body["email_campaign_composite_contract_review"]
    assert rev["structure_complete"] is True
    assert rev["callout_count"] == 3
    assert rev["business_truth"]["leakage_clean"] is True
    assert rev["business_truth"]["thermostat_uses_unsupported_0_200C"] is False
    assert rev["business_truth"]["ai_substrate_is_truth"] is False
