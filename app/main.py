from __future__ import annotations
import os
import sys
import json                     # ← 你用了 json，但之前没导入
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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





from app.config import get_settings

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


def _model_dump(model):
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    if hasattr(model, "dict"):
        return model.dict(exclude_none=True)
    return {}


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

