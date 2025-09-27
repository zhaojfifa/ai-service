# app/main.py
from __future__ import annotations
import os

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import (
    GeneratePosterResponse,
    PosterInput,
    SendEmailRequest,
    SendEmailResponse,
)
from app.services.poster import (
    render_layout_preview,
    build_openai_prompt,     # 作为通用 prompt
    compose_marketing_email,
)
from app.services.email_sender import send_email

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

@app.get("/", include_in_schema=False)
def index():
    return RedirectResponse(url="/docs", status_code=307)

@app.head("/", include_in_schema=False)
def index_head():
    return Response(status_code=204)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/api/generate-poster", response_model=GeneratePosterResponse)
def generate_poster(payload: PosterInput) -> GeneratePosterResponse:
    """
    根据 IMAGE_BACKEND 选择后端：
    - openai：调用 OpenAI 生成图
    - glibatree：调用 Glibatree（保持你现有的生成器）
    """
    preview = render_layout_preview(payload)
    backend = (os.getenv("IMAGE_BACKEND") or getattr(settings, "IMAGE_BACKEND", "") or "glibatree").lower()

    if backend == "openai":
        # 延迟导入，避免无 key 时启动失败
        try:
            from app.services.openai_image import generate_image_with_openai
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"OpenAI 生成不可用：{exc}")

        api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
        if not api_key:
            raise HTTPException(status_code=500, detail="未配置 OPENAI_API_KEY")

        prompt = build_openai_prompt(payload)
        try:
            png_path = generate_image_with_openai(
                prompt=prompt,
                api_key=api_key,
                base_url=os.getenv("OPENAI_BASE_URL") or getattr(settings, "OPENAI_BASE_URL", None),
                size=os.getenv("OPENAI_IMAGE_SIZE", "1024x1024"),
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

        # 返回前端可直接显示的 data URL（简化：从文件读成 base64）
        import base64
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

    # ---- glibatree 分支（保持你原有的生成方式）----
    from app.services.glibatree import generate_poster_asset as gliba_generate
    prompt = build_openai_prompt(payload)  # 作为通用 prompt
    poster_image = gliba_generate(payload, prompt, preview)
    email_body = compose_marketing_email(payload, poster_image.filename)
    return GeneratePosterResponse(
        layout_preview=preview,
        prompt=prompt,
        email_body=email_body,
        poster_image=poster_image,
    )

@app.post("/api/send-email", response_model=SendEmailResponse)
def send_marketing_email(payload: SendEmailRequest) -> SendEmailResponse:
    try:
        return send_email(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

__all__ = ["app"]
