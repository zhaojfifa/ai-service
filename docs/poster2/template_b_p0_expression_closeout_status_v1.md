# Template B P0 Expression Closeout Status v1

## Scope

This note records `PR-TB-P0A`, the contract-first expression closeout for `template_product_sheet_v1`.

It does not redesign Template B, change Family B geometry, or reopen Template A behavior.

## Goals Closed

- Added explicit Template B behavior truth for:
  - `header_visual_mode`
  - `top_copy_hierarchy_mode`
  - `materials_emphasis_mode`
  - `secondary_product_mode`
  - `description_density_mode`
- Made renderer consume those Template B mode classes instead of leaving them as implicit styling assumptions
- Exposed the new Family B expression modes in Stage2 diagnostics
- Added a compact short-description response path inside the existing `description_region`

## Effective Runtime Truth

Template B now exports these expression modes through backend metadata:

- `header_visual_mode = subdued_catalog_strip`
- `top_copy_hierarchy_mode = sku_meta_title_subtitle_catalog`
- `materials_emphasis_mode = evidence_strip_subordinate`
- `secondary_product_mode = inset_hidden_no_reserve` when no secondary asset
- `secondary_product_mode = inset_visible_supporting_detail` when a secondary asset exists
- `description_density_mode = compact_short_copy` for short copy
- `description_density_mode = standard_block` otherwise

## Files Changed

- `app/templates/specs/template_product_sheet_v1.json`
- `app/services/poster2/template_behavior.py`
- `app/services/poster2/pipeline.py`
- `app/services/poster2/renderer.py`
- `app/templates_html/template_product_sheet_v1.css`
- `frontend/stage2.html`
- `docs/stage2.html`
- `docs/app.js`
- `tests/poster2/test_contracts.py`
- `tests/poster2/test_pipeline.py`
- `tests/test_stage2_guard_diagnostics_surface.py`

## Validation

- `./.venv/bin/python -m py_compile app/services/poster2/template_behavior.py app/services/poster2/pipeline.py app/services/poster2/renderer.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_contracts.py -k 'product_sheet or behavior_modes'`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TemplateBBackendGenerationFix and (behavior_modes_surface_expression_closeout_truth or secondary_asset_reports_correct_layout_reason or description_evidence_emitted_when_description_fields_exist or product_hero_evidence_uses_consistent_full_width_owner_geometry)'`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py -k 'prefers_backend_product_and_bottom_runtime_evidence or docs_publish_mirror_contains_same_guard_diagnostics'`

## Remaining Gaps

- Header de-emphasis, hero de-fogging, materials visual subordination, and description visual tightening still belong to the next P0B renderer/CSS pass
- Stage1 / Stage2 operator-line cleanup still belongs to the next P0C frontend pass
- Live generated Template B samples should still be rechecked after P0B so visual output matches the now-explicit expression modes
