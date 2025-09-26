from __future__ import annotations

import textwrap

from app.schemas import PosterInput


def render_layout_preview(poster: PosterInput) -> str:
    """Return a textual preview summarising the required layout structure."""


    features_preview = "\n".join(
        f"    - 功能点{i + 1}: {feature}" for i, feature in enumerate(poster.features)
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

      · {poster.series_description}

    角落副标题 / 标语（大号粗体红字）
      · {poster.subtitle}

    主色建议：黑（功能）、红（标题 / 副标题）、灰 / 银（金属质感）
    背景：浅灰或白色，整体保持现代、简洁与留白感。
    """
    return textwrap.dedent(preview).strip()


def build_glibatree_prompt(poster: PosterInput) -> str:
    """Generate the prompt that will be forwarded to Glibatree Art Designer."""

    features = "\n".join(
        f"- 功能点{i + 1}: {feature}"
        for i, feature in enumerate(poster.features, start=1)
    )


    prompt = f"""
    使用 "Glibatree Art Designer" 绘制现代简洁风格的厨电宣传海报。
    关键要求：
    - 版式：左侧 40% 宽度放置应用场景图，右侧视觉中心展示 {poster.product_name} 的 45° 渲染图。
    - 顶部横条：左上角嵌入品牌 {poster.brand_name} Logo，右上角标注代理 {poster.agent_name}。
    - 产品材质：突出金属与塑料质感，背景为浅灰或白色。
    - 功能标注：在产品周围添加 3–4 条功能提示，使用虚线连接，黑色小号字体。
    {features}
    - 标题：中心位置使用大号粗体红字写 "{poster.title}"。
    - 底部：横向排列灰度三视图或系列产品缩略图，文字说明 "{poster.series_description}"。
    - 副标题：左下角或右下角以大号粗体红字呈现 "{poster.subtitle}"。

    - 色彩基调：黑 / 红 / 银灰，保持整洁对齐与留白。

    输出：高分辨率海报，适用于市场营销宣传。
    """
    return textwrap.dedent(prompt).strip()


def compose_marketing_email(poster: PosterInput, poster_filename: str) -> str:
    """Create a marketing email body tailored for the target client."""

    feature_lines = "\n".join(f"· {feature}" for feature in poster.features)

    email = f"""
    收件人：{poster.email}
    主题：{poster.brand_name} {poster.product_name} 市场推广海报

    尊敬的客户，

    您好！感谢您持续关注 {poster.brand_name} 厨房解决方案。我们最新推出的 {poster.product_name} 已经上线，特此奉上宣传海报供您推广使用。海报以 "{poster.subtitle}" 为主题，在现代简洁的版式中突出了以下核心优势：
    {feature_lines}

    欢迎将本次营销物料分发至您的渠道。若需定制化内容或更多产品资料，我们的团队将随时为您跟进。

    营销海报文件：{poster_filename}

    期待与您的下一次合作，祝商祺！

    —— {poster.agent_name} 市场团队
    """
    return textwrap.dedent(email).strip()

