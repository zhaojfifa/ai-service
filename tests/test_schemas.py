from app.schemas import GeneratePosterRequest, GeneratePosterResponse, PosterImage, PromptBundle, PromptSlotConfig


def _base_request_payload() -> dict:
    return {
        "template_id": "template_dual",
        "brand_logo": {"key": "logo-key"},
        "scenario": {"key": "scenario-key"},
        "product": {"key": "product-key"},
        "gallery": [
            {"asset": {"key": "g1"}},
            {"asset": {"key": "g2"}},
            {"asset": {"key": "g3"}},
            {"asset": {"key": "g4"}},
        ],
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


def test_generate_poster_request_aliases_prompts_field() -> None:
    payload = _base_request_payload()
    payload["prompts"] = {
        "scenario": {"prompt": "Moody", "aspect": "1:1"},
        "product": {"prompt": "Floating", "aspect": "4:5"},
        "gallery": {"prompt": "Angles", "aspect": "4:3"},
    }

    request = GeneratePosterRequest.model_validate(payload)

    assert request.prompt_bundle.scenario.prompt == "Moody"
    assert request.prompt_bundle.product.aspect == "4:5"
    assert request.prompt_bundle.gallery.aspect == "4:3"
