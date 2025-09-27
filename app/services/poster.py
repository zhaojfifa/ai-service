# app/services/poster.py
from __future__ import annotations

import textwrap
from typing import Tuple

from app.schemas import PosterInput
from app.services.openai_image import generate_image_with_openai


def render_layout_preview(poster: PosterInput) -> str:
    """返回一个基于输入素材的版式结构预览（纯文本）。"""
    features_preview = "\n".join(
        f"    - 功能点{i + 1}: {feature}" for i, feature in enumerate(poster.features)
    )

    gallery_line = (
        f"已上传 {len(poster.gallery_assets)} 张底部产品小图，配文：{poster.series_description}"
        if poster.gallery_assets
        else poster.series_description or "（未提供）"
    )

    preview = f"""
    顶部横条
      · 品牌 Logo（左上）：{poster.brand_name}
      · 代理 / 分销（右上）：{poster.agent_name}

    左侧区域（约 40% 宽）
      · 应用场景图：{poster.scenario_image}

    右侧区域（视觉中心）
      · 主产品 45° 渲染图：{poster.product_name}
      · 功能点标注：
    {features_preview}

    中部标题（大号粗体红字）
      · {poster.title}

    底部区域（三视图或系列说明）
      · {gallery_line}

    角落副标题 / 标语（大号粗体红字）
      · {poster.subtitle}

    主色建议：黑（功能）、红（标题 / 副标题）、灰 / 银（金属质感）
    背景：浅灰或白色，整体保持现代、简洁与留白感。
    """
    return textwrap.dedent(preview).strip()


def build_openai_prompt(poster: PosterInput) -> str:
    """生成给 OpenAI 图片模型的提示词（Prompt）。"""

    features = "\n".join(
        f"- 功能点{i + 1}: {feature}"
        for i, feature in enumerate(poster.features, start=1)
    )
    brand_title = (poster.brand_name or "").upper()

    prompt = f"""
现代简洁风格的厨房电器宣传海报，要求：
- 版式：左侧 40% 宽放应用场景图，右侧视觉中心展示「{poster.product_name}」的 45° 渲染图；
- 顶部横条：左上放 {poster.brand_name} 品牌 Logo，右上以大写字母展示 {brand_title}；
- 产品材质：突出金属 / 塑料质感，背景浅灰或白色；
- 功能标注：在产品周围用虚线 + 黑色小号字体标注 3–4 条功能点：
{features}
- 中部标题：使用大号粗体红字「{poster.title}」；
- 底部：横向排列灰度的三视图或系列产品小图，附文字「{poster.series_description}」；
- 角落副标题：左下或右下以大号粗体红字呈现「{poster.subtitle}」；
- 色彩基调：黑 / 红 / 银灰，整体对齐规整，留白充足；
- 输出：高分辨率、清晰、可印刷。
"""
    return textwrap.dedent(prompt).strip()


def generate_poster_with_openai(
    poster: PosterInput,
    openai_api_key: str,
    openai_base_url: str | None = None,
    size: str = "1024x1024",
) -> Tuple[str, str, str]:
    """
    使用 OpenAI 生成海报图片，返回 (preview, prompt, png_path)
    """
    preview = render_layout_preview(poster)
    prompt = build_openai_prompt(poster)
    png_path = generate_image_with_openai(
        prompt=prompt,
        api_key=openai_api_key,
        base_url=openai_base_url,
        size=size,
    )
    return preview, prompt, png_path


def compose_marketing_email(poster: PosterInput, poster_filename: str) -> str:
    """生成营销邮件正文（纯文本），适合直接发送。"""
    brand = poster.brand_name or ""
    product = poster.product_name or ""
    subtitle = poster.subtitle or ""
    to_email = poster.email or ""
    features = poster.features or []
    feature_lines = "\n".join(f"• {f}" for f in features) if features else "（详见海报标注）"

    email = f'''收件人：{to_email}
主题：{brand} {product} 市场推广海报

尊敬的客户，

您好！感谢持续关注 {brand} 厨房解决方案。我们最新推出的 {product} 已经上线，特此奉上海报供您推广使用。
海报以“{subtitle}”为主题，在现代简洁的版式中突出以下功能亮点：
{feature_lines}

欢迎将本次营销物料分发至您的渠道。若需定制化内容或更多产品资料，我们的团队将随时为您跟进。

营销海报文件：{poster_filename}

期待与您的下一次合作，祝商祺！

—— {brand} 市场团队
'''
    return textwrap.dedent(email).strip()
