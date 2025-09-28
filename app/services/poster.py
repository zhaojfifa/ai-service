# app/services/poster.py
from __future__ import annotations

import textwrap
from typing import Tuple, Optional

from app.schemas import PosterInput

# 可选：只有在你确实需要用到 generate_poster_with_openai 时才会用到该导入
try:
    from app.services.openai_image import generate_image_with_openai  # 可选
except Exception:
    generate_image_with_openai = None  # 避免导入失败导致应用无法启动


def render_layout_preview(poster: PosterInput) -> str:
    """基于输入素材生成版式结构的文本预览。"""
    # 更智能：如果提供了素材文件则提示“已上传…”，否则展示文本占位
    logo_line = (
        f"已上传品牌 Logo（{poster.brand_name}）" if getattr(poster, "brand_logo", None) else poster.brand_name
    )
    scenario_line = (
        f"已上传场景图（描述：{poster.scenario_image}）"
        if getattr(poster, "scenario_asset", None)
        else (poster.scenario_image or "（未提供）")
    )
    product_line = (
        f"已上传 45° 渲染图（{poster.product_name}）"
        if getattr(poster, "product_asset", None)
        else (poster.product_name or "（未提供）")
    )
    if getattr(poster, "gallery_assets", None):
        gallery_line = f"已上传 {len(poster.gallery_assets)} 张底部产品小图，配文：{poster.series_description or '（未提供）'}"
    else:
        gallery_line = poster.series_description or "（未提供）"

    features_preview = "\n".join(
        f"    - 功能点{i + 1}: {feature}" for i, feature in enumerate(poster.features or [])
    )

    preview = f"""
    顶部横条
      · 品牌 Logo（左上）：{logo_line}
      · 代理 / 分销（右上）：{getattr(poster, 'agent_name', '')}

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

    主色建议：黑（功能）、红（标题/副标题）、灰/银（金属质感）
    背景：浅灰或白色，整体保持现代、简洁与留白感。
    """
    return textwrap.dedent(preview).strip()


def build_openai_prompt(poster: PosterInput) -> str:
    """生成给 OpenAI 图片模型的提示词（Prompt）。"""
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


# 兼容旧代码：若其他模块仍从 poster 导入 build_glibatree_prompt，不再报 ImportError
def build_glibatree_prompt(poster: PosterInput) -> str:
    return build_openai_prompt(poster)


def compose_marketing_email(poster: PosterInput, poster_filename: str) -> str:
    """生成营销邮件正文（纯文本）。"""
    features = poster.features or []
    feature_lines = "\n".join(f"• {f}" for f in features) if features else "（详见海报标注）"
    agent = getattr(poster, "agent_name", None)
    agent_tail = f" · {agent}" if agent else ""

    email = f"""尊敬的客户，

您好！感谢持续关注 {poster.brand_name} 厨房解决方案。我们最新推出的 {poster.product_name} 已上线，随附海报供您推广使用。
主题「{poster.title}」，副标题「{poster.subtitle}」，功能亮点如下：
{feature_lines}

欢迎分发至您的渠道，如需定制或更多资料，我们随时支持。

营销海报文件：{poster_filename}

—— {poster.brand_name} 市场团队{agent_tail}
"""
    return textwrap.dedent(email).strip()


# 可选的辅助：如需在服务层直接用 OpenAI 生成图片文件，可使用该包装函数
def generate_poster_with_openai(
    poster: PosterInput,
    openai_api_key: str,
    openai_base_url: Optional[str] = None,
    size: str = "1024x1024",
) -> Tuple[str, str, str]:
    """
    返回：(layout_preview, prompt, png_path)
    仅当仓库存在 app/services/openai_image.py 且已实现 generate_image_with_openai 时可用。
    """
    if generate_image_with_openai is None:
        raise RuntimeError("generate_image_with_openai 未可用：缺少 app.services.openai_image 或导入失败。")

    preview = render_layout_preview(poster)
    prompt = build_openai_prompt(poster)
    png_path = generate_image_with_openai(
        prompt=prompt,
        api_key=openai_api_key,
        base_url=openai_base_url,
        size=size,
    )
    return preview, prompt, png_path
