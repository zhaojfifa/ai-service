#!/usr/bin/env python3
"""Generate clean HEADER-ONLY email banner band assets for CUISTANCE v1 Step 3.

The previous banner_option_02.jpg was 1080x720 (a 3:2 image, not a header strip) which cover-cropped into the
email header showing body/product content. These replacements are unambiguous header strips (wide aspect ~6:1,
charcoal brand band + red filet + wordmark) — header only, no product/body/CTA/footer.

Outputs:
  frontend/assets/header_band_01.png  (brand default header)
  frontend/assets/header_band_02.png  (campaign header)

Usage: ./.venv/bin/python scripts/poster2_cuistance_header_band_assets.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "frontend" / "assets"
FONT_BOLD = REPO / "assets/fonts/NotoSansSC-SemiBold.ttf"
FONT_REG = REPO / "assets/fonts/NotoSansSC-Regular.ttf"

W, H = 1200, 200
CHARCOAL = (31, 35, 41)       # #1f2329
RED = (225, 0, 42)            # #E1002A
WHITE = (255, 255, 255)
MUTED = (207, 211, 216)       # #cfd3d8


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def build(path: Path, wordmark: str, tag: str | None) -> None:
    im = Image.new("RGB", (W, H), CHARCOAL)
    d = ImageDraw.Draw(im)
    # brand wordmark (left)
    d.text((48, 64), wordmark, font=_font(FONT_BOLD, 64), fill=WHITE)
    # optional campaign tag (right) on a red chip
    if tag:
        f = _font(FONT_BOLD, 30)
        tb = d.textbbox((0, 0), tag, font=f)
        tw, th = tb[2] - tb[0], tb[3] - tb[1]
        pad = 16
        x1 = W - 48 - (tw + pad * 2)
        y1 = (H - (th + pad)) // 2
        d.rounded_rectangle([x1, y1, x1 + tw + pad * 2, y1 + th + pad], radius=8, fill=RED)
        d.text((x1 + pad, y1 + pad // 2 - tb[1]), tag, font=f, fill=WHITE)
    # red filet at the very bottom (header boundary)
    d.rectangle([0, H - 8, W, H], fill=RED)
    im.save(path, "PNG")
    print("wrote", path.relative_to(REPO), im.size)


def main() -> None:
    build(OUT / "header_band_01.png", "CUISTANCE", None)
    build(OUT / "header_band_02.png", "CUISTANCE", "NOUVEAUTÉ")


if __name__ == "__main__":
    main()
