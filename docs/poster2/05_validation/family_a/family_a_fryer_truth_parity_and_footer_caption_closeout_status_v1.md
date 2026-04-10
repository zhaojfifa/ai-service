# Family A Fryer Truth Parity And Footer Caption Closeout Status v1

## Validation Scope

- Template A / Family A only
- fryer-only closeout
- same fryer sample input used for before/after runtime capture
- preview/request-state fixes not reopened

## Tests Run

- `./.venv/bin/python -m py_compile app/services/poster2/template_behavior.py app/services/poster2/pipeline.py app/services/poster2/renderer.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'fryer_annotation_contract_review_uses_resolved_positions_source or fryer_dense_quad_detail_row_adds_breathing or non_fryer_bottom_keeps_caption_mode_none or template_a_fryer_bottom_contract_review_exposes_caption_truth or annotation_contract_review_product_region_bounds_from_product_policy or fryer_variant_expands_product_text_shell_and_annotation_capacity or fryer_secondary_asset_keeps_single_primary_hero_and_supporting_inset'`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'fryer_dense_quad_gallery_markup_emits_semantic_captions or fryer_caption_helper_leaves_non_fryer_gallery_status_unchanged or resolve_feature_callout_map_uses_fryer_variant_annotation_bounds or fryer_variant_annotation_bounds or product_shell_boundary_closure'`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'template_a_regression_path_remains_unchanged or non_fryer_bottom_keeps_caption_mode_none'`

## Runtime Evidence

Before:

- preview screenshot: `/tmp/pr_fa_wysiwyg_before/preview.png`
- final screenshot: `/tmp/pr_fa_wysiwyg_before/final.png`
- metadata: `/tmp/pr_fa_wysiwyg_before/metadata.json`
- summary: `/tmp/pr_fa_wysiwyg_before/summary.json`

After:

- preview screenshot: `/tmp/pr_fa_wysiwyg_after/preview.png`
- final screenshot: `/tmp/pr_fa_wysiwyg_after/final.png`
- metadata: `/tmp/pr_fa_wysiwyg_after/metadata.json`
- summary: `/tmp/pr_fa_wysiwyg_after/summary.json`

Comparison sheets:

- preview comparison: `/tmp/pr_fa_wysiwyg_comparison_preview.png`
- final comparison: `/tmp/pr_fa_wysiwyg_comparison_final.png`

## Proved

- `structure_complete = true`
- `deliverable = true`
- `header_mode = identity_left_agent_right`
- `feature_mode = product_anchor_callouts`
- `product_annotation_owner = product_region`
- fixed 3 annotation slots remain present
- `bottom_mode = title_gallery_split`
- `gallery_mode = strip_local_visible_only`
- fryer annotation evidence changed from `template_spec_fixed` to `family_a_fryer_fixed_variant`
- fryer annotation bounds remain inside `product_region`
- final footer caption truth changed from:
  - `gallery_caption_mode = none`
  - no caption owner
  to:
  - `gallery_caption_mode = semantic_detail_caption_row`
  - `gallery_caption_owner = gallery_strip_region`
- final footer now consumes caption truth with the semantic order:
  1. Basket Detail
  2. Single Tank
  3. Lid Detail
  4. Dual Tank

## Before / After Runtime Delta

- product stage bounds unchanged:
  - primary `312x496 @ 460,214`
  - secondary `104x104 @ 486,596`
- fryer annotation bounds unified to resolved fryer slots:
  - before: `x=784 / y=216,316,416`
  - after: `x=796 / y=220,316,412`
- footer item bounds unchanged:
  - four items `172x80`
  - peer gap `18`
- footer expression changed:
  - before: image-only strip in final
  - after: thumbnail + caption row in final

## Non-Fryer Regression Guard

- non-fryer Family A bottom remains `gallery_caption_mode = none`
- existing Template A regression path test remains unchanged and passing

## Remaining Risks

- local screenshot generation used fallback system fonts because `NotoSansSC` files are not installed in this workspace
- this pass is bounded to fryer-only truth/parity closeout and does not reopen Family A redesign
