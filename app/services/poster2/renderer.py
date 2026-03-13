"""
LayoutRenderer — deterministic foreground rendering via Pillow.

INVARIANT: This module MUST NOT import or call any AI/network service.
           All inputs are PIL Images resolved by AssetLoader.
           Same inputs → bit-identical PNG output.

Output: RGBA foreground.png with transparent background.
        Only text, logo, product, scenario (if provided), and gallery are drawn.
        The Composer later alpha-composites this over the Firefly background.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Optional

from PIL import Image as PILImage, ImageDraw, ImageFilter, ImageFont

from .contracts import (
    GalleryStripSpec,
    ImageSlotSpec,
    PosterSpec,
    ResolvedAssets,
    TemplateSpec,
    TextSlotSpec,
)
from .font_registry import FontRegistry

logger = logging.getLogger("ai-service.poster2")


@dataclass
class ForegroundResult:
    image: PILImage.Image       # RGBA
    png_bytes: bytes
    sha256: str


class LayoutRenderer:
    """
    Renders the foreground layer from TemplateSpec + PosterSpec + ResolvedAssets.
    Must be instantiated once and reused (FontRegistry caches fonts).
    """

    ENGINE_VERSION = "2.0.0"

    def __init__(self, font_registry: FontRegistry | None = None):
        self._fonts = font_registry or FontRegistry()

    # ── Public entry point ────────────────────────────────────────────────────

    def render(
        self,
        spec: TemplateSpec,
        poster: PosterSpec,
        assets: ResolvedAssets,
    ) -> ForegroundResult:
        """
        Deterministic render. Transparent canvas → draw all foreground elements
        in layer order → return RGBA PNG.
        """
        canvas = PILImage.new("RGBA", (spec.canvas_w, spec.canvas_h), (0, 0, 0, 0))

        # Draw order: scenario → product → gallery → logo → text
        if spec.scenario_slot and assets.scenario:
            self._draw_image(canvas, spec.scenario_slot, assets.scenario)

        self._draw_product(canvas, spec.product_slot, assets.product)
        self._draw_gallery(canvas, spec.gallery_slot, assets.gallery)

        if spec.logo_slot and assets.logo:
            self._draw_image(canvas, spec.logo_slot, assets.logo)

        self._draw_text(canvas, spec.brand_name_slot, poster.brand_name)
        self._draw_text(canvas, spec.agent_name_slot, poster.agent_name)
        self._draw_text(canvas, spec.title_slot, poster.title)
        self._draw_text(canvas, spec.subtitle_slot, poster.subtitle)

        for i, slot in enumerate(spec.features_slot):
            text = poster.features[i] if i < len(poster.features) else ""
            if text:
                self._draw_text(canvas, slot, text)

        png_bytes = _to_png(canvas)
        return ForegroundResult(
            image=canvas,
            png_bytes=png_bytes,
            sha256=hashlib.sha256(png_bytes).hexdigest(),
        )

    # ── Image slots ───────────────────────────────────────────────────────────

    def _draw_image(
        self,
        canvas: PILImage.Image,
        slot: ImageSlotSpec,
        img: PILImage.Image,
    ) -> None:
        fitted = _fit_image(img, slot.w, slot.h, slot.fit)
        if slot.shadow:
            fitted = _add_drop_shadow(fitted)
        if slot.radius > 0:
            fitted = _apply_radius(fitted, slot.radius)
        # Center within slot
        ox = slot.x + (slot.w - fitted.width) // 2
        oy = slot.y + (slot.h - fitted.height) // 2
        canvas.alpha_composite(fitted.convert("RGBA"), (ox, oy))

    def _draw_product(
        self,
        canvas: PILImage.Image,
        slot: ImageSlotSpec,
        img: PILImage.Image,
    ) -> None:
        """Product image: ensure RGBA, then composite at slot position."""
        product = img.convert("RGBA")
        self._draw_image(canvas, slot, product)

    def _draw_gallery(
        self,
        canvas: PILImage.Image,
        strip: GalleryStripSpec,
        images: list[PILImage.Image],
    ) -> None:
        if not images:
            return
        for i, img in enumerate(images[: strip.count]):
            x = strip.x + i * (strip.thumb_w + strip.gap)
            thumb_slot = ImageSlotSpec(
                x=x,
                y=strip.y,
                w=strip.thumb_w,
                h=strip.h,
                fit="cover",
                radius=strip.thumb_radius,
            )
            self._draw_image(canvas, thumb_slot, img)

    # ── Text slots ────────────────────────────────────────────────────────────

    def _draw_text(
        self,
        canvas: PILImage.Image,
        slot: TextSlotSpec,
        text: str,
    ) -> None:
        if not text:
            return

        draw = ImageDraw.Draw(canvas)
        font = self._fonts.get(slot.font_key, slot.font_size)

        if slot.auto_shrink:
            font, text = self._fit_text(draw, text, slot, font)

        # Handle multi-line wrapping within slot width
        lines = _wrap_text(draw, text, font, slot.w, slot.max_lines)
        _draw_lines(draw, lines, slot, font)

    def _fit_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        slot: TextSlotSpec,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    ) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, str]:
        """Reduce font size until text fits in slot, down to min size 8."""
        size = slot.font_size
        while size > 8:
            f = self._fonts.get(slot.font_key, size)
            bbox = draw.textbbox((0, 0), text, font=f)
            if (bbox[2] - bbox[0]) <= slot.w and (bbox[3] - bbox[1]) <= slot.h:
                return f, text
            size -= 2
        return self._fonts.get(slot.font_key, 8), text


# ── Module-level helpers (no self, pure functions) ────────────────────────────

def _fit_image(
    img: PILImage.Image, w: int, h: int, fit: str
) -> PILImage.Image:
    img = img.convert("RGBA")
    if fit == "contain":
        img = img.copy()
        img.thumbnail((w, h), PILImage.LANCZOS)
        return img
    if fit == "cover":
        ratio = max(w / img.width, h / img.height)
        new_w = int(img.width * ratio)
        new_h = int(img.height * ratio)
        img = img.resize((new_w, new_h), PILImage.LANCZOS)
        left = (new_w - w) // 2
        top = (new_h - h) // 2
        return img.crop((left, top, left + w, top + h))
    # fill
    return img.resize((w, h), PILImage.LANCZOS)


def _add_drop_shadow(
    img: PILImage.Image,
    offset: tuple[int, int] = (4, 6),
    blur: int = 12,
    shadow_alpha: int = 100,
) -> PILImage.Image:
    result = PILImage.new("RGBA", img.size, (0, 0, 0, 0))
    shadow = PILImage.new("RGBA", img.size, (0, 0, 0, 0))
    # Use the alpha channel of the source image as shadow shape
    if img.mode == "RGBA":
        r, g, b, a = img.split()
        shadow_mask = PILImage.new("RGBA", img.size, (0, 0, 0, 0))
        shadow_mask.paste(
            PILImage.new("RGBA", img.size, (0, 0, 0, shadow_alpha)),
            mask=a,
        )
    else:
        shadow_mask = PILImage.new(
            "RGBA", img.size, (0, 0, 0, shadow_alpha)
        )
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(blur))
    result.alpha_composite(shadow_mask, dest=offset)
    result.alpha_composite(img)
    return result


def _apply_radius(img: PILImage.Image, radius: int) -> PILImage.Image:
    img = img.convert("RGBA")
    mask = PILImage.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=radius, fill=255)
    result = PILImage.new("RGBA", img.size, (0, 0, 0, 0))
    result.paste(img, mask=mask)
    return result


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    """Wrap text into lines that fit within max_width."""
    words = text.split()
    if not words:
        return []

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        test = current + " " + word
        bbox = draw.textbbox((0, 0), test, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            current = test
        else:
            lines.append(current)
            if len(lines) >= max_lines:
                break
            current = word

    if len(lines) < max_lines:
        lines.append(current)

    return lines


def _draw_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    slot: TextSlotSpec,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    if not lines:
        return

    # Measure total text block height
    sample_bbox = draw.textbbox((0, 0), "A", font=font)
    line_h = sample_bbox[3] - sample_bbox[1]
    spacing = int(line_h * (slot.line_height - 1.0))
    block_h = line_h * len(lines) + spacing * (len(lines) - 1)

    # Vertical center in slot
    y = slot.y + max(0, (slot.h - block_h) // 2)

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]

        if slot.align == "center":
            x = slot.x + max(0, (slot.w - line_w) // 2)
        elif slot.align == "right":
            x = slot.x + max(0, slot.w - line_w)
        else:
            x = slot.x

        draw.text((x, y), line, font=font, fill=slot.color)
        y += line_h + spacing


def _to_png(img: PILImage.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()
