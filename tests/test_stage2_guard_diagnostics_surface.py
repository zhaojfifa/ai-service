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
    assert "annotationReview, scenarioReview, titleTextLayer, subtitleTextLayer, headerTextLayer)" in html


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
    assert "buildProductDetail(productReview, annotationReview)" in html
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


def test_docs_publish_mirror_contains_same_guard_diagnostics():
    frontend_html = (ROOT / "frontend" / "stage2.html").read_text(encoding="utf-8")
    frontend_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    docs_html = (ROOT / "docs" / "stage2.html").read_text(encoding="utf-8")
    docs_js = (ROOT / "docs" / "app.js").read_text(encoding="utf-8")

    assert docs_html == frontend_html
    assert docs_js == frontend_js


def test_stage2_annotation_detail_surfaces_shell_and_text_placement_mode():
    frontend_html = (ROOT / "frontend" / "stage2.html").read_text(encoding="utf-8")

    assert "buildProductAnnotationDetail" in frontend_html
    assert "annotation_shell?.bounds" in frontend_html
    assert "text_placement_mode" in frontend_html
    assert "connector:" in frontend_html
    assert "marker:" in frontend_html


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
