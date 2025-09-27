# app/main.py
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import (
    GeneratePosterResponse,
    PosterInput,
    SendEmailRequest,
    SendEmailResponse,
)
from app.services.email_sender import send_email

# --- Glibatree 后端（原有） ---
# 如果后端选择 glibatree，会用到下面两个工具函数
from app.services.glibatree import generate_poster_asset as gliba_generate

# 版式预览 / 邮件文案 等通用逻辑依然复用
from app.services.poster import (
    render_layout_preview,
    compose_marketing_email,
    build_glibatree_prompt,   # 仍保留以便选择 glibatree 时使用
)

# --- OpenAI 后端（新增） ---
# 兼容两种放置方式：你可能把 OpenAI 的实现放在 app/services/openai_gen.py，
# 也可能直接放到了 app/services/poster.py 里。这里做容错导入。
OPENAI_FUNCS = None
try:
    # 推荐做法：单独文件 app/services/openai_gen.py
    from app.services.openai_gen import (  # type: ignore
        build_openai_prompt,
        generate_poster_asset_openai,
    )

    OPENAI_FUNCS = ("openai_gen", build_openai_prompt, generate_poster_asset_openai)
except Exception:
    try:
        # 兜底：如果你把 OpenAI 的实现合并在 poster.py
        from app.services.poster import (  # type: ignore
            build_openai_prompt,
            generate_poster_asset_openai,
        )

        OPENAI_FUNCS = ("poster", build_openai_prompt, generate_poster_asset_openai)
    except Exception:
        OPENAI_FUNCS = None


settings = get_settings()

app = FastAPI(title="Marketing Poster API", version="1.0.0")

# -------- CORS ----------
allow_origins = settings.allowed_origins
allow_credentials = False if allow_origins == ["*"] else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root():
    return {"ok": True, "service": "ai-service", "version": "1.0.0"}


@app.post("/api/generate-poster", response_model=GeneratePosterResponse)
def generate_poster(payload: PosterInput) -> GeneratePosterResponse:
    """
    根据配置的后端（GLIBATREE 或 OPENAI）生成海报，并返回
    - 布局预览图（layout_preview）
    - 提示词（prompt）
    - 邮件文案（email_body）
    - 生成的主图（poster_image）
    """
    # 1) 先生成前端所需的布局预览
    preview = render_layout_preview(payload)

    # 2) 根据环境变量 / 配置决定用哪个后端
    backend = getattr(settings, "image_backend", "glibatree").lower()

    # 3) 分支：OpenAI 或 Glibatree
    if backend == "openai":
        if not OPENAI_FUNCS:
            # 没有找到 OpenAI 的实现，给出友好错误
            raise HTTPException(
                status_code=500,
                detail=(
                    "OpenAI backend selected but functions not found. "
                    "Please ensure app/services/openai_gen.py (or poster.py) "
                    "provides build_openai_prompt() and generate_poster_asset_openai()."
                ),
            )

        _, _build_openai_prompt, _generate_openai = OPENAI_FUNCS
        prompt = _build_openai_prompt(payload)
        poster_image = _generate_openai(payload, prompt, preview)
    else:
        # 默认/回退：继续使用 Glibatree 流程
        prompt = build_glibatree_prompt(payload)
        poster_image = gliba_generate(payload, prompt, preview)

    # 4) 生成营销邮件正文
    email_body = compose_marketing_email(payload, poster_image.filename)

    # 5) 返回统一响应
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
    except Exception as exc:  # pragma: no cover - ensures HTTP friendly message
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["app"]
