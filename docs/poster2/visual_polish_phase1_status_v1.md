# visual polish phase1 status v1

## Scope

PR-10A only: visual hierarchy polish for `template_dual_v2` without changing contract truth or geometry truth.

This round is limited to:

- header optical balance
- scenario attention softening
- product primary-secondary hierarchy polish
- callout pill refinement
- bottom title/subtitle emphasis rebalance
- gallery strip evidence styling

## Frozen Unchanged

- `feature_mode = product_anchor_callouts`
- `feature_region` remains suppressed under active product annotation
- `product_text_shell` remains a right-side sibling shell
- product primary slot / secondary slot / annotation shell bounds unchanged
- `bottom_mode = title_gallery_split`
- `gallery_mode = strip_local_visible_only`
- no region-bound changes
- no ownership changes
- no resend / email / storage changes
- no contract expansion

## What Changed

### Header optical balance

- softened header shell border / shadow weight
- added mild glass blur to the header shell
- slightly improved brand / agent tracking and agent line-height for cleaner right-lane reading

### Scenario attention softening

- reduced visual dominance of the real scenario image through a softer treatment filter
- kept scenario shell and layout truth unchanged
- product remains the stronger visual subject in the peer region

### Product hierarchy polish

- strengthened outer product card shell presence without changing bounds
- increased primary product image shadow presence
- softened secondary product image opacity/treatment so it reads as supporting, not competing

### Callout pill refinement

- moved callout cards to a cleaner pill surface with lighter shadow and refined border
- softened connectors and improved marker halo/shadow
- preserved anchored-callout ownership, count, and bounds

### Bottom emphasis rebalance

- increased title weight / optical tracking slightly
- reduced subtitle size, saturation, and opacity so subtitle no longer competes with title
- preserved bottom shell, title band, gallery strip, and slot geometry

### Gallery strip evidence styling

- refined gallery strip surface into a lighter frosted panel
- added subtle gallery-item border polish
- preserved gallery count, placement, and distribution policy

## Files Changed

- `app/templates_html/template_dual_v2.css`
- `tests/poster2/test_renderer.py`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/visual_polish_phase1_status_v1.md`
- `docs/poster2/README.md`

## Validation / Tests

- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'template_css_exposes_peer_region_fit_policies or template_css_exposes_visual_polish_phase1_without_geometry_tokens_drift or HeaderAndTitleBandLayoutControl or template_html_marks_real_scenario_when_asset_exists or text_only_expanded_html_keeps_full_width_text_layer_vars'`
  - `8 passed, 97 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TestProductLayoutContract or TestTask2FinalProductGeometry or TestProductImageContract or TestBottomModeFamilyContractClosure'`
  - `32 passed, 228 deselected`

Out-of-scope note:

- `tests/poster2/test_pipeline.py::TestPosterPipelineRun::test_renderer_metadata_includes_layer_render_status` currently fails on `template_layout_policy.layout_density_mode == balanced` vs `bottom_dense`
- this is a pre-existing metadata assertion mismatch outside PR-10A visual-polish scope and was not changed here

## Remaining Risks

- final visual quality still needs human render review in production-like examples
- CSS polish is intentionally light; stronger art-direction changes would require a later, explicitly scoped visual phase

## One-line State

Phase 1 visual polish is now in place for header, scenario, product, callout pills, bottom emphasis, and gallery styling without any geometry or ownership drift.
