from __future__ import annotations

import re
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_BASE64_RE = re.compile(r'"(?:image|data)[^"]*?base64,', re.IGNORECASE)


class RejectHugeOrBase64(BaseHTTPMiddleware):
    """
    拒绝过大的请求体，或包含 base64 图片的数据。
    - 以应用层返回 413/400，避免占用带宽与内存。
    - 仅拦截 POST/PUT/PATCH；GET/DELETE 跳过。
    """

    def __init__(
        self,
        app,
        *,
        max_bytes: int = 4 * 1024 * 1024,
        check_base64: bool = True,
    ) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes
        self.check_base64 = check_base64

    async def dispatch(self, request: Request, call_next: Callable):
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        body = await request.body()
        if self.max_bytes and len(body) > self.max_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": "Payload too large or contains base64 image. "
                    "Upload assets to R2 first and send only key/url."
                },
            )

        if self.check_base64 and body:
            try:
                text = body.decode("utf-8", errors="ignore")
                if _BASE64_RE.search(text):
                    return JSONResponse(
                        status_code=400,
                        content={
                            "detail": "Payload contains base64 image. "
                            "Upload assets to R2 and send only key/url."
                        },
                    )
            except Exception:
                # 不阻断非 UTF-8 的情况
                pass

        return await call_next(request)


class BodyGuardMiddleware(RejectHugeOrBase64):
    """Backwards-compatible alias."""

    def __init__(self, app, *, max_bytes: int, allow_base64: bool = False) -> None:
        super().__init__(
            app,
            max_bytes=max_bytes,
            check_base64=not allow_base64,
        )


__all__ = ["RejectHugeOrBase64", "BodyGuardMiddleware"]
