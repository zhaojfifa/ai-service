from __future__ import annotations

import logging
import os
import re
import time
import uuid
from typing import Any, Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("ai-service")

# 环境变量可调；给出合理默认
MAX_BODY_BYTES = int(os.getenv("MAX_BODY_BYTES", "2097152"))  # 2 MiB
MAX_INLINE_BASE64_BYTES = int(os.getenv("MAX_INLINE_BASE64_BYTES", "131072"))  # 128 KiB

DATA_URL_RE = re.compile(r"data:image/(?:png|jpe?g|webp|gif);base64,[A-Za-z0-9+/=\s]{256,}", re.I)
LONG_BASE64_CHUNK_RE = re.compile(r"[A-Za-z0-9+/]{8000,}={0,2}")


class RejectHugeOrBase64(BaseHTTPMiddleware):
    """Reject requests with oversized bodies or large inline base64 payloads."""

    WATCH_PATH_PREFIXES = ("/api/", "/imagen", "/images", "/upload")

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
        if request.method not in {"POST", "PUT", "PATCH"}:
            return await call_next(request)

        path = request.url.path
        if not any(path.startswith(prefix) for prefix in self.WATCH_PATH_PREFIXES):
            return await call_next(request)

        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        start = time.time()

        content_length_header = request.headers.get("content-length")
        try:
            content_length = int(content_length_header) if content_length_header else None
        except (TypeError, ValueError):
            content_length = None

        body = await request.body()
        size = len(body)
        preview = body[:200].decode(errors="ignore")

        reason = None
        if self._too_large(content_length, size):
            reason = f"oversize:{size}"
        else:
            try:
                full_text = body.decode(errors="ignore")
            except Exception:  # pragma: no cover - extremely rare decode failure
                full_text = preview
            if self._contains_big_base64(body) or DATA_URL_RE.search(full_text):
                reason = "base64"

        logger.info(
            "[guard] rid=%s path=%s method=%s cl=%s size=%s reason=%s preview=%r",
            rid,
            path,
            request.method,
            content_length_header,
            size,
            reason,
            preview,
        )

        if reason:
            status_code = 413 if reason.startswith("oversize") else 422
            return JSONResponse(
                status_code=status_code,
                content={
                    "ok": False,
                    "error": "REQUEST_BODY_BLOCKED",
                    "reason": reason,
                    "hint": "请先上传到 R2/GCS，后续仅传 key/url。",
                },
            )

        async def receive() -> dict[str, Any]:
            return {"type": "http.request", "body": body, "more_body": False}

        response = await call_next(Request(request.scope, receive))
        duration_ms = int((time.time() - start) * 1000)
        logger.info(
            "[guard] rid=%s done status=%s dur_ms=%s",
            rid,
            response.status_code,
            duration_ms,
        )
        return response
