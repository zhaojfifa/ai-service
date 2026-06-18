"""PR-1 — CUISTANCE commercial trial workbench truth model.

Covers: create empty workbench, patch product_truth, confirm parameter rows, lock confirmed parameters,
reject invalid parameter keys/states, reject base64 in asset fields, url/key-only product_assets + email_banner,
round-trip read/write, 190°C accepted as an ordinary thermostat value (not a platform rule), and PR-2…PR-4
placeholders remain inert.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client(monkeypatch, tmp_path):
    # isolate the workbench store to a temp dir; force the R2-less local fallback path
    monkeypatch.setattr("app.services.workbench_records.WORKBENCH_RECORD_DIR", tmp_path / "wb")
    monkeypatch.setattr(
        "app.services.workbench_records.put_bytes", lambda *a, **k: None
    )

    def _boom_get(*a, **k):
        raise RuntimeError("no r2 in test")

    monkeypatch.setattr("app.services.workbench_records.get_bytes", _boom_get)
    return TestClient(app)


def test_create_empty_workbench(client):
    r = client.post("/api/v2/workbench", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["workbench_key"].startswith("wb_")
    assert body["language"] == "zh"
    assert body["status"] == "draft"
    assert body["product_truth"]["parameters"] == []
    assert body["product_truth"]["parameters_locked"] is False
    assert body["product_assets"]["product_images"] == []
    assert body["email_banner"]["channel_name"] == ""
    # PR-2…PR-4 placeholders inert
    assert body["poster_candidates"] == {}
    assert body["selected_email_body_visual"] is None
    assert body["email_package_ref"] is None
    assert body["recipients"] == []
    assert body["send_attempts"] == []


def test_create_french_language(client):
    r = client.post("/api/v2/workbench", json={"language": "fr"})
    assert r.status_code == 200
    assert r.json()["language"] == "fr"


def test_patch_product_truth_and_round_trip(client):
    key = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    patch = {
        "product_truth": {
            "product_name": "Friteuse électrique double",
            "reference": "EF132V",
            "description": "Deux cuves inox amovibles, construction robuste.",
            "parameters": [
                {"key": "reference", "label": "Référence", "value": "EF132V", "source": "manual", "state": "pending"},
                {"key": "capacity", "label": "Capacité", "value": "2 cuves 13 + 13 L", "source": "imported", "state": "pending"},
            ],
        }
    }
    r = client.patch(f"/api/v2/workbench/{key}", json=patch)
    assert r.status_code == 200
    truth = r.json()["product_truth"]
    assert truth["reference"] == "EF132V"
    assert truth["description"].startswith("Deux cuves")
    assert len(truth["parameters"]) == 2

    # round-trip read returns identical truth
    got = client.get(f"/api/v2/workbench/{key}").json()
    assert got["product_truth"] == truth


def test_confirm_parameters_then_lock(client):
    key = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    # confirm both rows
    confirmed = {
        "product_truth": {
            "parameters": [
                {"key": "power", "value": "3 + 3 kW", "state": "confirmed"},
                {"key": "voltage", "value": "230 V", "state": "confirmed"},
            ],
        }
    }
    r = client.patch(f"/api/v2/workbench/{key}", json=confirmed)
    assert r.status_code == 200
    assert all(p["state"] == "confirmed" for p in r.json()["product_truth"]["parameters"])

    # now lock them
    locked = {
        "product_truth": {
            "parameters": [
                {"key": "power", "value": "3 + 3 kW", "state": "confirmed", "locked": True},
                {"key": "voltage", "value": "230 V", "state": "confirmed", "locked": True},
            ],
            "parameters_locked": True,
        }
    }
    r2 = client.patch(f"/api/v2/workbench/{key}", json=locked)
    assert r2.status_code == 200
    body = r2.json()["product_truth"]
    assert body["parameters_locked"] is True
    assert all(p["locked"] for p in body["parameters"])


def test_lock_without_confirmation_is_rejected(client):
    key = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    r = client.patch(
        f"/api/v2/workbench/{key}",
        json={
            "product_truth": {
                "parameters": [{"key": "power", "value": "3 kW", "state": "pending"}],
                "parameters_locked": True,
            }
        },
    )
    assert r.status_code == 422


def test_locked_row_requires_confirmed_state(client):
    key = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    r = client.patch(
        f"/api/v2/workbench/{key}",
        json={"product_truth": {"parameters": [{"key": "power", "value": "3 kW", "state": "pending", "locked": True}]}},
    )
    assert r.status_code == 422


def test_invalid_parameter_key_rejected(client):
    key = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    r = client.patch(
        f"/api/v2/workbench/{key}",
        json={"product_truth": {"parameters": [{"key": "weight", "value": "10 kg"}]}},
    )
    assert r.status_code == 422


def test_invalid_parameter_state_rejected(client):
    key = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    r = client.patch(
        f"/api/v2/workbench/{key}",
        json={"product_truth": {"parameters": [{"key": "power", "value": "3 kW", "state": "verified"}]}},
    )
    assert r.status_code == 422


def test_thermostat_190c_is_ordinary_value_not_required(client):
    key = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    # 190°C accepted as a normal confirmed thermostat row...
    r = client.patch(
        f"/api/v2/workbench/{key}",
        json={"product_truth": {"parameters": [{"key": "thermostat", "value": "jusqu'à 190°C", "state": "confirmed"}]}},
    )
    assert r.status_code == 200
    assert r.json()["product_truth"]["parameters"][0]["value"] == "jusqu'à 190°C"

    # ...and a product with NO thermostat row is equally valid (190°C is not a platform rule)
    key2 = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    r2 = client.patch(
        f"/api/v2/workbench/{key2}",
        json={
            "product_truth": {
                "parameters": [{"key": "capacity", "value": "5 L", "state": "confirmed"}],
                "parameters_locked": True,
            }
        },
    )
    assert r2.status_code == 200
    assert r2.json()["product_truth"]["parameters_locked"] is True


def test_product_assets_url_key_only(client):
    key = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    r = client.patch(
        f"/api/v2/workbench/{key}",
        json={
            "product_assets": {
                "product_images": [
                    {"url": "https://r2.example/p1.png", "key": "product/p1.png"},
                    {"url": "https://r2.example/p2.png"},
                ],
                "gallery_images": [{"url": "https://r2.example/g1.png"}],
                "atmosphere": {"url": "https://r2.example/scene.png", "is_truth": False},
            }
        },
    )
    assert r.status_code == 200
    assets = r.json()["product_assets"]
    assert len(assets["product_images"]) == 2
    assert assets["product_images"][0]["key"] == "product/p1.png"
    assert assets["atmosphere"]["is_truth"] is False


def test_atmosphere_is_truth_true_rejected(client):
    key = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    r = client.patch(
        f"/api/v2/workbench/{key}",
        json={"product_assets": {"atmosphere": {"url": "https://r2.example/scene.png", "is_truth": True}}},
    )
    assert r.status_code == 422


def test_base64_in_product_image_rejected(client):
    key = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    r = client.patch(
        f"/api/v2/workbench/{key}",
        json={"product_assets": {"product_images": [{"url": "data:image/png;base64,iVBORw0KGgo="}]}},
    )
    assert r.status_code == 422


def test_base64_in_email_banner_logo_rejected(client):
    key = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    r = client.patch(
        f"/api/v2/workbench/{key}",
        json={"email_banner": {"logo": {"url": "data:image/png;base64,AAAA"}}},
    )
    assert r.status_code == 422


def test_email_banner_url_key_only(client):
    key = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    r = client.patch(
        f"/api/v2/workbench/{key}",
        json={
            "email_banner": {
                "logo": {"url": "https://r2.example/logo.png", "key": "logo/logo.png"},
                "background": {"url": "https://r2.example/banner.png"},
                "channel_name": "CUISTANCE Europe",
                "campaign_label": "Nouveauté",
                "selected_banner_ref": "banner_option_01",
            }
        },
    )
    assert r.status_code == 200
    banner = r.json()["email_banner"]
    assert banner["logo"]["key"] == "logo/logo.png"
    assert banner["channel_name"] == "CUISTANCE Europe"
    assert banner["selected_banner_ref"] == "banner_option_01"


def test_get_unknown_workbench_404(client):
    r = client.get("/api/v2/workbench/wb_does_not_exist")
    assert r.status_code == 404
    assert r.json()["detail"] == "workbench_record_not_found"


def test_patch_unknown_workbench_404(client):
    r = client.patch("/api/v2/workbench/wb_missing", json={"language": "fr"})
    assert r.status_code == 404


def test_patch_status_transition_and_language(client):
    key = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    r = client.patch(f"/api/v2/workbench/{key}", json={"status": "assets", "language": "fr"})
    assert r.status_code == 200
    assert r.json()["status"] == "assets"
    assert r.json()["language"] == "fr"


def test_invalid_status_rejected(client):
    key = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    r = client.patch(f"/api/v2/workbench/{key}", json={"status": "published"})
    assert r.status_code == 422


def test_too_many_product_images_rejected(client):
    key = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    r = client.patch(
        f"/api/v2/workbench/{key}",
        json={
            "product_assets": {
                "product_images": [
                    {"url": "https://r2.example/p1.png"},
                    {"url": "https://r2.example/p2.png"},
                    {"url": "https://r2.example/p3.png"},
                ]
            }
        },
    )
    assert r.status_code == 422
