from app.schemas import (
    GeneratePosterResponse,
    PosterImage,
    PromptBundle,
)


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
                "positive": "bright lighting",
                "negative": None,
                "aspect": "1:1",
            },
            "product": None,
        },
    )

    assert response.prompt_bundle is not None
    assert (
        response.prompt_bundle.scenario
        == "bright lighting | Preset: scenario-closeup | Aspect: 1:1"
    )
    # Pydantic should coerce null entries to ``None`` when slot is missing.
    assert response.prompt_bundle.product is None


def test_generate_poster_response_model_validate_normalises_bundle() -> None:
    payload = {
        "layout_preview": "data:image/png;base64,preview",
        "prompt": "make poster",
        "email_body": "hello",
        "poster_image": {
            "filename": "poster.png",
            "media_type": "image/png",
            "width": 1024,
            "height": 1024,
        },
        "prompt_bundle": {
            "scenario": {
                "preset": "scenario-closeup",
                "positive": "sunny",
                "negative": None,
                "aspect": "1:1",
            }
        },
    }

    response = GeneratePosterResponse.model_validate(payload)

    assert isinstance(response.prompt_bundle, PromptBundle)
    assert response.prompt_bundle is not None
    assert (
        response.prompt_bundle.scenario
        == "sunny | Preset: scenario-closeup | Aspect: 1:1"
    )


def test_prompt_bundle_accepts_plain_strings() -> None:
    bundle = PromptBundle.model_validate({
        "scenario": "  moody lighting   ",
        "product": None,
        "gallery": "",
    })

    assert bundle.scenario == "moody lighting"
    assert bundle.product is None
    assert bundle.gallery is None
