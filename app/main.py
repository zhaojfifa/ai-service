"""
FastAPI 入口：
- 提供 /health
- 安全导入并注册 RejectHugeOrBase64，避免启动阶段报错
"""
from __future__ import annotations

import logging
from typing import Awaitable, Callable

from fastapi import FastAPI

app = FastAPI(title="ai-service")
log = logging.getLogger("ai-service")

try:
    from app.middlewares.reject_huge_or_base64 import RejectHugeOrBase64
except Exception as e:  # noqa: BLE001
    log.error("RejectHugeOrBase64 import failed: %r; using no-op middleware", e)
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response

    class RejectHugeOrBase64(BaseHTTPMiddleware):  # type: ignore[no-redef]
        async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
            return await call_next(request)

app.add_middleware(RejectHugeOrBase64)


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}
