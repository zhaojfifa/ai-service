"""Thin wrapper around the R2 client for storing generated images."""
from __future__ import annotations

import datetime as _dt
import mimetypes
import uuid
from typing import Any, Dict

from app.services.s3_client import public_url_for, put_bytes

_DEFAULT_EXT = "png"


def _new_key(ext: str = _DEFAULT_EXT) -> str:
    today = _dt.datetime.utcnow().strftime("%Y/%m/%d")
    safe_ext = ext.lstrip(".") or _DEFAULT_EXT
    return f"imagen/{today}/{uuid.uuid4().hex}.{safe_ext}"


def store_image_and_url(
    data: bytes,
    *,
    ext: str = _DEFAULT_EXT,
    content_type: str | None = None,
    key: str | None = None,
) -> Dict[str, Any]:
    """Persist *data* to Cloudflare R2 and return metadata."""

    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("image payload must be bytes")

    storage_key = (key or _new_key(ext)).lstrip("/")
    ext_hint = storage_key.rsplit(".", 1)[-1] if "." in storage_key else ext
    safe_ext = ext_hint.lstrip(".") or _DEFAULT_EXT
    guessed_type = mimetypes.types_map.get(f".{safe_ext}", "image/png")
    ct = content_type or guessed_type

    url = put_bytes(storage_key, bytes(data), content_type=ct) or public_url_for(storage_key)
    if not url:
        raise RuntimeError(f"Failed to store image at key={storage_key}")

    return {"key": storage_key, "url": url, "content_type": ct}
