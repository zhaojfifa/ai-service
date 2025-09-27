# app/main.py
from __future__ import annotations

import os
import base64
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.schemas import (
    GeneratePosterResponse,
    PosterInput,
    SendEmailRequest,
    SendEmailResponse,
)
from app.services.email_sender import send_email
from app.services.poster import (
    render_layout_preview,
    compose_marketing_email,
)

# ---------------------------------------------------------------------
# 初始化配置 / 应用
# ---------------------------------------------------------------------
settings = get_settings()
app = FastAPI(title="Marketing Poster API", version="1.0.0")

allow_origins = settings.allowed_origins
allow_credentials = False if allow_origins == ["*"] else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# 根路由 & 健康检查（Render 探活会请求 / 和 HEAD /）
# ---------------------------------------------------------------------
@app.get("/", include_in_schema=False)
def index():
    return RedirectResponse(url="/docs", status_code=307)

@app.head("/", include_in_schema=False)
def index_head():
    return Response(status_code=204)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

# ---------------------------------------------------------------------
# 生成海报：支持两种后端（IMAGE_BACKEND=openai/glibatree）
# - 返回结构兼容前端：poster_image.data_url 直接可作为 <img src>
# ---------------------------------------------------------------------
@app.post("/api/generate-poster", response_model=GeneratePosterResponse)
def api_generate_poster(payload: PosterInput) -> GeneratePosterResponse:
    backend = os.getenv("IMAGE_BACKEND", "openai").lower()

    try:
        # 文案/版式预览：前后端都展示
        preview = render_layout_preview(payload)

        if backend == "openai":
            # 使用我们在 services.poster 中封装的 OpenAI 方案
            from app.services.poster import generate_poster_with_openai, build_openai_prompt

            openai_api_key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise RuntimeError("OPENAI_API_KEY 未配置（IMAGE_BACKEND=openai 时必需）")

            _preview, prompt, png_path = generate_poster_with_openai(
                poster=payload,
                openai_api_key=openai_api_key,
                openai_base_url=os.getenv("OPENAI_BASE_URL"),
                size=os.getenv("OPENAI_IMAGE_SIZE"
