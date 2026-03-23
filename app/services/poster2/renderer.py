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
from dataclasses import dataclass, field
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
        canvas = PILImage.new("RGBA", (spec.canvas_w, spec.canvas_h), (0, 0, 0, 0))
        layer_timings: dict[str, int] = {}

        t0 = _now()
        if spec.scenario_slot and assets.scenario:
            self._draw_image(canvas, spec.scenario_slot, assets.scenario)
        self._draw_product(canvas, spec.product_slot, assets.product)
        self._draw_gallery(canvas, spec.gallery_slot, assets.gallery)
        if spec.logo_slot and assets.logo:
            self._draw_image(canvas, spec.logo_slot, assets.logo)
        layer_timings["product_material_layer_ms"] = _elapsed(t0)

        t1 = _now()
        self._draw_feature_callout_structure(canvas, spec.feature_callouts, poster.features)
        if spec.agent_name_slot.bg_color:
            self._draw_slot_background(canvas, spec.agent_name_slot)
        layer_timings["foreground_structure_layer_ms"] = _elapsed(t1)

        t2 = _now()
        self._draw_feature_callout_labels(canvas, spec.feature_callouts, poster.features)
        self._draw_text(canvas, spec.brand_name_slot, poster.brand_name, draw_background=False)
        self._draw_text(canvas, spec.agent_name_slot, poster.agent_name, draw_background=False)
        self._draw_text(canvas, spec.title_slot, poster.title, draw_background=False)
        self._draw_text(canvas, spec.subtitle_slot, poster.subtitle, draw_background=False)
        layer_timings["text_layer_ms"] = _elapsed(t2)

        png_bytes = _to_png(canvas)
        return ForegroundResult(
            image=canvas,
            png_bytes=png_bytes,
            sha256=hashlib.sha256(png_bytes).hexdigest(),
            render_engine_used=self.RENDER_ENGINE,
            foreground_renderer=self.RENDERER_NAME,
            template_contract_version=spec.contract_version,
            layer_timings_ms=layer_timings,
        )

    def _draw_feature_callout_structure(
        self,
        canvas: PILImage.Image,
        callouts: list[FeatureCalloutSpec],
        features: tuple[str, ...],
    ) -> None:
        draw = ImageDraw.Draw(canvas)
        for i, callout in enumerate(callouts):
            text = features[i] if i < len(features) else ""
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
        callouts: list[FeatureCalloutSpec],
        features: tuple[str, ...],
    ) -> None:
        for i, callout in enumerate(callouts):
            text = features[i] if i < len(features) else ""
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
        fitted = _fit_image(img, slot.w, slot.h, slot.fit)
        if slot.shadow:
            fitted = _add_drop_shadow(fitted)
        if slot.radius > 0:
            fitted = _apply_radius(fitted, slot.radius)
        ox = slot.x + (slot.w - fitted.width) // 2
        oy = slot.y + (slot.h - fitted.height) // 2
        canvas.alpha_composite(fitted.convert("RGBA"), (ox, oy))

    def _draw_product(self, canvas: PILImage.Image, slot: ImageSlotSpec, img: PILImage.Image) -> None:
        self._draw_image(canvas, slot, img.convert("RGBA"))

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

    def __init__(self, templates_dir: Path | None = None, font_registry: FontRegistry | None = None):
        self._templates_dir = templates_dir or _HTML_TEMPLATES_DIR
        self._fonts = font_registry or FontRegistry()

    async def render(
        self,
        spec: TemplateSpec,
        poster: PosterSpec,
        assets: ResolvedAssets,
    ) -> ForegroundResult:
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
            asset_urls = {
                "logo": _image_to_data_url(assets.logo) if assets.logo else "",
                "scenario": _image_to_data_url(assets.scenario) if assets.scenario else "",
                "product": _image_to_data_url(assets.product),
                "gallery": [_image_to_data_url(img) for img in assets.gallery[:4]],
            }
        except Exception as exc:
            raise _classify_puppeteer_exception(exc, stage="asset_load") from exc
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
            )
        except Exception as exc:
            raise _classify_puppeteer_exception(exc, stage="template_render") from exc
        layer_timings["text_layer_ms"] = _elapsed(t2)

        png_bytes = await self._render_html_to_png(html_payload, spec.canvas_w, spec.canvas_h)
        image = PILImage.open(BytesIO(png_bytes)).convert("RGBA")
        return ForegroundResult(
            image=image,
            png_bytes=png_bytes,
            sha256=hashlib.sha256(png_bytes).hexdigest(),
            render_engine_used=self.RENDER_ENGINE,
            foreground_renderer=self.RENDERER_NAME,
            template_contract_version=str(slot_spec.get("template_contract_version", spec.contract_version)),
            layer_timings_ms=layer_timings,
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
    ) -> str:
        template_contract_version = str(slot_spec.get("template_contract_version", spec.contract_version))
        font_css = self._font_faces_css()
        gallery_markup, gallery_layer_class = self._gallery_markup(slot_spec, asset_urls["gallery"])
        feature_markup = self._feature_markup(anchor_map, poster.features)
        header_layer_class = "state-logo-empty" if not asset_urls["logo"] else "state-logo-show"
        scenario_layer_class = "state-safe-empty" if not asset_urls["scenario"] else "state-show"
        replacements = {
            "__INLINE_CSS__": css_template,
            "__FONT_FACE_CSS__": font_css,
            "__SAFE_MARGIN__": str(slot_spec.get("safe_margin", spec.safe_margin)),
            "__TEMPLATE_ID__": html.escape(spec.template_id),
            "__TEMPLATE_CONTRACT_VERSION__": html.escape(template_contract_version),
            "__SVG_OVERLAY__": svg_overlay,
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
            "__SCENARIO_LAYER_CLASS__": scenario_layer_class,
            "__SCENARIO_STYLE__": _slot_style(slot_spec["slots"]["scenario"]),
            "__SCENARIO_URL__": asset_urls["scenario"],
            "__PRODUCT_STYLE__": _slot_style(slot_spec["slots"]["product"]),
            "__PRODUCT_URL__": asset_urls["product"],
            "__GALLERY_LAYER_CLASS__": gallery_layer_class,
            "__GALLERY_ITEMS__": gallery_markup,
            "__FEATURE_ITEMS__": feature_markup,
        }
        rendered = html_template
        for key, value in replacements.items():
            rendered = rendered.replace(key, value)
        return rendered

    def _gallery_markup(self, slot_spec: dict[str, Any], gallery_urls: list[str]) -> tuple[str, str]:
        gallery_slots = slot_spec["slots"]["gallery"]
        if not gallery_urls:
            return "", "state-hidden"
        layer_class = "state-show" if len(gallery_urls) >= len(gallery_slots) else "state-fallback-fill"
        filled_urls = [gallery_urls[idx % len(gallery_urls)] for idx in range(len(gallery_slots))]
        items: list[str] = []
        for idx, gallery_slot in enumerate(gallery_slots):
            url = filled_urls[idx]
            items.append(
                f'<div class="gallery-item" style="{_slot_style(gallery_slot)}">'
                f'<img src="{url}" alt="" loading="eager" />'
                "</div>"
            )
        return "".join(items), layer_class

    def _feature_markup(self, anchor_map: dict[str, Any], features: tuple[str, ...]) -> str:
        items: list[str] = []
        for idx, feature in enumerate(features[: len(anchor_map.get("feature_callouts", []))]):
            callout = anchor_map["feature_callouts"][idx]
            items.append(
                (
                    f'<div class="feature-callout" style="{_slot_style(callout["label_box"])}">'
                    f"{html.escape(feature)}"
                    "</div>"
                )
            )
        return "".join(items)

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
                logger.info("poster2.puppeteer: navigation_start")
                try:
                    await page.set_content(html_payload, wait_until="load")
                except Exception as exc:
                    raise _classify_puppeteer_exception(exc, stage="navigation") from exc
                logger.info("poster2.puppeteer: navigation_done")
                logger.info("poster2.puppeteer: screenshot_start")
                try:
                    png_bytes = await page.locator("#poster-root").screenshot(type="png", omit_background=True)
                except Exception as exc:
                    raise _classify_puppeteer_exception(exc, stage="screenshot") from exc
                logger.info("poster2.puppeteer: screenshot_done")
                return png_bytes
            finally:
                await browser.close()

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
        requested_mode = poster.renderer_mode
        target_mode = self.resolve_mode(requested_mode)
        if target_mode == "puppeteer":
            try:
                return await self._puppeteer.render(spec, poster, assets)
            except Exception as exc:
                failure = _extract_puppeteer_failure_info(exc)
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
    elif stage == "asset_load":
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
    canvas = PILImage.new("RGBA", (spec.canvas_w, spec.canvas_h), (0, 0, 0, 0))
    if spec.scenario_slot and assets.scenario:
        renderer._draw_image(canvas, spec.scenario_slot, assets.scenario)
    renderer._draw_product(canvas, spec.product_slot, assets.product)
    renderer._draw_gallery(canvas, spec.gallery_slot, assets.gallery)
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
