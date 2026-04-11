# Family A Fryer Hero Lift And Anchor Rebind Status v1

## Validation Scope

- Template A / Family A only
- fryer-only blocker pass
- same deterministic fryer sample used for before / after capture
- no footer redesign reopened
- no global visual polish reopened

## Tests Run

- `./.venv/bin/python -m py_compile app/services/poster2/template_behavior.py app/services/poster2/pipeline.py app/services/poster2/renderer.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'fryer_annotation_contract_review_uses_resolved_positions_source or fryer_secondary_asset_keeps_single_primary_hero_and_supporting_inset or fryer_variant_expands_product_text_shell_and_annotation_capacity'`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'resolve_feature_callout_map_uses_fryer_variant_annotation_bounds or product_annotation_wait_uses_resolved_fryer_label_bounds'`

## Runtime Evidence

Before:

- screenshot: `/tmp/fryer_anchor_before/before.png`
- metadata: `/tmp/fryer_anchor_before/metadata.json`
- summary: `/tmp/fryer_anchor_before/summary.json`

After:

- screenshot: `/tmp/fryer_anchor_after/after.png`
- metadata: `/tmp/fryer_anchor_after/metadata.json`
- summary: `/tmp/fryer_anchor_after/summary.json`

Comparison:

- sheet: `/tmp/fryer_anchor_compare/before_after.png`

## Proven

- `structure_complete = true`
- `deliverable = true`
- header remains 3-column
- `product_annotation_owner = product_region`
- fixed 3 annotation slots remain present
- `bottom_mode = title_gallery_split`
- annotation shell remains inside `product_region`
- primary hero slot and secondary inset now have non-overlapping vertical separation

## Before / After Runtime Delta

- anchor source:
  - before: `family_a_fryer_fixed_variant`
  - after: `family_a_fryer_visible_box_derived`
- anchor positions:
  - before: `x=764 / y=250,350,450`
  - after: `x=702 / y=258,354,450`
- product primary slot:
  - before: `x=460, y=214, w=312, h=496`
  - after: `x=460, y=192, w=312, h=384`
- product secondary slot:
  - before: `x=486, y=596, w=104, h=104`
  - after: `x=486, y=596, w=104, h=104`
- product region bounds:
  - before: `x=456, y=188, w=516, h=540`
  - after: `x=456, y=188, w=516, h=540`
- annotation shell bounds:
  - before: `x=796, y=220, w=176, h=268`
  - after: `x=796, y=220, w=176, h=268`
- vertical separation:
  - before: primary bottom `710` overlapped inset top `596`
  - after: primary bottom `576` clears inset top `596` by `20px`

## Visual Readout

- slot 1 now lands on the fryer hero body instead of floating at the old right-edge coordinate
- the supporting inset reads as a separate lower detail because the primary hero no longer overlaps its reserve zone
- the hero still keeps breathing room above the banner

## Remaining Risks

- the runtime capture used fallback system fonts because local `NotoSansSC` font files are missing in this workspace
- this is runtime metadata from this workspace, not deployed live metadata from the external environment

## Visual Rebalance Addendum

### Tests Run

- `./.venv/bin/python -m py_compile app/services/poster2/template_behavior.py app/services/poster2/pipeline.py app/services/poster2/renderer.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'fryer_annotation_contract_review_uses_resolved_positions_source or fryer_secondary_asset_keeps_single_primary_hero_and_supporting_inset or fryer_variant_expands_product_text_shell_and_annotation_capacity or title_gallery_split_fryer_dense_quad_detail_row_adds_breathing'`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'resolve_feature_callout_map_uses_fryer_variant_annotation_bounds or product_annotation_wait_uses_resolved_fryer_label_bounds'`

### Runtime Evidence

Before:

- screenshot: `/tmp/fryer_visual_rebalance_before/before.png`
- metadata: `/tmp/fryer_visual_rebalance_before/metadata.json`
- summary: `/tmp/fryer_visual_rebalance_before/summary.json`

After:

- screenshot: `/tmp/fryer_visual_rebalance_after/after.png`
- metadata: `/tmp/fryer_visual_rebalance_after/metadata.json`
- summary: `/tmp/fryer_visual_rebalance_after/summary.json`

Comparison:

- sheet: `/tmp/fryer_visual_rebalance_compare/before_after.png`

### Before / After Runtime Delta

- product region:
  - before: `x=456, y=188, w=516, h=540`
  - after: `x=424, y=188, w=516, h=540`
- product canvas:
  - before: `x=456, y=188, w=316, h=540`
  - after: `x=424, y=188, w=316, h=540`
- annotation shell:
  - before: `x=796, y=220, w=176, h=268`
  - after: `x=764, y=220, w=176, h=268`
- anchors:
  - before: `x=702 / y=258,354,450`
  - after: `x=670 / y=258,354,450`
- footer card bounds:
  - before: `w=172, h=80`
  - after: `w=164, h=92`
- footer media bounds:
  - before: `w=156, h=46`
  - after: `w=148, h=58`

### Proven

- `bottom_mode = title_gallery_split`
- `gallery_caption_mode = semantic_detail_caption_row`
- `structure_complete = true`
- `deliverable = true`
- annotations remain inside `product_region`
- 4 gallery items and captions remain rendered
