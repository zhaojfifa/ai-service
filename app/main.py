from __future__ import annotations

import base64
import binascii
import datetime as dt
import asyncio
import json
import logging
import os
import uuid
import io
import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

from google.api_core.exceptions import ResourceExhausted
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError, root_validator
from PIL import Image, ImageDraw, ImageFont

_GENERATE_POSTER_SEMAPHORE = asyncio.Semaphore(1)


def _env_positive_int(name: str, default: int) -> int:
    try:
        return max(int(os.getenv(name, str(default)) or default), 1)
    except (TypeError, ValueError):
        return default


def _generate_queue_timeout_ms() -> int:
    return _env_positive_int("POSTER2_GENERATE_QUEUE_TIMEOUT_MS", 10000)


def _generate_runtime_timeout_ms() -> int:
    return _env_positive_int("POSTER2_GENERATE_TIMEOUT_MS", 80000)

from app.config import get_settings
from app.middlewares.body_guard import BodyGuardMiddleware
from app.ops_auth import (
    auth_state as build_ops_auth_state,
    build_session_cookie,
    is_authenticated as is_ops_authenticated,
    is_protected_api_path,
    load_ops_auth_settings,
)
from app.schemas import (
    GeneratePosterRequest,
    GeneratePosterResponse,
    GenerateSlotImageRequest,
    GenerateSlotImageResponse,
    ImageRef,
    PosterImage,
    PosterImageAsset,
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
from app.schemas.kitposter import KitPosterDraft
from app.services.email_sender import send_email
from app.services.email.attachments import (
    SUPPORTED_ATTACHMENT_TYPES,
    build_email_assets_for_record,
    derive_email_body_visual,
    resolve_email_assets,
)
from app.services.email.copy_optimizer import build_email_draft_for_poster_record
from app.services.email.providers import get_email_provider
from app.services.glibatree import (
    configure_vertex_imagen,
    generate_poster_asset,
    poster_font_runtime_summary,
    run_kitposter_state_machine,
    generate_slot_image,
)
from app.services.image_provider.factory import get_provider
from app.services.poster import (
    build_glibatree_prompt,
    compose_marketing_email,
    render_layout_preview,
)
from app.services.r2_client import (
    make_key,
    presign_get_url,
    presign_put_url,
    public_url_for,
)
from app.services.template_variants import (
    TemplatePosterError,
    fallback_poster_entries,
    list_poster_entries,
    poster_entry_from_record,
    save_template_poster,
)
from app.services.vertex_imagen import init_vertex
from app.services.storage_bridge import store_image_and_url
from app.services.poster_records import (
    append_email_delivery,
    create_poster_record,
    generate_poster_key,
    load_poster_record,
    update_email_draft,
)
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
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
FRONTEND_INDEX = FRONTEND_DIR / "index.html"

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
    if FRONTEND_INDEX.exists():
        return FileResponse(FRONTEND_INDEX)
    return {"service": "ai-service", "ok": True}


@app.head("/", include_in_schema=False)
def root_head() -> Response:
    # HEAD 按规范不返回 body
    return Response(status_code=200)


settings = get_settings()


class OpsLoginRequest(BaseModel):
    username: str
    password: str


# 健康检查，确保 Render 能检测端口开放
@app.get("/health")
@app.get("/healthz")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/api/auth/me")
def ops_auth_me(request: Request) -> dict[str, Any]:
    return build_ops_auth_state(request)


@app.post("/api/auth/ops-login")
def ops_auth_login(request: Request, payload: OpsLoginRequest) -> JSONResponse:
    auth_settings = load_ops_auth_settings()
    if not auth_settings.is_active:
        return JSONResponse({"ok": True, **build_ops_auth_state(request)})
    if payload.username != auth_settings.username or payload.password != auth_settings.password:
        return JSONResponse(
            status_code=401,
            content={
                "ok": False,
                "enabled": True,
                "authenticated": False,
                "username": None,
                "error": "invalid_ops_credentials",
            },
        )
    response = JSONResponse(
        {
            "ok": True,
            "enabled": True,
            "authenticated": True,
            "username": auth_settings.username,
        }
    )
    response.set_cookie(
        key=auth_settings.cookie_name,
        value=build_session_cookie(auth_settings.username, auth_settings),
        max_age=auth_settings.cookie_max_age_sec,
        httponly=True,
        secure=auth_settings.cookie_secure,
        samesite=auth_settings.cookie_samesite,
        path="/",
    )
    return response


@app.post("/api/auth/logout")
def ops_auth_logout(request: Request) -> JSONResponse:
    auth_settings = load_ops_auth_settings()
    response = JSONResponse(
        {
            "ok": True,
            "enabled": auth_settings.is_active,
            "authenticated": False,
            "username": None,
        }
    )
    response.delete_cookie(
        key=auth_settings.cookie_name,
        path="/",
        secure=auth_settings.cookie_secure,
        httponly=True,
        samesite=auth_settings.cookie_samesite,
    )
    return response


def _storage_runtime_summary() -> dict[str, Any]:
    endpoint = (os.getenv("R2_ENDPOINT") or os.getenv("S3_ENDPOINT") or "").strip()
    bucket = (os.getenv("R2_BUCKET") or os.getenv("S3_BUCKET") or "").strip()
    public_base = (os.getenv("R2_PUBLIC_BASE") or os.getenv("S3_PUBLIC_BASE") or "").strip()
    configured = bool(endpoint and bucket)
    backend = "r2/s3" if configured else "none"
    return {
        "backend": backend,
        "configured": configured,
        "bucket": bucket or None,
        "has_public_base": bool(public_base),
    }


def _vertex_runtime_summary() -> dict[str, Any]:
    project = (os.getenv("GCP_PROJECT_ID") or os.getenv("VERTEX_PROJECT_ID") or "").strip()
    location = (os.getenv("GCP_LOCATION") or os.getenv("VERTEX_LOCATION") or "us-central1").strip()
    generate_model = (
        os.getenv("VERTEX_IMAGEN_MODEL_GENERATE")
        or os.getenv("VERTEX_IMAGEN_GENERATE_MODEL")
        or os.getenv("VERTEX_IMAGEN_MODEL")
        or "imagen-3.0-generate-001"
    ).strip()
    edit_model = (
        os.getenv("VERTEX_IMAGEN_EDIT_MODEL")
        or os.getenv("VERTEX_IMAGEN_MODEL_EDIT")
        or "imagen-3.0-capability-001"
    ).strip()
    edit_requested = (os.getenv("VERTEX_IMAGEN_ENABLE_EDIT") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    return {
        "project": project or None,
        "location": location,
        "generate_model": generate_model,
        "edit_model": edit_model if edit_requested else None,
        "edit_model_config": edit_model,
        "edit_enabled": edit_requested,
    }


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
        from app.services.poster2.vertex_runtime import (
            set_vertex_poster_client as set_poster2_vertex_poster_client,
        )
        set_poster2_vertex_poster_client(vertex_poster_client)
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
                "edit_enabled": vertex_poster_client.enable_edit,
            },
        )

from app.services.poster2.vertex_runtime import (
    set_vertex_poster_client as set_poster2_vertex_poster_client,
)
set_poster2_vertex_poster_client(vertex_poster_client)

logger.info(
    "Runtime configuration resolved",
    extra={
        "vertex": _vertex_runtime_summary(),
        "storage": _storage_runtime_summary(),
        "fonts": poster_font_runtime_summary(),
    },
)
logger.info(
    "Runtime configuration resolved vertex=%s storage=%s fonts=%s",
    _vertex_runtime_summary(),
    _storage_runtime_summary(),
    poster_font_runtime_summary(),
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
    """Parse comma/JSON separated origins and keep only scheme + host."""

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
        raw = str(item).strip().strip('"').strip("'")
        if not raw:
            continue
        parsed = urlparse(raw)
        candidate = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else raw
        candidate = candidate.rstrip("/")
        if candidate:
            cleaned.append(candidate)
    return cleaned or ["*"]

raw_origins = (
    getattr(settings, "allowed_origins", None)
    or os.getenv("CORS_ALLOW_ORIGINS")
    or os.getenv("ALLOWED_ORIGINS")
)
allow_origins = _normalise_allowed_origins(raw_origins)

DEFAULT_CORS_ORIGINS = {
    "https://zhaojfifa.github.io",
    "https://ai-service-leob.onrender.com",
    "https://ai-service-x758.onrender.com",
}
# GitHub Pages 访问时请在 Render 环境变量 `CORS_ALLOW_ORIGINS` 中包含浏览器地址栏的完整 origin，
# 例如 https://zhaojfifa.github.io，确保预检请求与页面一致。

cors_origins = {origin.rstrip("/") for origin in allow_origins}
if not raw_origins:
    cors_origins.update(DEFAULT_CORS_ORIGINS)

allow_all = "*" in cors_origins
explicit_origins = sorted(origin for origin in cors_origins if origin != "*")
if allow_all and explicit_origins:
    allow_all = False

cors_allow_origins = explicit_origins or ["*"]
cors_allow_credentials = getattr(settings, "cors_allow_credentials", True) and not allow_all

CORS_MIDDLEWARE_KWARGS = {
    "allow_origins": cors_allow_origins,
    "allow_credentials": cors_allow_credentials,
    "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    "allow_headers": [
        "Accept",
        "Authorization",
        "Content-Type",
        "Origin",
        "X-Request-ID",
    ],
    "max_age": 86400,
}


@app.middleware("http")
async def ops_auth_gate(request: Request, call_next):
    auth_settings = load_ops_auth_settings()
    if (
        not auth_settings.is_active
        or request.method.upper() == "OPTIONS"
        or not is_protected_api_path(request.url.path)
        or is_ops_authenticated(request, auth_settings)
    ):
        return await call_next(request)
    return JSONResponse(
        status_code=401,
        content={
            "ok": False,
            "authenticated": False,
            "error": "ops_auth_required",
        },
    )


@app.middleware("http")
async def request_id_response_header(request: Request, call_next):
    response = await call_next(request)
    request_id = _poster2_request_id(request)
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


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
        images = provider.generate(
            prompt="a tiny watercolor hummingbird, diagnostic",
            width=512,
            height=512,
            negative_prompt=None,
            number_of_images=1,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - remote dependency
        logger.exception("Imagen debug generate failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Imagen error: {exc}") from exc

    image_bytes = images[0]
    headers = {"X-Image-Provider": IMAGE_PROVIDER_NAME}
    return Response(content=image_bytes, media_type="image/png", headers=headers)



class ImagenGenerateRequest(BaseModel):
    prompt: str = Field(..., description="文生图提示词")
    size: str = Field("1024x1024", description="尺寸, 例如 1024x1024")
    negative: str | None = Field(None, description="反向提示词")
    width: int | None = Field(None, gt=0, description="覆盖宽度 (像素)")
    height: int | None = Field(None, gt=0, description="覆盖高度 (像素)")
    seed: int | None = Field(None, ge=0, description="可选种子")
    guidance_scale: float | None = Field(
        None, ge=0.0, description="Imagen 指导系数"
    )
    add_watermark: bool | None = Field(
        True,
        description="是否在生成图片中嵌入水印，默认为 True，与 Vertex 默认保持一致",
    )
    input_image: ImageRef | None = Field(
        None,
        description="可选参考图像，仅接受对象存储 URL 或 Key",
    )
    variants: int | None = Field(
        1,
        ge=1,
        le=8,
        description="一次生成的图片数量，默认 1，允许范围 1-8",
    )
    store: bool | None = Field(
        None,
        description=(
            "是否强制写入对象存储。当显式传 false 时若 RETURN_BINARY_DEFAULT=0 将被拒绝。"
        ),
    )
    force_mock: bool = Field(False, description="是否强制返回后端 Mock 图片（调试/占位用）")

    @root_validator(pre=True)
    def _alias_guidance(cls, values: dict[str, object]) -> dict[str, object]:
        # 兼容历史字段 guidance
        if "guidance_scale" not in values and "guidance" in values:
            values["guidance_scale"] = values["guidance"]
        if values.get("variants") is None:
            values.pop("variants", None)
        return values


class ImagenVariant(BaseModel):
    key: str = Field(..., description="存储键")
    url: str = Field(..., description="公开或签名 URL")
    content_type: str = Field("image/png", description="MIME 类型")


class ImagenGenerateResponse(BaseModel):
    ok: bool = Field(True, description="调用是否成功")
    variants: int = Field(..., ge=1, description="返回的图片数量")
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    provider: str = Field(IMAGE_PROVIDER_NAME, description="生成后端标识")
    results: list[ImagenVariant] = Field(
        ..., description="已写入对象存储的图片列表"
    )
    key: str | None = Field(
        None,
        description="首张图片的存储键，兼容旧版客户端",
    )
    url: str | None = Field(
        None,
        description="首张图片的公开或签名 URL，兼容旧版客户端",
    )
    content_type: str | None = Field(
        None,
        description="首张图片的 MIME 类型，兼容旧版客户端",
    )
    meta: dict[str, Any] = Field(
        default_factory=dict,
        description="额外元信息，例如种子、水印状态等",
    )


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



@app.post("/api/image/generate", response_model=ImagenGenerateResponse)
@app.post("/api/imagen/generate", response_model=ImagenGenerateResponse)
def api_imagen_generate(request: Request, request_data: ImagenGenerateRequest) -> Response:
    provider = _get_image_provider()
    base_width, base_height = _resolve_dimensions(request_data.size)
    width = request_data.width or base_width
    height = request_data.height or base_height

    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
    requested_variants = int(request_data.variants or 1)
    variants = max(1, min(requested_variants, 8))
    watermark_flag = True if request_data.add_watermark is None else bool(request_data.add_watermark)

    logger.info(
        "[payload] rid=%s prompt_len=%s neg_len=%s has_seed=%s add_watermark=%s variants=%s w=%s h=%s guidance=%s",
        rid,
        len(request_data.prompt or ""),
        len(request_data.negative or ""),
        request_data.seed is not None,
        request_data.add_watermark,
        variants,
        width,
        height,
        request_data.guidance_scale,
    )

    try:
        # Support force-mock mode for debugging / placeholder images
        if getattr(request_data, "force_mock", False):
            logger.info("force_mock requested - returning mock image bytes", extra={"rid": rid})
            try:
                img = Image.new("RGBA", (width, height), (240, 240, 240, 255))
                draw = ImageDraw.Draw(img)
                text = "MOCK"
                try:
                    font = ImageFont.load_default()
                except Exception:
                    font = None
                if font:
                    tw, th = draw.textsize(text, font=font)
                else:
                    tw, th = draw.textsize(text)
                draw.text(((width - tw) / 2, (height - th) / 2), text, fill=(60, 60, 60), font=font)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                images = [buf.read()]
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Failed to build mock image: %s", exc)
                raise HTTPException(status_code=500, detail=f"Mock image generation failed: {exc}") from exc
        else:
            images = provider.generate(
                prompt=request_data.prompt,
                width=width,
                height=height,
                negative_prompt=request_data.negative,
                seed=request_data.seed,
                guidance_scale=request_data.guidance_scale,
                add_watermark=request_data.add_watermark,
                number_of_images=variants,
                trace_id=rid,
            )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - remote dependency
        logger.exception("Imagen generate failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Imagen error: {exc}") from exc

    if not images:
        raise HTTPException(status_code=502, detail="Imagen returned no data")

    allow_binary = os.getenv("RETURN_BINARY_DEFAULT", "0") == "1"
    if request_data.store is False and not allow_binary:
        raise HTTPException(
            status_code=403,
            detail="Binary responses are disabled; only URL/Key responses are permitted.",
        )

    do_store = True if request_data.store is None else request_data.store
    if not do_store:
        if variants != 1:
            raise HTTPException(
                status_code=400,
                detail="Binary responses only support a single image. Omit variants or enable storage.",
            )
        logger.info(
            "Imagen binary response allowed by configuration",
            extra={"provider": IMAGE_PROVIDER_NAME},
        )
        headers = {"X-Image-Provider": IMAGE_PROVIDER_NAME, "X-Image-Variants": str(variants)}
        return Response(content=images[0], media_type="image/png", headers=headers)

    timestamp = dt.datetime.utcnow().strftime("%Y/%m/%d")
    base_prefix = f"imagen/{timestamp}/{rid}"
    variant_models: list[ImagenVariant] = []

    for index, data in enumerate(images):
        key = f"{base_prefix}/{index}.png"
        meta = store_image_and_url(
            data,
            ext="png",
            content_type="image/png",
            key=key,
        )
        logger.info(
            "Imagen output stored to R2",
            extra={
                "provider": IMAGE_PROVIDER_NAME,
                "key": meta["key"],
                "url": meta["url"],
                "variant_index": index,
                "rid": rid,
            },
        )
        variant_models.append(ImagenVariant(**meta))

    if not variant_models:
        raise HTTPException(status_code=500, detail="Failed to persist generated images")

    primary = variant_models[0]
    seed_used = request_data.seed if (not watermark_flag and request_data.seed is not None) else None

    payload = ImagenGenerateResponse(
        ok=True,
        variants=len(variant_models),
        width=width,
        height=height,
        provider=IMAGE_PROVIDER_NAME,
        results=variant_models,
        key=primary.key,
        url=primary.url,
        content_type=primary.content_type,
        meta={
            "add_watermark": watermark_flag,
            "seed_requested": request_data.seed,
            "seed_used": seed_used,
            "guidance_scale": request_data.guidance_scale,
            "requested_variants": requested_variants,
        },
    )
    return JSONResponse(payload.model_dump(exclude_none=True))




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


def _stored_to_asset(image: StoredImage | None) -> PosterImageAsset | None:
    if image is None:
        return None
    if not image.url or not image.key:
        return None
    return PosterImageAsset(
        key=image.key,
        url=image.url,
        width=getattr(image, "width", None),
        height=getattr(image, "height", None),
        content_type=getattr(image, "content_type", None),
    )


def _debug_artifact_payload(records: Any) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for record in records or []:
        if hasattr(record, "__dict__"):
            item = dict(record.__dict__)
        elif isinstance(record, dict):
            item = dict(record)
        else:
            continue
        payload.append(
            {
                "name": item.get("name"),
                "key": item.get("key"),
                "url": item.get("url"),
                "local_path": item.get("local_path"),
                "content_type": item.get("content_type"),
            }
        )
    return payload


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


def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    essential = {"X-Request-Trace", "X-Vertex-Trace", "X-Vertex-Fallback"}
    safe: dict[str, str] = {}
    for key, value in (headers or {}).items():
        if value is None:
            continue
        text = str(value)
        if len(text) > 1024:
            continue
        try:
            text.encode("latin-1")
            safe[key] = text
            continue
        except UnicodeEncodeError:
            if key not in essential:
                continue
        encoded = quote(text, safe="")
        if len(encoded) > 1024:
            continue
        safe[key] = f"utf8:{encoded}"
    return safe


def _extract_product_images(payload: dict[str, Any]) -> list[str]:
    items: list[str] = []
    if not isinstance(payload, dict):
        return items
    images = payload.get("product_images")
    if isinstance(images, list):
        for item in images:
            if isinstance(item, str) and item.strip():
                items.append(item.strip())
    for key in ("product_image_1", "product_image_2", "product_asset", "product_key"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            items.append(value.strip())
    return items


def _build_run_id(payload: Any, seed: int | None) -> str:
    encoded = jsonable_encoder(payload, exclude_none=True)
    text = json.dumps(encoded, ensure_ascii=False, sort_keys=True)
    if seed is not None:
        text = f"{text}|seed:{seed}"
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _validate_kitposter_draft(raw_payload: dict[str, Any]) -> KitPosterDraft | None:
    draft_payload = raw_payload.get("draft") or raw_payload.get("poster_draft")
    if not draft_payload:
        return None
    try:
        if hasattr(KitPosterDraft, "model_validate"):
            return KitPosterDraft.model_validate(draft_payload)
        return KitPosterDraft.parse_obj(draft_payload)
    except ValidationError as exc:
        detail = {
            "error_code": "invalid_draft",
            "message": "Draft validation failed.",
            "details": exc.errors(),
        }
        raise HTTPException(status_code=422, detail=detail) from exc


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


def _legacy_generate_failure_response(
    *,
    status_code: int,
    trace: str,
    stage: str,
    code: str,
    message: str,
    retryable: bool,
    timeout_ms: int | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "failed",
            "error": "poster_generation_failed",
            "request_id": trace,
            "failure": {
                "stage": stage,
                "code": code,
                "message": message,
                "detail": message,
                "exception_class": "TimeoutError",
                "retryable": retryable,
                **({"timeout_ms": timeout_ms} if timeout_ms is not None else {}),
            },
        },
        headers={"X-Request-Trace": trace},
    )


def _release_legacy_generation_semaphore(task: asyncio.Task) -> None:
    try:
        task.exception()
    except asyncio.CancelledError:
        pass
    finally:
        _GENERATE_POSTER_SEMAPHORE.release()


@app.post("/api/generate-poster", response_model=GeneratePosterResponse)
async def generate_poster(request: Request) -> JSONResponse:
    trace = _ensure_trace_id(request)
    guard_info = getattr(request.state, "guard_info", {})
    content_length = request.headers.get("content-length")

    try:
        raw_payload = await read_json_relaxed(request)
        raw_assets = _summarise_assets(raw_payload.get("poster", {})) if isinstance(raw_payload, dict) else {}
        draft = _validate_kitposter_draft(raw_payload)
        render_mode_raw = raw_payload.get("render_mode") if isinstance(raw_payload, dict) else None
        if render_mode_raw in {"kitposter1_a", "kitposter1_b"} and draft is None:
            poster_payload = raw_payload.get("poster", {}) if isinstance(raw_payload, dict) else {}
            if not _extract_product_images(poster_payload):
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_code": "product_images_required",
                        "message": "At least one product image is required.",
                        "details": {"field": "product_images"},
                    },
                )
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

        def _run_legacy_generation():
            seed_value = (
                draft.options.seed
                if draft is not None and draft.options.seed is not None
                else payload.seed
            )
            if draft is not None or payload.render_mode in {"kitposter1_a", "kitposter1_b"}:
                result, extra_warnings, degraded_extra, quality_mode_used = run_kitposter_state_machine(
                    draft=draft,
                    poster=poster,
                    prompt=prompt_text,
                    preview=preview,
                    prompt_bundle=prompt_payload,
                    prompt_details=prompt_details,
                    render_mode=payload.render_mode,
                    variants=payload.variants,
                    seed=seed_value,
                    lock_seed=payload.lock_seed,
                    trace_id=trace,
                    aspect_closeness=payload.aspect_closeness,
                    quality_mode=(draft.options.quality_mode if draft is not None else "stable"),
                )
            else:
                result = generate_poster_asset(
                    poster,
                    prompt_text,
                    preview,
                    prompt_bundle=prompt_payload,
                    prompt_details=prompt_details,
                    render_mode=payload.render_mode,
                    variants=payload.variants,
                    seed=seed_value,
                    lock_seed=payload.lock_seed,
                    trace_id=trace,
                    aspect_closeness=payload.aspect_closeness,
                )
                extra_warnings = []
                degraded_extra = False
                quality_mode_used = "stable"
            return result, extra_warnings, degraded_extra, quality_mode_used, seed_value

        queue_timeout_ms = _generate_queue_timeout_ms()
        runtime_timeout_ms = _generate_runtime_timeout_ms()
        try:
            await asyncio.wait_for(
                _GENERATE_POSTER_SEMAPHORE.acquire(),
                timeout=queue_timeout_ms / 1000,
            )
        except TimeoutError:
            logger.warning(
                "generate_poster queue timeout",
                extra={"trace": trace, "timeout_ms": queue_timeout_ms},
            )
            return _legacy_generate_failure_response(
                status_code=503,
                trace=trace,
                stage="semaphore_wait",
                code="poster_generate_queue_timeout",
                message="poster generate queue wait exceeded timeout",
                retryable=True,
                timeout_ms=queue_timeout_ms,
            )

        generation_task = asyncio.create_task(asyncio.to_thread(_run_legacy_generation))
        release_deferred = False
        try:
            result, extra_warnings, degraded_extra, quality_mode_used, seed_value = await asyncio.wait_for(
                asyncio.shield(generation_task),
                timeout=runtime_timeout_ms / 1000,
            )
        except TimeoutError:
            release_deferred = True
            generation_task.add_done_callback(_release_legacy_generation_semaphore)
            logger.warning(
                "generate_poster runtime timeout",
                extra={"trace": trace, "timeout_ms": runtime_timeout_ms},
            )
            return _legacy_generate_failure_response(
                status_code=504,
                trace=trace,
                stage="generate_runtime",
                code="poster_generate_timeout",
                message="poster generate runtime exceeded timeout",
                retryable=True,
                timeout_ms=runtime_timeout_ms,
            )
        finally:
            if not release_deferred:
                _GENERATE_POSTER_SEMAPHORE.release()

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
                "provider": getattr(result, "provider", None),
                "render_path_used": getattr(result, "render_path_used", None),
                "edit_attempted": getattr(result, "edit_attempted", None),
                "edit_succeeded": getattr(result, "edit_succeeded", None),
                "fallback_reason": getattr(result, "fallback_reason", None),
                "debug_artifact_count": len(getattr(result, "debug_artifacts", []) or []),
            },
        )
        warnings = sorted(set((result.warnings or []) + extra_warnings))
        run_id = _build_run_id(draft or raw_payload, seed_value)
        seed_used = result.seed if result.seed is not None else seed_value
        response_payload = GeneratePosterResponse(
            status="success",
            warnings=warnings,
            degraded=result.degraded or degraded_extra,
            run_id=run_id,
            seed_used=seed_used,
            quality_mode_used=quality_mode_used,
            layout_preview=preview,
            prompt=prompt_text,
            email_body=email_body,
            poster_image=result.poster,
            final_poster=result.poster,
            prompt_details=result.prompt_details,
            prompt_bundle=response_bundle,
            variants=result.variants,
            scores=result.scores,
            seed=result.seed,
            lock_seed=result.lock_seed,
            vertex_trace_ids=result.trace_ids or None,
            fallback_used=result.fallback_used if result.fallback_used else None,
            degraded_reason=result.degraded_reason,
            render_path_used=result.render_path_used,
            edit_attempted=result.edit_attempted,
            edit_succeeded=result.edit_succeeded,
            fallback_reason=result.fallback_reason,
            debug_artifacts=_debug_artifact_payload(result.debug_artifacts),
            scenario_image=_stored_to_asset(result.scenario_image),
            product_image=_stored_to_asset(result.product_image),
            gallery_images=[_stored_to_asset(item) for item in result.gallery_images or [] if _stored_to_asset(item)],
        )

        primary_url = getattr(result.poster, "url", None) or response_payload.poster_url
        primary_key = getattr(result.poster, "key", None) or response_payload.poster_key

        update_kwargs: dict[str, Any] = {"results": None}
        if primary_url:
            update_kwargs["poster_url"] = primary_url
        if primary_key:
            update_kwargs["poster_key"] = primary_key

        if hasattr(response_payload, "model_copy"):
            response_payload = response_payload.model_copy(update=update_kwargs)  # type: ignore[attr-defined]
        else:  # pragma: no cover - Pydantic v1 fallback
            payload_dict = response_payload.dict()
            payload_dict.update(update_kwargs)
            response_payload = GeneratePosterResponse(**payload_dict)

        slot_assets = {
            "scenario_url": getattr(response_payload.scenario_image, "url", None),
            "product_url": getattr(response_payload.product_image, "url", None),
            "gallery_count": len(response_payload.gallery_images or []),
            "poster_url": getattr(response_payload, "poster_url", None),
        }
        logger.info(
            "generate_poster slot assets prepared",
            extra={"trace": trace, "slot_assets": slot_assets},
        )
        headers: dict[str, str] = {}
        if result.trace_ids:
            headers["X-Vertex-Trace"] = ",".join(result.trace_ids)
        if result.fallback_used:
            headers["X-Vertex-Fallback"] = "1"
        headers["X-Request-Trace"] = trace
        safe_headers = _sanitize_headers(headers)
        return JSONResponse(content=_model_dump(response_payload), headers=safe_headers)

    except ResourceExhausted as exc:
        logger.warning(
            "Vertex quota exceeded for imagen3", extra={"trace": trace, "error": str(exc)}
        )
        raise HTTPException(
            status_code=429,
            detail={
                "error": "vertex_quota_exceeded",
                "message": "Google Vertex 图像模型日配额已用尽，请稍后重试或改用本地上传。",
                "provider": "vertex",
            },
        ) from exc
    except Exception as exc:  # defensive logging
        logger.exception("Failed to generate poster", extra={"trace": trace})
        raise HTTPException(
            status_code=500,
            detail={"error": "poster_generation_failed", "message": str(exc)},
        ) from exc


@app.post("/api/send-email", response_model=SendEmailResponse)
def send_marketing_email(payload: SendEmailRequest) -> SendEmailResponse:
    try:
        return send_email(payload)
    except Exception as exc:  # pragma: no cover - ensures HTTP friendly message
        logger.exception("Failed to send marketing email")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Poster 2.0 — /api/v2/generate-poster
# ---------------------------------------------------------------------------

from app.schemas.poster2 import (
    EmailPreviewRequest,
    EmailPreviewResponse,
    EmailSendV2Request,
    EmailSendV2Response,
    EmailBanner,
    GeneratePosterV2Request,
    GeneratePosterV2Response,
    PosterRecordResponse,
    Poster2DebugArtifacts,
    EmailAssemblyPreviewResponse,
    ProductAssets,
    ProductTruth,
    WorkbenchCreateRequest,
    WorkbenchEmailSendRequest,
    WorkbenchEmailSendResponse,
    WorkbenchPatchRequest,
    WorkbenchRecordResponse,
    WorkbenchSelectVisualRequest,
)
from app.services.email.assembly import build_email_assembly
from app.services.email.workbench_send import normalize_recipients
from app.services.workbench_records import (
    append_send_attempts,
    create_workbench_record,
    generate_workbench_key,
    load_workbench_record,
    select_email_body_visual,
    set_poster_candidate,
    update_workbench_record,
)
from app.services.workbench_candidate_generation import (
    CANDIDATE_TEMPLATE,
    build_candidate_payload,
)
from app.services.poster2.contracts import (
    AssetRef as P2AssetRef,
    CopyOptimizationSpec as P2CopyOptimizationSpec,
    PosterSpec as P2PosterSpec,
    StyleSpec as P2StyleSpec,
)
from app.services.poster2.errors import PosterGenerationStageError, failure_response_payload
from app.services.poster2.pipeline import (
    PosterPipeline as P2Pipeline,
    reset_request_lifecycle_id,
    set_request_lifecycle_id,
)
from app.services.poster2.template_registry import (
    is_campaign_explainer_template,
    is_catalog_hero_template,
    is_email_campaign_composite_template,
)

_poster2_pipeline: P2Pipeline | None = None


def _get_poster2_pipeline() -> P2Pipeline:
    global _poster2_pipeline
    if _poster2_pipeline is None:
        _poster2_pipeline = P2Pipeline()
    return _poster2_pipeline


def _to_asset_ref(ref) -> P2AssetRef:
    if ref is None:
        return None
    return P2AssetRef(url=ref.url, key=ref.key)


def _validate_poster2_renderer_request(template_id: str, renderer_mode: str) -> None:
    if renderer_mode != "puppeteer":
        return
    # Family A campaign-explainer lineage and the additive portrait catalog-hero family
    # may use the Chromium engine. Family B still rejects an explicit puppeteer request.
    if not (
        is_campaign_explainer_template(template_id)
        or is_catalog_hero_template(template_id)
        or is_email_campaign_composite_template(template_id)
    ):
        raise ValueError(
            "renderer_mode=puppeteer is only enabled for the template_dual_v2 "
            "campaign-explainer lineage during the pilot"
        )


async def _generate_catalog_hero_v1(
    request_id: str | None,
    spec: "P2PosterSpec",
    payload: GeneratePosterV2Request,
) -> JSONResponse:
    """Additive portrait catalog-hero render path. Dispatched ONLY for catalog-hero
    template ids; does NOT enter PosterPipeline / RendererSelector (Family A/B untouched).
    Reuses the existing AssetLoader for asset resolution and the request schema/slots."""
    import base64
    import hashlib
    from io import BytesIO

    from app.services.poster2 import catalog_hero as _ch
    from app.services.poster2.asset_loader import AssetLoader as _AssetLoader

    _poster2_lifecycle_log("catalog_hero_dispatch", request_id=request_id, template_id=payload.template_id)
    assets = await _AssetLoader().load(spec)
    inputs = _ch.resolve_inputs(
        brand_name=payload.brand_name,
        agent_name=payload.agent_name,
        title=payload.title,
        subtitle=payload.subtitle or "",
        sku_text=payload.sku_text or "",
        features=list(payload.features or []),
        cta_label=payload.on_poster_cta_label or "",
        cta_email=payload.on_poster_cta_email or "",
        logo=assets.logo,
        product=assets.product,
        scenario_image=assets.scenario,
        gallery_images=list(assets.gallery or []),
    )
    result = await _ch.render_catalog_hero_async(inputs)

    buf = BytesIO()
    result.image.save(buf, format="PNG")
    png_bytes = buf.getvalue()
    final_hash = hashlib.sha256(png_bytes).hexdigest()[:16]
    final_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode()
    trace_id = request_id or final_hash

    response_payload = GeneratePosterV2Response(
        poster_key=generate_poster_key(),
        trace_id=trace_id,
        final_url=final_url,
        final_hash=final_hash,
        foreground_url=final_url,
        background_url="",
        background_seed=0,
        background_model="none",
        template_id=_ch.CATALOG_HERO_TEMPLATE_ID,
        template_version=_ch.CATALOG_HERO_TEMPLATE_VERSION,
        template_contract_version=_ch.CATALOG_HERO_CONTRACT_VERSION,
        engine_version="catalog_hero_v1",
        renderer_mode=payload.renderer_mode,
        render_engine_used=result.engine,
        foreground_renderer=result.engine,
        background_renderer="none",
        poster_spec_hash=final_hash,
        timings_ms=result.timings_ms,
        debug_artifacts=Poster2DebugArtifacts(),
        degraded=result.degraded,
        degraded_reason="chromium_unavailable_pillow_fallback" if result.degraded else None,
        structure_complete=result.contract_review["structure_complete"],
        incomplete_structure=not result.contract_review["structure_complete"],
        deliverable=result.contract_review["structure_complete"],
        missing_required_slots=result.contract_review["missing_required_slots"],
        catalog_hero_contract_review=result.contract_review,
        catalog_hero_grammar_profile=result.grammar_profile,
    )
    response_payload_dict = _model_dump(response_payload)
    # omit empty optional reviews that belong to the Family A/B response shape
    for empty_key in ("template_b_parity_review",):
        if response_payload_dict.get(empty_key) is None:
            response_payload_dict.pop(empty_key, None)

    poster_key = response_payload.poster_key
    create_poster_record(
        poster_key=poster_key,
        request_snapshot=_model_dump(payload),
        render_result=response_payload_dict,
        final_poster={
            "filename": f"{trace_id}-catalog-hero.png",
            "media_type": "image/png",
            "width": result.image.width,
            "height": result.image.height,
            "storage_key": trace_id,
            "url": final_url,
            "key": None,
        },
    )
    _poster2_lifecycle_log("response_ready", request_id=request_id, status_code=200, trace_id=trace_id)
    return JSONResponse(
        content=response_payload_dict,
        headers={"X-Request-ID": request_id} if request_id else None,
    )


async def _generate_email_campaign_composite_v1(
    request_id: str | None,
    spec: "P2PosterSpec",
    payload: GeneratePosterV2Request,
) -> JSONResponse:
    """Additive campaign-composite render path. Dispatched ONLY for the email_campaign_composite_v1
    template id; does NOT enter PosterPipeline / RendererSelector (Family A/B / Product Sheet / Catalog
    Hero untouched). Reuses the existing AssetLoader + the dedicated email_campaign_composite renderer.
    All business truth is deterministic (defaults = the validated case001 truth); the scenario image is an
    operator-gated visual substrate only and is NEVER treated as business truth."""
    import base64
    import hashlib
    from io import BytesIO

    from app.services.poster2 import email_campaign_composite as _ecc
    from app.services.poster2.asset_loader import AssetLoader as _AssetLoader

    # Stage-tracked so any failure returns JSON (never an HTML 502/500) with request_id/stage/error_type.
    stage = "entry"
    try:
        n_gallery = len(payload.gallery_images or [])
        logger.info(
            "ecc.generate entry request_id=%s template_id=%s renderer_mode=%s assets[product=%s logo=%s scenario=%s gallery=%d]",
            request_id, payload.template_id, payload.renderer_mode,
            bool(payload.product_image and payload.product_image.url),
            bool(payload.logo and payload.logo.url),
            bool(payload.scenario_image and payload.scenario_image.url), n_gallery,
        )

        stage = "asset_fetch"
        logger.info("ecc.generate asset_fetch_start request_id=%s product=1 logo=%d scenario=%d gallery=%d",
                    request_id, 1 if payload.logo else 0, 1 if payload.scenario_image else 0, n_gallery)
        assets = await _AssetLoader().load(spec)
        logger.info("ecc.generate asset_fetch_success request_id=%s resolved[product=%s logo=%s scenario=%s gallery=%d]",
                    request_id, assets.product is not None, assets.logo is not None,
                    assets.scenario is not None, len(assets.gallery or []))

        stage = "resolve_inputs"
        inputs = _ecc.resolve_inputs(
            title=payload.title or None,
            strapline=payload.subtitle or None,
            callouts=list(payload.features) if payload.features else None,
            contact=None,
            logo=assets.logo,
            product=assets.product,
            gallery_images=list(assets.gallery or []),
            substrate_image=assets.scenario,  # operator-gated campaign substrate; never business truth
        )

        stage = "render"
        logger.info("ecc.generate render_start request_id=%s renderer_selected=email_campaign_composite_v1/puppeteer", request_id)
        result = await _ecc.render_async(inputs, request_id=request_id)
        logger.info("ecc.generate render_done request_id=%s engine=%s degraded=%s", request_id, result.engine, result.degraded)

        stage = "encode"
        buf = BytesIO()
        result.image.save(buf, format="PNG")
        png_bytes = buf.getvalue()
        final_hash = hashlib.sha256(png_bytes).hexdigest()[:16]
        trace_id = request_id or final_hash
        data_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode()

        # Additive R2 hosting bridge (this family only): host the PNG so the email flow references a small
        # HTTPS URL instead of a ~9.5MB inline data: URL. Falls back to the data: URL if R2 is not configured.
        stage = "r2_upload"
        poster_hosting = "inline_data_url"
        final_url = data_url
        try:
            from app.services.r2_client import make_key as _r2_make_key, put_bytes as _r2_put_bytes

            logger.info("ecc.generate poster_upload_start request_id=%s bytes=%d", request_id, len(png_bytes))
            hosted_url = _r2_put_bytes(
                _r2_make_key("poster2/email_campaign_composite", f"{trace_id}.png"),
                png_bytes,
                content_type="image/png",
            )
            if hosted_url and hosted_url.startswith("https://"):
                final_url, poster_hosting = hosted_url, "r2"
            logger.info("ecc.generate poster_upload_done request_id=%s hosting=%s", request_id, poster_hosting)
        except Exception as _up_exc:  # never fail generation on a hosting error — fall back to inline
            poster_hosting = "inline_data_url"
            logger.warning("ecc.generate poster_upload_fail request_id=%s error_type=%s -> inline_data_url",
                           request_id, type(_up_exc).__name__)
        stage = "respond"
        review = dict(result.contract_review)
        review["poster_hosting"] = poster_hosting
    except Exception as exc:  # ANY catchable failure -> JSON (no HTML); records request_id/stage/error_type
        logger.exception("ecc.generate FAILED request_id=%s stage=%s error_type=%s", request_id, stage, type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": "email_campaign_composite_generate_failed",
                     "request_id": request_id, "stage": stage,
                     "error_type": type(exc).__name__, "message": str(exc)[:300]},
            headers={"X-Request-ID": request_id} if request_id else None,
        )

    response_payload = GeneratePosterV2Response(
        poster_key=generate_poster_key(),
        trace_id=trace_id,
        final_url=final_url,
        final_hash=final_hash,
        foreground_url=final_url,
        background_url="",
        background_seed=0,
        background_model="none",
        template_id=_ecc.EMAIL_CAMPAIGN_COMPOSITE_TEMPLATE_ID,
        template_version=_ecc.EMAIL_CAMPAIGN_COMPOSITE_TEMPLATE_VERSION,
        template_contract_version=_ecc.EMAIL_CAMPAIGN_COMPOSITE_CONTRACT_VERSION,
        engine_version="email_campaign_composite_v1",
        renderer_mode=payload.renderer_mode,
        render_engine_used=result.engine,
        foreground_renderer=result.engine,
        background_renderer="none",
        poster_spec_hash=final_hash,
        timings_ms=result.timings_ms,
        debug_artifacts=Poster2DebugArtifacts(),
        degraded=result.degraded,
        degraded_reason="chromium_unavailable_pillow_fallback" if result.degraded else None,
        structure_complete=review["structure_complete"],
        incomplete_structure=not review["structure_complete"],
        deliverable=review["structure_complete"],
        missing_required_slots=review["missing_required_slots"],
        email_campaign_composite_contract_review=review,
    )
    response_payload_dict = _model_dump(response_payload)
    for empty_key in ("template_b_parity_review", "catalog_hero_contract_review", "catalog_hero_grammar_profile"):
        if response_payload_dict.get(empty_key) is None:
            response_payload_dict.pop(empty_key, None)

    create_poster_record(
        poster_key=response_payload.poster_key,
        request_snapshot=_model_dump(payload),
        render_result=response_payload_dict,
        final_poster={
            "filename": f"{trace_id}-email-campaign-composite.png",
            "media_type": "image/png",
            "width": result.image.width,
            "height": result.image.height,
            "storage_key": trace_id,
            "url": final_url,
            "key": None,
        },
    )
    _poster2_lifecycle_log("response_ready", request_id=request_id, status_code=200, trace_id=trace_id)
    return JSONResponse(
        content=response_payload_dict,
        headers={"X-Request-ID": request_id} if request_id else None,
    )


def _poster2_request_log_fields(request: Request, payload: GeneratePosterV2Request) -> dict[str, Any]:
    request_id = _poster2_request_id(request)
    return {
        "request_id": request_id or None,
        "origin": request.headers.get("Origin"),
        "content_type": request.headers.get("Content-Type"),
        "content_length": request.headers.get("Content-Length"),
        "template_id": payload.template_id,
        "renderer_mode": payload.renderer_mode,
        "feature_count": len(payload.features),
        "gallery_count": len(payload.gallery_images),
        "gallery_input_count_raw": payload.gallery_input_count_raw,
        "gallery_input_count_normalized": payload.gallery_input_count_normalized,
        "gallery_requested_count": payload.gallery_requested_count,
        "gallery_autofill_applied": payload.gallery_autofill_applied,
        "copy_optimization_mode": payload.copy_optimization.mode,
        "copy_optimization_decision": payload.copy_optimization.decision,
        "has_logo": payload.logo is not None,
        "has_scenario_image": payload.scenario_image is not None,
        "has_product_key": bool(payload.product_image.key),
        "product_url_host": urlparse(payload.product_image.url).netloc or None,
    }


def _poster2_final_poster_payload(manifest) -> dict[str, Any]:
    return {
        "filename": f"{manifest.trace_id}-final.png",
        "media_type": "image/png",
        "width": None,
        "height": None,
        "storage_key": manifest.trace_id,
        "url": manifest.final_url,
        "key": None,
    }


def _poster2_request_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID") or request.headers.get("X-Request-Id")


def _poster2_lifecycle_log(event: str, *, request_id: str | None, **fields: Any) -> None:
    logger.info(
        "poster2.lifecycle event=%s request_id=%s fields=%s",
        event,
        request_id,
        {key: value for key, value in fields.items() if value is not None},
    )


def _poster2_failure_response(
    *,
    status_code: int,
    request_id: str | None,
    stage: str,
    code: str,
    message: str,
    retryable: bool,
    timeout_ms: int | None = None,
    exception_class: str = "TimeoutError",
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": False,
            "error": "poster2_generation_failed",
            "error_code": code,
            "request_id": request_id,
            "failure": {
                "stage": stage,
                "code": code,
                "message": message,
                "detail": message,
                "exception_class": exception_class,
                "retryable": retryable,
                **({"timeout_ms": timeout_ms} if timeout_ms is not None else {}),
            },
        },
        headers={"X-Request-ID": request_id} if request_id else None,
    )


def _poster2_stage_error_status(exc: PosterGenerationStageError) -> int:
    if exc.stage != "puppeteer_render":
        return exc.status_code
    if exc.code.endswith("_timeout") or exc.context.timeout_ms is not None:
        return 504
    return 503


def _poster2_stage_failure_response(
    *,
    error: PosterGenerationStageError,
    request_id: str | None,
) -> JSONResponse:
    status_code = _poster2_stage_error_status(error)
    payload = failure_response_payload(error=error, request_id=request_id)
    payload["error_code"] = error.code
    return JSONResponse(
        status_code=status_code,
        content=payload,
        headers={"X-Request-ID": request_id} if request_id else None,
    )


@app.post(
    "/api/v2/generate-poster",
    response_model=GeneratePosterV2Response,
    summary="Poster 2.0 — structure-stable generation",
    tags=["poster-v2"],
)
async def generate_poster_v2(request: Request, payload: GeneratePosterV2Request) -> GeneratePosterV2Response:
    """
    Poster 2.0 pipeline:
      1. Adobe Firefly generates background only (no text / no structure).
      2. A deterministic renderer renders all foreground elements via Pillow or Chromium.
      3. Composer alpha-composites the two layers.

    Text, logo, product, and gallery are NEVER passed through a generative model.
    """
    request_log = _poster2_request_log_fields(request, payload)
    request_id = request_log["request_id"]
    _poster2_lifecycle_log(
        "request_received",
        request_id=request_id,
        template_id=payload.template_id,
        renderer_mode=payload.renderer_mode,
    )
    _poster2_lifecycle_log("auth_passed", request_id=request_id)
    logger.info("poster2: request start %s", request_log)
    try:
        _validate_poster2_renderer_request(payload.template_id, payload.renderer_mode)
        spec = P2PosterSpec(
            brand_name=payload.brand_name,
            agent_name=payload.agent_name,
            title=payload.title,
            subtitle=payload.subtitle or "",
            features=tuple(payload.features),
            product_image=P2AssetRef(
                url=payload.product_image.url,
                key=payload.product_image.key,
            ),
            product_secondary_image=_to_asset_ref(payload.product_secondary_image),
            logo=_to_asset_ref(payload.logo),
            scenario_image=_to_asset_ref(payload.scenario_image),
            gallery_images=tuple(
                P2AssetRef(url=g.url, key=g.key) for g in payload.gallery_images
            ),
            gallery_input_count_raw=payload.gallery_input_count_raw,
            gallery_input_count_normalized=payload.gallery_input_count_normalized,
            gallery_requested_count=payload.gallery_requested_count,
            gallery_autofill_applied=payload.gallery_autofill_applied,
            bottom_mode=payload.bottom_mode,
            gallery_mode=payload.gallery_mode,
            style=P2StyleSpec(
                prompt=payload.style.prompt,
                negative_prompt=payload.style.negative_prompt,
                seed=payload.style.seed,
                palette=tuple(payload.style.palette) if payload.style.palette else None,
            ),
            copy_optimization=P2CopyOptimizationSpec(
                mode=payload.copy_optimization.mode,
                decision=payload.copy_optimization.decision,
                accepted_title=payload.copy_optimization.accepted_title or "",
                accepted_subtitle=payload.copy_optimization.accepted_subtitle or "",
                accepted_features=tuple(payload.copy_optimization.accepted_features or []),
            ),
            template_id=payload.template_id,
            export_format=payload.export_format,
            renderer_mode=payload.renderer_mode,
            composition_strategy=payload.composition_strategy,
            materials_images=tuple(
                P2AssetRef(url=m.url, key=m.key) for m in (payload.materials_images or [])
            ),
            description_title=payload.description_title or "",
            description_body=payload.description_body or "",
            sku_text=payload.sku_text or "",
            availability_badge=payload.availability_badge or "",
            tariff_mode=payload.tariff_mode or "",
            on_poster_cta_label=payload.on_poster_cta_label or "",
            on_poster_cta_email=payload.on_poster_cta_email or "",
        )

        # Additive portrait catalog-hero family: dispatched to a dedicated render path
        # that never enters PosterPipeline (Family A/B code paths untouched).
        if is_catalog_hero_template(payload.template_id):
            response = await _generate_catalog_hero_v1(request_id, spec, payload)
            _poster2_lifecycle_log("response_ready", request_id=request_id, status_code=200)
            return response

        # Additive campaign-composite family: dedicated render path, never enters PosterPipeline.
        if is_email_campaign_composite_template(payload.template_id):
            response = await _generate_email_campaign_composite_v1(request_id, spec, payload)
            _poster2_lifecycle_log("response_ready", request_id=request_id, status_code=200)
            return response

        pipeline = _get_poster2_pipeline()
        queue_timeout_ms = _generate_queue_timeout_ms()
        runtime_timeout_ms = _generate_runtime_timeout_ms()
        _poster2_lifecycle_log(
            "semaphore_wait_start",
            request_id=request_id,
            timeout_ms=queue_timeout_ms,
        )
        try:
            await asyncio.wait_for(
                _GENERATE_POSTER_SEMAPHORE.acquire(),
                timeout=queue_timeout_ms / 1000,
            )
        except TimeoutError:
            _poster2_lifecycle_log(
                "timeout",
                request_id=request_id,
                stage="semaphore_wait",
                timeout_ms=queue_timeout_ms,
            )
            _poster2_lifecycle_log("response_ready", request_id=request_id, status_code=503)
            return _poster2_failure_response(
                status_code=503,
                request_id=request_id,
                stage="semaphore_wait",
                code="generate_busy",
                message="poster2 generate queue wait exceeded timeout",
                retryable=True,
                timeout_ms=queue_timeout_ms,
            )
        _poster2_lifecycle_log("semaphore_acquired", request_id=request_id)
        lifecycle_token = set_request_lifecycle_id(request_id)
        try:
            _poster2_lifecycle_log(
                "pipeline_start",
                request_id=request_id,
                timeout_ms=runtime_timeout_ms,
            )
            manifest = await asyncio.wait_for(
                pipeline.run(spec),
                timeout=runtime_timeout_ms / 1000,
            )
        except TimeoutError:
            _poster2_lifecycle_log(
                "timeout",
                request_id=request_id,
                stage="generate_runtime",
                timeout_ms=runtime_timeout_ms,
            )
            _poster2_lifecycle_log("response_ready", request_id=request_id, status_code=504)
            return _poster2_failure_response(
                status_code=504,
                request_id=request_id,
                stage="generate_runtime",
                code="generate_timeout",
                message="poster2 generate runtime exceeded timeout",
                retryable=True,
                timeout_ms=runtime_timeout_ms,
            )
        finally:
            reset_request_lifecycle_id(lifecycle_token)
            _GENERATE_POSTER_SEMAPHORE.release()
        logger.info(
            "poster2: request success request_id=%s trace_id=%s template=%s requested=%s effective=%s degraded=%s total_ms=%s",
            request_id,
            manifest.trace_id,
            manifest.template_id,
            manifest.renderer_mode,
            manifest.render_engine_used,
            manifest.degraded,
            manifest.timings_ms.get("total_ms"),
        )

        poster_key = generate_poster_key()
        response_payload = GeneratePosterV2Response(
            poster_key=poster_key,
            trace_id=manifest.trace_id,
            final_url=manifest.final_url,
            final_hash=manifest.final_hash,
            foreground_url=manifest.foreground_url,
            background_url=manifest.background_url,
            background_seed=manifest.background_seed,
            background_model=manifest.background_model,
            template_id=manifest.template_id,
            template_version=manifest.template_version,
            template_contract_version=manifest.template_contract_version,
            engine_version=manifest.engine_version,
            renderer_mode=manifest.renderer_mode,
            render_engine_used=manifest.render_engine_used,
            foreground_renderer=manifest.foreground_renderer,
            background_renderer=manifest.background_renderer,
            poster_spec_hash=manifest.poster_spec_hash,
            timings_ms=manifest.timings_ms,
            debug_artifacts=Poster2DebugArtifacts(
                background_layer_url=manifest.debug_artifacts.background_layer_url,
                product_material_layer_url=manifest.debug_artifacts.product_material_layer_url,
                foreground_layer_url=manifest.debug_artifacts.foreground_layer_url,
                final_composited_url=manifest.debug_artifacts.final_composited_url,
                renderer_metadata_url=manifest.debug_artifacts.renderer_metadata_url,
            ),
            fallback_reason_code=manifest.fallback_reason_code,
            fallback_reason_detail=manifest.fallback_reason_detail,
            degraded=manifest.degraded,
            degraded_reason=manifest.degraded_reason,
            structure_complete=manifest.structure_complete,
            incomplete_structure=manifest.incomplete_structure,
            deliverable=manifest.deliverable,
            structure_evidence_source=manifest.structure_evidence_source,
            structure_evidence_complete=manifest.structure_evidence_complete,
            missing_mandatory_regions=manifest.missing_mandatory_regions,
            missing_required_slots=manifest.missing_required_slots,
            region_render_status=manifest.region_render_status,
            slot_binding_status=manifest.slot_binding_status,
            template_behavior=manifest.template_behavior,
            geometry_evidence=manifest.geometry_evidence,
            relaxation_preset=manifest.relaxation_preset,
            composition_strategy=manifest.composition_strategy,
            hero_contract_review=manifest.hero_contract_review,
            product_contract_review=manifest.product_contract_review,
            header_contract_review=manifest.header_contract_review,
            feature_contract_review=manifest.feature_contract_review,
            bottom_contract_review=manifest.bottom_contract_review,
            product_annotation_contract_review=manifest.product_annotation_contract_review,
            scenario_contract_review=manifest.scenario_contract_review,
            top_copy_contract_review=manifest.top_copy_contract_review,
            description_contract_review=manifest.description_contract_review,
            announcement_variant_contract_review=manifest.announcement_variant_contract_review,
            title_text_layer=manifest.title_text_layer,
            subtitle_text_layer=manifest.subtitle_text_layer,
            header_text_layer=manifest.header_text_layer,
            copy_optimization_review=manifest.copy_optimization_review,
            visible_truth_evidence=manifest.visible_truth_evidence,
            template_b_parity_review=manifest.template_b_parity_review,
        )
        response_payload_dict = _model_dump(response_payload)
        if manifest.template_b_parity_review is None:
            response_payload_dict.pop("template_b_parity_review", None)
        _poster2_lifecycle_log("storage_start", request_id=request_id, trace_id=manifest.trace_id, target="poster_record")
        create_poster_record(
            poster_key=poster_key,
            request_snapshot=_model_dump(payload),
            render_result=response_payload_dict,
            final_poster=_poster2_final_poster_payload(manifest),
        )
        _poster2_lifecycle_log("storage_end", request_id=request_id, trace_id=manifest.trace_id, target="poster_record")
        _poster2_lifecycle_log("response_ready", request_id=request_id, status_code=200, trace_id=manifest.trace_id)
        return JSONResponse(
            content=response_payload_dict,
            headers={"X-Request-ID": request_id} if request_id else None,
        )

    except FileNotFoundError as exc:
        _poster2_lifecycle_log("exception", request_id=request_id, stage="request_file", exception_class=exc.__class__.__name__)
        logger.warning("poster2: request file error %s detail=%s", request_log, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        _poster2_lifecycle_log("exception", request_id=request_id, stage="request_validation", exception_class=exc.__class__.__name__)
        logger.warning("poster2: request validation error %s detail=%s", request_log, exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PosterGenerationStageError as exc:
        _poster2_lifecycle_log(
            "exception",
            request_id=request_id,
            stage=exc.stage,
            code=exc.code,
            exception_class=exc.__class__.__name__,
        )
        logger.warning(
            "poster2: request failed request=%s stage=%s code=%s detail=%s",
            request_log,
            exc.stage,
            exc.code,
            exc.detail,
        )
        status_code = _poster2_stage_error_status(exc)
        _poster2_lifecycle_log("response_ready", request_id=request_id, status_code=status_code)
        return _poster2_stage_failure_response(error=exc, request_id=request_id)
    except Exception as exc:
        reason_code = getattr(exc, "reason_code", None)
        detail = getattr(exc, "detail", None) or str(exc)
        failure_stage = getattr(exc, "stage", None) or getattr(exc, "fallback_stage", None)
        _poster2_lifecycle_log(
            "exception",
            request_id=request_id,
            stage=failure_stage or "unknown",
            code=reason_code or "poster2_generation_failed",
            exception_class=exc.__class__.__name__,
        )
        logger.exception(
            "poster2: generation failed request=%s exc_class=%s reason_code=%s failure_stage=%s detail=%s",
            request_log,
            exc.__class__.__name__,
            reason_code,
            failure_stage,
            detail,
        )
        _poster2_lifecycle_log("response_ready", request_id=request_id, status_code=500)
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "poster2_generation_failed",
                "error_code": reason_code or "poster2_generation_failed",
                "request_id": request_id,
                "failure": {
                    "stage": failure_stage or "unknown",
                    "code": reason_code or "poster2_generation_failed",
                    "message": detail,
                    "detail": detail,
                    "exception_class": exc.__class__.__name__,
                    "retryable": False,
                },
            },
            headers={"X-Request-ID": request_id} if request_id else None,
        )


@app.get(
    "/api/v2/posters/{poster_key}",
    response_model=PosterRecordResponse,
    summary="Poster 2.0 — load persisted poster record",
    tags=["poster-v2"],
)
def get_poster_v2_record(poster_key: str) -> PosterRecordResponse:
    record = load_poster_record(poster_key)
    if record is None:
        raise HTTPException(status_code=404, detail="poster_record_not_found")
    return PosterRecordResponse.model_validate(record)


@app.post(
    "/api/v2/workbench",
    response_model=WorkbenchRecordResponse,
    summary="CUISTANCE commercial trial — create workbench truth record (PR-1)",
    tags=["poster-v2"],
)
def create_workbench_v2(payload: WorkbenchCreateRequest) -> WorkbenchRecordResponse:
    record = create_workbench_record(
        workbench_key=generate_workbench_key(),
        language=payload.language,
        status=payload.status,
        product_truth=_model_dump(payload.product_truth or ProductTruth()),
        product_assets=_model_dump(payload.product_assets or ProductAssets()),
        email_banner=_model_dump(payload.email_banner or EmailBanner()),
    )
    return WorkbenchRecordResponse.model_validate(record)


@app.get(
    "/api/v2/workbench/{workbench_key}",
    response_model=WorkbenchRecordResponse,
    summary="CUISTANCE commercial trial — load workbench truth record (PR-1)",
    tags=["poster-v2"],
)
def get_workbench_v2(workbench_key: str) -> WorkbenchRecordResponse:
    record = load_workbench_record(workbench_key)
    if record is None:
        raise HTTPException(status_code=404, detail="workbench_record_not_found")
    return WorkbenchRecordResponse.model_validate(record)


@app.patch(
    "/api/v2/workbench/{workbench_key}",
    response_model=WorkbenchRecordResponse,
    summary="CUISTANCE commercial trial — update workbench truth record (PR-1)",
    tags=["poster-v2"],
)
def patch_workbench_v2(workbench_key: str, payload: WorkbenchPatchRequest) -> WorkbenchRecordResponse:
    if load_workbench_record(workbench_key) is None:
        raise HTTPException(status_code=404, detail="workbench_record_not_found")
    # Only provided fields are replaced; validation (param keys/states, lock rule, no base64,
    # atmosphere-not-truth) already ran at the WorkbenchPatchRequest boundary.
    updates = payload.model_dump(exclude_unset=True, exclude_none=True)
    record = update_workbench_record(workbench_key, updates)
    return WorkbenchRecordResponse.model_validate(record)


@app.post(
    "/api/v2/workbench/{workbench_key}/candidates/{candidate_type}/generate",
    response_model=WorkbenchRecordResponse,
    summary="CUISTANCE commercial trial — generate a Step-2 email body visual candidate (PR-2)",
    tags=["poster-v2"],
)
async def generate_workbench_candidate_v2(
    workbench_key: str, candidate_type: str, request: Request
) -> Any:
    """Generate one email body visual candidate (affiche|fiche) from workbench truth by REUSING the existing
    /api/v2/generate-poster code path (no renderer fork). Stores only the poster_key reference under the
    workbench; the candidate truth stays in the poster_record."""
    if candidate_type not in CANDIDATE_TEMPLATE:
        raise HTTPException(status_code=422, detail="invalid_candidate_type")
    record = load_workbench_record(workbench_key)
    if record is None:
        raise HTTPException(status_code=404, detail="workbench_record_not_found")

    try:
        payload_dict = build_candidate_payload(record, candidate_type)
        payload = _model_validate(GeneratePosterV2Request, payload_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    # Reuse the existing generation handler in-process (it always returns a JSONResponse).
    result = await generate_poster_v2(request, payload)
    body: dict[str, Any] = {}
    raw = getattr(result, "body", None)
    if raw is not None:
        try:
            body = json.loads(bytes(raw).decode("utf-8"))
        except Exception:  # pragma: no cover - defensive
            body = {}
    status_code = getattr(result, "status_code", 200)
    poster_key = body.get("poster_key")

    if status_code != 200 or not poster_key:
        set_poster_candidate(
            workbench_key,
            candidate_type,
            poster_key=None,
            status="failed",
            template_id=CANDIDATE_TEMPLATE[candidate_type],
            contract_review_summary={"http_status": status_code},
        )
        return JSONResponse(status_code=status_code, content=body or {"error": "candidate_generation_failed"})

    summary = {
        key: body.get(key)
        for key in ("template_id", "render_engine_used", "degraded", "structure_complete")
        if body.get(key) is not None
    }
    composite_review = body.get("email_campaign_composite_contract_review")
    if isinstance(composite_review, dict):
        summary["callout_count"] = composite_review.get("callout_count")
        summary["structure_complete"] = composite_review.get("structure_complete", summary.get("structure_complete"))

    record = set_poster_candidate(
        workbench_key,
        candidate_type,
        poster_key=poster_key,
        status="ready",
        template_id=body.get("template_id") or CANDIDATE_TEMPLATE[candidate_type],
        contract_review_summary=summary,
    )
    return WorkbenchRecordResponse.model_validate(record)


@app.patch(
    "/api/v2/workbench/{workbench_key}/selected-visual",
    response_model=WorkbenchRecordResponse,
    summary="CUISTANCE commercial trial — select the email body visual (PR-2)",
    tags=["poster-v2"],
)
def select_workbench_visual_v2(
    workbench_key: str, payload: WorkbenchSelectVisualRequest
) -> WorkbenchRecordResponse:
    if load_workbench_record(workbench_key) is None:
        raise HTTPException(status_code=404, detail="workbench_record_not_found")
    try:
        record = select_email_body_visual(workbench_key, payload.selected_email_body_visual)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return WorkbenchRecordResponse.model_validate(record)


def _resolve_workbench_email_package(workbench_key: str) -> dict[str, Any]:
    """Resolve the deterministic PR-3S email package for a workbench: load workbench -> selected visual ->
    selected candidate poster_key -> poster_record -> draft -> assembly (with email_body_plan). Raises
    HTTPException for the same guards used by preview. BOTH preview and send consume this single source so the
    sent email is byte-identical to the previewed one (no reconstruction in the send path)."""
    workbench = load_workbench_record(workbench_key)
    if workbench is None:
        raise HTTPException(status_code=404, detail="workbench_record_not_found")

    selected = workbench.get("selected_email_body_visual")
    if selected not in ("affiche", "fiche"):
        raise HTTPException(status_code=422, detail="no_selected_email_body_visual")

    candidate = (workbench.get("poster_candidates") or {}).get(selected) or {}
    poster_key = candidate.get("poster_key")
    if not poster_key or candidate.get("status") != "ready":
        raise HTTPException(status_code=422, detail="selected_candidate_not_ready")

    record = load_poster_record(poster_key)
    if record is None:
        raise HTTPException(status_code=404, detail="selected_poster_record_not_found")

    # Deterministic draft (parameters never exposed to Gemini) + plan-driven assembly.
    draft = build_email_draft_for_poster_record(record)
    standalone_url = (record.get("final_poster") or {}).get("url") or (record.get("render_result") or {}).get("final_url")
    # derive the email-embedded body visual (no inner poster banner) deterministically — NEVER the standalone poster
    ebv = derive_email_body_visual(record)
    email_body_visual_url = ebv.get("url") or standalone_url
    try:
        assembly = build_email_assembly(
            workbench=workbench,
            draft=draft,
            body_visual_url=email_body_visual_url,
            candidate_type=selected,
            template_id=candidate.get("template_id"),
            poster_key=poster_key,
            body_visual_variant=ebv.get("variant"),
            body_visual_contains_own_banner=bool(ebv.get("contains_own_banner")),
            standalone_poster_url=standalone_url,
        )
    except Exception as exc:  # plan/assembly could not be built
        raise HTTPException(status_code=422, detail="email_body_plan_unavailable") from exc

    return {
        "workbench": workbench,
        "selected": selected,
        "candidate": candidate,
        "poster_key": poster_key,
        "record": record,
        "draft": draft,
        "assembly": assembly,
        "body_url": email_body_visual_url,
        "standalone_poster_url": standalone_url,
        "email_body_visual": ebv,
    }


@app.post(
    "/api/v2/workbench/{workbench_key}/email/preview",
    response_model=EmailAssemblyPreviewResponse,
    summary="CUISTANCE commercial trial — assemble email preview (banner + selected visual) (PR-3)",
    tags=["poster-v2"],
)
def preview_workbench_email_v2(workbench_key: str) -> EmailAssemblyPreviewResponse:
    """Assemble the final email preview at the email level: Email Banner Module (from workbench.email_banner)
    + the deterministically-selected body visual (the selected candidate's poster_record final_poster URL)
    + intro/CTA + footer/contact + attachment readiness. The visual is chosen ONLY by
    workbench.selected_email_body_visual — never by Gemini or frontend state. Does not change the existing
    poster_key-based /api/v2/email/preview."""
    pkg = _resolve_workbench_email_package(workbench_key)
    selected, poster_key = pkg["selected"], pkg["poster_key"]
    candidate, record, draft, assembly, body_url = (
        pkg["candidate"], pkg["record"], pkg["draft"], pkg["assembly"], pkg["body_url"]
    )

    settings = get_settings()
    if settings.email_attachment.enabled and settings.email_attachment.build_on_preview:
        record = build_email_assets_for_record(poster_key)
    email_assets = record.get("email_assets") or {}

    return EmailAssemblyPreviewResponse(
        workbench_key=workbench_key,
        selected_email_body_visual=selected,
        email_body_plan=assembly["email_body_plan"],
        banner=assembly["banner"],
        body_visual={
            "candidate_type": selected,
            "poster_key": poster_key,
            "url": body_url,
            "template_id": candidate.get("template_id"),
        },
        subject=assembly["subject"],
        preview_text=assembly["preview_text"],
        intro=assembly["intro"],
        cta_label=assembly["cta_label"],
        html=assembly["html"],
        text=assembly["text"],
        generated_from=draft.get("generated_from") or "deterministic",
        email_assets=email_assets,
        available_attachment_types=sorted(email_assets.keys()),
        buildable_attachment_types=list(SUPPORTED_ATTACHMENT_TYPES) if settings.email_attachment.enabled else [],
        body_visual_contains_own_banner=assembly["body_visual_contains_own_banner"],
        email_container_template_id=assembly.get("email_container_template_id", "cuistance_email_container_psd_v1"),
        email_fill_format=assembly.get("email_fill_format"),
        email_header_source=assembly.get("email_header_source", "ttt_html_header"),
        email_container=assembly.get("email_container", {}),
        standalone_poster_url=pkg.get("standalone_poster_url"),
        email_body_visual_url=assembly.get("email_body_visual_url") or body_url,
        body_visual_variant=assembly.get("body_visual_variant"),
        email_body_visual_contract_pass=assembly.get("email_body_visual_contract_pass", True),
    )


@app.post(
    "/api/v2/workbench/{workbench_key}/email/send",
    response_model=WorkbenchEmailSendResponse,
    summary="CUISTANCE commercial trial — manual multi-recipient confirmed send + evidence (PR-4)",
    tags=["poster-v2"],
)
def send_workbench_email_v2(
    workbench_key: str, payload: WorkbenchEmailSendRequest
) -> WorkbenchEmailSendResponse:
    """Send the deterministic PR-3S email package to manually-entered recipients. Requires explicit
    confirm_send; sends per recipient with isolated results; persists evidence on workbench.send_attempts.
    Consumes the SAME assembled package as the preview (no body reconstruction, no candidate re-selection, no
    Gemini fact change, no new poster). Reuses the existing provider path; does NOT change the single-recipient
    /api/v2/email/send. Manual recipients only — no contact import / Excel / CRM / scheduling / segmentation /
    analytics."""
    # deterministic package (raises the same 404/422 guards as preview, incl. email_body_plan_unavailable)
    pkg = _resolve_workbench_email_package(workbench_key)
    selected, poster_key, candidate = pkg["selected"], pkg["poster_key"], pkg["candidate"]
    record, assembly = pkg["record"], pkg["assembly"]

    # explicit confirmation — neither test nor real send happens implicitly
    if not payload.confirm_send:
        raise HTTPException(status_code=422, detail="confirm_send_required")

    norm = normalize_recipients(payload.recipients)
    if not norm["unique"]:
        raise HTTPException(status_code=422, detail="recipients_required")

    settings = get_settings()
    requested_types = list(payload.attachment_types or [])
    attachments: list[dict[str, Any]] = []
    if payload.delivery_mode == "resend" and requested_types:
        if settings.email_attachment.enabled:
            record = build_email_assets_for_record(poster_key, asset_types=requested_types)
        try:
            attachments = resolve_email_assets(record, requested_types)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    # consume the planned package verbatim — never reconstruct the body
    subject = assembly["subject"]
    preview_text = assembly["preview_text"]
    html = assembly["html"]
    text = assembly["text"]
    layout_type = (assembly.get("email_body_plan") or {}).get("layout_type")

    provider = get_email_provider(payload.delivery_mode)
    invalid_set = set(norm["invalid"])
    attempts: list[dict[str, Any]] = []
    sent_count = failed_count = skipped_count = 0

    for recipient in norm["unique"]:
        base = {
            "recipient": recipient,
            "mode": payload.mode,
            "attachment_types": requested_types,
            "at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
            "selected_email_body_visual": selected,
            "body_visual_poster_key": poster_key,
            "layout_type": layout_type,
            "subject": subject,
            "deduplicated": False,
            "provider_message_id": None,
            "error_code": None,
            "error_message": None,
        }
        if recipient in invalid_set:
            attempts.append({**base, "status": "error", "provider": "validation",
                             "error_code": "invalid_recipient", "error_message": "invalid email address"})
            failed_count += 1
            continue
        try:
            result = provider.send(
                recipient=recipient, subject=subject, preview_text=preview_text,
                html=html, text=text, attachments=attachments,
            )
            if result.status == "sent":
                attempts.append({**base, "status": "sent", "provider": result.provider,
                                 "provider_message_id": result.provider_message_id})
                sent_count += 1
            elif result.status == "preview_only":
                attempts.append({**base, "status": "skipped", "provider": result.provider,
                                 "error_code": "preview_only"})
                skipped_count += 1
            else:
                attempts.append({**base, "status": "error", "provider": result.provider,
                                 "error_code": result.status or "send_error", "error_message": result.error})
                failed_count += 1
        except Exception as exc:  # per-recipient isolation — never erase other recipients' evidence
            attempts.append({**base, "status": "error", "provider": payload.delivery_mode,
                             "error_code": "provider_exception", "error_message": str(exc)[:300]})
            failed_count += 1

    append_send_attempts(workbench_key, attempts, mark_sent=(payload.mode == "real" and sent_count > 0))

    return WorkbenchEmailSendResponse(
        workbench_key=workbench_key,
        mode=payload.mode,
        total=len(norm["unique"]),
        sent_count=sent_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
        deduplicated_count=norm["deduplicated_count"],
        attempts=attempts,
    )


@app.post(
    "/api/v2/email/preview",
    response_model=EmailPreviewResponse,
    summary="Poster 2.0 — build email draft from poster record",
    tags=["poster-v2"],
)
def preview_poster_v2_email(payload: EmailPreviewRequest) -> EmailPreviewResponse:
    record = load_poster_record(payload.poster_key)
    if record is None:
        raise HTTPException(status_code=404, detail="poster_record_not_found")
    draft = build_email_draft_for_poster_record(record)
    update_email_draft(payload.poster_key, draft)
    settings = get_settings()
    if settings.email_attachment.enabled and settings.email_attachment.build_on_preview:
        record = build_email_assets_for_record(payload.poster_key)
    else:
        record = load_poster_record(payload.poster_key) or record
    email_assets = record.get("email_assets") or {}
    return EmailPreviewResponse(
        poster_key=payload.poster_key,
        subject=draft["subject"],
        preview_text=draft["preview_text"],
        html=draft["html"],
        text=draft["text"],
        summary_points=list(draft.get("summary_points") or []),
        tone=str(draft.get("tone") or "clean_product_business"),
        generated_from=draft.get("generated_from") or "deterministic",
        email_assets=email_assets,
        available_attachment_types=sorted(email_assets.keys()),
        buildable_attachment_types=list(SUPPORTED_ATTACHMENT_TYPES) if settings.email_attachment.enabled else [],
    )


@app.post(
    "/api/v2/email/send",
    response_model=EmailSendV2Response,
    summary="Poster 2.0 — send email from poster record draft",
    tags=["poster-v2"],
)
def send_poster_v2_email(payload: EmailSendV2Request) -> EmailSendV2Response:
    record = load_poster_record(payload.poster_key)
    if record is None:
        raise HTTPException(status_code=404, detail="poster_record_not_found")

    generated_draft = record.get("email_draft") or build_email_draft_for_poster_record(record)
    draft = {
        "subject": payload.subject or generated_draft["subject"],
        "preview_text": payload.preview_text or generated_draft["preview_text"],
        "html": payload.html or generated_draft["html"],
        "text": payload.text or generated_draft["text"],
        "summary_points": list(generated_draft.get("summary_points") or []),
        "tone": generated_draft.get("tone") or "clean_product_business",
        "generated_from": generated_draft.get("generated_from") or "deterministic",
        "generated_at": generated_draft["generated_at"],
    }

    requested_attachment_types = list(payload.attachment_types or [])

    attachments = []
    if payload.delivery_mode == "resend" and requested_attachment_types:
        try:
            attachments = resolve_email_assets(record, requested_attachment_types)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    provider = get_email_provider(payload.delivery_mode)
    delivery_result = provider.send(
        recipient=str(payload.recipient),
        subject=draft["subject"],
        preview_text=draft["preview_text"],
        html=draft["html"],
        text=draft["text"],
        attachments=attachments,
    )
    delivery = {
        "sent_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "provider": delivery_result.provider,
        "delivery_mode": payload.delivery_mode,
        "status": delivery_result.status,
        "recipient": str(payload.recipient),
        "provider_message_id": delivery_result.provider_message_id,
        "error": delivery_result.error,
    }
    append_email_delivery(payload.poster_key, delivery, draft=draft)

    return EmailSendV2Response(
        poster_key=payload.poster_key,
        provider=delivery_result.provider,
        delivery_mode=payload.delivery_mode,
        status=delivery_result.status,
        recipient=str(payload.recipient),
        provider_message_id=delivery_result.provider_message_id,
        error=delivery_result.error,
        attachment_types=requested_attachment_types,
    )

if FRONTEND_DIR.exists():
    # Mount the static frontend after API routes so a single Render Web Service
    # can restore both the browser UI and the backend API.
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


# Wrap the fully constructed FastAPI app so CORS headers also survive error responses.
app = CORSMiddleware(app, **CORS_MIDDLEWARE_KWARGS)


__all__ = ["app"]
