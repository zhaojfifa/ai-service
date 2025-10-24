"""Compatibility shim that re-exports the new guard middleware."""
from __future__ import annotations

from app.middlewares.huge_or_b64_guard import BodyGuardMiddleware, RejectHugeOrBase64

__all__ = ["BodyGuardMiddleware", "RejectHugeOrBase64"]
