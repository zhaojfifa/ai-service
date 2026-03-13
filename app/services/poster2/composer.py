"""
Composer — alpha-composite background + foreground into final poster.

Rule: NEVER modify text or structural elements here.
      Only blend the two layers; optional: environment light/shadow pass.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from io import BytesIO

from PIL import Image as PILImage

logger = logging.getLogger("ai-service.poster2")


@dataclass
class ComposerResult:
    image: PILImage.Image   # RGB (flattened for export)
    png_bytes: bytes
    sha256: str


class Composer:

    def compose(
        self,
        background: PILImage.Image,      # RGB or RGBA background (Firefly output)
        foreground: PILImage.Image,      # RGBA foreground (LayoutRenderer output)
        export_format: str = "png",
    ) -> ComposerResult:
        """
        Merge layers:
          1. Resize background to match foreground canvas size.
          2. Alpha-composite foreground over background.
          3. Flatten to RGB and encode.
        """
        # Ensure background fills the exact canvas
        if background.size != foreground.size:
            background = background.resize(foreground.size, PILImage.LANCZOS)

        base = background.convert("RGBA")
        base.alpha_composite(foreground)
        result = base.convert("RGB")

        png_bytes = _encode(result, export_format)
        return ComposerResult(
            image=result,
            png_bytes=png_bytes,
            sha256=hashlib.sha256(png_bytes).hexdigest(),
        )


def _encode(img: PILImage.Image, fmt: str) -> bytes:
    buf = BytesIO()
    fmt_upper = fmt.upper()
    if fmt_upper == "JPEG":
        img.save(buf, format="JPEG", quality=92, optimize=True)
    elif fmt_upper == "WEBP":
        img.save(buf, format="WEBP", quality=90, method=4)
    else:
        img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
