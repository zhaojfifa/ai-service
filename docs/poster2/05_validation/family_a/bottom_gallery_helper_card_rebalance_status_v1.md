# Bottom Gallery Helper Card Rebalance Status v1

## Scope

Validation status for `PR-BOTTOM-GALLERY-VIS1` only:

- Family A commercial fryer helper-image row only
- 4-slot bottom gallery only
- visual sizing rebalance only

This step does not change:

- bottom contract truth
- `bottom_mode` / `gallery_mode`
- caption ownership
- AI generation behavior
- Stage2 / Stage3 routing or production flow

## Bound Oracle

- template: `template_dual_v2`
- family: `Family A`
- bottom mode remains `title_gallery_split`
- gallery mode remains `strip_local_visible_only`
- fryer helper row remains `dense_quad_detail_row`
- caption owner remains `gallery_strip_region`

## Applied Visual Rebalance

- helper card height increased from `90` to `100`
- helper shell height tightened from `116` to `106` so the taller cards stay inside the accepted bottom frame
- media bounds increased from `140x56` to `142x71`
- caption bounds reduced from `140x14` to `142x12`
- captioned helper cards now prefer `object-fit: contain` instead of `cover`

## Validation

- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'title_gallery_split_fryer_dense_quad_detail_row_adds_breathing or template_a_fryer_bottom_contract_review_exposes_caption_truth'`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'fryer_dense_quad_gallery_markup_emits_semantic_captions'`

## Acceptance

Accepted when:

1. four helper-image cards remain balanced across the same 4-slot row
2. media area gains readable vertical space without changing bottom truth
3. captions remain present but visually weaker than the helper imagery
4. fryer-only dense-quad caption truth stays reviewable in metadata
