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

# ---- 生成海报（统一一个路由，内部选择后端）----
# ...省略前文

@app.post("/api/generate-poster", response_model=GeneratePosterResponse)
def generate_poster(payload: PosterInput) -> GeneratePosterResponse:
    preview = render_layout_preview(payload)

    backend = (
        os.getenv("IMAGE_BACKEND")
        or getattr(settings, "IMAGE_BACKEND", "")
        or "glibatree"
    ).lower()

    if backend == "openai":
        # 这里保持你原来 openai 分支的实现（按需导入）
        # ...
        pass

    else:
        # ---- Glibatree 分支：延迟导入 + 兜底 prompt ----
        try:
            from app.services.poster import build_glibatree_prompt as _build_gliba_prompt
            prompt = _build_gliba_prompt(payload)
        except Exception:
            # 兜底版 prompt（当 poster.py 没有 build_glibatree_prompt 时仍可工作）
            features = "\n".join(
                f"- 功能点{i+1}: {f}" for i, f in enumerate(payload.features or [])
            )
            prompt = (
                f"为厨电产品『{payload.brand_name} {payload.product_name}』生成现代简洁风海报：\n"
                f"- 版式：左侧约 40% 放应用场景「{payload.scenario_image}」，右侧视觉中心放 45° 产品渲染；\n"
                f"- 中部标题（红色粗体）：{payload.title}\n"
                f"- 底部灰度小图（3-4张），说明：{payload.series_description}\n"
                f"- 右下角副标题（红色粗体）：{payload.subtitle}\n"
                f"- 功能点标注：\n{features}\n"
                "主色黑/红/银灰，背景浅灰/白；排版规整对齐、留白充分。"
            )

        try:
            # 延迟导入 glibatree 生成器，避免顶层 import 阻塞启动
            from app.services.glibatree import generate_poster_asset as gliba_generate
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Glibatree 后端未就绪：{e}")

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
