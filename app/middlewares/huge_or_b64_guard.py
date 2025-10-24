from __future__ import annotations

import json
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RejectHugeOrBase64(BaseHTTPMiddleware):
    """
    保护后端：请求体超过 ``max_bytes`` 或 JSON 里出现明显的 base64 大体量字段时拒绝。
    仅用于 API/海报生成入口，不影响静态与健康探针。
    """

    def __init__(self, app, max_bytes: int = 4 * 1024 * 1024, check_base64: bool = True) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes
        self.check_base64 = check_base64

    async def dispatch(self, request: Request, call_next: Callable):
        # 放行健康探针与静态资源
        if request.url.path in {"/healthz", "/"}:
            return await call_next(request)

        body = await request.body()
        if len(body) > self.max_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large. Upload assets to R2 and send key/url only."},
            )

        if self.check_base64 and request.headers.get("content-type", "").startswith("application/json"):
            try:
                data = json.loads(body.decode("utf-8"))

                def _looks_like_b64(value: object) -> bool:
                    if not isinstance(value, str) or len(value) < 1024:
                        return False
                    if value.startswith("data:image/") and ";base64," in value:
                        return True
                    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r")
                    sample = value[:4096]
                    return all(ch in allowed for ch in sample)

                stack = [data]
                while stack:
                    current = stack.pop()
                    if isinstance(current, dict):
                        for nested in current.values():
                            if _looks_like_b64(nested):
                                return JSONResponse(
                                    status_code=422,
                                    content={
                                        "detail": "Base64 image detected. Upload to R2 first and pass key/url."
                                    },
                                )
                            if isinstance(nested, (dict, list)):
                                stack.append(nested)
                    elif isinstance(current, list):
                        stack.extend(current)
            except Exception:
                # JSON 解析失败由业务路由决定是否报错
                pass

        return await call_next(request)
