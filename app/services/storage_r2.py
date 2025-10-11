"""Backward compatible wrapper for legacy imports.

The new Cloudflare R2 helpers live in :mod:`app.services.s3_client`.
This module simply re-exports ``put_bytes`` so existing imports keep working.
"""

from __future__ import annotations

from app.services.s3_client import put_bytes

__all__ = ["put_bytes"]
