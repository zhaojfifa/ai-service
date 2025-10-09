
from __future__ import annotations

import json                     # ← 你用了 json，但之前没导入
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# 建议模块方式导入 schemas，避免局部名被不小心覆盖
from app.schemas import (
    GeneratePosterRequest,
    GeneratePosterResponse,
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

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title="Marketing Poster API", version="1.0.0")

def _normalize_allowed_origins(value) -> list[str]:
    """
    支持：None / "" / "*" / 逗号分隔字符串 / JSON 数组 / 原生 list
    输出：去重、去尾随斜杠的 List[str]
    """
    if value in (None, "", [], ("",), {}):
        result = ["*"]
    elif isinstance(value, list):
        result = [str(o).strip() for o in value if str(o).strip()]
    elif isinstance(value, str):
        s = value.strip()
        if s == "*":
            result = ["*"]
        elif s.startswith("["):
            # 正确解析 JSON 数组
            try:
                arr = json.loads(s)
                result = [str(o).strip() for o in arr if str(o).strip()]
            except Exception:
                # 回退：把外层[]去掉再按逗号切（尽量容错）
                s2 = s.strip("[]")
                result = [p.strip().strip('"').strip("'") for p in s2.split(",") if p.strip()]
        else:
            result = [p.strip() for p in s.split(",") if p.strip()]
    else:
        result = ["*"]

    # 去尾随 /、去重
    result = [r.rstrip("/") for r in result]
    return list(dict.fromkeys(result))

raw = getattr(settings, "allowed_origins", None) or getattr(settings, "ALLOWED_ORIGINS", None)
allow_origins = _normalize_allowed_origins(raw)

# 只要包含 * 就必须关闭 credentials
allow_credentials = "*" not in allow_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins if "*" not in allow_origins else ["*"],
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("CORS raw=%r -> allow_origins=%s, allow_credentials=%s",raw, allow_origins, allow_credentials)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def _model_dump(model):
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    if hasattr(model, "dict"):
        return model.dict(exclude_none=True)
    return {}


@app.post("/api/generate-poster", response_model=GeneratePosterResponse)
def generate_poster(payload: GeneratePosterRequest) -> GeneratePosterResponse:
    try:
        poster = payload.poster
        preview = render_layout_preview(poster)
        prompt_payload = _model_dump(payload.prompts)
        prompt_text, prompt_details, prompt_bundle = build_glibatree_prompt(
            poster, prompt_payload
        )
        result = generate_poster_asset(
            poster,
            prompt_text,
            preview,
            prompt_bundle=prompt_payload,
            prompt_details=prompt_details,
            render_mode=payload.render_mode,
            variants=payload.variants,
            seed=payload.seed,
            lock_seed=payload.lock_seed,
        )
        email_body = compose_marketing_email(poster, result.poster.filename)
        return GeneratePosterResponse(
            layout_preview=preview,
            prompt=prompt_text,
            email_body=email_body,
            poster_image=result.poster,
            prompt_details=prompt_details,
            prompt_bundle=prompt_bundle,
            variants=result.variants,
            scores=result.scores,
            seed=result.seed,
            lock_seed=result.lock_seed,
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Failed to generate poster")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/send-email", response_model=SendEmailResponse)
def send_marketing_email(payload: SendEmailRequest) -> SendEmailResponse:
    try:
        return send_email(payload)
    except Exception as exc:  # pragma: no cover - ensures HTTP friendly message
        logger.exception("Failed to send marketing email")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["app"]
