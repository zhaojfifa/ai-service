"""Middleware utilities for ai-service (legacy import path)."""
from __future__ import annotations

import importlib
import warnings

RejectHugeOrBase64 = None
try:
    RejectHugeOrBase64 = getattr(importlib.import_module("app.middlewares.huge_or_b64_guard"), "RejectHugeOrBase64", None)
except Exception as exc:  # pragma: no cover - legacy compatibility
    warnings.warn(f"RejectHugeOrBase64 unavailable: {exc!r}")

BodyGuardMiddleware = RejectHugeOrBase64

__all__ = ["BodyGuardMiddleware", "RejectHugeOrBase64"]
