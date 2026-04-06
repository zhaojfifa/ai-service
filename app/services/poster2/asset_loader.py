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

        async def fetch_gallery(ref: AssetRef, index: int) -> Optional[PILImage.Image]:
            logger.info("poster2.gallery_fetch_item_start index=%d url=%s", index, ref.url)
            img = await maybe(ref)
            if img is None:
                logger.info("poster2.gallery_fetch_item_done index=%d ok=false", index)
                return None
            logger.info(
                "poster2.gallery_fetch_item_done index=%d ok=true size=%sx%s",
                index,
                img.width,
                img.height,
            )
            return img

        product_task = asyncio.create_task(maybe(spec.product_image))
        product_secondary_task = asyncio.create_task(maybe(spec.product_secondary_image))
        logo_task = asyncio.create_task(maybe(spec.logo))
        scenario_task = asyncio.create_task(maybe(spec.scenario_image))
        gallery_refs = list(spec.gallery_images)[:4]
        logger.info("poster2.gallery_resolve_start count=%d", len(gallery_refs))
        gallery_tasks = []
        gallery_status: list[dict] = []
        for idx, ref in enumerate(gallery_refs):
            gallery_status.append({
                "index": idx,
                "url": ref.url,
                "resolved": False,
                "error_code": None,
            })
            gallery_tasks.append(asyncio.create_task(fetch_gallery(ref, idx)))

        materials_refs = list(spec.materials_images)[:5]
        materials_tasks = []
        materials_status: list[dict] = []
        for idx, ref in enumerate(materials_refs):
            materials_status.append({
                "index": idx,
                "url": ref.url,
                "resolved": False,
                "error_code": None,
            })
            materials_tasks.append(asyncio.create_task(maybe(ref)))

        product = await product_task
        if product is None:
            raise ValueError("product_image is required and could not be loaded")

        product_secondary = await product_secondary_task
        logo = await logo_task
        scenario = await scenario_task
        gallery_results = await asyncio.gather(*gallery_tasks)
        gallery: list[PILImage.Image] = []
        for idx, img in enumerate(gallery_results):
            if img is None:
                gallery_status[idx]["error_code"] = "gallery_item_load_failed"
                continue
            gallery.append(img)
            gallery_status[idx]["resolved"] = True
        logger.info(
            "poster2.gallery_resolve_done requested=%d resolved=%d",
            len(gallery_refs),
            len(gallery),
        )

        materials_results = await asyncio.gather(*materials_tasks)
        materials: list[PILImage.Image] = []
        for idx, img in enumerate(materials_results):
            if img is None:
                materials_status[idx]["error_code"] = "materials_item_load_failed"
                continue
            materials.append(img)
            materials_status[idx]["resolved"] = True

        return ResolvedAssets(
            product=product,
            logo=logo,
            scenario=scenario,
            product_secondary=product_secondary,
            gallery=gallery,
            gallery_status=gallery_status,
            materials=materials,
            materials_status=materials_status,
        )

    async def load_url(self, url: str) -> PILImage.Image:
        """Convenience: fetch a single URL and return PIL Image."""
        ref = AssetRef(url=url)
        raw = await _resolve_bytes(ref, self._fetch)
        return _bytes_to_pil(raw)
