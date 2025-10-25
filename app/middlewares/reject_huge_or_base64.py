from __future__ import annotations

import json
import logging
import os
import re
from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("ai-service")

MAX_BODY_BYTES = int(os.getenv("MAX_BODY_BYTES", "2097152"))
MAX_INLINE_BASE64_BYTES = int(os.getenv("MAX_INLINE_BASE64_BYTES", "131072"))

DATA_URL_RE = re.compile(
    r"data:image/(?:png|jpeg|jpg|webp|gif);base64,[A-Za-z0-9+/=\s]{256,}",
    re.IGNORECASE,
)
LONG_BASE64_CHUNK_RE = re.compile(r"[A-Za-z0-9+/]{8000,}={0,2}")

def _too_large(content_length: int | None, body_len: int) -> bool:
    if content_length is not None and content_length > MAX_BODY_BYTES:
        return True
    return body_len > MAX_BODY_BYTES

def _contains_big_base64(body: bytes) -> bool:
    if DATA_URL_RE.search(body.decode(errors="ignore")):
        return True
    if len(body) <= MAX_INLINE_BASE64_BYTES:
        return False
    return LONG_BASE64_CHUNK_RE.search(body.decode(errors="ignore")) is not None

class RejectHugeOrBase64(BaseHTTPMiddleware):
    """
    拦截过大的请求体，或包含大块 base64 图像的请求；
    指引前端先把素材上传 R2，仅传 key/url。
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.method in {"POST", "PUT", "PATCH"}:
            ctype = (request.headers.get("content-type") or "").lower()
            if any(t in ctype for t in ("application/json", "multipart/form-data", "application/x-www-form-urlencoded")):
                body = await request.body()
                cl = request.headers.get("content-length")
                content_length = int(cl) if cl and cl.isdigit() else None

                too_big = _too_large(content_length, len(body))
                has_b64 = _contains_big_base64(body)

                if too_big or has_b64:
                    logger.warning(
                        "[reject.body] too_big=%s has_b64=%s clen=%s body=%s",
                        too_big,
                        has_b64,
                        content_length,
                        len(body),
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": "请求体过大或包含 base64 图片，请先上传素材到 R2，仅传输 key/url。",
                            "hints": {
                                "upload": "将图片文件先上传到 R2，得到 key 与公开/签名 URL；再把 key/url 放到请求 JSON 中。",
                                "limits": {
                                    "MAX_BODY_BYTES": MAX_BODY_BYTES,
                                    "MAX_INLINE_BASE64_BYTES": MAX_INLINE_BASE64_BYTES,
                                },
                            },
                        },
                    )
                request._body = body  # noqa: SLF001

        return await call_next(request)
