from __future__ import annotations

import json
import re
from json import JSONDecodeError
from typing import Any, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_BASE64_RE = re.compile(r"data:image/[^;]+;base64,", re.IGNORECASE)


def _scan_for_base64(payload: Any) -> bool:
    """Recursively search ``payload`` for inline base64 image markers."""

    if payload is None:
        return False
    if isinstance(payload, str):
        return bool(_BASE64_RE.search(payload))
    if isinstance(payload, dict):
        return any(_scan_for_base64(value) for value in payload.values())
    if isinstance(payload, (list, tuple, set)):
        return any(_scan_for_base64(item) for item in payload)
    return False


class RejectHugeOrBase64(BaseHTTPMiddleware):
    """拦截超大或包含 base64 图片的请求体，提示走 R2 直传流程。"""

    def __init__(
        self,
        app,
        *,
        max_bytes: int = 4 * 1024 * 1024,
        allow_base64: bool = False,
    ) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes
        self.allow_base64 = allow_base64

    async def dispatch(self, request: Request, call_next: Callable):
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        if self.max_bytes:
            try:
                length_header = request.headers.get("content-length")
                if length_header and int(length_header) > self.max_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": "Payload exceeds limit. Upload to R2 and send key/url instead.",
                            "limit_bytes": self.max_bytes,
                        },
                    )
            except ValueError:
                # Ignore malformed header and fall back to actual body length.
                pass

        body = await request.body()
        if hasattr(request, "_body"):
            request._body = body  # type: ignore[attr-defined]

        if self.max_bytes and len(body) > self.max_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": "Payload exceeds limit. Upload to R2 and send key/url instead.",
                    "limit_bytes": self.max_bytes,
                },
            )

        if self.allow_base64 or not body:
            return await call_next(request)

        parsed: Any
        try:
            parsed = json.loads(body)
        except JSONDecodeError:
            try:
                text = body.decode("utf-8", errors="ignore")
            except Exception:
                text = ""
            if _BASE64_RE.search(text):
                return JSONResponse(
                    status_code=422,
                    content={
                        "detail": "Inline base64 uploads are disabled. Upload to R2 and provide key/url.",
                        "reason": "base64_inline_blocked",
                    },
                )
            return await call_next(request)

        if _scan_for_base64(parsed):
            return JSONResponse(
                status_code=422,
                content={
                    "detail": "Inline base64 uploads are disabled. Upload to R2 and provide key/url.",
                    "reason": "base64_inline_blocked",
                },
            )

        return await call_next(request)


class BodyGuardMiddleware(RejectHugeOrBase64):
    """Backwards-compatible alias."""

    def __init__(self, app, *, max_bytes: int, allow_base64: bool = False) -> None:
        super().__init__(app, max_bytes=max_bytes, allow_base64=allow_base64)


__all__ = ["RejectHugeOrBase64", "BodyGuardMiddleware"]
