"""PR-2 — Step 2 email body visual candidates + selected visual persistence.

Reuses the existing /api/v2/generate-poster code path (no renderer fork): the fiche path runs through the fake
PosterPipeline (template_product_sheet_v1); the affiche path is faked at the dedicated composite seam
(_generate_email_campaign_composite_v1) so no real Chromium render is required.
"""
from __future__ import annotations

import pytest
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.main import app
from app.services.poster_records import create_poster_record, generate_poster_key
from tests.poster2.test_api import _FakePoster2Pipeline


def _boom(*a, **k):
    raise RuntimeError("no r2 in test")


def _fake_affiche():
    async def _fake(request_id, spec, payload):
        pk = generate_poster_key()
        body = {
            "poster_key": pk,
            "trace_id": request_id or "trace",
            "template_id": "email_campaign_composite_v1",
            "final_url": "https://example.com/affiche.png",
            "render_engine_used": "chromium",
            "degraded": False,
            "structure_complete": True,
            "email_campaign_composite_contract_review": {
                "structure_complete": True,
                "callout_count": 3,
            },
        }
        create_poster_record(
            poster_key=pk,
            request_snapshot={
                "template_id": payload.template_id,
                "product_secondary_image": (
                    payload.product_secondary_image.url if payload.product_secondary_image else None
                ),
            },
            render_result=body,
            final_poster={"filename": f"{pk}.png", "media_type": "image/png", "url": body["final_url"]},
        )
        return JSONResponse(content=body)

    return _fake


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.workbench_records.WORKBENCH_RECORD_DIR", tmp_path / "wb")
    monkeypatch.setattr("app.services.workbench_records.put_bytes", lambda *a, **k: None)
    monkeypatch.setattr("app.services.workbench_records.get_bytes", _boom)
    monkeypatch.setattr("app.services.poster_records.POSTER_RECORD_DIR", tmp_path / "pr")
    monkeypatch.setattr("app.services.poster_records.put_bytes", lambda *a, **k: None)
    monkeypatch.setattr("app.services.poster_records.get_bytes", _boom)
    # affiche: fake the dedicated composite render seam; fiche: fake the PosterPipeline
    monkeypatch.setattr("app.main._generate_email_campaign_composite_v1", _fake_affiche())
    monkeypatch.setattr("app.main._get_poster2_pipeline", lambda: _FakePoster2Pipeline())
    return TestClient(app)


def _make_workbench(client, *, two_images: bool = True, with_thermostat: bool = True) -> str:
    wb = client.post("/api/v2/workbench", json={}).json()["workbench_key"]
    images = [{"url": "https://r2.example/p1.png", "key": "product/p1.png"}]
    if two_images:
        images.append({"url": "https://r2.example/p2.png", "key": "product/p2.png"})
    params = []
    if with_thermostat:
        params.append({"key": "thermostat", "value": "jusqu'à 190°C", "state": "confirmed"})
    else:
        params.append({"key": "capacity", "value": "2 x 13 L", "state": "confirmed"})
    client.patch(
        f"/api/v2/workbench/{wb}",
        json={
            "product_truth": {
                "product_name": "Friteuse électrique double",
                "reference": "EF132V",
                "description": "Deux cuves inox amovibles, construction robuste.",
                "parameters": params,
            },
            "product_assets": {"product_images": images, "gallery_images": [{"url": "https://r2.example/g1.png"}]},
            "email_banner": {"logo": {"url": "https://r2.example/logo.png", "key": "logo/logo.png"}},
        },
    )
    return wb


def _gen(client, wb, candidate_type):
    return client.post(f"/api/v2/workbench/{wb}/candidates/{candidate_type}/generate")


# 1
def test_generate_affiche_stores_poster_key(client):
    wb = _make_workbench(client)
    r = _gen(client, wb, "affiche")
    assert r.status_code == 200
    cand = r.json()["poster_candidates"]["affiche"]
    assert cand["poster_key"].startswith("p2_")
    assert cand["status"] == "ready"
    assert cand["generated_at"]
    assert cand["template_id"] == "email_campaign_composite_v1"
    assert cand["contract_review_summary"]["callout_count"] == 3


# 2
def test_generate_fiche_stores_poster_key(client):
    wb = _make_workbench(client)
    r = _gen(client, wb, "fiche")
    assert r.status_code == 200
    cand = r.json()["poster_candidates"]["fiche"]
    assert cand["poster_key"].startswith("p2_")
    assert cand["status"] == "ready"
    assert cand["template_id"] == "template_product_sheet_v1"


# 3
def test_fiche_accepts_primary_and_secondary_images(client):
    wb = _make_workbench(client, two_images=True)
    r = _gen(client, wb, "fiche")
    assert r.status_code == 200
    poster_key = r.json()["poster_candidates"]["fiche"]["poster_key"]
    record = client.get(f"/api/v2/posters/{poster_key}").json()
    snap = record["request_snapshot"]
    assert snap["product_image"]["url"] == "https://r2.example/p1.png"
    assert snap["product_secondary_image"]["url"] == "https://r2.example/p2.png"


def test_fiche_single_image_has_no_secondary(client):
    wb = _make_workbench(client, two_images=False)
    r = _gen(client, wb, "fiche")
    assert r.status_code == 200
    poster_key = r.json()["poster_candidates"]["fiche"]["poster_key"]
    record = client.get(f"/api/v2/posters/{poster_key}").json()
    assert record["request_snapshot"].get("product_secondary_image") is None


# 4
def test_candidate_poster_key_loadable_via_poster_record(client):
    wb = _make_workbench(client)
    poster_key = _gen(client, wb, "affiche").json()["poster_candidates"]["affiche"]["poster_key"]
    rec = client.get(f"/api/v2/posters/{poster_key}")
    assert rec.status_code == 200
    assert rec.json()["poster_key"] == poster_key


# 5 / 6
def test_select_affiche_and_fiche(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    _gen(client, wb, "fiche")
    r1 = client.patch(f"/api/v2/workbench/{wb}/selected-visual", json={"selected_email_body_visual": "affiche"})
    assert r1.status_code == 200
    assert r1.json()["selected_email_body_visual"] == "affiche"
    r2 = client.patch(f"/api/v2/workbench/{wb}/selected-visual", json={"selected_email_body_visual": "fiche"})
    assert r2.status_code == 200
    assert r2.json()["selected_email_body_visual"] == "fiche"


# 7
def test_cannot_select_unready_candidate(client):
    wb = _make_workbench(client)
    # no candidate generated yet
    r = client.patch(f"/api/v2/workbench/{wb}/selected-visual", json={"selected_email_body_visual": "affiche"})
    assert r.status_code == 422
    assert r.json()["detail"] == "candidate_not_ready"


# 8
def test_selecting_replaces_previous_selection(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    _gen(client, wb, "fiche")
    client.patch(f"/api/v2/workbench/{wb}/selected-visual", json={"selected_email_body_visual": "affiche"})
    client.patch(f"/api/v2/workbench/{wb}/selected-visual", json={"selected_email_body_visual": "fiche"})
    got = client.get(f"/api/v2/workbench/{wb}").json()
    assert got["selected_email_body_visual"] == "fiche"


# 9
def test_regenerating_selected_candidate_clears_selection(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    client.patch(f"/api/v2/workbench/{wb}/selected-visual", json={"selected_email_body_visual": "affiche"})
    assert client.get(f"/api/v2/workbench/{wb}").json()["selected_email_body_visual"] == "affiche"
    r = _gen(client, wb, "affiche")  # regenerate the selected candidate
    assert r.status_code == 200
    assert r.json()["selected_email_body_visual"] is None


# 10
def test_regenerating_unselected_candidate_keeps_selection(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    _gen(client, wb, "fiche")
    client.patch(f"/api/v2/workbench/{wb}/selected-visual", json={"selected_email_body_visual": "affiche"})
    r = _gen(client, wb, "fiche")  # regenerate the NON-selected candidate
    assert r.status_code == 200
    assert r.json()["selected_email_body_visual"] == "affiche"


# 11
def test_get_workbench_returns_candidates_and_selection(client):
    wb = _make_workbench(client)
    _gen(client, wb, "affiche")
    _gen(client, wb, "fiche")
    client.patch(f"/api/v2/workbench/{wb}/selected-visual", json={"selected_email_body_visual": "fiche"})
    body = client.get(f"/api/v2/workbench/{wb}").json()
    assert set(body["poster_candidates"].keys()) == {"affiche", "fiche"}
    assert body["poster_candidates"]["affiche"]["status"] == "ready"
    assert body["poster_candidates"]["fiche"]["status"] == "ready"
    assert body["selected_email_body_visual"] == "fiche"


# 14
def test_190c_is_ordinary_param_no_thermostat_also_generates(client):
    # product with a thermostat 190°C row generates fine...
    wb1 = _make_workbench(client, with_thermostat=True)
    assert _gen(client, wb1, "affiche").status_code == 200
    # ...and a product with NO thermostat row generates equally (190°C is not a platform rule)
    wb2 = _make_workbench(client, with_thermostat=False)
    assert _gen(client, wb2, "fiche").status_code == 200


def test_generate_requires_product_image(client):
    wb = client.post("/api/v2/workbench", json={}).json()["workbench_key"]  # no assets
    r = _gen(client, wb, "affiche")
    assert r.status_code == 422
    assert r.json()["detail"] == "product_image_required"


def test_invalid_candidate_type_rejected(client):
    wb = _make_workbench(client)
    r = client.post(f"/api/v2/workbench/{wb}/candidates/banner/generate")
    assert r.status_code == 422
    assert r.json()["detail"] == "invalid_candidate_type"


def test_generate_unknown_workbench_404(client):
    r = client.post("/api/v2/workbench/wb_missing/candidates/affiche/generate")
    assert r.status_code == 404
