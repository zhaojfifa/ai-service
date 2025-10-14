# app/main.py
from __future__ import annotations

import os
import sys
import json
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.config import get_settings
from app.schemas import (  # 保持你的导入不变
    GeneratePosterRequest, GeneratePosterResponse, PromptBundle,
    R2PresignPutRequest, R2PresignPutResponse,
    SendEmailRequest, SendEmailResponse,
    TemplatePosterCollection, TemplatePosterEntry, TemplatePosterUploadRequest,
)
from app.services.email_sender import send_email
from app.services.glibatree import generate_poster_asset
from app.services.poster import build_glibatree_prompt, compose_marketing_email, render_layout_preview
from app.services.s3_client import make_key, presigned_put_url, public_url_for
from app.services.template_variants import list_poster_entries, poster_entry_from_record, save_template_poster

# -----------------------
# 日志：强制覆盖第三方默认设置
# -----------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
    force=True,
)
for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
    logging.getLogger(name).setLevel(LOG_LEVEL)
logger = logging.getLogger("ai-service")
logger.info("Logging initialized. level=%s", LOG_LEVEL)

# -----------------------
# FastAPI app
# -----------------------
settings = get_settings()
app = FastAPI(title="Marketing Poster API", version="1.0.0")

# -----------------------
# CORS 允许来源：支持 JSON/CSV/通配
# -----------------------
def _normalize_allowed_origins(value: Any) -> list[str]:
    if not value:
        return ["*"]
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        s = value.strip()
        if s.startswith("["):
            try:
                items = json.loads(s)
            except Exception:
                items = s.split(",")
        else:
            items = s.split(",")
    else:
        items = [str(value)]

    def clean(x: str) -> str:
        return str(x).strip().strip('"').strip("'").rstrip("/")

    out = [clean(x) for x in items if clean(x)]
    return out or ["*"]

raw_allowed = getattr(settings, "allowed_origins", None) or os.getenv("ALLOWED_ORIGINS")
allow_origins = _normalize_allowed_origins(raw_allowed)

# 建议：明确写你的前端来源（无路径、无末尾斜杠）
# 你也可以用 env ALLOWED_ORIGINS 覆盖
if allow_origins == ["*"]:
    allow_origins = ["https://zhaojfifa.github.io"]  # 先跑通；需要多域时再扩展

logger.info("CORS allow_origins=%s", allow_origins)

# 先加 Starlette 的 CORS 中间件（正常情况下它就够了）
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)

# -----------------------
# 兜底 CORS 中间件（关键补丁）
# 说明：
#   - 某些托管/代理环境下，预检可能在 Starlette CORS 之前被 400/405 拦掉，
#     这里我们在极靠前的位置拦截 OPTIONS，直接 204 并补齐响应头；
#   - 同时对非预检请求，也补一份 CORS 响应头（以防异常返回时缺头）。
# -----------------------
@app.middleware("http")
async def cors_fallback_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    # 只对来自浏览器的跨域请求做处理
    if origin:
        # 计算是否允许这个 origin
        allow_this_origin = (
            "*" in allow_origins or origin.rstrip("/") in allow_origins
        )

        # 预检请求：直接放行 204，并带上允许头
        if request.method.upper() == "OPTIONS":
            resp = Response(status_code=204)
            if allow_this_origin:
                resp.headers["Access-Control-Allow-Origin"] = origin
                resp.headers["Vary"] = "Origin"
                # 浏览器发来的预检所声称的方法/头
                req_method = request.headers.get("Access-Control-Request-Method", "POST")
                req_headers = request.headers.get("Access-Control-Request-Headers", "*")
                resp.headers["Access-Control-Allow-Methods"] = req_method or "POST"
                resp.headers["Access-Control-Allow-Headers"] = req_headers or "*"
                resp.headers["Access-Control-Max-Age"] = "86400"
            return resp

        # 非预检：让下游处理，然后补 CORS 响应头（异常时也能带上）
        response = await call_next(request)
        if allow_this_origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
        return response

    # 非跨域（无 Origin）直接走正常逻辑
    return await call_next(request)

# 你原来的 2 个 @app.options 通配路由可以删了（避免路由冲突）
# 如果你想保留一个也行，但有了上面的 middleware 就没必要了。

# -----------------------
# 健康检查
# -----------------------
@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}



def _model_dump(model):
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    if hasattr(model, "dict"):
        return model.dict(exclude_none=True)
    return {}


def _model_validate(model, data):
    if hasattr(model, "model_validate"):
        return model.model_validate(data)
    if hasattr(model, "parse_obj"):
        return model.parse_obj(data)
    return model(**data)


def _preview_json(value: Any, limit: int = 512) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False)
    except Exception:  # pragma: no cover - defensive fallback
        text = str(value)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}…(+{len(text) - limit} chars)"


def _summarise_prompt_bundle(bundle: PromptBundle | None) -> dict[str, Any]:
    if not bundle:
        return {}

    if isinstance(bundle, PromptBundle):
        data = bundle.model_dump(exclude_none=False)
    elif hasattr(bundle, "model_dump"):
        data = bundle.model_dump(exclude_none=False)
    elif hasattr(bundle, "dict"):
        data = bundle.dict(exclude_none=False)
    elif isinstance(bundle, dict):
        data = bundle
    else:
        return {}

    summary: dict[str, Any] = {}
    for slot in ("scenario", "product", "gallery"):
        config = data.get(slot)
        if not config:
            continue

        if isinstance(config, dict):
            preset = config.get("preset")
            aspect = config.get("aspect")
            prompt = config.get("prompt") or config.get("positive") or ""
            negative = (
                config.get("negative_prompt")
                or config.get("negative")
                or ""
            )
        else:
            preset = getattr(config, "preset", None)
            aspect = getattr(config, "aspect", None)
            prompt = getattr(config, "prompt", "") or getattr(config, "positive", "") or ""
            negative = (
                getattr(config, "negative_prompt", "")
                or getattr(config, "negative", "")
                or ""
            )

        summary[slot] = {
            "preset": preset,
            "aspect": aspect,
            "prompt_len": len(str(prompt)),
            "negative_len": len(str(negative)),
        }

    return summary


def _summarise_poster(poster: Any) -> dict[str, Any]:
    if poster is None:
        return {}

    try:
        features = [item for item in getattr(poster, "features", []) if item]
    except Exception:  # pragma: no cover - defensive fallback
        features = []

    try:
        gallery_items = [item for item in getattr(poster, "gallery_items", []) if item]
    except Exception:  # pragma: no cover - defensive fallback
        gallery_items = []

    return {
        "template_id": getattr(poster, "template_id", None),
        "scenario_mode": getattr(poster, "scenario_mode", None),
        "product_mode": getattr(poster, "product_mode", None),
        "feature_count": len(features),
        "gallery_count": len(gallery_items),
    }


async def read_json_relaxed(request: Request) -> dict:
    try:
        payload = await request.json()
    except Exception:
        body = await request.body()
        if not body:
            return {}
        payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")
    return payload


@app.post("/api/r2/presign-put", response_model=R2PresignPutResponse)
def presign_r2_upload(request: R2PresignPutRequest) -> R2PresignPutResponse:
    if UPLOAD_ALLOWED_MIME and request.content_type not in UPLOAD_ALLOWED_MIME:
        raise HTTPException(status_code=415, detail=f"content_type not allowed: {request.content_type}")
    if UPLOAD_MAX_BYTES and request.size and request.size > UPLOAD_MAX_BYTES:
        raise HTTPException(status_code=413, detail="file exceeds permitted size")

    try:
        key = make_key(request.folder, request.filename)
        put_url = presigned_put_url(key, request.content_type)
    except RuntimeError as exc:  # pragma: no cover - configuration issue
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return R2PresignPutResponse(key=key, put_url=put_url, public_url=public_url_for(key))


@app.get("/api/template-posters", response_model=TemplatePosterCollection)
def fetch_template_posters() -> TemplatePosterCollection:
    try:
        entries = list_poster_entries()
    except Exception as exc:  # pragma: no cover - unexpected IO failure
        logger.exception("Failed to load template posters")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return TemplatePosterCollection(posters=entries)


@app.post("/api/template-posters", response_model=TemplatePosterEntry)
def upload_template_poster(payload: TemplatePosterUploadRequest) -> TemplatePosterEntry:
    try:
        record = save_template_poster(
            slot=payload.slot,
            filename=payload.filename,
            content_type=payload.content_type,
            data=payload.data,
        )
        return poster_entry_from_record(record)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - unexpected IO failure
        logger.exception("Failed to store template poster")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/generate-poster", response_model=GeneratePosterResponse)
async def generate_poster(request: Request) -> GeneratePosterResponse:
    try:
        raw_payload = await read_json_relaxed(request)
        logger.info(
            "generate_poster request received: %s",
            _preview_json(raw_payload, limit=768),
        )
        payload = _model_validate(GeneratePosterRequest, raw_payload)
    except ValidationError as exc:
        logger.warning("generate_poster validation error: %s", exc.errors())
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("generate_poster payload parsing failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        logger.info(
            "generate_poster normalised payload: %s",
            {
                "poster": _summarise_poster(payload.poster),
                "variants": payload.variants,
                "seed": payload.seed,
                "lock_seed": payload.lock_seed,
                "prompt_bundle": _summarise_prompt_bundle(payload.prompt_bundle),
            },
        )
        poster = payload.poster
        preview = render_layout_preview(poster)
        prompt_payload = _model_dump(payload.prompt_bundle)
        prompt_text, prompt_details, prompt_bundle = build_glibatree_prompt(
            poster, prompt_payload
        )

        # 生成主图与变体
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
        response_bundle: PromptBundle | None = None
        if prompt_bundle:
            converted: dict[str, Any] = {}
            for slot, config in prompt_bundle.items():
                if not config:
                    continue
                converted[slot] = {
                    "preset": config.get("preset"),
                    "aspect": config.get("aspect"),
                    "prompt": config.get("prompt")
                    or config.get("positive")
                    or "",
                    "negative_prompt": config.get("negative_prompt")
                    or config.get("negative")
                    or "",
                }
            if converted:
                if hasattr(PromptBundle, "model_validate"):
                    response_bundle = PromptBundle.model_validate(converted)
                elif hasattr(PromptBundle, "parse_obj"):
                    response_bundle = PromptBundle.parse_obj(converted)
                else:  # pragma: no cover - legacy Pydantic fallback
                    response_bundle = PromptBundle(**converted)

        logger.info(
            "generate_poster completed: %s",
            {
                "response": {
                    "poster_filename": getattr(result.poster, "filename", None),
                    "variant_count": len(result.variants or []),
                    "has_scores": bool(result.scores),
                    "seed": result.seed,
                    "lock_seed": result.lock_seed,
                },
                "prompt_bundle": _summarise_prompt_bundle(
                    response_bundle or payload.prompt_bundle
                ),
            },
        )
        return GeneratePosterResponse(
            layout_preview=preview,
            prompt=prompt_text,
            email_body=email_body,
            poster_image=result.poster,
            prompt_details=prompt_details,
            prompt_bundle=response_bundle,
            variants=result.variants,
            scores=result.scores,
            seed=result.seed,
            lock_seed=result.lock_seed,
        )

    except Exception as exc:  # defensive logging
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
