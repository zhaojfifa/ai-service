# app/services/poster.py
from __future__ import annotations

import textwrap
from typing import Tuple

from app.schemas import PosterInput
from app.services.openai_image import generate_image_with_openai  # 如有需要

def render_layout_preview(poster: PosterInput) -> str:
    features_preview = "\n".join(
        f"    - 功能点{i + 1}: {feature}" for i, feature in enumerate(poster.features or [])
    )
    gallery_line = (
        f"已上传 {len(poster.gallery_assets)} 张底部产品小图，配文：{poster.series_description}"
        if getattr(poster, "gallery_assets", None)
        else (poster.series_description or "（未提供）")
    )
    preview = f"""
    顶部横条
      · 品牌 Logo（左上）：{poster.brand_name}
      · 代理 / 分销（右上）：{getattr(poster, 'agent_name', '')}

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

    主色建议：黑（功能）、红（标题/副标题）、灰/银（金属质感）
    背景：浅灰或白色，整体保持现代、简洁与留白感。
    """
    return textwrap.dedent(preview).strip()

def build_openai_prompt(poster: PosterInput) -> str:
    features = "\n".join(
        f"- 功能点{i + 1}: {f}" for i, f in enumerate(poster.features or [], start=1)
    )
    brand_title = (poster.brand_name or "").upper()
    prompt = f"""
现代简洁风的厨房电器宣传海报：
- 版式：左侧 40% 放应用场景图，右侧视觉中心展示「{poster.product_name}」45° 渲染图；
- 顶部横条：左上放 {poster.brand_name} Logo，右上展示 {brand_title}；
- 材质：金属/塑料质感清晰，背景浅灰或白；
- 功能标注（虚线+小号黑体）：
{features}
- 中部标题（红色粗体）：{poster.title}
- 底部灰度小图（3–4 张），说明「{poster.series_description}」；
- 角落副标题（红色粗体）：{poster.subtitle}
- 主色：黑/红/银灰；排版规整、留白充足；输出高分辨率。
"""
    return textwrap.dedent(prompt).strip()

# 如你仍有代码在别处 import build_glibatree_prompt，这里提供一个“桥接”同名函数，避免再次 ImportError：
def build_glibatree_prompt(poster: PosterInput) -> str:
    return build_openai_prompt(poster)

def compose_marketing_email(poster: PosterInput, poster_filename: str) -> str:
    features = poster.features or []
    feature_lines = "\n".join(f"• {f}" for f in features) if features else "（详见海报标注）"
    email = f"""尊敬的客户，

您好！感谢持续关注 {poster.brand_name} 厨房解决方案。我们最新推出的 {poster.product_name} 已上线，随附海报供您推广使用。
主题「{poster.title}」，副标题「{poster.subtitle}」，功能亮点如下：
{feature_lines}

欢迎分发至您的渠道，如需定制或更多资料，我们随时支持。

营销海报文件：{poster_filename}

—— {poster.brand_name} 市场团队
"""
    return textwrap.dedent(email).strip()

# 可选：如果你用到 OpenAI 生成并需要文件路径，可提供包装器
def generate_poster_with_openai(
    poster: PosterInput,
    openai_api_key: str,
    openai_base_url: str | None = None,
    size: str = "1024x1024",
) -> Tuple[str, str, str]:
    preview = render_layout_preview(poster)
    prompt = build_openai_prompt(poster)
    png_path = generate_image_with_openai(
        prompt=prompt, api_key=openai_api_key, base_url=openai_base_url, size=size
    )
    return preview, prompt, png_path
