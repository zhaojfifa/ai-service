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

# 两种后端
from app.services.glibatree import generate_poster_asset as gliba_generate
from app.services.poster import (
    render_layout_preview,
    compose_marketing_email,
    build_openai_prompt,
    generate_poster_with_openai,
    build_glibatree_prompt,
)

settings = get_settings()
app = FastAPI(title="Marketing Poster API", version="1.0.0")

# ---- CORS ----
allow_origins = settings.allowed_origins
allow_credentials = False if allow_origins == ["*"] else True
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 根路径 & 健康检查（避免 Render 探活 404）----
@app.get("/", include_in_schema=False)
def index() -> RedirectResponse:
    return RedirectResponse(url="/docs", status_code=307)

@app.head("/", include_in_schema=False)
def index_head() -> Response:
    return Response(status_code=204)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

# ---- 生成海报 ----
@app.post("/api/generate-poster", response_model=GeneratePosterResponse)
def generate_poster(payload: PosterInput) -> GeneratePosterResponse:
    """
    根据 IMAGE_BACKEND 环境变量选择后端：
      - openai  : 使用 OpenAI 生成
      - glibatree(默认): 使用 Glibatree 生成
    """
    preview = render_layout_preview(payload)
    backend = (os.getenv("IMAGE_BACKEND") or getattr(settings, "IMAGE_BACKEND", "") or "glibatree").lower()

    if backend == "openai":
        # —— OpenAI 路径 ——
        api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
        if not api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY 未配置（IMAGE_BACKEND=openai）")

        try:
            # 生成图片文件，返回 (preview_text, prompt, png_path)
            _pv, prompt, png_path = generate_poster_with_openai(
                poster=payload,
                openai_api_key=api_key,
                openai_base_url=os.getenv("OPENAI_BASE_URL"),
                size=os.getenv("OPENAI_IMAGE_SIZE", "1024x1024"),
            )

            # 转为 Data URL 回前端
            with open(png_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            data_url = f"data:image/png;base64,{b64}"

            email_body = compose_marketing_email(payload, os.path.basename(png_path))
            return GeneratePosterResponse(
                layout_preview=preview,
                prompt=prompt,
                email_body=email_body,
                poster_image={"filename": os.path.basename(png_path), "data_url": data_url},
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    else:
        # —— Glibatree 路径（默认）——
        prompt = build_glibatree_prompt(payload)
        try:
            poster_asset = gliba_generate(payload, prompt, preview)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        email_body = compose_marketing_email(payload, poster_asset.filename)
        return GeneratePosterResponse(
            layout_preview=preview,
            prompt=prompt,
            email_body=email_body,
            poster_image=poster_asset,
        )

# ---- 发送邮件 ----
@app.post("/api/send-email", response_model=SendEmailResponse)
def send_marketing_email(payload: SendEmailRequest) -> SendEmailResponse:
    try:
        return send_email(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["app"]
