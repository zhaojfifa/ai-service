"""Compatibility shim that re-exports the new guard middleware."""
from __future__ import annotations

from app.middlewares.body_guard import BodyGuardMiddleware
from app.middlewares.reject_huge_or_base64 import RejectHugeOrBase64

__all__ = ["BodyGuardMiddleware", "RejectHugeOrBase64"]
