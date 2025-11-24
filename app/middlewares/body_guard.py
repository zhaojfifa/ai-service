"""Backward-compatible body guard middleware wrappers."""
from __future__ import annotations

import logging
from typing import Any

from .reject_huge_or_base64 import RejectHugeOrBase64

logger = logging.getLogger("ai-service.body-guard")


class BodyGuardMiddleware(RejectHugeOrBase64):
    """Compatibility shim that exposes the legacy middleware name."""

    def __init__(
        self,
        app,
        *,
        max_bytes: int | None = None,
        max_inline_base64_bytes: int | None = None,
        **kwargs: Any,
    ) -> None:  # type: ignore[override]
        super().__init__(
            app,
            max_body_bytes=max_bytes,
            max_inline_base64_bytes=max_inline_base64_bytes,
            **kwargs,
        )
        logger.debug(
            "BodyGuardMiddleware configured",
            extra={
                "max_body_bytes": self.max_body_bytes,
                "max_inline_base64_bytes": self.max_inline_base64_bytes,
            },
        )


__all__ = ["BodyGuardMiddleware"]
