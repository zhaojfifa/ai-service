# Family A Fryer Truth Parity And Footer Caption Closeout v1

## Scope

- Template A / Family A only
- fryer-only closeout
- contract-first
- no Template B work
- no Stage1/Stage2 request-state reopen
- no bottom redesign

## Problem

Preview/final direction was mostly aligned, but two Family A fryer gaps remained open:

1. `product_annotation_contract_review` still leaked stale `template_spec_fixed` evidence in fryer paths even though fryer annotation bounds were already resolved from `product_policy`
2. HTML preview already expressed fryer footer as thumbnail + caption, but Pillow final still rendered an image-only strip because footer caption truth was not formalized and consumed end-to-end

There was also a bounded presentation mismatch inside the frozen fryer product-region family:

- Pillow final annotation chips still read heavier than preview
- fryer hero-plane presentation needed a tighter grounded/frosted finish without changing Family A ownership or slot behavior

## Contract / Resolver Changes

### Product annotation evidence

- `product_annotation_contract_review` now reads fryer slot geometry, marker policy, connector policy, and `positions_source` from resolved `product_policy.annotation_items`
- fryer-only review evidence no longer rebuilds slot truth from template-spec defaults
- fryer review now reports `family_a_fryer_fixed_variant` consistently where fryer product policy already resolved that variant

### Footer caption truth

`ResolvedBottomBehavior` now exposes bounded caption truth for the fryer detail-row path:

- `gallery_caption_mode`
- `gallery_caption_owner`
- `gallery_caption_slots`

For the fryer dense quad detail row:

- `gallery_caption_mode = semantic_detail_caption_row`
- `gallery_caption_owner = gallery_strip_region`
- caption order remains:
  1. Basket Detail
  2. Single Tank
  3. Lid Detail
  4. Dual Tank

Non-fryer Family A paths continue to expose `gallery_caption_mode = none`.

## Renderer Consumption

### Pillow footer

- `LayoutRenderer._draw_gallery()` now consumes footer caption truth
- fryer detail-row items render as bounded thumbnail cards with media bounds plus caption bounds instead of image-only strips
- gallery ownership remains `gallery_strip_region`

### Pillow product-region refinement

- fryer-only hero plane and supporting inset shell remain inside the existing product-region family
- fryer annotation cards use a lighter frosted treatment in Pillow so final reads closer to approved preview without changing slot ownership or anchor behavior
- single-primary + supporting-inset structure remains unchanged

## Files Changed

- `app/services/poster2/template_behavior.py`
- `app/services/poster2/pipeline.py`
- `app/services/poster2/renderer.py`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_renderer.py`

## Acceptance

- fryer annotation evidence is unified with resolved product truth
- final footer is a true thumbnail + caption row
- fixed 3 annotation slots remain unchanged
- product annotations remain product-owned and inside `product_region`
- bottom remains `title_gallery_split`
- gallery remains `strip_local_visible_only`
