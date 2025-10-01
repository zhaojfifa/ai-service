from __future__ import annotations

import base64
import logging
import textwrap
from contextlib import ExitStack
from io import BytesIO
from typing import Any, Tuple

import httpx
import requests
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageOps

from app.config import GlibatreeConfig, get_settings
from app.schemas import PosterImage, PosterInput


logger = logging.getLogger(__name__)

OPENAI_IMAGE_SIZE = "1024x1024"


def generate_poster_asset(poster: PosterInput, prompt: str, preview: str) -> PosterImage:
    """Generate a poster image via Glibatree or a local fallback."""

    settings = get_settings()
    if settings.glibatree.is_configured:
        try:
            if settings.glibatree.use_openai_client:
                logger.debug("Requesting Glibatree asset via OpenAI client")
                return _request_glibatree_openai(settings.glibatree, prompt)
            logger.debug("Requesting Glibatree asset via HTTP endpoint %s", settings.glibatree.api_url)
            return _request_glibatree_http(
                settings.glibatree.api_url or "",
                settings.glibatree.api_key or "",
                prompt,
            )
        except Exception:
            logger.exception("Glibatree request failed, falling back to mock poster")
            # Fall back to mocked asset in case of network/API errors.
            pass
    return _generate_mock_poster(poster, preview)


def _request_glibatree_http(api_url: str, api_key: str, prompt: str) -> PosterImage:
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

    return PosterImage(
        filename=filename,
        media_type=media_type,
        data_url=data_url,
        width=width,
        height=height,
    )


def _request_glibatree_openai(config: GlibatreeConfig, prompt: str) -> PosterImage:
    """Request a poster asset via the OpenAI 1.x client with optional proxy support."""

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

    with ExitStack() as stack:
        if http_client is not None:
            stack.callback(http_client.close)

        client = OpenAI(**client_kwargs)
        response = client.images.generate(
            model=config.model or "gpt-image-1",
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

    media_type = getattr(image, "mime_type", None) or "image/png"
    filename = getattr(image, "filename", None) or "poster.png"
    width_attr = getattr(image, "width", None)
    height_attr = getattr(image, "height", None)
    if isinstance(width_attr, int) and isinstance(height_attr, int) and width_attr > 0 and height_attr > 0:
        width, height = width_attr, height_attr
    else:
        width, height = _parse_image_size(getattr(image, "size", None) or OPENAI_IMAGE_SIZE)

    data_url = f"data:{media_type};base64,{b64_data}"

    return PosterImage(
        filename=filename,
        media_type=media_type,
        data_url=data_url,
        width=width,
        height=height,
    )


def _parse_image_size(size: str) -> Tuple[int, int]:
    try:
        left, right = size.lower().split("x", 1)
        width = int(left)
        height = int(right)
        return max(width, 1), max(height, 1)
    except Exception:  # pragma: no cover - defensive fallback
        return 1024, 1024


def _load_image_from_data_url(data_url: str | None) -> Image.Image | None:
    """Decode a base64 data URL into a Pillow image, returning ``None`` on error.""

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


def _generate_mock_poster(poster: PosterInput, preview: str) -> PosterImage:
    """Create a placeholder poster that visualises the requested layout."""
    width, height = 1280, 720
    image = Image.new("RGB", (width, height), color=(245, 245, 245))
    draw = ImageDraw.Draw(image)
    font_title = ImageFont.load_default()
    font_body = ImageFont.load_default()
    # Top banner
    banner_height = int(height * 0.15)
    draw.rectangle([(0, 0), (width, banner_height)], fill=(230, 230, 230))
    logo_size = max(min(96, banner_height - 32), 48)
    logo_box = (40, 20, 40 + logo_size, 20 + logo_size)
    logo_image = _load_image_from_data_url(poster.brand_logo)
    if logo_image:
        _paste_image(image, logo_image, logo_box, mode="contain")
    else:
        draw.text((logo_box[0], logo_box[1]), f"Logo: {poster.brand_name}", fill=(0, 0, 0), font=font_body)

    agent_text = poster.agent_name.upper()
    draw.text(
        (width - 40 - draw.textlength(agent_text, font=font_body), 30),
        agent_text,
        fill=(0, 0, 0),
        font=font_body,
    )

    # Left scenario area
    left_width = int(width * 0.38)
    scenario_top = banner_height + 30
    scenario_bottom = height - 220
    scenario_box = (40, scenario_top, 40 + left_width, scenario_bottom)
    draw.rounded_rectangle(scenario_box, radius=26, outline=(180, 180, 180), width=4, fill=(236, 239, 243))

    scenario_image = _load_image_from_data_url(poster.scenario_asset)
    if scenario_image:
        _paste_image(image, scenario_image, scenario_box, mode="cover")
    else:
        scenario_text = textwrap.fill(f"场景: {poster.scenario_image}", width=20)
        draw.multiline_text(
            (scenario_box[0] + 20, scenario_top + 20),
            scenario_text,
            fill=(80, 80, 80),
            font=font_body,
            spacing=4,
        )


    # Right product render area
    product_left = 80 + left_width
    product_top = banner_height + 30
    product_bottom = height - 240
    product_box = (product_left, product_top, width - 60, product_bottom)
    draw.rounded_rectangle(product_box, radius=24, outline=(150, 150, 150), width=4, fill=(235, 238, 243))

    product_image = _load_image_from_data_url(poster.product_asset)
    if product_image:
        _paste_image(image, product_image, product_box, mode="contain")
    else:
        draw.text(
            (product_left + 24, product_top + 20),
            f"产品: {poster.product_name}",
            fill=(20, 20, 20),
            font=font_body,
        )

    # Feature annotations
    feature_start_y = product_top + 80
    for idx, feature in enumerate(poster.features, start=1):
        text = textwrap.fill(f"{idx}. {feature}", width=24)
        y = feature_start_y + (idx - 1) * 60
        draw.text((product_left + 32, y), text, fill=(40, 40, 40), font=font_body)

    # Title and subtitle
    title_y = height - 240
    draw.text((40, title_y), poster.title, fill=(220, 20, 60), font=font_title)
    subtitle_y = height - 50
    draw.text((40, subtitle_y), poster.subtitle, fill=(220, 20, 60), font=font_title)

    # Series section at bottom
    series_top = height - 170
    series_bottom = height - 70
    series_box = (40, series_top, width - 40, series_bottom)
    draw.rounded_rectangle(series_box, radius=18, outline=(210, 210, 210), width=3, fill=(248, 248, 248))

    gallery_images = [
        _load_image_from_data_url(asset)
        for asset in poster.gallery_assets[:4]
    ]
    gallery_images = [img for img in gallery_images if img is not None]

    if gallery_images:
        gallery_count = max(len(gallery_images), 3)
        gallery_left = series_box[0] + 20
        gallery_right = series_box[2] - 20
        gallery_top = series_top + 14
        gallery_bottom = series_top + 70
        total_width = gallery_right - gallery_left
        spacing = 16
        slot_width = (total_width - spacing * (gallery_count - 1)) // gallery_count
        slot_height = max(gallery_bottom - gallery_top, 1)

        for index in range(gallery_count):
            slot_left = gallery_left + index * (slot_width + spacing)
            slot_right = slot_left + slot_width
            box = (slot_left, gallery_top, slot_right, gallery_top + slot_height)
            draw.rounded_rectangle(box, radius=12, outline=(180, 180, 180), width=2, fill=(240, 240, 240))
            if index < len(gallery_images):
                _paste_image(image, gallery_images[index], box, mode="cover")

        series_text_y = gallery_bottom + 10
    else:
        series_text_y = series_top + 20

    series_text = textwrap.fill(poster.series_description, width=60)
    draw.text((series_box[0] + 20, series_text_y), series_text, fill=(90, 90, 90), font=font_body)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    base64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
    data_url = f"data:image/png;base64,{base64_data}"

    return PosterImage(
        filename="mock_poster.png",
        media_type="image/png",
        data_url=data_url,
        width=width,
        height=height,
    )

