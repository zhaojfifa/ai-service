# Template B Line 2 Independent Flow Status v1

## Scope

PR-TB-LINE2 closes the remaining Stage1 -> Stage2 -> generate-path coupling that still made `template_product_sheet_v1` behave like Family A in several places.

This pass is limited to:

- Stage1 preview independence
- Stage2 family-aware panel switching
- dedicated Template B serializer
- request-state carry-through for Template B fields
- runtime guards for optional arrays / optional media
- frontend/docs mirror sync

It does not change:

- Family A runtime behavior
- bottom SOP baseline
- `product_anchor_callouts` path in Template A
- Stage3 / Resend / email closure
- product / header / bottom geometry truth

## Problem Statement

Template B had become only partially split from Family A:

1. Stage1 Material Preview / Layout Preview still rendered Family A dual-column assumptions
2. Stage2 still showed Family A copy/bottom surfaces
3. generate could crash after payload assembly with `Cannot read properties of undefined (reading 'map')`
4. Template B fields were collected in Stage1 but not carried through a clean independent family line

## What Was Read First

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/product_region_annotation_contract_status_v1.md`
- `docs/poster2/bottom_behavior_contract_status_v1.md`

Additional notes:

- `docs/poster2/template_b_kitchen_center_hero_status_v1.md` is missing in this workspace
- no tracked latest Stage2 screenshot / console / network evidence bundle was present in the workspace
- branch inspection was done first on:
  - `claude/flamboyant-mclaren`
  - `claude/gracious-allen`

## Root Cause

The Template B path was a half-split implementation:

- Stage1 preview still used `updatePosterPreview()` and `buildLayoutPreview()` with Family A scenario/product/gallery assumptions
- Stage2 family switching only hid the bottom panel; it did not replace the Family A copy model with a Template B summary surface
- the Template B serializer path still fed later audit/debug logic that assumed `posterPayload.gallery_items` existed, which caused the observed `undefined.map` crash
- the prior Template B generate branch still used the older `/api/generate-poster` shape, while Template B field compatibility already existed on `/api/v2/generate-poster`

## Contract Truth Preserved

The fix does not change poster contract truth:

- Template A ownership stays unchanged
- bottom semantics stay unchanged
- product annotation ownership stays unchanged
- Family A `product_anchor_callouts` stays frozen
- no geometry / region-bound drift was introduced

## What Changed

### 1. Stage1 preview independence

Added a dedicated Template B preview surface and branch:

- Family A preview remains in `preview-family-a`
- Template B preview now renders in `preview-family-b`
- Template B preview shows:
  - logo / brand / agent banner
  - title / subtitle / SKU block
  - materials strip
  - centered primary product hero
  - optional secondary detail image
  - description block

If optional sections are absent, they collapse cleanly.

### 2. Stage2 UI independence

Template family switching now uses `template_id` / `template_variant` as the single source of truth:

- hides Family A-only copy/bottom surfaces for Template B
- keeps Bottom Region controls hidden for Template B
- disables `puppeteer` for Template B in the renderer selector
- shows a dedicated Template B summary block with:
  - title
  - subtitle
  - SKU
  - description title
  - description body
  - materials preview state
  - primary / secondary product state

### 3. Dedicated Template B serializer

Added `buildTemplateBPosterPayload(...)` and moved Template B generation onto `/api/v2/generate-poster`.

Template B payload now carries only B-relevant fields:

- `template_id = template_product_sheet_v1`
- `brand_name`
- `agent_name`
- `title`
- `subtitle`
- `sku_text`
- `description_title`
- `description_body`
- `product_image`
- `product_secondary_image`
- `materials_images`

It intentionally does not send Family A-only generation fields:

- scenario fields
- gallery fields
- bottom mode controls
- old feature/callout editing payload

### 4. Runtime guards

The active crash was closed by removing Family A assumptions from Template B follow-on logic:

- `gallery: (posterPayload.gallery_items || []).map(...)`
- Template B materials normalization now defaults arrays to `[]`
- secondary image and materials paths remain optional

## Request Normalization Rules

- Stage1 Template B state still stores:
  - `sku_text`
  - `description_title`
  - `description_body`
  - `materials_images`
  - `product_image_1`
  - `product_image_2`
- Stage2 hydrates those values without converting them into Family A copy or bottom fields
- final generate request for Template B is now a dedicated v2 payload, not a patched Family A payload

## Compatibility Notes

- no backend schema patch was required
- Template B compatibility was verified against `/api/v2/generate-poster`
- Template A path remains unchanged
- single-primary fallback remains valid when the secondary image is absent

## Validation / Tests

- `node --check frontend/app.js` -> pass
- `bash scripts/sync_frontend_to_docs.sh` -> synced `index.html`, `stage2.html`, `app.js`, `styles.css`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` -> `5 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py` -> `25 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'single_primary'` -> `3 passed`

## One-line State

Template B is now an independent Stage1 -> Stage2 -> `/api/v2/generate-poster` working line, with Family A preview/control assumptions removed from its active operator path.
