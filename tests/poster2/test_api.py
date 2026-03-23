from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.poster2.contracts import RenderDebugArtifacts, RenderManifest


class _FakePoster2Pipeline:
    async def run(self, spec, template=None) -> RenderManifest:
        return RenderManifest(
            trace_id="trace-123",
            template_id=spec.template_id,
            template_version="2.1.0",
            template_contract_version="poster2.template_dual_v2.v1",
            engine_version="2.0.0",
            renderer_mode=spec.renderer_mode,
            render_engine_used="pillow",
            foreground_renderer="poster2.pillow_layout",
            background_renderer="firefly-v3",
            poster_spec_hash="deadbeefdeadbeef",
            resolved_inputs={"title": spec.title},
            background_url="https://example.com/bg.png",
            background_prompt="clean studio",
            background_seed=42,
            background_model="firefly-v3",
            foreground_url="https://example.com/fg.png",
            foreground_hash="a" * 64,
            final_url="https://example.com/final.png",
            final_hash="b" * 64,
            timings_ms={"total_ms": 12},
            debug_artifacts=RenderDebugArtifacts(
                background_layer_url="https://example.com/bg.png",
                product_material_layer_url="https://example.com/product-material.png",
                foreground_layer_url="https://example.com/fg.png",
                final_composited_url="https://example.com/final.png",
                renderer_metadata_url="https://example.com/renderer-metadata.json",
                slot_structure_layer_url="https://example.com/slot-structure.png",
                content_layer_url="https://example.com/content-layer.png",
                text_layer_url="https://example.com/text-layer.png",
                structure_overlay_url="https://example.com/structure-overlay.png",
                slot_metadata_url="https://example.com/slot-metadata.json",
            ),
        )


class _FakeDegradedPoster2Pipeline:
    async def run(self, spec, template=None) -> RenderManifest:
        return RenderManifest(
            trace_id="trace-degraded",
            template_id=spec.template_id,
            template_version="2.1.0",
            template_contract_version="poster2.template_dual_v2.v1",
            engine_version="2.0.0",
            renderer_mode=spec.renderer_mode,
            render_engine_used="pillow",
            foreground_renderer="poster2.pillow_layout",
            background_renderer="firefly-v3",
            poster_spec_hash="deadbeefdeadbeef",
            resolved_inputs={"title": spec.title},
            background_url="https://example.com/bg.png",
            background_prompt="clean studio",
            background_seed=42,
            background_model="firefly-v3",
            foreground_url="https://example.com/fg.png",
            foreground_hash="a" * 64,
            final_url="https://example.com/final.png",
            final_hash="b" * 64,
            timings_ms={"total_ms": 12},
            debug_artifacts=RenderDebugArtifacts(
                background_layer_url="https://example.com/bg.png",
                product_material_layer_url="https://example.com/product-material.png",
                foreground_layer_url="https://example.com/fg.png",
                final_composited_url="https://example.com/final.png",
                renderer_metadata_url="https://example.com/renderer-metadata.json",
                slot_structure_layer_url="https://example.com/slot-structure.png",
                content_layer_url="https://example.com/content-layer.png",
                text_layer_url="https://example.com/text-layer.png",
                structure_overlay_url="https://example.com/structure-overlay.png",
                slot_metadata_url="https://example.com/slot-metadata.json",
            ),
            fallback_reason_code="puppeteer_browser_launch_failed",
            fallback_reason_detail="BrowserType.launch: target closed",
            degraded=True,
            degraded_reason="puppeteer_browser_launch_failed",
        )


class _BoomPoster2Pipeline:
    async def run(self, spec, template=None) -> RenderManifest:
        raise RuntimeError("simulated poster2 failure")


def test_generate_poster_v2_route_is_backward_compatible(monkeypatch):
    monkeypatch.setattr("app.main._get_poster2_pipeline", lambda: _FakePoster2Pipeline())
    client = TestClient(app)

    response = client.post(
        "/api/v2/generate-poster",
        json={
            "brand_name": "厨厨房",
            "agent_name": "智能顾问",
            "title": "测试标题",
            "subtitle": "测试副标题",
            "features": ["特性A", "特性B"],
            "product_image": {"url": "https://example.com/product.png"},
            "style": {"prompt": "warm kitchen", "seed": 42},
            "template_id": "template_dual_v2",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["final_url"] == "https://example.com/final.png"
    assert body["template_version"] == "2.1.0"
    assert body["template_contract_version"] == "poster2.template_dual_v2.v1"
    assert body["renderer_mode"] == "auto"
    assert body["render_engine_used"] == "pillow"
    assert body["foreground_renderer"] == "poster2.pillow_layout"
    assert body["background_renderer"] == "firefly-v3"
    assert body["debug_artifacts"]["product_material_layer_url"] == "https://example.com/product-material.png"
    assert body["debug_artifacts"]["renderer_metadata_url"] == "https://example.com/renderer-metadata.json"
    assert body["debug_artifacts"]["slot_structure_layer_url"] == "https://example.com/slot-structure.png"
    assert body["debug_artifacts"]["content_layer_url"] == "https://example.com/content-layer.png"
    assert body["debug_artifacts"]["text_layer_url"] == "https://example.com/text-layer.png"
    assert body["debug_artifacts"]["structure_overlay_url"] == "https://example.com/structure-overlay.png"
    assert body["debug_artifacts"]["slot_metadata_url"] == "https://example.com/slot-metadata.json"


def test_generate_poster_v2_accepts_explicit_puppeteer_for_pilot_template(monkeypatch):
    monkeypatch.setattr("app.main._get_poster2_pipeline", lambda: _FakePoster2Pipeline())
    client = TestClient(app)

    response = client.post(
        "/api/v2/generate-poster",
        json={
            "brand_name": "厨厨房",
            "agent_name": "智能顾问",
            "title": "测试标题",
            "subtitle": "测试副标题",
            "features": ["特性A", "特性B"],
            "product_image": {"url": "https://example.com/product.png"},
            "template_id": "template_dual_v2",
            "renderer_mode": "puppeteer",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["renderer_mode"] == "puppeteer"


def test_generate_poster_v2_exposes_explicit_fallback_reason_fields(monkeypatch):
    monkeypatch.setattr("app.main._get_poster2_pipeline", lambda: _FakeDegradedPoster2Pipeline())
    client = TestClient(app)

    response = client.post(
        "/api/v2/generate-poster",
        json={
            "brand_name": "厨厨房",
            "agent_name": "智能顾问",
            "title": "测试标题",
            "subtitle": "测试副标题",
            "features": ["特性A", "特性B"],
            "product_image": {"url": "https://example.com/product.png"},
            "template_id": "template_dual_v2",
            "renderer_mode": "puppeteer",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["render_engine_used"] == "pillow"
    assert body["degraded"] is True
    assert body["degraded_reason"] == "puppeteer_browser_launch_failed"
    assert body["fallback_reason_code"] == "puppeteer_browser_launch_failed"
    assert body["fallback_reason_detail"] == "BrowserType.launch: target closed"


def test_generate_poster_v2_rejects_puppeteer_for_non_pilot_template():
    client = TestClient(app)

    response = client.post(
        "/api/v2/generate-poster",
        json={
            "brand_name": "厨厨房",
            "agent_name": "智能顾问",
            "title": "测试标题",
            "subtitle": "测试副标题",
            "features": ["特性A", "特性B"],
            "product_image": {"url": "https://example.com/product.png"},
            "template_id": "template_focus_v1",
            "renderer_mode": "puppeteer",
        },
    )

    assert response.status_code == 422
    assert "template_dual_v2" in response.json()["detail"]


def test_generate_poster_v2_preflight_allows_content_type_and_x_request_id():
    client = TestClient(app)

    response = client.options(
        "/api/v2/generate-poster",
        headers={
            "Origin": "https://zhaojfifa.github.io",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-request-id",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-methods"]
    allow_headers = response.headers.get("access-control-allow-headers", "").lower()
    assert "content-type" in allow_headers
    assert "x-request-id" in allow_headers


def test_generate_poster_v2_error_response_keeps_cors_headers(monkeypatch):
    monkeypatch.setattr("app.main._get_poster2_pipeline", lambda: _BoomPoster2Pipeline())
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/api/v2/generate-poster",
        headers={"Origin": "https://zhaojfifa.github.io"},
        json={
            "brand_name": "厨厨房",
            "agent_name": "智能顾问",
            "title": "测试标题",
            "subtitle": "测试副标题",
            "features": ["特性A", "特性B"],
            "product_image": {"url": "https://example.com/product.png"},
            "template_id": "template_dual_v2",
            "renderer_mode": "pillow",
        },
    )

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == "https://zhaojfifa.github.io"
    assert response.json()["detail"]["error"] == "poster2_generation_failed"
