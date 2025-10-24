"""Request body guards for API endpoints."""
from __future__ import annotations

import logging
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

DEFAULT_MAX_BYTES = int(os.getenv("MAX_JSON_BODY", "1048576"))  # 1 MiB default

logger = logging.getLogger("ai-service.body-guard")


class RejectHugeOrBase64(BaseHTTPMiddleware):
    """Reject oversized requests or inline base64 images on API routes."""

    def __init__(self, app, max_bytes: int | None = None) -> None:  # type: ignore[override]
        super().__init__(app)
        self.max_bytes = max_bytes if max_bytes is not None else DEFAULT_MAX_BYTES

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if request.url.path.startswith("/api/"):
            body = await request.body()
            body_len = len(body)

            if self.max_bytes and body_len > self.max_bytes:
                logger.warning(
                    "Rejecting oversized request", extra={
                        "path": request.url.path,
                        "method": request.method,
                        "bytes": body_len,
                        "limit": self.max_bytes,
                    }
                )
                detail = (
                    "请求体过大（实际 %d bytes，上限 %d bytes）。请先上传素材到 R2，仅传输 key/url。"
                    % (body_len, self.max_bytes)
                )
                return JSONResponse({"detail": detail}, status_code=413)

            lowered = body.lower()
            if b"data:image" in lowered or b"base64," in lowered:
                logger.warning(
                    "Rejecting base64 payload", extra={
                        "path": request.url.path,
                        "method": request.method,
                        "bytes": body_len,
                    }
                )
                detail = (
                    "检测到 base64 图片（%d bytes）。请先上传素材到 R2，仅传输 key/url。"
                    % body_len
                )
                return JSONResponse({"detail": detail}, status_code=422)

        return await call_next(request)
