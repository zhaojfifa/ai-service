from __future__ import annotations

import base64
import unittest
from io import BytesIO

from app.schemas import PosterInput
from app.services.glibatree import generate_poster_asset
from app.services.poster import (
    build_glibatree_prompt,
    compose_marketing_email,
    render_layout_preview,
)
from PIL import Image


def make_data_url(color: tuple[int, int, int]) -> str:
    image = Image.new("RGB", (120, 120), color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


class PosterServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.poster = PosterInput(
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
                "gallery_assets": [make_data_url((245, 220, 0))] * 3,
            }
        )
        poster = PosterInput(**payload)

        preview = render_layout_preview(poster)
        prompt = build_glibatree_prompt(poster)
        asset = generate_poster_asset(poster, prompt, preview)

        _header, encoded = asset.data_url.split(",", 1)
        image = Image.open(BytesIO(base64.b64decode(encoded))).convert("RGB")

        width, height = image.size
        banner_height = int(height * 0.15)
        logo_size = max(min(96, banner_height - 32), 48)
        left_width = int(width * 0.38)

        scenario_top = banner_height + 30
        scenario_bottom = height - 220
        product_left = 80 + left_width
        product_top = banner_height + 30
        product_bottom = height - 240
        series_top = height - 170
        gallery_top = series_top + 14
        gallery_bottom = series_top + 70
        gallery_left = 60
        gallery_right = width - 60
        gallery_count = 3
        spacing = 16
        slot_width = (gallery_right - gallery_left - spacing * (gallery_count - 1)) // gallery_count
        slot_height = gallery_bottom - gallery_top

        logo_center = (40 + logo_size // 2, 20 + logo_size // 2)
        scenario_center = (
            40 + left_width // 2,
            scenario_top + (scenario_bottom - scenario_top) // 2,
        )
        product_center = (
            product_left + (width - 60 - product_left) // 2,
            product_top + (product_bottom - product_top) // 2,
        )
        gallery_center = (
            gallery_left + slot_width // 2,
            gallery_top + slot_height // 2,
        )

        logo_pixel = image.getpixel(logo_center)
        scenario_pixel = image.getpixel(scenario_center)
        product_pixel = image.getpixel(product_center)
        gallery_pixel = image.getpixel(gallery_center)

        self.assertGreater(logo_pixel[0], logo_pixel[1])
        self.assertGreater(logo_pixel[0], logo_pixel[2])
        self.assertGreater(scenario_pixel[1], scenario_pixel[0])
        self.assertGreater(scenario_pixel[1], scenario_pixel[2])
        self.assertGreater(product_pixel[2], product_pixel[0])
        self.assertGreater(product_pixel[2], product_pixel[1])
        self.assertGreater(gallery_pixel[0], gallery_pixel[2])
        self.assertGreater(gallery_pixel[1], gallery_pixel[2])


if __name__ == "__main__":
    unittest.main()
