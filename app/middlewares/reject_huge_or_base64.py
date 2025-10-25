from __future__ import annotations

import logging
import os
import re
from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

log = logging.getLogger("ai-service")

# 环境变量可调；给出合理默认
MAX_BODY_BYTES = int(os.getenv("MAX_BODY_BYTES", "2097152"))  # 2 MiB
MAX_INLINE_BASE64_BYTES = int(os.getenv("MAX_INLINE_BASE64_BYTES", "131072"))  # 128 KiB

DATA_URL_RE = re.compile(r"data:image/(?:png|jpe?g|webp|gif);base64,[A-Za-z0-9+/=\s]{256,}", re.I)
LONG_BASE64_CHUNK_RE = re.compile(r"[A-Za-z0-9+/]{8000,}={0,2}")

def _too_large(content_length: int | None, body_len: int) -> bool:
    if content_length and content_length > MAX_BODY_BYTES:
        return True
    return body_len > MAX_BODY_BYTES

def _contains_big_base64(body: bytes) -> bool:
    if len(body) <= MAX_INLINE_BASE64_BYTES:
        return False
    s = body.decode(errors="ignore")
    return bool(DATA_URL_RE.search(s) or LONG_BASE64_CHUNK_RE.search(s))


class RejectHugeOrBase64(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method in {"POST", "PUT", "PATCH"}:
            ctype = (request.headers.get("content-type") or "").lower()
            if "json" in ctype or "multipart" in ctype or "x-www-form-urlencoded" in ctype:
                body = await request.body()
                cl = int(request.headers.get("content-length") or 0) or None
                if _too_large(cl, len(body)) or _contains_big_base64(body):
                    log.warning("Reject request: size=%s, ctype=%s", len(body), ctype)
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": "请求体过大或包含 base64 图片，请先上传素材到 R2，仅传输 key/url。",
                            "limits": {
                                "MAX_BODY_BYTES": MAX_BODY_BYTES,
                                "MAX_INLINE_BASE64_BYTES": MAX_INLINE_BASE64_BYTES,
                            },
                        },
                    )
                request._body = body  # noqa: SLF001
        return await call_next(request)
