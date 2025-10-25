"""Legacy compatibility shim for RejectHugeOrBase64 middleware."""
from __future__ import annotations

from .reject_huge_or_base64 import RejectHugeOrBase64

BodyGuardMiddleware = RejectHugeOrBase64

__all__ = ["RejectHugeOrBase64", "BodyGuardMiddleware"]
