"""Legacy body guard compatibility wrappers."""
from __future__ import annotations

from .huge_or_b64_guard import RejectHugeOrBase64


BodyGuardMiddleware = RejectHugeOrBase64

__all__ = ["RejectHugeOrBase64", "BodyGuardMiddleware"]
