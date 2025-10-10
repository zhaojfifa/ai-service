from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any, Tuple

import httpx
import requests
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

from app.config import GlibatreeConfig, get_settings
from app.schemas import PosterGalleryItem, PosterImage, PosterInput
from app.services.s3_client import get_bytes, put_bytes


logger = logging.getLogger(__name__)

OPENAI_IMAGE_SIZE = "1024x1024"
ASSET_IMAGE_SIZE = os.getenv("OPENAI_ASSET_SIZE", OPENAI_IMAGE_SIZE)
GALLERY_IMAGE_SIZE = os.getenv("OPENAI_GALLERY_SIZE", "512x512")
TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "frontend" / "templates"
DEFAULT_TEMPLATE_ID = "template_dual"

BRAND_RED = (239, 76, 84)
INK_BLACK = (31, 41, 51)
SILVER = (244, 245, 247)
GUIDE_GREY = (203, 210, 217)


def _copy_model(instance, **update):
    """Compatibility helper for cloning Pydantic v1/v2 models with updates."""

    if hasattr(instance, "model_copy"):
        return instance.model_copy(update=update, deep=True)  # type: ignore[attr-defined]
    data = instance.dict()
    data.update(update)
    return type(instance)(**data)


@dataclass
class TemplateResources:
    id: str
    spec: dict[str, Any]
    template: Image.Image
    mask_background: Image.Image
    mask_scene: Image.Image | None


@dataclass
class PosterGenerationResult:
    poster: PosterImage
    prompt_details: dict[str, str]
    variants: list[PosterImage]
    scores: dict[str, float] | None = None
    seed: int | None = None
    lock_seed: bool = False


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
    template_asset = assets.get("template", "")
    mask_bg_asset = assets.get("mask_background", "")
    mask_scene_asset = assets.get("mask_scene", "")

    template_image = _load_template_asset(template_asset)
    mask_background = _load_template_asset(mask_bg_asset)
    mask_scene = _load_template_asset(mask_scene_asset, required=False)

    return TemplateResources(
        id=template_id,
        spec=spec,
        template=template_image,
        mask_background=mask_background,
        mask_scene=mask_scene,
    )


def _load_template_asset(asset_name: str, *, required: bool = True) -> Image.Image | None:
    """Load a template asset from PNG or its Base64-encoded fallback."""

    if not asset_name:
        if required:
            raise FileNotFoundError("Template asset name is empty")
        return None

    png_path = TEMPLATE_ROOT / asset_name
    if png_path.exists():
        return Image.open(png_path).convert("RGBA")

    b64_path = png_path.with_suffix(".b64")
    if b64_path.exists():
        try:
            decoded = base64.b64decode(b64_path.read_text(encoding="utf-8"))
            return Image.open(BytesIO(decoded)).convert("RGBA")
        except (UnidentifiedImageError, ValueError) as exc:
            raise RuntimeError(f"Unable to decode template asset {b64_path.name}") from exc

    if required:
        raise FileNotFoundError(f"Template asset missing: {png_path}")

    return None


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
        scenario_image = _load_image_asset(
            poster.scenario_asset, getattr(poster, "scenario_key", None)
        )
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
        product_image = _load_image_asset(
            poster.product_asset, getattr(poster, "product_key", None)
        )
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
        asset_image = _load_image_asset(entry.asset, getattr(entry, "key", None))
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


def generate_poster_asset(
    poster: PosterInput,
    prompt: str,
    preview: str,
    *,
    prompt_bundle: dict[str, Any] | None = None,
    prompt_details: dict[str, str] | None = None,
    render_mode: str = "locked",
    variants: int = 1,
    seed: int | None = None,
    lock_seed: bool = False,
) -> PosterGenerationResult:
    """Generate a poster image using locked templates with an OpenAI edit fallback."""

    template = _load_template_resources(poster.template_id)
    locked_frame = _render_template_frame(poster, template, fill_background=False)

    settings = get_settings()
    primary: PosterImage | None = None
    if settings.glibatree.is_configured:
        try:
            if settings.glibatree.use_openai_client:
                logger.debug("Requesting Glibatree asset via OpenAI edit pipeline")
                primary = _request_glibatree_openai_edit(
                    settings.glibatree, prompt, locked_frame, template
                )
            else:
                logger.debug(
                    "Requesting Glibatree asset via HTTP endpoint %s",
                    settings.glibatree.api_url,
                )
                primary = _request_glibatree_http(
                    settings.glibatree.api_url or "",
                    settings.glibatree.api_key or "",
                    prompt,
                    locked_frame,
                    template,
                )
        except Exception:
            logger.exception("Glibatree request failed, falling back to mock poster")

    if primary is None:
        logger.debug("Falling back to local template renderer")
        mock_frame = _render_template_frame(poster, template, fill_background=True)
        primary = _poster_image_from_pillow(mock_frame, f"{template.id}_mock.png")

    variant_images: list[PosterImage] = []
    desired_variants = max(1, variants)
    if desired_variants > 1:
        for index in range(1, desired_variants):
            suffix = f"_v{index + 1}"
            filename = primary.filename
            if "." in filename:
                stem, ext = filename.rsplit(".", 1)
                filename = f"{stem}{suffix}.{ext}"
            else:
                filename = f"{filename}{suffix}"
            variant_images.append(
                _copy_model(
                    primary,
                    filename=filename,
                )
            )

    return PosterGenerationResult(
        poster=primary,
        prompt_details=prompt_details or {},
        variants=variant_images,
        scores=None,
        seed=seed if lock_seed else None,
        lock_seed=bool(lock_seed),
    )


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
    if "," not in data_url:
        logger.warning("Data URL missing comma separator: %s", data_url[:32])
        return None

    header, encoded = data_url.split(",", 1)
    if not header.startswith("data:") or ";base64" not in header:
        logger.warning("Unsupported data URL header: %s", header)
        return None

    try:
        binary = base64.b64decode(encoded)
    except (base64.binascii.Error, ValueError) as exc:
        logger.warning("Failed to decode data URL: %s", exc)
        return None

    try:
        image = Image.open(BytesIO(binary))
    except Exception as exc:
        logger.warning("Decoded image is invalid: %s", exc)
        return None

    return image.convert("RGBA")


def _load_image_from_key(key: str | None) -> Image.Image | None:
    if not key:
        return None
    try:
        payload = get_bytes(key)
    except Exception as exc:  # pragma: no cover - depends on network configuration
        logger.warning("Unable to download object %s from R2: %s", key, exc)
        return None

    try:
        return Image.open(BytesIO(payload)).convert("RGBA")
    except Exception as exc:
        logger.warning("Downloaded asset %s is not a valid image: %s", key, exc)
        return None


def _load_image_asset(data_url: str | None, key: str | None) -> Image.Image | None:
    image = _load_image_from_key(key)
    if image is not None:
        return image
    return _load_image_from_data_url(data_url)


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
    image_bytes = buffer.getvalue()

    safe_filename = filename or "poster.png"
    slug = safe_filename.replace(" ", "_").replace("/", "_")
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    digest = hashlib.sha1(image_bytes).hexdigest()[:10]
    key = f"posters/{timestamp}-{digest}-{slug}"

    url = put_bytes(key, image_bytes, content_type="image/png")
    data_url: str | None = None
    if not url:
        encoded = base64.b64encode(image_bytes).decode("ascii")
        data_url = f"data:image/png;base64,{encoded}"

    return PosterImage(
        filename=safe_filename,
        media_type="image/png",
        data_url=data_url,
        url=url,
        width=output.width,
        height=output.height,
    )


def _generate_image_from_openai(config: GlibatreeConfig, prompt: str, size: str) -> str:
    if not config.api_key:
        raise ValueError("GLIBATREE_API_KEY 未配置，无法调用 OpenAI 生成素材。")

    client_kwargs: dict[str, Any] = {"api_key": config.api_key}
    if config.api_url:
        client_kwargs["base_url"] = config.api_url

    http_client: httpx.Client | None = None
    if config.proxy:
        timeout = httpx.Timeout(60.0, connect=10.0, read=60.0)
        http_client = httpx.Client(proxies=config.proxy, timeout=timeout)
        client_kwargs["http_client"] = http_client

    with ExitStack() as stack:
        if http_client is not None:
            stack.callback(http_client.close)

        client = OpenAI(**client_kwargs)
        response = client.images.generate(
            model=config.model or "gpt-image-1",
            prompt=prompt,
            size=size,
        )

    if not response.data:
        raise ValueError("OpenAI 未返回任何图像数据。")

    image = response.data[0]
    b64_data = getattr(image, "b64_json", None)
    if not b64_data:
        raise ValueError("OpenAI 响应缺少 b64_json 字段。")

    return f"data:image/png;base64,{b64_data}"


def _enforce_template_materials(
    poster: PosterInput, template: TemplateResources
) -> tuple[PosterInput, dict[str, Any]]:
    """Ensure poster inputs respect the selected template's material constraints."""

    materials = template.spec.get("materials", {})

    def _interpret_flag(raw_value: Any, default: bool) -> bool:
        if raw_value is None:
            return default
        if isinstance(raw_value, bool):
            return raw_value
        if isinstance(raw_value, (int, float)):
            return bool(raw_value)
        if isinstance(raw_value, str):
            candidate = raw_value.strip().lower()
            if not candidate:
                return default
            if candidate in {"1", "true", "yes", "y", "on"}:
                return True
            if candidate in {"0", "false", "no", "n", "off"}:
                return False
            return default
        return bool(raw_value)

    def _resolve_material(material: dict[str, Any]) -> tuple[str, bool, bool]:
        material_type = (material.get("type") or "image").lower()
        allows_upload = _interpret_flag(
            material.get("allowsUpload"),
            material_type != "text",
        )
        if material_type == "text":
            allows_upload = False

        allows_prompt = _interpret_flag(
            material.get("allowsPrompt"),
            True,
        )
        if not allows_upload:
            allows_prompt = True

        return material_type, allows_prompt, allows_upload

    scenario_material = materials.get("scenario", {})
    scenario_type, scenario_allows_prompt, scenario_allows_upload = _resolve_material(
        scenario_material
    )

    product_material = materials.get("product", {})
    product_type, product_allows_prompt, product_allows_upload = _resolve_material(
        product_material
    )

    gallery_material = materials.get("gallery", {})
    gallery_type, gallery_allows_prompt, gallery_allows_upload = _resolve_material(
        gallery_material
    )

    gallery_spec = template.spec.get("gallery", {})
    gallery_slot_count = len(gallery_spec.get("items", []) or [])
    gallery_limit_raw = gallery_material.get("count")
    try:
        gallery_limit_from_material = int(gallery_limit_raw) if gallery_limit_raw is not None else None
    except (TypeError, ValueError):
        gallery_limit_from_material = None

    gallery_limit = gallery_limit_from_material or gallery_slot_count or len(poster.gallery_items)

    updates: dict[str, Any] = {}

    desired_scenario_mode = poster.scenario_mode
    if not scenario_allows_upload:
        desired_scenario_mode = "prompt"
    elif desired_scenario_mode == "prompt" and not scenario_allows_prompt:
        desired_scenario_mode = "upload"
    if desired_scenario_mode != poster.scenario_mode:
        logger.info(
            "Template %s enforces scenario mode %s.",
            template.id,
            desired_scenario_mode,
        )
        updates["scenario_mode"] = desired_scenario_mode
    if not scenario_allows_upload and (poster.scenario_asset or poster.scenario_key):
        updates["scenario_asset"] = None
        updates["scenario_key"] = None

    desired_product_mode = poster.product_mode
    if not product_allows_upload:
        desired_product_mode = "prompt"
    elif desired_product_mode == "prompt" and not product_allows_prompt:
        desired_product_mode = "upload"
    if desired_product_mode != poster.product_mode:
        logger.info(
            "Template %s enforces product mode %s.",
            template.id,
            desired_product_mode,
        )
        updates["product_mode"] = desired_product_mode
    if not product_allows_upload and (poster.product_asset or poster.product_key):
        updates["product_asset"] = None
        updates["product_key"] = None

    sanitised_gallery: list[PosterGalleryItem] = []
    gallery_changed = False
    for index, item in enumerate(poster.gallery_items):
        if index >= gallery_limit:
            gallery_changed = True
            break

        desired_mode = item.mode
        updates_for_item: dict[str, Any] = {}
        if not gallery_allows_upload:
            desired_mode = "prompt"
            if item.asset is not None or item.key is not None:
                updates_for_item["asset"] = None
                updates_for_item["key"] = None
        elif desired_mode == "prompt" and not gallery_allows_prompt:
            desired_mode = "upload"

        if desired_mode != item.mode:
            updates_for_item["mode"] = desired_mode

        sanitised_item = (
            item if not updates_for_item else _copy_model(item, **updates_for_item)
        )
        sanitised_gallery.append(sanitised_item)
        if sanitised_item is not item:
            gallery_changed = True

    if len(poster.gallery_items) != len(sanitised_gallery):
        gallery_changed = True

    if gallery_changed:
        updates["gallery_items"] = sanitised_gallery

    if updates:
        poster = _copy_model(poster, **updates)

    material_flags = {
        "scenario": {
            "allows_prompt": scenario_allows_prompt,
            "allows_upload": scenario_allows_upload,
            "type": scenario_type,
        },
        "product": {
            "allows_prompt": product_allows_prompt,
            "allows_upload": product_allows_upload,
            "type": product_type,
        },
        "gallery": {
            "allows_prompt": gallery_allows_prompt,
            "allows_upload": gallery_allows_upload,
            "type": gallery_type,
            "count": gallery_limit,
        },
    }

    return poster, material_flags


def prepare_poster_assets(poster: PosterInput) -> PosterInput:
    """Resolve AI-generated assets for scenario, product, and gallery slots."""

    template = _load_template_resources(poster.template_id)
    poster, material_flags = _enforce_template_materials(poster, template)

    settings = get_settings()
    config = settings.glibatree

    if not config.use_openai_client or not config.api_key:
        return poster

    updates: dict[str, Any] = {}

    scenario_allows_prompt = material_flags["scenario"].get("allows_prompt", False)
    if (
        scenario_allows_prompt
        and poster.scenario_mode == "prompt"
        and not poster.scenario_asset
        and not poster.scenario_key
    ):
        prompt_text = poster.scenario_prompt or poster.scenario_image
        if prompt_text:
            try:
                scenario_asset = _generate_image_from_openai(config, prompt_text, ASSET_IMAGE_SIZE)
                updates["scenario_asset"] = scenario_asset
            except Exception:  # pragma: no cover - network failure paths
                logger.exception("Failed to generate scenario asset from prompt: %s", prompt_text)

    product_allows_prompt = material_flags["product"].get("allows_prompt", False)
    if (
        product_allows_prompt
        and poster.product_mode == "prompt"
        and not poster.product_asset
        and not poster.product_key
    ):
        prompt_text = poster.product_prompt or poster.product_name
        if prompt_text:
            try:
                product_asset = _generate_image_from_openai(config, prompt_text, ASSET_IMAGE_SIZE)
                updates["product_asset"] = product_asset
            except Exception:  # pragma: no cover - network failure paths
                logger.exception("Failed to generate product asset from prompt: %s", prompt_text)

    gallery_flags = material_flags["gallery"]
    gallery_allows_prompt = gallery_flags.get("allows_prompt", False)
    gallery_limit = gallery_flags.get("count") or len(poster.gallery_items)

    gallery_updates: list[PosterGalleryItem] = []
    gallery_changed = False
    for index, item in enumerate(poster.gallery_items):
        if index >= gallery_limit:
            break
        if (
            gallery_allows_prompt
            and item.mode == "prompt"
            and not item.asset
            and not item.key
            and item.prompt
        ):
            try:
                asset_url = _generate_image_from_openai(config, item.prompt, GALLERY_IMAGE_SIZE)
                gallery_updates.append(_copy_model(item, asset=asset_url))
                gallery_changed = True
            except Exception:  # pragma: no cover - network failure paths
                logger.exception("Failed to generate gallery asset from prompt: %s", item.prompt)
                gallery_updates.append(item)
        else:
            gallery_updates.append(item)

    if gallery_changed:
        updates["gallery_items"] = gallery_updates

    if updates:
        return _copy_model(poster, **updates)
    return poster

