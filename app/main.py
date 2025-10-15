from __future__ import annotations
import os
import sys
import json                     # ← 你用了 json，但之前没导入
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import ValidationError
from app.schemas import TemplatePosterCollection，TemplatePosterEntry



from app.config import get_settings
from app.schemas import (
    GeneratePosterRequest,
    GeneratePosterResponse,
    PromptBundle,
    R2PresignPutRequest,
    R2PresignPutResponse,
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
from app.services.s3_client import make_key, presigned_put_url, public_url_for

logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title="Marketing Poster API", version="1.0.0")

UPLOAD_MAX_BYTES = max(int(os.getenv("UPLOAD_MAX_BYTES", "20000000") or 0), 0)
UPLOAD_ALLOWED_MIME = {
    item.strip()
    for item in os.getenv("UPLOAD_ALLOWED_MIME", "image/png,image/jpeg,image/webp").split(",")
    if item.strip()
}


def _normalize_allowed_origins(value):
    # 支持 None / "" / "*" / CSV / JSON / list
    if not value:
        return ["*"]
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        s = value.strip()
        if s.startswith("["):  # JSON
            try:
                items = json.loads(s)
            except Exception:
                items = s.split(",")
        else:                   # CSV
            items = s.split(",")
    else:
        items = [str(value)]

    def clean(x: str) -> str:
        s = str(x).strip().strip('"').strip("'").rstrip("/")
        return s

    out = [clean(x) for x in items if clean(x)]
    return out or ["*"]

raw = (
    getattr(settings, "allowed_origins", None)
    or os.getenv("ALLOWED_ORIGINS")
)
allow_origins = _normalize_allowed_origins(raw)

allow_credentials = "*" not in allow_origins

# 建议明确写你的前端域名（更安全）
allow_origins = [
    "https://zhaojfifa.github.io",
    "https://zhaojfifa.github.io/ai-service/"
    # 或调试用： "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"],   # GET, POST, OPTIONS...
    allow_headers=["*"],   # Content-Type, Authorization, x-api-key...
    expose_headers=[],     # 如需要可暴露自定义响应头
    max_age=86400,         # 预检缓存
)

# 若你路由里对 OPTIONS 会 405/400，可加兜底（通常 CORSMiddleware 已处理）
from fastapi.responses import Response
@app.options("/{path:path}")
async def cors_preflight(path: str):
    return Response(status_code=204)

@app.options("/{rest_of_path:path}")
def cors_preflight_handler(rest_of_path: str) -> Response:
    """Ensure any CORS preflight request receives an immediate 204 response."""
    return Response(status_code=204)


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


@app.get("/api/template-posters", response_model=TemplatePosterCollection)
def fetch_template_posters() -> TemplatePosterCollection:
    try:
        entries = list_poster_entries()
    except Exception as exc:  # pragma: no cover - unexpected IO failure
        logger.exception("Failed to load template posters")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return TemplatePosterCollection(posters=entries)


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
