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
from dataclasses import asdict, replace
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
from .region_matrix import _BOTTOM_MODE_COLLAPSED_BY_DESIGN
from .renderer import LayoutRenderer, RendererSelector, render_product_material_debug_layer
from .renderer_routing import assert_quality_guard_deliverable
from .template_behavior import (
    _FROZEN_PRODUCT_OWNER_SURFACES,
    _PRODUCT_ANNOTATION_OWNER_SLOT,
    resolve_template_behavior,
)
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
        requested_spec = spec
        effective_spec = _normalize_contract_text_spec(spec)

        if template is None:
            template = load_template(effective_spec.template_id)
        else:
            validate_template_registration(template)
        run_preflight_guard(template, effective_spec)

        spec_hash = _hash_spec(effective_spec)
        gallery_counts = _gallery_contract_counts(effective_spec)

        # ── Phase 1: background layer + product/material layer preparation ───
        t0 = _now()
        if effective_spec.template_id == "template_dual_v2":
            assets = await self._loader.load(effective_spec)
            if assets.scenario is not None:
                bg_result = await build_template_dual_v2_background(
                    assets.scenario,
                    width=effective_spec.size[0],
                    height=effective_spec.size[1],
                    trace_id=trace_id,
                )
            else:
                bg_result = await self._bg.generate(
                    style_prompt="",
                    negative_prompt=effective_spec.style.negative_prompt,
                    width=effective_spec.size[0],
                    height=effective_spec.size[1],
                    seed=effective_spec.style.seed,
                    template_hint=template.background_prompt_hint,
                    trace_id=trace_id,
                )
        else:
            assets, bg_result = await asyncio.gather(
                self._loader.load(effective_spec),
                self._bg.generate(
                    style_prompt=effective_spec.style.prompt,
                    negative_prompt=effective_spec.style.negative_prompt,
                    width=effective_spec.size[0],
                    height=effective_spec.size[1],
                    seed=effective_spec.style.seed,
                    template_hint=template.background_prompt_hint,
                    trace_id=trace_id,
                ),
            )
        timings["load_and_bg_ms"] = _elapsed(t0)
        timings["background_layer_ms"] = timings["load_and_bg_ms"]
        resolved_behavior = resolve_template_behavior(
            template,
            feature_count=len([item for item in effective_spec.features if item and item.strip()]),
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
        fg_result = await self._renderer.render(template, effective_spec, assets)
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
        inferred_region_render_status = _build_region_render_status(inferred_layer_render_status)
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
            binding_inputs={"bottom_mode": resolved_behavior.bottom_policy.effective_mode},
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
            bg_image, fg_result.image, effective_spec.export_format
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

        ext = effective_spec.export_format
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
            ),
            "scenario_contract_review": _build_scenario_contract_review(
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
            ),
            "subtitle_text_layer": _build_subtitle_text_layer_evidence(
                template,
                requested_spec=requested_spec,
                effective_spec=effective_spec,
                resolved_behavior=resolved_behavior,
            ),
            "header_text_layer": _build_header_text_layer_evidence(
                template,
                requested_spec=requested_spec,
                effective_spec=effective_spec,
                resolved_behavior=resolved_behavior,
                layer_render_status=layer_render_status,
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
            geometry_evidence=renderer_metadata_payload["geometry_evidence"],
            hero_contract_review=renderer_metadata_payload["hero_contract_review"],
            product_contract_review=renderer_metadata_payload["product_contract_review"],
            header_contract_review=renderer_metadata_payload["header_contract_review"],
            feature_contract_review=renderer_metadata_payload["feature_contract_review"],
            bottom_contract_review=renderer_metadata_payload["bottom_contract_review"],
            product_annotation_contract_review=renderer_metadata_payload["product_annotation_contract_review"],
            scenario_contract_review=renderer_metadata_payload["scenario_contract_review"],
            title_text_layer=renderer_metadata_payload["title_text_layer"],
            subtitle_text_layer=renderer_metadata_payload["subtitle_text_layer"],
            header_text_layer=renderer_metadata_payload["header_text_layer"],
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


def _normalize_contract_text_spec(spec: PosterSpec) -> PosterSpec:
    brand_name = _normalize_requested_text(spec.brand_name)
    agent_name = _normalize_requested_text(spec.agent_name)
    title = _normalize_requested_text(spec.title)
    subtitle = _normalize_requested_text(spec.subtitle)
    features = tuple(
        normalized
        for item in spec.features
        if (normalized := _normalize_requested_text(item))
    )
    if not brand_name:
        raise ValueError("brand_name must not be empty after normalization")
    if not title:
        raise ValueError("title must not be empty after normalization")
    gallery_counts = _gallery_contract_counts(spec)
    return replace(
        spec,
        brand_name=brand_name,
        agent_name=agent_name,
        title=title,
        subtitle=subtitle,
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


def _build_layer_render_status(
    *,
    template: TemplateSpec,
    spec: PosterSpec,
    assets,
    bg_result: BackgroundResult,
    behavior,
) -> dict[str, dict[str, object]]:
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
    layer_status: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
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


def _build_geometry_evidence(
    template: TemplateSpec,
    *,
    resolved_behavior,
    layer_render_status: dict[str, dict[str, object]],
    region_render_status: dict[str, dict[str, object]],
) -> dict[str, object]:
    return {
        "region_bounds": {
            "header_region": _header_region_bounds(template, resolved_behavior),
            "scenario_region": _scenario_region_bounds(template, resolved_behavior),
            "bottom_region": _bottom_region_bounds(template, resolved_behavior),
            "title_band_region": _title_band_region_bounds(template, resolved_behavior),
            "product_region": _product_region_bounds(template, resolved_behavior),
            "gallery_strip_region": _gallery_strip_region_bounds(template, resolved_behavior),
        },
        "slot_bounds": {
            "brand_logo_slot": _header_logo_slot_bounds(template, resolved_behavior),
            "brand_name_slot": _brand_name_slot_bounds(template, resolved_behavior),
            "agent_name_slot": _agent_name_slot_bounds(template, resolved_behavior),
            "title_slot": _title_slot_bounds(template, resolved_behavior),
            "subtitle_slot": _subtitle_slot_bounds(template, resolved_behavior),
            "scenario_slot": _scenario_slot_bounds(template, resolved_behavior),
            "product_slot": _product_slot_bounds(template, resolved_behavior),
            "product_primary_slot": _product_primary_slot_bounds(resolved_behavior),
            "product_secondary_slot": _product_secondary_slot_bounds(resolved_behavior),
            "gallery_slot": _gallery_item_slot_bounds(template, resolved_behavior),
        },
        "visible_item_count": {
            "header_region": int(region_render_status.get("header_region", {}).get("count", 0)),
            "scenario_region": int(region_render_status.get("scenario_region", {}).get("count", 0)),
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
        "y": int(layout["bottom_shell_top"]),
        "w": 832,
        "h": int(layout["bottom_shell_height"]),
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
    metrics = resolved_behavior.hero_policy.layout_metrics
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
        "x": 112,
        "y": int(layout["title_band_top"]),
        "w": 800,
        "h": int(layout["title_band_height"]),
    }


def _gallery_strip_region_bounds(template: TemplateSpec, resolved_behavior) -> dict[str, int]:
    layout = resolved_behavior.bottom_policy.layout_metrics
    return {
        "x": int(layout.get("gallery_shell_x", template.gallery_slot.x)),
        "y": int(layout["gallery_shell_top"]),
        "w": int(layout.get("gallery_shell_w", template.gallery_slot.w)),
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
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
    region_render_status: dict[str, dict[str, object]],
) -> dict[str, object]:
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
            "bottom_text_emphasis_policy": resolved_behavior.bottom_policy.bottom_text_emphasis_policy,
            "title_line_clamp": resolved_behavior.bottom_policy.title_line_clamp,
            "subtitle_line_clamp": resolved_behavior.bottom_policy.subtitle_line_clamp,
            "title_char_budget": resolved_behavior.bottom_policy.title_char_budget,
            "subtitle_char_budget": resolved_behavior.bottom_policy.subtitle_char_budget,
            "layout_metrics": dict(resolved_behavior.bottom_policy.layout_metrics),
        },
        "collapsed_optional_slots": list(resolved_behavior.bottom_policy.collapsed_optional_slots),
        "subtitle_slot": dict(resolved_behavior.bottom_policy.subtitle_slot_state),
        "gallery_slots": gallery_slots,
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
    return {
        "header_mode": resolved_behavior.header_policy.mode,
        "requested_brand_text": requested_spec.brand_name,
        "requested_agent_text": requested_spec.agent_name,
        "sanitized_brand_text": effective_spec.brand_name,
        "sanitized_agent_text": effective_spec.agent_name,
        "rendered_brand_excerpt": brand_excerpt,
        "rendered_agent_excerpt": agent_excerpt,
        "brand_truncation_applied": brand_excerpt != effective_spec.brand_name,
        "agent_truncation_applied": agent_excerpt != effective_spec.agent_name,
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


def _build_title_text_layer_evidence(
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
) -> dict[str, object]:
    bottom_policy = resolved_behavior.bottom_policy
    rendered = bottom_policy.title_slot_rendered
    sanitized_text = effective_spec.title
    rendered_excerpt = (
        _apply_text_budget(sanitized_text, bottom_policy.title_char_budget)
        if rendered
        else ""
    )
    layout_metrics = dict(bottom_policy.layout_metrics)
    slot_y = int(layout_metrics.get("title_slot_y", layout_metrics.get("title_band_top", 0)))
    slot_h = int(layout_metrics.get("title_slot_height", 0))
    return {
        "layer_id": "title_text_layer",
        "rendered": rendered,
        "slot_bounds": {"x": 112, "y": slot_y, "w": 800, "h": slot_h},
        "requested_text": requested_spec.title,
        "sanitized_text": sanitized_text,
        "rendered_excerpt": rendered_excerpt,
        "truncation_applied": rendered and rendered_excerpt != sanitized_text,
        "line_clamp": bottom_policy.title_line_clamp,
        "char_budget": bottom_policy.title_char_budget,
        "owner_region": "title_band_region",
    }


def _build_subtitle_text_layer_evidence(
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
) -> dict[str, object]:
    bottom_policy = resolved_behavior.bottom_policy
    rendered = bottom_policy.subtitle_slot_rendered
    sanitized_text = effective_spec.subtitle
    rendered_excerpt = (
        _apply_text_budget(sanitized_text, bottom_policy.subtitle_char_budget)
        if rendered
        else ""
    )
    layout_metrics = dict(bottom_policy.layout_metrics)
    slot_y = int(layout_metrics.get("subtitle_slot_y", layout_metrics.get("title_band_top", 0)))
    slot_h = int(layout_metrics.get("subtitle_slot_height", 0))
    return {
        "layer_id": "subtitle_text_layer",
        "rendered": rendered,
        "slot_bounds": {"x": 152, "y": slot_y, "w": 720, "h": slot_h},
        "requested_text": requested_spec.subtitle,
        "sanitized_text": sanitized_text,
        "rendered_excerpt": rendered_excerpt,
        "truncation_applied": rendered and rendered_excerpt != sanitized_text,
        "line_clamp": bottom_policy.subtitle_line_clamp,
        "char_budget": bottom_policy.subtitle_char_budget,
        "owner_region": "title_band_region",
    }


def _build_header_text_layer_evidence(
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
) -> dict[str, object]:
    header_policy = resolved_behavior.header_policy
    brand_excerpt = _apply_text_budget(effective_spec.brand_name, header_policy.brand_char_budget)
    agent_rendered = header_policy.agent_pill_visible
    agent_excerpt = (
        _apply_text_budget(effective_spec.agent_name, header_policy.agent_char_budget)
        if agent_rendered
        else ""
    )
    metrics = header_policy.layout_metrics
    return {
        "layer_id": "header_text_layer",
        "rendered": bool(effective_spec.brand_name),
        "brand_text_slot": {
            "rendered": bool(effective_spec.brand_name),
            "requested_text": requested_spec.brand_name,
            "sanitized_text": effective_spec.brand_name,
            "rendered_excerpt": brand_excerpt,
            "truncation_applied": brand_excerpt != effective_spec.brand_name,
            "line_clamp": header_policy.brand_line_clamp,
            "char_budget": header_policy.brand_char_budget,
            "slot_bounds": {
                "x": int(metrics.get("brand_slot_x", 244)),
                "y": int(metrics.get("brand_slot_y", 88)),
                "w": int(metrics.get("brand_slot_w", 416)),
                "h": int(metrics.get("brand_slot_h", 36)),
            },
        },
        "agent_text_slot": {
            "rendered": agent_rendered,
            "requested_text": requested_spec.agent_name,
            "sanitized_text": effective_spec.agent_name,
            "rendered_excerpt": agent_excerpt,
            "truncation_applied": agent_rendered and agent_excerpt != effective_spec.agent_name,
            "line_clamp": 1,
            "char_budget": header_policy.agent_char_budget,
            "slot_bounds": {
                "x": int(metrics.get("agent_slot_x", 684)),
                "y": int(metrics.get("agent_slot_y", 96)),
                "w": int(metrics.get("agent_slot_w", 228)),
                "h": int(metrics.get("agent_slot_h", 18)),
            },
        },
        "owner_region": "header_region",
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
) -> dict[str, object]:
    product_policy = resolved_behavior.product_policy
    rendered_items = []
    annotation_slots = []
    requested_items = list(requested_spec.features[: product_policy.max_annotation_items])
    sanitized_items = list(effective_spec.features[: product_policy.max_annotation_items])
    for index in range(product_policy.max_annotation_items):
        requested_text = requested_items[index] if index < len(requested_items) else ""
        sanitized_text = sanitized_items[index] if index < len(sanitized_items) else ""
        rendered = (
            product_policy.annotation_mode != "none"
            and index < product_policy.visible_annotation_count
            and bool(sanitized_text)
        )
        rendered_excerpt = (
            _apply_text_budget(sanitized_text, product_policy.char_budget)
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
                "requested_text": requested_text,
                "sanitized_text": sanitized_text,
                "rendered_excerpt": rendered_excerpt,
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
        "product_canvas_shell_layer": {
            "rendered": bool(layer_render_status.get("product_canvas_shell_layer", {}).get("rendered", False)),
            "reason_code": layer_render_status.get("product_canvas_shell_layer", {}).get("reason_code"),
            "bounds": {
                "x": int(layout_metrics["product_region_x"]),
                "y": int(layout_metrics["product_region_y"]),
                "w": int(layout_metrics["product_region_w"]),
                "h": int(layout_metrics["product_region_h"]),
            },
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
        "product_primary_slot": dict(product_policy.product_primary_slot),
        "product_secondary_slot": dict(product_policy.product_secondary_slot) if product_policy.product_secondary_slot else None,
        "product_secondary_slot_rendered": product_policy.product_secondary_slot_rendered,
        "product_secondary_asset_policy": product_policy.product_secondary_asset_policy,
        "owner_surfaces": sorted(_FROZEN_PRODUCT_OWNER_SURFACES),
        "annotation_owner_slot": _PRODUCT_ANNOTATION_OWNER_SLOT,
        "secondary_slot_annotation_ownership": False,
        "behavior_policy": {
            "annotation_count_policy": product_policy.annotation_count_policy,
            "annotation_connector_policy": product_policy.annotation_connector_policy,
            "annotation_marker_policy": product_policy.annotation_marker_policy,
            "annotation_shell_policy": product_policy.annotation_shell_policy,
            "annotation_bounds_policy": product_policy.annotation_bounds_policy,
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
            _apply_text_budget(text, resolved_behavior.feature_policy.char_budget)
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
        rendered_excerpt = _apply_text_budget(sanitized_text, resolved_behavior.feature_policy.char_budget) if slot_rendered else ""
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
) -> dict[str, object]:
    feature_policy = resolved_behavior.feature_policy
    product_policy = resolved_behavior.product_policy
    annotation_mode = product_policy.annotation_mode
    if annotation_mode == "none":
        return {
            "product_annotation_mode": "none",
            "annotation_active": False,
            "annotation_slots": [],
            "product_region": {
                "rendered": bool(region_render_status.get("product_region", {}).get("rendered", False)),
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
        is_visible = i < product_policy.visible_annotation_count and bool(sanitized_text)
        rendered_excerpt = (
            _apply_text_budget(sanitized_text, product_policy.char_budget)
            if is_visible
            else ""
        )
        if i < len(template.feature_callouts):
            fc = template.feature_callouts[i]
            lb = fc.label_box
            anchor_x = int(fc.anchor_x)
            anchor_y = int(fc.anchor_y)
            label_bounds = {"x": int(lb.x), "y": int(lb.y), "w": int(lb.w), "h": int(lb.h)}
            anchor_color = fc.anchor_color
        else:
            anchor_x = None
            anchor_y = None
            label_bounds = None
            anchor_color = None
        slot_reviews.append({
            "slot_index": i,
            "slot_id": f"annotation_slot_{i + 1}",
            "rendered": is_visible,
            "requested_text": requested_text,
            "sanitized_text": sanitized_text,
            "rendered_excerpt": rendered_excerpt,
            "truncation_applied": rendered_excerpt != sanitized_text,
            "anchor_x": anchor_x,
            "anchor_y": anchor_y,
            "label_bounds": label_bounds,
            "connector_policy": feature_policy.connector_policy,
            "annotation_owner": "product_region",
            "marker_policy": "dot_marker_accent_color",
            "positions_source": "template_spec_fixed",
            "anchor_color": anchor_color,
        })

    return {
        "product_annotation_mode": annotation_mode,
        "annotation_active": True,
        "max_slots": max_slots,
        "visible_slot_count": product_policy.visible_annotation_count,
        "annotation_slots": slot_reviews,
        "product_region": {
            "rendered": bool(region_render_status.get("product_region", {}).get("rendered", False)),
            "bounds": {
                "x": int(resolved_behavior.hero_policy.layout_metrics["product_region_x"]),
                "y": int(resolved_behavior.hero_policy.layout_metrics["product_region_y"]),
                "w": int(resolved_behavior.hero_policy.layout_metrics["product_region_w"]),
                "h": int(resolved_behavior.hero_policy.layout_metrics["product_region_h"]),
            },
        },
        "behavior_policy": {
            "visible_item_count_policy": feature_policy.visible_item_count_policy,
            "connector_policy": product_policy.annotation_connector_policy,
            "marker_policy": "dot_marker_accent_color",
            "box_policy": feature_policy.box_policy,
            "start_strategy": feature_policy.start_strategy,
            "char_budget": product_policy.char_budget,
            "line_clamp": product_policy.line_clamp,
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


def _build_title_text_layer_evidence(
    template: TemplateSpec,
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
) -> dict[str, object]:
    bottom = resolved_behavior.bottom_policy
    rendered = bottom.title_slot_rendered
    char_budget = bottom.title_char_budget
    line_clamp = bottom.title_line_clamp
    sanitized = effective_spec.title
    rendered_excerpt = _apply_text_budget(sanitized, char_budget) if rendered else ""
    truncation_applied = rendered and len(sanitized) > len(rendered_excerpt)
    layout = bottom.layout_metrics
    slot_bounds = {
        "x": template.title_slot.x,
        "y": int(layout.get("title_slot_y", template.title_slot.y)),
        "w": template.title_slot.w,
        "h": int(layout.get("title_slot_height", template.title_slot.h)),
    }
    return {
        "layer_id": "title_text_layer",
        "rendered": rendered,
        "slot_bounds": slot_bounds,
        "requested_text": requested_spec.title,
        "sanitized_text": sanitized,
        "rendered_excerpt": rendered_excerpt,
        "truncation_applied": truncation_applied,
        "line_clamp": line_clamp,
        "char_budget": char_budget,
        "owner_region": "title_band_region",
        "bottom_layout_mode": bottom.bottom_layout_mode,
        "bottom_shell_top": bottom.bottom_shell_top,
    }


def _build_subtitle_text_layer_evidence(
    template: TemplateSpec,
    *,
    requested_spec: PosterSpec,
    effective_spec: PosterSpec,
    resolved_behavior,
) -> dict[str, object]:
    bottom = resolved_behavior.bottom_policy
    rendered = bottom.subtitle_slot_rendered
    char_budget = bottom.subtitle_char_budget
    line_clamp = bottom.subtitle_line_clamp
    sanitized = effective_spec.subtitle
    rendered_excerpt = _apply_text_budget(sanitized, char_budget) if rendered else ""
    truncation_applied = rendered and len(sanitized) > len(rendered_excerpt)
    layout = bottom.layout_metrics
    slot_bounds = {
        "x": template.subtitle_slot.x,
        "y": int(layout.get("subtitle_slot_y", template.subtitle_slot.y)),
        "w": template.subtitle_slot.w,
        "h": int(layout.get("subtitle_slot_height", template.subtitle_slot.h)),
    }
    return {
        "layer_id": "subtitle_text_layer",
        "rendered": rendered,
        "slot_bounds": slot_bounds,
        "requested_text": requested_spec.subtitle,
        "sanitized_text": sanitized,
        "rendered_excerpt": rendered_excerpt,
        "truncation_applied": truncation_applied,
        "line_clamp": line_clamp,
        "char_budget": char_budget,
        "owner_region": "title_band_region",
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
            "line_clamp": 1,
            "char_budget": header.agent_char_budget,
            "slot_bounds": {
                "x": int(metrics["agent_slot_x"]),
                "y": int(metrics["agent_slot_y"]),
                "w": int(metrics["agent_slot_w"]),
                "h": int(metrics["agent_slot_h"]),
            },
        },
        "owner_region": "header_region",
        "header_mode": header.mode,
        "identity_zone_mode": header.identity_zone_mode,
        "agent_pill_visible": header.agent_pill_visible,
    }
