from __future__ import annotations

import textwrap

from typing import Any, List, Tuple

from app.models import PosterSpec
from app.schemas import PosterInput, PromptSlotConfig

PROMPT_SLOT_LABELS = {
    "scenario": "场景背景",
    "product": "核心产品",
    "gallery": "底部系列小图",
}

EN_DEFAULT_TITLE = "Refresh your kitchen efficiency"
EN_DEFAULT_SUBTITLE = "Smart steam-roast • Chef-grade results at home"
EN_DEFAULT_FEATURES = [
    "One-tap steam & roast with precise flavor lock",
    "360° smart hot-air circulation for even heating",
    "High-temperature self-clean cavity",
    "Wi-Fi remote control with guided recipes",
]

ZH_DEFAULT_TITLE = "焕新你的厨房效率"
ZH_DEFAULT_SUBTITLE = "智能蒸烤·厨师级口感回家"
ZH_DEFAULT_FEATURES = [
    "一键蒸烤联动，精准锁鲜",
    "360° 热风均匀烘烤",
    "高温蒸汽自清洁腔体",
    "云端菜谱与远程操控",
]


def _normalise_prompt_config(config: Any) -> dict[str, Any] | None:
    """Normalise legacy prompt payloads into a consistent dictionary."""

    if config is None:
        return None

    if isinstance(config, PromptSlotConfig):
        return config.model_dump(exclude_none=True)

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
            "prompt": text,
            "negative_prompt": None,
            "aspect": None,
        }

    if isinstance(config, dict):
        preset = (config.get("preset") or "").strip()
        prompt_text = (
            config.get("prompt")
            or config.get("positive")
            or config.get("text")
            or ""
        ).strip()
        negative = (
            config.get("negative_prompt")
            or config.get("negative")
            or ""
        ).strip()
        aspect = (config.get("aspect") or config.get("aspect_ratio") or "").strip()

        if not any([preset, prompt_text, negative, aspect]):
            return None

        return {
            "preset": preset or None,
            "prompt": prompt_text or None,
            "negative_prompt": negative or None,
            "aspect": aspect or None,
        }

    text = str(config).strip()
    if not text:
        return None
    return {
        "preset": None,
        "prompt": text,
        "negative_prompt": None,
        "aspect": None,
    }


def _poster_model_copy(instance: PosterInput, **update: Any) -> PosterInput:
    if hasattr(instance, "model_copy"):
        return instance.model_copy(update=update, deep=True)  # type: ignore[attr-defined]
    data = instance.dict()
    data.update(update)
    return PosterInput(**data)


def _poster_spec_from_input(poster: PosterInput) -> PosterSpec:
    lang = getattr(poster, "lang", "en") or "en"
    spec = PosterSpec(
        lang=lang,
        title=getattr(poster, "title", None),
        subtitle=getattr(poster, "subtitle", None),
        features=list(getattr(poster, "features", []) or []),
        brand_name=getattr(poster, "brand_name", None),
    )
    defaults = {
        "default_title": EN_DEFAULT_TITLE,
        "default_subtitle": EN_DEFAULT_SUBTITLE,
        "default_features": EN_DEFAULT_FEATURES,
    }
    if spec.lang == "zh":
        defaults = {
            "default_title": ZH_DEFAULT_TITLE,
            "default_subtitle": ZH_DEFAULT_SUBTITLE,
            "default_features": ZH_DEFAULT_FEATURES,
        }
    return spec.ensure_defaults(**defaults)


def build_prompt(spec: PosterSpec, section: str, preset: str | None = None) -> str:
    lang = (spec.lang or "en").lower()
    features = [item for item in spec.features[:4] if item]
    brand = spec.brand_name or "ChefCraft"

    if lang == "en":
        copy_map = {
            "scenario": (
                "Modern kitchen counter-top scene, tight crop, soft directional lighting, muted neutrals,"
                " subtle depth."
            ),
            "product": (
                "Premium 45-degree catalog hero, stainless steel and glass texture, crisp highlights,"
                " refined reflections."
            ),
            "gallery": (
                "Lifestyle detail close-ups, shallow depth of field, consistent palette, supports hero story."
            ),
        }
        lang_line = "All typography must be in English with a clean sans-serif hierarchy."
        feature_line = (
            f"Feature highlights: {', '.join(features)}. Limit callouts to flat, monochrome badges."
            if features
            else "Limit callouts to at most four flat, monochrome badges."
        )
        brand_line = (
            f"Brand lock-up: place {brand} logo and name together in the upper-left corner, single occurrence."
        )
    else:
        copy_map = {
            "scenario": "现代厨房台面，柔和光影，色调克制，构图干净。",
            "product": "45° 产品主视图，金属与玻璃质感清晰，商拍光影。",
            "gallery": "生活化细节特写，浅景深，整体风格统一。",
        }
        lang_line = "文案使用中文，版式保持简洁分层。"
        feature_line = (
            f"功能亮点：{'、'.join(features)}，徽章扁平且不超过四个。" if features else "徽章不超过四个，保持扁平化。"
        )
        brand_line = f"品牌锁定：{brand} Logo 与品牌名置于左上角，仅出现一次。"

    base_copy = copy_map.get(section, copy_map.get("scenario", ""))

    sections: List[str] = [base_copy]
    if lang == "en":
        sections.append(f'Primary headline: "{spec.title}" (bold, single line).')
        sections.append(f'Secondary line: "{spec.subtitle}" (light weight).')
    else:
        sections.append(f'主标题："{spec.title}"，单行加粗。')
        sections.append(f'副标题："{spec.subtitle}"，轻量字体。')
    sections.append(feature_line)
    sections.append(brand_line)
    sections.append(lang_line)
    if preset:
        sections.append(f"Preset reference: {preset}.")

    return " ".join(section for section in sections if section)


def normalise_poster_copy(poster: PosterInput) -> Tuple[PosterInput, PosterSpec]:
    spec = _poster_spec_from_input(poster)
    updated = _poster_model_copy(
        poster,
        lang=spec.lang,
        title=spec.title,
        subtitle=spec.subtitle,
        features=spec.features,
    )
    return updated, spec


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
    """Generate the prompt forwarded to Vertex along with slot summaries."""

    spec = _poster_spec_from_input(poster)
    prompt_details: dict[str, str] = {}
    prompt_bundle: dict[str, Any] = {}

    def _build_slot(slot: str) -> dict[str, Any]:
        base_config = _normalise_prompt_config(prompts.get(slot)) if prompts else None
        preset = base_config.get("preset") if base_config else None
        base_prompt = build_prompt(spec, slot, preset)
        merged: dict[str, Any] = dict(base_config) if base_config else {}

        prompt_text = (merged.get("prompt") or merged.get("positive") or "").strip()
        if prompt_text:
            if spec.lang == "en" and "English" not in prompt_text:
                prompt_text = f"{prompt_text} All copy must remain in English."
        else:
            prompt_text = base_prompt

        merged["prompt"] = prompt_text
        cleaned = {k: v for k, v in merged.items() if v not in (None, "")}

        lines = []
        if cleaned.get("preset"):
            lines.append(f"Preset: {cleaned['preset']}")
        if cleaned.get("aspect"):
            lines.append(f"Aspect: {cleaned['aspect']}")
        lines.append(f"Prompt: {prompt_text}")
        if cleaned.get("negative_prompt"):
            lines.append(f"Negative: {cleaned['negative_prompt']}")

        prompt_details[slot] = "\n".join(lines)
        prompt_bundle[slot] = cleaned
        return cleaned

    scenario_cfg = _build_slot("scenario")
    product_cfg = _build_slot("product")
    gallery_cfg = _build_slot("gallery")

    brand = spec.brand_name or poster.brand_name
    if spec.lang == "en":
        feature_text = "; ".join(spec.features[:4])
        lang_line = "All copy and UI text must stay in English."
    else:
        feature_text = "、".join(spec.features[:4])
        lang_line = "所有文案保持中文表达。"

    prompt_body = textwrap.dedent(
        f"""
        Design a premium marketing poster for {brand}. Follow the locked layout template {poster.template_id} with clear hierarchy, tight crop, and minimal flat badges.
        Headline: "{spec.title}". Subtitle: "{spec.subtitle}". Feature bullets (max four): {feature_text}. Keep the brand lock-up (logo + name) in the upper-left and do not duplicate it elsewhere.
        Scenario guidance: {scenario_cfg.get('prompt')}
        Product hero guidance: {product_cfg.get('prompt')}
        Gallery guidance: {gallery_cfg.get('prompt')}
        Palette: soft, muted neutrals with stainless steel and glass materials rendered realistically. Maintain product color dominance, polished reflections, and consistent studio lighting. {lang_line}
        """
    ).strip()

    if prompt_details:
        sections = []
        for slot, summary in prompt_details.items():
            label = PROMPT_SLOT_LABELS.get(slot, slot)
            sections.append(f"{label} Guidance:\n{summary}")
        prompt_body = f"{prompt_body}\n\n{chr(10).join(sections)}"

    return prompt_body, prompt_details, prompt_bundle


def compose_marketing_email(poster: PosterInput, poster_filename: str) -> str:
    """Create a marketing email body tailored for the target client."""

    spec = _poster_spec_from_input(poster)
    features = spec.features[:4]

    if spec.lang == "en":
        feature_lines = "\n".join(f"• {item}" for item in features)
        email = f"""
        Hello,

        We're excited to share the latest marketing poster for {poster.product_name} from {poster.brand_name}. The layout leads with the headline "{spec.title}" and supporting line "{spec.subtitle}" to reinforce the product promise.

        Key highlights:
        {feature_lines}

        Download the poster here: {poster_filename}

        Let us know if you need localized copy, additional formats, or more campaign assets.

        Best regards,
        {poster.brand_name} — {poster.agent_name}
        """
        return textwrap.dedent(email).strip()

    feature_lines = "\n".join(f"· {feature}" for feature in features)
    email = f"""
    尊敬的客户，

    您好！感谢您持续关注 {poster.brand_name} 厨房解决方案。由 {poster.agent_name} 代理的 {poster.product_name} 已经上线，特此奉上宣传海报供您推广使用。海报以 "{spec.subtitle}" 为主题，在现代简洁的版式中突出了以下核心优势：
    {feature_lines}

    欢迎将本次营销物料分发至您的渠道。若需定制化内容或更多产品资料，我们的团队将随时为您跟进。

    营销海报文件：{poster_filename}

    期待与您的下一次合作，祝商祺！

    —— {poster.brand_name} · {poster.agent_name}
    """
    return textwrap.dedent(email).strip()

