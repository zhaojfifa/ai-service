from __future__ import annotations
import json
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class RejectHugeOrBase64(BaseHTTPMiddleware):
    def __init__(self, app, max_bytes: int = 4 * 1024 * 1024, check_base64: bool = True):
        super().__init__(app)
        self.max_bytes = max_bytes
        self.check_base64 = check_base64

    async def dispatch(self, request: Request, call_next: Callable):
        if request.url.path in ("/healthz", "/"):
            return await call_next(request)

        body = await request.body()
        if len(body) > self.max_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large. Upload to R2 and pass key/url only."},
            )

        if self.check_base64 and request.headers.get("content-type", "").startswith("application/json"):
            try:
                data = json.loads(body.decode("utf-8"))
                def looks_like_b64(v: str) -> bool:
                    if not isinstance(v, str) or len(v) < 1024:
                        return False
                    if v.startswith("data:image/") and ";base64," in v:
                        return True
                    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r")
                    return all(ch in allowed for ch in v[:4096])
                stack = [data]
                while stack:
                    x = stack.pop()
                    if isinstance(x, dict):
                        for _, v in x.items():
                            if isinstance(v, str) and looks_like_b64(v):
                                return JSONResponse(
                                    status_code=422,
                                    content={"detail": "Base64 image detected. Upload to R2 and pass key/url."},
                                )
                            if isinstance(v, (dict, list)):
                                stack.append(v)
                    elif isinstance(x, list):
                        stack.extend(x)
            except Exception:
                pass

        return await call_next(request)
