# app/services/glibatree.py
from __future__ import annotations

import base64
import io
import os
from typing import Tuple

try:
    import httpx  # 用于代理/自定义超时
except ModuleNotFoundError as e:
    raise RuntimeError("Missing dependency 'httpx'. Run: pip install httpx") from e

from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

from app.schemas import PosterImage, PosterInput

# 供测试与业务共用的常量
OPENAI_IMAGE_SIZE = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024")


# ----------------------------- OpenAI client ------------------------------ #
def _parse_size(size: str) -> Tuple[int, int]:
    w, h = size.lower().split("x")
    return int(w), int(h)


def _get_openai_client() -> OpenAI:
    """
    创建 OpenAI 客户端。
    - 支持通过环境变量 OPENAI_BASE_URL / OPENAI_API_KEY / OPENAI_MODEL
    - 支持从 HTTP(S)_PROXY 注入代理（OpenAI SDK v1 需通过 http_client 注入）
    """
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")

    if http_proxy or https_proxy:
        proxies = {}
        if http_proxy:
            proxies["http"] = http_proxy
        if https_proxy:
            proxies["https"] = https_proxy
        http_client = httpx.Client(proxies=proxies, timeout=60)
        return OpenAI(api_key=key, base_url=base, http_client=http_client)

    return OpenAI(api_key=key, base_url=base)


# ----------------------------- OpenAI backend ----------------------------- #
def _request_glibatree_openai(poster: PosterInput, prompt: str, preview: str) -> PosterImage:
    """
    调用 OpenAI 图像生成（示例用 gpt-image-1）。
    返回 PosterImage（data_url 内含 base64）。
    """
    client = _get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-image-1")
    size = OPENAI_IMAGE_SIZE
    width, height = _parse_size(size)

    # OpenAI Images API（SDK v1）
    resp = client.images.generate(
        model=model,
        prompt=prompt,
        size=size,
    )
    image_b64 = resp.data[0].b64_json  # SDK v1 字段名

    return PosterImage(
        filename="poster_openai.png",
        media_type="image/png",
        width=width,
        height=height,
        data_url=f"data:image/png;base64,{image_b64}",
    )


# --------------------------- Mock / 占位图后备 ---------------------------- #
def _draw_multiline(draw: ImageDraw.ImageDraw, xy, text: str, font, fill, max_width: int):
    """
    极简断行：按空格切分，超过宽度就换行。
    """
    words = text.split()
    lines = []
    line = ""
    for w in words:
        trial = (line + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)

    x, y = xy
    lh = font.size + 4
    for ln in lines:
        draw.text((x, y), ln, font=font, fill=fill)
        y += lh


def _generate_mock_image(poster: PosterInput, prompt: str, preview: str) -> PosterImage:
    """
    生成占位海报：用于未配置真实图像后端时的可视化回退。
    - 顶部横条：品牌 + 代理
    - 左侧灰底代表“场景图”
    - 右侧浅底代表“产品图”+ 功能点文本
    - 中部标题、底部系列说明、右下副标题
    """
    width, height = _parse_size(OPENAI_IMAGE_SIZE)
    img = Image.new("RGB", (width, height), (248, 250, 252))
    draw = ImageDraw.Draw(img)

    # 字体（平台上没有系统字体时，用默认）
    try:
        font_bold = ImageFont.truetype("arial.ttf", size=36)
        font_text = ImageFont.truetype("arial.ttf", size=22)
        font_small = ImageFont.truetype("arial.ttf", size=18)
    except Exception:
        font_bold = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 顶部横条
    header_h = int(height * 0.1)
    draw.rectangle((32, 32, width - 32, 32 + header_h), fill=(255, 240, 241), outline=(239, 76, 84))
    draw.text((48, 48), f"{poster.brand_name}", font=font_bold, fill=(31, 41, 51))
    draw.text((width - 48 - draw.textlength(poster.agent_name, font=font_small), 48),
              poster.agent_name, font=font_small, fill=(31, 41, 51))

    # 主体两栏
    body_top = 48 + header_h + 24
    gutter = 24
    left_w = int(width * 0.4) - 64
    right_x = 32 + left_w + gutter
    # 左侧“场景图”
    draw.rectangle((32, body_top, 32 + left_w, height - 220), fill=(229, 233, 240), outline=(200, 210, 220))
    _draw_multiline(draw, (48, body_top + 16), poster.scenario_image or "应用场景图", font_small, (80, 90, 100), left_w - 32)

    # 右侧“产品 + 功能点”
    draw.rectangle((right_x, body_top, width - 32, height - 220), fill=(235, 239, 245), outline=(200, 210, 220))
    _draw_multiline(draw, (right_x + 16, body_top + 16), poster.product_name or "主产品 45° 渲染图", font_text,
                    (30, 30, 30), (width - 32) - (right_x + 32))
    y = body_top + 70
    for i, feat in enumerate(poster.features[:4], start=1):
        _draw_multiline(draw, (right_x + 16, y), f"{i}. {feat}", font_small, (30, 30, 30),
                        (width - 32) - (right_x + 32))
        y += font_small.size + 10

    # 标题
    draw.text((32, height - 210), poster.title, font=font_bold, fill=(239, 76, 84))
    # 底部“系列说明”
    _draw_multiline(draw, (32, height - 170), poster.series_description, font_small, (82, 96, 109), width - 64)
    # 右下“副标题”
    sub_w = draw.textlength(poster.subtitle, font=font_bold)
    draw.text((width - 32 - sub_w, height - 60), poster.subtitle, font=font_bold, fill=(239, 76, 84))

    # 输出为 base64 data URL
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return PosterImage(
        filename="poster_mock.png",
        media_type="image/png",
        width=width,
        height=height,
        data_url=f"data:image/png;base64,{b64}",
    )


# ------------------------------- Facade ----------------------------------- #
def generate_poster_asset(poster: PosterInput, prompt: str, preview: str) -> PosterImage:
    """
    统一入口：
    - 如果 IMAGE_BACKEND=openai 且配置了 OPENAI_API_KEY，则走 OpenAI 生成。
    - 否则返回占位图（Mock），保证流程不阻塞。
    """
    backend = os.getenv("IMAGE_BACKEND", "").lower()
    if backend == "openai" and os.getenv("OPENAI_API_KEY"):
        try:
            return _request_glibatree_openai(poster, prompt, preview)
        except Exception as e:
            # 失败回退占位图，同时把异常拼进 alt 内容方便排查
            return _generate_mock_image(
                poster,
                prompt,
                preview + f"\n[openai-error]: {e}"
            )
    return _generate_mock_image(poster, prompt, preview)
