"""
FastAPI 入口：
- 提供 /healthz
- 直接导入并注册 RejectHugeOrBase64，确保启动阶段不会再报 NameError
"""
from __future__ import annotations

from fastapi import FastAPI
from app.middlewares.reject_huge_or_base64 import RejectHugeOrBase64

app = FastAPI(title="ai-service")

@app.get("/healthz")
def healthz():
    return {"ok": True}

app.add_middleware(RejectHugeOrBase64)
