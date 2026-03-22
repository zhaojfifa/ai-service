"""
PosterPipeline — orchestrates the three-layer poster generation.

Execution order (parallelised where possible):
  [background generation + asset loading] → foreground render → compose → store

Returns a RenderManifest with full provenance for every output.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from PIL import Image as PILImage

from .asset_loader import AssetLoader
from .background import FireflyBackgroundService, make_background_service
from .composer import Composer
from .contracts import PosterSpec, RenderManifest, TemplateSpec
from .font_registry import FontRegistry
from .renderer import LayoutRenderer, RendererSelector

logger = logging.getLogger("ai-service.poster2")

ENGINE_VERSION = "2.0.0"

_SPECS_DIR = Path(__file__).resolve().parents[3] / "app" / "templates" / "specs"


def load_template(template_id: str) -> TemplateSpec:
    """Load a TemplateSpec JSON from app/templates/specs/<template_id>.json."""
    path = _SPECS_DIR / f"{template_id}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"TemplateSpec not found: {path}. "
            f"Available specs: {[p.stem for p in _SPECS_DIR.glob('*.json')]}"
        )
    return TemplateSpec.from_json(path)


class PosterPipeline:
    """
    Stateless orchestrator — instantiate once at app startup and reuse.
    Each call to .run() is fully independent.
    """

    def __init__(
        self,
        background_svc: Optional[FireflyBackgroundService] = None,
        renderer: Optional[object] = None,
        composer: Optional[Composer] = None,
        asset_loader: Optional[AssetLoader] = None,
        put_bytes_fn=None,  # injectable for testing; defaults to r2_client.put_bytes
    ):
        self._bg = background_svc or make_background_service()
        if isinstance(renderer, RendererSelector):
            self._renderer = renderer
        elif isinstance(renderer, LayoutRenderer):
            self._renderer = RendererSelector(pillow_renderer=renderer)
        elif renderer is None:
            self._renderer = RendererSelector(
                pillow_renderer=LayoutRenderer(FontRegistry())
            )
        else:
            self._renderer = renderer
        self._composer = composer or Composer()
        self._loader = asset_loader or AssetLoader()
        self._put_bytes = put_bytes_fn  # None → lazy-loaded r2_client at call time

    async def run(
        self,
        spec: PosterSpec,
        template: Optional[TemplateSpec] = None,
    ) -> RenderManifest:
        """
        Full pipeline run. Returns a RenderManifest with URLs and hashes.
        """
        trace_id = str(uuid.uuid4())
        timings: dict[str, int] = {}

        if template is None:
            template = load_template(spec.template_id)

        spec_hash = _hash_spec(spec)

        # ── Phase 1: background layer + product/material layer preparation ───
        t0 = _now()
        assets, bg_result = await asyncio.gather(
            self._loader.load(spec),
            self._bg.generate(
                style_prompt=spec.style.prompt,
                negative_prompt=spec.style.negative_prompt,
                width=spec.size[0],
                height=spec.size[1],
                seed=spec.style.seed,
                template_hint=template.background_prompt_hint,
                trace_id=trace_id,
            ),
        )
        timings["load_and_bg_ms"] = _elapsed(t0)
        timings["background_layer_ms"] = timings["load_and_bg_ms"]
        logger.info(
            "poster2: trace=%s bg=%.1fs assets=loaded",
            trace_id, timings["background_layer_ms"] / 1000,
        )

        # ── Phase 2: deterministic foreground/text render ────────────────────
        t1 = _now()
        fg_result = await self._renderer.render(template, spec, assets)
        timings["renderer_ms"] = _elapsed(t1)
        timings.update(fg_result.layer_timings_ms)
        logger.info(
            "poster2: trace=%s fg_hash=%s engine=%s renderer=%.0fms",
            trace_id, fg_result.sha256[:8], fg_result.render_engine_used, timings["renderer_ms"],
        )

        # ── Phase 3: load background bytes and compose ───────────────────────
        t2 = _now()
        bg_image = await self._loader.load_url(bg_result.url)
        compose_result = self._composer.compose(
            bg_image, fg_result.image, spec.export_format
        )
        timings["compose_ms"] = _elapsed(t2)

        # ── Phase 4: store foreground + final to R2 ──────────────────────────
        if self._put_bytes is None:
            from app.services import r2_client  # lazy: keeps boto3 out of test collection
            _put = r2_client.put_bytes
        else:
            _put = self._put_bytes

        t3 = _now()
        fg_key = f"poster2/fg/{trace_id}.png"
        fg_url = _put(fg_key, fg_result.png_bytes, content_type="image/png")
        if not fg_url:
            logger.warning("poster2: R2 upload failed for fg key=%s", fg_key)
            fg_url = ""

        ext = spec.export_format
        final_key = f"poster2/final/{trace_id}.{ext}"
        final_url = _put(final_key, compose_result.png_bytes, content_type=f"image/{ext}")
        if not final_url:
            raise RuntimeError(f"R2 upload failed for final poster key={final_key}")

        timings["storage_ms"] = _elapsed(t3)
        timings["total_ms"] = _elapsed(t0)

        logger.info(
            "poster2: trace=%s DONE final=%s total=%.1fs",
            trace_id, final_url, timings["total_ms"] / 1000,
        )

        return RenderManifest(
            trace_id=trace_id,
            template_id=template.template_id,
            template_version=template.version,
            template_contract_version=fg_result.template_contract_version,
            engine_version=ENGINE_VERSION,
            renderer_mode=spec.renderer_mode,
            render_engine_used=fg_result.render_engine_used,
            foreground_renderer=fg_result.foreground_renderer,
            background_renderer=bg_result.model,
            poster_spec_hash=spec_hash,
            resolved_inputs=_summarise_inputs(spec),
            background_url=bg_result.url,
            background_prompt=bg_result.prompt_used,
            background_seed=bg_result.seed_used,
            background_model=bg_result.model,
            foreground_url=fg_url,
            foreground_hash=fg_result.sha256,
            final_url=final_url,
            final_hash=compose_result.sha256,
            timings_ms=timings,
            degraded=fg_result.degraded,
            degraded_reason=fg_result.degraded_reason,
        )


# ── helpers ──────────────────────────────────────────────────────────────────

def _now() -> int:
    return time.monotonic_ns()


def _elapsed(t0: int) -> int:
    return (time.monotonic_ns() - t0) // 1_000_000


def _hash_spec(spec: PosterSpec) -> str:
    payload = json.dumps(asdict(spec), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _summarise_inputs(spec: PosterSpec) -> dict:
    return {
        "brand_name": spec.brand_name,
        "agent_name": spec.agent_name,
        "title": spec.title,
        "template_id": spec.template_id,
        "renderer_mode": spec.renderer_mode,
        "product_url": spec.product_image.url,
        "gallery_count": len(spec.gallery_images),
        "seed": spec.style.seed,
    }
