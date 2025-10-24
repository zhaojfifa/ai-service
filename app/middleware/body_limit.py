"""Guard incoming JSON payloads against large bodies or inline base64 images."""
from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_413_REQUEST_ENTITY_TOO_LARGE

logger = logging.getLogger("ai-service.body-guard")

DATAURL_RE = re.compile(r"data:image/[a-zA-Z0-9.+-]+;base64,", re.IGNORECASE)


class BodyGuardMiddleware(BaseHTTPMiddleware):
    """Reject API requests that exceed size limits or embed base64 image payloads."""

    def __init__(self, app, max_bytes: int = 200_000) -> None:  # type: ignore[override]
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        trace = getattr(request.state, "trace_id", None)
        if not trace:
            trace = uuid.uuid4().hex[:8]
            request.state.trace_id = trace

        guard_info: dict[str, Any] = {"trace": trace}
        request.state.guard_info = guard_info

        if request.method in {"POST", "PUT", "PATCH"} and request.headers.get(
            "content-type", ""
        ).startswith("application/json"):
            body = await request.body()
            request._body = body  # allow downstream to reuse the cached payload
            size = len(body)
            guard_info["bytes"] = size
            too_big = self.max_bytes > 0 and size > self.max_bytes
            guard_info["too_big"] = too_big

            text = body.decode("utf-8", "ignore") if body else ""
            has_b64 = bool(DATAURL_RE.search(text))
            guard_info["has_base64"] = has_b64

            logger.info(
                "[guard] trace=%s path=%s bytes=%s too_big=%s has_base64=%s",
                trace,
                request.url.path,
                size,
                too_big,
                has_b64,
            )

            if too_big or has_b64:
                logger.warning(
                    "Rejecting payload: trace=%s path=%s bytes=%s limit=%s has_base64=%s",
                    trace,
                    request.url.path,
                    size,
                    self.max_bytes,
                    has_b64,
                )
                detail = (
                    "Payload too large or contains base64 image. Please upload images to R2 and send key/url only."
                )
                return JSONResponse(
                    status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "trace": trace,
                        "detail": detail,
                        "bytes": size,
                        "limit": self.max_bytes,
                        "has_base64": has_b64,
                    },
                )
        else:
            guard_info.setdefault("bytes", None)
            guard_info.setdefault("has_base64", False)
            guard_info.setdefault("too_big", False)

        return await call_next(request)


class RejectHugeOrBase64(BodyGuardMiddleware):
    """Backwards-compatible alias for legacy imports."""

    pass
