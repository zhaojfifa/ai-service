"""
Renderer abstraction for poster2 foreground composition.

Two deterministic engines are available:
  - pillow: existing pure-Pillow renderer, always available
  - puppeteer: structured HTML/CSS/SVG renderer backed by Chromium/Playwright

The Chromium path is additive and optional. If it is unavailable or fails at
runtime, callers can degrade back to Pillow without changing the poster2 route.
"""
from __future__ import annotations

import base64
import asyncio
import hashlib
import html
import json
import logging
import os
import time
from dataclasses import dataclass, field, replace
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

from PIL import Image as PILImage, ImageDraw, ImageFilter, ImageFont

from .contracts import (
    FeatureCalloutSpec,
    GalleryStripSpec,
    ImageSlotSpec,
    PosterSpec,
    RendererMode,
    ResolvedAssets,
    TemplateSpec,
    TextSlotSpec,
)
from .font_registry import FontRegistry
from .renderer_routing import RendererRoutingError, evaluate_fallback_eligibility, resolve_renderer_routing
from .template_behavior import (
    ResolvedBottomBehavior,
    ResolvedFeatureBehavior,
    ResolvedHeaderBehavior,
    ResolvedProductBehavior,
    resolve_feature_layout_mode,
    resolve_template_behavior,
)
from .template_registry import resolve_template_metadata

logger = logging.getLogger("ai-service.poster2")

_HTML_TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "app" / "templates_html"
class RendererUnavailableError(RuntimeError):
    """Raised when a requested renderer is not available in the runtime."""


@dataclass
class PuppeteerFailureInfo:
    reason_code: str
    detail: str
    exception_class: str
    stage: str


class PuppeteerRenderError(RuntimeError):
    def __init__(self, failure: PuppeteerFailureInfo):
        super().__init__(failure.detail)
        self.failure = failure


@dataclass
class ForegroundResult:
    image: PILImage.Image
    png_bytes: bytes
    sha256: str
    render_engine_used: str
    foreground_renderer: str
    template_contract_version: str
    layer_timings_ms: dict[str, int] = field(default_factory=dict)
    fallback_reason_code: Optional[str] = None
    fallback_reason_detail: Optional[str] = None
    fallback_exception_class: Optional[str] = None
    fallback_stage: Optional[str] = None
    degraded: bool = False
    degraded_reason: Optional[str] = None
    gallery_items_status: list[dict] = field(default_factory=list)
    layer_render_status: dict[str, dict[str, Any]] = field(default_factory=dict)
    region_render_status: dict[str, dict[str, Any]] = field(default_factory=dict)


def _rectangles_intersect(
    ax: int,
    ay: int,
    aw: int,
    ah: int,
    bx: int,
    by: int,
    bw: int,
    bh: int,
) -> bool:
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


class LayoutRenderer:
    """
    Deterministic foreground rendering via Pillow.

    This is the existing poster2 renderer and remains the default fallback.
    """

    ENGINE_VERSION = "2.1.0"
    RENDER_ENGINE = "pillow"
    RENDERER_NAME = "poster2.pillow_layout"

    def __init__(self, font_registry: FontRegistry | None = None):
        self._fonts = font_registry or FontRegistry()

    def render(
        self,
        spec: TemplateSpec,
        poster: PosterSpec,
        assets: ResolvedAssets,
    ) -> ForegroundResult:
        feature_count = len(_normalized_feature_texts(poster.features))
        behavior = resolve_template_behavior(
            spec,
            feature_count=feature_count,
            title_text=poster.title,
            subtitle_text=poster.subtitle,
            brand_name=poster.brand_name,
            gallery_requested_count=poster.gallery_requested_count if poster.gallery_requested_count is not None else len(poster.gallery_images),
            gallery_input_count_normalized=poster.gallery_input_count_normalized if poster.gallery_input_count_normalized is not None else len(poster.gallery_images),
            gallery_resolved_count=min(len(assets.gallery), spec.gallery_slot.count),
            bottom_mode=poster.bottom_mode,
            gallery_mode=poster.gallery_mode,
            agent_name=poster.agent_name,
            has_product_secondary_asset=assets.product_secondary is not None,
        )
        canvas = PILImage.new("RGBA", (spec.canvas_w, spec.canvas_h), (0, 0, 0, 0))
        layer_timings: dict[str, int] = {}

        t0 = _now()
        self._draw_shells(
            canvas,
            spec,
            poster,
            behavior,
            has_scenario=behavior.hero_policy.scenario_enabled and assets.scenario is not None,
        )
        if behavior.hero_policy.scenario_enabled and spec.scenario_slot and assets.scenario:
            self._draw_image(canvas, _scenario_image_slot(spec, behavior.hero_policy), assets.scenario)
        self._draw_product(
            canvas,
            _product_image_slot(spec, behavior.hero_policy, behavior.product_policy),
            assets.product,
        )
        if behavior.product_policy.product_secondary_slot_rendered and assets.product_secondary is not None:
            self._draw_product(
                canvas,
                _product_secondary_image_slot(spec, behavior.product_policy),
                assets.product_secondary,
            )
        self._draw_gallery(
            canvas,
            spec.gallery_slot,
            assets.gallery,
            bottom_policy=behavior.bottom_policy,
            visible_count=behavior.bottom_policy.visible_item_count if behavior.bottom_policy.gallery_strip_rendered else 0,
        )
        if spec.logo_slot and assets.logo and behavior.header_policy.identity_zone_mode != "brand_only":
            self._draw_image(canvas, spec.logo_slot, assets.logo)
        layer_timings["product_material_layer_ms"] = _elapsed(t0)

        t1 = _now()
        resolved_callouts = _resolve_feature_callout_layout(
            spec.feature_callouts,
            poster.features,
            feature_policy=behavior.feature_policy,
            product_policy=behavior.product_policy,
            accent_color=behavior.accent_color,
            text_color=behavior.text_colors["feature"],
        )
        self._draw_feature_callout_structure(canvas, resolved_callouts)
        layer_timings["foreground_structure_layer_ms"] = _elapsed(t1)

        t2 = _now()
        self._draw_feature_callout_labels(canvas, resolved_callouts)
        self._draw_text(
            canvas,
            _brand_text_slot(spec, behavior.header_policy, color=behavior.text_colors["brand"]),
            _apply_char_budget(poster.brand_name, behavior.header_policy.brand_char_budget),
            draw_background=False,
        )
        if behavior.header_policy.agent_pill_visible:
            self._draw_text(
                canvas,
                _agent_text_slot(spec, behavior.header_policy, color=behavior.text_colors["agent"]),
                _apply_char_budget(poster.agent_name, behavior.header_policy.agent_char_budget),
                draw_background=False,
            )
        if behavior.bottom_policy.title_slot_rendered:
            self._draw_text(
                canvas,
                _title_text_slot(spec, behavior.bottom_policy, color=behavior.text_colors["title"]),
                _apply_char_budget(poster.title, behavior.bottom_policy.title_char_budget),
                draw_background=False,
            )
        if behavior.bottom_policy.subtitle_slot_rendered:
            self._draw_text(
                canvas,
                _subtitle_text_slot(spec, behavior.bottom_policy, color=behavior.text_colors["subtitle"]),
                _apply_char_budget(poster.subtitle, behavior.bottom_policy.subtitle_char_budget),
                draw_background=False,
            )
        layer_timings["text_layer_ms"] = _elapsed(t2)

        png_bytes = _to_png(canvas)
        gallery_items_status = _annotate_gallery_items_status_from_spec(assets.gallery_status, spec, behavior.bottom_policy)
        layer_render_status = _build_renderer_layer_render_status(
            poster=poster,
            has_logo=assets.logo is not None,
            has_scenario=behavior.hero_policy.scenario_enabled and assets.scenario is not None,
            has_product=assets.product is not None,
            has_product_secondary=assets.product_secondary is not None,
            feature_count=behavior.feature_policy.visible_item_count,
            gallery_valid=min(len(assets.gallery), spec.gallery_slot.count),
            gallery_visible=behavior.bottom_policy.visible_item_count if behavior.bottom_policy.gallery_strip_rendered else 0,
            gallery_requested=min(len(poster.gallery_images), spec.gallery_slot.count),
            scenario_source=(
                poster.scenario_image.url
                if (poster.scenario_image and behavior.hero_policy.scenario_enabled)
                else None
            ),
            product_source=poster.product_image.url,
            logo_source=poster.logo.url if poster.logo else None,
            scenario_safe_fill=False,
            bottom_policy=behavior.bottom_policy,
            header_policy=behavior.header_policy,
            feature_mode=behavior.feature_policy.mode,
            product_policy=behavior.product_policy,
        )
        return ForegroundResult(
            image=canvas,
            png_bytes=png_bytes,
            sha256=hashlib.sha256(png_bytes).hexdigest(),
            render_engine_used=self.RENDER_ENGINE,
            foreground_renderer=self.RENDERER_NAME,
            template_contract_version=spec.contract_version,
            layer_timings_ms=layer_timings,
            gallery_items_status=gallery_items_status,
            layer_render_status=layer_render_status,
            region_render_status=_build_renderer_region_render_status(layer_render_status),
        )

    def _draw_shells(
        self,
        canvas: PILImage.Image,
        spec: TemplateSpec,
        poster: PosterSpec,
        behavior: Any,
        *,
        has_scenario: bool,
    ) -> None:
        has_title_band = behavior.bottom_policy.title_band_rendered
        has_gallery = behavior.bottom_policy.gallery_strip_rendered
        header_box = _header_shell_bounds(spec, behavior.header_policy)
        self._draw_shell_box(
            canvas,
            header_box,
            radius=28,
            fill=_pillow_shell_fill("header", behavior.beauty_tokens.shell_surface, accent=behavior.accent_color),
            border=_pillow_border("header", behavior.beauty_tokens.shell_border, accent=behavior.accent_color),
            shadow=_pillow_shadow(behavior.beauty_tokens.shell_shadow),
        )
        if behavior.hero_policy.scenario_enabled and spec.scenario_slot:
            self._draw_shell_box(
                canvas,
                _scenario_shell_bounds(spec, behavior.hero_policy),
                radius=24,
                fill=_pillow_shell_fill(
                    "scenario_real" if has_scenario else "scenario_safe",
                    behavior.beauty_tokens.shell_surface,
                    accent=behavior.accent_color,
                ),
                border=_pillow_border("hero", behavior.beauty_tokens.shell_border, accent=behavior.accent_color),
                shadow=_pillow_shadow(behavior.beauty_tokens.shell_shadow),
            )
        self._draw_shell_box(
            canvas,
            _product_shell_bounds(spec, behavior.product_policy),
            radius=24,
            fill=_pillow_shell_fill("product", behavior.beauty_tokens.shell_surface, accent=behavior.accent_color),
            border=_pillow_border("product", behavior.beauty_tokens.shell_border, accent=behavior.accent_color),
            shadow=_pillow_shadow(behavior.beauty_tokens.shell_shadow),
        )
        if has_title_band or has_gallery:
            self._draw_shell_box(
                canvas,
                _bottom_shell_bounds(spec, behavior.bottom_policy),
                radius=28,
                fill=_pillow_shell_fill("bottom", behavior.beauty_tokens.shell_surface, accent=behavior.accent_color),
                border=_pillow_border("bottom", behavior.beauty_tokens.shell_border, accent=behavior.accent_color),
                shadow=_pillow_shadow(behavior.beauty_tokens.shell_shadow),
            )
        if has_title_band:
            self._draw_shell_box(
                canvas,
                _title_band_shell_bounds(spec, behavior.bottom_policy),
                radius=28,
                fill=_pillow_shell_fill("title_band", behavior.beauty_tokens.shell_surface, accent=behavior.accent_color),
                border=_pillow_border("bottom", behavior.beauty_tokens.shell_border, accent=behavior.accent_color),
                shadow=_pillow_shadow(behavior.beauty_tokens.shell_shadow),
            )
        if has_gallery:
            self._draw_shell_box(
                canvas,
                _gallery_strip_shell_bounds(spec, behavior.bottom_policy),
                radius=int(behavior.bottom_policy.layout_metrics.get("gallery_shell_radius", 20)),
                fill=_pillow_shell_fill("gallery_strip", behavior.beauty_tokens.shell_surface, accent=behavior.accent_color),
                border=_pillow_border("gallery", behavior.beauty_tokens.shell_border, accent=behavior.accent_color),
                shadow=_pillow_shadow(behavior.beauty_tokens.shell_shadow),
            )

    def _draw_shell_box(
        self,
        canvas: PILImage.Image,
        bounds: tuple[int, int, int, int],
        *,
        radius: int,
        fill: tuple[int, int, int, int],
        border: tuple[int, int, int, int],
        shadow: tuple[int, int, int, int, int] | None,
    ) -> None:
        x, y, w, h = bounds
        if shadow is not None:
            ox, oy, blur, expansion, alpha = shadow
            shadow_layer = PILImage.new("RGBA", canvas.size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            shadow_draw.rounded_rectangle(
                [x - expansion + ox, y - expansion + oy, x + w + expansion + ox, y + h + expansion + oy],
                radius=max(radius + expansion, 0),
                fill=(20, 16, 16, alpha),
            )
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=blur))
            canvas.alpha_composite(shadow_layer)
        box_layer = PILImage.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(box_layer)
        draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill, outline=border, width=1)
        canvas.alpha_composite(box_layer)

    def _draw_feature_callout_structure(
        self,
        canvas: PILImage.Image,
        callouts: list[tuple[FeatureCalloutSpec, str]],
    ) -> None:
        draw = ImageDraw.Draw(canvas)
        for callout, text in callouts:
            if not text or callout.anchor_radius <= 0:
                continue
            r = callout.anchor_radius
            ax, ay = callout.anchor_x, callout.anchor_y
            draw.ellipse([ax - r - 2, ay - r - 2, ax + r + 2, ay + r + 2], fill=(255, 255, 255, 200))
            draw.ellipse([ax - r, ay - r, ax + r, ay + r], fill=callout.anchor_color)
            lb = callout.label_box
            draw.line(
                [(ax, ay), (lb.x, lb.y + lb.h // 2)],
                fill=callout.leader_color,
                width=callout.leader_width,
            )

    def _draw_feature_callout_labels(
        self,
        canvas: PILImage.Image,
        callouts: list[tuple[FeatureCalloutSpec, str]],
    ) -> None:
        for callout, text in callouts:
            if not text:
                continue
            self._draw_text(canvas, callout.label_box, text, draw_background=False)

    def _draw_feature_callout(
        self,
        draw: ImageDraw.ImageDraw,
        canvas: PILImage.Image,
        callout: FeatureCalloutSpec,
        text: str,
    ) -> None:
        if text and callout.anchor_radius > 0:
            r = callout.anchor_radius
            ax, ay = callout.anchor_x, callout.anchor_y
            draw.ellipse([ax - r, ay - r, ax + r, ay + r], fill=callout.anchor_color)
            lb = callout.label_box
            draw.line(
                [(ax, ay), (lb.x, lb.y + lb.h // 2)],
                fill=callout.leader_color,
                width=callout.leader_width,
            )
        if text:
            self._draw_text(canvas, callout.label_box, text, draw_background=False)

    def _draw_slot_background(self, canvas: PILImage.Image, slot: TextSlotSpec) -> None:
        draw = ImageDraw.Draw(canvas)
        _draw_pill_bg(draw, slot)

    def _draw_image(self, canvas: PILImage.Image, slot: ImageSlotSpec, img: PILImage.Image) -> None:
        inner_x = slot.x + slot.pad_left
        inner_y = slot.y + slot.pad_top
        inner_w = max(1, slot.w - slot.pad_left - slot.pad_right)
        inner_h = max(1, slot.h - slot.pad_top - slot.pad_bottom)
        fitted = _fit_image(img, inner_w, inner_h, slot.fit)
        if slot.shadow:
            fitted = _add_drop_shadow(fitted)
        if slot.radius > 0:
            fitted = _apply_radius(fitted, slot.radius)
        if slot.align_x == "start":
            ox = inner_x
        elif slot.align_x == "end":
            ox = inner_x + max(0, inner_w - fitted.width)
        else:
            ox = inner_x + max(0, (inner_w - fitted.width) // 2)
        if slot.align_y == "start":
            oy = inner_y
        elif slot.align_y == "end":
            oy = inner_y + max(0, inner_h - fitted.height)
        else:
            oy = inner_y + max(0, (inner_h - fitted.height) // 2)
        canvas.alpha_composite(fitted.convert("RGBA"), (ox, oy))

    def _draw_product(self, canvas: PILImage.Image, slot: ImageSlotSpec, img: PILImage.Image) -> None:
        self._draw_image(canvas, slot, img.convert("RGBA"))

    def _draw_gallery(
        self,
        canvas: PILImage.Image,
        strip: GalleryStripSpec,
        images: list[PILImage.Image],
        *,
        bottom_policy: ResolvedBottomBehavior,
        visible_count: int,
    ) -> None:
        if not images or visible_count <= 0:
            return
        gallery_item_layouts = list(bottom_policy.layout_metrics.get("gallery_item_layouts", []))
        if not gallery_item_layouts:
            raise AssertionError(
                "gallery_item_layouts must be populated by the behavior resolver before "
                "gallery strip render. Call resolve_template_behavior() with "
                "gallery_resolved_count before invoking _draw_gallery."
            )
        for i, img in enumerate(images[: min(strip.count, visible_count)]):
            if i >= len(gallery_item_layouts):
                raise AssertionError(
                    f"gallery_item_layouts has {len(gallery_item_layouts)} entries but "
                    f"slot index {i} was requested. visible_count ({visible_count}) must "
                    "not exceed len(gallery_item_layouts)."
                )
            slot_layout = gallery_item_layouts[i]
            x = int(slot_layout["x"])
            y = int(slot_layout["y"])
            w = int(slot_layout["w"])
            h = int(slot_layout["h"])
            thumb_slot = ImageSlotSpec(
                x=x,
                y=y,
                w=w,
                h=h,
                fit="cover",
                radius=int(bottom_policy.layout_metrics.get("gallery_item_radius", strip.thumb_radius)),
            )
            self._draw_image(canvas, thumb_slot, img)

    def _draw_text(
        self,
        canvas: PILImage.Image,
        slot: TextSlotSpec,
        text: str,
        *,
        draw_background: bool = True,
    ) -> None:
        if not text:
            return
        draw = ImageDraw.Draw(canvas)
        if draw_background and slot.bg_color:
            _draw_pill_bg(draw, slot)

        font = self._fonts.get(slot.font_key, slot.font_size)
        if slot.auto_shrink:
            font, text = self._fit_text(draw, text, slot)
        lines = _wrap_text(draw, text, font, slot.w, slot.max_lines)
        _draw_lines(draw, lines, slot, font)

    def _fit_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        slot: TextSlotSpec,
    ) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, str]:
        size = slot.font_size
        while size > 8:
            font = self._fonts.get(slot.font_key, size)
            bbox = draw.textbbox((0, 0), text, font=font)
            if (bbox[2] - bbox[0]) <= slot.w and (bbox[3] - bbox[1]) <= slot.h:
                return font, text
            size -= 2
        return self._fonts.get(slot.font_key, 8), text


class PuppeteerStructuredRenderer:
    """
    Structured HTML foreground renderer backed by Chromium/Playwright.

    The mode name is `puppeteer` to match the product architecture decision.
    The Python runtime uses Playwright to drive Chromium.
    """

    ENGINE_VERSION = "2.1.0"
    RENDER_ENGINE = "puppeteer"
    RENDERER_NAME = "poster2.puppeteer_structured"
    DEFAULT_NAVIGATION_TIMEOUT_MS = 45000
    DEFAULT_RENDER_TIMEOUT_MS = 45000
    DEFAULT_FONT_READY_GRACE_MS = 1500

    def __init__(
        self,
        templates_dir: Path | None = None,
        font_registry: FontRegistry | None = None,
        navigation_timeout_ms: int | None = None,
        render_timeout_ms: int | None = None,
        font_ready_grace_ms: int | None = None,
    ):
        self._templates_dir = templates_dir or _HTML_TEMPLATES_DIR
        self._fonts = font_registry or FontRegistry()
        self._navigation_timeout_ms = navigation_timeout_ms or self.DEFAULT_NAVIGATION_TIMEOUT_MS
        self._render_timeout_ms = render_timeout_ms or self.DEFAULT_RENDER_TIMEOUT_MS
        self._font_ready_grace_ms = font_ready_grace_ms or self.DEFAULT_FONT_READY_GRACE_MS

    async def render(
        self,
        spec: TemplateSpec,
        poster: PosterSpec,
        assets: ResolvedAssets,
    ) -> ForegroundResult:
        feature_count = len(_normalized_feature_texts(poster.features))
        behavior = resolve_template_behavior(
            spec,
            feature_count=feature_count,
            title_text=poster.title,
            subtitle_text=poster.subtitle,
            brand_name=poster.brand_name,
            gallery_requested_count=poster.gallery_requested_count if poster.gallery_requested_count is not None else len(poster.gallery_images),
            gallery_input_count_normalized=poster.gallery_input_count_normalized if poster.gallery_input_count_normalized is not None else len(poster.gallery_images),
            gallery_resolved_count=min(len(assets.gallery), spec.gallery_slot.count),
            bottom_mode=poster.bottom_mode,
            gallery_mode=poster.gallery_mode,
            agent_name=poster.agent_name,
            has_product_secondary_asset=assets.product_secondary is not None,
        )
        t0 = _now()
        logger.info("poster2.puppeteer: template_render_start template=%s", spec.template_id)
        try:
            html_template = self._read_template_file(f"{spec.template_id}.html")
            css_template = self._read_template_file(f"{spec.template_id}.css")
            svg_overlay = self._read_template_file(f"{spec.template_id}.svg", optional=True)
            slot_spec = self._read_json_file(f"slot_spec.{spec.template_id}.json")
            anchor_map = self._read_json_file(f"anchor_map.{spec.template_id}.json")
        except Exception as exc:
            raise _classify_puppeteer_exception(exc, stage="template_render") from exc
        layer_timings: dict[str, int] = {}
        layer_timings["foreground_structure_layer_ms"] = _elapsed(t0)
        logger.info("poster2.puppeteer: template_render_done template=%s ms=%d", spec.template_id, layer_timings["foreground_structure_layer_ms"])

        t1 = _now()
        try:
            has_real_scenario = behavior.hero_policy.scenario_enabled and assets.scenario is not None
            scenario_url = ""
            if behavior.hero_policy.scenario_enabled:
                scenario_url = (
                    _image_to_data_url(assets.scenario)
                    if has_real_scenario
                    else _safe_preset_scenario_data_url()
                )
            logger.info(
                "poster2.gallery_prepare_start requested=%d resolved=%d",
                len(assets.gallery_status),
                len(assets.gallery),
            )
            gallery_urls, gallery_items_status = _prepare_gallery_urls(
                assets.gallery,
                assets.gallery_status,
                slot_spec,
            )
            logger.info(
                "poster2.gallery_prepare_done requested=%d prepared=%d",
                len(assets.gallery_status),
                len(gallery_urls),
            )
            logger.info("poster2.gallery_render_start count=%d", len(gallery_urls))
            asset_urls = {
                "logo": _image_to_data_url(assets.logo) if assets.logo else "",
                "scenario": scenario_url,
                "scenario_is_real": has_real_scenario,
                "product": _image_to_data_url(assets.product),
                "product_secondary": _image_to_data_url(assets.product_secondary) if assets.product_secondary else "",
                "gallery": gallery_urls,
            }
            logger.info(
                "poster2.gallery_render_done count=%d bytes=%d",
                len(gallery_urls),
                sum(len(url) for url in gallery_urls),
            )
            gallery_visible_count = _visible_gallery_item_count(slot_spec, len(gallery_urls))
        except Exception as exc:
            raise _classify_puppeteer_exception(exc, stage="gallery_render") from exc
        layer_timings["product_material_layer_ms"] = _elapsed(t1)

        t2 = _now()
        try:
            html_payload = self._build_html(
                html_template=html_template,
                css_template=css_template,
                svg_overlay=svg_overlay,
                poster=poster,
                asset_urls=asset_urls,
                slot_spec=slot_spec,
                anchor_map=anchor_map,
                spec=spec,
                behavior=behavior,
            )
        except Exception as exc:
            raise _classify_puppeteer_exception(exc, stage="template_render") from exc
        layer_timings["text_layer_ms"] = _elapsed(t2)

        png_bytes = await self._render_html_to_png(html_payload, spec.canvas_w, spec.canvas_h)
        image = PILImage.open(BytesIO(png_bytes)).convert("RGBA")
        gallery_items_status = _annotate_gallery_items_status(gallery_items_status, behavior.bottom_policy)
        layer_render_status = _build_renderer_layer_render_status(
            poster=poster,
            has_logo=bool(asset_urls["logo"]),
            has_scenario=behavior.hero_policy.scenario_enabled and bool(asset_urls.get("scenario_is_real")),
            has_product=True,
            has_product_secondary=bool(asset_urls.get("product_secondary")),
            feature_count=behavior.feature_policy.visible_item_count,
            gallery_valid=min(len(asset_urls["gallery"]), spec.gallery_slot.count),
            gallery_visible=behavior.bottom_policy.visible_item_count if behavior.bottom_policy.gallery_strip_rendered else 0,
            gallery_requested=min(len(poster.gallery_images), spec.gallery_slot.count),
            scenario_source=(
                poster.scenario_image.url
                if (poster.scenario_image and behavior.hero_policy.scenario_enabled)
                else ("safe_preset_image" if behavior.hero_policy.scenario_enabled else None)
            ),
            product_source=poster.product_image.url,
            logo_source=poster.logo.url if poster.logo else None,
            scenario_safe_fill=behavior.hero_policy.scenario_enabled and not bool(asset_urls.get("scenario_is_real")),
            bottom_policy=behavior.bottom_policy,
            header_policy=behavior.header_policy,
            feature_mode=behavior.feature_policy.mode,
            product_policy=behavior.product_policy,
        )
        return ForegroundResult(
            image=image,
            png_bytes=png_bytes,
            sha256=hashlib.sha256(png_bytes).hexdigest(),
            render_engine_used=self.RENDER_ENGINE,
            foreground_renderer=self.RENDERER_NAME,
            template_contract_version=str(slot_spec.get("template_contract_version", spec.contract_version)),
            layer_timings_ms=layer_timings,
            gallery_items_status=gallery_items_status,
            layer_render_status=layer_render_status,
            region_render_status=_build_renderer_region_render_status(layer_render_status),
        )

    def _read_template_file(self, name: str, optional: bool = False) -> str:
        path = self._templates_dir / name
        if not path.exists():
            if optional:
                return ""
            raise RendererUnavailableError(f"Structured renderer asset missing: {path}")
        return path.read_text(encoding="utf-8")

    def _read_json_file(self, name: str) -> dict[str, Any]:
        return json.loads(self._read_template_file(name))

    def _build_html(
        self,
        *,
        html_template: str,
        css_template: str,
        svg_overlay: str,
        poster: PosterSpec,
        asset_urls: dict[str, Any],
        slot_spec: dict[str, Any],
        anchor_map: dict[str, Any],
        spec: TemplateSpec,
        behavior: Any | None = None,
    ) -> str:
        behavior = behavior or resolve_template_behavior(
            spec,
            feature_count=len(_normalized_feature_texts(poster.features)),
            title_text=poster.title,
            subtitle_text=poster.subtitle,
            brand_name=poster.brand_name,
            gallery_requested_count=poster.gallery_requested_count if poster.gallery_requested_count is not None else len(poster.gallery_images),
            gallery_input_count_normalized=poster.gallery_input_count_normalized if poster.gallery_input_count_normalized is not None else len(poster.gallery_images),
            gallery_resolved_count=len(asset_urls.get("gallery") or []),
            bottom_mode=poster.bottom_mode,
            gallery_mode=poster.gallery_mode,
            agent_name=poster.agent_name,
        )
        template_contract_version = str(slot_spec.get("template_contract_version", spec.contract_version))
        font_css = self._font_faces_css()
        gallery_markup, gallery_layer_class = self._gallery_markup(
            slot_spec,
            asset_urls["gallery"][: behavior.bottom_policy.visible_item_count],
            behavior.bottom_policy,
        )
        feature_markup, feature_layer_class = self._feature_markup(
            anchor_map,
            poster.features,
            feature_policy=behavior.feature_policy,
            product_policy=behavior.product_policy,
        )
        logo_suppressed_by_mode = behavior.header_policy.identity_zone_mode == "brand_only"
        header_logo_class = "state-logo-empty" if (not asset_urls["logo"] or logo_suppressed_by_mode) else "state-logo-show"
        header_layer_class = " ".join(filter(None, [header_logo_class, *behavior.header_policy.css_classes]))
        scenario_is_real = bool(asset_urls.get("scenario_is_real")) and behavior.hero_policy.scenario_enabled
        hero_mode_class = behavior.root_classes[0]
        if behavior.hero_policy.scenario_enabled:
            scenario_state = "state-real" if scenario_is_real else "state-safe-fill"
            scenario_layer_class = (
                f"{scenario_state} state-fit-{behavior.hero_policy.scenario_fit} "
                f"state-anchor-{behavior.hero_policy.scenario_anchor} {hero_mode_class}"
            )
            scenario_shell_class = scenario_state
            scenario_content_class = scenario_layer_class
        else:
            scenario_layer_class = f"state-hidden {hero_mode_class}"
            scenario_shell_class = "state-hidden"
            scenario_content_class = f"state-hidden {hero_mode_class}"
        product_layer_class = (
            f"state-fit-{behavior.hero_policy.product_fit} "
            f"state-anchor-{behavior.hero_policy.product_anchor} {hero_mode_class}"
        )
        product_content_class = product_layer_class
        agent_text_class = "state-show" if behavior.header_policy.agent_pill_visible else "state-hidden"
        bottom_region_class = (
            f"state-show {behavior.bottom_policy.bottom_region_state}"
            if behavior.bottom_policy.bottom_region_rendered
            else "state-hidden"
        )
        title_band_class = "state-show" if behavior.bottom_policy.title_band_rendered else "state-hidden"
        title_content_class = "state-show" if behavior.bottom_policy.title_band_rendered else "state-hidden"
        subtitle_class = "state-show" if behavior.bottom_policy.subtitle_slot_rendered else "state-hidden"
        gallery_region_class = "state-show" if behavior.bottom_policy.gallery_strip_rendered else "state-hidden"
        gallery_items_class = gallery_layer_class
        bottom_tagline_text = ""
        bottom_tagline_class = "state-hidden"
        replacements = {
            "__INLINE_CSS__": css_template,
            "__FONT_FACE_CSS__": font_css,
            "__SAFE_MARGIN__": str(slot_spec.get("safe_margin", spec.safe_margin)),
            "__ROOT_BEHAVIOR_CLASS__": html.escape(behavior.root_class_name()),
            "__BEAUTY_CSS_VARS__": behavior.css_var_style(),
            "__TEMPLATE_ID__": html.escape(spec.template_id),
            "__TEMPLATE_CONTRACT_VERSION__": html.escape(template_contract_version),
            "__SVG_OVERLAY__": "",
            "__HEADER_LAYER_CLASS__": header_layer_class,
            "__LOGO_STYLE__": _slot_style(_header_logo_slot(slot_spec, behavior.header_policy)),
            "__LOGO_URL__": asset_urls["logo"],
            "__BRAND_STYLE__": _slot_style(_header_brand_slot(slot_spec, behavior.header_policy)),
            "__BRAND_TEXT__": html.escape(_apply_char_budget(poster.brand_name, behavior.header_policy.brand_char_budget)),
            "__AGENT_STYLE__": _slot_style(_header_agent_slot(slot_spec, behavior.header_policy)),
            "__AGENT_TEXT__": html.escape(_apply_char_budget(poster.agent_name, behavior.header_policy.agent_char_budget)),
            "__TITLE_STYLE__": _slot_style(slot_spec["slots"]["title"]),
            "__TITLE_TEXT__": html.escape(_apply_char_budget(poster.title, behavior.bottom_policy.title_char_budget)),
            "__SUBTITLE_STYLE__": _slot_style(slot_spec["slots"]["subtitle"]),
            "__SUBTITLE_TEXT__": html.escape(_apply_char_budget(poster.subtitle, behavior.bottom_policy.subtitle_char_budget)),
            "__SUBTITLE_CLASS__": subtitle_class,
            "__SCENARIO_LAYER_CLASS__": scenario_layer_class,
            "__SCENARIO_SHELL_CLASS__": scenario_shell_class,
            "__SCENARIO_CONTENT_CLASS__": scenario_content_class,
            "__AGENT_TEXT_CLASS__": agent_text_class,
            "__SCENARIO_STYLE__": _slot_style(_scenario_slot(slot_spec, behavior.hero_policy)),
            "__SCENARIO_URL__": asset_urls["scenario"],
            "__PRODUCT_LAYER_CLASS__": product_layer_class,
            "__PRODUCT_CONTENT_CLASS__": product_content_class,
            "__PRODUCT_STYLE__": _slot_style(_product_slot(slot_spec, behavior.hero_policy, behavior.product_policy)),
            "__PRODUCT_URL__": asset_urls["product"],
            "__PRODUCT_SECONDARY_CLASS__": (
                "state-show"
                if behavior.product_policy.product_secondary_slot_rendered and asset_urls.get("product_secondary")
                else "state-hidden"
            ),
            "__PRODUCT_SECONDARY_STYLE__": _slot_style(_product_secondary_slot(slot_spec, behavior.product_policy)),
            "__PRODUCT_SECONDARY_URL__": asset_urls.get("product_secondary", ""),
            "__FEATURE_LAYER_CLASS__": feature_layer_class,
            "__BOTTOM_REGION_CLASS__": bottom_region_class,
            "__TITLE_BAND_CLASS__": title_band_class,
            "__TITLE_CONTENT_CLASS__": title_content_class,
            "__GALLERY_REGION_CLASS__": gallery_region_class,
            "__GALLERY_ITEMS_CLASS__": gallery_items_class,
            "__GALLERY_ITEMS__": gallery_markup,
            "__FEATURE_ITEMS__": feature_markup,
            "__BOTTOM_TAGLINE_CLASS__": bottom_tagline_class,
            "__BOTTOM_TAGLINE_STYLE__": _slot_style(slot_spec["slots"]["bottom_tagline"]),
            "__BOTTOM_TAGLINE_TEXT__": html.escape(bottom_tagline_text),
        }
        rendered = html_template
        for key, value in replacements.items():
            rendered = rendered.replace(key, value)
        return rendered

    def _gallery_markup(
        self,
        slot_spec: dict[str, Any],
        gallery_urls: list[str],
        bottom_policy: ResolvedBottomBehavior,
    ) -> tuple[str, str]:
        gallery_slots = list(bottom_policy.layout_metrics.get("gallery_item_layouts", []))
        if not gallery_urls:
            return "", "state-hidden"
        logger.info(
            "poster2.gallery_compose_start count=%d slots=%d",
            len(gallery_urls),
            len(gallery_slots),
        )
        layer_class = "state-show"
        items: list[str] = []
        for idx, gallery_slot in enumerate(gallery_slots[: len(gallery_urls)]):
            url = gallery_urls[idx]
            local_slot = {
                "x": int(gallery_slot["local_x"]),
                "y": int(gallery_slot["local_y"]),
                "w": int(gallery_slot["w"]),
                "h": int(gallery_slot["h"]),
            }
            items.append(
                f'<div class="gallery-item" style="{_slot_style(local_slot)}">'
                f'<img src="{url}" alt="" loading="eager" />'
                "</div>"
            )
        logger.info(
            "poster2.gallery_compose_done items=%d state=%s",
            len(items),
            layer_class,
        )
        return "".join(items), layer_class

    def _feature_markup(
        self,
        anchor_map: dict[str, Any],
        features: tuple[str, ...],
        *,
        feature_policy: ResolvedFeatureBehavior,
        product_policy: ResolvedProductBehavior | None = None,
    ) -> tuple[str, str]:
        callouts = _resolve_feature_callout_map(
            anchor_map,
            features,
            feature_policy=feature_policy,
            product_policy=product_policy,
        )
        if not callouts:
            return "", "state-hidden feature-mode-0"
        mode, mode_spec = resolve_feature_layout_mode(feature_policy.visible_item_count, feature_policy.mode)
        items: list[str] = []
        for callout, feature in callouts:
            anchor_x = int(callout["anchor_x"])
            anchor_y = int(callout["anchor_y"])
            label_box = callout["label_box"]
            label_x = int(label_box["x"])
            connector_left = min(anchor_x, label_x)
            connector_width = max(label_x - anchor_x, 0)
            connector_policy = html.escape(str(callout.get("mode_connector_policy", mode_spec["connector_policy"])))
            items.append(
                f'<div class="feature-callout-connector connector-policy-{connector_policy}" style="left:{connector_left}px;top:{anchor_y}px;width:{connector_width}px;"></div>'
            )
            items.append(
                f'<div class="feature-callout-marker" style="left:{anchor_x}px;top:{anchor_y}px;"></div>'
            )
            items.append(
                (
                    f'<div class="feature-callout feature-mode-box-{mode}" style="{_slot_style(label_box)}">'
                    f"{html.escape(feature)}"
                    "</div>"
                )
            )
        return "".join(items), f"state-show feature-mode-{mode}"

    async def _render_html_to_png(self, html_payload: str, width: int, height: int) -> bytes:
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:  # pragma: no cover - import path depends on runtime
            raise _classify_puppeteer_exception(exc, stage="browser_launch") from exc

        chromium_executable = (os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE") or "").strip()
        launch_kwargs: dict[str, Any] = {
            "headless": True,
            "args": ["--disable-dev-shm-usage", "--font-render-hinting=none"],
        }
        if chromium_executable:
            launch_kwargs["executable_path"] = chromium_executable

        async with async_playwright() as playwright:
            logger.info("poster2.puppeteer: browser_launch_start width=%d height=%d", width, height)
            try:
                browser = await playwright.chromium.launch(**launch_kwargs)
            except Exception as exc:
                raise _classify_puppeteer_exception(exc, stage="browser_launch") from exc
            logger.info("poster2.puppeteer: browser_launch_done")
            try:
                page = await browser.new_page(
                    viewport={"width": width, "height": height},
                    device_scale_factor=1,
                )
                page.set_default_timeout(self._render_timeout_ms)
                page.set_default_navigation_timeout(self._navigation_timeout_ms)
                logger.info("poster2.puppeteer: navigation_start")
                try:
                    await page.set_content(
                        html_payload,
                        wait_until="domcontentloaded",
                        timeout=self._navigation_timeout_ms,
                    )
                    await self._stabilize_page_for_screenshot(page)
                except Exception as exc:
                    raise _classify_puppeteer_exception(exc, stage="navigation") from exc
                logger.info("poster2.puppeteer: navigation_done")
                logger.info("poster2.puppeteer: screenshot_start")
                try:
                    png_bytes = await page.locator("#poster-root").screenshot(
                        type="png",
                        omit_background=True,
                        timeout=self._render_timeout_ms,
                    )
                except Exception as exc:
                    raise _classify_puppeteer_exception(exc, stage="screenshot") from exc
                logger.info("poster2.puppeteer: screenshot_done")
                return png_bytes
            finally:
                await browser.close()

    async def _stabilize_page_for_screenshot(self, page: Any) -> None:
        await page.locator("#poster-root").wait_for(
            state="visible",
            timeout=self._render_timeout_ms,
        )
        try:
            await asyncio.wait_for(
                page.evaluate(
                    "() => document.fonts ? document.fonts.ready.then(() => true) : Promise.resolve(true)"
                ),
                timeout=self._font_ready_grace_ms / 1000,
            )
        except Exception:
            logger.info("poster2.puppeteer: font_ready_grace_elapsed")
        await page.wait_for_function(
            "() => document.readyState === 'interactive' || document.readyState === 'complete'",
            timeout=self._render_timeout_ms,
        )
        await page.wait_for_timeout(32)

    def _font_faces_css(self) -> str:
        font_defs: list[str] = []
        seen: set[str] = set()
        for font_key, family in {
            "brand_bold": "Poster2BrandBold",
            "brand_regular": "Poster2BrandRegular",
            "feature": "Poster2Feature",
            "label": "Poster2Label",
        }.items():
            if family in seen:
                continue
            font_bytes = _font_file_bytes(self._fonts, font_key)
            if not font_bytes:
                continue
            seen.add(family)
            font_defs.append(
                "@font-face {"
                f"font-family: '{family}';"
                f"src: url(data:font/ttf;base64,{base64.b64encode(font_bytes).decode('ascii')}) format('truetype');"
                "font-display: block;"
                "}"
            )
        return "".join(font_defs)


class RendererSelector:
    """Chooses a renderer mode and degrades to Pillow if needed."""

    def __init__(
        self,
        pillow_renderer: LayoutRenderer | None = None,
        puppeteer_renderer: PuppeteerStructuredRenderer | None = None,
        default_mode: RendererMode | None = None,
    ):
        self._pillow = pillow_renderer or LayoutRenderer()
        self._puppeteer = puppeteer_renderer or PuppeteerStructuredRenderer()
        self._default_mode = default_mode or _default_renderer_mode()

    async def render(
        self,
        spec: TemplateSpec,
        poster: PosterSpec,
        assets: ResolvedAssets,
    ) -> ForegroundResult:
        metadata = resolve_template_metadata(spec.template_id)
        routing = resolve_renderer_routing(
            metadata,
            poster.renderer_mode,
            default_mode=self._default_mode,
        )
        target_mode = routing.effective_renderer_mode
        if target_mode == "puppeteer":
            try:
                return await self._puppeteer.render(spec, poster, assets)
            except Exception as exc:
                failure = _extract_puppeteer_failure_info(exc)
                gate = evaluate_fallback_eligibility(metadata, spec, poster, assets)
                if not gate.eligible:
                    raise RendererRoutingError(
                        gate.reason_code or "fallback_not_allowed",
                        gate.detail or "fallback is not allowed for this contract/input state",
                        failure_type=gate.failure_type,
                    ) from exc
                if failure.reason_code not in metadata.allowed_fallback_reason_codes:
                    raise RendererRoutingError(
                        "fallback_reason_not_allowed",
                        (
                            "renderer failure is not eligible for fallback: "
                            f"{failure.reason_code}"
                        ),
                        failure_type="renderer_failure",
                    ) from exc
                if routing.fallback_renderer != "pillow":
                    raise RendererRoutingError(
                        "fallback_renderer_unavailable",
                        f"unsupported fallback renderer configured: {routing.fallback_renderer}",
                        failure_type="renderer_failure",
                    ) from exc
                logger.warning(
                    "poster2: puppeteer fallback stage=%s code=%s exc=%s detail=%s",
                    failure.stage,
                    failure.reason_code,
                    failure.exception_class,
                    failure.detail,
                )
                fallback = self._pillow.render(spec, poster, assets)
                fallback.degraded = True
                fallback.degraded_reason = failure.reason_code
                fallback.fallback_reason_code = failure.reason_code
                fallback.fallback_reason_detail = failure.detail
                fallback.fallback_exception_class = failure.exception_class
                fallback.fallback_stage = failure.stage
                return fallback
        return self._pillow.render(spec, poster, assets)

    def resolve_mode(self, renderer_mode: RendererMode) -> str:
        if renderer_mode == "auto":
            return self._default_mode
        return renderer_mode


def _default_renderer_mode() -> RendererMode:
    raw = (os.getenv("POSTER2_DEFAULT_RENDERER_MODE") or "pillow").strip().lower()
    if raw in {"auto", "pillow", "puppeteer"}:
        return raw  # type: ignore[return-value]
    return "pillow"


def _extract_puppeteer_failure_info(exc: Exception) -> PuppeteerFailureInfo:
    if isinstance(exc, PuppeteerRenderError):
        return exc.failure
    return _build_puppeteer_failure_info(exc, stage="unknown")


def _classify_puppeteer_exception(exc: Exception, *, stage: str) -> PuppeteerRenderError:
    return PuppeteerRenderError(_build_puppeteer_failure_info(exc, stage=stage))


def _build_puppeteer_failure_info(exc: Exception, *, stage: str) -> PuppeteerFailureInfo:
    detail = _truncate_detail(str(exc) or exc.__class__.__name__)
    lowered = detail.lower()
    exception_class = exc.__class__.__name__

    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)) or "timeout" in lowered:
        reason_code = "puppeteer_timeout"
    elif "executable doesn't exist" in lowered or "playwright install" in lowered or "headless_shell" in lowered:
        reason_code = "puppeteer_missing_chromium"
    elif "error while loading shared libraries" in lowered or "libnss3" in lowered or "libatk" in lowered or "libgbm" in lowered:
        reason_code = "puppeteer_missing_system_libs"
    elif stage in {"asset_load", "gallery_render"}:
        reason_code = "puppeteer_asset_load_failed"
    elif stage == "template_render":
        reason_code = "puppeteer_template_render_failed"
    elif stage == "navigation":
        reason_code = "puppeteer_navigation_failed"
    elif stage == "screenshot":
        reason_code = "puppeteer_screenshot_failed"
    elif stage == "browser_launch":
        reason_code = "puppeteer_browser_launch_failed"
    else:
        reason_code = "puppeteer_unknown_error"

    return PuppeteerFailureInfo(
        reason_code=reason_code,
        detail=detail,
        exception_class=exception_class,
        stage=stage,
    )


def _truncate_detail(detail: str, limit: int = 240) -> str:
    compact = " ".join(detail.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _normalized_feature_texts(features: tuple[str, ...] | list[str]) -> list[str]:
    return [item.strip() for item in features if item and item.strip()]


def _resolve_feature_mode(count: int) -> tuple[int, dict[str, int | str]]:
    return resolve_feature_layout_mode(count, "count_driven_callout_stack")


def _resolve_feature_callout_layout(
    callouts: list[FeatureCalloutSpec],
    features: tuple[str, ...] | list[str],
    *,
    feature_policy: ResolvedFeatureBehavior | None = None,
    product_policy: ResolvedProductBehavior | None = None,
    accent_color: str | None = None,
    text_color: str | None = None,
) -> list[tuple[FeatureCalloutSpec, str]]:
    normalized_features = _normalized_feature_texts(features)
    if not callouts or not normalized_features:
        return []

    product_runtime_callouts = _resolve_product_annotation_callout_layout(
        callouts,
        normalized_features,
        product_policy=product_policy,
        accent_color=accent_color,
        text_color=text_color,
    )
    if product_runtime_callouts is not None:
        return product_runtime_callouts

    limited_features = normalized_features[: min(len(normalized_features), len(callouts))]
    count = len(limited_features)
    if feature_policy is None:
        _, mode_spec = resolve_feature_layout_mode(count, "count_driven_callout_stack")
    else:
        mode_spec = {
            "box_h": feature_policy.box_h,
            "gap": feature_policy.gap,
            "connector_policy": feature_policy.connector_policy,
        }
    source = callouts[:count]
    region_top = min(item.label_box.y for item in callouts)
    region_bottom = max(item.label_box.y + item.label_box.h for item in callouts)
    box_h = int(mode_spec["box_h"])
    gap = int(mode_spec["gap"])
    total_height = box_h * count + gap * max(count - 1, 0)
    start_y = region_top + max((region_bottom - region_top - total_height) // 2, 0)
    resolved = []
    for idx, (base, feature_text) in enumerate(zip(source, limited_features)):
        label_y = start_y + idx * (box_h + gap)
        label_box = replace(
            base.label_box,
            y=label_y,
            h=box_h,
            max_lines=2,
        )
        resolved_callout = replace(
            base,
            anchor_y=label_y + box_h // 2,
            anchor_color=accent_color or base.anchor_color,
            leader_color=accent_color or base.leader_color,
            label_box=label_box,
        )
        if text_color:
            resolved_callout = replace(
                resolved_callout,
                label_box=replace(resolved_callout.label_box, color=text_color),
            )
        resolved.append((resolved_callout, feature_text))
    return resolved


def _resolve_feature_callout_map(
    anchor_map: dict[str, Any],
    features: tuple[str, ...] | list[str],
    *,
    feature_policy: ResolvedFeatureBehavior | None = None,
    product_policy: ResolvedProductBehavior | None = None,
) -> list[tuple[dict[str, Any], str]]:
    normalized_features = _normalized_feature_texts(features)
    if not normalized_features:
        return []
    product_runtime_callouts = _resolve_product_annotation_callout_map(
        normalized_features,
        product_policy=product_policy,
    )
    if product_runtime_callouts is not None:
        return product_runtime_callouts
    raw_callouts = anchor_map.get("feature_callouts", [])
    if not raw_callouts:
        return []
    limited_features = normalized_features[: min(len(normalized_features), len(raw_callouts))]
    count = len(limited_features)
    if feature_policy is None:
        _, mode_spec = resolve_feature_layout_mode(count, "count_driven_callout_stack")
    else:
        mode_spec = {
            "box_h": feature_policy.box_h,
            "gap": feature_policy.gap,
            "connector_policy": feature_policy.connector_policy,
        }
    source = raw_callouts[:count]
    region_top = min(int(item["label_box"]["y"]) for item in raw_callouts)
    region_bottom = max(int(item["label_box"]["y"]) + int(item["label_box"]["h"]) for item in raw_callouts)
    box_h = int(mode_spec["box_h"])
    gap = int(mode_spec["gap"])
    total_height = box_h * count + gap * max(count - 1, 0)
    start_y = region_top + max((region_bottom - region_top - total_height) // 2, 0)
    resolved: list[tuple[dict[str, Any], str]] = []
    for idx, (base, feature_text) in enumerate(zip(source, limited_features)):
        label_y = start_y + idx * (box_h + gap)
        label_box = dict(base["label_box"])
        label_box["y"] = label_y
        label_box["h"] = box_h
        callout = dict(base)
        callout["anchor_y"] = label_y + box_h // 2
        callout["mode_connector_policy"] = str(mode_spec["connector_policy"])
        callout["label_box"] = label_box
        resolved.append((callout, feature_text))
    return resolved


def _resolve_product_annotation_callout_layout(
    callouts: list[FeatureCalloutSpec],
    normalized_features: list[str],
    *,
    product_policy: ResolvedProductBehavior | None,
    accent_color: str | None = None,
    text_color: str | None = None,
) -> list[tuple[FeatureCalloutSpec, str]] | None:
    if product_policy is None or product_policy.annotation_mode != "product_anchor_callouts":
        return None
    if product_policy.annotation_text_placement_mode != "template_label_box_fixed":
        return None
    if not product_policy.annotation_items:
        return []
    max_visible = min(product_policy.visible_annotation_count, len(product_policy.annotation_items))
    limited_features = normalized_features[:max_visible]
    resolved: list[tuple[FeatureCalloutSpec, str]] = []
    for base, item, feature_text in zip(callouts[:max_visible], product_policy.annotation_items[:max_visible], limited_features):
        label_bounds = item.get("label_bounds") or {}
        label_box = TextSlotSpec(
            x=int(label_bounds.get("x", 0)),
            y=int(label_bounds.get("y", 0)),
            w=int(label_bounds.get("w", 0)),
            h=int(label_bounds.get("h", 0)),
            font_key=base.label_box.font_key,
            font_size=base.label_box.font_size,
            color=text_color or "#101010",
            align=base.label_box.align,
            max_lines=int(product_policy.line_clamp),
            line_height=base.label_box.line_height,
            auto_shrink=base.label_box.auto_shrink,
            bg_color=base.label_box.bg_color,
            bg_radius=base.label_box.bg_radius,
        )
        resolved_callout = FeatureCalloutSpec(
            label_box=label_box,
            anchor_x=int(item.get("anchor_x", 0)),
            anchor_y=int(item.get("anchor_y", 0)),
            anchor_radius=int(item.get("anchor_radius", 0)),
            anchor_color=str(accent_color or item.get("anchor_color") or "#E8002A"),
            leader_color=str(accent_color or item.get("leader_color") or "#E8002A"),
            leader_width=int(item.get("leader_width", 2)),
        )
        resolved.append((resolved_callout, feature_text))
    return resolved


def _resolve_product_annotation_callout_map(
    normalized_features: list[str],
    *,
    product_policy: ResolvedProductBehavior | None,
) -> list[tuple[dict[str, Any], str]] | None:
    if product_policy is None or product_policy.annotation_mode != "product_anchor_callouts":
        return None
    if product_policy.annotation_text_placement_mode != "template_label_box_fixed":
        return None
    if not product_policy.annotation_items:
        return []
    max_visible = min(product_policy.visible_annotation_count, len(product_policy.annotation_items))
    limited_features = normalized_features[:max_visible]
    resolved: list[tuple[dict[str, Any], str]] = []
    for item, feature_text in zip(product_policy.annotation_items[:max_visible], limited_features):
        label_bounds = item.get("label_bounds") or {}
        resolved.append(
            (
                {
                    "anchor_x": int(item.get("anchor_x", 0)),
                    "anchor_y": int(item.get("anchor_y", 0)),
                    "anchor_radius": int(item.get("anchor_radius", 0)),
                    "anchor_color": str(item.get("anchor_color") or "#E8002A"),
                    "leader_color": str(item.get("leader_color") or "#E8002A"),
                    "leader_width": int(item.get("leader_width", 2)),
                    "mode_connector_policy": str(item.get("connector_policy") or product_policy.annotation_connector_policy),
                    "label_box": {
                        "x": int(label_bounds.get("x", 0)),
                        "y": int(label_bounds.get("y", 0)),
                        "w": int(label_bounds.get("w", 0)),
                        "h": int(label_bounds.get("h", 0)),
                    },
                    "marker_policy": str(item.get("marker_policy") or product_policy.annotation_marker_policy),
                    "text_placement_mode": str(item.get("text_placement_mode") or product_policy.annotation_text_placement_mode),
                },
                feature_text,
            )
        )
    return resolved


def _visible_gallery_item_count(slot_spec: dict[str, Any], gallery_count: int) -> int:
    gallery_slots = slot_spec["slots"]["gallery"][:gallery_count]
    gallery_layer = slot_spec["layers"]["bottom_gallery_items_layer"]
    visible = 0
    for slot in gallery_slots:
        local_x = int(slot["x"]) - int(gallery_layer["x"])
        local_y = int(slot["y"]) - int(gallery_layer["y"])
        if _rectangles_intersect(
            local_x,
            local_y,
            int(slot["w"]),
            int(slot["h"]),
            0,
            0,
            int(gallery_layer["w"]),
            int(gallery_layer["h"]),
        ):
            visible += 1
    return visible


def _gallery_layer_bounds_from_spec(
    spec: TemplateSpec,
    bottom_policy: ResolvedBottomBehavior | None = None,
) -> dict[str, int]:
    if bottom_policy is not None:
        layout = bottom_policy.layout_metrics
        return {
            "x": spec.gallery_slot.x,
            "y": int(layout["gallery_items_top"]),
            "w": spec.gallery_slot.w,
            "h": int(layout["gallery_items_height"]),
        }
    return {
        "x": spec.gallery_slot.x,
        "y": spec.gallery_slot.y,
        "w": spec.gallery_slot.w,
        "h": spec.gallery_slot.h,
    }


def _gallery_slots_from_spec(spec: TemplateSpec, bottom_policy: ResolvedBottomBehavior | None = None) -> list[dict[str, int]]:
    if bottom_policy is not None:
        slots: list[dict[str, int]] = []
        for item in bottom_policy.layout_metrics.get("gallery_item_layouts", []):
            slots.append(
                {
                    "x": int(item["x"]),
                    "y": int(item["y"]),
                    "w": int(item["w"]),
                    "h": int(item["h"]),
                }
            )
        if slots:
            return slots
    slots = []
    for idx in range(spec.gallery_slot.count):
        slots.append(
            {
                "x": spec.gallery_slot.x + idx * (spec.gallery_slot.thumb_w + spec.gallery_slot.gap),
                "y": spec.gallery_slot.y,
                "w": spec.gallery_slot.thumb_w,
                "h": spec.gallery_slot.h,
            }
        )
    return slots


def _annotate_gallery_items_status(
    gallery_items_status: list[dict[str, Any]],
    bottom_policy: ResolvedBottomBehavior,
) -> list[dict[str, Any]]:
    gallery_slots = list(bottom_policy.layout_metrics.get("gallery_item_layouts", []))
    annotated: list[dict[str, Any]] = []
    for idx, status in enumerate(gallery_items_status):
        slot = gallery_slots[idx] if idx < len(gallery_slots) else None
        item = dict(status)
        if slot is None:
            item["visible_in_strip"] = False
            item["local_bounds"] = None
            annotated.append(item)
            continue
        item["visible_in_strip"] = True
        item["local_bounds"] = {
            "x": int(slot["local_x"]),
            "y": int(slot["local_y"]),
            "w": int(slot["w"]),
            "h": int(slot["h"]),
        }
        annotated.append(item)
    return annotated


def _annotate_gallery_items_status_from_spec(
    gallery_items_status: list[dict[str, Any]],
    spec: TemplateSpec,
    bottom_policy: ResolvedBottomBehavior | None = None,
) -> list[dict[str, Any]]:
    gallery_layer = _gallery_layer_bounds_from_spec(spec, bottom_policy)
    gallery_slots = _gallery_slots_from_spec(spec, bottom_policy)
    annotated: list[dict[str, Any]] = []
    for idx, status in enumerate(gallery_items_status):
        slot = gallery_slots[idx] if idx < len(gallery_slots) else None
        item = dict(status)
        if slot is None:
            item["visible_in_strip"] = False
            item["local_bounds"] = None
            annotated.append(item)
            continue
        local_x = int(slot["x"]) - int(gallery_layer["x"])
        local_y = int(slot["y"]) - int(gallery_layer["y"])
        visible = _rectangles_intersect(
            local_x,
            local_y,
            int(slot["w"]),
            int(slot["h"]),
            0,
            0,
            int(gallery_layer["w"]),
            int(gallery_layer["h"]),
        )
        item["visible_in_strip"] = visible
        item["local_bounds"] = {
            "x": local_x,
            "y": local_y,
            "w": int(slot["w"]),
            "h": int(slot["h"]),
        }
        annotated.append(item)
    return annotated


def _build_renderer_layer_render_status(
    *,
    poster: PosterSpec,
    has_logo: bool,
    has_scenario: bool,
    has_product: bool,
    has_product_secondary: bool,
    feature_count: int,
    gallery_valid: int,
    gallery_visible: int,
    gallery_requested: int,
    scenario_source: Optional[str],
    product_source: str,
    logo_source: Optional[str],
    scenario_safe_fill: bool,
    bottom_policy: ResolvedBottomBehavior,
    header_policy: ResolvedHeaderBehavior,
    feature_mode: str,
    product_policy=None,
) -> dict[str, dict[str, Any]]:
    # This is renderer-side structural status derivation from bound inputs and
    # renderer-controlled asset preparation. It is not a post-render pixel check.
    gallery_requested = max(0, min(int(poster.gallery_requested_count or gallery_requested), 4))
    gallery_input_raw = max(0, min(int(poster.gallery_input_count_raw or gallery_requested), 4))
    gallery_input_normalized = max(
        0,
        min(
            int(
                poster.gallery_input_count_normalized
                if poster.gallery_input_count_normalized is not None
                else gallery_valid
            ),
            4,
        ),
    )
    gallery_autofill_applied = bool(poster.gallery_autofill_applied)
    gallery_rendered = bottom_policy.gallery_strip_rendered and gallery_visible > 0
    scenario_rendered = has_scenario or scenario_safe_fill
    logo_suppressed_by_mode = header_policy.identity_zone_mode == "brand_only"
    logo_rendered = has_logo and not logo_suppressed_by_mode
    annotation_active = getattr(product_policy, "annotation_mode", "none") == "product_anchor_callouts"
    product_annotation_visible = min(
        getattr(product_policy, "visible_annotation_count", 0),
        len([item for item in poster.features if item and item.strip()]),
    )
    product_annotation_rendered = annotation_active and product_annotation_visible > 0
    delegated_feature_rendering = annotation_active and feature_mode == "product_anchor_callouts"
    visible_feature_count = 0 if delegated_feature_rendering else feature_count
    return {
        "brand_logo_layer": {
            "rendered": logo_rendered,
            "reason_code": (
                None if logo_rendered
                else ("logo_suppressed_by_header_mode" if logo_suppressed_by_mode else "logo_missing")
            ),
            "source_binding": logo_source,
            "count": 1 if logo_rendered else 0,
            "collapsed": not logo_rendered,
        },
        "brand_text_layer": {
            "rendered": bool(poster.brand_name),
            "reason_code": None if poster.brand_name else "brand_name_empty",
            "source_binding": "request.brand_name",
            "count": 1 if poster.brand_name else 0,
            "collapsed": not bool(poster.brand_name),
        },
        "agent_name_text_layer": {
            "rendered": header_policy.agent_pill_visible,
            "reason_code": (
                None if header_policy.agent_pill_visible
                else ("agent_name_empty" if not poster.agent_name else "suppressed_by_header_mode")
            ),
            "source_binding": "request.agent_name",
            "count": 1 if header_policy.agent_pill_visible else 0,
            "collapsed": not header_policy.agent_pill_visible,
        },
        "scenario_image_layer": {
            "rendered": scenario_rendered,
            "reason_code": None if has_scenario else ("safe_preset_fill" if scenario_safe_fill else "scenario_missing"),
            "source_binding": scenario_source,
            "count": 1 if scenario_rendered else 0,
            "collapsed": not scenario_rendered,
        },
        "product_image_layer": {
            "rendered": has_product,
            "reason_code": None if has_product else "product_image_missing",
            "source_binding": product_source,
            "count": 1 if has_product else 0,
            "collapsed": not has_product,
        },
        "product_secondary_image_layer": {
            "rendered": has_product_secondary and getattr(product_policy, "product_secondary_slot_rendered", False),
            "reason_code": (
                None
                if has_product_secondary and getattr(product_policy, "product_secondary_slot_rendered", False)
                else (
                    "secondary_slot_not_active"
                    if not getattr(product_policy, "product_secondary_slot_rendered", False)
                    else "secondary_image_missing"
                )
            ),
            "source_binding": poster.product_secondary_image.url if poster.product_secondary_image else None,
            "count": 1 if (has_product_secondary and getattr(product_policy, "product_secondary_slot_rendered", False)) else 0,
            "collapsed": not (has_product_secondary and getattr(product_policy, "product_secondary_slot_rendered", False)),
        },
        "product_canvas_shell_layer": {
            "rendered": True,
            "reason_code": None,
            "source_binding": "template_dual_v2.product_canvas_shell",
            "count": 1,
            "collapsed": False,
        },
        "product_annotation_shell_layer": {
            "rendered": product_annotation_rendered,
            "reason_code": (
                None
                if product_annotation_rendered
                else (
                    "annotation_mode_none"
                    if getattr(product_policy, "annotation_mode", "none") == "none"
                    else (
                        "annotation_items_empty"
                        if product_annotation_visible == 0
                        else "annotation_renderer_pending"
                    )
                )
            ),
            "source_binding": getattr(product_policy, "annotation_mode", "none"),
            "count": 1 if product_annotation_rendered else 0,
            "collapsed": not product_annotation_rendered,
        },
        "product_annotation_items_layer": {
            "rendered": product_annotation_rendered,
            "reason_code": (
                None
                if product_annotation_rendered
                else (
                    "annotation_mode_none"
                    if getattr(product_policy, "annotation_mode", "none") == "none"
                    else (
                        "annotation_items_empty"
                        if product_annotation_visible == 0
                        else "annotation_renderer_pending"
                    )
                )
            ),
            "source_binding": "features",
            "count": product_annotation_visible if product_annotation_rendered else 0,
            "collapsed": not product_annotation_rendered,
        },
        "feature_callout_layer": {
            "rendered": visible_feature_count > 0,
            "reason_code": (
                "delegated_to_product_annotation_region"
                if delegated_feature_rendering
                else (None if visible_feature_count > 0 else "features_empty")
            ),
            "source_binding": "features",
            "count": visible_feature_count,
            "collapsed": visible_feature_count == 0,
        },
        "title_layer": {
            "rendered": bottom_policy.title_slot_rendered,
            "reason_code": None if bottom_policy.title_slot_rendered else ("title_empty" if not poster.title else "suppressed_by_bottom_mode"),
            "source_binding": "title",
            "count": 1 if bottom_policy.title_slot_rendered else 0,
            "collapsed": not bottom_policy.title_slot_rendered,
        },
        "subtitle_layer": {
            "rendered": bottom_policy.subtitle_slot_rendered,
            "reason_code": bottom_policy.subtitle_slot_state["reason_code"],
            "source_binding": "subtitle",
            "count": 1 if bottom_policy.subtitle_slot_rendered else 0,
            "collapsed": not bottom_policy.subtitle_slot_rendered,
        },
        "title_band_region_shell_layer": {
            "rendered": bottom_policy.title_band_rendered,
            "reason_code": None if bottom_policy.title_band_rendered else "title_band_collapsed",
            "source_binding": "bottom_mode",
            "count": 1 if bottom_policy.title_band_rendered else 0,
            "collapsed": not bottom_policy.title_band_rendered,
        },
        "gallery_strip_region_shell_layer": {
            "rendered": bottom_policy.gallery_strip_rendered,
            "reason_code": None if bottom_policy.gallery_strip_rendered else ("gallery_hidden_by_bottom_mode" if gallery_requested > 0 else "gallery_empty"),
            "source_binding": "gallery_mode",
            "count": 1 if bottom_policy.gallery_strip_rendered else 0,
            "collapsed": not bottom_policy.gallery_strip_rendered,
        },
        "bottom_gallery_items_layer": {
            "rendered": gallery_rendered,
            "reason_code": None if gallery_rendered else ("gallery_not_visible" if gallery_valid > 0 else "gallery_empty"),
            "source_binding": "gallery_images",
            "count": bottom_policy.visible_item_count,
            "gallery_input_count_raw": gallery_input_raw,
            "gallery_input_count_normalized": gallery_input_normalized,
            "count_requested": gallery_requested,
            "count_valid": gallery_valid,
            "count_visible": bottom_policy.visible_item_count,
            "gallery_autofill_applied": gallery_autofill_applied,
            "collapsed": not gallery_rendered,
        },
    }


def _build_renderer_region_render_status(
    layer_status: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    header_count = sum(
        int(layer_status[layer_name]["count"])
        for layer_name in ("brand_logo_layer", "brand_text_layer", "agent_name_text_layer")
    )
    scenario_count = int(layer_status["scenario_image_layer"]["count"])
    product_count = (
        int(layer_status["product_image_layer"]["count"])
        + int(layer_status["product_secondary_image_layer"]["count"])
        + int(layer_status["product_annotation_items_layer"]["count"])
    )
    feature_count = int(layer_status["feature_callout_layer"]["count"])
    title_count = int(layer_status["title_layer"]["count"])
    subtitle_count = int(layer_status["subtitle_layer"]["count"])
    gallery_count = int(layer_status["bottom_gallery_items_layer"]["count"])
    title_band_region_rendered = int(layer_status["title_band_region_shell_layer"]["count"]) > 0
    gallery_strip_region_rendered = int(layer_status["gallery_strip_region_shell_layer"]["count"]) > 0
    bottom_count = title_count + subtitle_count + gallery_count
    return {
        "header_region": {
            "rendered": header_count > 0,
            "count": header_count,
            "collapsed": header_count == 0,
        },
        "scenario_region": {
            "rendered": scenario_count > 0,
            "count": scenario_count,
            "collapsed": scenario_count == 0,
        },
        "product_region": {
            "rendered": product_count > 0,
            "count": product_count,
            "collapsed": product_count == 0,
        },
        "feature_region": {
            "rendered": feature_count > 0,
            "count": feature_count,
            "collapsed": feature_count == 0,
        },
        "title_band_region": {
            "rendered": title_band_region_rendered,
            "count": title_count + subtitle_count,
            "collapsed": not title_band_region_rendered,
        },
        "gallery_strip_region": {
            "rendered": gallery_strip_region_rendered,
            "count": gallery_count,
            "collapsed": not gallery_strip_region_rendered,
        },
        "bottom_region": {
            "rendered": bottom_count > 0,
            "count": bottom_count,
            "collapsed": bottom_count == 0,
        },
    }


def render_product_material_debug_layer(
    spec: TemplateSpec,
    assets: ResolvedAssets,
    font_registry: FontRegistry | None = None,
) -> ForegroundResult:
    """
    Deterministic debug layer for loaded product/material assets.

    This is used for pilot observability regardless of the foreground engine
    selected for the final structured render.
    """
    renderer = LayoutRenderer(font_registry=font_registry)
    gallery_resolved = min(len(assets.gallery), spec.gallery_slot.count)
    behavior = resolve_template_behavior(
        spec,
        brand_name=None,
        gallery_resolved_count=gallery_resolved,
        gallery_requested_count=gallery_resolved,
        gallery_input_count_normalized=gallery_resolved,
        has_product_secondary_asset=assets.product_secondary is not None,
    )
    canvas = PILImage.new("RGBA", (spec.canvas_w, spec.canvas_h), (0, 0, 0, 0))
    if behavior.hero_policy.scenario_enabled and spec.scenario_slot and assets.scenario:
        renderer._draw_image(canvas, spec.scenario_slot, assets.scenario)
    renderer._draw_product(canvas, _product_image_slot(spec, behavior.hero_policy, behavior.product_policy), assets.product)
    if assets.product_secondary is not None:
        renderer._draw_product(canvas, _product_secondary_image_slot(spec, behavior.product_policy), assets.product_secondary)
    renderer._draw_gallery(
        canvas,
        spec.gallery_slot,
        assets.gallery,
        bottom_policy=behavior.bottom_policy,
        visible_count=behavior.bottom_policy.visible_item_count,
    )
    if spec.logo_slot and assets.logo:
        renderer._draw_image(canvas, spec.logo_slot, assets.logo)
    png_bytes = _to_png(canvas)
    return ForegroundResult(
        image=canvas,
        png_bytes=png_bytes,
        sha256=hashlib.sha256(png_bytes).hexdigest(),
        render_engine_used="debug",
        foreground_renderer="poster2.debug_product_material",
        template_contract_version=spec.contract_version,
    )


def _header_shell_bounds(spec: TemplateSpec, header_policy: ResolvedHeaderBehavior) -> tuple[int, int, int, int]:
    metrics = header_policy.layout_metrics
    return (
        int(metrics["header_banner_left"]),
        int(metrics["header_banner_top"]),
        int(metrics["header_banner_width"]),
        int(metrics["header_banner_height"]),
    )


def _brand_text_slot(spec: TemplateSpec, header_policy: ResolvedHeaderBehavior, *, color: str) -> TextSlotSpec:
    metrics = header_policy.layout_metrics
    return replace(
        spec.brand_name_slot,
        x=int(metrics["brand_slot_x"]),
        y=int(metrics["brand_slot_y"]),
        w=int(metrics["brand_slot_w"]),
        h=int(metrics["brand_slot_h"]),
        color=color,
        max_lines=max(header_policy.brand_line_clamp, 1),
    )


def _agent_text_slot(spec: TemplateSpec, header_policy: ResolvedHeaderBehavior, *, color: str) -> TextSlotSpec:
    metrics = header_policy.layout_metrics
    return replace(
        spec.agent_name_slot,
        x=int(metrics["agent_slot_x"]),
        y=int(metrics["agent_slot_y"]),
        w=int(metrics["agent_slot_w"]),
        h=int(metrics["agent_slot_h"]),
        color=color,
        max_lines=1,
    )


def _scenario_shell_bounds(spec: TemplateSpec, hero_policy) -> tuple[int, int, int, int]:
    metrics = hero_policy.layout_metrics
    return (
        int(metrics["scenario_region_x"]),
        int(metrics["scenario_region_y"]),
        int(metrics["scenario_region_w"]),
        int(metrics["scenario_region_h"]),
    )


def _product_shell_bounds(spec: TemplateSpec, product_policy) -> tuple[int, int, int, int]:
    product_region = product_policy.product_region
    return (
        int(product_region["x"]),
        int(product_region["y"]),
        int(product_region["w"]),
        int(product_region["h"]),
    )


def _scenario_image_slot(spec: TemplateSpec, hero_policy):
    if spec.scenario_slot is None:
        return None
    metrics = hero_policy.layout_metrics
    return replace(
        spec.scenario_slot,
        x=int(metrics["scenario_region_x"]),
        y=int(metrics["scenario_region_y"]),
        w=int(metrics["scenario_region_w"]),
        h=int(metrics["scenario_region_h"]),
        fit=hero_policy.scenario_fit,
        align_x=hero_policy.scenario_anchor if hero_policy.scenario_anchor in {"start", "center", "end"} else "center",
        align_y=hero_policy.scenario_anchor if hero_policy.scenario_anchor in {"start", "center", "end"} else "center",
    )


def _product_image_slot(spec: TemplateSpec, hero_policy, product_policy=None):
    if product_policy is not None:
        primary = product_policy.product_primary_slot
        fit = product_policy.product_primary_image_fit
        if getattr(product_policy, "product_layout_mode", "single_primary") == "primary_secondary_dual":
            return replace(
                spec.product_slot,
                x=int(primary["x"]),
                y=int(primary["y"]),
                w=int(primary["w"]),
                h=int(primary["h"]),
                fit=fit,
                align_x="center",
                align_y="center",
                pad_top=16,
                pad_right=12,
                pad_bottom=8,
                pad_left=12,
            )
        # single_primary: bounds from product_policy, padding from hero_policy metrics
        metrics = hero_policy.layout_metrics
        anchor = hero_policy.product_anchor if hero_policy.product_anchor in {"start", "center", "end"} else "center"
        return replace(
            spec.product_slot,
            x=int(primary["x"]),
            y=int(primary["y"]),
            w=int(primary["w"]),
            h=int(primary["h"]),
            fit=fit,
            align_x="center",
            align_y=anchor,
            pad_top=int(metrics["product_pad_top"]),
            pad_right=int(metrics["product_pad_right"]),
            pad_bottom=int(metrics["product_pad_bottom"]),
            pad_left=int(metrics["product_pad_left"]),
        )
    # No product_policy: legacy hero-only fallback
    metrics = hero_policy.layout_metrics
    anchor = hero_policy.product_anchor if hero_policy.product_anchor in {"start", "center", "end"} else "center"
    return replace(
        spec.product_slot,
        x=int(metrics["product_region_x"]),
        y=int(metrics["product_region_y"]),
        w=int(metrics["product_region_w"]),
        h=int(metrics["product_region_h"]),
        fit=hero_policy.product_fit,
        align_x="center",
        align_y=anchor,
        pad_top=int(metrics["product_pad_top"]),
        pad_right=int(metrics["product_pad_right"]),
        pad_bottom=int(metrics["product_pad_bottom"]),
        pad_left=int(metrics["product_pad_left"]),
    )


def _product_secondary_image_slot(spec: TemplateSpec, product_policy):
    secondary = product_policy.product_secondary_slot
    if secondary is None:
        return replace(spec.product_slot, x=0, y=0, w=0, h=0)
    return replace(
        spec.product_slot,
        x=int(secondary["x"]),
        y=int(secondary["y"]),
        w=int(secondary["w"]),
        h=int(secondary["h"]),
        fit="contain",
        align_x="center",
        align_y="center",
        pad_top=8,
        pad_right=12,
        pad_bottom=10,
        pad_left=12,
    )


def _title_band_shell_bounds(spec: TemplateSpec, bottom_policy: ResolvedBottomBehavior) -> tuple[int, int, int, int]:
    layout = bottom_policy.layout_metrics
    return (
        spec.title_slot.x,
        int(layout["title_band_top"]),
        spec.title_slot.w,
        int(layout["title_band_height"]),
    )


def _gallery_strip_shell_bounds(spec: TemplateSpec, bottom_policy: ResolvedBottomBehavior) -> tuple[int, int, int, int]:
    layout = bottom_policy.layout_metrics
    return (
        int(layout.get("gallery_shell_x", spec.gallery_slot.x)),
        int(layout["gallery_shell_top"]),
        int(layout.get("gallery_shell_w", spec.gallery_slot.w)),
        int(layout["gallery_shell_height"]),
    )


def _bottom_shell_bounds(spec: TemplateSpec, bottom_policy: ResolvedBottomBehavior) -> tuple[int, int, int, int]:
    if not bottom_policy.bottom_region_rendered:
        return spec.gallery_slot.x, int(bottom_policy.layout_metrics["bottom_shell_top"]), spec.gallery_slot.w, 0
    return (
        spec.gallery_slot.x,
        int(bottom_policy.layout_metrics["bottom_shell_top"]),
        spec.gallery_slot.w,
        int(bottom_policy.layout_metrics["bottom_shell_height"]),
    )


def _title_text_slot(spec: TemplateSpec, bottom_policy: ResolvedBottomBehavior, *, color: str) -> TextSlotSpec:
    layout = bottom_policy.layout_metrics
    return replace(
        spec.title_slot,
        y=int(layout["title_slot_y"]),
        h=int(layout["title_slot_height"]),
        color=color,
        max_lines=max(bottom_policy.title_line_clamp, 1),
    )


def _subtitle_text_slot(spec: TemplateSpec, bottom_policy: ResolvedBottomBehavior, *, color: str) -> TextSlotSpec:
    layout = bottom_policy.layout_metrics
    return replace(
        spec.subtitle_slot,
        y=int(layout["subtitle_slot_y"]),
        h=int(layout["subtitle_slot_height"]),
        color=color,
        max_lines=max(bottom_policy.subtitle_line_clamp, 1),
    )


def _pillow_shell_fill(role: str, shell_surface: str, *, accent: str) -> tuple[int, int, int, int]:
    presets: dict[str, dict[str, tuple[int, int, int, int]]] = {
        "glass_light": {
            "header": (255, 250, 248, 238),
            "scenario_safe": (247, 238, 234, 82),
            "scenario_real": (255, 255, 255, 18),
            "product": (255, 248, 246, 240),
            "bottom": (255, 249, 247, 178),
            "title_band": (255, 249, 247, 238),
            "gallery_strip": (255, 249, 247, 182),
        },
        "panel_clean": {
            "header": (255, 255, 255, 246),
            "scenario_safe": (244, 244, 244, 240),
            "scenario_real": (255, 255, 255, 28),
            "product": (252, 252, 252, 248),
            "bottom": (250, 250, 250, 228),
            "title_band": (255, 255, 255, 244),
            "gallery_strip": (255, 255, 255, 214),
        },
        "panel_dark_soft": {
            "header": (43, 40, 46, 232),
            "scenario_safe": (58, 54, 60, 194),
            "scenario_real": (56, 52, 58, 118),
            "product": (49, 46, 52, 232),
            "bottom": (47, 43, 49, 210),
            "title_band": (51, 47, 53, 222),
            "gallery_strip": (46, 43, 49, 194),
        },
        "solid_soft": {
            "header": (255, 252, 250, 250),
            "scenario_safe": (246, 240, 236, 234),
            "scenario_real": (255, 255, 255, 36),
            "product": (255, 251, 248, 250),
            "bottom": (255, 250, 247, 234),
            "title_band": (255, 252, 250, 244),
            "gallery_strip": (255, 250, 247, 208),
        },
    }
    return presets[shell_surface][role]


def _pillow_border(role: str, shell_border: str, *, accent: str) -> tuple[int, int, int, int]:
    accent_rgb = _hex_to_rgb(accent)
    alpha_by_preset = {"soft_line": 26, "clean_frame": 52, "none": 0}
    if role in {"hero", "gallery"} and shell_border != "none":
        white_alpha = {"soft_line": 60, "clean_frame": 88, "none": 0}[shell_border]
        return (255, 255, 255, white_alpha)
    return (*accent_rgb, alpha_by_preset[shell_border])


def _pillow_shadow(shell_shadow: str) -> tuple[int, int, int, int, int] | None:
    if shell_shadow == "none":
        return None
    if shell_shadow == "soft":
        return (0, 12, 12, 0, 32)
    if shell_shadow == "medium":
        return (0, 14, 16, 0, 44)
    raise ValueError(f"Unsupported shell_shadow: {shell_shadow}")


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = color.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _font_file_bytes(font_registry: FontRegistry, font_key: str) -> bytes:
    filename = {
        "brand_bold": "NotoSansSC-SemiBold.ttf",
        "brand_regular": "NotoSansSC-Regular.ttf",
        "feature": "NotoSansSC-Regular.ttf",
        "label": "NotoSansSC-Regular.ttf",
    }.get(font_key, "NotoSansSC-Regular.ttf")
    path = font_registry._dir / filename  # type: ignore[attr-defined]
    if not path.exists():
        return b""
    return path.read_bytes()


def _slot_style(slot: dict[str, Any]) -> str:
    radius = slot.get("radius", 0)
    fit = slot.get("fit")
    extra = []
    if fit == "contain":
        extra.append("object-fit:contain;")
    elif fit == "cover":
        extra.append("object-fit:cover;")
    elif fit == "fill":
        extra.append("object-fit:fill;")
    if radius:
        extra.append(f"border-radius:{radius}px;")
        extra.append("overflow:hidden;")
    return (
        f"left:{slot['x']}px;top:{slot['y']}px;width:{slot['w']}px;height:{slot['h']}px;"
        + "".join(extra)
    )


def _header_logo_slot(slot_spec: dict[str, Any], header_policy: ResolvedHeaderBehavior) -> dict[str, Any]:
    slot = dict(slot_spec["slots"]["logo"])
    metrics = header_policy.layout_metrics
    slot["w"] = int(metrics["header_logo_width"])
    slot["h"] = int(metrics["header_logo_height"])
    return slot


def _header_brand_slot(slot_spec: dict[str, Any], header_policy: ResolvedHeaderBehavior) -> dict[str, Any]:
    slot = dict(slot_spec["slots"]["brand_name"])
    metrics = header_policy.layout_metrics
    slot.update(
        {
            "x": int(metrics["brand_slot_x"]),
            "y": int(metrics["brand_slot_y"]),
            "w": int(metrics["brand_slot_w"]),
            "h": int(metrics["brand_slot_h"]),
        }
    )
    return slot


def _header_agent_slot(slot_spec: dict[str, Any], header_policy: ResolvedHeaderBehavior) -> dict[str, Any]:
    slot = dict(slot_spec["slots"]["agent_name"])
    metrics = header_policy.layout_metrics
    slot.update(
        {
            "x": int(metrics["agent_slot_x"]),
            "y": int(metrics["agent_slot_y"]),
            "w": int(metrics["agent_slot_w"]),
            "h": int(metrics["agent_slot_h"]),
        }
    )
    return slot


def _scenario_slot(slot_spec: dict[str, Any], hero_policy) -> dict[str, Any]:
    slot = dict(slot_spec["slots"]["scenario"])
    metrics = hero_policy.layout_metrics
    slot.update(
        {
            "x": int(metrics["scenario_region_x"]),
            "y": int(metrics["scenario_region_y"]),
            "w": int(metrics["scenario_region_w"]),
            "h": int(metrics["scenario_region_h"]),
            "fit": hero_policy.scenario_fit,
        }
    )
    return slot


def _product_slot(slot_spec: dict[str, Any], hero_policy, product_policy=None) -> dict[str, Any]:
    slot = dict(slot_spec["slots"]["product"])
    # Use product_primary_slot geometry when product_policy is available.
    # For single_primary: primary_slot == full product_region — backward compatible.
    # For primary_secondary_dual: primary_slot is upper portion (h:310 not h:520).
    if product_policy is not None:
        primary = product_policy.product_primary_slot
        slot.update(
            {
                "x": int(primary["x"]),
                "y": int(primary["y"]),
                "w": int(primary["w"]),
                "h": int(primary["h"]),
                "fit": hero_policy.product_fit,
                "pad_top": 16,
                "pad_right": 12,
                "pad_bottom": 8,
                "pad_left": 12,
            }
        )
    else:
        metrics = hero_policy.layout_metrics
        slot.update(
            {
                "x": int(metrics["product_region_x"]),
                "y": int(metrics["product_region_y"]),
                "w": int(metrics["product_region_w"]),
                "h": int(metrics["product_region_h"]),
                "fit": hero_policy.product_fit,
                "pad_top": int(metrics["product_pad_top"]),
                "pad_right": int(metrics["product_pad_right"]),
                "pad_bottom": int(metrics["product_pad_bottom"]),
                "pad_left": int(metrics["product_pad_left"]),
            }
        )
    return slot


def _product_secondary_slot(slot_spec: dict[str, Any], product_policy) -> dict[str, Any]:
    """Build style dict for the secondary product slot from contract geometry."""
    secondary = product_policy.product_secondary_slot
    if secondary is None:
        return {"x": 0, "y": 0, "w": 0, "h": 0}
    slot = dict(slot_spec["slots"]["product"])
    slot.update(
        {
            "x": int(secondary["x"]),
            "y": int(secondary["y"]),
            "w": int(secondary["w"]),
            "h": int(secondary["h"]),
            "fit": "contain",
            "pad_top": 8,
            "pad_right": 12,
            "pad_bottom": 10,
            "pad_left": 12,
        }
    )
    return slot


def _image_to_data_url(img: Optional[PILImage.Image]) -> str:
    if img is None:
        img = PILImage.new("RGBA", (1, 1), (0, 0, 0, 0))
    buf = BytesIO()
    img.convert("RGBA").save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _prepare_gallery_urls(
    gallery: list[PILImage.Image],
    gallery_status: list[dict],
    slot_spec: dict[str, Any],
) -> tuple[list[str], list[dict]]:
    requested = gallery_status[:4]
    if not requested:
        return [], []
    slots = slot_spec.get("slots", {}).get("gallery", [])
    slot = slots[0] if slots else {"w": 196, "h": 56, "fit": "cover"}
    w = int(slot.get("w", 0)) or 196
    h = int(slot.get("h", 0)) or 56
    fit = slot.get("fit", "cover")
    urls: list[str] = []
    status_out: list[dict] = []
    img_idx = 0
    for item in requested:
        status = {
            "index": item.get("index"),
            "url": item.get("url"),
            "resolved": bool(item.get("resolved")),
            "prepared": False,
            "rendered": False,
            "error_code": item.get("error_code"),
        }
        if status["resolved"]:
            if img_idx < len(gallery):
                try:
                    img = _fit_image(gallery[img_idx], w, h, fit)
                    img_idx += 1
                    url = _image_to_data_url(img)
                    urls.append(url)
                    status["prepared"] = True
                    status["rendered"] = True
                except Exception:
                    status["error_code"] = "gallery_item_prepare_failed"
            else:
                status["error_code"] = "gallery_item_missing"
        status_out.append(status)
    return urls, status_out


def _safe_preset_scenario_data_url() -> str:
    img = PILImage.new("RGBA", (288, 520), (245, 236, 232, 255))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([18, 18, 270, 502], radius=24, outline=(232, 0, 42, 46), width=2)
    draw.rectangle([38, 58, 250, 442], fill=(255, 255, 255, 80))
    draw.rectangle([58, 96, 230, 128], fill=(232, 0, 42, 24))
    draw.rectangle([58, 146, 210, 176], fill=(232, 0, 42, 18))
    draw.rectangle([58, 196, 224, 226], fill=(232, 0, 42, 14))
    return _image_to_data_url(img)


def _now() -> int:
    return time.monotonic_ns()


def _elapsed(t0: int) -> int:
    return (time.monotonic_ns() - t0) // 1_000_000


def _draw_pill_bg(draw: ImageDraw.ImageDraw, slot: TextSlotSpec) -> None:
    r = min(slot.bg_radius, slot.h // 2)
    draw.rounded_rectangle(
        [slot.x, slot.y, slot.x + slot.w, slot.y + slot.h],
        radius=r,
        fill=slot.bg_color,
    )


def _fit_image(img: PILImage.Image, w: int, h: int, fit: str) -> PILImage.Image:
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
    return img.resize((w, h), PILImage.LANCZOS)


def _add_drop_shadow(
    img: PILImage.Image,
    offset: tuple[int, int] = (4, 6),
    blur: int = 12,
    shadow_alpha: int = 100,
) -> PILImage.Image:
    result = PILImage.new("RGBA", img.size, (0, 0, 0, 0))
    if img.mode == "RGBA":
        _, _, _, a = img.split()
        shadow_mask = PILImage.new("RGBA", img.size, (0, 0, 0, 0))
        shadow_mask.paste(PILImage.new("RGBA", img.size, (0, 0, 0, shadow_alpha)), mask=a)
    else:
        shadow_mask = PILImage.new("RGBA", img.size, (0, 0, 0, shadow_alpha))
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
    sample_bbox = draw.textbbox((0, 0), "A", font=font)
    line_h = sample_bbox[3] - sample_bbox[1]
    spacing = int(line_h * (slot.line_height - 1.0))
    block_h = line_h * len(lines) + spacing * (len(lines) - 1)
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


def _apply_char_budget(text: str, budget: int) -> str:
    """Hard-truncate text to char budget. budget=0 means no text (caller should not render)."""
    if not text or budget <= 0:
        return text
    if len(text) <= budget:
        return text
    return text[:budget]


def _to_png(img: PILImage.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()
