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
import os
import re
import time
import uuid
from dataclasses import asdict, replace
from pathlib import Path
from typing import Optional

from PIL import Image as PILImage
from app.services.email.copy_safety import (
    normalize_marketing_subtitle,
    normalize_marketing_title,
)

from .asset_loader import AssetLoader
from .background import (
    FireflyBackgroundService,
    build_template_dual_v2_background,
    make_background_service,
)
from .composer import Composer
from .contracts import PosterSpec, RenderDebugArtifacts, RenderManifest, TemplateSpec
from .errors import PosterGenerationStageError
from .copy_optimizer import resolve_copy_optimization
from .font_registry import FontRegistry
from .quality_guard import evaluate_deliverability, run_preflight_guard
from .region_matrix import _BOTTOM_MODE_COLLAPSED_BY_DESIGN
from .renderer import LayoutRenderer, RendererSelector, render_product_material_debug_layer
from .renderer_routing import assert_quality_guard_deliverable
from .skills.evidence.family_a_evidence_surface_v1 import (
    filter_visible_truth_evidence as filter_family_a_visible_truth_evidence,
    get_visible_truth_keys as get_family_a_visible_truth_keys,
)
from .skills.structure.family_a_structure_surface_v1 import (
    build_structure_surface as build_family_a_structure_surface,
)
from .template_behavior import (
    _FAMILY_A_FRYER_ANNOTATION_CARD_STYLE_TOKENS,
    _FAMILY_A_FRYER_BOTTOM_SURFACE_TOKENS,
    _FROZEN_PRODUCT_ANNOTATION_SLOT_IDS,
    _FROZEN_PRODUCT_OWNER_SURFACES,
    _PRODUCT_ANNOTATION_OWNER_SLOT,
    _PRODUCT_ANNOTATION_TEXT_OWNER_REGION,
    _TEXT_LAYER_OWNER_MAP,
    resolve_template_behavior,
)
from .template_registry import validate_template_registration

logger = logging.getLogger("ai-service.poster2")

ENGINE_VERSION = "2.0.0"
_DEFAULT_STAGE_TIMEOUTS_MS = {
    "asset_fetch": max(int(os.getenv("POSTER2_ASSET_STAGE_TIMEOUT_MS", "30000") or 0), 1),
    "material_prepare": max(int(os.getenv("POSTER2_MATERIAL_STAGE_TIMEOUT_MS", "30000") or 0), 1),
    "puppeteer_render": max(int(os.getenv("POSTER2_RENDER_STAGE_TIMEOUT_MS", "60000") or 0), 1),
    "compose": max(int(os.getenv("POSTER2_COMPOSE_STAGE_TIMEOUT_MS", "30000") or 0), 1),
    "storage_publish": max(int(os.getenv("POSTER2_STORAGE_STAGE_TIMEOUT_MS", "30000") or 0), 1),
}
_TEMPLATE_B_SKU_CHAR_BUDGET = 64
_TEMPLATE_B_TITLE_CHAR_BUDGET = 120
_TEMPLATE_B_SUBTITLE_CHAR_BUDGET = 80
_TEMPLATE_B_DESCRIPTION_TITLE_CHAR_BUDGET = 80
_TEMPLATE_B_DESCRIPTION_BODY_CHAR_BUDGET = 400
_TEMPLATE_A_VISIBLE_TRUTH_KEYS = set(get_family_a_visible_truth_keys())
_TEMPLATE_B_VISIBLE_TRUTH_KEYS = {
    "logo_banner_region",
    "brand_logo_slot",
    "brand_name_slot",
    "agent_name_slot",
    "top_copy_region",
    "sku_text_layer",
    "top_copy_title_layer",
    "top_copy_subtitle_layer",
    "materials_strip_region",
    "materials_item_0",
    "materials_item_1",
    "materials_item_2",
    "materials_item_3",
    "materials_item_4",
    "product_hero_region",
    "product_primary_image",
    "product_secondary_inset",
    "description_region",
    "description_title_layer",
    "description_body_layer",
}

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


def _filter_visible_truth_evidence(template: TemplateSpec, evidence: dict[str, object]) -> dict[str, object]:
    if not evidence:
        return {}
    if template.template_id == "template_product_sheet_v1":
        return {
            key: value
            for key, value in evidence.items()
            if key in _TEMPLATE_B_VISIBLE_TRUTH_KEYS
        }
    return filter_family_a_visible_truth_evidence(evidence)


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
        requested_spec = spec

        if template is None:
            template = load_template(spec.template_id)
        else:
            validate_template_registration(template)
        effective_spec = _normalize_contract_text_spec(spec, template)
        effective_spec, copy_optimization_review = resolve_copy_optimization(
            template,
            requested_spec=requested_spec,
            effective_spec=effective_spec,
        )
        run_preflight_guard(template, effective_spec)

        spec_hash = _hash_spec(effective_spec)
        gallery_counts = _gallery_contract_counts(effective_spec)

        # ── Phase 1: background layer + product/material layer preparation ───
        t0 = _now()
        try:
            if effective_spec.template_id == "template_dual_v2":
                assets = await _run_stage_with_timeout(
                    "asset_fetch",
                    self._loader.load(effective_spec),
                )
                if assets.scenario is not None:
                    bg_result = await _run_stage_with_timeout(
                        "material_prepare",
                        build_template_dual_v2_background(
                            assets.scenario,
                            width=effective_spec.size[0],
                            height=effective_spec.size[1],
                            trace_id=trace_id,
                        ),
                    )
                else:
                    bg_result = await _run_stage_with_timeout(
                        "material_prepare",
                        self._bg.generate(
                            style_prompt="",
                            negative_prompt=effective_spec.style.negative_prompt,
                            width=effective_spec.size[0],
                            height=effective_spec.size[1],
                            seed=effective_spec.style.seed,
                            template_hint=template.background_prompt_hint,
                            trace_id=trace_id,
                        ),
                    )
            else:
                assets, bg_result = await asyncio.gather(
                    _run_stage_with_timeout("asset_fetch", self._loader.load(effective_spec)),
                    _run_stage_with_timeout(
                        "material_prepare",
                        self._bg.generate(
                            style_prompt=effective_spec.style.prompt,
                            negative_prompt=effective_spec.style.negative_prompt,
                            width=effective_spec.size[0],
                            height=effective_spec.size[1],
                            seed=effective_spec.style.seed,
                            template_hint=template.background_prompt_hint,
                            trace_id=trace_id,
                        ),
                    ),
                )
        except PosterGenerationStageError:
            raise
        except Exception as exc:
            raise PosterGenerationStageError(
                "material_prepare",
                "background_prepare_failed",
                "failed to prepare background or materials",
                detail=str(exc),
                exception_class=exc.__class__.__name__,
            ) from exc
        timings["load_and_bg_ms"] = _elapsed(t0)
        timings["background_layer_ms"] = timings["load_and_bg_ms"]
        resolved_behavior = resolve_template_behavior(
            template,
            feature_count=len([item for item in effective_spec.features if item and item.strip()]),
            product_image_size=assets.product.size,
            title_text=effective_spec.title,
            subtitle_text=effective_spec.subtitle,
            brand_name=effective_spec.brand_name,
            gallery_requested_count=int(gallery_counts["requested"]),
            gallery_input_count_normalized=int(gallery_counts["normalized"]),
            gallery_resolved_count=min(len(assets.gallery), template.gallery_slot.count),
            bottom_mode=effective_spec.bottom_mode,
            gallery_mode=effective_spec.gallery_mode,
            agent_name=effective_spec.agent_name,
            has_product_secondary_asset=assets.product_secondary is not None,
            # Template B extensions
            materials_count=len(assets.materials),
            description_title=effective_spec.description_title,
            description_body=effective_spec.description_body,
            sku_text=effective_spec.sku_text,
        )
        logger.info(
            "poster2: trace=%s bg=%.1fs assets=loaded",
            trace_id, timings["background_layer_ms"] / 1000,
        )
        logger.info(
            "poster2.gallery_presence_done requested=%d resolved=%d",
            int(gallery_counts["requested"]),
            min(len(assets.gallery), 4),
        )

        # ── Phase 2: deterministic foreground/text render ────────────────────
        t1 = _now()
        try:
            fg_result = await _run_stage_with_timeout(
                "puppeteer_render",
                self._renderer.render(template, effective_spec, assets),
            )
        except PosterGenerationStageError:
            raise
        except Exception as exc:
            raise PosterGenerationStageError(
                "puppeteer_render",
                "renderer_execution_failed",
                "failed to render poster foreground",
                detail=str(exc),
                exception_class=exc.__class__.__name__,
            ) from exc
        timings["renderer_ms"] = _elapsed(t1)
        timings.update(fg_result.layer_timings_ms)
        logger.info(
            "poster2: trace=%s fg_hash=%s engine=%s renderer=%.0fms",
            trace_id, fg_result.sha256[:8], fg_result.render_engine_used, timings["renderer_ms"],
        )

        layer_render_status = fg_result.layer_render_status or _build_layer_render_status(
            template=template,
            spec=effective_spec,
            assets=assets,
            bg_result=bg_result,
            behavior=resolved_behavior,
        )
        inferred_layer_render_status = _build_layer_render_status(
            template=template,
            spec=effective_spec,
            assets=assets,
            bg_result=bg_result,
            behavior=resolved_behavior,
        )
        inferred_region_render_status = _build_region_render_status(template, inferred_layer_render_status)
        structure_evidence_complete = bool(fg_result.layer_render_status) and bool(fg_result.region_render_status)
        structure_evidence_source = (
            "renderer_derived" if structure_evidence_complete else "pipeline_inferred"
        )
        layer_render_status = _merge_status_maps(inferred_layer_render_status, fg_result.layer_render_status)
        region_render_status = _merge_status_maps(inferred_region_render_status, fg_result.region_render_status)
        quality_guard_report = evaluate_deliverability(
            template=template,
            spec=effective_spec,
            assets=assets,
            layer_render_status=(
                fg_result.layer_render_status if structure_evidence_complete else inferred_layer_render_status
            ),
            region_render_status=(
                fg_result.region_render_status if structure_evidence_complete else inferred_region_render_status
            ),
            structure_evidence_source=structure_evidence_source,
            structure_evidence_complete=structure_evidence_complete,
            binding_inputs={
                "bottom_mode": resolved_behavior.bottom_policy.effective_mode,
                "brand_name": effective_spec.brand_name,
                "sku_text": effective_spec.sku_text,
                "title": effective_spec.title,
                "subtitle": effective_spec.subtitle,
                "materials_images": list(effective_spec.materials_images),
                "description_title": effective_spec.description_title,
                "description_body": effective_spec.description_body,
                "product_image_present": assets.product is not None,
            },
        )
        visible_truth_evidence = _filter_visible_truth_evidence(
            template,
            fg_result.visible_truth_evidence or {},
        )
        template_b_parity_review = (
            _build_template_b_parity_review(
                template,
                visible_truth_evidence=visible_truth_evidence,
                geometry_evidence=_build_geometry_evidence(
                    template,
                    resolved_behavior=resolved_behavior,
                    layer_render_status=layer_render_status,
                    region_render_status=quality_guard_report.region_render_status,
                ),
            )
            if fg_result.render_engine_used == "puppeteer" and template.template_id == "template_product_sheet_v1"
            else None
        )
        quality_guard_report = _apply_template_b_parity_to_quality_guard(
            quality_guard_report,
            template_b_parity_review=template_b_parity_review,
        )
        if fg_result.degraded:
            assert_quality_guard_deliverable(
                deliverable=quality_guard_report.deliverable,
                missing_required_slots=quality_guard_report.missing_required_slots,
                missing_mandatory_regions=quality_guard_report.missing_mandatory_regions,
            )

        # ── Phase 3: load background bytes and compose ───────────────────────
        t2 = _now()
        try:
            bg_image = await _run_stage_with_timeout(
                "asset_fetch",
                self._loader.load_url(bg_result.url),
            )
            compose_result = await _run_stage_with_timeout(
                "compose",
                asyncio.to_thread(
                    self._composer.compose,
                    bg_image,
                    fg_result.image,
                    effective_spec.export_format,
                ),
            )
        except PosterGenerationStageError:
            raise
        except Exception as exc:
            raise PosterGenerationStageError(
                "compose",
                "compose_failed",
                "failed to compose final poster",
                detail=str(exc),
                exception_class=exc.__class__.__name__,
            ) from exc
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
        fg_url = await _publish_bytes(
            _put,
            key=fg_key,
            data=fg_result.png_bytes,
            content_type="image/png",
            required=False,
        )
        if not fg_url:
            logger.warning("poster2: R2 upload failed for fg key=%s", fg_key)
            fg_url = ""

        product_material_key = f"poster2/debug/product-material/{trace_id}.png"
        product_material_url = await _publish_bytes(
            _put,
            key=product_material_key,
            data=debug_product_material.png_bytes,
            content_type="image/png",
            required=False,
        )
        if not product_material_url:
            logger.warning("poster2: R2 upload failed for product/material key=%s", product_material_key)
            product_material_url = ""

        ext = effective_spec.export_format
        final_key = f"poster2/final/{trace_id}.{ext}"
        final_url = await _publish_bytes(
            _put,
            key=final_key,
            data=compose_result.png_bytes,
            content_type=f"image/{ext}",
            required=True,
        )

        geometry_evidence = _build_geometry_evidence(
            template,
            resolved_behavior=resolved_behavior,
            layer_render_status=layer_render_status,
            region_render_status=quality_guard_report.region_render_status,
        )
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
            "geometry_evidence": geometry_evidence,
            "hero_contract_review": _build_hero_contract_review(
                template,
                requested_spec=requested_spec,
                effective_spec=effective_spec,
                resolved_behavior=resolved_behavior,
                layer_render_status=layer_render_status,
                region_render_status=quality_guard_report.region_render_status,
            ),
            "product_contract_review": _build_product_contract_review(
                requested_spec=requested_spec,
                effective_spec=effective_spec,
                resolved_behavior=resolved_behavior,
                layer_render_status=layer_render_status,
                region_render_status=quality_guard_report.region_render_status,
                copy_optimization_review=copy_optimization_review,
            ),
            "header_contract_review": _build_header_contract_review(
                template,
                requested_spec=requested_spec,
                effective_spec=effective_spec,
                resolved_behavior=resolved_behavior,
                layer_render_status=layer_render_status,
                region_render_status=quality_guard_report.region_render_status,
            ),
            "feature_contract_review": _build_feature_contract_review(
                template,
                requested_spec=requested_spec,
                effective_spec=effective_spec,
                resolved_behavior=resolved_behavior,
                region_render_status=quality_guard_report.region_render_status,
            ),
            "template_layout_review": {
                "template_layout_policy": resolved_behavior.template_layout_policy.as_dict(),
                "feature_region_response": {
                    "visible_item_count": resolved_behavior.feature_policy.visible_item_count,
                    "box_h": resolved_behavior.feature_policy.box_h,
                    "gap": resolved_behavior.feature_policy.gap,
                    "start_strategy": resolved_behavior.feature_policy.start_strategy,
                },
                "bottom_region_response": {
                    "content_priority_policy": resolved_behavior.bottom_policy.content_priority_policy,
                    "title_band_sizing_mode": resolved_behavior.bottom_policy.title_band_sizing_mode,
                    "gallery_distribution_policy": resolved_behavior.bottom_policy.gallery_distribution_policy,
                    "visible_item_count": resolved_behavior.bottom_policy.visible_item_count,
                },
            },
            "bottom_contract_review": _build_bottom_contract_review(
                template,
                requested_spec=requested_spec,
                effective_spec=effective_spec,
                resolved_behavior=resolved_behavior,
                region_render_status=quality_guard_report.region_render_status,
            ),
            "product_annotation_contract_review": _build_product_annotation_contract_review(
                template,
                requested_spec=requested_spec,
                effective_spec=effective_spec,
                resolved_behavior=resolved_behavior,
                region_render_status=quality_guard_report.region_render_status,
                copy_optimization_review=copy_optimization_review,
            ),
            "scenario_contract_review": _build_scenario_contract_review(
                template,
                requested_spec=requested_spec,
                effective_spec=effective_spec,
                resolved_behavior=resolved_behavior,
                layer_render_status=layer_render_status,
                region_render_status=quality_guard_report.region_render_status,
            ),
            "top_copy_contract_review": _build_top_copy_contract_review(
                template,
                requested_spec=requested_spec,
                effective_spec=effective_spec,
                resolved_behavior=resolved_behavior,
                layer_render_status=layer_render_status,
                region_render_status=quality_guard_report.region_render_status,
            ),
            "description_contract_review": _build_description_contract_review(
                template,
                requested_spec=requested_spec,
                effective_spec=effective_spec,
                resolved_behavior=resolved_behavior,
                layer_render_status=layer_render_status,
                region_render_status=quality_guard_report.region_render_status,
            ),
            "title_text_layer": _build_title_text_layer_evidence(
                template,
                requested_spec=requested_spec,
                effective_spec=effective_spec,
                resolved_behavior=resolved_behavior,
                copy_optimization_review=copy_optimization_review,
            ),
            "subtitle_text_layer": _build_subtitle_text_layer_evidence(
                template,
                requested_spec=requested_spec,
                effective_spec=effective_spec,
                resolved_behavior=resolved_behavior,
                copy_optimization_review=copy_optimization_review,
            ),
            "header_text_layer": _build_header_text_layer_evidence(
                template,
                requested_spec=requested_spec,
                effective_spec=effective_spec,
                resolved_behavior=resolved_behavior,
                layer_render_status=layer_render_status,
            ),
            "copy_optimization_review": copy_optimization_review,
            "visible_truth_evidence": visible_truth_evidence,
            **(
                {"template_b_parity_review": template_b_parity_review}
                if template_b_parity_review is not None
                else {}
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
        renderer_metadata_url = await _publish_bytes(
            _put,
            key=renderer_metadata_key,
            data=json.dumps(renderer_metadata_payload, ensure_ascii=False, sort_keys=True).encode("utf-8"),
            content_type="application/json",
            required=False,
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
            renderer_mode=effective_spec.renderer_mode,
            render_engine_used=fg_result.render_engine_used,
            foreground_renderer=fg_result.foreground_renderer,
            background_renderer=bg_result.model,
            poster_spec_hash=spec_hash,
            resolved_inputs=_summarise_inputs(effective_spec),
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
            geometry_evidence=geometry_evidence,
            hero_contract_review=renderer_metadata_payload["hero_contract_review"],
            product_contract_review=renderer_metadata_payload["product_contract_review"],
            header_contract_review=renderer_metadata_payload["header_contract_review"],
            feature_contract_review=renderer_metadata_payload["feature_contract_review"],
            bottom_contract_review=renderer_metadata_payload["bottom_contract_review"],
            product_annotation_contract_review=renderer_metadata_payload["product_annotation_contract_review"],
            scenario_contract_review=renderer_metadata_payload["scenario_contract_review"],
            top_copy_contract_review=renderer_metadata_payload["top_copy_contract_review"],
            description_contract_review=renderer_metadata_payload["description_contract_review"],
            title_text_layer=renderer_metadata_payload["title_text_layer"],
            subtitle_text_layer=renderer_metadata_payload["subtitle_text_layer"],
            header_text_layer=renderer_metadata_payload["header_text_layer"],
            copy_optimization_review=copy_optimization_review,
            visible_truth_evidence=visible_truth_evidence,
            template_b_parity_review=template_b_parity_review,
        )


# ── helpers ──────────────────────────────────────────────────────────────────

def _now() -> int:
    return time.monotonic_ns()


def _elapsed(t0: int) -> int:
    return (time.monotonic_ns() - t0) // 1_000_000


async def _run_stage_with_timeout(stage: str, awaitable):
    timeout_ms = _DEFAULT_STAGE_TIMEOUTS_MS.get(stage)
    if not timeout_ms:
        return await awaitable
    try:
        return await asyncio.wait_for(awaitable, timeout=timeout_ms / 1000)
    except PosterGenerationStageError:
        raise
    except asyncio.TimeoutError as exc:
        raise PosterGenerationStageError(
            stage,
            f"{stage}_timeout",
            f"{stage} exceeded timeout",
            detail=f"{stage} timed out after {timeout_ms}ms",
            exception_class=exc.__class__.__name__,
            retryable=True,
            timeout_ms=timeout_ms,
        ) from exc


async def _publish_bytes(
    put_bytes_fn,
    *,
    key: str,
    data: bytes,
    content_type: str,
    required: bool,
) -> str:
    try:
        url = await _run_stage_with_timeout(
            "storage_publish",
            asyncio.to_thread(put_bytes_fn, key, data, content_type=content_type),
        )
    except PosterGenerationStageError:
        raise
    except Exception as exc:
        raise PosterGenerationStageError(
            "storage_publish",
            "storage_publish_failed",
            "failed to publish poster artifact",
            detail=str(exc),
            exception_class=exc.__class__.__name__,
            extra={"key": key, "content_type": content_type, "required": required},
        ) from exc
    if url:
        return url
    if required:
        raise PosterGenerationStageError(
            "storage_publish",
            "storage_publish_failed",
            "failed to publish poster artifact",
            detail=f"empty storage URL for key={key}",
            exception_class="RuntimeError",
            extra={"key": key, "content_type": content_type, "required": required},
        )
    return ""


def _hash_spec(spec: PosterSpec) -> str:
    payload = json.dumps(asdict(spec), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _summarise_inputs(spec: PosterSpec) -> dict:
    gallery_counts = _gallery_contract_counts(spec)
    return {
        "brand_name": spec.brand_name,
        "agent_name": spec.agent_name,
        "title": spec.title,
        "template_id": spec.template_id,
        "renderer_mode": spec.renderer_mode,
        "product_url": spec.product_image.url,
        "gallery_count": len(spec.gallery_images),
        "gallery_requested_count": int(gallery_counts["requested"]),
        "gallery_input_count_raw": int(gallery_counts["raw"]),
        "gallery_input_count_normalized": int(gallery_counts["normalized"]),
        "gallery_autofill_applied": bool(gallery_counts["autofill_applied"]),
        "seed": spec.style.seed,
    }


def _normalize_requested_text(value: str) -> str:
    return value.strip() if isinstance(value, str) else ""


_INVALID_TEXT_CHAR_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def _normalize_hygiene_only_text(value: str) -> str:
    text = _normalize_requested_text(value)
    if not text:
        return ""
    text = _INVALID_TEXT_CHAR_RE.sub("", text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    text = re.sub(r"\s+([,;:!?])", r"\1", text)
    text = re.sub(r"([!?.,;:]){2,}", r"\1", text)
    return text.strip()


def _is_template_b_template(template: TemplateSpec) -> bool:
    return template.template_id.startswith("template_product_sheet")


def _clamp_gallery_count(value: int | None) -> int:
    if value is None:
        return 0
    return max(0, min(int(value), 4))


def _gallery_contract_counts(spec: PosterSpec) -> dict[str, object]:
    actual_count = min(len(spec.gallery_images), 4)
    requested_count = _clamp_gallery_count(
        spec.gallery_requested_count if spec.gallery_requested_count is not None else actual_count
    )
    raw_count = _clamp_gallery_count(
        spec.gallery_input_count_raw if spec.gallery_input_count_raw is not None else requested_count
    )
    normalized_count = _clamp_gallery_count(
        spec.gallery_input_count_normalized if spec.gallery_input_count_normalized is not None else actual_count
    )
    normalized_count = min(normalized_count, requested_count if requested_count else 4)
    return {
        "raw": raw_count,
        "normalized": normalized_count,
        "requested": requested_count,
        "actual": actual_count,
        "autofill_applied": bool(spec.gallery_autofill_applied),
    }


def _normalize_contract_text_spec(spec: PosterSpec, template=None) -> PosterSpec:
    brand_name = _normalize_requested_text(spec.brand_name)
    agent_name = _normalize_requested_text(spec.agent_name)
    title = normalize_marketing_title(_normalize_requested_text(spec.title))
    subtitle_requested = _normalize_requested_text(spec.subtitle)
    if (template.template_id if template else spec.template_id) == "template_dual_v2":
        subtitle = subtitle_requested
    else:
        subtitle = normalize_marketing_subtitle(
            subtitle_requested,
            title=title,
        )
    sku_text = _normalize_requested_text(spec.sku_text)
    description_title = normalize_marketing_title(_normalize_requested_text(spec.description_title))
    description_body = _normalize_requested_text(spec.description_body)
    if (template.template_id if template else spec.template_id) == "template_dual_v2":
        features = tuple(
            normalized
            for item in spec.features
            if (normalized := _normalize_hygiene_only_text(item))
        )
    else:
        features = tuple(
            normalized
            for item in spec.features
            if (normalized := _normalize_requested_text(item))
        )
    if not brand_name:
        raise ValueError("brand_name must not be empty after normalization")
    # gallery_only collapses the title band by design; title is not required for this mode.
    requested_mode = spec.bottom_mode or (template.behavior_modes.bottom_mode if template else None)
    title_required = requested_mode != "gallery_only"
    if not title and title_required:
        raise ValueError("title must not be empty after normalization")
    gallery_counts = _gallery_contract_counts(spec)
    return replace(
        spec,
        brand_name=brand_name,
        agent_name=agent_name,
        title=title,
        subtitle=subtitle,
        sku_text=sku_text,
        description_title=description_title,
        description_body=description_body,
        features=features,
        gallery_images=tuple(spec.gallery_images[: gallery_counts["requested"] or gallery_counts["actual"]]),
        gallery_input_count_raw=gallery_counts["raw"],
        gallery_input_count_normalized=gallery_counts["normalized"],
        gallery_requested_count=gallery_counts["requested"],
        gallery_autofill_applied=bool(gallery_counts["autofill_applied"]),
    )


def _apply_text_budget(text: str, budget: int) -> str:
    if not text or budget <= 0:
        return text
    if len(text) <= budget:
        return text
    return text[:budget]


def _apply_text_budget_word_safe(text: str, budget: int) -> str:
    """Truncate to budget at a word boundary and append ellipsis.

    Prefers truncating at the last space within budget so no partial word
    is visible.  Only falls back to the hard character boundary when no
    usable space is found within the last 30 % of the budget.
    """
    if not text or budget <= 0:
        return text
    if len(text) <= budget:
        return text
    truncated = text[:budget]
    last_space = truncated.rfind(" ")
    if last_space >= int(budget * 0.7):
        truncated = truncated[:last_space]
    return truncated + "\u2026"


def _build_layer_render_status(
    *,
    template: TemplateSpec,
    spec: PosterSpec,
    assets,
    bg_result: BackgroundResult,
    behavior,
) -> dict[str, dict[str, object]]:
    if _is_template_b_template(template):
        logo_suppressed_by_mode = behavior.header_policy.identity_zone_mode == "brand_only"
        logo_rendered = assets.logo is not None and not logo_suppressed_by_mode
        sku_rendered = bool((spec.sku_text or "").strip())
        title_rendered = bool(behavior.top_copy_policy and behavior.top_copy_policy.title_present)
        subtitle_rendered = bool(behavior.top_copy_policy and behavior.top_copy_policy.subtitle_present)
        materials_rendered = bool(behavior.materials_policy and behavior.materials_policy.rendered and assets.materials)
        product_rendered = assets.product is not None
        secondary_rendered = (
            assets.product_secondary is not None
            and behavior.product_policy.product_secondary_slot_rendered
        )
        description_title_rendered = bool(behavior.description_policy and behavior.description_policy.title_present)
        description_body_rendered = bool(behavior.description_policy and behavior.description_policy.body_present)
        description_rendered = bool(behavior.description_policy and behavior.description_policy.rendered)
        return {
            "background_base_layer": {
                "rendered": True,
                "reason_code": None,
                "source_binding": bg_result.url,
                "count": 1,
            },
            "header_shell_layer": {
                "rendered": True,
                "reason_code": None,
                "source_binding": "template_product_sheet_v1.logo_banner_region",
                "count": 1,
            },
            "brand_logo_layer": {
                "rendered": logo_rendered,
                "reason_code": (
                    None
                    if logo_rendered
                    else ("logo_suppressed_by_header_mode" if logo_suppressed_by_mode else "logo_missing")
                ),
                "source_binding": spec.logo.url if spec.logo else None,
                "count": 1 if logo_rendered else 0,
                "collapsed": not logo_rendered,
            },
            "brand_text_layer": {
                "rendered": bool(spec.brand_name),
                "reason_code": None if spec.brand_name else "brand_name_empty",
                "source_binding": "request.brand_name",
                "count": 1 if spec.brand_name else 0,
                "collapsed": not bool(spec.brand_name),
            },
            "agent_name_text_layer": {
                "rendered": behavior.header_policy.agent_pill_visible,
                "reason_code": (
                    None
                    if behavior.header_policy.agent_pill_visible
                    else ("agent_name_empty" if not spec.agent_name else "suppressed_by_header_mode")
                ),
                "source_binding": "request.agent_name",
                "count": 1 if behavior.header_policy.agent_pill_visible else 0,
                "collapsed": not behavior.header_policy.agent_pill_visible,
            },
            "scenario_image_layer": {
                "rendered": False,
                "reason_code": "scenario_disabled_for_template_b",
                "source_binding": None,
                "count": 0,
                "collapsed": True,
            },
            "top_copy_title_layer": {
                "rendered": title_rendered,
                "reason_code": None if title_rendered else "title_empty",
                "source_binding": "title",
                "count": 1 if title_rendered else 0,
                "collapsed": not title_rendered,
            },
            "sku_text_layer": {
                "rendered": sku_rendered,
                "reason_code": None if sku_rendered else "sku_text_empty",
                "source_binding": "sku_text",
                "count": 1 if sku_rendered else 0,
                "collapsed": not sku_rendered,
            },
            "top_copy_subtitle_layer": {
                "rendered": subtitle_rendered,
                "reason_code": None if subtitle_rendered else "subtitle_empty",
                "source_binding": "subtitle",
                "count": 1 if subtitle_rendered else 0,
                "collapsed": not subtitle_rendered,
            },
            "materials_items_layer": {
                "rendered": materials_rendered,
                "reason_code": None if materials_rendered else "materials_empty",
                "source_binding": "materials_images",
                "count": len(assets.materials) if materials_rendered else 0,
                "collapsed": not materials_rendered,
            },
            "product_card_shell_layer": {
                "rendered": True,
                "reason_code": None,
                "source_binding": "template_product_sheet_v1.product_hero_region",
                "count": 1,
            },
            "product_canvas_shell_layer": {
                "rendered": True,
                "reason_code": None,
                "source_binding": "template_product_sheet_v1.product_hero_region",
                "count": 1,
            },
            "product_text_shell_layer": {
                "rendered": False,
                "reason_code": "not_used_in_template_b",
                "source_binding": None,
                "count": 0,
                "collapsed": True,
            },
            "product_image_layer": {
                "rendered": product_rendered,
                "reason_code": None if product_rendered else "product_image_missing",
                "source_binding": spec.product_image.url,
                "count": 1 if product_rendered else 0,
                "collapsed": not product_rendered,
            },
            "product_secondary_image_layer": {
                "rendered": secondary_rendered,
                "reason_code": (
                    None
                    if secondary_rendered
                    else (
                        "secondary_slot_not_active"
                        if not behavior.product_policy.product_secondary_slot_rendered
                        else "secondary_image_missing"
                    )
                ),
                "source_binding": spec.product_secondary_image.url if spec.product_secondary_image else None,
                "count": 1 if secondary_rendered else 0,
                "collapsed": not secondary_rendered,
            },
            "product_annotation_shell_layer": {
                "rendered": False,
                "reason_code": "annotation_mode_none",
                "source_binding": behavior.product_policy.annotation_mode,
                "count": 0,
                "collapsed": True,
            },
            "product_annotation_items_layer": {
                "rendered": False,
                "reason_code": "annotation_mode_none",
                "source_binding": "features",
                "count": 0,
                "collapsed": True,
            },
            "feature_callout_layer": {
                "rendered": False,
                "reason_code": "feature_mode_disabled_for_template_b",
                "source_binding": "features",
                "count": 0,
                "collapsed": True,
            },
            "description_title_layer": {
                "rendered": description_title_rendered,
                "reason_code": None if description_title_rendered else "description_title_empty",
                "source_binding": "description_title",
                "count": 1 if description_title_rendered else 0,
                "collapsed": not description_title_rendered,
            },
            "description_body_layer": {
                "rendered": description_body_rendered,
                "reason_code": None if description_body_rendered else "description_body_empty",
                "source_binding": "description_body",
                "count": 1 if description_body_rendered else 0,
                "collapsed": not description_body_rendered,
            },
            "description_region_shell_layer": {
                "rendered": description_rendered,
                "reason_code": None if description_rendered else "description_empty",
                "source_binding": "description_region",
                "count": 1 if description_rendered else 0,
                "collapsed": not description_rendered,
            },
        }

    gallery_counts = _gallery_contract_counts(spec)
    gallery_requested = int(gallery_counts["requested"])
    gallery_input_raw = int(gallery_counts["raw"])
    gallery_input_normalized = int(gallery_counts["normalized"])
    gallery_autofill_applied = bool(gallery_counts["autofill_applied"])
    gallery_valid = min(len(assets.gallery), 4)
    gallery_rendered = behavior.bottom_policy.gallery_strip_rendered and gallery_valid > 0
    feature_count = min(len([item for item in spec.features if item and item.strip()]), len(template.feature_callouts))
    annotation_active = behavior.product_policy.annotation_mode == "product_anchor_callouts"
    product_annotation_visible = min(
        behavior.product_policy.visible_annotation_count,
        len([item for item in spec.features if item and item.strip()]),
    )
    product_annotation_rendered = annotation_active and product_annotation_visible > 0
    delegated_feature_rendering = annotation_active
    visible_feature_count = 0 if delegated_feature_rendering else feature_count
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
            "source_binding": "request.brand_name",
            "count": 1 if spec.brand_name else 0,
            "collapsed": not bool(spec.brand_name),
        },
        "agent_name_text_layer": {
            "rendered": behavior.header_policy.agent_pill_visible,
            "reason_code": (
                None if behavior.header_policy.agent_pill_visible
                else ("agent_name_empty" if not spec.agent_name else "suppressed_by_header_mode")
            ),
            "source_binding": "request.agent_name",
            "count": 1 if behavior.header_policy.agent_pill_visible else 0,
            "collapsed": not behavior.header_policy.agent_pill_visible,
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
        "product_canvas_shell_layer": {
            "rendered": True,
            "reason_code": None,
            "source_binding": "template_dual_v2.product_canvas_shell",
            "count": 1,
        },
        "product_text_shell_layer": {
            "rendered": behavior.product_policy.annotation_mode != "none",
            "reason_code": (
                "annotation_mode_none"
                if behavior.product_policy.annotation_mode == "none"
                else None
            ),
            "source_binding": "product_region.product_text_shell",
            "count": 1 if behavior.product_policy.annotation_mode != "none" else 0,
            "collapsed": behavior.product_policy.annotation_mode == "none",
        },
        "product_image_layer": {
            "rendered": assets.product is not None,
            "reason_code": None if assets.product is not None else "product_image_missing",
            "source_binding": spec.product_image.url,
            "count": 1 if assets.product is not None else 0,
        },
        "product_secondary_image_layer": {
            "rendered": assets.product_secondary is not None and behavior.product_policy.product_secondary_slot_rendered,
            "reason_code": (
                None
                if assets.product_secondary is not None and behavior.product_policy.product_secondary_slot_rendered
                else (
                    "secondary_slot_not_active"
                    if not behavior.product_policy.product_secondary_slot_rendered
                    else "secondary_image_missing"
                )
            ),
            "source_binding": spec.product_secondary_image.url if spec.product_secondary_image else None,
            "count": 1 if (assets.product_secondary is not None and behavior.product_policy.product_secondary_slot_rendered) else 0,
        },
        "product_support_surface_layer": {
            "rendered": bool(behavior.product_policy.product_support_surface_rendered and assets.gallery),
            "reason_code": (
                None
                if behavior.product_policy.product_support_surface_rendered and assets.gallery
                else (
                    "bottom_gallery_item_1_unavailable"
                    if behavior.product_policy.product_support_surface_source == "bottom_gallery_item_1_unavailable"
                    else "support_surface_inactive"
                )
            ),
            "source_binding": (
                spec.gallery_images[0].url
                if behavior.product_policy.product_support_surface_rendered and spec.gallery_images
                else behavior.product_policy.product_support_surface_source
            ),
            "count": 1 if behavior.product_policy.product_support_surface_rendered and assets.gallery else 0,
            "collapsed": not bool(behavior.product_policy.product_support_surface_rendered and assets.gallery),
        },
        "product_annotation_shell_layer": {
            "rendered": product_annotation_rendered,
            "reason_code": (
                None
                if product_annotation_rendered
                else (
                    "annotation_mode_none"
                    if behavior.product_policy.annotation_mode == "none"
                    else (
                        "annotation_items_empty"
                        if product_annotation_visible == 0
                        else "annotation_renderer_pending"
                    )
                )
            ),
            "source_binding": behavior.product_policy.annotation_mode,
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
                    if behavior.product_policy.annotation_mode == "none"
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
            "gallery_input_count_raw": gallery_input_raw,
            "gallery_input_count_normalized": gallery_input_normalized,
            "count_requested": gallery_requested,
            "count_valid": gallery_valid,
            "gallery_autofill_applied": gallery_autofill_applied,
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
            "gallery_input_count_raw": gallery_input_raw,
            "gallery_input_count_normalized": gallery_input_normalized,
            "count_requested": gallery_requested,
            "count_valid": gallery_valid,
            "count_visible": behavior.bottom_policy.visible_item_count,
            "gallery_autofill_applied": gallery_autofill_applied,
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
    template: TemplateSpec,
    layer_status: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    if _is_template_b_template(template):
        banner_count = sum(
            int(layer_status.get(layer_name, {}).get("count", 0))
            for layer_name in ("brand_logo_layer", "brand_text_layer", "agent_name_text_layer")
        )
        top_copy_count = sum(
            int(layer_status.get(layer_name, {}).get("count", 0))
            for layer_name in ("sku_text_layer", "top_copy_title_layer", "top_copy_subtitle_layer")
        )
        materials_count = int(layer_status.get("materials_items_layer", {}).get("count", 0))
        hero_count = (
            int(layer_status.get("product_image_layer", {}).get("count", 0))
            + int(layer_status.get("product_secondary_image_layer", {}).get("count", 0))
        )
        description_count = (
            int(layer_status.get("description_title_layer", {}).get("count", 0))
            + int(layer_status.get("description_body_layer", {}).get("count", 0))
        )
        return {
            "logo_banner_region": {
                "rendered": banner_count > 0,
                "count": banner_count,
                "collapsed": banner_count == 0,
            },
            "top_copy_region": {
                "rendered": top_copy_count > 0,
                "count": top_copy_count,
                "collapsed": top_copy_count == 0,
            },
            "materials_strip_region": {
                "rendered": materials_count > 0,
                "count": materials_count,
                "collapsed": materials_count == 0,
            },
            "product_hero_region": {
                "rendered": hero_count > 0,
                "count": hero_count,
                "collapsed": hero_count == 0,
            },
            "description_region": {
                "rendered": description_count > 0,
                "count": description_count,
                "collapsed": description_count == 0,
            },
        }

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


def _template_b_top_copy_region_bounds(template: TemplateSpec) -> dict[str, int]:
    left = min(
        int(template.title_slot.x) - 16,
        int(template.subtitle_slot.x) - 56 if template.subtitle_slot else int(template.title_slot.x) - 16,
    )
    top = int(template.title_slot.y) - 8
    right = max(
        int(template.title_slot.x + template.title_slot.w) + 16,
        int(template.subtitle_slot.x + template.subtitle_slot.w) + 56
        if template.subtitle_slot
        else int(template.title_slot.x + template.title_slot.w) + 16,
    )
    bottom = (
        int(template.materials_slot.y) - 12
        if template.materials_slot
        else int(template.product_slot.y) - 16
    )
    return {"x": left, "y": top, "w": right - left, "h": max(bottom - top, 0)}


def _template_b_description_region_bounds(template: TemplateSpec) -> dict[str, int]:
    left = min(
        int(template.description_title_slot.x) - 16 if template.description_title_slot else template.canvas_w,
        int(template.description_body_slot.x) - 32 if template.description_body_slot else template.canvas_w,
    )
    if left == template.canvas_w:
        left = int(template.safe_margin)
    top_candidates = []
    if template.description_title_slot:
        top_candidates.append(int(template.description_title_slot.y) - 8)
    if template.description_body_slot:
        top_candidates.append(int(template.description_body_slot.y) - 56)
    top = min(top_candidates) if top_candidates else int(template.canvas_h - template.safe_margin)
    right_candidates = []
    if template.description_title_slot:
        right_candidates.append(int(template.description_title_slot.x + template.description_title_slot.w) + 16)
    if template.description_body_slot:
        right_candidates.append(int(template.description_body_slot.x + template.description_body_slot.w) + 32)
    right = max(right_candidates) if right_candidates else int(template.canvas_w - template.safe_margin)
    bottom = int(template.canvas_h - template.safe_margin)
    return {"x": left, "y": top, "w": max(right - left, 0), "h": max(bottom - top, 0)}


def _template_b_sku_slot_bounds(template: TemplateSpec) -> dict[str, int]:
    return {
        "x": int(template.title_slot.x),
        "y": max(int(template.title_slot.y) - 4, 0),
        "w": int(template.title_slot.w),
        "h": 20,
    }


def _build_geometry_evidence(
    template: TemplateSpec,
    *,
    resolved_behavior,
    layer_render_status: dict[str, dict[str, object]],
    region_render_status: dict[str, dict[str, object]],
) -> dict[str, object]:
    if _is_template_b_template(template):
        return {
            "region_bounds": {
                "logo_banner_region": _header_region_bounds(template, resolved_behavior),
                "top_copy_region": _template_b_top_copy_region_bounds(template),
                "materials_strip_region": _slot_bounds(template.materials_slot) if template.materials_slot else {"x": 0, "y": 0, "w": 0, "h": 0},
                "product_hero_region": _product_region_bounds(template, resolved_behavior),
                "description_region": _template_b_description_region_bounds(template),
            },
            "slot_bounds": {
                "brand_logo_slot": _header_logo_slot_bounds(template, resolved_behavior),
                "brand_name_slot": _brand_name_slot_bounds(template, resolved_behavior),
                "agent_name_slot": _agent_name_slot_bounds(template, resolved_behavior),
                "sku_text_slot": _template_b_sku_slot_bounds(template),
                "title_slot": _text_slot_bounds(template.title_slot),
                "subtitle_slot": _text_slot_bounds(template.subtitle_slot),
                "product_slot": _product_slot_bounds(template, resolved_behavior),
                "product_primary_slot": _product_primary_slot_bounds(resolved_behavior),
                "product_secondary_slot": _product_secondary_slot_bounds(resolved_behavior),
                "description_title_slot": _text_slot_bounds(template.description_title_slot) if template.description_title_slot else {"x": 0, "y": 0, "w": 0, "h": 0},
                "description_body_slot": _text_slot_bounds(template.description_body_slot) if template.description_body_slot else {"x": 0, "y": 0, "w": 0, "h": 0},
            },
            "visible_item_count": {
                "logo_banner_region": int(region_render_status.get("logo_banner_region", {}).get("count", 0)),
                "top_copy_region": int(region_render_status.get("top_copy_region", {}).get("count", 0)),
                "materials_strip_region": int(region_render_status.get("materials_strip_region", {}).get("count", 0)),
                "product_hero_region": int(region_render_status.get("product_hero_region", {}).get("count", 0)),
                "description_region": int(region_render_status.get("description_region", {}).get("count", 0)),
            },
        }

    return build_family_a_structure_surface(
        template,
        resolved_behavior=resolved_behavior,
        layer_render_status=layer_render_status,
        region_render_status=region_render_status,
    )


def _bounds_contains(container: dict[str, int], child: dict[str, int] | None) -> bool:
    if not child:
        return False
    if child.get("w", 0) <= 0 or child.get("h", 0) <= 0:
        return False
    return (
        int(child["x"]) >= int(container["x"])
        and int(child["y"]) >= int(container["y"])
        and int(child["x"]) + int(child["w"]) <= int(container["x"]) + int(container["w"])
        and int(child["y"]) + int(child["h"]) <= int(container["y"]) + int(container["h"])
    )


def _parity_target_review(
    *,
    target_key: str,
    region_key: str,
    visible_truth_evidence: dict[str, object],
    geometry_evidence: dict[str, object],
) -> dict[str, object]:
    region_bounds = dict((geometry_evidence.get("region_bounds") or {}).get(region_key) or {})
    target = dict(visible_truth_evidence.get(target_key) or {})
    visible_bounds = target.get("visible_bounds")
    contained = _bounds_contains(region_bounds, visible_bounds) if region_bounds else False
    return {
        "target_key": target_key,
        "region_key": region_key,
        "rendered": bool(target.get("rendered", False)),
        "visible_bounds": visible_bounds,
        "layout_bounds": target.get("layout_bounds"),
        "region_bounds": region_bounds,
        "inside_region": contained,
        "overflow_state": target.get("overflow_state"),
        "clipping_state": target.get("clipping_state"),
        "computed_opacity": target.get("computed_opacity"),
        "stacking_context": target.get("stacking_context"),
        "transform_summary": target.get("transform_summary"),
        "reason_code": target.get("reason_code"),
    }


def _parity_passes_when_rendered(target: dict[str, object]) -> bool:
    return (not bool(target.get("rendered", False))) or bool(target.get("inside_region", False))


def _build_template_b_parity_review(
    template: TemplateSpec,
    *,
    visible_truth_evidence: dict[str, object],
    geometry_evidence: dict[str, object],
) -> dict[str, object]:
    if not _is_template_b_template(template):
        return {}

    if not visible_truth_evidence:
        return {
            "parity_enabled": False,
            "parity_passed": False,
            "parity_failure_reasons": ["visible_truth_evidence_missing"],
            "header_in_banner": False,
            "top_copy_in_region": False,
            "hero_in_region": False,
            "description_in_region": False,
            "targets": {},
        }

    targets = {
        "brand_logo_slot": _parity_target_review(
            target_key="brand_logo_slot",
            region_key="logo_banner_region",
            visible_truth_evidence=visible_truth_evidence,
            geometry_evidence=geometry_evidence,
        ),
        "brand_name_slot": _parity_target_review(
            target_key="brand_name_slot",
            region_key="logo_banner_region",
            visible_truth_evidence=visible_truth_evidence,
            geometry_evidence=geometry_evidence,
        ),
        "sku_text_layer": _parity_target_review(
            target_key="sku_text_layer",
            region_key="top_copy_region",
            visible_truth_evidence=visible_truth_evidence,
            geometry_evidence=geometry_evidence,
        ),
        "top_copy_title_layer": _parity_target_review(
            target_key="top_copy_title_layer",
            region_key="top_copy_region",
            visible_truth_evidence=visible_truth_evidence,
            geometry_evidence=geometry_evidence,
        ),
        "top_copy_subtitle_layer": _parity_target_review(
            target_key="top_copy_subtitle_layer",
            region_key="top_copy_region",
            visible_truth_evidence=visible_truth_evidence,
            geometry_evidence=geometry_evidence,
        ),
        "product_primary_image": _parity_target_review(
            target_key="product_primary_image",
            region_key="product_hero_region",
            visible_truth_evidence=visible_truth_evidence,
            geometry_evidence=geometry_evidence,
        ),
        "product_secondary_inset": _parity_target_review(
            target_key="product_secondary_inset",
            region_key="product_hero_region",
            visible_truth_evidence=visible_truth_evidence,
            geometry_evidence=geometry_evidence,
        ),
        "description_title_layer": _parity_target_review(
            target_key="description_title_layer",
            region_key="description_region",
            visible_truth_evidence=visible_truth_evidence,
            geometry_evidence=geometry_evidence,
        ),
        "description_body_layer": _parity_target_review(
            target_key="description_body_layer",
            region_key="description_region",
            visible_truth_evidence=visible_truth_evidence,
            geometry_evidence=geometry_evidence,
        ),
    }

    failures: list[str] = []
    if not _parity_passes_when_rendered(targets["brand_logo_slot"]):
        failures.append("brand_logo_slot_outside_logo_banner_region")
    if not _parity_passes_when_rendered(targets["brand_name_slot"]):
        failures.append("brand_name_slot_outside_logo_banner_region")
    if not all(_parity_passes_when_rendered(targets[key]) for key in ("sku_text_layer", "top_copy_title_layer", "top_copy_subtitle_layer")):
        failures.append("top_copy_content_outside_top_copy_region")
    if not _parity_passes_when_rendered(targets["product_primary_image"]):
        failures.append("product_primary_image_outside_product_hero_region")
    if not _parity_passes_when_rendered(targets["product_secondary_inset"]):
        failures.append("product_secondary_inset_outside_product_hero_region")
    if not all(_parity_passes_when_rendered(targets[key]) for key in ("description_title_layer", "description_body_layer")):
        failures.append("description_content_outside_description_region")

    return {
        "parity_enabled": True,
        "parity_passed": not failures,
        "parity_failure_reasons": failures,
        "header_in_banner": all(_parity_passes_when_rendered(targets[key]) for key in ("brand_logo_slot", "brand_name_slot")),
        "top_copy_in_region": all(_parity_passes_when_rendered(targets[key]) for key in ("sku_text_layer", "top_copy_title_layer", "top_copy_subtitle_layer")),
        "hero_in_region": _parity_passes_when_rendered(targets["product_primary_image"]) and (
            _parity_passes_when_rendered(targets["product_secondary_inset"])
        ),
        "description_in_region": all(_parity_passes_when_rendered(targets[key]) for key in ("description_title_layer", "description_body_layer")),
        "targets": targets,
    }


def _apply_template_b_parity_to_quality_guard(
    report,
    *,
    template_b_parity_review: dict[str, object] | None,
):
    if not template_b_parity_review:
        return report
    failures = list(template_b_parity_review.get("parity_failure_reasons") or [])
    if not failures:
        return report
    missing_regions = sorted(set(report.missing_mandatory_regions) | {"template_b_visual_parity"})
    return replace(
        report,
        structure_complete=False,
        incomplete_structure=True,
        deliverable=False,
        structure_evidence_complete=False,
        missing_mandatory_regions=missing_regions,
    )


def _slot_bounds(slot) -> dict[str, int]:
    return {"x": int(slot.x), "y": int(slot.y), "w": int(slot.w), "h": int(slot.h)}


def _text_slot_bounds(slot) -> dict[str, int]:
    return {"x": int(slot.x), "y": int(slot.y), "w": int(slot.w), "h": int(slot.h)}


def _header_region_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    metrics = resolved_behavior.header_policy.layout_metrics
    return {
        "x": int(metrics["header_banner_left"]),
        "y": int(metrics["header_banner_top"]),
        "w": int(metrics["header_banner_width"]),
        "h": int(metrics["header_banner_height"]),
    }


def _header_logo_slot_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    metrics = resolved_behavior.header_policy.layout_metrics
    return {
        "x": int(template.logo_slot.x),
        "y": int(template.logo_slot.y),
        "w": int(metrics["header_logo_width"]),
        "h": int(metrics["header_logo_height"]),
    }


def _brand_name_slot_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    metrics = resolved_behavior.header_policy.layout_metrics
    return {
        "x": int(metrics["brand_slot_x"]),
        "y": int(metrics["brand_slot_y"]),
        "w": int(metrics["brand_slot_w"]),
        "h": int(metrics["brand_slot_h"]),
    }


def _agent_name_slot_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    metrics = resolved_behavior.header_policy.layout_metrics
    return {
        "x": int(metrics["agent_slot_x"]),
        "y": int(metrics["agent_slot_y"]),
        "w": int(metrics["agent_slot_w"]),
        "h": int(metrics["agent_slot_h"]),
    }


def _bottom_region_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    layout = resolved_behavior.bottom_policy.layout_metrics
    return {
        "x": 96,
        "y": int(layout.get("bottom_shell_top", 0)),
        "w": 832,
        "h": int(layout.get("bottom_shell_height", layout.get("bottom_shell_h", 0))),
    }


def _scenario_region_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    metrics = resolved_behavior.hero_policy.layout_metrics
    return {
        "x": int(metrics["scenario_region_x"]),
        "y": int(metrics["scenario_region_y"]),
        "w": int(metrics["scenario_region_w"]),
        "h": int(metrics["scenario_region_h"]),
    }


def _product_region_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    product_policy = getattr(resolved_behavior, "product_policy", None)
    metrics = getattr(product_policy, "layout_metrics", None) or resolved_behavior.hero_policy.layout_metrics
    return {
        "x": int(metrics["product_region_x"]),
        "y": int(metrics["product_region_y"]),
        "w": int(metrics["product_region_w"]),
        "h": int(metrics["product_region_h"]),
    }


def _scenario_slot_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    if template.scenario_slot is None:
        return {"x": 0, "y": 0, "w": 0, "h": 0}
    bounds = _scenario_region_bounds(template, resolved_behavior)
    return bounds


def _product_slot_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    return _product_primary_slot_bounds(resolved_behavior)


def _product_primary_slot_bounds(resolved_behavior) -> dict[str, int]:
    primary = resolved_behavior.product_policy.product_primary_slot
    return {
        "x": int(primary["x"]),
        "y": int(primary["y"]),
        "w": int(primary["w"]),
        "h": int(primary["h"]),
    }


def _product_secondary_slot_bounds(resolved_behavior) -> dict[str, int]:
    secondary = resolved_behavior.product_policy.product_secondary_slot
    if secondary is None:
        return {"x": 0, "y": 0, "w": 0, "h": 0}
    return {
        "x": int(secondary["x"]),
        "y": int(secondary["y"]),
        "w": int(secondary["w"]),
        "h": int(secondary["h"]),
    }


def _title_band_region_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    layout = resolved_behavior.bottom_policy.layout_metrics
    return {
        "x": int(layout.get("title_band_x", 112)),
        "y": int(layout["title_band_top"]),
        "w": int(layout.get("title_band_w", 800)),
        "h": int(layout["title_band_height"]),
    }


def _gallery_strip_region_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    layout = resolved_behavior.bottom_policy.layout_metrics
    return {
        "x": int(layout.get("gallery_shell_x", template.gallery_slot.x)),
        "y": int(layout.get("gallery_shell_top", template.gallery_slot.y)),
        "w": int(layout.get("gallery_shell_w", template.gallery_slot.w)),
        "h": int(layout.get("gallery_shell_height", template.gallery_slot.h)),
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
        "x": int(layout.get("title_band_x", template.title_slot.x)),
        "y": int(layout.get("title_slot_y", template.title_slot.y)),
        "w": int(layout.get("title_band_w", template.title_slot.w)),
        "h": int(layout.get("title_slot_height", template.title_slot.h)),
    }


def _subtitle_slot_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    layout = resolved_behavior.bottom_policy.layout_metrics
    return {
        "x": int(layout.get("subtitle_slot_x", template.subtitle_slot.x)),
        "y": int(layout.get("subtitle_slot_y", template.subtitle_slot.y)),
        "w": int(layout.get("subtitle_slot_w", template.subtitle_slot.w)),
        "h": int(layout.get("subtitle_slot_height", template.subtitle_slot.h)),
    }


def _build_bottom_contract_review(
    template: TemplateSpec,
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
    region_render_status: dict[str, dict[str, object]],
) -> dict[str, object]:
    if _is_template_b_template(template):
        requested_bottom_mode = requested_spec.bottom_mode
        effective_bottom_mode = resolved_behavior.bottom_policy.effective_mode
        bottom_mode_remapped = requested_bottom_mode not in (None, effective_bottom_mode)
        return {
            "requested_bottom_mode": requested_bottom_mode,
            "effective_bottom_mode": effective_bottom_mode,
            "bottom_mode": effective_bottom_mode,
            "bottom_mode_remapped": bottom_mode_remapped,
            "bottom_mode_alias": (
                f"{requested_bottom_mode} → {effective_bottom_mode}"
                if bottom_mode_remapped
                else None
            ),
            "bottom_mode_override_reason": resolved_behavior.bottom_policy.mode_override_reason,
            "bottom_layout_mode": resolved_behavior.bottom_policy.bottom_layout_mode,
            "bottom_contract_scope": "description_region_only",
            "gallery_mode": "none",
            "gallery_input_count_raw": 0,
            "gallery_input_count_normalized": 0,
            "gallery_requested_count": 0,
            "gallery_visible_count": 0,
            "gallery_autofill_applied": False,
            "requested_title_text": None,
            "requested_subtitle_text": None,
            "sanitized_title_text": None,
            "sanitized_subtitle_text": None,
            "rendered_title_excerpt": "",
            "rendered_subtitle_excerpt": "",
            "title_truncation_applied": False,
            "subtitle_truncation_applied": False,
            "title_source": None,
            "subtitle_source": None,
            "description_region": {
                "rendered": bool(region_render_status.get("description_region", {}).get("rendered", False)),
                "bounds": _template_b_description_region_bounds(template),
            },
            "gallery_caption_mode": "none",
            "caption_owner": "gallery_strip_region",
            "behavior_policy": {
                "content_priority_policy": resolved_behavior.bottom_policy.content_priority_policy,
                "peer_balance_policy": resolved_behavior.bottom_policy.peer_balance_policy,
                "bottom_peer_balance_policy": resolved_behavior.bottom_policy.bottom_peer_balance_policy,
                "gallery_caption_mode": "none",
                "gallery_caption_owner": "gallery_strip_region",
                "layout_metrics": dict(resolved_behavior.bottom_policy.layout_metrics),
            },
            "collapsed_optional_slots": list(resolved_behavior.bottom_policy.collapsed_optional_slots),
            "gallery_slots": {},
            "gallery_caption_slots": {},
            "semantic_owner_exclusions": {
                "sku_text": "top_copy_region",
                "title": "top_copy_region",
                "subtitle": "top_copy_region",
            },
            "bottom_mode_region_contract": {
                "effective_bottom_mode": effective_bottom_mode,
                "description_region_owner": True,
                "title_subtitle_owner_region": "top_copy_region",
                "sku_owner_region": "top_copy_region",
                "collapsed_by_design_regions": ["gallery_strip_region", "title_band_region"],
            },
        }

    gallery_counts = _gallery_contract_counts(effective_spec)
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
    gallery_caption_slots = {
        slot_state["slot_id"]: {
            "rendered": bool(slot_state.get("rendered", False)),
            "caption_text": slot_state.get("caption_text", ""),
            "owner_region": slot_state.get("owner_region"),
            "item_slot_id": slot_state.get("item_slot_id"),
            "bounds": slot_state.get("bounds"),
            "local_bounds": slot_state.get("local_bounds"),
            "media_bounds": slot_state.get("media_bounds"),
            "media_local_bounds": slot_state.get("media_local_bounds"),
            "card_bounds": slot_state.get("card_bounds"),
            "card_local_bounds": slot_state.get("card_local_bounds"),
        }
        for slot_state in resolved_behavior.bottom_policy.gallery_caption_slots
    }
    rendered_title_excerpt = (
        _apply_text_budget(effective_spec.title, resolved_behavior.bottom_policy.title_char_budget)
        if resolved_behavior.bottom_policy.title_slot_rendered
        else ""
    )
    rendered_subtitle_excerpt = (
        _apply_text_budget(effective_spec.subtitle, resolved_behavior.bottom_policy.subtitle_char_budget)
        if resolved_behavior.bottom_policy.subtitle_slot_rendered
        else ""
    )
    requested_bottom_mode = requested_spec.bottom_mode
    effective_bottom_mode = resolved_behavior.bottom_policy.effective_mode
    bottom_mode_override_reason = resolved_behavior.bottom_policy.mode_override_reason
    # Frozen per-mode region contract: which regions are collapsed by design for this mode.
    _cbd = _BOTTOM_MODE_COLLAPSED_BY_DESIGN.get(effective_bottom_mode, frozenset())
    bottom_mode_region_contract = {
        "effective_bottom_mode": effective_bottom_mode,
        "title_band_region_required": "title_band_region" not in _cbd,
        "gallery_strip_region_required": False,  # gallery_strip_region is never required
        "title_band_region_collapsed_by_mode": "title_band_region" in _cbd,
        "gallery_strip_region_collapsed_by_mode": "gallery_strip_region" in _cbd,
        "collapsed_by_design_regions": sorted(_cbd),
    }
    return {
        "requested_bottom_mode": requested_bottom_mode,
        "effective_bottom_mode": effective_bottom_mode,
        "bottom_mode": effective_bottom_mode,
        "bottom_mode_remapped": requested_bottom_mode != effective_bottom_mode,
        "bottom_mode_alias": (
            f"{requested_bottom_mode} → {effective_bottom_mode}"
            if requested_bottom_mode != effective_bottom_mode
            else None
        ),
        "bottom_mode_override_reason": bottom_mode_override_reason,
        "bottom_layout_mode": resolved_behavior.bottom_policy.bottom_layout_mode,
        "gallery_mode": resolved_behavior.bottom_policy.gallery_mode,
        "gallery_input_count_raw": int(gallery_counts["raw"]),
        "gallery_input_count_normalized": int(gallery_counts["normalized"]),
        "gallery_requested_count": int(gallery_counts["requested"]),
        "gallery_visible_count": resolved_behavior.bottom_policy.visible_item_count,
        "gallery_autofill_applied": bool(gallery_counts["autofill_applied"]),
        "requested_title_text": requested_spec.title,
        "requested_subtitle_text": requested_spec.subtitle,
        "sanitized_title_text": effective_spec.title,
        "sanitized_subtitle_text": effective_spec.subtitle,
        "rendered_title_excerpt": rendered_title_excerpt,
        "rendered_subtitle_excerpt": rendered_subtitle_excerpt,
        "title_truncation_applied": rendered_title_excerpt != effective_spec.title,
        "subtitle_truncation_applied": rendered_subtitle_excerpt != effective_spec.subtitle,
        "title_source": "request.title",
        "subtitle_source": "request.subtitle",
        "title_band_region": {
            "rendered": bool(region_render_status.get("title_band_region", {}).get("rendered", False)),
            "bounds": _title_band_region_bounds(template, resolved_behavior),
        },
        "gallery_strip_region": {
            "rendered": bool(region_render_status.get("gallery_strip_region", {}).get("rendered", False)),
            "visible_item_count": resolved_behavior.bottom_policy.visible_item_count,
            "bounds": _gallery_strip_region_bounds(template, resolved_behavior),
        },
        "gallery_caption_mode": resolved_behavior.bottom_policy.gallery_caption_mode,
        "caption_owner": resolved_behavior.bottom_policy.gallery_caption_owner,
        "surface_tokens": (
            dict(_FAMILY_A_FRYER_BOTTOM_SURFACE_TOKENS)
            if resolved_behavior.product_policy.product_geometry_mode == "family_a_fryer_hero_supporting_inset_v1"
            else {}
        ),
        "behavior_policy": {
            "title_band_sizing_mode": resolved_behavior.bottom_policy.title_band_sizing_mode,
            "title_band_growth_policy": resolved_behavior.bottom_policy.title_band_growth_policy,
            "subtitle_overflow_policy": resolved_behavior.bottom_policy.subtitle_overflow_policy,
            "title_text_budget_policy": resolved_behavior.bottom_policy.title_text_budget_policy,
            "subtitle_text_budget_policy": resolved_behavior.bottom_policy.subtitle_text_budget_policy,
            "content_priority_policy": resolved_behavior.bottom_policy.content_priority_policy,
            "peer_balance_policy": resolved_behavior.bottom_policy.peer_balance_policy,
            "bottom_peer_balance_policy": resolved_behavior.bottom_policy.bottom_peer_balance_policy,
            "gallery_distribution_policy": resolved_behavior.bottom_policy.gallery_distribution_policy,
            "gallery_shell_frame_policy": resolved_behavior.bottom_policy.gallery_shell_frame_policy,
            "gallery_strip_shift_policy": resolved_behavior.bottom_policy.gallery_strip_shift_policy,
            "gallery_aspect_policy": resolved_behavior.bottom_policy.gallery_aspect_policy,
            "gallery_spacing_policy": resolved_behavior.bottom_policy.gallery_spacing_policy,
            "gallery_caption_mode": resolved_behavior.bottom_policy.gallery_caption_mode,
            "gallery_caption_owner": resolved_behavior.bottom_policy.gallery_caption_owner,
            "bottom_text_emphasis_policy": resolved_behavior.bottom_policy.bottom_text_emphasis_policy,
            "title_line_clamp": resolved_behavior.bottom_policy.title_line_clamp,
            "subtitle_line_clamp": resolved_behavior.bottom_policy.subtitle_line_clamp,
            "title_char_budget": resolved_behavior.bottom_policy.title_char_budget,
            "subtitle_char_budget": resolved_behavior.bottom_policy.subtitle_char_budget,
            "layout_metrics": dict(resolved_behavior.bottom_policy.layout_metrics),
        },
        "collapsed_optional_slots": list(resolved_behavior.bottom_policy.collapsed_optional_slots),
        "title_slot_rendered": resolved_behavior.bottom_policy.title_slot_rendered,
        "subtitle_slot_rendered": resolved_behavior.bottom_policy.subtitle_slot_rendered,
        "gallery_distribution_policy": resolved_behavior.bottom_policy.gallery_distribution_policy,
        "subtitle_slot": dict(resolved_behavior.bottom_policy.subtitle_slot_state),
        "gallery_slots": gallery_slots,
        "gallery_caption_slots": gallery_caption_slots,
        "bottom_mode_region_contract": bottom_mode_region_contract,
    }


def _build_header_contract_review(
    template: TemplateSpec,
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
    layer_render_status: dict[str, dict[str, object]],
    region_render_status: dict[str, dict[str, object]],
) -> dict[str, object]:
    brand_excerpt = _apply_text_budget(
        effective_spec.brand_name,
        resolved_behavior.header_policy.brand_char_budget,
    )
    agent_excerpt = (
        _apply_text_budget(
            effective_spec.agent_name,
            resolved_behavior.header_policy.agent_char_budget,
        )
        if resolved_behavior.header_policy.agent_pill_visible
        else ""
    )
    agent_visual_font_size = (
        16
        if resolved_behavior.product_policy.product_geometry_mode == "family_a_fryer_hero_supporting_inset_v1"
        else int(template.agent_name_slot.font_size)
    )
    if _is_template_b_template(template):
        header_bounds = _header_region_bounds(template, resolved_behavior)
        banner_rendered = bool(region_render_status.get("logo_banner_region", {}).get("rendered", False))
        return {
            "header_mode": resolved_behavior.header_policy.mode,
            "header_visual_mode": resolved_behavior.header_policy.visual_mode,
            "requested_brand_text": requested_spec.brand_name,
            "requested_agent_text": requested_spec.agent_name,
            "sanitized_brand_text": effective_spec.brand_name,
            "sanitized_agent_text": effective_spec.agent_name,
            "rendered_brand_excerpt": brand_excerpt,
            "rendered_agent_excerpt": agent_excerpt,
            "brand_truncation_applied": brand_excerpt != effective_spec.brand_name,
            "agent_truncation_applied": bool(
                resolved_behavior.header_policy.agent_pill_visible
                and agent_excerpt != effective_spec.agent_name
            ),
            "brand_source": "request.brand_name",
            "agent_source": "request.agent_name",
            "header_region": {
                "rendered": banner_rendered,
                "bounds": header_bounds,
            },
            "logo_banner_region": {
                "rendered": banner_rendered,
                "bounds": header_bounds,
            },
            "identity_zone": {
                "rendered": bool(
                    layer_render_status.get("brand_logo_layer", {}).get("rendered", False)
                    or layer_render_status.get("brand_text_layer", {}).get("rendered", False)
                ),
                "identity_zone_mode": resolved_behavior.header_policy.identity_zone_mode,
            },
            "behavior_policy": {
                "lane_layout_mode": resolved_behavior.header_policy.lane_layout_mode,
                "header_visual_mode": resolved_behavior.header_policy.visual_mode,
                "identity_zone_mode": resolved_behavior.header_policy.identity_zone_mode,
                "agent_pill_collapse_condition": resolved_behavior.header_policy.agent_pill_collapse_condition,
                "brand_text_policy": resolved_behavior.header_policy.brand_text_policy,
                "content_priority_policy": resolved_behavior.header_policy.content_priority_policy,
                "brand_line_clamp": resolved_behavior.header_policy.brand_line_clamp,
                "brand_char_budget": resolved_behavior.header_policy.brand_char_budget,
                "agent_line_clamp": resolved_behavior.header_policy.agent_line_clamp,
                "agent_char_budget": resolved_behavior.header_policy.agent_char_budget,
                "layout_metrics": dict(resolved_behavior.header_policy.layout_metrics),
            },
            "brand_logo_slot": {
                "rendered": bool(layer_render_status.get("brand_logo_layer", {}).get("rendered", False)),
                "reason_code": layer_render_status.get("brand_logo_layer", {}).get("reason_code"),
                "bounds": _header_logo_slot_bounds(template, resolved_behavior),
            },
            "brand_name_slot": {
                "rendered": bool(layer_render_status.get("brand_text_layer", {}).get("rendered", False)),
                "reason_code": layer_render_status.get("brand_text_layer", {}).get("reason_code"),
                "bounds": _brand_name_slot_bounds(template, resolved_behavior),
            },
            "agent_name_slot": {
                "rendered": bool(layer_render_status.get("agent_name_text_layer", {}).get("rendered", False)),
                "reason_code": layer_render_status.get("agent_name_text_layer", {}).get("reason_code"),
                "bounds": _agent_name_slot_bounds(template, resolved_behavior),
            },
        }

    return {
        "header_mode": resolved_behavior.header_policy.mode,
        "requested_brand_text": requested_spec.brand_name,
        "requested_agent_text": requested_spec.agent_name,
        "sanitized_brand_text": effective_spec.brand_name,
        "sanitized_agent_text": effective_spec.agent_name,
        "rendered_brand_excerpt": brand_excerpt,
        "rendered_agent_excerpt": agent_excerpt,
        "brand_truncation_applied": brand_excerpt != effective_spec.brand_name,
        "agent_truncation_applied": bool(
            resolved_behavior.header_policy.agent_pill_visible
            and agent_excerpt != effective_spec.agent_name
        ),
        "brand_source": "request.brand_name",
        "agent_source": "request.agent_name",
        "header_region": {
            "rendered": bool(region_render_status.get("header_region", {}).get("rendered", False)),
            "bounds": _header_region_bounds(template, resolved_behavior),
        },
        "identity_zone": {
            "rendered": bool(
                layer_render_status.get("brand_logo_layer", {}).get("rendered", False)
                or layer_render_status.get("brand_text_layer", {}).get("rendered", False)
            ),
            "identity_zone_mode": resolved_behavior.header_policy.identity_zone_mode,
        },
        "behavior_policy": {
            "lane_layout_mode": resolved_behavior.header_policy.lane_layout_mode,
            "identity_zone_mode": resolved_behavior.header_policy.identity_zone_mode,
            "agent_pill_collapse_condition": resolved_behavior.header_policy.agent_pill_collapse_condition,
            "brand_text_policy": resolved_behavior.header_policy.brand_text_policy,
            "content_priority_policy": resolved_behavior.header_policy.content_priority_policy,
            "brand_line_clamp": resolved_behavior.header_policy.brand_line_clamp,
            "brand_char_budget": resolved_behavior.header_policy.brand_char_budget,
            "agent_line_clamp": resolved_behavior.header_policy.agent_line_clamp,
            "agent_char_budget": resolved_behavior.header_policy.agent_char_budget,
            "layout_metrics": dict(resolved_behavior.header_policy.layout_metrics),
        },
        "brand_logo_slot": {
            "rendered": bool(layer_render_status.get("brand_logo_layer", {}).get("rendered", False)),
            "reason_code": layer_render_status.get("brand_logo_layer", {}).get("reason_code"),
            "bounds": _header_logo_slot_bounds(template, resolved_behavior),
        },
        "brand_name_slot": {
            "rendered": bool(layer_render_status.get("brand_text_layer", {}).get("rendered", False)),
            "reason_code": layer_render_status.get("brand_text_layer", {}).get("reason_code"),
            "bounds": _brand_name_slot_bounds(template, resolved_behavior),
        },
        "agent_name_slot": {
            "rendered": bool(layer_render_status.get("agent_name_text_layer", {}).get("rendered", False)),
            "reason_code": layer_render_status.get("agent_name_text_layer", {}).get("reason_code"),
            "bounds": _agent_name_slot_bounds(template, resolved_behavior),
            "visual_font_size": agent_visual_font_size,
        },
    }


def _build_hero_contract_review(
    template: TemplateSpec,
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
    layer_render_status: dict[str, dict[str, object]],
    region_render_status: dict[str, dict[str, object]],
) -> dict[str, object]:
    scenario_source = requested_spec.scenario_image.url if requested_spec.scenario_image else None
    product_source = requested_spec.product_image.url
    if _is_template_b_template(template):
        product_region_bounds = _product_region_bounds(template, resolved_behavior)
        return {
            "hero_mode": resolved_behavior.hero_policy.mode,
            "requested_scenario_source": None,
            "requested_product_source": product_source,
            "effective_scenario_source": None,
            "effective_product_source": product_source,
            "rendered_scenario_source": None,
            "rendered_product_source": product_source,
            "scenario_safe_fill_applied": False,
            "product_hero_region": {
                "rendered": bool(region_render_status.get("product_hero_region", {}).get("rendered", False)),
                "bounds": product_region_bounds,
            },
            "behavior_policy": {
                "scenario_render_policy": resolved_behavior.hero_policy.scenario_render_policy,
                "product_render_policy": resolved_behavior.hero_policy.product_render_policy,
                "peer_layout_policy": resolved_behavior.hero_policy.peer_layout_policy,
                "product_fit": resolved_behavior.hero_policy.product_fit,
                "product_anchor": resolved_behavior.hero_policy.product_anchor,
                "layout_metrics": dict(resolved_behavior.hero_policy.layout_metrics),
            },
            "product_slot": {
                "rendered": bool(layer_render_status.get("product_image_layer", {}).get("rendered", False)),
                "reason_code": layer_render_status.get("product_image_layer", {}).get("reason_code"),
                "bounds": _product_slot_bounds(template, resolved_behavior),
            },
            "product_secondary_slot": {
                "rendered": bool(layer_render_status.get("product_secondary_image_layer", {}).get("rendered", False)),
                "reason_code": layer_render_status.get("product_secondary_image_layer", {}).get("reason_code"),
                "bounds": _product_secondary_slot_bounds(resolved_behavior),
            },
        }

    return {
        "hero_mode": resolved_behavior.hero_policy.mode,
        "requested_scenario_source": scenario_source,
        "requested_product_source": product_source,
        "effective_scenario_source": scenario_source,
        "effective_product_source": product_source,
        "rendered_scenario_source": (
            "safe_preset_image"
            if layer_render_status.get("scenario_image_layer", {}).get("reason_code") == "safe_preset_fill"
            else scenario_source
        ),
        "rendered_product_source": product_source,
        "scenario_safe_fill_applied": layer_render_status.get("scenario_image_layer", {}).get("reason_code") == "safe_preset_fill",
        "scenario_region": {
            "rendered": bool(region_render_status.get("scenario_region", {}).get("rendered", False)),
            "bounds": _scenario_region_bounds(template, resolved_behavior),
        },
        "product_region": {
            "rendered": bool(region_render_status.get("product_region", {}).get("rendered", False)),
            "bounds": _product_region_bounds(template, resolved_behavior),
        },
        "behavior_policy": {
            "scenario_render_policy": resolved_behavior.hero_policy.scenario_render_policy,
            "product_render_policy": resolved_behavior.hero_policy.product_render_policy,
            "peer_layout_policy": resolved_behavior.hero_policy.peer_layout_policy,
            "scenario_fit": resolved_behavior.hero_policy.scenario_fit,
            "scenario_anchor": resolved_behavior.hero_policy.scenario_anchor,
            "product_fit": resolved_behavior.hero_policy.product_fit,
            "product_anchor": resolved_behavior.hero_policy.product_anchor,
            "layout_metrics": dict(resolved_behavior.hero_policy.layout_metrics),
        },
        "scenario_slot": {
            "rendered": bool(layer_render_status.get("scenario_image_layer", {}).get("rendered", False)),
            "reason_code": layer_render_status.get("scenario_image_layer", {}).get("reason_code"),
            "bounds": _scenario_slot_bounds(template, resolved_behavior),
        },
        "product_slot": {
            "rendered": bool(layer_render_status.get("product_image_layer", {}).get("rendered", False)),
            "reason_code": layer_render_status.get("product_image_layer", {}).get("reason_code"),
            "bounds": _product_slot_bounds(template, resolved_behavior),
        },
    }


def _build_product_contract_review(
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
    layer_render_status: dict[str, dict[str, object]],
    region_render_status: dict[str, dict[str, object]],
    copy_optimization_review: dict[str, object] | None = None,
) -> dict[str, object]:
    product_policy = resolved_behavior.product_policy
    if effective_spec.template_id.startswith("template_product_sheet"):
        layout_metrics = dict(product_policy.layout_metrics)
        owner_surfaces = [
            "product_card_shell_layer",
            "product_canvas_shell_layer",
            "product_image_layer",
            "product_primary_slot",
        ]
        if product_policy.product_secondary_slot_rendered:
            owner_surfaces.extend(["product_secondary_image_layer", "product_secondary_slot"])
        return {
            "product_annotation_mode": product_policy.annotation_mode,
            "product_annotation_owner": "not_applicable_template_b",
            "secondary_product_mode": product_policy.secondary_product_mode,
            "requested_product_source": requested_spec.product_image.url,
            "effective_product_source": effective_spec.product_image.url,
            "rendered_product_source": effective_spec.product_image.url,
            "product_source": "request.product_image",
            "requested_annotation_items": [],
            "sanitized_annotation_items": [],
            "rendered_annotation_items": [],
            "product_hero_region": {
                "rendered": bool(region_render_status.get("product_hero_region", {}).get("rendered", False)),
                "bounds": {
                    "x": int(layout_metrics["product_region_x"]),
                    "y": int(layout_metrics["product_region_y"]),
                    "w": int(layout_metrics["product_region_w"]),
                    "h": int(layout_metrics["product_region_h"]),
                },
            },
            "product_card_shell_layer": {
                "rendered": bool(layer_render_status.get("product_card_shell_layer", {}).get("rendered", False)),
                "reason_code": layer_render_status.get("product_card_shell_layer", {}).get("reason_code"),
                "bounds": {
                    "x": int(layout_metrics["product_region_x"]),
                    "y": int(layout_metrics["product_region_y"]),
                    "w": int(layout_metrics["product_region_w"]),
                    "h": int(layout_metrics["product_region_h"]),
                },
            },
            "product_canvas_shell_layer": {
                "rendered": bool(layer_render_status.get("product_canvas_shell_layer", {}).get("rendered", False)),
                "reason_code": layer_render_status.get("product_canvas_shell_layer", {}).get("reason_code"),
                "bounds": {
                    "x": int(layout_metrics["product_canvas_shell_x"]),
                    "y": int(layout_metrics["product_canvas_shell_y"]),
                    "w": int(layout_metrics["product_canvas_shell_w"]),
                    "h": int(layout_metrics["product_canvas_shell_h"]),
                },
            },
            "product_text_shell_layer": {
                "rendered": bool(layer_render_status.get("product_text_shell_layer", {}).get("rendered", False)),
                "reason_code": layer_render_status.get("product_text_shell_layer", {}).get("reason_code"),
                "bounds": {
                    "x": int(layout_metrics["product_text_shell_x"]),
                    "y": int(layout_metrics["product_text_shell_y"]),
                    "w": int(layout_metrics["product_text_shell_w"]),
                    "h": int(layout_metrics["product_text_shell_h"]),
                },
                "owner_region": "product_hero_region",
                "owner_surface": "not_used_in_template_b",
                "text_does_not_compete_with_canvas": True,
            },
            "product_image_layer": {
                "rendered": bool(layer_render_status.get("product_image_layer", {}).get("rendered", False)),
                "reason_code": layer_render_status.get("product_image_layer", {}).get("reason_code"),
                "bounds": _product_primary_slot_bounds(resolved_behavior),
            },
            "product_secondary_image_layer": {
                "rendered": bool(layer_render_status.get("product_secondary_image_layer", {}).get("rendered", False)),
                "reason_code": layer_render_status.get("product_secondary_image_layer", {}).get("reason_code"),
                "source_binding": layer_render_status.get("product_secondary_image_layer", {}).get("source_binding"),
                "bounds": _product_secondary_slot_bounds(resolved_behavior),
            },
            "product_support_surface_layer": {
                "rendered": False,
                "reason_code": "not_applicable_template_b",
                "source_binding": None,
                "bounds": None,
            },
            "product_annotation_shell_layer": {
                "rendered": False,
                "reason_code": layer_render_status.get("product_annotation_shell_layer", {}).get("reason_code"),
                "bounds": {
                    "x": int(layout_metrics["annotation_shell_x"]),
                    "y": int(layout_metrics["annotation_shell_y"]),
                    "w": int(layout_metrics["annotation_shell_w"]),
                    "h": int(layout_metrics["annotation_shell_h"]),
                },
            },
            "product_annotation_items_layer": {
                "rendered": False,
                "reason_code": layer_render_status.get("product_annotation_items_layer", {}).get("reason_code"),
                "visible_item_count": 0,
            },
            "product_layout_mode": product_policy.product_layout_mode,
            "product_layout_mode_reason": product_policy.product_layout_mode_reason,
            "product_geometry_mode": product_policy.product_geometry_mode,
            "product_geometry_mode_reason": product_policy.product_geometry_mode_reason,
            "geometry_frozen": True,
            "product_primary_image_fit": product_policy.product_primary_image_fit,
            "product_primary_slot": dict(product_policy.product_primary_slot),
            "product_secondary_slot": dict(product_policy.product_secondary_slot) if product_policy.product_secondary_slot else None,
            "product_secondary_slot_rendered": product_policy.product_secondary_slot_rendered,
            "product_secondary_asset_policy": product_policy.product_secondary_asset_policy,
            "product_support_surface_rendered": False,
            "product_support_surface_source": None,
            "product_support_surface_mode": "not_applicable_template_b",
            "product_support_surface_bounds": None,
            "product_support_surface_caption_text": "",
            "owner_surfaces": owner_surfaces,
            "annotation_owner_slot": None,
            "secondary_slot_annotation_ownership": False,
            "behavior_policy": {
                "annotation_count_policy": product_policy.annotation_count_policy,
                "annotation_connector_policy": product_policy.annotation_connector_policy,
                "annotation_marker_policy": product_policy.annotation_marker_policy,
                "annotation_shell_policy": product_policy.annotation_shell_policy,
                "annotation_bounds_policy": product_policy.annotation_bounds_policy,
                "text_budget_policy": product_policy.text_budget_policy,
                "secondary_product_mode": product_policy.secondary_product_mode,
                "line_clamp": product_policy.line_clamp,
                "char_budget": product_policy.char_budget,
                "layout_metrics": layout_metrics,
            },
            "annotation_slots": [],
        }

    rendered_items = []
    annotation_slots = []
    requested_items = list(requested_spec.features[: product_policy.max_annotation_items])
    sanitized_items = list(effective_spec.features[: product_policy.max_annotation_items])
    for index in range(product_policy.max_annotation_items):
        requested_text = requested_items[index] if index < len(requested_items) else ""
        sanitized_text = sanitized_items[index] if index < len(sanitized_items) else ""
        optimization_item = (
            copy_optimization_review.get("annotation_items", [])[index]
            if copy_optimization_review and index < len(copy_optimization_review.get("annotation_items", []))
            else {}
        )
        rendered = (
            product_policy.annotation_mode != "none"
            and index < product_policy.visible_annotation_count
            and bool(sanitized_text)
        )
        rendered_excerpt = (
            _apply_text_budget_word_safe(sanitized_text, product_policy.char_budget)
            if rendered
            else ""
        )
        annotation_meta = (
            product_policy.annotation_items[index]
            if index < len(product_policy.annotation_items)
            else {}
        )
        annotation_slots.append(
            {
                "slot_id": f"product_annotation_slot_{index + 1}",
                "slot_fixed": True,
                "requested_text": requested_text,
                "sanitized_text": sanitized_text,
                "cleanup_text": optimization_item.get("cleanup_text", sanitized_text),
                "fit_rewrite_text": optimization_item.get("fit_rewrite_text", sanitized_text),
                "fit_rewrite_applied": bool(optimization_item.get("fit_rewrite_applied", False)),
                "fit_rewrite_reason": optimization_item.get("fit_rewrite_reason", ""),
                "optimized_text": optimization_item.get("optimized_text", ""),
                "accepted_text": optimization_item.get("accepted_text", ""),
                "rendered_text": optimization_item.get("rendered_text", rendered_excerpt),
                "rendered_text_source": optimization_item.get("rendered_text_source", "sanitized_text"),
                "rendered_excerpt": rendered_excerpt,
                "char_budget": product_policy.char_budget,
                "line_clamp": product_policy.line_clamp,
                "rendered": rendered,
                "truncation_applied": rendered_excerpt != sanitized_text,
                "reason_code": (
                    None
                    if rendered
                    else (
                        "annotation_mode_none"
                        if product_policy.annotation_mode == "none"
                        else "collapsed_when_empty_or_capped"
                    )
                ),
                "anchor_index": annotation_meta.get("anchor_index"),
                "anchor_x": annotation_meta.get("anchor_x"),
                "anchor_y": annotation_meta.get("anchor_y"),
                "anchor_color": annotation_meta.get("anchor_color"),
                "label_bounds": annotation_meta.get("label_bounds"),
                "connector_policy": annotation_meta.get("connector_policy"),
                "marker_policy": annotation_meta.get("marker_policy"),
                "positions_source": annotation_meta.get("positions_source"),
            }
        )
        if rendered:
            rendered_items.append(rendered_excerpt)

    layout_metrics = dict(product_policy.layout_metrics)
    primary_bounds = _product_primary_slot_bounds(resolved_behavior)
    secondary_bounds = (
        _product_secondary_slot_bounds(resolved_behavior)
        if product_policy.product_secondary_slot is not None
        else None
    )
    return {
        "product_annotation_mode": product_policy.annotation_mode,
        "product_annotation_owner": "product_region" if product_policy.annotation_mode == "product_anchor_callouts" else "feature_region",
        "secondary_product_mode": product_policy.secondary_product_mode,
        "visible_annotation_count": product_policy.visible_annotation_count,
        "requested_product_source": requested_spec.product_image.url,
        "effective_product_source": effective_spec.product_image.url,
        "rendered_product_source": effective_spec.product_image.url,
        "product_source": "request.product_image",
        "requested_annotation_items": requested_items,
        "sanitized_annotation_items": sanitized_items,
        "rendered_annotation_items": rendered_items,
        "product_region": {
            "rendered": bool(region_render_status.get("product_region", {}).get("rendered", False)),
            "bounds": {
                "x": int(layout_metrics["product_region_x"]),
                "y": int(layout_metrics["product_region_y"]),
                "w": int(layout_metrics["product_region_w"]),
                "h": int(layout_metrics["product_region_h"]),
            },
        },
        "product_card_shell_layer": {
            "rendered": bool(layer_render_status.get("product_card_shell_layer", {}).get("rendered", False)),
            "reason_code": layer_render_status.get("product_card_shell_layer", {}).get("reason_code"),
            "bounds": {
                "x": int(layout_metrics["product_region_x"]),
                "y": int(layout_metrics["product_region_y"]),
                "w": int(layout_metrics["product_region_w"]),
                "h": int(layout_metrics["product_region_h"]),
            },
        },
        "product_canvas_shell_layer": {
            "rendered": bool(layer_render_status.get("product_canvas_shell_layer", {}).get("rendered", False)),
            "reason_code": layer_render_status.get("product_canvas_shell_layer", {}).get("reason_code"),
            "bounds": {
                "x": int(layout_metrics["product_canvas_shell_x"]),
                "y": int(layout_metrics["product_canvas_shell_y"]),
                "w": int(layout_metrics["product_canvas_shell_w"]),
                "h": int(layout_metrics["product_canvas_shell_h"]),
            },
        },
        "product_text_shell_layer": {
            "rendered": bool(layer_render_status.get("product_text_shell_layer", {}).get("rendered", False)),
            "reason_code": layer_render_status.get("product_text_shell_layer", {}).get("reason_code"),
            "bounds": {
                "x": int(layout_metrics["product_text_shell_x"]),
                "y": int(layout_metrics["product_text_shell_y"]),
                "w": int(layout_metrics["product_text_shell_w"]),
                "h": int(layout_metrics["product_text_shell_h"]),
            },
            "owner_region": _PRODUCT_ANNOTATION_TEXT_OWNER_REGION,
            "owner_surface": "product_text_shell_layer",
            "text_does_not_compete_with_canvas": (
                int(layout_metrics["product_text_shell_x"])
                >= (int(layout_metrics["product_canvas_shell_x"]) + int(layout_metrics["product_canvas_shell_w"]))
            ),
        },
        "product_image_layer": {
            "rendered": bool(layer_render_status.get("product_image_layer", {}).get("rendered", False)),
            "reason_code": layer_render_status.get("product_image_layer", {}).get("reason_code"),
            "bounds": primary_bounds,
        },
        "product_secondary_image_layer": {
            "rendered": bool(layer_render_status.get("product_secondary_image_layer", {}).get("rendered", False)),
            "reason_code": layer_render_status.get("product_secondary_image_layer", {}).get("reason_code"),
            "source_binding": layer_render_status.get("product_secondary_image_layer", {}).get("source_binding"),
            "bounds": secondary_bounds,
        },
        "product_support_surface_layer": {
            "rendered": bool(layer_render_status.get("product_support_surface_layer", {}).get("rendered", False)),
            "reason_code": layer_render_status.get("product_support_surface_layer", {}).get("reason_code"),
            "source_binding": layer_render_status.get("product_support_surface_layer", {}).get("source_binding"),
            "bounds": product_policy.product_support_surface_bounds,
        },
        "product_annotation_shell_layer": {
            "rendered": bool(layer_render_status.get("product_annotation_shell_layer", {}).get("rendered", False)),
            "reason_code": layer_render_status.get("product_annotation_shell_layer", {}).get("reason_code"),
            "bounds": {
                "x": int(layout_metrics["annotation_shell_x"]),
                "y": int(layout_metrics["annotation_shell_y"]),
                "w": int(layout_metrics["annotation_shell_w"]),
                "h": int(layout_metrics["annotation_shell_h"]),
            },
        },
        "product_annotation_items_layer": {
            "rendered": bool(layer_render_status.get("product_annotation_items_layer", {}).get("rendered", False)),
            "reason_code": layer_render_status.get("product_annotation_items_layer", {}).get("reason_code"),
            "visible_item_count": product_policy.visible_annotation_count,
        },
        "product_layout_mode": product_policy.product_layout_mode,
        "product_layout_mode_reason": product_policy.product_layout_mode_reason,
        "product_geometry_mode": product_policy.product_geometry_mode,
        "product_geometry_mode_reason": product_policy.product_geometry_mode_reason,
        "geometry_frozen": True,
        "product_primary_image_fit": product_policy.product_primary_image_fit,
        "product_primary_slot": dict(product_policy.product_primary_slot),
        "product_secondary_slot": dict(product_policy.product_secondary_slot) if product_policy.product_secondary_slot else None,
        "product_secondary_slot_rendered": product_policy.product_secondary_slot_rendered,
        "product_secondary_asset_policy": product_policy.product_secondary_asset_policy,
        "product_support_surface_rendered": product_policy.product_support_surface_rendered,
        "product_support_surface_source": product_policy.product_support_surface_source,
        "product_support_surface_mode": product_policy.product_support_surface_mode,
        "product_support_surface_bounds": product_policy.product_support_surface_bounds,
        "product_support_surface_caption_text": product_policy.product_support_surface_caption_text,
        "owner_surfaces": sorted(_FROZEN_PRODUCT_OWNER_SURFACES),
        "annotation_owner_slot": _PRODUCT_ANNOTATION_OWNER_SLOT,
        "secondary_slot_annotation_ownership": False,
        "behavior_policy": {
            "annotation_count_policy": product_policy.annotation_count_policy,
            "annotation_connector_policy": product_policy.annotation_connector_policy,
            "annotation_marker_policy": product_policy.annotation_marker_policy,
            "annotation_shell_policy": product_policy.annotation_shell_policy,
            "annotation_bounds_policy": product_policy.annotation_bounds_policy,
            "text_shell_variant": product_policy.text_shell_variant,
            "annotation_capacity_variant": product_policy.annotation_capacity_variant,
            "text_budget_policy": product_policy.text_budget_policy,
            "line_clamp": product_policy.line_clamp,
            "char_budget": product_policy.char_budget,
            "layout_metrics": layout_metrics,
        },
        "annotation_slots": annotation_slots,
    }


def _build_feature_contract_review(
    template: TemplateSpec,
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
    region_render_status: dict[str, dict[str, object]],
) -> dict[str, object]:
    if _is_template_b_template(template):
        return {
            "feature_mode": resolved_behavior.feature_policy.mode,
            "feature_view_mode": "not_applicable_template_b",
            "responsibility_owner": "none",
            "delegated_to_product_annotation": False,
            "requested_feature_items": list(requested_spec.features),
            "sanitized_feature_items": list(effective_spec.features),
            "rendered_feature_items": [],
            "feature_region": {
                "rendered": False,
                "visible_item_count": 0,
                "bounds": None,
                "reason_code": "feature_mode_disabled_for_template_b",
            },
            "behavior_policy": {
                "visible_item_count_policy": resolved_behavior.feature_policy.visible_item_count_policy,
                "connector_policy": resolved_behavior.feature_policy.connector_policy,
                "box_policy": resolved_behavior.feature_policy.box_policy,
                "truncation_policy": resolved_behavior.feature_policy.truncation_policy,
                "collapse_policy": resolved_behavior.feature_policy.collapse_policy,
                "text_budget_policy": resolved_behavior.feature_policy.text_budget_policy,
                "line_clamp": resolved_behavior.feature_policy.line_clamp,
                "char_budget": resolved_behavior.feature_policy.char_budget,
                "box_h": resolved_behavior.feature_policy.box_h,
                "gap": resolved_behavior.feature_policy.gap,
                "start_strategy": resolved_behavior.feature_policy.start_strategy,
                "responsibility_policy": "feature_mode_disabled_for_template_b",
            },
            "feature_slots": [],
            "anchor_evidence": None,
        }

    feature_region_bounds = {
        "x": int(template.feature_callouts[0].label_box.x) if template.feature_callouts else 0,
        "y": int(template.feature_callouts[0].label_box.y) if template.feature_callouts else 0,
        "w": 164,
        "h": 392,
    }
    delegated_to_product_annotation = resolved_behavior.product_policy.annotation_mode == "product_anchor_callouts"
    rendered_items = (
        []
        if delegated_to_product_annotation
        else [
            _apply_text_budget_word_safe(text, resolved_behavior.feature_policy.char_budget)
            for text in effective_spec.features[: resolved_behavior.feature_policy.visible_item_count]
        ]
    )
    item_reviews = []
    for index, requested_text in enumerate(requested_spec.features, start=1):
        sanitized_text = effective_spec.features[index - 1] if index - 1 < len(effective_spec.features) else ""
        slot_rendered = (
            not delegated_to_product_annotation
            and index <= resolved_behavior.feature_policy.visible_item_count
            and bool(sanitized_text)
        )
        rendered_excerpt = _apply_text_budget_word_safe(sanitized_text, resolved_behavior.feature_policy.char_budget) if slot_rendered else ""
        if index <= len(template.feature_callouts):
            label_box = template.feature_callouts[index - 1].label_box
            bounds = {"x": int(label_box.x), "y": int(label_box.y), "w": int(label_box.w), "h": int(label_box.h)}
        else:
            bounds = None
        item_reviews.append(
            {
                "slot_id": f"feature_item_slot_{index}",
                "requested_text": requested_text,
                "sanitized_text": sanitized_text,
                "rendered_excerpt": rendered_excerpt,
                "rendered": slot_rendered,
                "truncation_applied": False if delegated_to_product_annotation else (rendered_excerpt != sanitized_text),
                "reason_code": (
                    "delegated_to_product_annotation_region"
                    if delegated_to_product_annotation
                    else (None if slot_rendered else "collapsed_when_empty_or_capped")
                ),
                "bounds": bounds,
            }
        )
    anchor_evidence = None
    if resolved_behavior.feature_policy.mode == "product_anchor_callouts" and not delegated_to_product_annotation:
        anchor_evidence = [
            {
                "anchor_index": i,
                "anchor_x": int(template.feature_callouts[i].anchor_x) if i < len(template.feature_callouts) else None,
                "anchor_y": int(template.feature_callouts[i].anchor_y) if i < len(template.feature_callouts) else None,
                "anchor_color": template.feature_callouts[i].anchor_color if i < len(template.feature_callouts) else None,
                "positions_source": "template_spec_fixed",
            }
            for i in range(resolved_behavior.feature_policy.max_items)
        ]
    return {
        "feature_mode": resolved_behavior.feature_policy.mode,
        "feature_view_mode": "delegated_diagnostic" if delegated_to_product_annotation else "owner",
        "responsibility_owner": "product_region" if delegated_to_product_annotation else "feature_region",
        "delegated_to_product_annotation": delegated_to_product_annotation,
        "requested_feature_items": list(requested_spec.features),
        "sanitized_feature_items": list(effective_spec.features),
        "rendered_feature_items": rendered_items,
        "feature_region": {
            "rendered": bool(region_render_status.get("feature_region", {}).get("rendered", False)),
            "visible_item_count": 0 if delegated_to_product_annotation else resolved_behavior.feature_policy.visible_item_count,
            "bounds": feature_region_bounds,
            "reason_code": (
                "delegated_to_product_annotation_region"
                if delegated_to_product_annotation
                else None
            ),
        },
        "behavior_policy": {
            "visible_item_count_policy": resolved_behavior.feature_policy.visible_item_count_policy,
            "connector_policy": resolved_behavior.feature_policy.connector_policy,
            "box_policy": resolved_behavior.feature_policy.box_policy,
            "truncation_policy": resolved_behavior.feature_policy.truncation_policy,
            "collapse_policy": resolved_behavior.feature_policy.collapse_policy,
            "text_budget_policy": resolved_behavior.feature_policy.text_budget_policy,
            "line_clamp": resolved_behavior.feature_policy.line_clamp,
            "char_budget": resolved_behavior.feature_policy.char_budget,
            "box_h": resolved_behavior.feature_policy.box_h,
            "gap": resolved_behavior.feature_policy.gap,
            "start_strategy": resolved_behavior.feature_policy.start_strategy,
            "responsibility_policy": (
                "delegated_to_product_annotation_region"
                if delegated_to_product_annotation
                else "feature_region_owns_feature_callouts"
            ),
        },
        "feature_slots": item_reviews,
        "anchor_evidence": anchor_evidence,
    }


def _build_product_annotation_contract_review(
    template: TemplateSpec,
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
    region_render_status: dict[str, dict[str, object]],
    copy_optimization_review: dict[str, object] | None = None,
) -> dict[str, object]:
    feature_policy = resolved_behavior.feature_policy
    product_policy = resolved_behavior.product_policy
    annotation_mode = product_policy.annotation_mode
    if annotation_mode == "none":
        product_region_key = "product_hero_region" if _is_template_b_template(template) else "product_region"
        return {
            "product_annotation_mode": "none",
            "annotation_active": False,
            "annotation_slots": [],
            product_region_key: {
                "rendered": bool(region_render_status.get(product_region_key, {}).get("rendered", False)),
            },
        }

    max_slots = product_policy.max_annotation_items  # fixed 3
    slot_reviews = []
    for i in range(max_slots):
        requested_text = (
            requested_spec.features[i]
            if i < len(requested_spec.features)
            else ""
        )
        sanitized_text = (
            effective_spec.features[i]
            if i < len(effective_spec.features)
            else ""
        )
        optimization_item = (
            copy_optimization_review.get("annotation_items", [])[i]
            if copy_optimization_review and i < len(copy_optimization_review.get("annotation_items", []))
            else {}
        )
        is_visible = i < product_policy.visible_annotation_count and bool(sanitized_text)
        rendered_excerpt = (
            _apply_text_budget_word_safe(sanitized_text, product_policy.char_budget)
            if is_visible
            else ""
        )
        annotation_meta = (
            product_policy.annotation_items[i]
            if i < len(product_policy.annotation_items)
            else {}
        )
        slot_reviews.append({
            "slot_index": i,
            "slot_id": f"product_annotation_slot_{i + 1}",
            "slot_fixed": True,
            "rendered": is_visible,
            "requested_text": requested_text,
            "sanitized_text": sanitized_text,
            "cleanup_text": optimization_item.get("cleanup_text", sanitized_text),
            "fit_rewrite_text": optimization_item.get("fit_rewrite_text", sanitized_text),
            "fit_rewrite_applied": bool(optimization_item.get("fit_rewrite_applied", False)),
            "fit_rewrite_reason": optimization_item.get("fit_rewrite_reason", ""),
            "optimized_text": optimization_item.get("optimized_text", ""),
            "accepted_text": optimization_item.get("accepted_text", ""),
            "rendered_text": optimization_item.get("rendered_text", rendered_excerpt),
            "rendered_text_source": optimization_item.get("rendered_text_source", "sanitized_text"),
            "rendered_excerpt": rendered_excerpt,
            "char_budget": product_policy.char_budget,
            "line_clamp": product_policy.line_clamp,
            "truncation_applied": rendered_excerpt != sanitized_text,
            "anchor_x": annotation_meta.get("anchor_x"),
            "anchor_y": annotation_meta.get("anchor_y"),
            "label_bounds": annotation_meta.get("label_bounds"),
            "connector_policy": annotation_meta.get("connector_policy", product_policy.annotation_connector_policy),
            "annotation_owner": "product_region",
            "marker_policy": annotation_meta.get("marker_policy", product_policy.annotation_marker_policy),
            "positions_source": annotation_meta.get("positions_source"),
            "anchor_color": annotation_meta.get("anchor_color"),
        })

    return {
        "product_annotation_mode": annotation_mode,
        "annotation_active": True,
        "annotation_text_owner_region": _PRODUCT_ANNOTATION_TEXT_OWNER_REGION,
        "annotation_slot_ids": list(_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS),
        "ownership_frozen": True,
        "max_slots": max_slots,
        "visible_slot_count": product_policy.visible_annotation_count,
        "annotation_slots": slot_reviews,
        "product_region": {
            "rendered": bool(region_render_status.get("product_region", {}).get("rendered", False)),
            "bounds": {
                "x": int(resolved_behavior.product_policy.layout_metrics["product_region_x"]),
                "y": int(resolved_behavior.product_policy.layout_metrics["product_region_y"]),
                "w": int(resolved_behavior.product_policy.layout_metrics["product_region_w"]),
                "h": int(resolved_behavior.product_policy.layout_metrics["product_region_h"]),
            },
        },
        "behavior_policy": {
            "visible_item_count_policy": feature_policy.visible_item_count_policy,
            "connector_policy": product_policy.annotation_connector_policy,
            "marker_policy": product_policy.annotation_marker_policy,
            "box_policy": feature_policy.box_policy,
            "start_strategy": feature_policy.start_strategy,
            "char_budget": product_policy.char_budget,
            "line_clamp": product_policy.line_clamp,
            "annotation_bounds_policy": product_policy.annotation_bounds_policy,
            "positions_source": (
                product_policy.annotation_items[0].get("positions_source")
                if product_policy.annotation_items
                else None
            ),
            "annotation_card_surface_tokens": (
                dict(_FAMILY_A_FRYER_ANNOTATION_CARD_STYLE_TOKENS)
                if product_policy.text_shell_variant == "family_a_fryer_extended_right_lane"
                else {}
            ),
            "layout_metrics": dict(product_policy.layout_metrics),
        },
        "feature_suppression": {
            "feature_right_stack_suppressed": True,
            "suppression_reason": "product_annotation_mode_active",
        },
    }


def _build_scenario_contract_review(
    template: TemplateSpec,
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
    layer_render_status: dict[str, dict[str, object]],
    region_render_status: dict[str, dict[str, object]],
) -> dict[str, object]:
    hero = resolved_behavior.hero_policy
    if _is_template_b_template(template):
        return {
            "hero_mode": hero.mode,
            "scenario_enabled": False,
            "scenario_render_policy": hero.scenario_render_policy,
            "requested_source": None,
            "sanitized_source": None,
            "rendered_source": None,
            "safe_fill_applied": False,
            "source_binding": None,
            "scenario_region": {
                "rendered": False,
                "bounds": {"x": 0, "y": 0, "w": 0, "h": 0},
            },
            "scenario_slot": {
                "rendered": False,
                "reason_code": "scenario_disabled_for_template_b",
                "source_binding": None,
                "bounds": {"x": 0, "y": 0, "w": 0, "h": 0},
            },
            "behavior_policy": {
                "scenario_render_policy": hero.scenario_render_policy,
                "scenario_fit": hero.scenario_fit,
                "scenario_anchor": hero.scenario_anchor,
                "peer_layout_policy": hero.peer_layout_policy,
                "layout_metrics": {
                    key: value
                    for key, value in hero.layout_metrics.items()
                    if key.startswith("scenario_")
                },
            },
            "renderer_path_parity": "template_b_scenario_disabled",
            "evidence_source": "resolver_layer_status",
        }

    scenario_source = requested_spec.scenario_image.url if requested_spec.scenario_image else None
    safe_fill = layer_render_status.get("scenario_image_layer", {}).get("reason_code") == "safe_preset_fill"
    rendered_source = "safe_preset_image" if safe_fill else scenario_source
    scenario_metrics = {
        k: v for k, v in hero.layout_metrics.items() if k.startswith("scenario_")
    }
    return {
        "hero_mode": hero.mode,
        "scenario_enabled": hero.scenario_enabled,
        "scenario_render_policy": hero.scenario_render_policy,
        "requested_source": scenario_source,
        "sanitized_source": scenario_source,
        "rendered_source": rendered_source,
        "safe_fill_applied": safe_fill,
        "source_binding": "request.scenario_image.url",
        "scenario_region": {
            "rendered": bool(region_render_status.get("scenario_region", {}).get("rendered", False)),
            "bounds": _scenario_region_bounds(template, resolved_behavior),
        },
        "scenario_slot": {
            "rendered": bool(layer_render_status.get("scenario_image_layer", {}).get("rendered", False)),
            "reason_code": layer_render_status.get("scenario_image_layer", {}).get("reason_code"),
            "source_binding": layer_render_status.get("scenario_image_layer", {}).get("source_binding"),
            "bounds": _scenario_slot_bounds(template, resolved_behavior),
        },
        "behavior_policy": {
            "scenario_render_policy": hero.scenario_render_policy,
            "scenario_fit": hero.scenario_fit,
            "scenario_anchor": hero.scenario_anchor,
            "peer_layout_policy": hero.peer_layout_policy,
            "layout_metrics": scenario_metrics,
        },
        # Renderer-path parity note (narrowed scope):
        # Both Puppeteer and Pillow call the same _build_renderer_layer_render_status()
        # builder so the evidence *shape* is identical. However, there is one known
        # value divergence: Pillow always passes scenario_safe_fill=False, while
        # Puppeteer sets it conditionally (True when scenario is absent but
        # scenario_enabled=True). As a result:
        #   - Pillow path: absent scenario → reason_code="scenario_missing", safe_fill_applied=False
        #   - Puppeteer path: absent scenario → reason_code="safe_preset_fill", safe_fill_applied=True
        # This gap is documented in docs/poster2/scenario_region_resolver_and_renderer_parity_status_v1.md
        # and tracked as an open follow-up, not resolved in this PR.
        "renderer_path_parity": "shape_aligned_safe_fill_pillow_always_false_puppeteer_conditional",
        "evidence_source": "resolver_layer_status",
    }


def _build_top_copy_contract_review(
    template: TemplateSpec,
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
    layer_render_status: dict[str, dict[str, object]],
    region_render_status: dict[str, dict[str, object]],
) -> dict[str, object]:
    if not _is_template_b_template(template):
        return {}

    sku_sanitized = effective_spec.sku_text or ""
    title_sanitized = effective_spec.title
    subtitle_sanitized = effective_spec.subtitle
    sku_rendered = bool(layer_render_status.get("sku_text_layer", {}).get("rendered", False))
    title_rendered = bool(layer_render_status.get("top_copy_title_layer", {}).get("rendered", False))
    subtitle_rendered = bool(layer_render_status.get("top_copy_subtitle_layer", {}).get("rendered", False))
    sku_excerpt = _apply_text_budget(sku_sanitized, _TEMPLATE_B_SKU_CHAR_BUDGET) if sku_rendered else ""
    title_excerpt = _apply_text_budget(title_sanitized, _TEMPLATE_B_TITLE_CHAR_BUDGET) if title_rendered else ""
    subtitle_excerpt = _apply_text_budget(subtitle_sanitized, _TEMPLATE_B_SUBTITLE_CHAR_BUDGET) if subtitle_rendered else ""
    return {
        "top_copy_mode": resolved_behavior.top_copy_policy.mode if resolved_behavior.top_copy_policy else "title_subtitle_stack",
        "top_copy_hierarchy_mode": resolved_behavior.top_copy_policy.hierarchy_mode if resolved_behavior.top_copy_policy else "sku_meta_title_subtitle_catalog",
        "top_copy_region": {
            "rendered": bool(region_render_status.get("top_copy_region", {}).get("rendered", False)),
            "bounds": _template_b_top_copy_region_bounds(template),
        },
        "behavior_policy": {
            "region_ownership_policy": "top_copy_region_owns_sku_title_subtitle",
            "top_copy_hierarchy_mode": resolved_behavior.top_copy_policy.hierarchy_mode if resolved_behavior.top_copy_policy else "sku_meta_title_subtitle_catalog",
            "sku_char_budget": _TEMPLATE_B_SKU_CHAR_BUDGET,
            "title_char_budget": _TEMPLATE_B_TITLE_CHAR_BUDGET,
            "subtitle_char_budget": _TEMPLATE_B_SUBTITLE_CHAR_BUDGET,
            "title_line_clamp": 2,
            "subtitle_line_clamp": 1,
        },
        "sku_text_layer": {
            "layer_id": "sku_text_layer",
            "rendered": sku_rendered,
            "reason_code": layer_render_status.get("sku_text_layer", {}).get("reason_code"),
            "requested_text": requested_spec.sku_text,
            "sanitized_text": sku_sanitized,
            "rendered_excerpt": sku_excerpt,
            "truncation_applied": sku_rendered and sku_excerpt != sku_sanitized,
            "line_clamp": 1,
            "char_budget": _TEMPLATE_B_SKU_CHAR_BUDGET,
            "slot_bounds": _template_b_sku_slot_bounds(template),
            "owner_region": "top_copy_region",
        },
        "top_copy_title_layer": {
            "layer_id": "top_copy_title_layer",
            "rendered": title_rendered,
            "reason_code": layer_render_status.get("top_copy_title_layer", {}).get("reason_code"),
            "requested_text": requested_spec.title,
            "sanitized_text": title_sanitized,
            "rendered_excerpt": title_excerpt,
            "truncation_applied": title_rendered and title_excerpt != title_sanitized,
            "line_clamp": 2,
            "char_budget": _TEMPLATE_B_TITLE_CHAR_BUDGET,
            "slot_bounds": _text_slot_bounds(template.title_slot),
            "owner_region": "top_copy_region",
        },
        "top_copy_subtitle_layer": {
            "layer_id": "top_copy_subtitle_layer",
            "rendered": subtitle_rendered,
            "reason_code": layer_render_status.get("top_copy_subtitle_layer", {}).get("reason_code"),
            "requested_text": requested_spec.subtitle,
            "sanitized_text": subtitle_sanitized,
            "rendered_excerpt": subtitle_excerpt,
            "truncation_applied": subtitle_rendered and subtitle_excerpt != subtitle_sanitized,
            "line_clamp": 1,
            "char_budget": _TEMPLATE_B_SUBTITLE_CHAR_BUDGET,
            "slot_bounds": _text_slot_bounds(template.subtitle_slot),
            "owner_region": "top_copy_region",
        },
    }


def _build_description_contract_review(
    template: TemplateSpec,
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
    layer_render_status: dict[str, dict[str, object]],
    region_render_status: dict[str, dict[str, object]],
) -> dict[str, object]:
    if not _is_template_b_template(template):
        return {}

    title_sanitized = effective_spec.description_title or ""
    body_sanitized = effective_spec.description_body or ""
    title_rendered = bool(layer_render_status.get("description_title_layer", {}).get("rendered", False))
    body_rendered = bool(layer_render_status.get("description_body_layer", {}).get("rendered", False))
    title_excerpt = _apply_text_budget(title_sanitized, _TEMPLATE_B_DESCRIPTION_TITLE_CHAR_BUDGET) if title_rendered else ""
    body_excerpt = _apply_text_budget(body_sanitized, _TEMPLATE_B_DESCRIPTION_BODY_CHAR_BUDGET) if body_rendered else ""
    return {
        "description_mode": resolved_behavior.description_policy.mode if resolved_behavior.description_policy else "description_block",
        "description_density_mode": resolved_behavior.description_policy.density_mode if resolved_behavior.description_policy else "standard_block",
        "description_region": {
            "rendered": bool(region_render_status.get("description_region", {}).get("rendered", False)),
            "bounds": _template_b_description_region_bounds(template),
        },
        "behavior_policy": {
            "region_ownership_policy": "description_region_owns_description_title_and_body",
            "description_density_mode": resolved_behavior.description_policy.density_mode if resolved_behavior.description_policy else "standard_block",
            "title_char_budget": _TEMPLATE_B_DESCRIPTION_TITLE_CHAR_BUDGET,
            "body_char_budget": _TEMPLATE_B_DESCRIPTION_BODY_CHAR_BUDGET,
            "title_line_clamp": 1,
            "body_line_clamp": 5,
            "collapse_policy": "collapse_when_title_and_body_empty",
        },
        "description_title_layer": {
            "layer_id": "description_title_layer",
            "rendered": title_rendered,
            "reason_code": layer_render_status.get("description_title_layer", {}).get("reason_code"),
            "requested_text": requested_spec.description_title,
            "sanitized_text": title_sanitized,
            "rendered_excerpt": title_excerpt,
            "truncation_applied": title_rendered and title_excerpt != title_sanitized,
            "line_clamp": 1,
            "char_budget": _TEMPLATE_B_DESCRIPTION_TITLE_CHAR_BUDGET,
            "slot_bounds": _text_slot_bounds(template.description_title_slot) if template.description_title_slot else {"x": 0, "y": 0, "w": 0, "h": 0},
            "owner_region": "description_region",
        },
        "description_body_layer": {
            "layer_id": "description_body_layer",
            "rendered": body_rendered,
            "reason_code": layer_render_status.get("description_body_layer", {}).get("reason_code"),
            "requested_text": requested_spec.description_body,
            "sanitized_text": body_sanitized,
            "rendered_excerpt": body_excerpt,
            "truncation_applied": body_rendered and body_excerpt != body_sanitized,
            "line_clamp": 5,
            "char_budget": _TEMPLATE_B_DESCRIPTION_BODY_CHAR_BUDGET,
            "slot_bounds": _text_slot_bounds(template.description_body_slot) if template.description_body_slot else {"x": 0, "y": 0, "w": 0, "h": 0},
            "owner_region": "description_region",
        },
    }


def _build_title_text_layer_evidence(
    template: TemplateSpec,
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
    copy_optimization_review: dict[str, object] | None = None,
) -> dict[str, object]:
    if _is_template_b_template(template):
        rendered = bool(resolved_behavior.top_copy_policy and resolved_behavior.top_copy_policy.title_present)
        sanitized = effective_spec.title
        rendered_excerpt = _apply_text_budget(sanitized, _TEMPLATE_B_TITLE_CHAR_BUDGET) if rendered else ""
        return {
            "layer_id": "title_text_layer",
            "rendered": rendered,
            "slot_bounds": _text_slot_bounds(template.title_slot),
            "requested_text": requested_spec.title,
            "sanitized_text": sanitized,
            "rendered_excerpt": rendered_excerpt,
            "truncation_applied": rendered and rendered_excerpt != sanitized,
            "line_clamp": 2,
            "char_budget": _TEMPLATE_B_TITLE_CHAR_BUDGET,
            "owner_region": "top_copy_region",
            "ownership_frozen": True,
            "top_copy_mode": resolved_behavior.top_copy_policy.mode if resolved_behavior.top_copy_policy else "title_subtitle_stack",
        }

    bottom = resolved_behavior.bottom_policy
    rendered = bottom.title_slot_rendered
    char_budget = bottom.title_char_budget
    line_clamp = bottom.title_line_clamp
    sanitized = effective_spec.title
    rendered_excerpt = _apply_text_budget(sanitized, char_budget) if rendered else ""
    truncation_applied = rendered and len(sanitized) > len(rendered_excerpt)
    layout = bottom.layout_metrics
    slot_bounds = {
        "x": int(layout.get("title_band_x", template.title_slot.x)),
        "y": int(layout.get("title_slot_y", template.title_slot.y)),
        "w": int(layout.get("title_band_w", template.title_slot.w)),
        "h": int(layout.get("title_slot_height", template.title_slot.h)),
    }
    return {
        "layer_id": "title_text_layer",
        "rendered": rendered,
        "slot_bounds": slot_bounds,
        "requested_text": requested_spec.title,
        "sanitized_text": sanitized,
        "cleanup_text": (copy_optimization_review or {}).get("title", {}).get("cleanup_text", sanitized),
        "fit_rewrite_text": (copy_optimization_review or {}).get("title", {}).get("fit_rewrite_text", sanitized),
        "fit_rewrite_applied": bool((copy_optimization_review or {}).get("title", {}).get("fit_rewrite_applied", False)),
        "fit_rewrite_reason": (copy_optimization_review or {}).get("title", {}).get("fit_rewrite_reason", ""),
        "optimized_text": (copy_optimization_review or {}).get("title", {}).get("optimized_text", ""),
        "accepted_text": (copy_optimization_review or {}).get("title", {}).get("accepted_text", ""),
        "rendered_text_source": (copy_optimization_review or {}).get("title", {}).get("rendered_text_source", "sanitized_text"),
        "rendered_excerpt": rendered_excerpt,
        "truncation_applied": truncation_applied,
        "line_clamp": line_clamp,
        "char_budget": char_budget,
        "owner_region": _TEXT_LAYER_OWNER_MAP["title_text_layer"],
        "ownership_frozen": True,
        "bottom_layout_mode": bottom.bottom_layout_mode,
        "bottom_shell_top": bottom.bottom_shell_top,
    }


def _build_subtitle_text_layer_evidence(
    template: TemplateSpec,
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
    copy_optimization_review: dict[str, object] | None = None,
) -> dict[str, object]:
    if _is_template_b_template(template):
        rendered = bool(resolved_behavior.top_copy_policy and resolved_behavior.top_copy_policy.subtitle_present)
        sanitized = effective_spec.subtitle
        rendered_excerpt = _apply_text_budget(sanitized, _TEMPLATE_B_SUBTITLE_CHAR_BUDGET) if rendered else ""
        return {
            "layer_id": "subtitle_text_layer",
            "rendered": rendered,
            "slot_bounds": _text_slot_bounds(template.subtitle_slot),
            "requested_text": requested_spec.subtitle,
            "sanitized_text": sanitized,
            "rendered_excerpt": rendered_excerpt,
            "truncation_applied": rendered and rendered_excerpt != sanitized,
            "line_clamp": 1,
            "char_budget": _TEMPLATE_B_SUBTITLE_CHAR_BUDGET,
            "owner_region": "top_copy_region",
            "ownership_frozen": True,
            "top_copy_mode": resolved_behavior.top_copy_policy.mode if resolved_behavior.top_copy_policy else "title_subtitle_stack",
        }

    bottom = resolved_behavior.bottom_policy
    rendered = bottom.subtitle_slot_rendered
    char_budget = bottom.subtitle_char_budget
    line_clamp = bottom.subtitle_line_clamp
    sanitized = effective_spec.subtitle
    rendered_excerpt = _apply_text_budget(sanitized, char_budget) if rendered else ""
    truncation_applied = rendered and len(sanitized) > len(rendered_excerpt)
    layout = bottom.layout_metrics
    slot_bounds = {
        "x": int(layout.get("subtitle_slot_x", template.subtitle_slot.x)),
        "y": int(layout.get("subtitle_slot_y", template.subtitle_slot.y)),
        "w": int(layout.get("subtitle_slot_w", template.subtitle_slot.w)),
        "h": int(layout.get("subtitle_slot_height", template.subtitle_slot.h)),
    }
    return {
        "layer_id": "subtitle_text_layer",
        "rendered": rendered,
        "slot_bounds": slot_bounds,
        "requested_text": requested_spec.subtitle,
        "sanitized_text": sanitized,
        "cleanup_text": (copy_optimization_review or {}).get("subtitle", {}).get("cleanup_text", sanitized),
        "fit_rewrite_text": (copy_optimization_review or {}).get("subtitle", {}).get("fit_rewrite_text", sanitized),
        "fit_rewrite_applied": bool((copy_optimization_review or {}).get("subtitle", {}).get("fit_rewrite_applied", False)),
        "fit_rewrite_reason": (copy_optimization_review or {}).get("subtitle", {}).get("fit_rewrite_reason", ""),
        "optimized_text": (copy_optimization_review or {}).get("subtitle", {}).get("optimized_text", ""),
        "accepted_text": (copy_optimization_review or {}).get("subtitle", {}).get("accepted_text", ""),
        "rendered_text_source": (copy_optimization_review or {}).get("subtitle", {}).get("rendered_text_source", "sanitized_text"),
        "rendered_excerpt": rendered_excerpt,
        "truncation_applied": truncation_applied,
        "line_clamp": line_clamp,
        "char_budget": char_budget,
        "owner_region": _TEXT_LAYER_OWNER_MAP["subtitle_text_layer"],
        "ownership_frozen": True,
        "subtitle_slot_state": dict(bottom.subtitle_slot_state),
        "bottom_layout_mode": bottom.bottom_layout_mode,
        "bottom_shell_top": bottom.bottom_shell_top,
    }


def _build_header_text_layer_evidence(
    template: TemplateSpec,
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
    layer_render_status: dict[str, dict[str, object]],
) -> dict[str, object]:
    header = resolved_behavior.header_policy
    brand_rendered = bool(layer_render_status.get("brand_text_layer", {}).get("rendered", False))
    agent_rendered = bool(layer_render_status.get("agent_name_text_layer", {}).get("rendered", False))
    brand_sanitized = effective_spec.brand_name
    agent_sanitized = effective_spec.agent_name
    brand_excerpt = _apply_text_budget(brand_sanitized, header.brand_char_budget)
    agent_excerpt = _apply_text_budget(agent_sanitized, header.agent_char_budget) if header.agent_char_budget > 0 else ""
    metrics = header.layout_metrics
    agent_visual_font_size = (
        16
        if resolved_behavior.product_policy.product_geometry_mode == "family_a_fryer_hero_supporting_inset_v1"
        else int(template.agent_name_slot.font_size)
    )
    return {
        "layer_id": "header_text_layer",
        "rendered": brand_rendered or agent_rendered,
        "brand_text_slot": {
            "rendered": brand_rendered,
            "requested_text": requested_spec.brand_name,
            "sanitized_text": brand_sanitized,
            "rendered_excerpt": brand_excerpt if brand_rendered else "",
            "truncation_applied": brand_rendered and len(brand_sanitized) > len(brand_excerpt),
            "line_clamp": header.brand_line_clamp,
            "char_budget": header.brand_char_budget,
            "slot_bounds": {
                "x": int(metrics["brand_slot_x"]),
                "y": int(metrics["brand_slot_y"]),
                "w": int(metrics["brand_slot_w"]),
                "h": int(metrics["brand_slot_h"]),
            },
        },
        "agent_text_slot": {
            "rendered": agent_rendered,
            "requested_text": requested_spec.agent_name,
            "sanitized_text": agent_sanitized,
            "rendered_excerpt": agent_excerpt if agent_rendered else "",
            "truncation_applied": agent_rendered and len(agent_sanitized) > len(agent_excerpt),
            "line_clamp": header.agent_line_clamp,
            "char_budget": header.agent_char_budget,
            "visual_font_size": agent_visual_font_size,
            "slot_bounds": {
                "x": int(metrics["agent_slot_x"]),
                "y": int(metrics["agent_slot_y"]),
                "w": int(metrics["agent_slot_w"]),
                "h": int(metrics["agent_slot_h"]),
            },
        },
        "owner_region": "logo_banner_region" if _is_template_b_template(template) else _TEXT_LAYER_OWNER_MAP["header_text_layer"],
        "ownership_frozen": True,
        "header_mode": header.mode,
        "identity_zone_mode": header.identity_zone_mode,
        "agent_pill_visible": header.agent_pill_visible,
    }
