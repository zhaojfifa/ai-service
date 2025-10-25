from __future__ import annotations

import logging
import os
import re
from typing import Any, Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

log = logging.getLogger("ai-service")

# 环境变量可调；给出合理默认
MAX_BODY_BYTES = int(os.getenv("MAX_BODY_BYTES", "2097152"))  # 2 MiB
MAX_INLINE_BASE64_BYTES = int(os.getenv("MAX_INLINE_BASE64_BYTES", "131072"))  # 128 KiB

DATA_URL_RE = re.compile(r"data:image/(?:png|jpe?g|webp|gif);base64,[A-Za-z0-9+/=\s]{256,}", re.I)
LONG_BASE64_CHUNK_RE = re.compile(r"[A-Za-z0-9+/]{8000,}={0,2}")


class RejectHugeOrBase64(BaseHTTPMiddleware):
    """Reject requests with oversized bodies or large inline base64 payloads."""

    def __init__(
        self,
        app,
        *,
        max_body_bytes: int | None = None,
        max_inline_base64_bytes: int | None = None,
        **_: Any,
    ) -> None:  # type: ignore[override]
        self.max_body_bytes = self._normalise_limit(max_body_bytes, MAX_BODY_BYTES)
        self.max_inline_base64_bytes = self._normalise_limit(
            max_inline_base64_bytes, MAX_INLINE_BASE64_BYTES
        )
        super().__init__(app)

    @staticmethod
    def _normalise_limit(candidate: int | None, fallback: int) -> int | None:
        if candidate is None:
            candidate = fallback
        if candidate <= 0:
            return None
        return candidate

    def _too_large(self, content_length: int | None, body_len: int) -> bool:
        if self.max_body_bytes is None:
            return False
        if content_length and content_length > self.max_body_bytes:
            return True
        return body_len > self.max_body_bytes

    def _contains_big_base64(self, body: bytes) -> bool:
        limit = self.max_inline_base64_bytes
        if limit is not None and len(body) <= limit:
            return False
        text = body.decode(errors="ignore")
        return bool(DATA_URL_RE.search(text) or LONG_BASE64_CHUNK_RE.search(text))

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
                if self._too_large(cl, len(body)) or self._contains_big_base64(body):
                    log.warning(
                        "Reject request: size=%s, ctype=%s, limit=%s",
                        len(body),
                        ctype,
                        self.max_body_bytes,
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": "请求体过大或包含 base64 图片，请先上传素材到 R2，仅传输 key/url。",
                            "limits": {
                                "MAX_BODY_BYTES": self.max_body_bytes,
                                "MAX_INLINE_BASE64_BYTES": self.max_inline_base64_bytes,
                            },
                        },
                    )
                request._body = body  # noqa: SLF001
        return await call_next(request)
