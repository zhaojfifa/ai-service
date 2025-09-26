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
from app.services.glibatree import generate_poster_asset
from app.services.poster import (
    build_glibatree_prompt,
    compose_marketing_email,
    render_layout_preview,
)


settings = get_settings()

app = FastAPI(title="Marketing Poster API", version="1.0.0")

allow_origins = settings.allowed_origins
if allow_origins == ["*"]:
    allow_credentials = False
else:
    allow_credentials = True

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
    preview = render_layout_preview(payload)
    prompt = build_glibatree_prompt(payload)
    poster_image = generate_poster_asset(payload, prompt, preview)
    email_body = compose_marketing_email(payload, poster_image.filename)
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

