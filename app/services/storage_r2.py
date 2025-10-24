"""Backward compatible wrapper for legacy imports.

The Cloudflare R2 helpers now live in :mod:`app.services.r2_client`.  This
module continues to expose ``put_bytes`` for older call-sites that still import
from ``app.services.storage_r2``.
"""

from __future__ import annotations

from app.services.r2_client import put_bytes

__all__ = ["put_bytes"]
