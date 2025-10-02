from __future__ import annotations

import base64
import json
import unittest
from io import BytesIO
from pathlib import Path

try:
    from app.schemas import PosterInput
    from app.services.glibatree import generate_poster_asset
    from app.services.poster import (
        build_glibatree_prompt,
        compose_marketing_email,
        render_layout_preview,
    )
    from PIL import Image
except ModuleNotFoundError as exc:  # pragma: no cover - exercised via skip
    DEPENDENCY_ERROR = exc
    PosterInput = None  # type: ignore[assignment]
    generate_poster_asset = build_glibatree_prompt = compose_marketing_email = render_layout_preview = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment]
else:
    DEPENDENCY_ERROR = None


def make_data_url(color: tuple[int, int, int]) -> str:
    if Image is None:  # pragma: no cover - skip path
        raise RuntimeError("Pillow is required for this helper")
    image = Image.new("RGB", (120, 120), color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


@unittest.skipIf(DEPENDENCY_ERROR is not None, f"Missing dependency: {DEPENDENCY_ERROR}")
class PosterServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.poster = PosterInput(  # type: ignore[call-arg]
            brand_name="厨匠ChefCraft",
            agent_name="星辉渠道",
            scenario_image="开放式厨房中烤箱与早餐场景",
            product_name="ChefCraft 蒸烤大师",
            features=[
                "一键蒸烤联动",
                "360° 智能热风循环",
                "高温自清洁腔体",
            ],
            title="焕新厨房效率",
            series_description="标准款 / 高配款 / 嵌入式款",
            subtitle="智能蒸烤 · 家宴轻松掌控",
        )

    def test_render_layout_preview_contains_key_sections(self) -> None:
        preview = render_layout_preview(self.poster)
        self.assertIn("顶部横条", preview)
        self.assertIn("星辉渠道", preview)
        self.assertIn("ChefCraft 蒸烤大师", preview)
        self.assertIn("功能点标注", preview)

    def test_build_glibatree_prompt_mentions_brand_and_agent(self) -> None:
        prompt = build_glibatree_prompt(self.poster)
        self.assertIn("厨匠ChefCraft", prompt)
        self.assertIn("CHEFCRAFT", prompt.upper())
        self.assertIn("功能点1", prompt)

    def test_compose_marketing_email_lists_features(self) -> None:
        poster_image_filename = "poster.png"
        email = compose_marketing_email(self.poster, poster_image_filename)
        for feature in self.poster.features:
            with self.subTest(feature=feature):
                self.assertIn(feature, email)
        self.assertIn(poster_image_filename, email)

    def test_mock_poster_embeds_uploaded_assets(self) -> None:
        try:
            payload = self.poster.model_dump()
        except AttributeError:
            payload = self.poster.dict()
        payload.update(
            {
                "brand_logo": make_data_url((255, 0, 0)),
                "scenario_asset": make_data_url((0, 200, 0)),
                "product_asset": make_data_url((0, 0, 255)),
                "gallery_items": [
                    {"asset": make_data_url((245, 220, 0)), "caption": f"系列 {i+1}"}
                    for i in range(3)
                ],
            }
        )
        poster = PosterInput(**payload)  # type: ignore[arg-type]

        preview = render_layout_preview(poster)
        prompt = build_glibatree_prompt(poster)
        asset = generate_poster_asset(poster, prompt, preview)

        _header, encoded = asset.data_url.split(",", 1)
        image = Image.open(BytesIO(base64.b64decode(encoded))).convert("RGB")
        spec_path = Path("frontend/templates/template_dual_spec.json")
        spec = json.loads(spec_path.read_text(encoding="utf-8"))

        logo_slot = spec["slots"]["logo"]
        scenario_slot = spec["slots"]["scenario"]
        product_slot = spec["slots"]["product"]
        gallery_slot = spec["gallery"]["items"][0]

        def slot_center(slot: dict[str, int]) -> tuple[int, int]:
            return (
                slot["x"] + slot["width"] // 2,
                slot["y"] + slot["height"] // 2,
            )

        logo_pixel = image.getpixel(slot_center(logo_slot))
        scenario_pixel = image.getpixel(slot_center(scenario_slot))
        product_pixel = image.getpixel(slot_center(product_slot))
        gallery_pixel = image.getpixel(slot_center(gallery_slot))


        self.assertGreater(logo_pixel[0], logo_pixel[1])
        self.assertGreater(logo_pixel[0], logo_pixel[2])
        self.assertGreater(scenario_pixel[1], scenario_pixel[0])
        self.assertGreater(scenario_pixel[1], scenario_pixel[2])
        self.assertGreater(product_pixel[2], product_pixel[0])
        self.assertGreater(product_pixel[2], product_pixel[1])
        self.assertTrue(abs(gallery_pixel[0] - gallery_pixel[1]) <= 5)


if __name__ == "__main__":
    unittest.main()
