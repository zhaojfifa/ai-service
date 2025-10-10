from __future__ import annotations

import base64
import json
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

try:
    from app.schemas import PosterGalleryItem, PosterInput
    from app.services.glibatree import (
        TemplateResources,
        generate_poster_asset,
        prepare_poster_assets,
    )
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
    prepare_poster_assets = None  # type: ignore[assignment]
    TemplateResources = None  # type: ignore[assignment]
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
        prompt_text, prompt_details, _ = build_glibatree_prompt(self.poster)
        self.assertIn("厨匠ChefCraft", prompt_text)
        self.assertIn("CHEFCRAFT", prompt_text.upper())
        self.assertIn("功能点1", prompt_text)
        self.assertIsInstance(prompt_details, dict)

    def test_compose_marketing_email_lists_features(self) -> None:
        poster_image_filename = "poster.png"
        email = compose_marketing_email(self.poster, poster_image_filename)
        for feature in self.poster.features:
            with self.subTest(feature=feature):
                self.assertIn(feature, email)
        self.assertIn(poster_image_filename, email)

    def test_preview_mentions_ai_generation_when_prompt_modes(self) -> None:
        update = {
            "scenario_mode": "prompt",
            "scenario_prompt": "开放式厨房柔和背光",
            "product_mode": "prompt",
            "product_prompt": "银灰色蒸烤一体机 45° 正面", 
            "gallery_items": [
                PosterGalleryItem(mode="prompt", prompt="小图 1 描述", caption="系列 1"),
                PosterGalleryItem(mode="prompt", prompt="小图 2 描述", caption="系列 2"),
                PosterGalleryItem(mode="prompt", prompt="小图 3 描述", caption="系列 3"),
            ],
        }
        try:
            poster = self.poster.model_copy(update=update)  # type: ignore[attr-defined]
        except AttributeError:
            data = self.poster.dict()
            data.update(
                {
                    "scenario_mode": "prompt",
                    "scenario_prompt": "开放式厨房柔和背光",
                    "product_mode": "prompt",
                    "product_prompt": "银灰色蒸烤一体机 45° 正面",
                    "gallery_items": [
                        {"mode": "prompt", "prompt": "小图 1 描述", "caption": "系列 1"},
                        {"mode": "prompt", "prompt": "小图 2 描述", "caption": "系列 2"},
                        {"mode": "prompt", "prompt": "小图 3 描述", "caption": "系列 3"},
                    ],
                }
            )
            poster = PosterInput(**data)  # type: ignore[arg-type]

        preview = render_layout_preview(poster)
        self.assertIn("AI 生成", preview)

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
        prompt_text, prompt_details, prompt_bundle = build_glibatree_prompt(poster)
        result = generate_poster_asset(
            poster,
            prompt_text,
            preview,
            prompt_bundle=prompt_bundle,
            prompt_details=prompt_details,
        )
        asset = result.poster

        if not asset.data_url:
            self.skipTest("Poster asset delivered via remote URL; base64 fallback disabled")

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

    @unittest.skipIf(DEPENDENCY_ERROR is not None, f"Missing dependency: {DEPENDENCY_ERROR}")
    def test_prepare_poster_assets_respects_template_materials(self) -> None:
        if prepare_poster_assets is None or TemplateResources is None or Image is None:  # pragma: no cover - safety
            self.skipTest("Required helpers are unavailable")

        template_image = Image.new("RGBA", (16, 16), (255, 255, 255, 255))
        spec = {
            "id": "custom",
            "materials": {
                "scenario": {"type": "image", "allowsPrompt": False},
                "product": {"type": "image", "allowsPrompt": True},
                "gallery": {"type": "image", "allowsPrompt": False, "count": 2},
            },
            "gallery": {"items": [{}, {}]},
        }

        template = TemplateResources(
            id="custom",
            spec=spec,
            template=template_image,
            mask_background=template_image,
            mask_scene=None,
        )

        gallery_items = [
            PosterGalleryItem(mode="prompt", prompt="AI 小图 1", caption="系列 1"),
            PosterGalleryItem(mode="upload", asset=make_data_url((32, 32, 32)), caption="系列 2"),
            PosterGalleryItem(mode="prompt", prompt="AI 小图 3", caption="系列 3"),
        ]

        update = {
            "scenario_mode": "prompt",
            "scenario_prompt": "需要生成的厨房背景",
            "product_mode": "prompt",
            "product_prompt": "不锈钢蒸烤箱 45° 角度",
            "gallery_items": gallery_items,
        }

        try:
            poster = self.poster.model_copy(update=update)  # type: ignore[attr-defined]
        except AttributeError:
            data = self.poster.dict()
            data.update(update)
            poster = PosterInput(**data)  # type: ignore[arg-type]

        with patch("app.services.glibatree._load_template_resources", return_value=template):
            prepared = prepare_poster_assets(poster)

        self.assertEqual(prepared.scenario_mode, "upload")
        self.assertEqual(prepared.product_mode, "prompt")
        self.assertEqual(len(prepared.gallery_items), 2)
        for item in prepared.gallery_items:
            self.assertNotEqual(item.mode, "prompt")

    def test_prepare_poster_assets_forces_prompt_when_upload_disabled(self) -> None:
        if prepare_poster_assets is None or TemplateResources is None or Image is None:  # pragma: no cover - safety
            self.skipTest("Required helpers are unavailable")

        template_image = Image.new("RGBA", (16, 16), (255, 255, 255, 255))
        spec = {
            "id": "text-only",
            "materials": {
                "scenario": {"type": "text"},
                "product": {"type": "image", "allowsPrompt": True},
                "gallery": {
                    "type": "image",
                    "allowsUpload": False,
                    "allowsPrompt": True,
                    "count": 2,
                },
            },
            "gallery": {"items": [{}, {}]},
        }

        template = TemplateResources(
            id="text-only",
            spec=spec,
            template=template_image,
            mask_background=template_image,
            mask_scene=None,
        )

        gallery_items = [
            PosterGalleryItem(mode="upload", asset=make_data_url((120, 120, 120)), caption="系列 A"),
            PosterGalleryItem(mode="prompt", prompt="AI 小图", caption="系列 B"),
        ]

        update = {
            "scenario_mode": "upload",
            "scenario_asset": make_data_url((0, 0, 0)),
            "product_mode": "prompt",
            "gallery_items": gallery_items,
        }

        try:
            poster = self.poster.model_copy(update=update)  # type: ignore[attr-defined]
        except AttributeError:
            data = self.poster.dict()
            data.update(update)
            poster = PosterInput(**data)  # type: ignore[arg-type]

        with patch("app.services.glibatree._load_template_resources", return_value=template):
            prepared = prepare_poster_assets(poster)

        self.assertEqual(prepared.scenario_mode, "prompt")
        self.assertIsNone(prepared.scenario_asset)
        self.assertTrue(all(item.mode == "prompt" for item in prepared.gallery_items))
        for item in prepared.gallery_items:
            self.assertIsNone(item.asset)

    def test_template_material_flags_accept_string_values(self) -> None:
        if prepare_poster_assets is None or TemplateResources is None or Image is None:  # pragma: no cover - safety
            self.skipTest("Required helpers are unavailable")

        template_image = Image.new("RGBA", (16, 16), (255, 255, 255, 255))
        spec = {
            "id": "string-flags",
            "materials": {
                "scenario": {"type": "image", "allowsUpload": "false", "allowsPrompt": "YES"},
                "product": {"type": "image", "allowsPrompt": "no"},
                "gallery": {
                    "type": "image",
                    "allowsUpload": "0",
                    "allowsPrompt": "1",
                    "count": "3",
                },
            },
            "gallery": {"items": [{}, {}, {}]},
        }

        template = TemplateResources(
            id="string-flags",
            spec=spec,
            template=template_image,
            mask_background=template_image,
            mask_scene=None,
        )

        gallery_items = [
            PosterGalleryItem(mode="upload", asset=make_data_url((10, 20, 30)), caption="图 1"),
            PosterGalleryItem(mode="prompt", prompt="需要生成的图 2", caption="图 2"),
            PosterGalleryItem(mode="upload", asset=make_data_url((40, 50, 60)), caption="图 3"),
            PosterGalleryItem(mode="prompt", prompt="需要生成的图 4", caption="图 4"),
        ]

        update = {
            "scenario_mode": "upload",
            "scenario_asset": make_data_url((120, 120, 120)),
            "scenario_prompt": "明亮的厨房场景",
            "product_mode": "prompt",
            "product_prompt": "磨砂金属蒸烤箱",
            "gallery_items": gallery_items,
        }

        try:
            poster = self.poster.model_copy(update=update)  # type: ignore[attr-defined]
        except AttributeError:
            data = self.poster.dict()
            data.update(update)
            poster = PosterInput(**data)  # type: ignore[arg-type]

        with patch("app.services.glibatree._load_template_resources", return_value=template):
            prepared = prepare_poster_assets(poster)

        self.assertEqual(prepared.scenario_mode, "prompt")
        self.assertIsNone(prepared.scenario_asset)
        self.assertEqual(prepared.product_mode, "upload")
        self.assertEqual(len(prepared.gallery_items), 3)
        for item in prepared.gallery_items:
            self.assertEqual(item.mode, "prompt")
            self.assertIsNone(item.asset)


if __name__ == "__main__":
    unittest.main()
