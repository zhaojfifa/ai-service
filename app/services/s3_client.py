"""Backward compatibility layer for legacy imports.

The project historically imported Cloudflare R2 helpers from
``app.services.s3_client``.  The new implementation lives in
:mod:`app.services.r2_client`; this module simply re-exports the public
functions so existing imports keep working while newer code can depend on
``r2_client`` directly.
"""
from __future__ import annotations

from app.services.r2_client import (
    get_bytes,
    get_client,
    make_key,
    presign_get_url,
    presign_put,
    presign_put_url,
    public_url_for,
    put_bytes,
)

__all__ = [
    "get_bytes",
    "get_client",
    "make_key",
    "presign_get_url",
    "presign_put",
    "presign_put_url",
    "public_url_for",
    "put_bytes",
]
