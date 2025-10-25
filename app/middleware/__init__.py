"""Middleware utilities for ai-service (legacy import path)."""
from __future__ import annotations

from app.middlewares.reject_huge_or_base64 import RejectHugeOrBase64

BodyGuardMiddleware = RejectHugeOrBase64

__all__ = ["BodyGuardMiddleware", "RejectHugeOrBase64"]
