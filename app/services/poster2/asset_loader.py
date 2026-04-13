"""
AssetLoader — fetch remote/R2/base64 assets and return PIL Images.

Designed for testability: inject a custom `fetch_url` coroutine to avoid
network calls in unit tests.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import os
from io import BytesIO
from typing import Callable, Awaitable, Optional

import httpx
from PIL import Image as PILImage, ImageFile, ImageOps, UnidentifiedImageError

from .contracts import AssetRef, PosterSpec, ResolvedAssets
from .errors import PosterGenerationStageError

logger = logging.getLogger("ai-service.poster2")

ImageFile.LOAD_TRUNCATED_IMAGES = False

_DEFAULT_FETCH_TIMEOUT_SEC = float(os.getenv("POSTER2_ASSET_FETCH_TIMEOUT_SEC", "20") or "20")
_IMAGE_DECODE_TIMEOUT_SEC = float(os.getenv("POSTER2_IMAGE_DECODE_TIMEOUT_SEC", "15") or "15")
_MATERIAL_PREPARE_TIMEOUT_SEC = float(os.getenv("POSTER2_MATERIAL_PREPARE_TIMEOUT_SEC", "15") or "15")
_MAX_ASSET_BYTES = max(int(os.getenv("POSTER2_MAX_ASSET_BYTES", str(20 * 1024 * 1024)) or 0), 1)
_MAX_IMAGE_PIXELS = max(int(os.getenv("POSTER2_MAX_IMAGE_PIXELS", str(24 * 1024 * 1024)) or 0), 1)
_MAX_IMAGE_DIMENSION = max(int(os.getenv("POSTER2_MAX_IMAGE_DIMENSION", "4096") or 0), 1)


async def _default_fetch(url: str) -> tuple[bytes, str | None]:
    """Download bytes from an https:// URL (used in production)."""
    timeout = httpx.Timeout(_DEFAULT_FETCH_TIMEOUT_SEC)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content, resp.headers.get("content-type")


def _r2_key_from_ref(ref: AssetRef) -> Optional[str]:
    """Extract R2 key from r2://key refs."""
    if ref.url.startswith("r2://"):
        return ref.url[5:]
    return ref.key  # may be None


async def _resolve_bytes(
    ref: AssetRef,
    fetch: Callable[[str], Awaitable[tuple[bytes, str | None]]],
) -> tuple[bytes, str | None]:
    url = ref.url

    # Base64 data URL
    if url.startswith("data:"):
        header, b64 = url.split(",", 1)
        mime = header[5:].split(";", 1)[0] or None
        return base64.b64decode(b64), mime

    # R2 direct key (r2://some/key)
    if url.startswith("r2://"):
        from app.services import r2_client  # lazy: keeps boto3 out of test collection
        key = url[5:]
        return r2_client.get_bytes(key), None

    # Public / presigned HTTPS URL
    if url.startswith("https://") or url.startswith("http://"):
        return await fetch(url)

    raise ValueError(f"Unsupported asset URL scheme: {url!r}")


def _normalize_content_type(value: str | None) -> str | None:
    if not value:
        return None
    return value.split(";", 1)[0].strip().lower() or None


def _decode_image(data: bytes, *, ref: AssetRef, content_type: str | None) -> PILImage.Image:
    normalized_content_type = _normalize_content_type(content_type)
    byte_size = len(data)
    if byte_size > _MAX_ASSET_BYTES:
        raise PosterGenerationStageError(
            "asset_fetch",
            "asset_too_large",
            "asset exceeds configured byte limit",
            asset_url=ref.url,
            content_type=normalized_content_type,
            byte_size=byte_size,
            detail=f"asset size {byte_size} exceeds max {_MAX_ASSET_BYTES}",
        )
    try:
        img = PILImage.open(BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise PosterGenerationStageError(
            "image_decode",
            "image_decode_failed",
            "failed to decode asset image",
            detail=str(exc),
            exception_class=exc.__class__.__name__,
            asset_url=ref.url,
            content_type=normalized_content_type,
            byte_size=byte_size,
        ) from exc

    return img


def _normalize_image(
    img: PILImage.Image,
    *,
    ref: AssetRef,
    content_type: str | None,
    byte_size: int,
) -> PILImage.Image:
    normalized_content_type = _normalize_content_type(content_type)
    width, height = img.size
    pixel_count = width * height
    if width <= 0 or height <= 0 or pixel_count <= 0:
        raise PosterGenerationStageError(
            "image_decode",
            "image_invalid_dimensions",
            "decoded image has invalid dimensions",
            asset_url=ref.url,
            content_type=normalized_content_type,
            byte_size=byte_size,
            decoded_width=width,
            decoded_height=height,
        )
    if pixel_count > _MAX_IMAGE_PIXELS:
        raise PosterGenerationStageError(
            "image_decode",
            "image_pixel_limit_exceeded",
            "decoded image exceeds configured pixel limit",
            asset_url=ref.url,
            content_type=normalized_content_type,
            byte_size=byte_size,
            decoded_width=width,
            decoded_height=height,
            detail=f"decoded pixels {pixel_count} exceeds max {_MAX_IMAGE_PIXELS}",
        )

    try:
        img = ImageOps.exif_transpose(img)
        if img.mode not in {"RGB", "RGBA"}:
            img = img.convert("RGB")
        elif img.mode == "RGBA":
            img = img.copy()
        else:
            img = img.copy()
        if img.width > _MAX_IMAGE_DIMENSION or img.height > _MAX_IMAGE_DIMENSION:
            img.thumbnail((_MAX_IMAGE_DIMENSION, _MAX_IMAGE_DIMENSION), PILImage.LANCZOS)
        if "icc_profile" in img.info:
            img.info.pop("icc_profile", None)
    except Exception as exc:
        raise PosterGenerationStageError(
            "material_prepare",
            "asset_normalization_failed",
            "failed to normalize asset image",
            detail=str(exc),
            exception_class=exc.__class__.__name__,
            asset_url=ref.url,
            content_type=normalized_content_type,
            byte_size=byte_size,
            decoded_width=width,
            decoded_height=height,
        ) from exc

    logger.info(
        "poster2.asset_preflight url=%s content_type=%s bytes=%d decoded=%sx%s normalized=%sx%s",
        ref.url,
        normalized_content_type,
        byte_size,
        width,
        height,
        img.width,
        img.height,
    )
    return img


async def _preflight_image(data: bytes, *, ref: AssetRef, content_type: str | None) -> PILImage.Image:
    byte_size = len(data)
    try:
        img = await asyncio.wait_for(
            asyncio.to_thread(_decode_image, data, ref=ref, content_type=content_type),
            timeout=_IMAGE_DECODE_TIMEOUT_SEC,
        )
    except PosterGenerationStageError:
        raise
    except asyncio.TimeoutError as exc:
        raise PosterGenerationStageError(
            "image_decode",
            "image_decode_timeout",
            "image decode exceeded timeout",
            detail=f"image_decode timed out after {int(_IMAGE_DECODE_TIMEOUT_SEC * 1000)}ms",
            exception_class=exc.__class__.__name__,
            asset_url=ref.url,
            content_type=_normalize_content_type(content_type),
            byte_size=byte_size,
            retryable=True,
            timeout_ms=int(_IMAGE_DECODE_TIMEOUT_SEC * 1000),
        ) from exc

    try:
        return await asyncio.wait_for(
            asyncio.to_thread(
                _normalize_image,
                img,
                ref=ref,
                content_type=content_type,
                byte_size=byte_size,
            ),
            timeout=_MATERIAL_PREPARE_TIMEOUT_SEC,
        )
    except PosterGenerationStageError:
        raise
    except asyncio.TimeoutError as exc:
        raise PosterGenerationStageError(
            "material_prepare",
            "material_prepare_timeout",
            "material preparation exceeded timeout",
            detail=f"material_prepare timed out after {int(_MATERIAL_PREPARE_TIMEOUT_SEC * 1000)}ms",
            exception_class=exc.__class__.__name__,
            asset_url=ref.url,
            content_type=_normalize_content_type(content_type),
            byte_size=byte_size,
            decoded_width=img.width,
            decoded_height=img.height,
            retryable=True,
            timeout_ms=int(_MATERIAL_PREPARE_TIMEOUT_SEC * 1000),
        ) from exc


class AssetLoader:
    """Resolve all asset refs in a PosterSpec to PIL Images."""

    def __init__(
        self,
        fetch_url: Callable[[str], Awaitable[tuple[bytes, str | None]]] | None = None,
    ):
        self._fetch = fetch_url or _default_fetch

    async def load(self, spec: PosterSpec) -> ResolvedAssets:
        import asyncio

        async def decode(ref: AssetRef) -> PILImage.Image:
            raw, content_type = await _resolve_bytes(ref, self._fetch)
            return await _preflight_image(raw, ref=ref, content_type=content_type)

        async def maybe(ref: Optional[AssetRef]) -> Optional[PILImage.Image]:
            if ref is None:
                return None
            try:
                return await decode(ref)
            except PosterGenerationStageError as exc:
                logger.warning(
                    "poster2.asset_failed stage=%s code=%s url=%s content_type=%s bytes=%s decoded=%sx%s detail=%s",
                    exc.stage,
                    exc.code,
                    exc.context.asset_url,
                    exc.context.content_type,
                    exc.context.byte_size,
                    exc.context.decoded_width,
                    exc.context.decoded_height,
                    exc.detail,
                )
                return None
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

        product_task = asyncio.create_task(decode(spec.product_image))
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

        try:
            product = await product_task
        except PosterGenerationStageError:
            raise
        except Exception as exc:
            raise PosterGenerationStageError(
                "image_decode",
                "product_image_load_failed",
                "product_image is required and could not be loaded",
                detail=str(exc),
                exception_class=exc.__class__.__name__,
                asset_url=spec.product_image.url,
            ) from exc

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
        raw, content_type = await _resolve_bytes(ref, self._fetch)
        return await _preflight_image(raw, ref=ref, content_type=content_type)
