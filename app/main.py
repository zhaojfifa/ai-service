from __future__ import annotations

import json
import logging
import os
import uuid
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

from app.config import get_settings
from app.middlewares.body_guard import BodyGuardMiddleware
from app.schemas import (
    GeneratePosterRequest,
    GeneratePosterResponse,
    PromptBundle,
    R2PresignPutRequest,
    R2PresignPutResponse,
    SendEmailRequest,
    SendEmailResponse,
    TemplatePosterCollection,
    TemplatePosterEntry,
    TemplatePosterUploadRequest,
)
from app.services.email_sender import send_email
from app.services.glibatree import configure_vertex_imagen, generate_poster_asset
from app.services.image_provider.factory import get_provider
from app.services.poster import (
    build_glibatree_prompt,
    compose_marketing_email,
    render_layout_preview,
)
from app.services.r2_client import make_key, presign_put_url, public_url_for
from app.services.template_variants import (
    list_poster_entries,
    poster_entry_from_record,
    save_template_poster,
)
from app.services.vertex_imagen import init_vertex
from app.services.storage_bridge import store_image_and_url
from app.services.vertex_imagen3 import VertexImagen3

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# uvicorn 日志级别统一
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("uvicorn").setLevel(LOG_LEVEL)
logging.getLogger("uvicorn.error").setLevel(LOG_LEVEL)
logging.getLogger("uvicorn.access").setLevel(LOG_LEVEL)
logging.getLogger("ai-service").setLevel(LOG_LEVEL)

log = logging.getLogger("ai-service")
logger = log
app = FastAPI(title="Marketing Poster API", version="1.0.0")

# ------------- 关键修复：安全导入 + 条件注册（防止 NameError） -------------
RejectHugeOrBase64 = None  # 先占位，避免后续引用未定义

try:
    # 绝对导入，要求 app 是包；配合 __init__.py（见下文）
    from app.middlewares.reject_huge_or_base64 import RejectHugeOrBase64  # type: ignore
    log.info("Loaded middleware: RejectHugeOrBase64")
except Exception as e:  # noqa: BLE001
    log.error("Failed to import RejectHugeOrBase64: %r; service will run without it.", e)
    RejectHugeOrBase64 = None

if RejectHugeOrBase64 is not None:
    app.add_middleware(RejectHugeOrBase64)
# -----------------------------------------------------------------------


# 首页：GET/HEAD 200（修复 405）
@app.get("/", include_in_schema=False)
def root() -> dict[str, Any]:
    return {"service": "ai-service", "ok": True}


@app.head("/", include_in_schema=False)
def root_head() -> Response:
    # HEAD 按规范不返回 body
    return Response(status_code=200)


settings = get_settings()


# 健康检查，确保 Render 能检测端口开放
@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}



vertex_poster_client: VertexImagen3 | None = None

try:
    init_vertex()
except Exception as exc:  # pragma: no cover - startup diagnostics
    logger.warning("Vertex init failed: %s", exc)
else:
    try:
        vertex_poster_client = VertexImagen3()
    except Exception as exc:  # pragma: no cover - startup diagnostics
        vertex_poster_client = None
        logger.warning("VertexImagen3 initialization failed: %s", exc)
    else:
        configure_vertex_imagen(vertex_poster_client)
        print(
            "[VertexImagen3]",
            f"project={vertex_poster_client.project}",
            f"location={vertex_poster_client.location}",
            f"gen_model={vertex_poster_client.model_generate}",
            f"edit_model={vertex_poster_client.model_edit}",
        )
        logger.info(
            "VertexImagen3 ready",
            extra={
                "project": vertex_poster_client.project,
                "location": vertex_poster_client.location,
                "generate_model": vertex_poster_client.model_generate,
                "edit_model": vertex_poster_client.model_edit,
            },
        )


IMAGE_PROVIDER_NAME = "vertex"


@lru_cache(maxsize=1)
def _get_image_provider():
    try:
        provider = get_provider()
    except Exception as exc:  # pragma: no cover - remote dependency init
        logger.exception("Failed to initialise image provider: %s", exc)
        raise HTTPException(status_code=503, detail="Image provider unavailable") from exc
    logger.info("Using %s image provider for imagen endpoint", IMAGE_PROVIDER_NAME)
    return provider

body_guard_limit = os.getenv("MAX_JSON_BYTES") or os.getenv("UPLOAD_MAX_BYTES") or "200000"
try:
    body_guard_bytes = max(int(body_guard_limit), 0)
except (TypeError, ValueError):  # pragma: no cover - defensive parsing
    body_guard_bytes = 200_000

app.add_middleware(BodyGuardMiddleware, max_bytes=body_guard_bytes)
logger.info("BodyGuardMiddleware ready", extra={"max_json_bytes": body_guard_bytes})

# ✅ 上传配置
UPLOAD_MAX_BYTES = max(int(os.getenv("UPLOAD_MAX_BYTES", "20000000") or 0), 0)
UPLOAD_ALLOWED_MIME = {
    item.strip()
    for item in os.getenv("UPLOAD_ALLOWED_MIME", "image/png,image/jpeg,image/webp").split(",")
    if item.strip()
}


def _normalise_allowed_origins(value: Any) -> list[str]:
    if not value:
        return ["*"]
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        text = value.strip()
        if text.startswith("["):
            try:
                items = json.loads(text)
            except (TypeError, ValueError):
                items = text.split(",")
        else:
            items = text.split(",")
    else:
        items = [str(value)]

    cleaned = []
    for item in items:
        candidate = str(item).strip().strip('"').strip("'").rstrip("/")
        if candidate:
            cleaned.append(candidate)
    return cleaned or ["*"]

raw_origins = getattr(settings, "allowed_origins", None) or os.getenv("ALLOWED_ORIGINS")
allow_origins = _normalise_allowed_origins(raw_origins)

DEFAULT_CORS_ORIGINS = {
    "https://zhaojfifa.github.io",
    "https://zhaojfifa.github.io/ai-service",
}

cors_origins = {origin.rstrip("/") for origin in allow_origins}
cors_origins.update(DEFAULT_CORS_ORIGINS)

allow_all = "*" in cors_origins
explicit_origins = sorted(origin for origin in cors_origins if origin != "*")
if allow_all and explicit_origins:
    allow_all = False

cors_allow_origins = explicit_origins or ["*"]
cors_allow_credentials = not allow_all

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)


@app.options("/{path:path}")
async def cors_preflight(path: str) -> Response:  # pragma: no cover - exercised by browsers
    return Response(status_code=204)

@app.get("/debug/vertex/ping")
def vertex_ping() -> JSONResponse:
    """Probe publisher model availability for debugging."""

    try:
        from google.cloud.aiplatform_v1.services.model_garden_service import (
            ModelGardenServiceClient,
        )

        client = ModelGardenServiceClient()
        name = "publishers/google/models/imagen-3.0-generate-001"
        model = client.get_publisher_model(name=name)
        payload = {
            "ok": True,
            "name": model.name,
            "version_id": getattr(model, "version_id", None),
        }
        return JSONResponse(payload)
    except Exception as exc:  # pragma: no cover - remote dependency
        logger.exception("Vertex ping failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


@app.get("/debug/vertex/generate")
def vertex_generate_debug() -> Response:
    """Create a tiny diagnostic image with the active provider."""

    provider = _get_image_provider()
    try:
        image_bytes = provider.generate(
            prompt="a tiny watercolor hummingbird, diagnostic",
            width=512,
            height=512,
            negative_prompt=None,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - remote dependency
        logger.exception("Imagen debug generate failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Imagen error: {exc}") from exc

    headers = {"X-Image-Provider": IMAGE_PROVIDER_NAME}
    return Response(content=image_bytes, media_type="image/png", headers=headers)


class ImagenGenerateRequest(BaseModel):
    prompt: str = Field(..., description="文生图提示词")
    size: str = Field("1024x1024", description="尺寸, 例如 1024x1024")
    negative: str | None = Field(None, description="反向提示词")
    width: int | None = Field(None, gt=0, description="覆盖宽度 (像素)")
    height: int | None = Field(None, gt=0, description="覆盖高度 (像素)")
    seed: int | None = Field(None, ge=0, description="可选种子")
    guidance: float | None = Field(
        None, ge=0.0, description="Imagen 指导系数"
    )
    store: bool | None = Field(
        None,
        description=(
            "是否强制写入对象存储。当显式传 false 时若 RETURN_BINARY_DEFAULT=0 将被拒绝。"
        ),
    )


class ImagenGenerateResponse(BaseModel):
    ok: bool = Field(True, description="调用是否成功")
    key: str = Field(..., description="存储键")
    url: str = Field(..., description="公开或签名 URL")
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    content_type: str = Field("image/png", description="MIME 类型")
    provider: str = Field(IMAGE_PROVIDER_NAME, description="生成后端标识")


def _resolve_dimensions(size: str) -> tuple[int, int]:
    text = (size or "1024x1024").lower().strip()
    try:
        width_str, height_str = text.split("x", 1)
        width = int(width_str)
        height = int(height_str)
    except Exception:
        logger.warning("Invalid size value '%s', falling back to 1024x1024", size)
        return 1024, 1024

    width = max(width, 1)
    height = max(height, 1)
    return width, height


@app.post("/api/imagen/generate", response_model=ImagenGenerateResponse)
def api_imagen_generate(request_data: ImagenGenerateRequest) -> Response:
    provider = _get_image_provider()
    base_width, base_height = _resolve_dimensions(request_data.size)
    width = request_data.width or base_width
    height = request_data.height or base_height

    try:
        image_bytes = provider.generate(
            prompt=request_data.prompt,
            width=width,
            height=height,
            negative_prompt=request_data.negative,
            seed=request_data.seed,
            guidance_scale=request_data.guidance,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - remote dependency
        logger.exception("Imagen generate failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Imagen error: {exc}") from exc

    allow_binary = os.getenv("RETURN_BINARY_DEFAULT", "0") == "1"
    if request_data.store is False and not allow_binary:
        raise HTTPException(
            status_code=403,
            detail="Binary responses are disabled; only URL/Key responses are permitted.",
        )

    do_store = True if request_data.store is None else request_data.store
    if not do_store:
        logger.info(
            "Imagen binary response allowed by configuration",
            extra={"provider": IMAGE_PROVIDER_NAME},
        )
        headers = {"X-Image-Provider": IMAGE_PROVIDER_NAME}
        return Response(content=image_bytes, media_type="image/png", headers=headers)  # type: ignore[return-value]

    meta = store_image_and_url(image_bytes, ext="png", content_type="image/png")
    logger.info(
        "Imagen output stored to R2",
        extra={"provider": IMAGE_PROVIDER_NAME, "key": meta["key"], "url": meta["url"]},
    )

    payload = ImagenGenerateResponse(
        ok=True,
        key=meta["key"],
        url=meta["url"],
        width=width,
        height=height,
        content_type=meta["content_type"],
        provider=IMAGE_PROVIDER_NAME,
    )
    return JSONResponse(payload.model_dump())



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


def _shorten_asset_value(value: str) -> str:
    text = value.strip()
    if len(text) <= 64:
        return text
    return f"{text[:32]}…{text[-16:]}"


def _summarise_assets(payload: Any) -> dict[str, Any]:
    keys: list[str] = []
    urls: list[str] = []

    def _record(candidate: Any) -> None:
        if candidate is None:
            return
        if isinstance(candidate, str):
            trimmed = candidate.strip()
            if not trimmed:
                return
            if trimmed.lower().startswith("http"):
                urls.append(_shorten_asset_value(trimmed))
            else:
                keys.append(_shorten_asset_value(trimmed))
            return
        if isinstance(candidate, dict):
            _record(candidate.get("key"))
            _record(candidate.get("url"))
            _record(candidate.get("asset"))
            return
        if hasattr(candidate, "key"):
            _record(getattr(candidate, "key"))
        if hasattr(candidate, "url"):
            _record(getattr(candidate, "url"))
        if hasattr(candidate, "asset"):
            _record(getattr(candidate, "asset"))

    source = payload
    if hasattr(payload, "model_dump"):
        try:
            source = payload.model_dump(exclude_none=True)
        except TypeError:  # pragma: no cover - defensive fallback
            source = payload.model_dump()
    elif hasattr(payload, "dict"):
        source = payload.dict(exclude_none=True)

    if isinstance(source, dict):
        for key in (
            "brand_logo",
            "logo",
            "scenario_asset",
            "product_asset",
            "scenario_key",
            "product_key",
            "scenario_image",
            "product_image",
        ):
            _record(source.get(key))
        gallery_candidates = source.get("gallery_items") or source.get("gallery") or []
        for entry in gallery_candidates:
            _record(entry)

    return {
        "keys": keys[:8],
        "urls": urls[:3],
        "count": len(keys) + len(urls),
    }


def _ensure_trace_id(request: Request) -> str:
    trace = getattr(request.state, "trace_id", None)
    if not trace:
        trace = uuid.uuid4().hex[:8]
        request.state.trace_id = trace
    return trace


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
        put_url = presign_put_url(key, request.content_type)
    except RuntimeError as exc:  # pragma: no cover - configuration issue
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return R2PresignPutResponse(key=key, put_url=put_url, public_url=public_url_for(key))

@app.post("/api/template-posters", response_model=TemplatePosterEntry)
def upload_template_poster(request_data: TemplatePosterUploadRequest) -> TemplatePosterEntry:
    slot = request_data.slot
    filename = request_data.filename
    content_type = request_data.content_type
    data = request_data.data

    logger.info(
        "template poster upload received",
        extra={
            "slot": slot,
            "poster_filename": filename,
            "content_type": content_type,
            "size_bytes": len(data or ""),
        },
    )
    try:
        record = save_template_poster(
            slot=slot,
            filename=filename,
            content_type=content_type,
            data=data,
        )
        return poster_entry_from_record(record)
    except ValueError as exc:
        logger.warning(
            "template poster upload rejected",
            extra={
                "slot": slot,
                "poster_filename": filename,
                "content_type": content_type,
            },
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - unexpected IO failure
        logger.exception(
            "Failed to store template poster",
            extra={
                "slot": slot,
                "poster_filename": filename,
                "content_type": content_type,
            },
        )
        raise HTTPException(status_code=500, detail="服务器内部错误，请稍后重试。") from exc


@app.get("/api/template-posters", response_model=TemplatePosterCollection)
def fetch_template_posters() -> TemplatePosterCollection:
    try:
        entries = list_poster_entries()
    except Exception as exc:  # pragma: no cover - unexpected IO failure
        logger.exception("Failed to load template posters")
        raise HTTPException(status_code=500, detail="无法加载模板列表，请稍后重试。") from exc
    return TemplatePosterCollection(posters=entries)


@app.post("/api/generate-poster", response_model=GeneratePosterResponse)
async def generate_poster(request: Request) -> JSONResponse:
    trace = _ensure_trace_id(request)
    guard_info = getattr(request.state, "guard_info", {})
    content_length = request.headers.get("content-length")

    try:
        raw_payload = await read_json_relaxed(request)
        raw_assets = _summarise_assets(raw_payload.get("poster", {})) if isinstance(raw_payload, dict) else {}
        logger.info(
            "generate_poster request received",
            extra={
                "trace": trace,
                "content_length": content_length,
                "body_bytes": guard_info.get("bytes"),
                "body_has_base64": guard_info.get("has_base64"),
                "asset_summary": raw_assets,
            },
        )
        payload = _model_validate(GeneratePosterRequest, raw_payload)
    except ValidationError as exc:
        logger.warning(
            "generate_poster validation error",
            extra={"trace": trace, "errors": exc.errors()},
        )
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "generate_poster payload parsing failed",
            extra={"trace": trace},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        poster = payload.poster
        normalised_assets = _summarise_assets(poster)
        logger.info(
            "generate_poster normalised payload",
            extra={
                "trace": trace,
                "poster": _summarise_poster(poster),
                "variants": payload.variants,
                "seed": payload.seed,
                "lock_seed": payload.lock_seed,
                "prompt_bundle": _summarise_prompt_bundle(payload.prompt_bundle),
                "asset_summary": normalised_assets,
            },
        )
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
            trace_id=trace,
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
            "generate_poster completed",
            extra={
                "trace": trace,
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
                "vertex_traces": result.trace_ids,
                "fallback_used": result.fallback_used,
            },
        )
        response_payload = GeneratePosterResponse(
            layout_preview=preview,
            prompt=prompt_text,
            email_body=email_body,
            poster_image=result.poster,
            prompt_details=result.prompt_details,
            prompt_bundle=response_bundle,
            variants=result.variants,
            scores=result.scores,
            seed=result.seed,
            lock_seed=result.lock_seed,
            vertex_trace_ids=result.trace_ids or None,
            fallback_used=result.fallback_used if result.fallback_used else None,
        )
        headers: dict[str, str] = {}
        if result.trace_ids:
            headers["X-Vertex-Trace"] = ",".join(result.trace_ids)
        if result.fallback_used:
            headers["X-Vertex-Fallback"] = "1"
        headers["X-Request-Trace"] = trace
        return JSONResponse(content=_model_dump(response_payload), headers=headers)

    except Exception as exc:  # defensive logging
        logger.exception("Failed to generate poster", extra={"trace": trace})
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/send-email", response_model=SendEmailResponse)
def send_marketing_email(payload: SendEmailRequest) -> SendEmailResponse:
    try:
        return send_email(payload)
    except Exception as exc:  # pragma: no cover - ensures HTTP friendly message
        logger.exception("Failed to send marketing email")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["app"]
