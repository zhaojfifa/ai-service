from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.poster2.contracts import RenderManifest


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
        )


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
