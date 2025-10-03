# app/main.py
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, PlainTextResponse

from app.config import get_settings
from app.schemas import (
    GeneratePosterResponse,
    PosterInput,
    SendEmailRequest,
    SendEmailResponse,
)
from app.services.email_sender import send_email
from app.services.glibatree import generate_poster_asset
from app.services.poster import (
    build_glibatree_prompt,
    compose_marketing_email,
    render_layout_preview,
)

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title="Marketing Poster API", version="1.0.0")

# --- CORS ---
allow_origins = settings.allowed_origins  # 总是返回列表（如 ["*"] 或具体域）
allow_credentials = allow_origins != ["*"]  # "*" 时禁止携带凭证以符合浏览器规范

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 根路径：修复 Render HEAD / 健康探测 & 人类可用性 ---
@app.get("/", include_in_schema=False)
def root_redirect():
    # 访问根直接跳到 Swagger 文档
    return RedirectResponse(url="/docs", status_code=307)

@app.head("/", include_in_schema=False)
def root_head():
    # Render 健康检查会发 HEAD /，这里返回 200
    return PlainTextResponse("", status_code=200)

# --- 健康检查 ---
@app.get("/health", include_in_schema=False)
def health_check() -> dict[str, str]:
    return {"status": "ok"}

# --- 业务 API ---
@app.post("/api/generate-poster", response_model=GeneratePosterResponse)
def generate_poster(payload: PosterInput) -> GeneratePosterResponse:
    try:
        preview = render_layout_preview(payload)
        prompt = build_glibatree_prompt(payload)
        poster_image = generate_poster_asset(payload, prompt, preview)
        email_body = compose_marketing_email(payload, poster_image.filename)
        return GeneratePosterResponse(
            layout_preview=preview,
            prompt=prompt,
            email_body=email_body,
            poster_image=poster_image,
        )
    except Exception as exc:  # 防御性日志
        logger.exception("Failed to generate poster")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@app.post("/api/send-email", response_model=SendEmailResponse)
def send_marketing_email(payload: SendEmailRequest) -> SendEmailResponse:
    try:
        return send_email(payload)
    except Exception as exc:  # 防御性日志
        logger.exception("Failed to send marketing email")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

__all__ = ["app"]
