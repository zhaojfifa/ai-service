from __future__ import annotations

import base64
import json
import logging
from contextlib import ExitStack
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any, Tuple

import httpx
import requests
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError


from app.config import GlibatreeConfig, get_settings
from app.schemas import PosterImage, PosterInput


logger = logging.getLogger(__name__)

OPENAI_IMAGE_SIZE = "1024x1024"
TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "frontend" / "templates"
DEFAULT_TEMPLATE_ID = "template_dual"

BRAND_RED = (239, 76, 84)
INK_BLACK = (31, 41, 51)
SILVER = (244, 245, 247)
GUIDE_GREY = (203, 210, 217)


@dataclass
class TemplateResources:
    id: str
    spec: dict[str, Any]
    template: Image.Image
    mask_background: Image.Image
    mask_scene: Image.Image | None


@lru_cache(maxsize=8)
def _load_template_resources(template_id: str) -> TemplateResources:
    """Load template spec, locked frame and masks for the given template id."""

    candidate = TEMPLATE_ROOT / f"{template_id}_spec.json"
    if not candidate.exists():
        logger.warning("Template %s not found, falling back to %s", template_id, DEFAULT_TEMPLATE_ID)
        candidate = TEMPLATE_ROOT / f"{DEFAULT_TEMPLATE_ID}_spec.json"
        template_id = DEFAULT_TEMPLATE_ID

    with candidate.open("r", encoding="utf-8") as handle:
        spec: dict[str, Any] = json.load(handle)

    assets = spec.get("assets", {})
    template_path = TEMPLATE_ROOT / assets.get("template", "")
    mask_bg_path = TEMPLATE_ROOT / assets.get("mask_background", "")
    mask_scene_path = TEMPLATE_ROOT / assets.get("mask_scene", "")

    if not template_path.exists():
        raise FileNotFoundError(f"Template image missing: {template_path}")
    if not mask_bg_path.exists():
        raise FileNotFoundError(f"Template mask missing: {mask_bg_path}")

    template_image = Image.open(template_path).convert("RGBA")
    mask_background = Image.open(mask_bg_path).convert("RGBA")
    mask_scene = None
    if mask_scene_path.exists():
        mask_scene = Image.open(mask_scene_path).convert("RGBA")

    return TemplateResources(
        id=template_id,
        spec=spec,
        template=template_image,
        mask_background=mask_background,
        mask_scene=mask_scene,
    )


def _load_font(size: int, *, weight: str = "regular") -> ImageFont.ImageFont:
    """Attempt to load a sans-serif font while gracefully falling back to default."""

    font_candidates = [
        "SourceSansPro-Semibold.ttf" if weight != "regular" else "SourceSansPro-Regular.ttf",
        "NotoSansCJKsc-Bold.otf" if weight != "regular" else "NotoSansCJKsc-Regular.otf",
        "Arial.ttf" if weight == "regular" else "Arial Bold.ttf",
        "PingFang.ttc",
        "Microsoft YaHei.ttf",
    ]

    for candidate in font_candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except Exception:
            continue

    return ImageFont.load_default()


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: Tuple[int, int, int, int],
    font: ImageFont.ImageFont,
    fill: Tuple[int, int, int],
    *,
    line_spacing: int = 6,
    align: str = "left",
) -> None:
    """Render multiline text constrained within the provided box."""

    left, top, width, height = box
    right = left + width
    bottom = top + height
    y = top
    max_width = max(width, 10)

    for paragraph in filter(None, [segment.strip() for segment in text.splitlines()]):
        words = paragraph.split(" ")
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if draw.textlength(candidate, font=font) <= max_width:
                line = candidate
            else:
                if line:
                    _draw_line(draw, line, font, fill, left, right, y, align)
                    y += font.size + line_spacing
                    if y > bottom:
                        return
                line = word
        if line:
            _draw_line(draw, line, font, fill, left, right, y, align)
            y += font.size + line_spacing
            if y > bottom:
                return


def _draw_line(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    fill: Tuple[int, int, int],
    left: int,
    right: int,
    y: int,
    align: str,
) -> None:
    width = draw.textlength(text, font=font)
    if align == "center":
        x = left + (right - left - width) / 2
    elif align == "right":
        x = right - width
    else:
        x = left
    draw.text((int(x), int(y)), text, font=font, fill=fill)


def _slot_to_box(slot: dict[str, Any]) -> Tuple[int, int, int, int]:
    return (
        int(slot.get("x", 0)),
        int(slot.get("y", 0)),
        int(slot.get("width", 0)),
        int(slot.get("height", 0)),
    )


def _render_template_frame(
    poster: PosterInput,
    template: TemplateResources,
    *,
    fill_background: bool = False,
) -> Image.Image:
    """Render the locked template frame with all deterministic elements applied."""

    spec = template.spec
    size = spec.get("size", {})
    width = int(size.get("width", template.template.width))
    height = int(size.get("height", template.template.height))

    background_color = (*SILVER, 255) if fill_background else (244, 245, 247, 255)
    canvas = Image.new("RGBA", (width, height), background_color)
    canvas.alpha_composite(template.template.copy())

    draw = ImageDraw.Draw(canvas)

    font_title = _load_font(64, weight="bold")
    font_subtitle = _load_font(40, weight="bold")
    font_brand = _load_font(36, weight="semibold")
    font_agent = _load_font(30, weight="semibold")
    font_body = _load_font(28)
    font_feature = _load_font(26)
    font_caption = _load_font(22)

    slots = spec.get("slots", {})

    # Brand logo
    logo_slot = slots.get("logo")
    if logo_slot:
        left, top, width_box, height_box = _slot_to_box(logo_slot)
        logo_box = (left, top, left + width_box, top + height_box)
        logo_image = _load_image_from_data_url(poster.brand_logo)
        if logo_image:
            _paste_image(canvas, logo_image, logo_box, mode="contain")
        else:
            draw.rectangle(logo_box, outline=GUIDE_GREY, width=2)
            _draw_wrapped_text(
                draw,
                poster.brand_name,
                (left + 8, top + 4, width_box - 16, height_box - 8),
                font_body,
                INK_BLACK,
            )

    # Brand and agent text
    brand_slot = slots.get("brand_name")
    if brand_slot:
        left, top, width_box, height_box = _slot_to_box(brand_slot)
        _draw_wrapped_text(
            draw,
            poster.brand_name,
            (left, top, width_box, height_box),
            font_brand,
            INK_BLACK,
        )

    agent_slot = slots.get("agent_name")
    if agent_slot:
        left, top, width_box, height_box = _slot_to_box(agent_slot)
        _draw_wrapped_text(
            draw,
            poster.agent_name.upper(),
            (left, top, width_box, height_box),
            font_agent,
            INK_BLACK,
            align="right",
        )

    # Scenario image
    scenario_slot = slots.get("scenario")
    if scenario_slot:
        left, top, width_box, height_box = _slot_to_box(scenario_slot)
        scenario_box = (left, top, left + width_box, top + height_box)
        scenario_image = _load_image_from_data_url(poster.scenario_asset)
        if scenario_image:
            _paste_image(canvas, scenario_image, scenario_box, mode="cover")
        else:
            draw.rectangle(scenario_box, outline=GUIDE_GREY, width=2)
            _draw_wrapped_text(
                draw,
                poster.scenario_image,
                (left + 16, top + 16, width_box - 32, height_box - 32),
                font_feature,
                INK_BLACK,
            )

    # Product render
    product_slot = slots.get("product")
    if product_slot:
        left, top, width_box, height_box = _slot_to_box(product_slot)
        product_box = (left, top, left + width_box, top + height_box)
        product_image = _load_image_from_data_url(poster.product_asset)
        if product_image:
            _paste_image(canvas, product_image, product_box, mode="contain")
        else:
            draw.rectangle(product_box, outline=GUIDE_GREY, width=3)
            _draw_wrapped_text(
                draw,
                poster.product_name,
                (left + 24, top + 24, width_box - 48, height_box - 48),
                font_body,
                INK_BLACK,
                align="center",
            )

    # Title and subtitle
    title_slot = slots.get("title")
    if title_slot:
        left, top, width_box, height_box = _slot_to_box(title_slot)
        _draw_wrapped_text(
            draw,
            poster.title,
            (left, top, width_box, height_box),
            font_title,
            BRAND_RED,
            align="center",
        )

    subtitle_slot = slots.get("subtitle")
    if subtitle_slot:
        left, top, width_box, height_box = _slot_to_box(subtitle_slot)
        _draw_wrapped_text(
            draw,
            poster.subtitle,
            (left, top, width_box, height_box),
            font_subtitle,
            BRAND_RED,
            align="right",
        )

    # Feature callouts
    callouts = spec.get("feature_callouts", [])
    for index, callout in enumerate(callouts):
        if index >= len(poster.features):
            break
        label_slot = callout.get("label_box", {})
        left, top, width_box, height_box = _slot_to_box(label_slot)
        feature_text = f"{index + 1}. {poster.features[index]}"
        _draw_wrapped_text(
            draw,
            feature_text,
            (left, top, width_box, height_box),
            font_feature,
            INK_BLACK,
        )

    # Gallery thumbnails
    gallery = spec.get("gallery", {})
    gallery_items = gallery.get("items", [])
    for index, slot in enumerate(gallery_items):
        if index >= len(poster.gallery_items):
            break
        entry = poster.gallery_items[index]
        left, top, width_box, height_box = _slot_to_box(slot)
        box = (left, top, left + width_box, top + height_box)
        if entry.asset:
            asset_image = _load_image_from_data_url(entry.asset)
            if asset_image:
                grayscale = ImageOps.grayscale(asset_image).convert("RGBA")
                _paste_image(canvas, grayscale, box, mode="cover")
        if entry.caption:
            _draw_wrapped_text(
                draw,
                entry.caption,
                (left + 8, top + height_box - 42, width_box - 16, 40),
                font_caption,
                INK_BLACK,
            )

    # Series description (placed within strip if defined)
    strip_slot = gallery.get("strip")
    if strip_slot:
        left, top, width_box, height_box = _slot_to_box(strip_slot)
        _draw_wrapped_text(
            draw,
            poster.series_description,
            (left + 8, top + height_box - 40, width_box - 16, 40),
            font_caption,
            INK_BLACK,
        )

    return canvas


def generate_poster_asset(poster: PosterInput, prompt: str, preview: str) -> PosterImage:
    """Generate a poster image using locked templates with an OpenAI edit fallback."""

    template = _load_template_resources(poster.template_id)
    locked_frame = _render_template_frame(poster, template, fill_background=False)


    settings = get_settings()
    if settings.glibatree.is_configured:
        try:
            if settings.glibatree.use_openai_client:
                logger.debug("Requesting Glibatree asset via OpenAI edit pipeline")
                return _request_glibatree_openai_edit(settings.glibatree, prompt, locked_frame, template)
            logger.debug("Requesting Glibatree asset via HTTP endpoint %s", settings.glibatree.api_url)
            response = _request_glibatree_http(
                settings.glibatree.api_url or "",
                settings.glibatree.api_key or "",
                prompt,
                locked_frame,
                template,
            )
            return response
        except Exception:
            logger.exception("Glibatree request failed, falling back to mock poster")

    logger.debug("Falling back to local template renderer")
    mock_frame = _render_template_frame(poster, template, fill_background=True)
    return _poster_image_from_pillow(mock_frame, f"{template.id}_mock.png")


def _request_glibatree_http(
    api_url: str,
    api_key: str,
    prompt: str,
    locked_frame: Image.Image,
    template: TemplateResources,
) -> PosterImage:
    """Call the remote Glibatree API and transform the result into PosterImage."""

    response = requests.post(
        api_url,
        headers={"Authorization": f"Bearer {api_key}"},
        json={"prompt": prompt},
        timeout=60,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover - relies on remote API failures
        detail = exc.response.text if exc.response is not None else str(exc)
        raise RuntimeError(f"Glibatree API 请求失败：{detail}") from exc
    payload: dict[str, Any] = response.json()

    if "data_url" in payload:
        data_url = payload["data_url"]
    elif "image_base64" in payload:
        data_url = f"data:image/png;base64,{payload['image_base64']}"
    else:
        raise ValueError("Unexpected Glibatree response format")

    width = int(payload.get("width", 1024))
    height = int(payload.get("height", 1024))
    filename = payload.get("filename", "poster.png")
    media_type = payload.get("media_type", "image/png")

    image = _load_image_from_data_url(data_url)
    if image:
        composed = image.convert("RGBA")
        mask_alpha = template.mask_background.split()[3]
        composed.paste(locked_frame, mask=mask_alpha)
        return _poster_image_from_pillow(composed, filename)

    return PosterImage(
        filename=filename,
        media_type=media_type,
        data_url=data_url,
        width=width,
        height=height,
    )


def _request_glibatree_openai_edit(
    config: GlibatreeConfig,
    prompt: str,
    locked_frame: Image.Image,
    template: TemplateResources,
) -> PosterImage:
    """Request a poster asset via the OpenAI 1.x image edit API."""

    if not config.api_key:
        raise ValueError("GLIBATREE_API_KEY 未配置。")

    client_kwargs: dict[str, Any] = {"api_key": config.api_key}
    if config.api_url:
        client_kwargs["base_url"] = config.api_url

    http_client: httpx.Client | None = None
    if config.proxy:
        timeout = httpx.Timeout(60.0, connect=10.0, read=60.0)
        http_client = httpx.Client(proxies=config.proxy, timeout=timeout)
        client_kwargs["http_client"] = http_client

    base_bytes = _image_to_png_bytes(locked_frame)
    mask_bytes = _image_to_png_bytes(template.mask_background)


    with ExitStack() as stack:
        if http_client is not None:
            stack.callback(http_client.close)

        client = OpenAI(**client_kwargs)
        response = client.images.edit(
            model=config.model or "gpt-image-1",
            image=base_bytes,
            mask=mask_bytes,

            prompt=prompt,
            size=OPENAI_IMAGE_SIZE,
            response_format="b64_json",
        )

    if not response.data:
        raise ValueError("Glibatree API 未返回任何图像数据。")

    image = response.data[0]
    b64_data = getattr(image, "b64_json", None)
    if not b64_data:
        raise ValueError("Glibatree API 响应缺少 b64_json 字段。")

    decoded = base64.b64decode(b64_data)

    try:
        generated = Image.open(BytesIO(decoded)).convert("RGBA")
    except UnidentifiedImageError:
        logger.exception("Failed to decode OpenAI image payload; returning raw data")
        size = template.spec.get("size", {})
        width = int(size.get("width") or _parse_size(OPENAI_IMAGE_SIZE)[0])
        height = int(size.get("height") or _parse_size(OPENAI_IMAGE_SIZE)[1])
        media_type = getattr(image, "mime_type", None) or "image/png"
        filename = getattr(image, "filename", None) or "poster.png"
        data_url = f"data:{media_type};base64,{b64_data}"
        return PosterImage(
            filename=filename,
            media_type=media_type,
            data_url=data_url,
            width=width,
            height=height,
        )

    mask_alpha = template.mask_background.split()[3]
    generated.paste(locked_frame, mask=mask_alpha)

    filename = getattr(image, "filename", None) or "poster.png"
    return _poster_image_from_pillow(generated, filename)


def _load_image_from_data_url(data_url: str | None) -> Image.Image | None:
    """Decode a base64 data URL into a Pillow image, returning ``None`` on error."""

    if not data_url:
        return None
    try:
        header, encoded = data_url.split(",", 1)
    except ValueError:
        return None
    if not header.startswith("data:") or ";base64" not in header:
        return None

    try:
        binary = base64.b64decode(encoded)
    except (base64.binascii.Error, ValueError):
        return None

    try:
        image = Image.open(BytesIO(binary))
    except Exception:
        return None

    return image.convert("RGBA")


try:  # Pillow >= 10 exposes resampling filters on ``Image.Resampling``
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
except AttributeError:  # pragma: no cover - fallback for older Pillow versions
    RESAMPLE_LANCZOS = Image.LANCZOS


def _paste_image(
    canvas: Image.Image,
    asset: Image.Image,
    box: Tuple[int, int, int, int],
    *,
    mode: str = "contain",
) -> None:
    """Paste ``asset`` into ``box`` on ``canvas`` while preserving aspect ratio."""

    left, top, right, bottom = box
    target_size = (max(right - left, 1), max(bottom - top, 1))

    if mode == "cover":
        resized = ImageOps.fit(asset, target_size, RESAMPLE_LANCZOS)
    else:
        resized = asset.copy()
        resized.thumbnail(target_size, RESAMPLE_LANCZOS)

    offset_x = left + (target_size[0] - resized.width) // 2
    offset_y = top + (target_size[1] - resized.height) // 2
    converted = resized.convert("RGBA")
    mask = converted.split()[3] if "A" in converted.getbands() else None
    canvas.paste(converted, (offset_x, offset_y), mask)


def _image_to_png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _poster_image_from_pillow(image: Image.Image, filename: str) -> PosterImage:
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    background = Image.new("RGBA", image.size, (*SILVER, 255))
    background.alpha_composite(image)
    output = background.convert("RGB")

    buffer = BytesIO()
    output.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

    return PosterImage(
        filename=filename,
        media_type="image/png",
        data_url=f"data:image/png;base64,{encoded}",
        width=output.width,
        height=output.height,
    )


