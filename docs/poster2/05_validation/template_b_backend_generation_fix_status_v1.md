# Template B Backend Generation Fix Status v1

## Scope

PR-TB-BE1 only.
Close the backend generation failure for `template_product_sheet_v1` without touching Template A runtime, Stage3/email closure, unrelated beautification, or the frozen bottom SOP baseline.

## Problem Statement

Template B frontend carry-through had already been split from Family A, but backend generation still failed with:

- `error = poster2_generation_failed`
- `message = reason_code`

The active failure was not request validation. It was backend runtime execution after the payload had already been accepted.

## Root Cause

Two Family A assumptions still leaked into the Template B backend path:

1. Puppeteer render still executed Family A gallery logic for Template B and dereferenced:
   - `slot_spec["layers"]["bottom_gallery_items_layer"]`
   - this raised `KeyError: 'bottom_gallery_items_layer'`

2. Pillow fallback and pipeline evidence still expected Family A bottom metadata:
   - `bottom_policy.subtitle_slot_state["reason_code"]`
   - Family B `description_block` stub had not populated that key

There was also one quality-guard carry-through bug:

3. `evaluate_deliverability(...)` only received `bottom_mode` as `binding_inputs`
   - Family B mandatory regions are derived from `brand_name`, `title`, `materials_images`, `description_*`, and product presence
   - this caused false missing-region failures during fallback deliverability checks

## Contract Truth Preserved

- `template_product_sheet_v1` remains Family B / product-sheet
- Template B does not reuse Family A bottom/gallery semantics
- Template A runtime behavior remains unchanged
- no geometry expansion was introduced
- no resend / Stage3 / email closure changes were made

## What Changed

### Renderer Path Split

- Puppeteer renderer now treats Template B as a no-gallery family
- Template B no longer enters Family A `bottom_gallery_items_layer` visibility math
- Template B now passes its own resolver inputs into Puppeteer behavior resolution:
  - `materials_count`
  - `description_title`
  - `description_body`
  - `sku_text`

### Template B Fallback Safety

- Added dedicated Template B renderer-side layer status builder
- Added dedicated Template B region status builder:
  - `logo_banner_region`
  - `top_copy_region`
  - `materials_strip_region`
  - `product_hero_region`
  - `description_region`

### Template B Stub Completeness

- Family B `description_block` bottom stub now emits a valid `subtitle_slot_state.reason_code`
- Template B bottom layout metrics now include safe defaults needed by downstream geometry/evidence consumers

### Quality Guard Binding Inputs

- Deliverability evaluation now receives the binding inputs needed for Family B:
  - `brand_name`
  - `title`
  - `subtitle`
  - `materials_images`
  - `description_title`
  - `description_body`
  - `product_image_present`
  - plus existing `bottom_mode`

### Error Observability

- `/api/v2/generate-poster` failure logging now records:
  - exception class
  - `reason_code` when present
  - failure stage when present
  - concrete detail string
- 500 response detail now includes:
  - `error`
  - `message`
  - `reason_code`
  - `exception_class`
  - `failure_stage`

## Exact Failure Reproduced

Local real-pipeline reproduction before the fix:

1. Puppeteer path failed with:
   - `KeyError: 'bottom_gallery_items_layer'`
   - classified as `stage=gallery_render`

2. Pillow fallback then failed with:
   - `KeyError: 'reason_code'`
   - from `bottom_policy.subtitle_slot_state["reason_code"]`

3. After those were fixed, deliverability still failed because Family B binding inputs were incomplete:
   - `fallback result does not satisfy minimum deliverable regions: logo_banner_region, product_hero_region, top_copy_region`

## Validation

- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py`
  - `27 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'product or annotation or single_primary or template_b'`
  - `81 passed, 191 deselected`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
  - `5 passed`

Representative coverage added:

- Template B primary image only
- Template B primary + secondary image
- Template B materials strip
- Template B empty materials path
- Template B empty description path
- Template A regression path
- API failure detail shape now carries concrete error metadata

## Compatibility Notes

- Template B remains backend-compatible with:
  - `materials_images=[]`
  - absent `product_secondary_image`
  - empty `description_title`
  - empty `description_body`
- Template B still prefers Puppeteer by metadata, but now degrades cleanly to Pillow when Puppeteer is unavailable

## Missing / Not Found During Read

- `docs/poster2/template_b_kitchen_center_hero_status_v1.md` was not present in this workspace
- this was recorded explicitly and did not block the PR

## One-Line State

Template B backend generation now succeeds end-to-end for accepted payload shapes, with Family B-specific renderer guards and concrete failure observability in place.
