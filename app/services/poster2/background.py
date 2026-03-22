"""
FireflyBackgroundService — background-only image generation via Adobe Firefly.

Architecture contract:
  - Firefly ONLY generates the background layer (scene, lighting, atmosphere).
  - The prompt MUST NOT contain text, logo, UI element, or button descriptions.
  - Falls back to Vertex Imagen3 if Firefly is not configured.

Adobe Firefly API reference (v3):
  Token:    POST https://ims-na1.adobelogin.com/ims/token/v3
  Generate: POST https://firefly-api.adobe.io/v3/images/generate
"""
from __future__ import annotations

import hashlib
import inspect
import logging
import time
from dataclasses import dataclass
from typing import Optional

import httpx

from .vertex_runtime import get_vertex_poster_client

logger = logging.getLogger("ai-service.poster2")

# ── Constants ───────────────────────────────────────────────────────────────
_FIREFLY_TOKEN_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
_FIREFLY_GENERATE_URL = "https://firefly-api.adobe.io/v3/images/generate"
_FIREFLY_SCOPE = "openid,AdobeID,firefly_enterprise,firefly_api,ff_apis"

# Prompt suffix appended to every background prompt (safety guardrail)
_NO_STRUCTURE_SUFFIX = (
    ", no text, no logo, no watermark, no UI elements, no buttons, "
    "no people, no faces"
)


# ── Result dataclass ─────────────────────────────────────────────────────────
@dataclass
class BackgroundResult:
    url: str
    key: str
    prompt_used: str
    seed_used: int
    model: str
    width: int
    height: int


# ── Token cache ──────────────────────────────────────────────────────────────
class _TokenCache:
    """Simple in-process token cache with expiry awareness."""

    def __init__(self) -> None:
        self._token: Optional[str] = None
        self._expires_at: float = 0.0

    def get(self) -> Optional[str]:
        if self._token and time.monotonic() < self._expires_at:
            return self._token
        return None

    def set(self, token: str, expires_in: int) -> None:
        # Apply 5-minute safety margin
        self._token = token
        self._expires_at = time.monotonic() + expires_in - 300


_token_cache = _TokenCache()


# ── Firefly provider ─────────────────────────────────────────────────────────
class FireflyProvider:
    """
    Calls Adobe Firefly v3 text-to-image.
    Thread-safe; token is refreshed automatically on expiry.
    """

    MODEL_ID = "firefly-v3"

    def __init__(self, client_id: str, client_secret: str):
        self._client_id = client_id
        self._client_secret = client_secret

    async def _get_token(self) -> str:
        cached = _token_cache.get()
        if cached:
            return cached

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                _FIREFLY_TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "scope": _FIREFLY_SCOPE,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            body = resp.json()

        token = body["access_token"]
        expires_in = int(body.get("expires_in", 86400))
        _token_cache.set(token, expires_in)
        logger.debug("Firefly: obtained new IMS token (expires_in=%d)", expires_in)
        return token

    async def generate(
        self,
        prompt: str,
        width: int,
        height: int,
        seed: Optional[int],
        negative_prompt: str,
    ) -> bytes:
        token = await self._get_token()

        payload: dict = {
            "prompt": prompt,
            "negativePrompt": negative_prompt or "text, logo, watermark",
            "size": {"width": width, "height": height},
            "numVariations": 1,
            "contentClass": "photo",
        }
        if seed is not None:
            payload["seeds"] = [seed]

        headers = {
            "Authorization": f"Bearer {token}",
            "x-api-key": self._client_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                _FIREFLY_GENERATE_URL,
                json=payload,
                headers=headers,
            )
            if resp.status_code == 401:
                # Token may have expired mid-request; invalidate and retry once
                _token_cache.set("", 0)
                token = await self._get_token()
                headers["Authorization"] = f"Bearer {token}"
                resp = await client.post(
                    _FIREFLY_GENERATE_URL,
                    json=payload,
                    headers=headers,
                )
            resp.raise_for_status()
            data = resp.json()

        # Download the generated image from the presigned URL
        presigned_url = data["outputs"][0]["image"]["presignedUrl"]
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            img_resp = await client.get(presigned_url)
            img_resp.raise_for_status()
            return img_resp.content


# ── Vertex fallback provider ─────────────────────────────────────────────────
class VertexBackgroundProvider:
    """
    Fallback: use Vertex Imagen3 (generate-only, no inpainting) for background.
    Reuses the shared poster2 vertex runtime client registered at app startup.
    """

    MODEL_ID = "vertex-imagen3"

    async def generate(
        self,
        prompt: str,
        width: int,
        height: int,
        seed: Optional[int],
        negative_prompt: str,
    ) -> bytes:
        vertex_poster_client = get_vertex_poster_client()
        if vertex_poster_client is None:
            raise RuntimeError("Vertex Imagen3 client is not initialised")

        return await self._generate_with_client(
            vertex_poster_client=vertex_poster_client,
            prompt=prompt,
            width=width,
            height=height,
            seed=seed,
            negative_prompt=negative_prompt,
        )

    async def _generate_with_client(
        self,
        *,
        vertex_poster_client,
        prompt: str,
        width: int,
        height: int,
        seed: Optional[int],
        negative_prompt: str,
    ) -> bytes:
        generate_async = getattr(vertex_poster_client, "generate_async", None)
        if callable(generate_async):
            result = await generate_async(
                prompt=prompt,
                width=width,
                height=height,
                seed=seed,
                negative_prompt=negative_prompt,
                num_images=1,
            )
            return _unwrap_vertex_result(result)

        generate_bytes = getattr(vertex_poster_client, "generate_bytes", None)
        if callable(generate_bytes):
            result = generate_bytes(
                prompt=prompt,
                width=width,
                height=height,
                negative_prompt=negative_prompt,
            )
            if inspect.isawaitable(result):
                result = await result
            return _unwrap_vertex_result(result)

        raise RuntimeError("Vertex Imagen3 client does not expose generate_async or generate_bytes")


# ── FireflyBackgroundService ─────────────────────────────────────────────────
class FireflyBackgroundService:
    """
    Orchestrates background generation:
      1. Build a safe prompt (never includes text/logo/UI words).
      2. Call provider (Firefly preferred, Vertex fallback).
      3. Store result to R2 and return BackgroundResult.
    """

    ENGINE_VERSION = "2.0.0"

    def __init__(self, provider: FireflyProvider | VertexBackgroundProvider):
        self._provider = provider

    def _build_prompt(self, style_prompt: str, template_hint: str) -> str:
        parts = [p for p in [template_hint, style_prompt] if p]
        combined = ", ".join(parts) if parts else "professional product background"
        # Guardrail: always append no-structure suffix
        return combined + _NO_STRUCTURE_SUFFIX

    def _effective_seed(self, prompt: str, requested: Optional[int]) -> int:
        if requested is not None:
            return requested
        # Derive deterministic seed from prompt text
        return int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16) % (2**31)

    async def generate(
        self,
        style_prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        seed: Optional[int] = None,
        template_hint: str = "",
        trace_id: str = "",
    ) -> BackgroundResult:
        prompt = self._build_prompt(style_prompt, template_hint)
        effective_seed = self._effective_seed(prompt, seed)
        model_id = getattr(self._provider, "MODEL_ID", "unknown")

        logger.info(
            "poster2.bg: provider=%s seed=%d size=%dx%d trace=%s",
            model_id, effective_seed, width, height, trace_id,
        )

        raw_bytes = await self._provider.generate(
            prompt=prompt,
            width=width,
            height=height,
            seed=effective_seed,
            negative_prompt=negative_prompt,
        )

        from app.services import r2_client  # lazy import: keeps boto3 out of test collection

        key = f"poster2/bg/{trace_id or 'anon'}_{effective_seed}.png"
        url = r2_client.put_bytes(key, raw_bytes, content_type="image/png")
        if not url:
            raise RuntimeError(f"R2 upload failed for background key={key}")

        return BackgroundResult(
            url=url,
            key=key,
            prompt_used=prompt,
            seed_used=effective_seed,
            model=model_id,
            width=width,
            height=height,
        )


# ── Factory ──────────────────────────────────────────────────────────────────
def make_background_service() -> FireflyBackgroundService:
    """
    Build a FireflyBackgroundService from environment variables.
    Prefers Firefly; falls back to Vertex if FIREFLY_CLIENT_ID is absent.
    """
    import os

    client_id = os.getenv("FIREFLY_CLIENT_ID", "").strip()
    client_secret = os.getenv("FIREFLY_CLIENT_SECRET", "").strip()

    if client_id and client_secret:
        logger.info("poster2.bg: using Adobe Firefly provider")
        provider: FireflyProvider | VertexBackgroundProvider = FireflyProvider(
            client_id=client_id,
            client_secret=client_secret,
        )
    else:
        logger.warning(
            "poster2.bg: FIREFLY_CLIENT_ID/SECRET not set — falling back to Vertex Imagen3"
        )
        provider = VertexBackgroundProvider()

    return FireflyBackgroundService(provider=provider)


def _unwrap_vertex_result(result) -> bytes:
    if isinstance(result, (list, tuple)):
        if not result:
            raise RuntimeError("Vertex Imagen3 returned no images")
        return bytes(result[0])
    return bytes(result)
