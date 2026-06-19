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


# ---- email body visual variant (no inner poster banner) ----
# The email container already renders a ttt_html_header; the standalone poster (email_campaign_composite_v1) bakes
# its OWN top banner (.header region = top 130px of the 1240x1754 canvas). Embedding the full standalone poster as
# the email body visual therefore double-headers. We derive an "email_embedded_no_header" variant by deterministically
# cropping that banner region (a named contract constant — NO AI, NO product-fact change). Ratio is used (not raw px)
# so it is robust to any raster scale of the stored poster.
EMAIL_CAMPAIGN_COMPOSITE_CANVAS_H = 1754
EMAIL_CAMPAIGN_COMPOSITE_HEADER_CROP_PX = 130          # .header region height in email_campaign_composite.py
EMAIL_CAMPAIGN_COMPOSITE_HEADER_CROP_RATIO = EMAIL_CAMPAIGN_COMPOSITE_HEADER_CROP_PX / EMAIL_CAMPAIGN_COMPOSITE_CANVAS_H
_TEMPLATE_HEADER_CROP_RATIO = {"email_campaign_composite_v1": EMAIL_CAMPAIGN_COMPOSITE_HEADER_CROP_RATIO}
_TEMPLATES_WITH_OWN_BANNER = {"email_campaign_composite_v1", "template_product_sheet_v1"}


def _read_any_poster_bytes(final_poster: dict[str, Any]) -> bytes:
    url = final_poster.get("url")
    if isinstance(url, str) and url.startswith("data:"):
        import base64
        _, _, b64 = url.partition(",")
        return base64.b64decode(b64)
    return _load_source_poster_bytes(final_poster)


def derive_email_body_visual(record: dict[str, Any]) -> dict[str, Any]:
    """Derive the email-embedded body visual (no inner poster banner) from the selected standalone poster.

    Deterministic image processing only (PIL crop of the named banner region). The standalone poster URL is left
    untouched for download/standalone use; the result is cached on the poster_record under 'email_body_visual'.
    """
    poster_key = record.get("poster_key") or ""
    template_id = record.get("template_id") or (record.get("render_result") or {}).get("template_id") or ""
    final_poster = record.get("final_poster") or {}
    standalone_url = final_poster.get("url") or (record.get("render_result") or {}).get("final_url")
    ratio = _TEMPLATE_HEADER_CROP_RATIO.get(template_id, 0.0)

    cached = record.get("email_body_visual")
    if isinstance(cached, dict) and cached.get("source_poster_key") == poster_key and cached.get("url"):
        return cached

    if ratio <= 0:
        # unknown banner geometry -> embed the standalone poster unchanged (flag its banner state honestly)
        result = {"variant": "standalone_passthrough", "url": standalone_url, "key": final_poster.get("key"),
                  "source_poster_key": poster_key, "contains_own_banner": template_id in _TEMPLATES_WITH_OWN_BANNER,
                  "cropped": False}
    else:
        try:
            with Image.open(io.BytesIO(_read_any_poster_bytes(final_poster))) as im:
                im = im.convert("RGB")
                w, h = im.size
                top = int(round(h * ratio))
                data_buf = io.BytesIO()
                im.crop((0, top, w, h)).save(data_buf, format="PNG")
                data = data_buf.getvalue()
            stored = _store_asset_bytes(poster_key=poster_key, asset_type="email_body_visual",
                                        filename="email_body_visual.png", content_type="image/png", data=data)
            url = stored.get("url")
            if not url:  # local (no R2) -> inline data URL so the email preview can render it
                import base64
                url = "data:image/png;base64," + base64.b64encode(data).decode()
            result = {"variant": "email_embedded_no_header", "url": url, "key": stored.get("key"),
                      "source_poster_key": poster_key, "contains_own_banner": False, "cropped": True,
                      "crop_top_px": top, "crop_ratio": ratio}
        except Exception as exc:  # safe fallback: standalone poster (still flagged as containing its own banner)
            result = {"variant": "standalone_fallback", "url": standalone_url, "key": final_poster.get("key"),
                      "source_poster_key": poster_key, "contains_own_banner": template_id in _TEMPLATES_WITH_OWN_BANNER,
                      "cropped": False, "error": str(exc)[:120]}

    record["email_body_visual"] = result
    try:
        save_poster_record(record)
    except Exception:
        pass
    return result


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
