"""
AssetLoader — fetch remote/R2/base64 assets and return PIL Images.

Designed for testability: inject a custom `fetch_url` coroutine to avoid
network calls in unit tests.
"""
from __future__ import annotations

import base64
import logging
from io import BytesIO
from typing import Callable, Awaitable, Optional

import httpx
from PIL import Image as PILImage

from .contracts import AssetRef, PosterSpec, ResolvedAssets

logger = logging.getLogger("ai-service.poster2")


async def _default_fetch(url: str) -> bytes:
    """Download bytes from an https:// URL (used in production)."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


def _r2_key_from_ref(ref: AssetRef) -> Optional[str]:
    """Extract R2 key from r2://key refs."""
    if ref.url.startswith("r2://"):
        return ref.url[5:]
    return ref.key  # may be None


async def _resolve_bytes(
    ref: AssetRef,
    fetch: Callable[[str], Awaitable[bytes]],
) -> bytes:
    url = ref.url

    # Base64 data URL
    if url.startswith("data:"):
        header, b64 = url.split(",", 1)
        return base64.b64decode(b64)

    # R2 direct key (r2://some/key)
    if url.startswith("r2://"):
        from app.services import r2_client  # lazy: keeps boto3 out of test collection
        key = url[5:]
        return r2_client.get_bytes(key)

    # Public / presigned HTTPS URL
    if url.startswith("https://") or url.startswith("http://"):
        return await fetch(url)

    raise ValueError(f"Unsupported asset URL scheme: {url!r}")


def _bytes_to_pil(data: bytes) -> PILImage.Image:
    img = PILImage.open(BytesIO(data))
    img.load()
    return img.convert("RGBA")


class AssetLoader:
    """Resolve all asset refs in a PosterSpec to PIL Images."""

    def __init__(
        self,
        fetch_url: Callable[[str], Awaitable[bytes]] | None = None,
    ):
        self._fetch = fetch_url or _default_fetch

    async def load(self, spec: PosterSpec) -> ResolvedAssets:
        import asyncio

        async def maybe(ref: Optional[AssetRef]) -> Optional[PILImage.Image]:
            if ref is None:
                return None
            try:
                raw = await _resolve_bytes(ref, self._fetch)
                return _bytes_to_pil(raw)
            except Exception as exc:
                logger.warning("Failed to load asset %s: %s", ref.url, exc)
                return None

        product_task = asyncio.create_task(maybe(spec.product_image))
        logo_task = asyncio.create_task(maybe(spec.logo))
        scenario_task = asyncio.create_task(maybe(spec.scenario_image))
        gallery_tasks = [
            asyncio.create_task(maybe(ref)) for ref in spec.gallery_images
        ]

        product = await product_task
        if product is None:
            raise ValueError("product_image is required and could not be loaded")

        logo = await logo_task
        scenario = await scenario_task
        gallery_results = await asyncio.gather(*gallery_tasks)
        gallery = [img for img in gallery_results if img is not None]

        return ResolvedAssets(
            product=product,
            logo=logo,
            scenario=scenario,
            gallery=gallery,
        )

    async def load_url(self, url: str) -> PILImage.Image:
        """Convenience: fetch a single URL and return PIL Image."""
        ref = AssetRef(url=url)
        raw = await _resolve_bytes(ref, self._fetch)
        return _bytes_to_pil(raw)
