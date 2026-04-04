from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import DEFAULT_CORS_ORIGINS, app
from app.services.poster2.contracts import RenderDebugArtifacts, RenderManifest


class _FakePoster2Pipeline:
    async def run(self, spec, template=None) -> RenderManifest:
        requested_bottom_mode = spec.bottom_mode or "title_gallery_split"
        title_band_rendered = requested_bottom_mode != "gallery_only"
        gallery_strip_rendered = requested_bottom_mode != "text_only_expanded"
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
            ),
            structure_complete=True,
            incomplete_structure=False,
            deliverable=True,
            structure_evidence_source="renderer_derived",
            structure_evidence_complete=True,
            missing_mandatory_regions=[],
            missing_required_slots=[],
            region_render_status={"header_region": {"rendered": True}},
            slot_binding_status={"missing_required_slots": []},
            template_behavior={
                "behavior_modes": {
                    "bottom_mode": requested_bottom_mode,
                    "bottom_layout_mode": requested_bottom_mode,
                    "gallery_mode": spec.gallery_mode or "strip_local_visible_only",
                }
            },
            geometry_evidence={"region_bounds": {"bottom_region": {"x": 96, "y": 728, "w": 832, "h": 232}}},
            hero_contract_review={
                "hero_mode": "scenario_cover_product_contain",
                "requested_product_source": spec.product_image.url,
                "rendered_product_source": spec.product_image.url,
            },
            product_contract_review={
                "product_annotation_mode": "none",
                "requested_product_source": spec.product_image.url,
                "rendered_product_source": spec.product_image.url,
            },
            header_contract_review={
                "header_mode": "identity_left_agent_right",
                "requested_brand_text": spec.brand_name,
                "sanitized_brand_text": spec.brand_name,
                "rendered_brand_excerpt": spec.brand_name,
            },
            feature_contract_review={
                "feature_mode": "count_driven_callout_stack",
                "requested_feature_items": list(spec.features),
                "sanitized_feature_items": list(spec.features),
                "rendered_feature_items": list(spec.features),
            },
            bottom_contract_review={
                "requested_bottom_mode": requested_bottom_mode,
                "effective_bottom_mode": requested_bottom_mode,
                "bottom_mode": requested_bottom_mode,
                "bottom_layout_mode": requested_bottom_mode,
                "bottom_mode_override_reason": (
                    "requested_matches_template_default"
                    if requested_bottom_mode == "title_gallery_split"
                    else "request_override_applied"
                ),
                "gallery_mode": spec.gallery_mode or "strip_local_visible_only",
                "title_band_region": {"rendered": title_band_rendered},
                "gallery_strip_region": {"rendered": gallery_strip_rendered},
            },
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
            ),
            fallback_reason_code="puppeteer_browser_launch_failed",
            fallback_reason_detail="BrowserType.launch: target closed",
            degraded=True,
            degraded_reason="puppeteer_browser_launch_failed",
            structure_complete=True,
            incomplete_structure=False,
            deliverable=True,
            structure_evidence_source="renderer_derived",
            structure_evidence_complete=True,
            missing_mandatory_regions=[],
            missing_required_slots=[],
            region_render_status={"header_region": {"rendered": True}},
            slot_binding_status={"missing_required_slots": []},
            template_behavior={
                "behavior_modes": {
                    "bottom_mode": spec.bottom_mode or "title_gallery_split",
                    "gallery_mode": spec.gallery_mode or "strip_local_visible_only",
                }
            },
            geometry_evidence={"region_bounds": {"bottom_region": {"x": 96, "y": 728, "w": 832, "h": 232}}},
            hero_contract_review={
                "hero_mode": "scenario_cover_product_contain",
                "requested_product_source": spec.product_image.url,
                "rendered_product_source": spec.product_image.url,
            },
            product_contract_review={
                "product_annotation_mode": "none",
                "requested_product_source": spec.product_image.url,
                "rendered_product_source": spec.product_image.url,
            },
            header_contract_review={
                "header_mode": "identity_left_agent_right",
                "requested_brand_text": spec.brand_name,
                "sanitized_brand_text": spec.brand_name,
                "rendered_brand_excerpt": spec.brand_name,
            },
            feature_contract_review={
                "feature_mode": "count_driven_callout_stack",
                "requested_feature_items": list(spec.features),
                "sanitized_feature_items": list(spec.features),
                "rendered_feature_items": list(spec.features),
            },
            bottom_contract_review={
                "bottom_mode": spec.bottom_mode or "title_gallery_split",
                "gallery_mode": spec.gallery_mode or "strip_local_visible_only",
                "title_band_region": {"rendered": True},
                "gallery_strip_region": {"rendered": False},
            },
        )


class _BoomPoster2Pipeline:
    async def run(self, spec, template=None) -> RenderManifest:
        raise RuntimeError("simulated poster2 failure")


def test_generate_poster_v2_route_is_backward_compatible(monkeypatch):
    monkeypatch.setattr("app.main._get_poster2_pipeline", lambda: _FakePoster2Pipeline())
    monkeypatch.setattr("app.services.poster_records.POSTER_RECORD_DIR", Path("/tmp/poster2-test-records-1"))
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
    assert body["poster_key"].startswith("p2_")
    assert body["template_version"] == "2.1.0"
    assert body["template_contract_version"] == "poster2.template_dual_v2.v1"
    assert body["renderer_mode"] == "auto"
    assert body["render_engine_used"] == "pillow"
    assert body["foreground_renderer"] == "poster2.pillow_layout"
    assert body["background_renderer"] == "firefly-v3"
    assert body["debug_artifacts"]["product_material_layer_url"] == "https://example.com/product-material.png"
    assert body["debug_artifacts"]["renderer_metadata_url"] == "https://example.com/renderer-metadata.json"
    assert body["structure_complete"] is True
    assert body["incomplete_structure"] is False
    assert body["deliverable"] is True
    assert body["structure_evidence_source"] == "renderer_derived"
    assert body["structure_evidence_complete"] is True
    assert body["missing_required_slots"] == []
    assert body["template_behavior"]["behavior_modes"]["bottom_mode"] == "title_gallery_split"
    assert body["hero_contract_review"]["hero_mode"] == "scenario_cover_product_contain"
    assert body["product_contract_review"]["product_annotation_mode"] == "none"
    assert body["header_contract_review"]["header_mode"] == "identity_left_agent_right"
    assert body["feature_contract_review"]["feature_mode"] == "count_driven_callout_stack"
    assert body["bottom_contract_review"]["bottom_mode"] == "title_gallery_split"
    assert body["geometry_evidence"]["region_bounds"]["bottom_region"] == {"x": 96, "y": 728, "w": 832, "h": 232}

    record = client.get(f"/api/v2/posters/{body['poster_key']}")
    assert record.status_code == 200
    record_body = record.json()
    assert record_body["poster_key"] == body["poster_key"]
    assert record_body["render_result"]["final_hash"] == body["final_hash"]
    assert record_body["final_poster"]["url"] == "https://example.com/final.png"


def test_generate_poster_v2_accepts_explicit_puppeteer_for_pilot_template(monkeypatch):
    monkeypatch.setattr("app.main._get_poster2_pipeline", lambda: _FakePoster2Pipeline())
    monkeypatch.setattr("app.services.poster_records.POSTER_RECORD_DIR", Path("/tmp/poster2-test-records-2"))
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


def test_generate_poster_v2_accepts_bottom_contract_fields(monkeypatch):
    monkeypatch.setattr("app.main._get_poster2_pipeline", lambda: _FakePoster2Pipeline())
    monkeypatch.setattr("app.services.poster_records.POSTER_RECORD_DIR", Path("/tmp/poster2-test-records-3"))
    client = TestClient(app)

    response = client.post(
        "/api/v2/generate-poster",
        json={
            "brand_name": "厨厨房",
            "agent_name": "智能顾问",
            "title": "测试标题",
            "subtitle": "测试副标题",
            "features": ["特性A"],
            "product_image": {"url": "https://example.com/product.png"},
            "template_id": "template_dual_v2",
            "bottom_mode": "gallery_only",
            "gallery_mode": "supporting_packshots",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["template_behavior"]["behavior_modes"]["bottom_mode"] == "gallery_only"
    assert body["template_behavior"]["behavior_modes"]["bottom_layout_mode"] == "gallery_only"
    assert body["template_behavior"]["behavior_modes"]["gallery_mode"] == "supporting_packshots"
    assert body["bottom_contract_review"]["bottom_mode"] == "gallery_only"
    assert body["bottom_contract_review"]["requested_bottom_mode"] == "gallery_only"
    assert body["bottom_contract_review"]["effective_bottom_mode"] == "gallery_only"
    assert body["bottom_contract_review"]["bottom_layout_mode"] == "gallery_only"
    assert body["bottom_contract_review"]["bottom_mode_override_reason"] == "request_override_applied"
    assert body["bottom_contract_review"]["gallery_mode"] == "supporting_packshots"
    assert body["bottom_contract_review"]["title_band_region"]["rendered"] is False
    assert body["bottom_contract_review"]["gallery_strip_region"]["rendered"] is True


def test_generate_poster_v2_accepts_text_gallery_expanded_with_runtime_diagnostics(monkeypatch):
    monkeypatch.setattr("app.main._get_poster2_pipeline", lambda: _FakePoster2Pipeline())
    monkeypatch.setattr("app.services.poster_records.POSTER_RECORD_DIR", Path("/tmp/poster2-test-records-4"))
    client = TestClient(app)

    response = client.post(
        "/api/v2/generate-poster",
        json={
            "brand_name": "厨厨房",
            "agent_name": "智能顾问",
            "title": "测试标题",
            "subtitle": "测试副标题",
            "features": ["特性A"],
            "product_image": {"url": "https://example.com/product.png"},
            "template_id": "template_dual_v2",
            "bottom_mode": "text_gallery_expanded",
            "gallery_mode": "strip_local_visible_only",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["template_behavior"]["behavior_modes"]["bottom_mode"] == "text_gallery_expanded"
    assert body["template_behavior"]["behavior_modes"]["bottom_layout_mode"] == "text_gallery_expanded"
    assert body["bottom_contract_review"]["requested_bottom_mode"] == "text_gallery_expanded"
    assert body["bottom_contract_review"]["effective_bottom_mode"] == "text_gallery_expanded"
    assert body["bottom_contract_review"]["bottom_layout_mode"] == "text_gallery_expanded"
    assert body["bottom_contract_review"]["bottom_mode_override_reason"] == "request_override_applied"
    assert body["bottom_contract_review"]["title_band_region"]["rendered"] is True
    assert body["bottom_contract_review"]["gallery_strip_region"]["rendered"] is True


def test_generate_poster_v2_accepts_bottom_gallery_count_trace_fields(monkeypatch):
    monkeypatch.setattr("app.main._get_poster2_pipeline", lambda: _FakePoster2Pipeline())
    monkeypatch.setattr("app.services.poster_records.POSTER_RECORD_DIR", Path("/tmp/poster2-test-records-5"))
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
            "gallery_images": [{"url": "https://example.com/gallery-1.png"}],
            "gallery_input_count_raw": 2,
            "gallery_input_count_normalized": 1,
            "gallery_requested_count": 2,
            "gallery_autofill_applied": False,
            "template_id": "template_dual_v2",
        },
    )

    assert response.status_code == 200


def test_generate_poster_v2_accepts_three_gallery_items_with_edited_subtitle(monkeypatch):
    monkeypatch.setattr("app.main._get_poster2_pipeline", lambda: _FakePoster2Pipeline())
    monkeypatch.setattr("app.services.poster_records.POSTER_RECORD_DIR", Path("/tmp/poster2-test-records-6"))
    client = TestClient(app)

    response = client.post(
        "/api/v2/generate-poster",
        json={
            "brand_name": "厨厨房",
            "agent_name": "智能顾问",
            "title": "测试标题",
            "subtitle": "编辑后的底部支持文案",
            "features": ["特性A", "特性B"],
            "product_image": {"url": "https://example.com/product.png"},
            "gallery_images": [
                {"url": "https://example.com/g1.png"},
                {"url": "https://example.com/g2.png"},
                {"url": "https://example.com/g3.png"},
            ],
            "template_id": "template_dual_v2",
            "bottom_mode": "title_gallery_split",
            "gallery_mode": "strip_local_visible_only",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["template_behavior"]["behavior_modes"]["bottom_mode"] == "title_gallery_split"
    assert body["template_behavior"]["behavior_modes"]["gallery_mode"] == "strip_local_visible_only"


def test_generate_poster_v2_exposes_explicit_fallback_reason_fields(monkeypatch):
    monkeypatch.setattr("app.main._get_poster2_pipeline", lambda: _FakeDegradedPoster2Pipeline())
    monkeypatch.setattr("app.services.poster_records.POSTER_RECORD_DIR", Path("/tmp/poster2-test-records-7"))
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
    assert body["deliverable"] is True
    assert body["structure_evidence_complete"] is True


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


def test_default_cors_origins_include_pages_origin_and_current_render_host():
    assert "https://zhaojfifa.github.io" in DEFAULT_CORS_ORIGINS
    assert "https://ai-service-leob.onrender.com" in DEFAULT_CORS_ORIGINS


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


def test_email_preview_and_inline_send_are_generated_from_poster_record(monkeypatch):
    monkeypatch.setattr("app.main._get_poster2_pipeline", lambda: _FakePoster2Pipeline())
    monkeypatch.setattr("app.services.poster_records.POSTER_RECORD_DIR", Path("/tmp/poster2-test-records-8"))
    client = TestClient(app)

    generated = client.post(
        "/api/v2/generate-poster",
        json={
            "brand_name": "ChefCraft",
            "agent_name": "Growth Team",
            "title": "Kitchen Upgrade",
            "subtitle": "Smart cooking for everyday use",
            "features": ["A", "B"],
            "product_image": {"url": "https://example.com/product.png"},
            "template_id": "template_dual_v2",
        },
    )
    poster_key = generated.json()["poster_key"]

    preview = client.post("/api/v2/email/preview", json={"poster_key": poster_key})
    assert preview.status_code == 200
    preview_body = preview.json()
    assert preview_body["poster_key"] == poster_key
    assert preview_body["subject"] == "ChefCraft | Kitchen Upgrade"
    assert "https://example.com/final.png" in preview_body["html"]

    send = client.post(
        "/api/v2/email/send",
        json={
            "poster_key": poster_key,
            "recipient": "user@example.com",
        },
    )
    assert send.status_code == 200
    send_body = send.json()
    assert send_body["status"] == "preview_only"
    assert send_body["provider"] == "inline_only"

    record = client.get(f"/api/v2/posters/{poster_key}")
    record_body = record.json()
    assert record_body["email_draft"]["subject"] == "ChefCraft | Kitchen Upgrade"
    assert record_body["email_deliveries"][-1]["status"] == "preview_only"


def test_email_send_supports_resend_provider(monkeypatch):
    monkeypatch.setattr("app.main._get_poster2_pipeline", lambda: _FakePoster2Pipeline())
    monkeypatch.setattr("app.services.poster_records.POSTER_RECORD_DIR", Path("/tmp/poster2-test-records-9"))

    class _FakeProvider:
        name = "resend"

        def send(self, *, recipient, subject, preview_text, html, text):
            return type("Delivery", (), {
                "provider": "resend",
                "status": "sent",
                "provider_message_id": "msg_123",
                "error": None,
            })()

    monkeypatch.setattr("app.main.get_email_provider", lambda delivery_mode: _FakeProvider())
    client = TestClient(app)

    generated = client.post(
        "/api/v2/generate-poster",
        json={
            "brand_name": "ChefCraft",
            "agent_name": "Growth Team",
            "title": "Kitchen Upgrade",
            "subtitle": "Smart cooking for everyday use",
            "features": ["A", "B"],
            "product_image": {"url": "https://example.com/product.png"},
            "template_id": "template_dual_v2",
        },
    )
    poster_key = generated.json()["poster_key"]

    send = client.post(
        "/api/v2/email/send",
        json={
            "poster_key": poster_key,
            "recipient": "user@example.com",
            "delivery_mode": "resend",
            "subject": "Custom subject",
            "preview_text": "Custom preview",
            "text": "Custom text",
            "html": "<p>Custom html</p>",
        },
    )
    assert send.status_code == 200
    body = send.json()
    assert body["status"] == "sent"
    assert body["provider"] == "resend"
    assert body["provider_message_id"] == "msg_123"
