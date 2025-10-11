from __future__ import annotations

import json
import logging
import os
import re
from typing import Iterable
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from pydantic import ValidationError

from app.config import get_settings
from app.schemas import (
    GeneratePosterRequest,
    GeneratePosterResponse,
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
uvlog = logging.getLogger("uvicorn.error")

settings = get_settings()
app = FastAPI(title="Marketing Poster API", version="1.0.0")

UPLOAD_MAX_BYTES = max(int(os.getenv("UPLOAD_MAX_BYTES", "20000000") or 0), 0)
UPLOAD_ALLOWED_MIME = {
    item.strip()
    for item in os.getenv("UPLOAD_ALLOWED_MIME", "image/png,image/jpeg,image/webp").split(",")
    if item.strip()
}

REQUEST_BODY_MAX_BYTES = 300_000
DATA_URL_PATTERN = re.compile(r"^data:[^;]+;base64,", re.IGNORECASE)


def _normalize_allowed_origins(value: Iterable[str] | str | None) -> list[str]:
    """Normalise configured origins to bare scheme://host pairs."""

    def to_origin(candidate: str | None) -> str | None:
        if not candidate:
            return None
        raw = str(candidate).strip().strip('"').strip("'")
        if not raw:
            return None
        guess = raw if "://" in raw else f"https://{raw}"
        parsed = urlsplit(guess)
        if not parsed.scheme or not parsed.netloc:
            return None
        scheme = parsed.scheme.lower()
        if scheme not in {"http", "https"}:
            return None
        return f"{scheme}://{parsed.netloc}"

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

    origins = [to_origin(item) for item in items]
    deduped = []
    for origin in origins:
        if origin and origin not in deduped:
            deduped.append(origin)
    return deduped or ["*"]

raw = (
    getattr(settings, "allowed_origins", None)
    or os.getenv("ALLOWED_ORIGINS")
)
allow_origins = _normalize_allowed_origins(raw)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)


@app.options("/{rest_of_path:path}")
def cors_preflight_handler(rest_of_path: str) -> Response:
    """Ensure any CORS preflight request receives an immediate 204 response."""
    return Response(status_code=204)


@app.get("/health", response_class=PlainTextResponse)
def health_check() -> PlainTextResponse:
    return PlainTextResponse("ok")


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


async def read_json_relaxed(request: Request) -> dict:
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > REQUEST_BODY_MAX_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail="Request body exceeds 300KB. Upload assets to object storage instead of embedding Base64.",
                )
        except ValueError:
            # Ignore invalid content-length headers and rely on actual body size.
            pass

    body = await request.body()
    if body and len(body) > REQUEST_BODY_MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Request body exceeds 300KB. Upload assets to object storage instead of embedding Base64.",
        )
    if not body:
        return {}

    try:
        decoded = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Request body must be UTF-8 encoded JSON") from exc

    try:
        payload = json.loads(decoded)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")
    return payload


def _detect_embedded_data_urls(poster) -> list[str]:
    """Return a list of fields that still contain Base64 data URLs."""

    fields: list[str] = []

    def register(value: str | None, label: str) -> None:
        if isinstance(value, str) and DATA_URL_PATTERN.match(value.strip()):
            fields.append(label)

    register(getattr(poster, "brand_logo", None), "poster.brand_logo")
    register(getattr(poster, "scenario_asset", None), "poster.scenario_asset")
    register(getattr(poster, "product_asset", None), "poster.product_asset")
    for index, item in enumerate(getattr(poster, "gallery_items", []) or []):
        register(getattr(item, "asset", None), f"poster.gallery_items[{index}].asset")

    return fields


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


@app.post("/api/generate-poster", response_model=GeneratePosterResponse)
async def generate_poster(request: Request) -> GeneratePosterResponse:
    try:
        raw_payload = await read_json_relaxed(request)
        payload = _model_validate(GeneratePosterRequest, raw_payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    poster = payload.poster
    data_url_fields = _detect_embedded_data_urls(poster)
    if data_url_fields:
        joined = ", ".join(data_url_fields)
        raise HTTPException(
            status_code=400,
            detail=(
                "请求体仍包含 Base64 图片，请改为上传至对象存储，仅传输对象 key 或公开 URL："
                f"{joined}"
            ),
        )

    try:
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
    except HTTPException:
        raise
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

