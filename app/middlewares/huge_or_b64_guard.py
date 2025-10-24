import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_BASE64_RE = re.compile(r'"(?:image|data)[^\"]*?base64,', re.IGNORECASE)


class RejectHugeOrBase64(BaseHTTPMiddleware):
    def __init__(self, app, *, max_bytes=4 * 1024 * 1024, check_base64=True):
        super().__init__(app)
        self.max_bytes = max_bytes
        self.check_base64 = check_base64

    async def dispatch(self, request: Request, call_next):
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        body = await request.body()
        if self.max_bytes and len(body) > self.max_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "Payload too large or contains base64 image. Upload to R2 and send key/url."},
            )
        if self.check_base64 and body:
            text = body.decode("utf-8", errors="ignore")
            if _BASE64_RE.search(text):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Payload contains base64 image. Upload to R2 and send key/url."},
                )
        return await call_next(request)
