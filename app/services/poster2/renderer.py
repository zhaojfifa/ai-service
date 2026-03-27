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
            gallery_requested_count=len(poster.gallery_images),
            gallery_resolved_count=min(len(assets.gallery), spec.gallery_slot.count),
            bottom_mode=poster.bottom_mode,
            gallery_mode=poster.gallery_mode,
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
            self._draw_image(canvas, spec.scenario_slot, assets.scenario)
        self._draw_product(canvas, spec.product_slot, assets.product)
        self._draw_gallery(
            canvas,
            spec.gallery_slot,
            assets.gallery,
            bottom_policy=behavior.bottom_policy,
            visible_count=behavior.bottom_policy.visible_item_count if behavior.bottom_policy.gallery_strip_rendered else 0,
        )
        if spec.logo_slot and assets.logo:
            self._draw_image(canvas, spec.logo_slot, assets.logo)
        layer_timings["product_material_layer_ms"] = _elapsed(t0)

        t1 = _now()
        resolved_callouts = _resolve_feature_callout_layout(
            spec.feature_callouts,
            poster.features,
            feature_policy=behavior.feature_policy,
            accent_color=behavior.accent_color,
            text_color=behavior.text_colors["feature"],
        )
        self._draw_feature_callout_structure(canvas, resolved_callouts)
        layer_timings["foreground_structure_layer_ms"] = _elapsed(t1)

        t2 = _now()
        self._draw_feature_callout_labels(canvas, resolved_callouts)
        self._draw_text(
            canvas,
            replace(spec.brand_name_slot, color=behavior.text_colors["brand"]),
            poster.brand_name,
            draw_background=False,
        )
        self._draw_text(
            canvas,
            replace(spec.agent_name_slot, color=behavior.text_colors["agent"]),
            poster.agent_name,
            draw_background=False,
        )
        if behavior.bottom_policy.title_slot_rendered:
            self._draw_text(
                canvas,
                _title_text_slot(spec, behavior.bottom_policy, color=behavior.text_colors["title"]),
                poster.title,
                draw_background=False,
            )
        if behavior.bottom_policy.subtitle_slot_rendered:
            self._draw_text(
                canvas,
                _subtitle_text_slot(spec, behavior.bottom_policy, color=behavior.text_colors["subtitle"]),
                poster.subtitle,
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
        header_box = _header_shell_bounds(spec)
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
                (spec.scenario_slot.x, spec.scenario_slot.y, spec.scenario_slot.w, spec.scenario_slot.h),
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
            (spec.product_slot.x, spec.product_slot.y, spec.product_slot.w, spec.product_slot.h),
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
                radius=20,
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
        for i, img in enumerate(images[: min(strip.count, visible_count)]):
            slot_layout = gallery_item_layouts[i] if i < len(gallery_item_layouts) else None
            if slot_layout is None:
                x = strip.x + i * (strip.thumb_w + strip.gap)
                y = strip.y
                w = strip.thumb_w
                h = strip.h
            else:
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
                radius=strip.thumb_radius,
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
            gallery_requested_count=len(poster.gallery_images),
            gallery_resolved_count=min(len(assets.gallery), spec.gallery_slot.count),
            bottom_mode=poster.bottom_mode,
            gallery_mode=poster.gallery_mode,
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
            gallery_requested_count=len(poster.gallery_images),
            gallery_resolved_count=len(asset_urls.get("gallery") or []),
            bottom_mode=poster.bottom_mode,
            gallery_mode=poster.gallery_mode,
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
        )
        header_layer_class = "state-logo-empty" if not asset_urls["logo"] else "state-logo-show"
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
        agent_text_class = "state-show" if (poster.agent_name or "").strip() else "state-hidden"
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
            "__LOGO_STYLE__": _slot_style(slot_spec["slots"]["logo"]),
            "__LOGO_URL__": asset_urls["logo"],
            "__BRAND_STYLE__": _slot_style(slot_spec["slots"]["brand_name"]),
            "__BRAND_TEXT__": html.escape(poster.brand_name),
            "__AGENT_STYLE__": _slot_style(slot_spec["slots"]["agent_name"]),
            "__AGENT_TEXT__": html.escape(poster.agent_name),
            "__TITLE_STYLE__": _slot_style(slot_spec["slots"]["title"]),
            "__TITLE_TEXT__": html.escape(poster.title),
            "__SUBTITLE_STYLE__": _slot_style(slot_spec["slots"]["subtitle"]),
            "__SUBTITLE_TEXT__": html.escape(poster.subtitle),
            "__SUBTITLE_CLASS__": subtitle_class,
            "__SCENARIO_LAYER_CLASS__": scenario_layer_class,
            "__SCENARIO_SHELL_CLASS__": scenario_shell_class,
            "__SCENARIO_CONTENT_CLASS__": scenario_content_class,
            "__AGENT_TEXT_CLASS__": agent_text_class,
            "__SCENARIO_STYLE__": _slot_style(slot_spec["slots"]["scenario"]),
            "__SCENARIO_URL__": asset_urls["scenario"],
            "__PRODUCT_LAYER_CLASS__": product_layer_class,
            "__PRODUCT_CONTENT_CLASS__": product_content_class,
            "__PRODUCT_STYLE__": _slot_style(slot_spec["slots"]["product"]),
            "__PRODUCT_URL__": asset_urls["product"],
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
    ) -> tuple[str, str]:
        callouts = _resolve_feature_callout_map(anchor_map, features, feature_policy=feature_policy)
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
            items.append(
                f'<div class="feature-callout-connector connector-policy-{html.escape(str(mode_spec["connector_policy"]))}" style="left:{connector_left}px;top:{anchor_y}px;width:{connector_width}px;"></div>'
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
    accent_color: str | None = None,
    text_color: str | None = None,
) -> list[tuple[FeatureCalloutSpec, str]]:
    normalized_features = _normalized_feature_texts(features)
    if not callouts or not normalized_features:
        return []
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
    first = source[0]
    region_top = min(item.label_box.y for item in callouts)
    region_bottom = max(item.label_box.y + item.label_box.h for item in callouts)
    box_h = int(mode_spec["box_h"])
    gap = int(mode_spec["gap"])
    total_height = box_h * count + gap * max(count - 1, 0)
    start_y = region_top + max((region_bottom - region_top - total_height) // 2, 0)
    resolved: list[tuple[FeatureCalloutSpec, str]] = []
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
) -> list[tuple[dict[str, Any], str]]:
    raw_callouts = anchor_map.get("feature_callouts", [])
    if not raw_callouts:
        return []
    normalized_features = _normalized_feature_texts(features)
    if not normalized_features:
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
    feature_count: int,
    gallery_valid: int,
    gallery_visible: int,
    gallery_requested: int,
    scenario_source: Optional[str],
    product_source: str,
    logo_source: Optional[str],
    scenario_safe_fill: bool,
    bottom_policy: ResolvedBottomBehavior,
) -> dict[str, dict[str, Any]]:
    # This is renderer-side structural status derivation from bound inputs and
    # renderer-controlled asset preparation. It is not a post-render pixel check.
    gallery_rendered = bottom_policy.gallery_strip_rendered and gallery_visible > 0
    scenario_rendered = has_scenario or scenario_safe_fill
    return {
        "brand_logo_layer": {
            "rendered": has_logo,
            "reason_code": None if has_logo else "logo_missing",
            "source_binding": logo_source,
            "count": 1 if has_logo else 0,
            "collapsed": not has_logo,
        },
        "brand_text_layer": {
            "rendered": bool(poster.brand_name),
            "reason_code": None if poster.brand_name else "brand_name_empty",
            "source_binding": "brand_name",
            "count": 1 if poster.brand_name else 0,
            "collapsed": not bool(poster.brand_name),
        },
        "agent_name_text_layer": {
            "rendered": bool(poster.agent_name),
            "reason_code": None if poster.agent_name else "agent_name_empty",
            "source_binding": "agent_name",
            "count": 1 if poster.agent_name else 0,
            "collapsed": not bool(poster.agent_name),
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
        "feature_callout_layer": {
            "rendered": feature_count > 0,
            "reason_code": None if feature_count > 0 else "features_empty",
            "source_binding": "features",
            "count": feature_count,
            "collapsed": feature_count == 0,
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
            "count_requested": gallery_requested,
            "count_valid": gallery_valid,
            "count_visible": bottom_policy.visible_item_count,
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
    product_count = int(layer_status["product_image_layer"]["count"])
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
    behavior = resolve_template_behavior(spec)
    canvas = PILImage.new("RGBA", (spec.canvas_w, spec.canvas_h), (0, 0, 0, 0))
    if behavior.hero_policy.scenario_enabled and spec.scenario_slot and assets.scenario:
        renderer._draw_image(canvas, spec.scenario_slot, assets.scenario)
    renderer._draw_product(canvas, spec.product_slot, assets.product)
    renderer._draw_gallery(
        canvas,
        spec.gallery_slot,
        assets.gallery,
        bottom_policy=behavior.bottom_policy,
        visible_count=min(len(assets.gallery), spec.gallery_slot.count),
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


def _header_shell_bounds(spec: TemplateSpec) -> tuple[int, int, int, int]:
    left = min(spec.logo_slot.x, spec.brand_name_slot.x, spec.agent_name_slot.x) - 32
    top = min(spec.logo_slot.y, spec.brand_name_slot.y, spec.agent_name_slot.y) - 18
    right = max(
        spec.logo_slot.x + spec.logo_slot.w,
        spec.brand_name_slot.x + spec.brand_name_slot.w,
        spec.agent_name_slot.x + spec.agent_name_slot.w,
    ) + 40
    bottom = max(
        spec.logo_slot.y + spec.logo_slot.h,
        spec.brand_name_slot.y + spec.brand_name_slot.h,
        spec.agent_name_slot.y + spec.agent_name_slot.h,
    ) + 22
    return left, top, right - left, bottom - top


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
        spec.gallery_slot.x,
        int(layout["gallery_shell_top"]),
        spec.gallery_slot.w,
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
            "bottom": (255, 249, 247, 156),
            "title_band": (255, 249, 247, 224),
            "gallery_strip": (255, 249, 247, 168),
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
    alpha_by_preset = {"soft_line": 20, "clean_frame": 52, "none": 0}
    if role in {"hero", "gallery"} and shell_border != "none":
        white_alpha = {"soft_line": 60, "clean_frame": 88, "none": 0}[shell_border]
        return (255, 255, 255, white_alpha)
    return (*accent_rgb, alpha_by_preset[shell_border])


def _pillow_shadow(shell_shadow: str) -> tuple[int, int, int, int, int] | None:
    if shell_shadow == "none":
        return None
    if shell_shadow == "soft":
        return (0, 10, 10, 0, 26)
    if shell_shadow == "medium":
        return (0, 12, 14, 0, 38)
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


def _to_png(img: PILImage.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()
