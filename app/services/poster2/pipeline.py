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
from .quality_guard import evaluate_deliverability, run_preflight_guard
from .renderer import LayoutRenderer, RendererSelector, render_product_material_debug_layer
from .renderer_routing import assert_quality_guard_deliverable
from .template_behavior import resolve_template_behavior
from .template_registry import validate_template_registration

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
    template = TemplateSpec.from_json(path)
    validate_template_registration(template)
    return template


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
        else:
            validate_template_registration(template)
        resolved_behavior = resolve_template_behavior(
            template,
            feature_count=len([item for item in spec.features if item and item.strip()]),
            title_text=spec.title,
            subtitle_text=spec.subtitle,
            gallery_requested_count=len(spec.gallery_images),
            bottom_mode=spec.bottom_mode,
            gallery_mode=spec.gallery_mode,
        )
        run_preflight_guard(template, spec)

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
        resolved_behavior = resolve_template_behavior(
            template,
            feature_count=len([item for item in spec.features if item and item.strip()]),
            title_text=spec.title,
            subtitle_text=spec.subtitle,
            gallery_requested_count=len(spec.gallery_images),
            gallery_resolved_count=min(len(assets.gallery), template.gallery_slot.count),
            bottom_mode=spec.bottom_mode,
            gallery_mode=spec.gallery_mode,
        )
        logger.info(
            "poster2: trace=%s bg=%.1fs assets=loaded",
            trace_id, timings["background_layer_ms"] / 1000,
        )
        logger.info(
            "poster2.gallery_presence_done requested=%d resolved=%d",
            min(len(spec.gallery_images), 4),
            min(len(assets.gallery), 4),
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

        layer_render_status = fg_result.layer_render_status or _build_layer_render_status(
            template=template,
            spec=spec,
            assets=assets,
            bg_result=bg_result,
            behavior=resolved_behavior,
        )
        inferred_layer_render_status = _build_layer_render_status(
            template=template,
            spec=spec,
            assets=assets,
            bg_result=bg_result,
            behavior=resolved_behavior,
        )
        inferred_region_render_status = _build_region_render_status(inferred_layer_render_status)
        structure_evidence_complete = bool(fg_result.layer_render_status) and bool(fg_result.region_render_status)
        structure_evidence_source = (
            "renderer_derived" if structure_evidence_complete else "pipeline_inferred"
        )
        layer_render_status = _merge_status_maps(inferred_layer_render_status, fg_result.layer_render_status)
        region_render_status = _merge_status_maps(inferred_region_render_status, fg_result.region_render_status)
        quality_guard_report = evaluate_deliverability(
            template=template,
            spec=spec,
            assets=assets,
            layer_render_status=(
                fg_result.layer_render_status if structure_evidence_complete else inferred_layer_render_status
            ),
            region_render_status=(
                fg_result.region_render_status if structure_evidence_complete else inferred_region_render_status
            ),
            structure_evidence_source=structure_evidence_source,
            structure_evidence_complete=structure_evidence_complete,
        )
        if fg_result.degraded:
            assert_quality_guard_deliverable(
                deliverable=quality_guard_report.deliverable,
                missing_required_slots=quality_guard_report.missing_required_slots,
                missing_mandatory_regions=quality_guard_report.missing_mandatory_regions,
            )

        # ── Phase 3: load background bytes and compose ───────────────────────
        t2 = _now()
        bg_image = await self._loader.load_url(bg_result.url)
        compose_result = self._composer.compose(
            bg_image, fg_result.image, spec.export_format
        )
        timings["compose_ms"] = _elapsed(t2)

        # ── Phase 3.5: pilot debug artifact assembly ────────────────────────
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

        ext = spec.export_format
        final_key = f"poster2/final/{trace_id}.{ext}"
        final_url = _put(final_key, compose_result.png_bytes, content_type=f"image/{ext}")
        if not final_url:
            raise RuntimeError(f"R2 upload failed for final poster key={final_key}")

        renderer_metadata_payload = {
            "trace_id": trace_id,
            "template_id": template.template_id,
            "template_version": template.version,
            "template_contract_version": fg_result.template_contract_version,
            "template_behavior": resolved_behavior.as_dict(),
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
            "layer_render_status": layer_render_status,
            "region_render_status": quality_guard_report.region_render_status,
            "region_completeness_status": quality_guard_report.region_completeness_status,
            "slot_binding_status": quality_guard_report.slot_binding_status,
            "structure_complete": quality_guard_report.structure_complete,
            "incomplete_structure": quality_guard_report.incomplete_structure,
            "deliverable": quality_guard_report.deliverable,
            "structure_evidence_source": quality_guard_report.structure_evidence_source,
            "structure_evidence_complete": quality_guard_report.structure_evidence_complete,
            "missing_mandatory_regions": quality_guard_report.missing_mandatory_regions,
            "missing_required_slots": quality_guard_report.missing_required_slots,
            "geometry_evidence": _build_geometry_evidence(
                template,
                resolved_behavior=resolved_behavior,
                layer_render_status=layer_render_status,
                region_render_status=quality_guard_report.region_render_status,
            ),
            "bottom_contract_review": _build_bottom_contract_review(
                template,
                resolved_behavior=resolved_behavior,
                region_render_status=quality_guard_report.region_render_status,
            ),
            "gallery_items_status": fg_result.gallery_items_status,
            "artifact_urls": {
                "background_layer_url": bg_result.url,
                "product_material_layer_url": product_material_url,
                "foreground_layer_url": fg_url,
                "final_composited_url": final_url,
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
            ),
            fallback_reason_code=fg_result.fallback_reason_code,
            fallback_reason_detail=fg_result.fallback_reason_detail,
            degraded=fg_result.degraded,
            degraded_reason=fg_result.degraded_reason,
            structure_complete=quality_guard_report.structure_complete,
            incomplete_structure=quality_guard_report.incomplete_structure,
            deliverable=quality_guard_report.deliverable,
            structure_evidence_source=quality_guard_report.structure_evidence_source,
            structure_evidence_complete=quality_guard_report.structure_evidence_complete,
            missing_mandatory_regions=quality_guard_report.missing_mandatory_regions,
            missing_required_slots=quality_guard_report.missing_required_slots,
            region_render_status=quality_guard_report.region_render_status,
            slot_binding_status=quality_guard_report.slot_binding_status,
            template_behavior=resolved_behavior.as_dict(),
            geometry_evidence=renderer_metadata_payload["geometry_evidence"],
            bottom_contract_review=renderer_metadata_payload["bottom_contract_review"],
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
    behavior,
) -> dict[str, dict[str, object]]:
    gallery_requested = min(len(spec.gallery_images), 4)
    gallery_valid = min(len(assets.gallery), 4)
    gallery_rendered = behavior.bottom_policy.gallery_strip_rendered and gallery_valid > 0
    feature_count = min(len([item for item in spec.features if item and item.strip()]), len(template.feature_callouts))
    layer_status = {
        "background_base_layer": {
            "rendered": True,
            "reason_code": None,
            "source_binding": bg_result.url,
            "count": 1,
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
            "collapsed": assets.logo is None,
        },
        "brand_text_layer": {
            "rendered": bool(spec.brand_name),
            "reason_code": None if spec.brand_name else "brand_name_empty",
            "source_binding": "brand_name",
            "count": 1 if spec.brand_name else 0,
            "collapsed": not bool(spec.brand_name),
        },
        "agent_name_text_layer": {
            "rendered": bool(spec.agent_name),
            "reason_code": None if spec.agent_name else "agent_name_empty",
            "source_binding": "agent_name",
            "count": 1 if spec.agent_name else 0,
            "collapsed": not bool(spec.agent_name),
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
            "collapsed": feature_count == 0,
        },
        "title_layer": {
            "rendered": behavior.bottom_policy.title_slot_rendered,
            "reason_code": None if behavior.bottom_policy.title_slot_rendered else ("title_empty" if not spec.title else "suppressed_by_bottom_mode"),
            "source_binding": "title",
            "count": 1 if behavior.bottom_policy.title_slot_rendered else 0,
        },
        "subtitle_layer": {
            "rendered": behavior.bottom_policy.subtitle_slot_rendered,
            "reason_code": behavior.bottom_policy.subtitle_slot_state["reason_code"],
            "source_binding": "subtitle",
            "count": 1 if behavior.bottom_policy.subtitle_slot_rendered else 0,
        },
        "title_band_region_shell_layer": {
            "rendered": behavior.bottom_policy.title_band_rendered,
            "reason_code": None if behavior.bottom_policy.title_band_rendered else "title_band_collapsed",
            "source_binding": "bottom_mode",
            "count": 1 if behavior.bottom_policy.title_band_rendered else 0,
            "collapsed": not behavior.bottom_policy.title_band_rendered,
        },
        "bottom_gallery_shell_layer": {
            "rendered": behavior.bottom_policy.gallery_strip_rendered,
            "reason_code": None if behavior.bottom_policy.gallery_strip_rendered else ("gallery_hidden_by_bottom_mode" if gallery_requested > 0 else "gallery_hidden"),
            "source_binding": "gallery_images",
            "count": 1 if behavior.bottom_policy.gallery_strip_rendered else 0,
            "count_requested": gallery_requested,
            "count_valid": gallery_valid,
            "collapsed": not behavior.bottom_policy.gallery_strip_rendered,
        },
        "gallery_strip_region_shell_layer": {
            "rendered": behavior.bottom_policy.gallery_strip_rendered,
            "reason_code": None if behavior.bottom_policy.gallery_strip_rendered else ("gallery_hidden_by_bottom_mode" if gallery_requested > 0 else "gallery_empty"),
            "source_binding": "gallery_mode",
            "count": 1 if behavior.bottom_policy.gallery_strip_rendered else 0,
            "collapsed": not behavior.bottom_policy.gallery_strip_rendered,
        },
        "bottom_gallery_items_layer": {
            "rendered": gallery_rendered,
            "reason_code": None if gallery_rendered else ("gallery_hidden_by_bottom_mode" if gallery_requested > 0 else "gallery_empty"),
            "source_binding": "gallery_images",
            "count": behavior.bottom_policy.visible_item_count,
            "count_requested": gallery_requested,
            "count_valid": gallery_valid,
            "count_visible": behavior.bottom_policy.visible_item_count,
            "collapsed": not gallery_rendered,
        },
        "bottom_tagline_layer": {
            "rendered": False,
            "reason_code": "operator_tagline_unbound",
            "source_binding": None,
            "count": 0,
        },
    }
    return layer_status


def _build_region_render_status(
    layer_status: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
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


def _merge_status_maps(
    inferred: dict[str, dict[str, object]],
    emitted: Optional[dict[str, dict[str, object]]],
) -> dict[str, dict[str, object]]:
    if not emitted:
        return inferred
    merged = {key: dict(value) for key, value in inferred.items()}
    for key, value in emitted.items():
        merged[key] = dict(value)
    return merged


def _build_geometry_evidence(
    template: TemplateSpec,
    *,
    resolved_behavior,
    layer_render_status: dict[str, dict[str, object]],
    region_render_status: dict[str, dict[str, object]],
) -> dict[str, object]:
    return {
        "region_bounds": {
            "header_region": _header_region_bounds(template),
            "bottom_region": _bottom_region_bounds(template, resolved_behavior),
            "title_band_region": _title_band_region_bounds(template, resolved_behavior),
            "product_region": _slot_bounds(template.product_slot),
            "gallery_strip_region": _gallery_strip_region_bounds(template, resolved_behavior),
        },
        "slot_bounds": {
            "brand_logo_slot": _slot_bounds(template.logo_slot),
            "brand_name_slot": _text_slot_bounds(template.brand_name_slot),
            "agent_name_slot": _text_slot_bounds(template.agent_name_slot),
            "title_slot": _title_slot_bounds(template, resolved_behavior),
            "subtitle_slot": _subtitle_slot_bounds(template, resolved_behavior),
            "product_slot": _slot_bounds(template.product_slot),
            "gallery_slot": _gallery_item_slot_bounds(template, resolved_behavior),
        },
        "visible_item_count": {
            "header_region": int(region_render_status.get("header_region", {}).get("count", 0)),
            "title_band_region": int(region_render_status.get("title_band_region", {}).get("count", 0)),
            "product_region": int(region_render_status.get("product_region", {}).get("count", 0)),
            "gallery_strip_region": int(
                layer_render_status.get("bottom_gallery_items_layer", {}).get("count_visible", 0)
            ),
            "bottom_region": int(region_render_status.get("bottom_region", {}).get("count", 0)),
        },
    }


def _slot_bounds(slot) -> dict[str, int]:
    return {"x": int(slot.x), "y": int(slot.y), "w": int(slot.w), "h": int(slot.h)}


def _text_slot_bounds(slot) -> dict[str, int]:
    return {"x": int(slot.x), "y": int(slot.y), "w": int(slot.w), "h": int(slot.h)}


def _header_region_bounds(template: TemplateSpec) -> dict[str, int]:
    left = min(template.logo_slot.x, template.brand_name_slot.x, template.agent_name_slot.x) - 32
    top = min(template.logo_slot.y, template.brand_name_slot.y, template.agent_name_slot.y) - 18
    right = max(
        template.logo_slot.x + template.logo_slot.w,
        template.brand_name_slot.x + template.brand_name_slot.w,
        template.agent_name_slot.x + template.agent_name_slot.w,
    ) + 40
    bottom = max(
        template.logo_slot.y + template.logo_slot.h,
        template.brand_name_slot.y + template.brand_name_slot.h,
        template.agent_name_slot.y + template.agent_name_slot.h,
    ) + 22
    return {"x": left, "y": top, "w": right - left, "h": bottom - top}


def _bottom_region_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    layout = resolved_behavior.bottom_policy.layout_metrics
    return {
        "x": 96,
        "y": int(layout["bottom_shell_top"]),
        "w": 832,
        "h": int(layout["bottom_shell_height"]),
    }


def _title_band_region_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    layout = resolved_behavior.bottom_policy.layout_metrics
    return {
        "x": 112,
        "y": int(layout["title_band_top"]),
        "w": 800,
        "h": int(layout["title_band_height"]),
    }


def _gallery_strip_region_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    layout = resolved_behavior.bottom_policy.layout_metrics
    return {
        "x": int(template.gallery_slot.x),
        "y": int(layout["gallery_shell_top"]),
        "w": int(template.gallery_slot.w),
        "h": int(layout["gallery_shell_height"]),
    }


def _gallery_item_slot_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    gallery_layouts = list(resolved_behavior.bottom_policy.layout_metrics.get("gallery_item_layouts", []))
    if gallery_layouts:
        first = gallery_layouts[0]
        return {
            "x": int(first["x"]),
            "y": int(first["y"]),
            "w": int(first["w"]),
            "h": int(first["h"]),
        }
    return {
        "x": int(template.gallery_slot.x),
        "y": int(template.gallery_slot.y),
        "w": int(template.gallery_slot.thumb_w),
        "h": int(template.gallery_slot.h),
    }


def _title_slot_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    layout = resolved_behavior.bottom_policy.layout_metrics
    return {
        "x": int(template.title_slot.x),
        "y": int(layout["title_slot_y"]),
        "w": int(template.title_slot.w),
        "h": int(layout["title_slot_height"]),
    }


def _subtitle_slot_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    layout = resolved_behavior.bottom_policy.layout_metrics
    return {
        "x": int(template.subtitle_slot.x),
        "y": int(layout["subtitle_slot_y"]),
        "w": int(template.subtitle_slot.w),
        "h": int(layout["subtitle_slot_height"]),
    }


def _build_bottom_contract_review(
    template: TemplateSpec,
    *,
    resolved_behavior,
    region_render_status: dict[str, dict[str, object]],
) -> dict[str, object]:
    gallery_slots = {
        slot_state["slot_id"]: {
            "rendered": slot_state["rendered"],
            "state": slot_state["state"],
            "reason_code": slot_state["reason_code"],
            "distribution_policy": slot_state.get("distribution_policy"),
            "bounds": slot_state.get("bounds"),
            "local_bounds": slot_state.get("local_bounds"),
        }
        for slot_state in resolved_behavior.bottom_policy.gallery_slot_states
    }
    return {
        "bottom_mode": resolved_behavior.bottom_policy.mode,
        "gallery_mode": resolved_behavior.bottom_policy.gallery_mode,
        "title_band_region": {
            "rendered": bool(region_render_status.get("title_band_region", {}).get("rendered", False)),
            "bounds": _title_band_region_bounds(template, resolved_behavior),
        },
        "gallery_strip_region": {
            "rendered": bool(region_render_status.get("gallery_strip_region", {}).get("rendered", False)),
            "visible_item_count": resolved_behavior.bottom_policy.visible_item_count,
            "bounds": _gallery_strip_region_bounds(template, resolved_behavior),
        },
        "behavior_policy": {
            "title_band_sizing_mode": resolved_behavior.bottom_policy.title_band_sizing_mode,
            "subtitle_overflow_policy": resolved_behavior.bottom_policy.subtitle_overflow_policy,
            "title_text_budget_policy": resolved_behavior.bottom_policy.title_text_budget_policy,
            "subtitle_text_budget_policy": resolved_behavior.bottom_policy.subtitle_text_budget_policy,
            "content_priority_policy": resolved_behavior.bottom_policy.content_priority_policy,
            "peer_balance_policy": resolved_behavior.bottom_policy.peer_balance_policy,
            "gallery_distribution_policy": resolved_behavior.bottom_policy.gallery_distribution_policy,
            "title_line_clamp": resolved_behavior.bottom_policy.title_line_clamp,
            "subtitle_line_clamp": resolved_behavior.bottom_policy.subtitle_line_clamp,
            "title_char_budget": resolved_behavior.bottom_policy.title_char_budget,
            "subtitle_char_budget": resolved_behavior.bottom_policy.subtitle_char_budget,
            "layout_metrics": dict(resolved_behavior.bottom_policy.layout_metrics),
        },
        "collapsed_optional_slots": list(resolved_behavior.bottom_policy.collapsed_optional_slots),
        "subtitle_slot": dict(resolved_behavior.bottom_policy.subtitle_slot_state),
        "gallery_slots": gallery_slots,
    }
