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
from .background import (
    FireflyBackgroundService,
    build_template_dual_v2_background,
    make_background_service,
)
from .composer import Composer
from .contracts import PosterSpec, RenderDebugArtifacts, RenderManifest, TemplateSpec
from .font_registry import FontRegistry
from .renderer import (
    LayoutRenderer,
    RendererSelector,
    load_structured_slot_spec,
    render_content_debug_layer,
    render_product_material_debug_layer,
    render_slot_structure_debug_layer,
    render_structure_overlay_debug_layer,
    render_text_debug_layer,
)

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
        self._debug_font_registry = FontRegistry()

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
        if spec.template_id == "template_dual_v2":
            assets = await self._loader.load(spec)
            if assets.scenario is not None:
                bg_result = await build_template_dual_v2_background(
                    assets.scenario,
                    width=spec.size[0],
                    height=spec.size[1],
                    trace_id=trace_id,
                )
            else:
                bg_result = await self._bg.generate(
                    style_prompt="",
                    negative_prompt=spec.style.negative_prompt,
                    width=spec.size[0],
                    height=spec.size[1],
                    seed=spec.style.seed,
                    template_hint=template.background_prompt_hint,
                    trace_id=trace_id,
                )
        else:
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

        # ── Phase 3.5: pilot debug artifact assembly ────────────────────────
        slot_spec = load_structured_slot_spec(template.template_id)
        slot_metadata_payload = _build_slot_metadata(
            template=template,
            slot_spec=slot_spec,
            spec=spec,
            assets=assets,
            bg_result=bg_result,
        )
        debug_slot_structure = render_slot_structure_debug_layer(
            template, slot_spec, font_registry=self._debug_font_registry
        )
        debug_content_layer = render_content_debug_layer(
            template, assets, font_registry=self._debug_font_registry
        )
        debug_text_layer = render_text_debug_layer(
            template, spec, font_registry=self._debug_font_registry
        )
        debug_structure_overlay = render_structure_overlay_debug_layer(
            template,
            slot_spec,
            slot_metadata_payload,
            font_registry=self._debug_font_registry,
        )
        debug_product_material = render_product_material_debug_layer(
            template, assets, font_registry=self._debug_font_registry
        )

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

        product_material_key = f"poster2/debug/product-material/{trace_id}.png"
        product_material_url = _put(
            product_material_key,
            debug_product_material.png_bytes,
            content_type="image/png",
        )
        if not product_material_url:
            logger.warning("poster2: R2 upload failed for product/material key=%s", product_material_key)
            product_material_url = ""

        slot_structure_key = f"poster2/debug/slot-structure/{trace_id}.png"
        slot_structure_url = _put(
            slot_structure_key,
            debug_slot_structure.png_bytes,
            content_type="image/png",
        ) or ""

        content_layer_key = f"poster2/debug/content-layer/{trace_id}.png"
        content_layer_url = _put(
            content_layer_key,
            debug_content_layer.png_bytes,
            content_type="image/png",
        ) or ""

        text_layer_key = f"poster2/debug/text-layer/{trace_id}.png"
        text_layer_url = _put(
            text_layer_key,
            debug_text_layer.png_bytes,
            content_type="image/png",
        ) or ""

        structure_overlay_key = f"poster2/debug/structure-overlay/{trace_id}.png"
        structure_overlay_url = _put(
            structure_overlay_key,
            debug_structure_overlay.png_bytes,
            content_type="image/png",
        ) or ""

        ext = spec.export_format
        final_key = f"poster2/final/{trace_id}.{ext}"
        final_url = _put(final_key, compose_result.png_bytes, content_type=f"image/{ext}")
        if not final_url:
            raise RuntimeError(f"R2 upload failed for final poster key={final_key}")

        slot_metadata_key = f"poster2/debug/slot-metadata/{trace_id}.json"
        slot_metadata_url = _put(
            slot_metadata_key,
            json.dumps(slot_metadata_payload, ensure_ascii=False, sort_keys=True).encode("utf-8"),
            content_type="application/json",
        )
        if not slot_metadata_url:
            logger.warning("poster2: R2 upload failed for slot metadata key=%s", slot_metadata_key)
            slot_metadata_url = ""

        renderer_metadata_payload = {
            "trace_id": trace_id,
            "template_id": template.template_id,
            "template_version": template.version,
            "template_contract_version": fg_result.template_contract_version,
            "requested_renderer_mode": spec.renderer_mode,
            "effective_renderer_mode": fg_result.render_engine_used,
            "render_engine_used": fg_result.render_engine_used,
            "foreground_renderer": fg_result.foreground_renderer,
            "background_renderer": bg_result.model,
            "background_seed": bg_result.seed_used,
            "foreground_hash": fg_result.sha256,
            "product_material_hash": debug_product_material.sha256,
            "final_hash": compose_result.sha256,
            "fallback_triggered": fg_result.degraded,
            "fallback_reason_code": fg_result.fallback_reason_code,
            "fallback_reason_detail": fg_result.fallback_reason_detail,
            "fallback_exception_class": fg_result.fallback_exception_class,
            "fallback_stage": fg_result.fallback_stage,
            "degraded": fg_result.degraded,
            "degraded_reason": fg_result.degraded_reason,
            "timings_ms": timings,
            "layer_render_status": _build_layer_render_status(
                template=template,
                spec=spec,
                assets=assets,
                bg_result=bg_result,
                slot_spec=slot_spec,
            ),
            "artifact_urls": {
                "background_layer_url": bg_result.url,
                "product_material_layer_url": product_material_url,
                "foreground_layer_url": fg_url,
                "final_composited_url": final_url,
                "slot_structure_layer_url": slot_structure_url,
                "content_layer_url": content_layer_url,
                "text_layer_url": text_layer_url,
                "structure_overlay_url": structure_overlay_url,
                "slot_metadata_url": slot_metadata_url,
            },
        }
        renderer_metadata_key = f"poster2/debug/metadata/{trace_id}.json"
        renderer_metadata_url = _put(
            renderer_metadata_key,
            json.dumps(renderer_metadata_payload, ensure_ascii=False, sort_keys=True).encode("utf-8"),
            content_type="application/json",
        )
        if not renderer_metadata_url:
            logger.warning("poster2: R2 upload failed for renderer metadata key=%s", renderer_metadata_key)
            renderer_metadata_url = ""

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
            debug_artifacts=RenderDebugArtifacts(
                background_layer_url=bg_result.url,
                product_material_layer_url=product_material_url,
                foreground_layer_url=fg_url,
                final_composited_url=final_url,
                renderer_metadata_url=renderer_metadata_url,
                slot_structure_layer_url=slot_structure_url,
                content_layer_url=content_layer_url,
                text_layer_url=text_layer_url,
                structure_overlay_url=structure_overlay_url,
                slot_metadata_url=slot_metadata_url,
            ),
            fallback_reason_code=fg_result.fallback_reason_code,
            fallback_reason_detail=fg_result.fallback_reason_detail,
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


def _build_layer_render_status(
    *,
    template: TemplateSpec,
    spec: PosterSpec,
    assets,
    bg_result: BackgroundResult,
    slot_spec: dict | None = None,
) -> dict[str, dict[str, object]]:
    gallery_count = min(len(assets.gallery), 4)
    gallery_rendered = gallery_count > 0
    feature_count = min(len(spec.features), len(template.feature_callouts))
    layer_status = {
        "background_base_layer": {
            "rendered": True,
            "reason_code": None,
            "source_binding": bg_result.url,
            "count": 1,
        },
        "background_tone_layer": {
            "rendered": False,
            "reason_code": "tone_overlay_disabled",
            "source_binding": None,
            "count": 0,
        },
        "header_shell_layer": {
            "rendered": True,
            "reason_code": None,
            "source_binding": "template_dual_v2.header_shell",
            "count": 1,
        },
        "brand_logo_layer": {
            "rendered": assets.logo is not None,
            "reason_code": None if assets.logo is not None else "logo_missing",
            "source_binding": spec.logo.url if spec.logo else None,
            "count": 1 if assets.logo is not None else 0,
        },
        "brand_text_layer": {
            "rendered": bool(spec.brand_name),
            "reason_code": None if spec.brand_name else "brand_name_empty",
            "source_binding": "brand_name",
            "count": 1 if spec.brand_name else 0,
        },
        "agent_pill_layer": {
            "rendered": bool(spec.agent_name),
            "reason_code": None if spec.agent_name else "agent_name_empty",
            "source_binding": "agent_name",
            "count": 1 if spec.agent_name else 0,
        },
        "scenario_card_shell_layer": {
            "rendered": True,
            "reason_code": None,
            "source_binding": "template_dual_v2.scenario_card_shell",
            "count": 1,
        },
        "scenario_image_layer": {
            "rendered": True,
            "reason_code": None if assets.scenario is not None else "safe_preset_fill",
            "source_binding": spec.scenario_image.url if spec.scenario_image else "safe_preset_image",
            "count": 1,
        },
        "product_card_shell_layer": {
            "rendered": True,
            "reason_code": None,
            "source_binding": "template_dual_v2.product_card_shell",
            "count": 1,
        },
        "product_image_layer": {
            "rendered": assets.product is not None,
            "reason_code": None if assets.product is not None else "product_image_missing",
            "source_binding": spec.product_image.url,
            "count": 1 if assets.product is not None else 0,
        },
        "feature_callout_layer": {
            "rendered": feature_count > 0,
            "reason_code": None if feature_count > 0 else "features_empty",
            "source_binding": "features",
            "count": feature_count,
        },
        "title_layer": {
            "rendered": bool(spec.title),
            "reason_code": None if spec.title else "title_empty",
            "source_binding": "title",
            "count": 1 if spec.title else 0,
        },
        "subtitle_layer": {
            "rendered": bool(spec.subtitle),
            "reason_code": None if spec.subtitle else "subtitle_empty",
            "source_binding": "subtitle",
            "count": 1 if spec.subtitle else 0,
        },
        "bottom_gallery_shell_layer": {
            "rendered": gallery_rendered,
            "reason_code": None if gallery_rendered else "gallery_hidden",
            "source_binding": "gallery_images",
            "count": gallery_count,
        },
        "bottom_gallery_items_layer": {
            "rendered": gallery_rendered,
            "reason_code": None if gallery_rendered else "gallery_empty",
            "source_binding": "gallery_images",
            "count": gallery_count,
        },
        "bottom_tagline_layer": {
            "rendered": False,
            "reason_code": "operator_tagline_unbound",
            "source_binding": None,
            "count": 0,
        },
    }
    return layer_status


def _build_slot_metadata(
    *,
    template: TemplateSpec,
    slot_spec: dict,
    spec: PosterSpec,
    assets,
    bg_result: BackgroundResult,
) -> dict[str, object]:
    gallery_count = min(len(assets.gallery), 4)
    gallery_state = "hide"
    if gallery_count > 0:
        gallery_state = "show" if gallery_count >= template.gallery_slot.count else "fallback-fill"
    regions = {
        "background_region": {
            "background_base_layer": {
                "rendered": True,
                "reason": None,
                "source_binding": bg_result.url,
                "bounds": slot_spec["slot_contracts"]["background_base_layer"]["bounds"],
            },
            "background_tone_layer": {
                "rendered": False,
                "reason": "tone_overlay_disabled",
                "source_binding": None,
                "bounds": slot_spec["slot_contracts"]["background_tone_layer"]["bounds"],
            },
        },
        "header_region": {
            "header_shell_layer": {
                "rendered": True,
                "reason": None,
                "source_binding": "template_dual_v2.header_shell",
                "bounds": slot_spec["slot_contracts"]["header_shell_layer"]["bounds"],
            },
            "brand_logo_slot": {
                "rendered": assets.logo is not None,
                "reason": None if assets.logo is not None else "logo_not_bound",
                "source_binding": spec.logo.url if spec.logo else None,
                "bounds": slot_spec["slot_contracts"]["brand_logo_slot"]["bounds"],
                "fit": "contain",
                "count": 1 if assets.logo is not None else 0,
            },
            "brand_text_slot": {
                "rendered": bool(spec.brand_name),
                "reason": None if spec.brand_name else "brand_name_empty",
                "source_binding": "brand_name",
                "bounds": slot_spec["slot_contracts"]["brand_text_slot"]["bounds"],
            },
            "agent_pill_slot": {
                "rendered": bool(spec.agent_name),
                "reason": None if spec.agent_name else "agent_name_empty",
                "source_binding": "agent_name",
                "bounds": slot_spec["slot_contracts"]["agent_pill_slot"]["bounds"],
            },
        },
        "scenario_region": {
            "scenario_card_shell_slot": {
                "rendered": True,
                "reason": None,
                "source_binding": "template_dual_v2.scenario_shell",
                "bounds": slot_spec["slot_contracts"]["scenario_card_shell_slot"]["bounds"],
            },
            "scenario_image_slot": {
                "rendered": True,
                "reason": None if assets.scenario is not None else "scenario_image_missing_safe_preset_fill",
                "source_binding": spec.scenario_image.url if spec.scenario_image else "safe_preset_image",
                "bounds": slot_spec["slot_contracts"]["scenario_image_slot"]["bounds"],
                "fit": "cover",
                "count": 1,
            },
        },
        "product_region": {
            "product_card_shell_slot": {
                "rendered": True,
                "reason": None,
                "source_binding": "template_dual_v2.product_shell",
                "bounds": slot_spec["slot_contracts"]["product_card_shell_slot"]["bounds"],
            },
            "product_image_slot": {
                "rendered": assets.product is not None,
                "reason": None if assets.product is not None else "product_image_missing",
                "source_binding": spec.product_image.url,
                "bounds": slot_spec["slot_contracts"]["product_image_slot"]["bounds"],
                "fit": "contain",
                "count": 1 if assets.product is not None else 0,
            },
        },
        "feature_region": {
            "feature_callout_slots": {
                "rendered": len(spec.features) > 0,
                "reason": None if len(spec.features) > 0 else "features_empty",
                "source_binding": "features[]",
                "bounds": slot_spec["slot_contracts"]["feature_callout_slots"]["bounds"],
                "count": min(len(spec.features), len(template.feature_callouts)),
                "max_lines": 2,
            },
        },
        "bottom_region": {
            "title_box": {
                "rendered": bool(spec.title),
                "reason": None if spec.title else "title_empty",
                "source_binding": "title",
                "bounds": slot_spec["slot_contracts"]["title_box"]["bounds"],
                "max_lines": 2,
            },
            "subtitle_box": {
                "rendered": bool(spec.subtitle),
                "reason": None if spec.subtitle else "subtitle_empty",
                "source_binding": "subtitle",
                "bounds": slot_spec["slot_contracts"]["subtitle_box"]["bounds"],
                "max_lines": 1,
            },
            "gallery_shell_slot": {
                "rendered": gallery_state != "hide",
                "reason": None if gallery_state != "hide" else "gallery_hidden_no_assets",
                "source_binding": "gallery_images[]",
                "bounds": slot_spec["slot_contracts"]["gallery_shell_slot"]["bounds"],
                "count": gallery_count,
                "state": gallery_state,
            },
            "gallery_item_slots": {
                "rendered": gallery_count > 0,
                "reason": None if gallery_count > 0 else "gallery_hidden_no_assets",
                "source_binding": "gallery_images[]",
                "bounds": slot_spec["slot_contracts"]["gallery_item_slots"]["bounds"],
                "fit": "cover",
                "count": gallery_count,
                "state": gallery_state,
            },
            "tagline_box": {
                "rendered": False,
                "reason": "operator_tagline_unbound",
                "source_binding": None,
                "bounds": slot_spec["slot_contracts"]["tagline_box"]["bounds"],
                "max_lines": 1,
            },
        },
    }
    return {
        "template_id": template.template_id,
        "template_contract_version": template.contract_version,
        "regions": regions,
    }
