"""
FontRegistry — load and cache PIL ImageFont objects.

Font keys used in TemplateSpec:
  "brand_bold"    → NotoSansSC-SemiBold.ttf  (or Bold if available)
  "brand_regular" → NotoSansSC-Regular.ttf
  "feature"       → NotoSansSC-Regular.ttf (smaller sizes)
  "label"         → NotoSansSC-Regular.ttf (gallery labels)

Falls back to PIL's built-in bitmap font when TTF files are missing,
so tests pass in CI without downloading fonts.
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from PIL import ImageFont

logger = logging.getLogger("ai-service.poster2")

_FONTS_DIR = Path(__file__).resolve().parents[3] / "app" / "assets" / "fonts"

_FONT_FILES: dict[str, str] = {
    "brand_bold": "NotoSansSC-SemiBold.ttf",
    "brand_regular": "NotoSansSC-Regular.ttf",
    "feature": "NotoSansSC-Regular.ttf",
    "label": "NotoSansSC-Regular.ttf",
}


@lru_cache(maxsize=256)
def _load_truetype(path: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(path, size)
    except (OSError, IOError):
        logger.warning("Font not found at %s; using default bitmap font", path)
        return ImageFont.load_default()


class FontRegistry:
    """Thread-safe, cached font loader."""

    def __init__(self, fonts_dir: Path | None = None):
        self._dir = fonts_dir or _FONTS_DIR

    def get(self, font_key: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Return a cached ImageFont for (font_key, size)."""
        filename = _FONT_FILES.get(font_key, "NotoSansSC-Regular.ttf")
        path = str(self._dir / filename)
        if not os.path.exists(path):
            logger.warning(
                "Font file missing: %s. Run scripts/fetch_fonts.sh to download.", path
            )
            return ImageFont.load_default()
        return _load_truetype(path, size)

    def preflight(self) -> dict[str, Any]:
        files: dict[str, Any] = {}
        ready = True
        for font_key, filename in _FONT_FILES.items():
            path = self._dir / filename
            exists = path.exists()
            readable = exists and os.access(path, os.R_OK)
            loadable = False
            error = None
            if readable:
                try:
                    ImageFont.truetype(str(path), size=16)
                    loadable = True
                except Exception as exc:  # pragma: no cover - defensive for runtime font errors
                    error = str(exc)
            else:
                error = "missing_or_unreadable"
            files[font_key] = {
                "path": str(path),
                "exists": exists,
                "readable": readable,
                "loadable": loadable,
                "filename": filename,
                "error": error,
            }
            ready = ready and exists and readable and loadable
        return {
            "ready": ready,
            "font_dir": str(self._dir),
            "required_fonts": files,
            "using_pil_default": not ready,
        }


@lru_cache(maxsize=4)
def poster2_font_preflight(fonts_dir: str | None = None) -> dict[str, Any]:
    registry = FontRegistry(Path(fonts_dir) if fonts_dir else None)
    payload = registry.preflight()
    level = logging.INFO if payload["ready"] else logging.WARNING
    logger.log(level, "poster2.font_preflight=%s", payload)
    return payload
