from __future__ import annotations

import unittest

from app.schemas import PosterInput
from app.services.poster import (
    build_glibatree_prompt,
    compose_marketing_email,
    render_layout_preview,
)


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


if __name__ == "__main__":
    unittest.main()
