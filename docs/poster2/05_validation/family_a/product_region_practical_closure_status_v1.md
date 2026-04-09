# Family A Product Region Practical Closure Status v1

## Scope

Validation status for the first practical beautification closure step on Family A product-region work.

This step covers:

- product shell polish
- annotation shell / leader / marker polish
- Stage2 product-region observability

This step does not cover:

- bottom-region practical closure
- Gemini copy optimizer integration
- Template B

## Bound Oracle

- template: `template_dual_v2`
- family: `Family A`
- canonical live sample: `annotation_triplet_gallery_triplet_subtitle_present`
- frozen control truth preserved:
  - `hero_mode = scenario_cover_product_contain`
  - `feature_mode = product_anchor_callouts`
  - `product_annotation_mode = product_anchor_callouts`
  - `bottom_mode = title_gallery_split`
  - `gallery_mode = strip_local_visible_only`
  - `product_layout_mode = single_primary`
  - `secondary_product_mode = inset_hidden_no_reserve`

## Practical Observability Surface

The Stage2 product detail panel now exposes:

- `product_layout_mode`
- `secondary_product_mode`
- `product_annotation_owner`
- `visible_annotation_count`

The same fields are present in backend `product_contract_review`.

## Validation Run

- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'product or family_a or accepted_output_keys'`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py`

## Expected Stable Anchors

- `tests/poster2/fixtures/family_a_visual_smoke.json`
- `tests/poster2/fixtures/family_a_runtime_rebaseline_smoke.json`
- `tests/poster2/fixtures/family_a_accepted_output_keys.json`

## Acceptance

Accepted when:

1. Family A visual smoke matches the refreshed practical-closure fixture
2. pipeline metadata exposes the product-region observability fields
3. Stage2 surfaces the same product-region backend truth
4. no Template B residue is introduced
5. no Family A geometry or ownership drift occurs
