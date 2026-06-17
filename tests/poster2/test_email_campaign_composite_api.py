"""Additive API smoke for email_campaign_composite_v1 (POSTER2-EMAIL-CAMPAIGN-COMPOSITE-V1-API-SMOKE).

Verifies the smallest additive endpoint branch routes template_id=email_campaign_composite_v1 to its
dedicated render path and returns the deterministic, evidence-backed contract review. AssetLoader is
mocked with case001 CUISTANCE images + an operator-upload substrate (no network, no AI, no secrets).
Existing template families/routes are untouched.
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
_SUBSTRATE = _REPO / "docs/poster2/assets/case001_campaign_explainer_heavy_v1/raw_substrate_01_fries_hero.png"


def _img(p, fallback=(200, 200, 200)):
    if Path(p).exists():
        return Image.open(p).convert("RGB")
    return Image.new("RGB", (400, 400), fallback)


class _FakeAssetLoader:
    """Returns case001 CUISTANCE assets; scenario = operator-upload substrate. No network."""

    async def load(self, spec):
        return SimpleNamespace(
            logo=_img(_PKG / "cuistance_logo_assets/cuistance_logo_01.jpg", (250, 250, 250)),
            product=_img(_PKG / "cuistance_product_assets/fryer_产品图.jpg"),
            gallery=[_img(_PKG / "cuistance_gallery_assets/Electric Fryer1.jpg"),
                     _img(_PKG / "cuistance_product_assets/fryer_产品图2.jpg"),
                     _img(_PKG / "cuistance_gallery_assets/Electric Fryer2.jpg")],
            scenario=_img(_SUBSTRATE, (180, 90, 30)),
        )


def _post(client):
    return client.post(
        "/api/v2/generate-poster",
        json={
            "brand_name": "CUISTANCE",
            "agent_name": "CUISTANCE",
            "title": "Les Friteuses Électriques",
            "features": [],  # empty -> deterministic case001 callout defaults (incl. 190°C) apply
            "product_image": {"url": "https://example.test/fryer.png"},
            "scenario_image": {"url": "https://example.test/substrate.png"},
            "template_id": "email_campaign_composite_v1",
            "renderer_mode": "puppeteer",
        },
    )


@pytest.fixture(autouse=True)
def _isolate(monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.poster2.asset_loader.AssetLoader", _FakeAssetLoader)
    monkeypatch.setattr("app.services.poster_records.POSTER_RECORD_DIR", tmp_path / "records")


def test_api_smoke_email_campaign_composite_v1():
    client = TestClient(app)
    resp = _post(client)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # routes to the additive family
    assert body["template_id"] == "email_campaign_composite_v1"
    assert body["template_contract_version"] == "poster2.email_campaign_composite_v1.v1"

    # output artifact produced
    assert body["final_url"].startswith("data:image/png;base64,")
    assert len(body["final_url"]) > 1000

    # contract review (deterministic, evidence-backed)
    review = body["email_campaign_composite_contract_review"]
    assert review is not None
    assert review["structure_complete"] is True
    assert review["callout_count"] == 3
    truth = review["business_truth"]
    assert truth["thermostat_uses_unsupported_0_200C"] is False
    assert truth["leakage_clean"] is True
    assert truth["ai_substrate_is_truth"] is False
    assert truth["brand"] == "CUISTANCE"
    # operator-gated substrate, never AI truth
    assert review["ai_runtime_asset_used"] is False
    assert truth["substrate_source"] == "operator_upload"


def test_api_smoke_does_not_leak_catalog_hero_fields():
    """The additive branch must not emit Catalog Hero / Family B review shells."""
    client = TestClient(app)
    body = _post(client).json()
    assert "catalog_hero_contract_review" not in body
    assert "catalog_hero_grammar_profile" not in body
    assert "template_b_parity_review" not in body
