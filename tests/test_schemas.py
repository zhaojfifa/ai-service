from app.schemas import GeneratePosterResponse, PosterImage


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
    assert response.prompt_bundle.scenario is not None
    assert response.prompt_bundle.scenario.preset == "scenario-closeup"
    # Pydantic should coerce null entries to None PromptSlotConfig instances.
    assert response.prompt_bundle.product is None
