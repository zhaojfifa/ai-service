from __future__ import annotations

import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from PIL import Image

from app.config import get_settings
from app.services.poster_records import load_poster_record, save_poster_record
from app.services.r2_client import get_bytes, put_bytes


EMAIL_ASSET_DIR = Path("/tmp/ai-service/email-assets")
EMAIL_ASSET_PREFIX = "email-assets"
SUPPORTED_ATTACHMENT_TYPES = ("poster_png", "poster_pdf")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _asset_storage_key(poster_key: str, filename: str) -> str:
    return f"{EMAIL_ASSET_PREFIX}/{poster_key}/{filename}"


def _local_asset_path(poster_key: str, filename: str) -> Path:
    return EMAIL_ASSET_DIR / poster_key / filename


def _store_asset_bytes(
    *,
    poster_key: str,
    asset_type: str,
    filename: str,
    content_type: str,
    data: bytes,
) -> dict[str, Any]:
    settings = get_settings()
    try:
        url = put_bytes(_asset_storage_key(poster_key, filename), data, content_type=content_type)
    except Exception:
        url = None

    if url:
        return {
            "asset_type": asset_type,
            "filename": filename,
            "content_type": content_type,
            "storage_backend": settings.email_attachment.store_backend if settings.email_attachment.store_backend != "auto" else "r2",
            "size_bytes": len(data),
            "created_at": _utc_now(),
            "url": url,
            "key": _asset_storage_key(poster_key, filename),
        }

    path = _local_asset_path(poster_key, filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {
        "asset_type": asset_type,
        "filename": filename,
        "content_type": content_type,
        "storage_backend": "local",
        "size_bytes": len(data),
        "created_at": _utc_now(),
        "url": None,
        "key": None,
        "local_path": str(path),
    }


def _load_source_poster_bytes(final_poster: dict[str, Any]) -> bytes:
    key = final_poster.get("key") or final_poster.get("storage_key")
    if key:
        try:
            return get_bytes(str(key))
        except Exception:
            pass
    url = final_poster.get("url")
    if url:
        response = requests.get(str(url), timeout=30)
        response.raise_for_status()
        return response.content
    raise RuntimeError("final_poster has no readable source")


def _build_pdf_from_png_bytes(png_bytes: bytes) -> bytes:
    with Image.open(io.BytesIO(png_bytes)) as image:
        rgb = image.convert("RGB")
        buffer = io.BytesIO()
        rgb.save(buffer, format="PDF")
        return buffer.getvalue()


def build_email_assets_for_record(
    poster_key: str,
    *,
    asset_types: list[str] | None = None,
) -> dict[str, Any]:
    record = load_poster_record(poster_key)
    if record is None:
        raise KeyError(poster_key)

    settings = get_settings()
    if not settings.email_attachment.enabled:
        return record

    requested_types = [
        item for item in (asset_types or settings.email_attachment.normalized_default_types or list(SUPPORTED_ATTACHMENT_TYPES))
        if item in SUPPORTED_ATTACHMENT_TYPES
    ]
    final_poster = record.get("final_poster") or {}
    email_assets = dict(record.get("email_assets") or {})

    png_bytes: bytes | None = None
    for asset_type in requested_types:
        existing = email_assets.get(asset_type)
        if existing and (existing.get("url") or existing.get("key") or existing.get("local_path")):
            continue
        if png_bytes is None:
            png_bytes = _load_source_poster_bytes(final_poster)
        if asset_type == "poster_png":
            email_assets[asset_type] = _store_asset_bytes(
                poster_key=poster_key,
                asset_type=asset_type,
                filename=f"{poster_key}-poster.png",
                content_type="image/png",
                data=png_bytes,
            )
        elif asset_type == "poster_pdf":
            pdf_bytes = _build_pdf_from_png_bytes(png_bytes)
            email_assets[asset_type] = _store_asset_bytes(
                poster_key=poster_key,
                asset_type=asset_type,
                filename=f"{poster_key}-poster.pdf",
                content_type="application/pdf",
                data=pdf_bytes,
            )

    record["email_assets"] = email_assets
    record["updated_at"] = _utc_now()
    save_poster_record(record)
    return record


def resolve_email_assets(record: dict[str, Any], attachment_types: list[str]) -> list[dict[str, Any]]:
    assets = record.get("email_assets") or {}
    resolved: list[dict[str, Any]] = []
    for asset_type in attachment_types:
        asset = assets.get(asset_type)
        if not asset:
            raise ValueError(f"missing_email_attachment_asset:{asset_type}")
        resolved.append(asset)
    return resolved


def load_email_asset_bytes(asset: dict[str, Any]) -> bytes:
    key = asset.get("key")
    if key:
        try:
            return get_bytes(str(key))
        except Exception:
            pass
    url = asset.get("url")
    if url:
        response = requests.get(str(url), timeout=30)
        response.raise_for_status()
        return response.content
    local_path = asset.get("local_path")
    if local_path:
        return Path(str(local_path)).read_bytes()
    raise RuntimeError(f"Unable to resolve attachment bytes for {asset.get('asset_type')}")
