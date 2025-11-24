from __future__ import annotations

import base64
import json
import logging
import os
from typing import Any, Iterable, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError, root_validator
from fastapi.responses import Response
from pydantic import ValidationError

from app.config import get_settings
from app.middlewares.body_guard import BodyGuardMiddleware
from app.schemas import (
    GeneratePosterRequest,
    GeneratePosterResponse,
    PosterGalleryItem,
    PosterInput,
    PromptBundle,
    R2PresignPutRequest,
    R2PresignPutResponse,
    StoredImage,
    SendEmailRequest,
    SendEmailResponse,
    TemplatePosterCollection,
    TemplatePosterEntry,
    TemplatePosterUploadRequest,
)
from app.services.email_sender import send_email
from app.services.glibatree import (
    configure_vertex_imagen,
    generate_poster_asset,
    generate_slot_image,
)
from app.services.image_provider.factory import get_provider
from app.services.glibatree import generate_poster_asset
from app.services.image_provider import ImageProvider
from app.services.poster import (
    build_glibatree_prompt,
    compose_marketing_email,
    render_layout_preview,
)
from app.services.s3_client import get_bytes, make_key, presigned_put_url, public_url_for
from app.services.template_variants import (
    list_poster_entries,
    poster_entry_from_record,
    save_template_poster,
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
image_provider = ImageProvider()
app = FastAPI(title="Marketing Poster API", version="1.0.0")

UPLOAD_MAX_BYTES = max(int(os.getenv("UPLOAD_MAX_BYTES", "20000000") or 0), 0)
UPLOAD_ALLOWED_MIME = {
    item.strip()
    for item in os.getenv("UPLOAD_ALLOWED_MIME", "image/png,image/jpeg,image/webp").split(",")
    if item.strip()
}


def _normalize_allowed_origins(value: Any) -> list[str]:
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
allow_origins = _normalize_allowed_origins(raw_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=86400,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)


@app.options("/{path:path}")
async def cors_preflight(path: str) -> Response:  # pragma: no cover - exercised by browsers
    return Response(status_code=204)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def _model_dump(model):
    if model is None:
        return None
    return jsonable_encoder(model, exclude_none=True)


def _model_validate(model, data):
    if hasattr(model, "model_validate"):
        return model.model_validate(data)
    if hasattr(model, "parse_obj"):
        return model.parse_obj(data)
    return model(**data)


def _decode_data_url_to_bytes(data_url: str) -> bytes:
    if "," not in data_url:
        raise ValueError("Invalid data URL: missing comma separator")
    header, encoded = data_url.split(",", 1)
    header_lower = header.lower()
    if not header_lower.startswith("data:") or ";base64" not in header_lower:
        raise ValueError("Only base64-encoded data URLs are supported")
    try:
        return base64.b64decode(encoded)
    except (binascii.Error, ValueError) as exc:  # pragma: no cover - defensive
        raise ValueError("Failed to decode data URL") from exc


def _infer_key_from_url(url: str | None) -> str | None:
    if not url:
        return None
    base = (os.getenv("R2_PUBLIC_BASE") or os.getenv("S3_PUBLIC_BASE") or "").rstrip("/")
    if base and url.startswith(f"{base}/"):
        return url[len(base) + 1 :]
    return None


def _poster_image_to_stored(image: PosterImage | None) -> StoredImage | None:
    if image is None:
        return None

    media_type = getattr(image, "media_type", "image/png") or "image/png"
    width = getattr(image, "width", None)
    height = getattr(image, "height", None)

    url = getattr(image, "url", None)
    key = getattr(image, "key", None)
    if url:
        key = key or _infer_key_from_url(url) or image.filename
        return StoredImage(
            key=key or image.filename,
            url=url,
            content_type=media_type,
            width=width,
            height=height,
        )

    data_url = getattr(image, "data_url", None)
    if data_url:
        stored = store_image_and_url(
            _decode_data_url_to_bytes(data_url),
            ext="png",
            content_type=media_type,
        )
        return StoredImage(
            key=stored["key"],
            url=stored["url"],
            content_type=stored["content_type"],
            width=width,
            height=height,
        )

    return None


def _preview_json(value: Any, limit: int = 512) -> str:
    try:
        encoded = jsonable_encoder(value)
        text = json.dumps(encoded, ensure_ascii=False)
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


def _coerce_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _asset_bytes(ref: Any) -> bytes | None:
    if not ref:
        return None

    key = getattr(ref, "key", None)
    url = getattr(ref, "url", None)

    if key:
        try:
            return get_bytes(key)
        except Exception as exc:
            logger.warning("Unable to fetch asset by key %s: %s", key, exc)

    if url:
        try:
            import httpx

            with httpx.Client(timeout=10) as client:
                resp = client.get(url)
                resp.raise_for_status()
                return resp.content
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("Unable to fetch asset by url %s: %s", url, exc)

    return None


def _asset_data_url(ref: Any) -> str | None:
    payload = _asset_bytes(ref)
    if not payload:
        return None
    mime = "image/png"
    encoded = base64.b64encode(payload).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _asset_uri(ref: Any) -> str | None:
    if not ref:
        return None
    url = getattr(ref, "url", None)
    key = getattr(ref, "key", None)
    if url:
        return str(url)
    if key:
        return public_url_for(key) or key
    return None


def _coerce_gallery(items: Iterable[PosterGalleryItem], fallback: Any) -> list[PosterGalleryItem]:
    entries: list[PosterGalleryItem] = []
    for item in items:
        if getattr(item, "asset", None) is None and getattr(item, "key", None) is None:
            entries.append(
                PosterGalleryItem(
                    caption=item.caption,
                    asset=fallback,
                    key=getattr(fallback, "key", None),
                    mode=getattr(item, "mode", "upload"),
                    prompt=getattr(item, "prompt", None),
                )
            )
        else:
            entries.append(item)
    if not entries:
        entries = [PosterGalleryItem(caption=None, asset=fallback) for _ in range(4)]

    while len(entries) < 4:
        entries.append(PosterGalleryItem(caption=None, asset=fallback))

    return entries[:4]


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

    bucket = os.getenv("R2_BUCKET") or os.getenv("S3_BUCKET")
    r2_url = f"r2://{bucket}/{key}" if bucket else None
    public_url = public_url_for(key)
    get_url = public_url
    headers: dict[str, str] = {"Content-Type": request.content_type}
    if not get_url:
        try:
            get_url = presign_get_url(key)
        except RuntimeError:
            get_url = None

    return R2PresignPutResponse(
        key=key,
        put_url=put_url,
        get_url=get_url,
        r2_url=r2_url,
        public_url=public_url,
        headers=headers,
    )

@app.post("/api/template-posters", response_model=TemplatePosterEntry)
def upload_template_poster(request_data: TemplatePosterUploadRequest) -> TemplatePosterEntry:
    slot = request_data.slot
    filename = request_data.filename
    content_type = request_data.content_type

    logger.info(
        "template poster upload received",
        extra={
            "slot": slot,
            "poster_filename": filename,
            "content_type": content_type,
            "size_bytes": request_data.size,
            "has_key": bool(request_data.key),
        },
    )
    try:
        record = save_template_poster(
            slot=slot,
            filename=filename,
            content_type=content_type,
            key=request_data.key,
            data=request_data.data,
            width=request_data.width,
            height=request_data.height,
        )
        return poster_entry_from_record(record)
    except TemplatePosterError as exc:
        logger.warning(
            "template poster upload rejected",
            extra={
                "slot": slot,
                "poster_filename": filename,
                "content_type": content_type,
            },
        )
        detail_payload = getattr(exc, "detail", None)
        raise HTTPException(status_code=400, detail=detail_payload or str(exc)) from exc
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
    if not entries:
        entries = fallback_poster_entries()
    return TemplatePosterCollection(posters=entries)


@app.post("/api/generate-slot-image", response_model=GenerateSlotImageResponse)
async def api_generate_slot_image(req: GenerateSlotImageRequest) -> GenerateSlotImageResponse:
    aspect = req.aspect or "1:1"

    try:
        key, url = await generate_slot_image(
            prompt=req.prompt,
            slot=req.slot,
            index=req.index,
            template_id=req.template_id,
            aspect=aspect,
        )
    except ResourceExhausted as exc:
        logger.warning("Vertex quota exceeded for imagen3", extra={"error": str(exc)})
        raise HTTPException(
            status_code=429,
            detail={
                "error": "vertex_quota_exceeded",
                "message": "Google Vertex 图像模型日配额已用尽，请稍后重试或改用本地上传。",
                "provider": "vertex",
            },
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - upstream failure
        logger.exception("generate_slot_image failed: %s", exc)
        raise HTTPException(status_code=500, detail="生成槽位图片失败") from exc

    return GenerateSlotImageResponse(url=url, key=key)


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
        gallery_items = _coerce_gallery(payload.gallery, payload.brand_logo)
        features = [text for text in (payload.features or []) if text]
        while len(features) < 3:
            features.append("核心卖点")
        features = features[:4]

        poster = PosterInput(
            brand_name=payload.brand_name or "品牌名称",
            agent_name=payload.agent_name or "代理名称",
            scenario_image=payload.scenario_text or "应用场景",
            product_name=payload.product_name or "主推产品",
            template_id=payload.template_id,
            features=features,
            title=payload.title or "新品海报",
            series_description=payload.series_description or "系列介绍",
            subtitle=payload.subtitle or "品牌标语",
            brand_logo=_asset_data_url(payload.brand_logo),
            scenario_key=_asset_uri(payload.scenario),
            product_key=_asset_uri(payload.product),
            gallery_items=gallery_items,
            gallery_limit=4,
            gallery_allows_prompt=False,
            gallery_allows_upload=True,
            scenario_mode="upload",
            product_mode="upload",
        )

        logger.info(
            "generate_poster normalised payload",
            extra={
                "trace": trace,
                "poster": _summarise_poster(poster),
            "generate_poster normalised payload: %s",
            {
                "poster": _summarise_poster(poster),
                "variants": payload.variants,
                "seed": payload.seed,
                "lock_seed": payload.lock_seed,
                "aspect_closeness": payload.aspect_closeness,
                "prompt_bundle": _summarise_prompt_bundle(payload.prompt_bundle),
                "asset_summary": normalised_assets,
            },
        )

        preview = render_layout_preview(poster)
        prompt_payload = _model_dump(payload.prompt_bundle)
        prompt_text, prompt_details, prompt_bundle = build_glibatree_prompt(
            poster, prompt_payload
        )

        provider_bytes: bytes | None = None
        provider_filename = f"{poster.template_id}_poster.png"

        try:
            provider_bytes = image_provider.generate(prompt=prompt_text)
        except HTTPException:
            raise
        except Exception:
            logger.exception("Image provider failed; falling back to legacy pipeline")

        result = generate_poster_asset(
            poster,
            prompt_text,
            preview,
            prompt_bundle=prompt_payload,
            prompt_details=prompt_details,
            render_mode="locked",
            variants=payload.variants,
            seed=payload.seed,
            lock_seed=payload.lock_seed,
            primary_image_bytes=provider_bytes,
            primary_image_filename=provider_filename,
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

        gallery_sources = [uri for uri in (_asset_uri(item.asset) for item in gallery_items) if uri]

        logger.info(
            "generate_poster completed",
            extra={
                "trace": trace,
                "response": {
                    "poster_filename": getattr(result.poster, "filename", None),
                    "poster_url": getattr(result.poster, "url", None),
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
                "provider": getattr(result, "provider", None),
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
            poster_url=getattr(result.poster, "url", None),
            poster_key=getattr(result.poster, "storage_key", None),
            gallery_images=gallery_sources,
        )

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
