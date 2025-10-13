from __future__ import annotations

import textwrap

from typing import Any

from app.schemas import PosterInput

PROMPT_SLOT_LABELS = {
    "scenario": "场景背景",
    "product": "核心产品",
    "gallery": "底部系列小图",
}


def _normalise_prompt_config(config: Any) -> dict[str, Any] | None:
    """Normalise legacy prompt payloads into a consistent dictionary."""

    if config is None:
        return None

    if hasattr(config, "model_dump"):
        config = config.model_dump(exclude_none=True)
    elif hasattr(config, "dict"):
        config = config.dict(exclude_none=True)

    if isinstance(config, str):
        text = config.strip()
        if not text:
            return None
        return {
            "preset": None,
            "positive": text,
            "negative": None,
            "aspect": None,
        }

    if isinstance(config, dict):
        preset = (config.get("preset") or "").strip()
        positive = (
            config.get("positive")
            or config.get("prompt")
            or config.get("text")
            or ""
        ).strip()
        negative = (
            config.get("negative")
            or config.get("negative_prompt")
            or ""
        ).strip()
        aspect = (config.get("aspect") or config.get("aspect_ratio") or "").strip()

        if not any([preset, positive, negative, aspect]):
            return None

        return {
            "preset": preset or None,
            "positive": positive or None,
            "negative": negative or None,
            "aspect": aspect or None,
        }

    text = str(config).strip()
    if not text:
        return None
    return {
        "preset": None,
        "positive": text,
        "negative": None,
        "aspect": None,
    }


def render_layout_preview(poster: PosterInput) -> str:
    """Return a textual preview summarising the required layout structure."""

    logo_line = (
        f"已上传品牌 Logo（{poster.brand_name}）"
        if poster.brand_logo
        else poster.brand_name
    )
    has_scenario_asset = bool(poster.scenario_asset or getattr(poster, "scenario_key", None))
    scenario_line = (
        f"已上传场景图（描述：{poster.scenario_image}）"
        if has_scenario_asset
        else poster.scenario_image
    )
    if getattr(poster, "scenario_mode", "upload") == "prompt":
        scenario_line = f"{scenario_line}（AI 生成）"
    has_product_asset = bool(poster.product_asset or getattr(poster, "product_key", None))
    product_line = (
        f"已上传 45° 渲染图（{poster.product_name}）"
        if has_product_asset
        else poster.product_name
    )
    if getattr(poster, "product_mode", "upload") == "prompt":
        product_line = f"{product_line}（AI 生成）"
    gallery_count = sum(1 for item in poster.gallery_items if item.asset or getattr(item, "key", None))
    gallery_line = (
        f"已上传 {gallery_count} 张底部产品小图，配文：{poster.series_description}"
        if gallery_count
        else poster.series_description
    )
    prompt_gallery = any(getattr(item, "mode", "upload") == "prompt" for item in poster.gallery_items)
    if prompt_gallery:
        gallery_line = f"{gallery_line}（部分由 AI 生成）"

    features_preview = "\n".join(
        f"    - 功能点{i + 1}: {feature}" for i, feature in enumerate(poster.features)
    )

    preview = f"""
    顶部横条
      · 品牌 Logo（左上）：{logo_line}
      · 品牌代理名 / 分销名（右上）：{poster.agent_name}

    模板锁版
      · 当前模板：{poster.template_id}

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


def build_glibatree_prompt(
    poster: PosterInput, prompts: dict[str, Any] | None = None
) -> tuple[str, dict[str, str], dict[str, Any]]:
    """Generate the prompt forwarded to Glibatree along with slot summaries."""

    has_scenario_asset = bool(
        poster.scenario_asset or getattr(poster, "scenario_key", None)
    )
    has_product_asset = bool(
        poster.product_asset or getattr(poster, "product_key", None)
    )
    gallery_count = sum(
        1 for item in poster.gallery_items if item.asset or getattr(item, "key", None)
    )

    features = "\n".join(
        f"- 功能点{i}: {feature}"
        for i, feature in enumerate(poster.features, start=1)
    )

    reference_assets: list[str] = []
    if poster.brand_logo:
        reference_assets.append("- 参考素材：品牌 Logo 已上传，请置于顶部横条左侧并保持清晰度。")
    if has_scenario_asset:
        reference_assets.append("- 参考素材：应用场景图已上传，用于左侧 40% 区域的背景演绎。")
    if has_product_asset:
        reference_assets.append(
            "- 参考素材：主产品 45° 渲染图已上传，请保留金属 / 塑料质感与光影。"
        )
    if gallery_count:
        reference_assets.append(
            f"- 参考素材：底部产品小图共 {gallery_count} 张，需转为灰度横向排列。"
        )

    references_block = "\n".join(reference_assets)
    reference_section = f"\n    {references_block}" if references_block else ""

    prompt_details: dict[str, str] = {}
    prompt_bundle: dict[str, Any] = {}
    if prompts:
        for slot, config in prompts.items():
            normalised = _normalise_prompt_config(config)
            if not normalised:
                continue

            preset = normalised.get("preset") or ""
            positive = normalised.get("positive") or ""
            negative = normalised.get("negative") or ""
            aspect = normalised.get("aspect") or ""

            lines = []
            if preset:
                lines.append(f"Preset: {preset}")
            if aspect:
                lines.append(f"Aspect: {aspect}")
            if positive:
                lines.append(f"Positive: {positive}")
            if negative:
                lines.append(f"Negative: {negative}")
            if lines:
                prompt_details[slot] = "\n".join(lines)
            prompt_bundle[slot] = normalised

    prompt = f"""
    You are an art director. You will receive a locked poster frame and a binary mask. Fill ONLY the transparent region of the mask. Do not modify or cover any existing pixels (logos, typography, callouts, product edges). Absolutely no new text or logos. No extra UI. Keep composition minimal and premium.

    风格基调：现代简洁（Swiss Minimal），软质棚拍光线，银灰背景，控制红色饱和度不过度抢眼。
    产品类别：{poster.product_name}
    品牌：{poster.brand_name}，代理：{poster.agent_name}
    背景方向：左暗右亮，突出主产品的金属与塑料质感。
    功能提示：
    {features}
    底部系列说明：{poster.series_description}
    副标题：{poster.subtitle}
    模板：{poster.template_id}
    注意：仅在 mask 透明区域内补足背景氛围与光影，不得新增文字或移动既有元素。{reference_section}
    """
    prompt = textwrap.dedent(prompt).strip()

    if prompt_details:
        sections = []
        for slot, summary in prompt_details.items():
            label = PROMPT_SLOT_LABELS.get(slot, slot)
            sections.append(f"{label}指引:\n{summary}")
        prompt = f"{prompt}\n\n{chr(10).join(sections)}"

    return prompt, prompt_details, prompt_bundle


def compose_marketing_email(poster: PosterInput, poster_filename: str) -> str:
    """Create a marketing email body tailored for the target client."""

    feature_lines = "\n".join(f"· {feature}" for feature in poster.features)

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

