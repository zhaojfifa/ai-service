"""Request body guards for API endpoints."""
from __future__ import annotations

import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

DEFAULT_MAX_BYTES = int(os.getenv("MAX_JSON_BODY", "1048576"))  # 1 MiB default


class RejectHugeOrBase64(BaseHTTPMiddleware):
    """Reject oversized requests or inline base64 images on API routes."""

    def __init__(self, app, max_bytes: int | None = None) -> None:  # type: ignore[override]
        super().__init__(app)
        self.max_bytes = max_bytes if max_bytes is not None else DEFAULT_MAX_BYTES

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if request.url.path.startswith("/api/"):
            body = await request.body()
            if self.max_bytes and len(body) > self.max_bytes:
                return JSONResponse(
                    {"detail": "Request too large. Upload files to R2 and send key/url only."},
                    status_code=413,
                )
            lowered = body.lower()
            if b"data:image" in lowered or b"base64," in lowered:
                return JSONResponse(
                    {
                        "detail": "Base64 images are not allowed. Upload to R2 and send key/url.",
                    },
                    status_code=422,
                )
        return await call_next(request)
