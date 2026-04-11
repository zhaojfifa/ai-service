# Family A Single-Primary Support Surface Status v1

## Status

Complete.

## Validation

- `./.venv/bin/python -m py_compile app/services/poster2/template_behavior.py app/services/poster2/pipeline.py app/services/poster2/renderer.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'support_surface or fryer_secondary_asset_keeps_single_primary_hero_and_supporting_inset or template_a_fryer_bottom_contract_review_exposes_caption_truth or template_a_regression_path_remains_unchanged'`

## Evidence Checked

- support surface renders in Family A fryer `single_primary` / `inset_hidden_no_reserve` / no-secondary state when gallery item 1 exists
- support surface collapses when gallery item 1 is unavailable
- source is recorded as `bottom_gallery_item_1_asset` or `bottom_gallery_item_1_unavailable`
- mode is recorded as `family_a_fryer_single_primary_bottom_gallery_1_support_surface` when active
- bounds are recorded as `{x:472, y:594, w:136, h:104}` when active
- caption reuses `gallery_caption_slot_1` text when available
- bottom gallery slot 1 and caption slot 1 remain present on the bottom contract path
- existing fryer secondary-inset path remains unchanged
- Template A regression path remains deliverable

## Remaining Risks

- local validation is structural and focused; full visual screenshot capture was not run in this pass
