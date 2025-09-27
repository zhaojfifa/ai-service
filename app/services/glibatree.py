from __future__ import annotations

import base64
import textwrap
from io import BytesIO
from typing import Any

import requests
from PIL import Image, ImageDraw, ImageFont

from app.config import get_settings
from app.schemas import PosterImage, PosterInput


def generate_poster_asset(poster: PosterInput, prompt: str, preview: str) -> PosterImage:
    """Generate a poster image via Glibatree or a local fallback."""

    settings = get_settings()
    if settings.glibatree.is_configured:
        try:
            return _request_glibatree_asset(settings.glibatree.api_url, settings.glibatree.api_key, prompt)
        except Exception:  # pragma: no cover - fallback guarantees resilience
            # Fall back to mocked asset in case of network/API errors.
            pass
    return _generate_mock_poster(poster, preview)


def _request_glibatree_asset(api_url: str, api_key: str, prompt: str) -> PosterImage:
    """Call the remote Glibatree API and transform the result into PosterImage."""

    response = requests.post(
        api_url,
        headers={"Authorization": f"Bearer {api_key}"},
        json={"prompt": prompt},
        timeout=60,
    )
    response.raise_for_status()
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


def _generate_mock_poster(poster: PosterInput, preview: str) -> PosterImage:
    """Create a placeholder poster that visualises the requested layout."""

    width, height = 1280, 720
    image = Image.new("RGB", (width, height), color=(245, 245, 245))
    draw = ImageDraw.Draw(image)
    font_title = ImageFont.load_default()
    font_body = ImageFont.load_default()

    # Top banner
    banner_height = int(height * 0.12)
    draw.rectangle([(0, 0), (width, banner_height)], fill=(230, 230, 230))
    draw.text((40, 20), f"Logo: {poster.brand_name}", fill=(0, 0, 0), font=font_body)
    agent_text = poster.agent_name.upper()
    draw.text(
        (width - 40 - draw.textlength(agent_text, font=font_body), 20),
        agent_text,
        fill=(0, 0, 0),
        font=font_body,
    )

    # Left scenario area
    left_width = int(width * 0.38)
    draw.rectangle([(40, banner_height + 20), (40 + left_width, height - 160)], outline=(180, 180, 180), width=4)
    scenario_text = textwrap.fill(f"场景: {poster.scenario_image}", width=20)
    draw.multiline_text((60, banner_height + 40), scenario_text, fill=(80, 80, 80), font=font_body, spacing=4)

    # Right product render area
    product_left = 80 + left_width
    draw.rectangle([(product_left, banner_height + 20), (width - 40, height - 220)], outline=(150, 150, 150), width=4)
    draw.text((product_left + 20, banner_height + 40), f"产品: {poster.product_name}", fill=(20, 20, 20), font=font_body)

    # Feature annotations
    feature_start_y = banner_height + 100
    for idx, feature in enumerate(poster.features, start=1):
        text = textwrap.fill(f"{idx}. {feature}", width=24)
        y = feature_start_y + (idx - 1) * 60
        draw.text((product_left + 20, y), text, fill=(40, 40, 40), font=font_body)

    # Title and subtitle
    title_y = height - 210
    draw.text((40, title_y), poster.title, fill=(220, 20, 60), font=font_title)
    subtitle_y = height - 60
    draw.text((40, subtitle_y), poster.subtitle, fill=(220, 20, 60), font=font_title)

    # Series section at bottom
    series_top = height - 150
    draw.rectangle([(40, series_top), (width - 40, series_top + 80)], outline=(210, 210, 210), width=3)
    series_text = textwrap.fill(poster.series_description, width=60)
    draw.text((60, series_top + 20), series_text, fill=(90, 90, 90), font=font_body)

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

