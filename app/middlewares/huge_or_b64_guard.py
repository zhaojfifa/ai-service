from __future__ import annotations

import json
import re
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse
from starlette.status import HTTP_413_REQUEST_ENTITY_TOO_LARGE

_B64_RE = re.compile(r"^data:image/[a-zA-Z0-9.+-]+;base64,", re.IGNORECASE)


def _contains_base64(obj: Any) -> bool:
    try:
        if isinstance(obj, dict):
            return any(_contains_base64(v) for v in obj.values())
        if isinstance(obj, list):
            return any(_contains_base64(v) for v in obj)
        if isinstance(obj, str):
            if _B64_RE.match(obj.strip()):
                return True
    except Exception:
        return False
    return False


class RejectHugeOrBase64(BaseHTTPMiddleware):
    """Reject JSON bodies that are too large or contain base64 data URLs."""

    def __init__(self, app, *, max_bytes: int, allow_base64: bool = False):
        super().__init__(app)
        self.max_bytes = int(max_bytes)
        self.allow_base64 = bool(allow_base64)

    async def dispatch(self, request, call_next):
        content_type = request.headers.get("content-type", "")
        if request.method in {"POST", "PUT", "PATCH"} and "application/json" in content_type:
            body = await request.body()
            if len(body) > self.max_bytes:
                return PlainTextResponse(
                    "Request entity too large. Upload images to R2 and send key/url only.",
                    status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                )

            if not self.allow_base64 and body:
                try:
                    payload = json.loads(body.decode("utf-8"))
                except Exception:
                    payload = None
                if payload is not None and _contains_base64(payload):
                    return PlainTextResponse(
                        "Payload contains base64 image. Upload to R2 first and send key/url only.",
                        status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    )
        return await call_next(request)


class BodyGuardMiddleware(RejectHugeOrBase64):
    """Backwards-compatible alias name."""

    pass
