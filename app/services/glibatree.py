from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any, Optional, Tuple

import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError

from app.config import GlibatreeConfig, get_settings
from app.schemas import PosterGalleryItem, PosterImage, PosterInput
from app.schemas.poster import PosterPayload
from app.services.vertex_imagen import _aspect_from_dims, _select_dimension_kwargs
from app.services.vertex_imagen3 import VertexImagen3
from app.services.s3_client import get_bytes, make_key, public_url_for, put_bytes
from app.services.template_variants import generation_overrides

logger = logging.getLogger(__name__)

vertex_imagen_client: VertexImagen3 | None = None


def configure_vertex_imagen(client: VertexImagen3 | None) -> None:
    """Configure the shared Vertex Imagen3 client used for poster generation."""

    global vertex_imagen_client
    vertex_imagen_client = client

OPENAI_IMAGE_SIZE = "1024x1024"
ASSET_IMAGE_SIZE = os.getenv("OPENAI_ASSET_SIZE", OPENAI_IMAGE_SIZE)
GALLERY_IMAGE_SIZE = os.getenv("OPENAI_GALLERY_SIZE", "512x512")
TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "frontend" / "templates"
DEFAULT_TEMPLATE_ID = "template_dual"

BRAND_RED = (239, 76, 84)
INK_BLACK = (31, 41, 51)
SILVER = (244, 245, 247)
GUIDE_GREY = (203, 210, 217)

_ALLOWED_REF_PREFIXES = ("r2://", "s3://", "gs://", "https://", "http://")
_BARE_KEY_PATTERN = re.compile(r"^[0-9A-Za-z._/-]+$")


def r2_public_url_from_ref(ref: str) -> str:
    """Resolve a storage reference into a publicly accessible URL."""

    if not ref:
        raise ValueError("empty storage reference")

    value = ref.strip()
    if value.startswith(("http://", "https://")):
        return value

    if value.startswith(("r2://", "s3://")):
        _, path = value.split("://", 1)
        if "/" not in path:
            raise ValueError(f"invalid storage reference: {value}")
        _, key = path.split("/", 1)
        url = public_url_for(key)
        return url or value

    if value.startswith("gs://"):
        # Vertex output written to GCS can be served directly or proxied.
        return value

    raise ValueError(f"unsupported storage reference: {value}")


def upload_bytes_to_r2_return_ref(
    data: bytes,
    *,
    key: str | None = None,
    ext: str = ".png",
    content_type: str = "image/png",
) -> tuple[str, str]:
    """Persist ``data`` to R2/S3 and return (r2://bucket/key, public_url)."""

    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("image payload must be bytes")

    bucket = (os.getenv("R2_BUCKET") or os.getenv("S3_BUCKET") or "").strip()
    if not bucket:
        raise RuntimeError("R2/S3 bucket is not configured")

    if key:
        storage_key = key.lstrip("/")
    else:
        filename = f"{uuid.uuid4().hex}{ext if ext.startswith('.') else f'.{ext}'}"
        storage_key = make_key("posters", filename)

    url = put_bytes(storage_key, bytes(data), content_type=content_type)
    if not url:
        raise RuntimeError(f"Failed to upload object {storage_key}")

    return f"r2://{bucket}/{storage_key}", url


def _default_asset_bucket() -> str | None:
    return (
        os.getenv("POSTER_ASSET_BUCKET")
        or os.getenv("R2_BUCKET")
        or os.getenv("S3_BUCKET")
    )


def _default_asset_scheme(bucket: str | None) -> str | None:
    scheme = os.getenv("POSTER_ASSET_SCHEME") or os.getenv("ASSET_SCHEME")
    if scheme:
        return scheme.rstrip(":/")

    r2_bucket = os.getenv("R2_BUCKET")
    s3_bucket = os.getenv("S3_BUCKET")
    if bucket and bucket == r2_bucket:
        return "r2"
    if bucket and bucket == s3_bucket:
        return "s3"

    if r2_bucket:
        return "r2"
    if s3_bucket:
        return "s3"
    return None


def _public_base_override() -> str | None:
    base = (
        os.getenv("POSTER_ASSET_PUBLIC_BASE")
        or os.getenv("ASSETS_PUBLIC_BASE")
        or os.getenv("R2_PUBLIC_BASE")
        or os.getenv("S3_PUBLIC_BASE")
    )
    if base:
        return base.rstrip("/")
    return None


def coerce_asset_ref_to_url(
    value: str | None, *, key: str | None = None
) -> tuple[str | None, str | None]:
    """Normalise loose asset references into allowed URL formats."""

    candidate = (value or "").strip()
    key_candidate = key.strip() if isinstance(key, str) else ""

    if not candidate and key_candidate:
        candidate = key_candidate

    if not candidate:
        return None, key_candidate or None

    if candidate.lower().startswith("data:"):
        raise ValueError("base64 not allowed – upload to R2/GCS and pass key/url")

    if candidate.startswith(_ALLOWED_REF_PREFIXES):
        return candidate, key_candidate.lstrip("/") or None

    fallback_key = key_candidate or candidate
    fallback_key = fallback_key.lstrip("/")
    if fallback_key and _BARE_KEY_PATTERN.match(fallback_key):
        bucket = _default_asset_bucket()
        scheme = _default_asset_scheme(bucket)
        public_base = _public_base_override()
        if bucket and scheme:
            return f"{scheme}://{bucket}/{fallback_key}", fallback_key
        if public_base:
            return f"{public_base}/{fallback_key}", fallback_key

    raise ValueError("invalid url; expected r2://, s3://, gs:// or http(s)")


def _normalise_asset_reference(label: str, value: Any) -> Any:
    """Coerce loose asset references into URL/Key pairs when possible."""

    if value is None:
        return None

    if hasattr(value, "model_dump"):
        normalised = value.model_dump(exclude_none=False)
    elif hasattr(value, "dict"):
        normalised = value.dict(exclude_none=False)
    elif isinstance(value, dict):
        normalised = dict(value)
    elif isinstance(value, str):
        normalised = {"url": value}
    else:
        return value

    raw_url = normalised.get("url")
    if isinstance(raw_url, str):
        candidate = raw_url.strip()
        normalised["url"] = candidate

    key_candidate = normalised.get("key")
    if isinstance(key_candidate, str):
        cleaned_key = key_candidate.strip().lstrip("/")
    else:
        cleaned_key = None
    if cleaned_key:
        normalised["key"] = cleaned_key
    elif "key" in normalised:
        normalised["key"] = None

    try:
        url_value, derived_key = coerce_asset_ref_to_url(
            normalised.get("url"), key=cleaned_key
        )
    except ValueError as exc:
        logger.debug(
            "poster.asset.invalid_ref",
            extra={"field": label, "value": normalised.get("url"), "error": str(exc)},
        )
        raise
    normalised["url"] = url_value
    if derived_key and not cleaned_key:
        normalised["key"] = derived_key

    return normalised


def _key_field_for_asset(field: str) -> str | None:
    overrides = {
        "scenario_image": "scenario_key",
        "product_image": "product_key",
    }
    return overrides.get(field)


def _apply_asset_reference(target: Any, field: str, value: Any) -> None:
    """Propagate normalised asset references back to the original payload."""

    if isinstance(target, dict):
        target[field] = value
        if isinstance(value, dict):
            key_field = _key_field_for_asset(field)
            if key_field:
                target[key_field] = value.get("key") or target.get(key_field)
        return

    if isinstance(value, dict):
        url_value = value.get("url")
    else:
        url_value = value

    if isinstance(url_value, str) and url_value:
        try:
            setattr(target, field, url_value)
        except Exception:  # pragma: no cover - defensive
            pass

    if isinstance(value, dict):
        key_value = value.get("key")
        key_field = _key_field_for_asset(field)
        if key_field and key_value and hasattr(target, key_field):
            try:
                setattr(target, key_field, key_value)
            except Exception:  # pragma: no cover - defensive
                pass


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
    trace_ids: list[str] = field(default_factory=list)
    fallback_used: bool = False
    provider: str | None = None


def _template_dimensions(
    template: TemplateResources, locked_frame: Image.Image
) -> tuple[int, int]:
    size_spec = template.spec.get("size", {})
    width = int(size_spec.get("width") or locked_frame.width)
    height = int(size_spec.get("height") or locked_frame.height)
    return max(width, 64), max(height, 64)


def _default_mask_b64(template: TemplateResources) -> str | None:
    mask = template.mask_background
    if not mask:
        return None

    alpha = mask.split()[3]
    inverted = ImageOps.invert(alpha)
    buffer = BytesIO()
    inverted.convert("L").save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _shorten_asset_value(value: str) -> str:
    text = value.strip()
    if len(text) <= 64:
        return text
    return f"{text[:32]}…{text[-16:]}"


def _poster_asset_summary(poster: PosterInput | dict[str, Any]) -> dict[str, Any]:
    keys: list[str] = []
    urls: list[str] = []

    def _record(candidate: str | None) -> None:
        if not candidate:
            return
        trimmed = candidate.strip()
        if not trimmed:
            return
        if trimmed.lower().startswith("http"):
            urls.append(_shorten_asset_value(trimmed))
        else:
            keys.append(_shorten_asset_value(trimmed))

    _record(getattr(poster, "brand_logo", None))
    _record(getattr(poster, "scenario_asset", None))
    _record(getattr(poster, "product_asset", None))
    _record(getattr(poster, "scenario_key", None))
    _record(getattr(poster, "product_key", None))

    for item in getattr(poster, "gallery_items", []) or []:
        if isinstance(item, PosterGalleryItem):
            _record(getattr(item, "key", None))
            _record(getattr(item, "asset", None))
        elif isinstance(item, dict):
            _record(str(item.get("key")) if item.get("key") else None)
            _record(str(item.get("asset")) if item.get("asset") else None)

    return {
        "keys": keys[:8],
        "urls": urls[:3],
        "count": len(keys) + len(urls),
    }


def _assert_assets_use_ref_only(poster: PosterInput | dict[str, Any]) -> None:
    """Ensure poster assets reference stored objects rather than base64 blobs."""

    if hasattr(poster, "model_dump"):
        try:
            payload = poster.model_dump(exclude_none=False)
        except TypeError:  # pragma: no cover - defensive
            payload = poster.model_dump()
    elif hasattr(poster, "dict"):
        payload = poster.dict(exclude_none=False)
    elif isinstance(poster, dict):
        payload = dict(poster)
    else:  # pragma: no cover - extremely rare
        payload = {
            key: getattr(poster, key)
            for key in dir(poster)
            if not key.startswith("__") and not callable(getattr(poster, key))
        }

    gallery = payload.get("gallery_items") or payload.get("gallery") or []
    normalised_gallery: list[Any] = []
    for entry in gallery:
        if hasattr(entry, "model_dump"):
            normalised_gallery.append(entry.model_dump(exclude_none=False))
        elif hasattr(entry, "dict"):
            normalised_gallery.append(entry.dict(exclude_none=False))
        else:
            normalised_gallery.append(entry)
    if normalised_gallery:
        payload["gallery_items"] = normalised_gallery

    for field in ("scenario_image", "brand_logo"):
        if field in payload:
            try:
                normalised_value = _normalise_asset_reference(field, payload.get(field))
            except ValueError as exc:
                message = str(exc)
                detail = (
                    "请求体过大或包含 base64 图片，请先上传素材到 R2，仅传输 key/url"
                    if "base64" in message.lower()
                    else f"{message}; field={field}"
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=detail,
                ) from exc
            payload[field] = normalised_value
            _apply_asset_reference(poster, field, normalised_value)

    try:
        if hasattr(PosterPayload, "model_validate"):
            PosterPayload.model_validate(payload)
        elif hasattr(PosterPayload, "parse_obj"):
            PosterPayload.parse_obj(payload)
        else:  # pragma: no cover - ultra legacy
            PosterPayload(**payload)
    except ValidationError as exc:
        issues = []
        for error in exc.errors():
            location = ".".join(str(item) for item in error.get("loc", ()))
            message = error.get("msg") or error.get("type") or "invalid"
            issues.append(f"{location}:{message}")
        logger.warning(
            "poster.asset.invalid",
            extra={"issues": issues, "template": payload.get("template_id")},
        )
        detail = "请求体过大或包含 base64 图片，请先上传素材到 R2，仅传输 key/url"
        if issues:
            detail = f"{detail}; bad={','.join(issues)}"
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        ) from exc


def _generate_poster_with_vertex(
    client: VertexImagen3,
    poster: PosterInput,
    prompt: str,
    locked_frame: Image.Image,
    template: TemplateResources,
    *,
    prompt_details: dict[str, str] | None = None,
    trace_id: str | None = None,
) -> tuple[PosterImage, dict[str, Any]]:
    width_default, height_default = _template_dimensions(template, locked_frame)

    requested_size = getattr(poster, "size", None)
    width = int(getattr(poster, "width", None) or width_default)
    height = int(getattr(poster, "height", None) or height_default)
    width = max(width, 64)
    height = max(height, 64)
    size_arg = requested_size or f"{width}x{height}"

    negative_prompt = getattr(poster, "negative_prompt", None)
    if not negative_prompt and prompt_details:
        negative_prompt = prompt_details.get("negative_prompt")

    guidance = getattr(poster, "guidance", None)
    aspect_ratio = getattr(poster, "aspect_ratio", None)

    base_image_b64 = getattr(poster, "base_image_b64", None)
    mask_b64 = getattr(poster, "mask_b64", None)
    region_rect = getattr(poster, "region_rect", None)

    should_edit = bool(base_image_b64 or mask_b64 or region_rect)
    request_trace = trace_id or uuid.uuid4().hex[:8]
    telemetry: dict[str, Any] = {
        "request_trace": request_trace,
        "mode": "edit" if should_edit else "generate",
        "size": f"{width}x{height}",
        "template": template.id,
    }

    params = getattr(
        client,
        "_edit_params" if should_edit else "_generate_params",
        None,
    )
    ratio_hint = aspect_ratio or _aspect_from_dims(width, height)
    if isinstance(params, set):
        _, size_mode = _select_dimension_kwargs(params, width, height, ratio_hint)
        telemetry["size_mode"] = size_mode

    vertex_trace: str | None = None
    start = time.time()
    try:
        if should_edit:
            base_bytes = (
                base64.b64decode(base_image_b64)
                if base_image_b64
                else _image_to_png_bytes(locked_frame)
            )
            mask_arg = mask_b64 or _default_mask_b64(template)
            payload = client.edit_bytes(
                base_image_bytes=base_bytes,
                prompt=prompt,
                mask_b64=mask_arg,
                region_rect=region_rect,
                size=size_arg,
                width=width,
                height=height,
                negative_prompt=negative_prompt,
                guidance=guidance,
                return_trace=True,
            )
        else:
            payload = client.generate_bytes(
                prompt=prompt,
                size=size_arg,
                width=width,
                height=height,
                negative_prompt=negative_prompt,
                aspect_ratio=aspect_ratio,
                guidance=guidance,
                return_trace=True,
            )
        if isinstance(payload, tuple):
            image_bytes, vertex_trace = payload
        else:  # pragma: no cover - defensive fallback
            image_bytes, vertex_trace = payload, None
    except Exception as exc:
        elapsed = (time.time() - start) * 1000
        telemetry.update(
            {
                "status": "error",
                "elapsed_ms": round(elapsed, 2),
                "vertex_trace": vertex_trace,
                "error": str(exc),
            }
        )
        logger.exception(
            "Vertex Imagen3 %s failed",
            telemetry["mode"],
            extra={"request_trace": request_trace, "vertex_trace": vertex_trace},
        )
        raise

    elapsed = (time.time() - start) * 1000
    telemetry.update(
        {
            "status": "ok",
            "elapsed_ms": round(elapsed, 2),
            "vertex_trace": vertex_trace,
        }
    )

    try:
        generated = Image.open(BytesIO(image_bytes)).convert("RGBA")
    except UnidentifiedImageError as exc:
        telemetry.update({"status": "invalid_image", "error": str(exc)})
        raise RuntimeError(f"Vertex Imagen3 returned invalid image: {exc}") from exc

    if template.mask_background:
        mask_alpha = template.mask_background.split()[3]
        generated.paste(locked_frame, mask=mask_alpha)
    else:
        generated.alpha_composite(locked_frame)

    safe_name = f"{template.id}_vertex.png"
    telemetry["bytes"] = len(image_bytes)
    logger.info(
        "Vertex Imagen3 poster generated",
        extra={
            "request_trace": request_trace,
            "vertex_trace": vertex_trace,
            "mode": telemetry["mode"],
            "size": telemetry["size"],
            "bytes": telemetry["bytes"],
        },
    )
    return _poster_image_from_pillow(generated, safe_name), telemetry



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
    trace_id: str | None = None,
    aspect_closeness: float | None = None,
) -> PosterGenerationResult:
    """Generate a poster image using locked templates with an OpenAI edit fallback."""
    _assert_assets_use_ref_only(poster)

    desired_variants = max(1, variants)
    override_posters = generation_overrides(desired_variants)
    override_primary = override_posters[0] if override_posters else None
    override_variants = override_posters[1:] if len(override_posters) > 1 else []
    used_override_primary = False

    provider_label = (
        vertex_imagen_client.__class__.__name__
        if vertex_imagen_client is not None
        else "LocalTemplateRenderer"
    )

    template = _load_template_resources(poster.template_id)
    locked_frame = _render_template_frame(poster, template, fill_background=False)

    settings = get_settings()
    primary: PosterImage | None = None
    variant_images: list[PosterImage] = []
    vertex_traces: list[str] = []
    fallback_used = vertex_imagen_client is None

    logger.info(
        "[vertex] generate_poster start",
        extra={
            "trace": trace_id,
            "template": template.id,
            "scenario_mode": getattr(poster, "scenario_mode", None),
            "product_mode": getattr(poster, "product_mode", None),
            "variants": variants,
            "seed": seed,
            "lock_seed": lock_seed,
            "provider": provider_label,
            "prompt_preview": prompt[:280],
            "neg_prompt_preview": (prompt_details or {}).get("negative_prompt")
            or (prompt_details or {}).get("negative"),
            "prompt_details": (prompt_details or {}).get("scenario"),
            "asset_summary": _poster_asset_summary(poster),
        },
    )

    if vertex_imagen_client is not None:
        try:
            primary, telemetry = _generate_poster_with_vertex(
                vertex_imagen_client,
                poster,
                prompt,
                locked_frame,
                template,
                prompt_details=prompt_details,
                trace_id=trace_id,
            )
            trace_value = telemetry.get("vertex_trace") or telemetry.get("request_trace")
            if trace_value:
                vertex_traces.append(str(trace_value))
            provider_label = getattr(vertex_imagen_client, "__class__", VertexImagen3).__name__
        except Exception:
            fallback_used = True
            logger.exception(
                "Vertex Imagen3 generation failed; falling back",
                extra={"trace": trace_id},
            )

    http_payload: dict[str, Any] | None = None
    if settings.glibatree.is_configured and settings.glibatree.api_url:
        http_payload = _generate_payload(
            poster,
            prompt,
            preview,
            prompt_bundle=prompt_bundle,
            prompt_details=prompt_details,
            render_mode=render_mode,
            variants=variants,
            seed=seed,
            lock_seed=lock_seed,
            trace_id=trace_id,
            aspect_closeness=aspect_closeness,
        )

    if (
        primary is None
        and settings.glibatree.is_configured
        and settings.glibatree.api_url
    ):
        fallback_used = True
        try:
            logger.debug(
                "Requesting Glibatree asset via HTTP endpoint %s",
                settings.glibatree.api_url,
                extra={"trace": trace_id},
            )
            primary = _request_glibatree_http(
                settings.glibatree.api_url or "",
                settings.glibatree.api_key or "",
                prompt,
                locked_frame,
                template,
                payload=http_payload,
                trace_id=trace_id,
            )
            provider_label = "GlibatreeHTTP"
        except Exception:
            logger.exception(
                "Glibatree request failed, falling back to mock poster",
                extra={"trace": trace_id},
            )

    if primary is None:
        fallback_used = True
        if override_primary is not None:
            logger.debug(
                "Using uploaded template poster override for primary result",
                extra={"trace": trace_id},
            )
            primary = override_primary
            variant_images = list(override_variants)
            used_override_primary = True
            provider_label = "TemplateOverride"
        else:
            logger.debug(
                "Falling back to local template renderer",
                extra={"trace": trace_id},
            )
            mock_frame = _render_template_frame(poster, template, fill_background=True)
            primary = _poster_image_from_pillow(mock_frame, f"{template.id}_mock.png")
            provider_label = "LocalTemplateRenderer"

    # 生成变体（仅重命名，不重复上传）
    if not used_override_primary and desired_variants > 1:
        for index in range(1, desired_variants):
            suffix = f"_v{index + 1}"
            filename = primary.filename
            if "." in filename:
                stem, ext = filename.rsplit(".", 1)
                filename = f"{stem}{suffix}.{ext}"
            else:
                filename = f"{filename}{suffix}"
            variant_images.append(_copy_model(primary, filename=filename))

    if not used_override_primary and override_variants:
        variant_images.extend(override_variants)

    result = PosterGenerationResult(
        poster=primary,
        prompt_details=prompt_details or {},
        variants=variant_images,
        scores=None,
        seed=seed if lock_seed else None,
        lock_seed=bool(lock_seed),
        trace_ids=vertex_traces,
        fallback_used=fallback_used,
        provider=provider_label,
    )

    logger.info(
        "[vertex] generate_poster done",
        extra={
            "trace": trace_id,
            "template": template.id,
            "provider": provider_label,
            "fallback_used": fallback_used,
            "poster_filename": getattr(primary, "filename", None),
            "variants": len(variant_images),
            "vertex_traces": vertex_traces,
        },
    )

    return result


def _generate_payload(
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
    trace_id: str | None = None,
    aspect_closeness: float | None = None,
) -> dict[str, Any]:
    """Serialise poster inputs into a JSON-safe payload for HTTP fallbacks."""

    if hasattr(poster, "model_dump"):
        poster_payload = poster.model_dump(exclude_none=True)
    elif hasattr(poster, "dict"):
        poster_payload = poster.dict(exclude_none=True)
    else:  # pragma: no cover - defensive fallback for legacy objects
        poster_payload = {
            key: getattr(poster, key)
            for key in dir(poster)
            if not key.startswith("__") and not callable(getattr(poster, key))
        }

    payload: dict[str, Any] = {
        "poster": poster_payload,
        "prompt": prompt,
        "preview": preview,
        "prompt_bundle": prompt_bundle or {},
        "prompt_details": prompt_details or {},
        "render_mode": render_mode,
        "variants": variants,
        "seed": seed,
        "lock_seed": lock_seed,
        "trace_id": trace_id,
    }
    if aspect_closeness is not None:
        payload["aspect_closeness"] = aspect_closeness

    return jsonable_encoder(payload, exclude_none=True)


def _request_glibatree_http(
    api_url: str,
    api_key: str,
    prompt: str,
    locked_frame: Image.Image,
    template: TemplateResources,
    *,
    payload: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> PosterImage:
    """Call the remote Glibatree API and transform the result into PosterImage."""
    body: dict[str, Any] = payload or {}
    if "prompt" not in body:
        body = dict(body)
        body["prompt"] = prompt

    safe_body = jsonable_encoder(body, exclude_none=True)
    logger.debug(
        "poster.asset.glibatree.payload",
        extra={"trace": trace_id, "payload_keys": sorted(safe_body.keys())},
    )

    response = requests.post(
        api_url,
        headers={"Authorization": f"Bearer {api_key}"},
        json=safe_body,
        timeout=60,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
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


def _compose_and_upload_from_b64(template: TemplateResources, locked_frame: Image.Image, b64_data: str) -> PosterImage:
    decoded = base64.b64decode(b64_data)
    try:
        generated = Image.open(BytesIO(decoded)).convert("RGBA")
    except UnidentifiedImageError:
        # 解码失败：回传 data_url 以便前端仍可预览
        w, h = _parse_size(OPENAI_IMAGE_SIZE)
        size = template.spec.get("size", {})
        w = int(size.get("width") or w)
        h = int(size.get("height") or h)
        data_url = f"data:image/png;base64,{b64_data}"
        return PosterImage(filename="poster.png", media_type="image/png",
                           data_url=data_url, width=w, height=h)

    # 叠加锁定 UI
    mask_alpha = template.mask_background.split()[3]
    generated.paste(locked_frame, mask=mask_alpha)
    return _poster_image_from_pillow(generated, "poster.png")



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
    if key.startswith("r2://"):
        key = key[5:]
    try:
        payload = get_bytes(key)
    except Exception as exc:
        logger.warning("Unable to download object %s from R2: %s", key, exc)
        return None

    try:
        return Image.open(BytesIO(payload)).convert("RGBA")
    except Exception as exc:
        logger.warning("Downloaded asset %s is not a valid image: %s", key, exc)
        return None


def _load_image_from_url(url: str) -> Image.Image | None:
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Failed to download asset %s: %s", url, exc)
        return None

    try:
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as exc:
        logger.warning("Downloaded asset %s is not a valid image: %s", url, exc)
        return None


def _load_image_asset(source: str | None, key: str | None) -> Image.Image | None:
    image = _load_image_from_key(key)
    if image is not None:
        return image

    if not source:
        return None

    if not isinstance(source, str):
        return None

    token = source.strip()
    if token.startswith("r2://"):
        return _load_image_from_key(token)
    if token.lower().startswith("data:image"):
        logger.warning("Ignoring inline data URL asset; upload to R2 first")
        return None
    if token.lower().startswith("http://") or token.lower().startswith("https://"):
        return _load_image_from_url(token)

    return None


try:
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
except AttributeError:
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
    """将 Pillow 图片上传到 R2；失败时回退 base64，并统一记录 key/url 以便排查。"""
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
    storage_key = f"posters/{timestamp}-{digest}-{slug}"

    storage_ref: str | None = None
    url: str | None = None
    try:
        storage_ref, url = upload_bytes_to_r2_return_ref(
            image_bytes,
            key=storage_key,
            content_type="image/png",
        )
        logger.info("R2 upload ok key=%s url=%s", storage_key, url)
    except Exception as exc:  # pragma: no cover - storage fallback
        logger.warning(
            "R2 upload failed; will return data_url instead", extra={"key": storage_key, "error": str(exc)}
        )

    data_url: str | None = None
    if not url:
        encoded = base64.b64encode(image_bytes).decode("ascii")
        data_url = f"data:image/png;base64,{encoded}"

    key_value: str | None = None
    if storage_ref and "://" in storage_ref:
        _, path = storage_ref.split("://", 1)
        key_value = path.split("/", 1)[1] if "/" in path else storage_key
    elif url:
        key_value = storage_key

    return PosterImage(
        filename=safe_filename,
        media_type="image/png",
        data_url=data_url,
        url=url,
        key=key_value,
        width=output.width,
        height=output.height,
    )


def _parse_size(size_str: str) -> tuple[int, int]:
    """Parse '1024x1024' into (1024, 1024) with safe fallback."""
    try:
        w, h = str(size_str).lower().split("x", 1)
        return int(w), int(h)
    except Exception:
        return 1024, 1024


def _generate_image_from_openai(config: GlibatreeConfig, prompt: str, size: str) -> str:
    """使用 Vertex Imagen3 生成 PNG data URL（兼容旧签名）。"""

    del config  # 保留兼容签名

    if vertex_imagen_client is None:
        raise RuntimeError("Vertex Imagen3 未配置，无法生成图像。")

    width, height = _parse_size(size)

    try:
        image_bytes = vertex_imagen_client.generate_bytes(
            prompt=prompt,
            size=size,
            width=width,
            height=height,
        )
    except Exception as exc:  # pragma: no cover - 网络或配置异常
        raise RuntimeError(f"vertex imagen generate error: {exc}") from exc

    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGBA")
    except Exception as exc:  # pragma: no cover - 非法图像
        raise RuntimeError(f"invalid image payload: {exc}") from exc

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


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

        allows_prompt = _interpret_flag(material.get("allowsPrompt"), True)
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
        logger.info("Template %s enforces scenario mode %s.", template.id, desired_scenario_mode)
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
        logger.info("Template %s enforces product mode %s.", template.id, desired_product_mode)
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

        sanitised_item = item if not updates_for_item else _copy_model(item, **updates_for_item)
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

    if not config.use_openai_client or not (config.api_key and config.api_url):
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
            except Exception:
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
            except Exception:
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
            except Exception:
                logger.exception("Failed to generate gallery asset from prompt: %s", item.prompt)
                gallery_updates.append(item)
        else:
            gallery_updates.append(item)

    if gallery_changed:
        updates["gallery_items"] = gallery_updates

    if updates:
        return _copy_model(poster, **updates)
    return poster
