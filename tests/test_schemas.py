import pytest
from fastapi import HTTPException

from app.schemas import (
    GeneratePosterRequest,
    GeneratePosterResponse,
    PosterImage,
    PromptBundle,
    PromptSlotConfig,
    R2PresignPutResponse,
)
from app.services.glibatree import _assert_assets_use_ref_only


def _base_poster_payload() -> dict:
    return {
        "brand_name": "Brand",
        "agent_name": "Agent",
        "scenario_image": "https://cdn.example.com/scenario.png",
        "product_name": "Product",
        "features": ["F1", "F2", "F3"],
        "title": "Headline",
        "series_description": "Series",
        "subtitle": "Tagline",
    }


def test_prompt_bundle_coerces_legacy_inputs() -> None:
    bundle = PromptBundle.model_validate(
        {
            "scenario": "  cinematic lighting  ",
            "product": {
                "preset": "hero-white-bg",
                "positive": "Floating bottle on white",
                "negative": "no blur",
                "aspect": "4:5",
            },
            "gallery": {
                "prompt": "Flat lay",
            },
        }
    )

    assert isinstance(bundle.scenario, PromptSlotConfig)
    assert bundle.scenario.aspect == "1:1"
    assert bundle.scenario.prompt == "cinematic lighting"
    assert bundle.product.preset == "hero-white-bg"
    assert bundle.product.negative_prompt == "no blur"
    assert bundle.gallery.aspect == "4:3"
    assert bundle.gallery.prompt == "Flat lay"


def test_generate_poster_response_accepts_prompt_bundle_dict() -> None:
    response = GeneratePosterResponse(
        layout_preview="data:image/png;base64,preview",
        prompt="make poster",
        email_body="hello",
        poster_image=PosterImage(
            filename="poster.png",
            media_type="image/png",
            width=1024,
            height=1024,
        ),
        prompt_bundle={
            "scenario": {
                "preset": "scenario-closeup",
                "prompt": "Bright lighting",
                "negative_prompt": "no crowds",
                "aspect": "1:1",
            },
        },
    )

    assert isinstance(response.prompt_bundle, PromptBundle)
    assert response.prompt_bundle.scenario.preset == "scenario-closeup"
    assert response.prompt_bundle.scenario.prompt == "Bright lighting"
    # Missing slots fall back to defaults
    assert response.prompt_bundle.product.aspect == "4:5"
    assert response.prompt_bundle.product.prompt == ""
    assert response.results == []
    assert response.poster_url is None


def test_generate_poster_request_aliases_prompts_field() -> None:
    payload = {
        "poster": _base_poster_payload(),
        "prompts": {
            "scenario": {"prompt": "Moody", "aspect": "1:1"},
            "product": {"prompt": "Floating", "aspect": "4:5"},
            "gallery": {"prompt": "Angles", "aspect": "4:3"},
        },
    }

    request = GeneratePosterRequest.model_validate(payload)

    assert request.prompt_bundle.scenario.prompt == "Moody"
    assert request.prompt_bundle.product.aspect == "4:5"
    assert request.prompt_bundle.gallery.aspect == "4:3"


def test_asset_validator_accepts_bare_keys(monkeypatch) -> None:
    monkeypatch.setenv("R2_BUCKET", "ai-service")
    payload = {
        "brand_name": "Brand",
        "scenario_image": {"url": "posters/demo.png"},
    }

    _assert_assets_use_ref_only(payload)

    assert payload["scenario_image"]["url"] == "r2://ai-service/posters/demo.png"
    assert payload["scenario_image"]["key"] == "posters/demo.png"


def test_asset_validator_rejects_base64_payload() -> None:
    payload = {
        "brand_name": "Brand",
        "scenario_image": {
            "url": "data:image/png;base64,AAAABBBB",
        },
    }

    with pytest.raises(HTTPException) as exc:
        _assert_assets_use_ref_only(payload)

    assert exc.value.status_code == 422
    assert "base64" in str(exc.value.detail).lower()


def test_asset_validator_rejects_plain_text_reference(monkeypatch) -> None:
    monkeypatch.delenv("R2_BUCKET", raising=False)
    monkeypatch.delenv("S3_BUCKET", raising=False)
    payload = {
        "brand_name": "Brand",
        "scenario_image": {
            "url": "现代开放式厨房背景图",
        },
    }

    with pytest.raises(HTTPException) as exc:
        _assert_assets_use_ref_only(payload)

    assert exc.value.status_code == 422


def test_presign_response_populates_headers() -> None:
    response = R2PresignPutResponse(
        key="brand/logo.png",
        put_url="https://r2.example.com/upload",
        get_url="https://cdn.example.com/brand/logo.png",
        r2_url="r2://bucket/brand/logo.png",
        public_url=None,
        headers={"Content-Type": "image/png"},
    )

    assert response.headers["Content-Type"] == "image/png"
    # legacy alias syncing still works
    assert response.get_url == "https://cdn.example.com/brand/logo.png"
