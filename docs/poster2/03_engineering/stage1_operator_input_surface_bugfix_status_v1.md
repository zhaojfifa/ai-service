# stage1 operator input surface bugfix status v1

## Problem Statement

Two Stage1 operator usability gaps remained open while the poster2 contract baseline was already frozen:

1. the secondary product image was optional in backend/runtime truth, but Stage1 had no explicit operator-facing clear/remove action
2. product explanation input was still operator-framed as generic bullets, while live production truth already routes product explanations into product-owned annotation/callout surfaces

At the same time, bottom subtitle semantics were already frozen and could not be repurposed into product explanation truth.

## Contract Truth Preserved

This pass preserves the current poster2 runtime truth:

- product explanation remains product-owned
- product callouts continue to flow through the canonical `features` payload surface under active product annotation
- bottom subtitle remains bottom-owned support copy semantics
- single-primary fallback remains valid when the secondary product image is absent
- no geometry, ownership, or renderer-routing changes were introduced

## Why Secondary Image Remove Is Valid

The secondary product image is already optional in backend request/renderer truth:

- `product_secondary_image` is nullable at the request boundary
- single-primary fallback is already a valid runtime path

So Stage1 remove/clear is not a schema expansion. It is an operator-facing bugfix that finally exposes the already-valid optional state.

## Why Subtitle Remains Bottom Support Copy

Subtitle continues to represent bottom support copy only:

- Stage1 now labels it as `Bottom Support Copy`
- Stage2 bottom editing also labels it as `Bottom Support Copy`
- the field still maps to canonical backend `subtitle`
- it is not auto-copied into product callouts

This preserves bottom contract semantics and avoids mixing product explanation with bottom text ownership.

## New Product Callout Input Surface

Stage1 now exposes three dedicated product callout inputs:

- `Callout 1`
- `Callout 2`
- `Callout 3`

These match the operator mental model and the live fixed-3 product annotation slot truth better than generic bullet wording.

## Request Normalization Rules

The new UI does not add a new backend schema field.

Normalization rules:

- Stage1 UI fields: `product_callouts[0..2]`
- Stage1 storage keeps:
  - `product_callouts`
  - compatibility aliases in `features`
  - compatibility aliases in `bullets`
- Stage2 poster2 request prefers:
  - `stage1Data.product_callouts`
  - then legacy `stage1Data.features`
  - then legacy `stage1Data.bullets`
- bottom support copy continues to map to canonical `subtitle`
- cleared secondary image removes `product_image_2` from Stage1 state, so `/api/v2/generate-poster` receives `product_secondary_image: null`

## Compatibility Notes

- older Stage1 data with only `features` or `bullets` still works
- older Stage1 data with `tagline` still hydrates into the new bottom support copy field
- no backend request or response schema was redesigned
- no resend / storage / email transport work was touched

Workspace note:

- there is no standalone `frontend/stage1.html` or `docs/stage1.html` in this repo
- Stage1 source/publish entry is `frontend/index.html` and `docs/index.html`

## Tests / Validation

- `node --check frontend/app.js`
  - pass
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py`
  - `23 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'product or annotation or single_primary'`
  - `73 passed, 190 deselected`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
  - `4 passed`

## One-line State

Stage1 input surfaces are now aligned with live contract truth: secondary product image is explicitly removable, bottom support copy stays bottom-owned, and product callouts have a dedicated operator input surface that normalizes into the existing product-owned annotation path.
