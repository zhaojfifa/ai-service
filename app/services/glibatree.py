# app/services/glibatree.py
from __future__ import annotations

import base64
import textwrap
from io import BytesIO
from typing import Any, Tuple

import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

from app.config import get_settings
from app.schemas import PosterImage, PosterInput


def generate_poster_asset(poster: PosterInput, prompt: str, preview: str) -> PosterImage:
    """
    优先调用 Glibatree 服务生成；若未配置或出错，则回退到本地占位图生成，
    以确保前后端流程不被阻断。
    """
    settings = get_settings()
    if getattr(settings, "glibatree", None) and settings.glibatree.is_configured:
        try:
            return _request_glibatree_asset(settings.glibatree.api_url, settings.glibatree.api_key, prompt)
        except Exception:
            # 网络/鉴权/格式异常时，回退到本地占位图
            pass
    return _generate_mock_poster(poster, preview)


def _request_glibatree_asset(api_url: str, api_key: str, prompt: str) -> PosterImage:
    """调用 Glibatree API 并转换为 PosterImage。"""
    response = requests.post(
        api_url,
        headers={"Authorization": f"Bearer {api_key}"},
        json={"prompt": prompt},
        timeout=60,
    )
    response.raise_for_status()
    payload: dict[str, Any] = response.json()

    # 兼容多种返回
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


def _load_image_from_data_url(data_url: str | None) -> Image.Image | None:
    """把 base64 data URL 解码为 Pillow Image（失败返回 None）。"""
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


# Pillow >=10 使用 Image.Resampling；向下兼容旧版本
try:
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
except AttributeError:  # pragma: no cover
    RESAMPLE_LANCZOS = Image.LANCZOS


def _paste_image(
    canvas: Image.Image,
    asset: Image.Image,
    box: Tuple[int, int, int, int],
    *,
    mode: str = "contain",
) -> None:
    """把 asset 按 box 尺寸粘贴到 canvas，保持比例；mode 支持 contain/cover。"""
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
    """
    生成占位海报：可视化版式（顶部横条 / 左侧场景 / 右侧产品 / 功能点 / 标题副标题 / 底部系列小图）。
    若上传了 data URL 图片，会嵌入到相应区域。
    """
    width, height = 1280, 720
    image = Image.new("RGB", (width, height), color=(245, 245, 245))
    draw = ImageDraw.Draw(image)
    font_title = ImageFont.load_default()
    font_body = ImageFont.load_default()

    # 顶部横条
    banner_height = int(height * 0.15)
    draw.rectangle([(0, 0), (width, banner_height)], fill=(230, 230, 230))

    # 左侧 Logo（支持图片）
    logo_size = max(min(96, banner_height - 32), 48)
    logo_box = (40, 20, 40 + logo_size, 20 + logo_size)
    logo_image = _load_image_from_data_url(getattr(poster, "brand_logo", None))
    if logo_image:
        _paste_image(image, logo_image, logo_box, mode="contain")
    else:
        draw.text((logo_box[0], logo_box[1]), f"Logo: {poster.brand_name}", fill=(0, 0, 0), font=font_body)

    # 右上角品牌/代理名
    agent_text = (getattr(poster, "agent_name", None) or poster.brand_name or "").upper()
    draw.text(
        (width - 40 - draw.textlength(agent_text, font=font_body), 30),
        agent_text,
        fill=(0, 0, 0),
        font=font_body,
    )

    # 左侧场景区域
    left_width = int(width * 0.38)
    scenario_top = banner_height + 30
    scenario_bottom = height - 220
    scenario_box = (40, scenario_top, 40 + left_width, scenario_bottom)
    draw.rounded_rectangle(scenario_box, radius=26, outline=(180, 180, 180), width=4, fill=(236, 239, 243))

    scenario_image = _load_image_from_data_url(getattr(poster, "scenario_asset", None))
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

    # 右侧产品区域
    product_left = 80 + left_width
    product_top = banner_height + 30
    product_bottom = height - 240
    product_box = (product_left, product_top, width - 60, product_bottom)
    draw.rounded_rectangle(product_box, radius=24, outline=(150, 150, 150), width=4, fill=(235, 238, 243))

    product_image = _load_image_from_data_url(getattr(poster, "product_asset", None))
    if product_image:
        _paste_image(image, product_image, product_box, mode="contain")
    else:
        draw.text(
            (product_left + 24, product_top + 20),
            f"产品: {poster.product_name}",
            fill=(20, 20, 20),
            font=font_body,
        )

    # 功能点标注（靠近产品区）
    feature_start_y = product_top + 80
    for idx, feature in enumerate(poster.features or [], start=1):
        text = textwrap.fill(f"{idx}. {feature}", width=24)
        y = feature_start_y + (idx - 1) * 60
        draw.text((product_left + 32, y), text, fill=(40, 40, 40), font=font_body)

    # 中部标题 / 右下副标题
    title_y = height - 240
    draw.text((40, title_y), poster.title, fill=(220, 20, 60), font=font_title)
    subtitle_y = height - 50
    draw.text((40, subtitle_y), poster.subtitle, fill=(220, 20, 60), font=font_title)

    # 底部系列区（小图 + 文案）
    series_top = height - 170
    series_bottom = height - 70
    series_box = (40, series_top, width - 40, series_bottom)
    draw.rounded_rectangle(series_box, radius=18, outline=(210, 210, 210), width=3, fill=(248, 248, 248))

    gallery_images = [
        _load_image_from_data_url(asset) for asset in (poster.gallery_assets or [])[:4]
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
        # 没有小图时，仅显示系列文案
        series_text_y = series_top + 20

    series_text = textwrap.fill(poster.series_description or "", width=60)
    draw.text((series_box[0] + 20, series_text_y), series_text, fill=(90, 90, 90), font=font_body)

    # 输出 base64 data URL
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
