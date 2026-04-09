from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_frontend_stage2_surfaces_guard_diagnostic_fields():
    html = (ROOT / "frontend" / "stage2.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")

    for marker in (
        "poster2-structure-complete",
        "poster2-incomplete-structure",
        "poster2-deliverable",
        "poster2-missing-mandatory-regions",
        "poster2-missing-required-slots",
        "poster2-region-render-status",
        "poster2-slot-binding-status",
        "poster2-template-behavior",
        "poster2-geometry-evidence",
        "poster2-bottom-contract-review",
        "poster2-title-text-layer",
        "poster2-subtitle-text-layer",
        "poster2-header-text-layer",
        "poster2-bottom-mode",
        "poster2-gallery-mode",
        "poster2-gallery-count",
        "poster2-bottom-request-preview",
        "poster2-product-contract-review",
        "poster2-copy-optimization-review",
        "poster2-visible-truth-evidence",
        "poster2-template-b-parity-review",
        'maxlength="120"',
    ):
        assert marker in html

    for field in (
        "structure_complete",
        "incomplete_structure",
        "deliverable",
        "missing_mandatory_regions",
        "missing_required_slots",
        "region_render_status",
        "slot_binding_status",
        "template_behavior",
        "geometry_evidence",
        "bottom_contract_review",
        "title_text_layer",
        "subtitle_text_layer",
        "header_text_layer",
        "product_contract_review",
        "copy_optimization_review",
        "visible_truth_evidence",
        "template_b_parity_review",
        "bottom_mode",
        "gallery_mode",
        "normalisePoster2BottomText",
        "requested_title_text",
        "requested_subtitle_text",
        "sanitized_title_text",
        "sanitized_subtitle_text",
        "title_source",
        "subtitle_source",
        "gallery_input_count_raw",
        "gallery_input_count_normalized",
        "gallery_requested_count",
        "gallery_autofill_applied",
        "exceeds max length",
        "STAGE2_PROD_API_BASE",
        "isDeprecatedApiBase",
        "https://ai-service-leob.onrender.com",
    ):
        assert field in js

    assert "bottomContract.subtitle || stage1Data.subtitle" not in js
    assert "https://ai-service-leob.onrender.com" in html


def test_frontend_stage2_surfaces_scenario_contract_review():
    """Prove that Stage 2 reads scenario evidence from the backend payload.

    Checks:
    1. HTML element poster2-scenario-contract-review is present.
    2. buildScenarioDetail() function is defined and uses the dedicated payload.
    3. scenario_region display uses buildScenarioDetail when scenarioReview is present.
    4. Fallback to buildHeroDetail remains present for backward compatibility.
    5. app.js binds scenario_contract_review from the backend response.
    """
    html = (ROOT / "frontend" / "stage2.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")

    # 1. Hidden storage element
    assert "poster2-scenario-contract-review" in html

    # 2. Dedicated detail builder function is defined
    assert "function buildScenarioDetail" in html

    # 3. scenario_region display branch uses buildScenarioDetail with the new payload
    assert "buildScenarioDetail(scenarioReview)" in html

    # 4. Backward-compatible fallback to hero detail when payload is absent
    assert "buildHeroDetail(heroReview, 'scenario_region')" in html

    # 5. JS writes the backend field to the DOM element
    assert "poster2-scenario-contract-review" in js
    assert "scenario_contract_review" in js

    # 6. renderResolverLayout receives scenarioReview and product/text-layer payloads
    #    as parameters (not relying on outer-scope access which would be undefined)
    assert "renderResolverLayout(" in html
    assert "annotationReview, scenarioReview, titleTextLayer, subtitleTextLayer, headerTextLayer, parityReview, copyOptimizationReview)" in html
    assert "parityReview" in html


def test_frontend_stage2_prefers_backend_product_and_bottom_runtime_evidence():
    html = (ROOT / "frontend" / "stage2.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")

    assert "requested/effective:" in html
    assert "bottom_mode_override_reason" in html
    assert "textRow('title', titleTextLayer.requested_text" in html
    assert "textRow('subtitle', subtitleTextLayer.requested_text" in html
    assert "buildHeaderDetail(headerReview, headerTextLayer)" in html
    assert "poster2-title-text-layer" in html
    assert "poster2-subtitle-text-layer" in html
    assert "poster2-header-text-layer" in html
    assert "buildProductDetail(productReview, annotationReview, copyOptimizationReview)" in html
    assert "header in-banner" in html
    assert "top-copy in-region" in html
    assert "hero in-region" in html
    assert "description in-region" in html
    assert "header-visual" in html
    assert "top-copy-hierarchy" in html
    assert "materials-emphasis" in html
    assert "secondary-product" in html
    assert "description-density" in html
    assert "poster2-template-b-parity-review" in html
    assert "poster2-visible-truth-evidence" in html
    assert "product_secondary_image_layer" in html
    assert "product_secondary_slot" in html
    assert "syncPoster2BottomContractFromControls(stage1Data)" in js
    assert "bottom_mode: bottomRequestState.bottom_mode" in js
    assert "product_secondary_image:" in js
    assert "layout mode:" in html
    assert "bottom_layout_mode" in html
    assert "requested/effective:" in html
    assert "text_gallery_expanded" in html
    assert "gallery_only" in html
    assert 'option value="title_only"' in html
    assert 'option value="title_only_expand"' not in html
    assert "canonicalizePoster2BottomMode" in js
    assert "title_only_expand: 'text_only_expanded'" in js
    assert "bottomMode.value = canonicalBottomMode" in js
    assert "bottom_mode: canonicalBottomMode" in js


def test_frontend_stage2_template_a_text_only_expanded_preview_uses_backend_bottom_truth():
    js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    css = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")

    assert "function resolvePoster2PreviewBottomState" in js
    assert "stage2State.poster2.latestResult = data || null;" in js
    assert "review?.effective_bottom_mode" in js
    assert "review?.subtitle_slot?.rendered" in js
    assert "review?.gallery_strip_region?.rendered" in js
    assert "root.classList.toggle('poster-preview--text-only-expanded', isTextOnlyExpanded);" in js
    assert "galleryRow.classList.toggle('hidden', galleryCollapsed);" in js
    assert "gallerySubtitleEl.classList.toggle('hidden', galleryCollapsed);" in js
    assert "bottomSubtitleEl.classList.toggle('hidden', !subtitleVisible);" in js
    assert ".poster-preview--text-only-expanded .poster-tagline" in css


def test_frontend_stage2_template_a_support_copy_mapping_stays_on_canonical_subtitle():
    js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")

    assert "function resolveTemplateABottomSupportCopy" in js
    assert "const subtitle = typeof source?.subtitle === 'string' ? source.subtitle.trim() : '';" in js
    assert "const legacyTagline = typeof source?.tagline === 'string' ? source.tagline.trim() : '';" in js
    assert "subtitle: resolveTemplateABottomSupportCopy(stage1Data, '')," in js
    assert "poster.subtitle = resolveTemplateABottomSupportCopy(snapshot, '');" in js
    assert "requested_subtitle_text" in js
    assert "sanitized_subtitle_text" in js


def test_frontend_stage2_surfaces_family_a_bottom_region_observability_cards():
    html = (ROOT / "frontend" / "stage2.html").read_text(encoding="utf-8")
    docs_html = (ROOT / "docs" / "stage2.html").read_text(encoding="utf-8")

    assert "subtitle_slot.state" in html
    assert "title_rendered" in html
    assert "subtitle_rendered" in html
    assert "gallery_distribution_policy" in html
    assert "const titleRendered = bottomReview?.title_slot_rendered" in html
    assert "const subtitleRendered = bottomReview?.subtitle_slot_rendered" in html
    assert "const subtitleState = bottomReview?.subtitle_slot?.state" in html
    assert "const galleryDistribution = bottomReview?.gallery_distribution_policy" in html
    assert docs_html == html


def test_frontend_stage2_surfaces_family_a_copy_optimization_controls_and_trace():
    html = (ROOT / "frontend" / "stage2.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    docs_html = (ROOT / "docs" / "stage2.html").read_text(encoding="utf-8")
    docs_js = (ROOT / "docs" / "app.js").read_text(encoding="utf-8")

    assert "poster2-copy-optimization-panel" in html
    assert "poster2-copy-optimization-mode" in html
    assert "poster2-copy-optimization-accept" in html
    assert "poster2-copy-optimization-reject" in html
    assert "poster2-copy-optimization-actions" in html
    assert "poster2-copy-optimization-toggle" in html
    assert "poster2-copy-optimization-lineage" in html
    assert "poster2-copy-optimization-summary" in html
    assert "poster2-copy-optimization-review" in html

    assert "function ensurePoster2CopyOptimizationState" in js
    assert "function buildPoster2CopyLineageRow" in js
    assert "function buildPoster2AnnotationOptimizationRows" in js
    assert "function buildPoster2CopyOptimizationSummary" in js
    assert "function buildPoster2CopyOptimizationLineage" in js
    assert "function renderPoster2CopyOptimizationReview" in js
    assert "function initPoster2CopyOptimizationControls" in js
    assert "copy_optimization:" in js
    assert "accepted_title" in js
    assert "accepted_subtitle" in js
    assert "accepted_features" in js
    assert "changed_fields" in js
    assert "disabled_reason" in js
    assert "actionable" in js
    assert "mode: 'suggest'" in js
    assert "requested_text ->" in js
    assert "sanitized_text ->" in js
    assert "cleanup_text ->" in js
    assert "fit_rewrite_text ->" in js
    assert "optimized_text ->" in js
    assert "accepted_text ->" in js
    assert "rendered_text ->" in js
    assert "rendered_text_source ->" in js
    assert "Show lineage" in js
    assert "Hide lineage" in js
    assert "toggleBtn.textContent = 'Show lineage';" in js
    assert "lineage.classList.toggle('hidden'" in js
    assert "actions.classList.toggle('hidden', !showActions);" in js

    assert docs_html == html
    assert docs_js == js


def test_docs_publish_mirror_contains_same_guard_diagnostics():
    frontend_html = (ROOT / "frontend" / "stage2.html").read_text(encoding="utf-8")
    frontend_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    docs_html = (ROOT / "docs" / "stage2.html").read_text(encoding="utf-8")
    docs_js = (ROOT / "docs" / "app.js").read_text(encoding="utf-8")

    assert docs_html == frontend_html
    assert docs_js == frontend_js


def test_frontend_stage2_surfaces_product_text_shell_evidence():
    """Prove that Stage2 reads product_text_shell evidence from the backend payload.

    Checks:
    1. text_shell status chip is present in buildProductDetail (reads product_text_shell_layer from payload).
    2. text_does_not_compete_with_canvas badge is present.
    3. owner_region / owner_surface are displayed.
    4. char_budget and line_clamp are displayed from behavior_policy.
    5. sanitized_text is referenced in the annotation slot text chain.
    6. feature_region continues to show delegated diagnostic (not a parallel owner).
    7. docs/stage2.html mirrors frontend/stage2.html exactly.
    """
    html = (ROOT / "frontend" / "stage2.html").read_text(encoding="utf-8")
    docs_html = (ROOT / "docs" / "stage2.html").read_text(encoding="utf-8")

    # 1. text_shell chip reads product_text_shell_layer from backend payload
    assert "product_text_shell_layer?.rendered" in html
    assert "product_text_shell_layer?.reason_code" in html

    # 2. no-compete badge is gated on backend truth
    assert "text_does_not_compete_with_canvas" in html

    # 3. owner_region / owner_surface displayed
    assert "textShell.owner_region" in html
    assert "textShell.owner_surface" in html

    # 4. char_budget and line_clamp from behavior_policy
    assert "char_budget" in html
    assert "line_clamp" in html
    assert "behavior_policy?.char_budget" in html
    assert "behavior_policy?.line_clamp" in html

    # 5. sanitized_text in annotation slot chain
    assert "sanitized_text" in html
    assert "sanitizedDiffers" in html

    # 6. feature_region delegated diagnostic badge is still present
    assert "delegated to product_annotation" in html

    # 7. docs mirror is identical
    assert docs_html == html


def test_frontend_stage2_surfaces_family_a_product_region_observability_cards():
    html = (ROOT / "frontend" / "stage2.html").read_text(encoding="utf-8")
    css = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")
    docs_html = (ROOT / "docs" / "stage2.html").read_text(encoding="utf-8")
    docs_css = (ROOT / "docs" / "styles.css").read_text(encoding="utf-8")

    assert "secondary_product_mode" in html
    assert "product_annotation_owner" in html
    assert "visible_annotation_count" in html
    assert "const secondaryMode = productReview.secondary_product_mode || '';" in html
    assert "const annotationOwner = productReview.product_annotation_owner || '';" in html
    assert "const visibleCount =" in html
    assert "function buildAnnotationLineageCard" in html
    assert "slot_fixed" in html
    assert "char_budget" in html
    assert "line_clamp" in html
    assert "rendered_excerpt:" in html
    assert "cleanup:" in html
    assert "fit_rewrite:" in html
    assert "accepted:" in html
    assert "rendered_source:" in html
    assert "truncation_applied:" in html
    assert "optimized:" in html
    assert "s2-diagnostics-grid" in html
    assert "s2-diagnostic-card" in css
    assert "s2-diagnostic-key" in css
    assert "s2-diagnostic-val" in css
    assert docs_html == html
    assert docs_css == css


def test_api_response_schema_exposes_scenario_and_annotation_contract_review():
    """Prove that GeneratePosterV2Response schema and main.py both surface
    scenario_contract_review and product_annotation_contract_review.

    Checks:
    1. Pydantic schema (app/schemas/poster2.py) declares both fields.
    2. main.py response constructor forwards both fields from the manifest.
    """
    schema_src = (ROOT / "app" / "schemas" / "poster2.py").read_text(encoding="utf-8")
    main_src = (ROOT / "app" / "main.py").read_text(encoding="utf-8")

    # Schema must declare both fields
    assert "scenario_contract_review" in schema_src
    assert "product_annotation_contract_review" in schema_src

    # main.py must forward both fields in the response constructor
    assert "scenario_contract_review=manifest.scenario_contract_review" in main_src
    assert "product_annotation_contract_review=manifest.product_annotation_contract_review" in main_src
    assert "visible_truth_evidence" in schema_src
    assert "template_b_parity_review" in schema_src
    assert "copy_optimization_review" in schema_src
    assert "visible_truth_evidence=manifest.visible_truth_evidence" in main_src
    assert "template_b_parity_review=manifest.template_b_parity_review" in main_src
    assert "copy_optimization_review=manifest.copy_optimization_review" in main_src
