import pytest

from app.schemas import PromptBundle, PromptSlotConfig


@pytest.mark.parametrize(
    "payload, expected_prompt",
    [
        ("  明亮厨房场景  ", "明亮厨房场景"),
        ({"prompt": "  产品主图  "}, "产品主图"),
        ({"positive": "  小图预设  "}, "小图预设"),
    ],
)
def test_prompt_slot_config_accepts_strings(payload, expected_prompt):
    slot = PromptSlotConfig.model_validate(payload)
    assert slot.prompt == expected_prompt
    assert slot.preset is None


def test_prompt_bundle_accepts_mixed_payloads():
    bundle = PromptBundle.model_validate(
        {
            "scenario": " 场景描述 ",
            "product": {"preset": "hero-white", "prompt": "  产品描述  "},
            "gallery": {
                "positive": "灰度小图",
                "negative": "反向词",
                "aspect_ratio": "4:3",
            },
        }
    )

    assert bundle.scenario.prompt == "场景描述"
    assert bundle.product.preset == "hero-white"
    assert bundle.product.prompt == "产品描述"
    assert bundle.gallery.prompt == "灰度小图"
    assert bundle.gallery.negative_prompt == "反向词"
    assert bundle.gallery.aspect == "4:3"
