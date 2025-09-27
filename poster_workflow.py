"""Marketing poster workflow for kitchen appliance campaign.

This module structures a three-step workflow:
1. Render the poster input layout preview.
2. Generate a prompt for the Glibatree Art Designer.
3. Prepare a marketing email with the generated poster reference.

The workflow is designed for demonstration purposes and does not perform
real image generation or email sending. Instead, it produces structured
text outputs that can be used with external services.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import argparse
import json
import textwrap


@dataclass
class PosterInput:
    """Container for the required poster inputs."""

    brand_name: str
    agent_name: str
    scenario_image: str
    product_name: str
    features: list[str]
    title: str
    series_description: str
    subtitle: str
    email: str

    def validate(self) -> None:
        if len(self.features) < 3:
            raise ValueError("功能点数量需至少为 3 条")
        if len(self.features) > 4:
            raise ValueError("功能点数量最多为 4 条")


class MarketingPosterWorkflow:
    """Coordinates the three-step poster generation workflow."""

    def __init__(self, poster_input: PosterInput, output_dir: Path | None = None):
        poster_input.validate()
        self.poster_input = poster_input
        self.output_dir = Path(output_dir or "output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1 -----------------------------------------------------------------
    def render_input_layout(self) -> str:
        """Build a textual preview of the input layout."""

        features_preview = "\n".join(
            f"    - 功能点{i + 1}: {feature}"
            for i, feature in enumerate(self.poster_input.features)
        )

        preview = f"""
        顶部横条
          · 品牌 Logo（左上）：{self.poster_input.brand_name}
          · 代理 / 分销（右上）：{self.poster_input.agent_name}

        左侧区域（约 40% 宽）
          · 应用场景图：{self.poster_input.scenario_image}

        右侧区域（视觉中心）
          · 主产品 45° 渲染图：{self.poster_input.product_name}
          · 功能点标注：
        {features_preview}

        中部标题（大号粗体红字）
          · {self.poster_input.title}

        底部区域（三视图或系列说明）
          · {self.poster_input.series_description}

        角落副标题 / 标语（大号粗体红字）
          · {self.poster_input.subtitle}

        主色建议：黑（功能）、红（标题 / 副标题）、灰 / 银（金属质感）
        背景：浅灰或白色，整体保持现代、简洁与留白感。
        """
        return textwrap.dedent(preview).strip()

    # Step 2 -----------------------------------------------------------------
    def build_art_designer_prompt(self) -> str:
        """Generate a prompt suitable for the Glibatree Art Designer."""

        features = "\n".join(
            f"- 功能点{i + 1}: {feature}"
            for i, feature in enumerate(self.poster_input.features, start=1)
        )

        prompt = f"""
        使用 "Glibatree Art Designer" 绘制现代简洁风格的厨电宣传海报。
        关键要求：
        - 版式：左侧 40% 宽度放置应用场景图，右侧视觉中心展示 {self.poster_input.product_name} 的 45° 渲染图。
        - 顶部横条：左上角嵌入品牌 {self.poster_input.brand_name} Logo，右上角标注代理 {self.poster_input.agent_name}。
        - 产品材质：突出金属与塑料质感，背景为浅灰或白色。
        - 功能标注：在产品周围添加 3–4 条功能提示，使用虚线连接，黑色小号字体。
        {features}
        - 标题：中心位置使用大号粗体红字写 "{self.poster_input.title}"。
        - 底部：横向排列灰度三视图或系列产品缩略图，文字说明 "{self.poster_input.series_description}"。
        - 副标题：左下角或右下角以大号粗体红字呈现 "{self.poster_input.subtitle}"。
        - 色彩基调：黑 / 红 / 银灰，保持整洁对齐与留白。
        输出：高分辨率海报，适用于市场营销宣传。
        """
        return textwrap.dedent(prompt).strip()

    # Step 3 -----------------------------------------------------------------
    def compose_marketing_email(self, poster_filename: str | None = None) -> str:
        """Create a marketing email body tailored for the target client."""

        product = self.poster_input.product_name
        brand = self.poster_input.brand_name
        subtitle = self.poster_input.subtitle
        feature_lines = "\n".join(
            f"· {feature}" for feature in self.poster_input.features
        )

        attachment_note = (
            f"营销海报文件：{poster_filename}" if poster_filename else "营销海报文件已随附"
        )

        email = f"""
        收件人：{self.poster_input.email}
        主题：{brand} {product} 市场推广海报

        尊敬的客户，

        您好！感谢您持续关注 {brand} 厨房解决方案。我们最新推出的 {product} 已经上线，特此奉上宣传海报供您推广使用。海报以 "{subtitle}" 为主题，在现代简洁的版式中突出了以下核心优势：
        {feature_lines}

        欢迎将本次营销物料分发至您的渠道。若需定制化内容或更多产品资料，我们的团队将随时为您跟进。

        {attachment_note}

        期待与您的下一次合作，祝商祺！

        —— {self.poster_input.agent_name} 市场团队
        """
        return textwrap.dedent(email).strip()

    # Utility ----------------------------------------------------------------
    def save_output(self, filename: str, content: str) -> Path:
        path = self.output_dir / filename
        path.write_text(content, encoding="utf-8")
        return path

    def run(self) -> dict[str, Path]:
        preview = self.render_input_layout()
        prompt = self.build_art_designer_prompt()
        preview_path = self.save_output("poster_input_preview.txt", preview)
        prompt_path = self.save_output("glibatree_prompt.txt", prompt)
        email = self.compose_marketing_email(poster_filename=prompt_path.name)
        email_path = self.save_output("marketing_email.txt", email)
        return {
            "preview": preview_path,
            "prompt": prompt_path,
            "email": email_path,
        }


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate marketing poster assets")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to a JSON file describing the poster input."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory where generated text outputs will be saved."
    )
    return parser.parse_args(argv)


def load_poster_input(config_path: Path | None) -> PosterInput:
    if config_path is None:
        return PosterInput(
            brand_name="厨匠ChefCraft",
            agent_name="味觉星球营销中心",
            scenario_image="现代开放式厨房中智能蒸烤一体机的使用场景",
            product_name="ChefCraft 智能蒸烤大师",
            features=[
                "一键蒸烤联动，精准锁鲜",
                "360° 智能热风循环，均匀受热",
                "高温自清洁腔体，省心维护",
                "Wi-Fi 远程操控，云端菜谱推送",
            ],
            title="焕新厨房效率，打造大厨级美味",
            series_description="标准款 / 高配款 / 嵌入式款 产品三视图",
            subtitle="智能蒸烤 · 家宴轻松掌控",
            email="client@example.com",
        )

    data = json.loads(config_path.read_text(encoding="utf-8"))
    return PosterInput(
        brand_name=data["brand_name"],
        agent_name=data["agent_name"],
        scenario_image=data["scenario_image"],
        product_name=data["product_name"],
        features=list(data["features"]),
        title=data["title"],
        series_description=data["series_description"],
        subtitle=data["subtitle"],
        email=data["email"],
    )


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    poster_input = load_poster_input(args.config)
    workflow = MarketingPosterWorkflow(poster_input, output_dir=args.output)
    paths = workflow.run()

    print("海报素材输入页预览：", paths["preview"].resolve())
    print("Glibatree 提示词：", paths["prompt"].resolve())
    print("营销邮件文案：", paths["email"].resolve())


if __name__ == "__main__":
    main()
