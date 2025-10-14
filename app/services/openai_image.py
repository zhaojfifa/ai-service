# app/services/openai_image.py
# -*- coding: utf-8 -*-
"""
Thin OpenAI image-generation helper used by tools/tests.
- Uses a safe OpenAI client factory (httpx proxy injected via http_client).
- Falls back to raw HTTP /v1/images/generations if the SDK call fails.
"""

from __future__ import annotations

import base64
import logging
from typing import Optional, Any
from uuid import uuid4

import httpx
from openai import OpenAI

logger = logging.getLogger(__name__)

# 仅允许传给 OpenAI SDK 的关键字（防止混入 proxies 等不被支持的参数）
_ALLOWED_OPENAI_KWARGS = {"api_key", "base_url", "timeout", "max_retries", "http_client"}


def _sanitize_openai_kwargs(kw: dict[str, Any]) -> dict[str, Any]:
    cleaned = {k: v for k, v in kw.items() if k in _ALLOWED_OPENAI_KWARGS}
    for k in set(kw) - _ALLOWED_OPENAI_KWARGS:
        if k.lower() == "proxies":
            logger.warning("Removed unsupported OpenAI kwarg 'proxies' from client kwargs")
        else:
            logger.debug("Removed unsupported OpenAI kwarg '%s' from client kwargs", k)
    return cleaned


def _build_openai_client(
    api_key: str,
    *,
    base_url: Optional[str] = None,
    proxy: Optional[str] = None,
) -> tuple[OpenAI, Optional[httpx.Client]]:
    """
    统一构建 OpenAI 客户端：
      - 代理只放在 httpx.Client(proxies=...)，通过 http_client 注入 SDK
      - 其它额外键一律丢弃（白名单）
      - 返回 (client, http_client)，调用方负责关闭 http_client
    """
    if not api_key:
        raise ValueError("OPENAI_API_KEY 未配置。")

    kw: dict[str, Any] = {"api_key": api_key}
    if base_url:
        kw["base_url"] = base_url

    http_client: httpx.Client | None = None
    if proxy:
        timeout = httpx.Timeout(60.0, connect=10.0, read=60.0)
        http_client = httpx.Client(proxies=proxy, timeout=timeout)
        kw["http_client"] = http_client

    kw = _sanitize_openai_kwargs(kw)
    return OpenAI(**kw), http_client


def _openai_images_generate_via_httpx(
    api_key: str,
    prompt: str,
    size: str,
    *,
    base_url: Optional[str] = None,
    proxy: Optional[str] = None,
    model: str = "gpt-image-1",
) -> str:
    """
    直接调用 REST /v1/images/generations（HTTP 兜底），返回 b64_json（不含 data: 前缀）。
    """
    if not api_key:
        raise ValueError("OPENAI_API_KEY 未配置。")
    root = (base_url or "https://api.openai.com/v1").rstrip("/")

    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "response_format": "b64_json",
    }
    timeout = httpx.Timeout(60.0, connect=10.0, read=60.0)
    with httpx.Client(proxies=proxy, timeout=timeout) as cli:
        r = cli.post(
            f"{root}/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
        if not data.get("data"):
            raise RuntimeError(f"OpenAI images/generations empty response: {data}")
        return data["data"][0]["b64_json"]


def generate_image_with_openai(
    prompt: str,
    api_key: str,
    base_url: Optional[str] = None,
    size: str = "1024x1024",
    *,
    proxy: Optional[str] = None,
    model: str = "gpt-image-1",
) -> str:
    """
    调用 OpenAI 图片模型生成海报，返回在容器 /tmp 下保存的 PNG 文件路径。
    - 优先使用 OpenAI Python SDK（注入 httpx.Client）
    - 若 SDK 因参数/版本差异抛 TypeError，自动切 HTTP 兜底
    """
    # 1) 优先走 SDK
    try:
        from contextlib import ExitStack

        with ExitStack() as stack:
            client, http_client = _build_openai_client(api_key, base_url=base_url, proxy=proxy)
            if http_client is not None:
                stack.callback(http_client.close)

            resp = client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                response_format="b64_json",  # 显式请求 b64_json，避免字段缺省
                # quality="high"  # 新版 SDK/后端不一定支持该参数，去掉可提升兼容性
            )
            if not resp.data:
                raise ValueError("OpenAI images.generate 空响应")
            b64_png = getattr(resp.data[0], "b64_json", None)
            if not b64_png:
                raise ValueError("OpenAI images.generate 缺少 b64_json")
    except TypeError as e:
        # 2) SDK 不兼容时，使用 HTTP 兜底
        logger.exception("OpenAI SDK images.generate failed, fallback to raw HTTP: %s", e)
        b64_png = _openai_images_generate_via_httpx(
            api_key, prompt, size, base_url=base_url, proxy=proxy, model=model
        )

    # 写入 /tmp
    img_bytes = base64.b64decode(b64_png)
    out_path = f"/tmp/poster_{uuid4().hex}.png"
    with open(out_path, "wb") as f:
        f.write(img_bytes)
    return out_path
