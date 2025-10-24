from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, ValidationError

from app.config import get_settings
from app.middlewares.huge_or_b64_guard import RejectHugeOrBase64
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
from app.services.vertex_imagen import VertexImagen, init_vertex
from app.services.vertex_imagen3 import VertexImagen3


def _configure_logging() -> logging.Logger:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = logging.getLogger("ai-service")
    logger.debug("Logging configured at %s", level)
    return logger


logger = _configure_logging()
settings = get_settings()
app = FastAPI(title="Marketing Poster API", version="1.0.0")

try:
    from app.middlewares.huge_or_b64_guard import RejectHugeOrBase64

    app.add_middleware(
        RejectHugeOrBase64,
        max_bytes=settings.guard.max_body_bytes,
        check_base64=settings.guard.check_base64,
    )
    print("[guard] RejectHugeOrBase64 enabled")
except Exception as exc:  # pragma: no cover - startup diagnostics
    print(f"[guard] disabled (import/add failed): {exc}")

imagen_endpoint_client: VertexImagen | None = None
vertex_poster_client: VertexImagen3 | None = None

try:
    init_vertex()
except Exception as exc:  # pragma: no cover - startup diagnostics
    logger.warning("Vertex init failed: %s", exc)
else:
    try:
        imagen_endpoint_client = VertexImagen("imagen-3.0-generate-001")
    except Exception as exc:  # pragma: no cover - startup diagnostics
        imagen_endpoint_client = None
        logger.warning("VertexImagen initialization failed: %s", exc)

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

# ✅ 健康检查
def _health_payload(verbose: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": True}
    if verbose:
        payload.update(
            guard={
                "max_body_bytes": settings.guard.max_body_bytes,
                "disallow_base64": settings.guard.disallow_base64,
            },
            cors={
                "allow_credentials": cors_allow_credentials,
                "origins": cors_allow_origins,
            },
        )
    return payload


@app.get("/healthz")
def healthz(verbose: bool = Query(False, description="Return guard and CORS details.")) -> dict[str, Any]:
    return _health_payload(verbose)


@app.get("/health")
def health_check(verbose: bool = Query(False)) -> dict[str, Any]:
    payload = _health_payload(verbose)
    payload["status"] = "ok"
    if not verbose:
        payload.pop("ok", None)
    return payload


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
    """Create a tiny diagnostic image directly from Vertex."""

    if imagen_endpoint_client is None:
        raise HTTPException(status_code=503, detail="Vertex Imagen not configured")

    try:
        payload = imagen_endpoint_client.generate_bytes(
            prompt="a tiny watercolor hummingbird, diagnostic",
            size="512x512",
            return_trace=True,
        )
        if isinstance(payload, tuple):
            image_bytes, trace_id = payload
        else:  # pragma: no cover - defensive fallback
            image_bytes, trace_id = payload, None
    except Exception as exc:  # pragma: no cover - remote dependency
        logger.exception("Vertex tiny generate failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Imagen error: {exc}") from exc

    headers = {"X-Vertex-Trace": trace_id} if trace_id else None
    return Response(content=image_bytes, media_type="image/jpeg", headers=headers)


class ImagenGenerateRequest(BaseModel):
    prompt: str = Field(..., description="文生图提示词")
    size: str = Field("1024x1024", description="尺寸, 例如 1024x1024")
    negative: str | None = Field(None, description="反向提示词")


@app.post("/api/imagen/generate")
def api_imagen_generate(request_data: ImagenGenerateRequest):
    if imagen_endpoint_client is None:
        raise HTTPException(status_code=503, detail="Vertex Imagen not configured")

    try:
        payload = imagen_endpoint_client.generate_bytes(
            prompt=request_data.prompt,
            size=request_data.size,
            negative_prompt=request_data.negative,
            return_trace=True,
        )
        if isinstance(payload, tuple):
            image_bytes, trace_id = payload
        else:  # pragma: no cover - defensive fallback
            image_bytes, trace_id = payload, None
    except Exception as exc:  # pragma: no cover - remote dependency
        logger.exception("Imagen generate failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Imagen error: {exc}") from exc

    headers = {"X-Vertex-Trace": trace_id} if trace_id else None
    return Response(content=image_bytes, media_type="image/jpeg", headers=headers)



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
