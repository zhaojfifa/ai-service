from __future__ import annotations

import textwrap

from app.schemas import PosterInput


def render_layout_preview(poster: PosterInput) -> str:
    """返回一段可读性强的版式结构预览文本。"""

    logo_line = (
        f"已上传品牌 Logo（{poster.brand_name}）" if poster.brand_logo else poster.brand_name
    )
    scenario_line = (
        f"已上传场景图（描述：{poster.scenario_image}）"
        if poster.scenario_asset
        else poster.scenario_image
    )
    product_line = (
        f"已上传 45° 渲染图（{poster.product_name}）"
        if poster.product_asset
        else poster.product_name
    )
    gallery_line = (
        f"已上传 {len(poster.gallery_assets)} 张底部产品小图，配文：{poster.series_description}"
        if poster.gallery_assets
        else poster.series_description
    )

    features_preview = "\n".join(
        f"    - 功能点{i + 1}: {feature}" for i, feature in enumerate(poster.features or [])
    )

    preview = f"""
    顶部横条
      · 品牌 Logo（左上）：{logo_line}
      · 品牌代理名 / 分销名（右上）：{poster.agent_name}

    左侧区域（约 40% 宽）
      · 应用场景图：{scenario_line}

    右侧区域（视觉中心）
      · 主产品 45° 渲染图：{product_line}
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


def build_glibatree_prompt(poster: PosterInput) -> str:
    """生成发送给 Glibatree Art Designer 的提示词。"""

    features = "\n".join(
        f"- 功能点{i}: {feature}" for i, feature in enumerate(poster.features or [], start=1)
    )

    reference_assets: list[str] = []
    if poster.brand_logo:
        reference_assets.append("- 参考素材：品牌 Logo 已上传，请置于顶部横条左侧并保持清晰度。")
    if poster.scenario_asset:
        reference_assets.append("- 参考素材：应用场景图已上传，用于左侧 40% 区域的背景演绎。")
    if poster.product_asset:
        reference_assets.append("- 参考素材：主产品 45° 渲染图已上传，请保留金属 / 塑料质感与光影。")
    if poster.gallery_assets:
        reference_assets.append(
            f"- 参考素材：底部产品小图共 {len(poster.gallery_assets)} 张，需转为灰度横向排列。"
        )

    references_block = "\n".join(reference_assets)
    reference_section = f"\n    {references_block}" if references_block else ""

    agent_title = poster.agent_name.upper()

    prompt = f"""
    使用 "Glibatree Art Designer" 绘制现代简洁风格的厨电宣传海报。
    关键要求：
    - 版式：左侧 40% 宽度放置应用场景图，右侧视觉中心展示 {poster.product_name} 的 45° 渲染图。
    - 顶部横条：左上角嵌入品牌 {poster.brand_name} Logo，右上角用大写字母展示合作代理 {agent_title}。
    - 产品材质：突出金属与塑料质感，背景为浅灰或白色。
    - 功能标注：在产品周围添加 3–4 条功能提示，使用虚线连接，黑色小号字体。
    {features}
    - 标题：中心位置使用大号粗体红字写 "{poster.title}"。
    - 底部：横向排列灰度三视图或系列产品缩略图，文字说明 "{poster.series_description}"。
    - 副标题：左下角或右下角以大号粗体红字呈现 "{poster.subtitle}"。
    - 色彩基调：黑 / 红 / 银灰，保持整洁对齐与留白。{reference_section}
    输出：高分辨率海报，适用于市场营销宣传。
    """
    return textwrap.dedent(prompt).strip()


def compose_marketing_email(poster: PosterInput, poster_filename: str) -> str:
    """生成营销邮件正文。"""

    feature_lines = "\n".join(f"· {feature}" for feature in (poster.features or []))

    email = f"""
    尊敬的客户，

    您好！感谢您持续关注 {poster.brand_name} 厨房解决方案。由 {poster.agent_name} 代理的 {poster.product_name} 已经上线，特此奉上宣传海报供您推广使用。海报以 "{poster.subtitle}" 为主题，在现代简洁的版式中突出了以下核心优势：
    {feature_lines}

    欢迎将本次营销物料分发至您的渠道。若需定制化内容或更多产品资料，我们的团队将随时为您跟进。

    营销海报文件：{poster_filename}

    期待与您的下一次合作，祝商祺！

    —— {poster.brand_name} · {poster.agent_name}
    """
    return textwrap.dedent(email).strip()


# --- 兼容 main.py 的导入：为 OpenAI 路线提供同名函数 ---
def build_openai_prompt(poster: PosterInput) -> str:
    """与 build_glibatree_prompt 兼容的同名接口，避免 ImportError。"""
    return build_glibatree_prompt(poster)


# 显式导出，避免打包/裁剪导致的符号缺失
__all__ = [
    "render_layout_preview",
    "build_glibatree_prompt",
    "build_openai_prompt",
    "compose_marketing_email",
]
