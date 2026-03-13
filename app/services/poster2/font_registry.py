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
