# Template B Contract Correction Status v1

## Scope

PR-TB-CONTRACT1 only.
Correct Template B contract ownership so `template_product_sheet_v1` behaves as a clean Family B contract-driven line.

Out of scope:

- Family A runtime behavior
- bottom SOP for Template A
- `product_anchor_callouts` in Template A
- email / storage / Stage3
- broad beautification

## Executive Summary

Template B already had its own region order and a stable structured runtime path, but its resolver and metadata still emitted several Family A semantics.

This pass corrected Template B at the contract / resolver / evidence layers:

- header mode is now `logo_banner_lockup`, not `brand_only`
- `brand_logo_slot` remains renderable in Template B
- title / subtitle ownership now resolves to `top_copy_region`
- Template B now emits explicit `top_copy_contract_review` and `description_contract_review`
- full-width hero evidence is now internally consistent (`product_canvas_shell_layer.w = 800`)
- hidden Family A product text-shell residues are zeroed / marked unused for Template B
- `bottom_contract_review` is reduced to description-only scope and no longer claims title / subtitle ownership

## Root Rules Followed

- contract-first
- behavior before beautification
- renderer executes contract truth; renderer does not define it
- Template A frozen behavior preserved
- Stage2 diagnostics remain backend-evidence-driven

## Problem Reproduced

Current Template B runtime metadata still showed Family A leakage:

- `header_contract_review.header_mode = "brand_only"`
- `header_contract_review.brand_logo_slot.rendered = false`
- `title_text_layer.owner_region = "title_band_region"`
- `subtitle_text_layer.owner_region = "title_band_region"`
- `rendered_title_excerpt = ""` and `rendered_subtitle_excerpt = ""` despite Template B text being present
- `product_primary_slot.w = 800` while `product_canvas_shell_w = 300`
- `product_text_shell_layer` still emitted Family A text-shell geometry
- `bottom_contract_review` still carried title / subtitle request semantics

## Root Cause

Template B was only partially split from Family A:

1. The Template B behavior resolver hard-coded `header_mode = "brand_only"` and returned `header_mode = "brand_only"` even though Template B has a real logo-banner shell.
2. Shared text-layer evidence builders still treated `title_text_layer` / `subtitle_text_layer` as frozen Family A bottom-owned layers.
3. Shared product evidence builders still emitted Family A canvas-shell and text-shell geometry even when Template B resolved to `single_hero_centered`.
4. Shared bottom review builders still assumed title-band semantics even when Template B title / subtitle were rendered in `top_copy_region`.
5. Renderer-side Template B layer status emitted only a partial Family B map, forcing the final payload to inherit Family A fallback assumptions for some shell evidence.

## Exact Contract Leaks Removed

### Header

- `template_product_sheet_v1.behavior_modes.header_mode`
  - from `brand_only`
  - to `logo_banner_lockup`
- Template B header review now maps to `logo_banner_region`
- `brand_logo_slot` remains renderable when logo input exists

### Top Copy

- `title_text_layer.owner_region`
  - from `title_band_region`
  - to `top_copy_region`
- `subtitle_text_layer.owner_region`
  - from `title_band_region`
  - to `top_copy_region`
- Added `top_copy_contract_review` with:
  - `sku_text_layer`
  - `top_copy_title_layer`
  - `top_copy_subtitle_layer`

### Product Hero

- Template B `product_canvas_shell_layer` now uses the full hero width
- Template B `product_text_shell_layer` now resolves to zero bounds with `reason_code = not_used_in_template_b`
- Template B `product_layout_mode_reason` now reflects secondary-asset presence:
  - `single_hero_centered_without_secondary_asset`
  - `single_hero_centered_with_secondary_inset`

### Description

- Added `description_contract_review` with:
  - `description_title_layer`
  - `description_body_layer`
- `bottom_contract_review` now scopes to `description_region_only`
- Template B bottom review explicitly excludes `sku_text`, `title`, and `subtitle` ownership

## Files Changed

- `app/templates/specs/template_product_sheet_v1.json`
- `app/services/poster2/template_behavior.py`
- `app/services/poster2/pipeline.py`
- `app/services/poster2/renderer.py`
- `app/services/poster2/slot_contracts.py`
- `app/services/poster2/contracts.py`
- `app/schemas/poster2.py`
- `app/main.py`
- `tests/poster2/test_pipeline.py`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/template_b_contract_correction_status_v1.md`
- `docs/poster2/README.md`

## Layer Changed

- contract
- validation
- resolver / behavior wiring
- renderer consumption
- evidence / metadata
- docs

## Tests Run

- `./.venv/bin/python -m py_compile app/services/poster2/template_behavior.py app/services/poster2/pipeline.py app/services/poster2/renderer.py app/main.py app/schemas/poster2.py app/services/poster2/slot_contracts.py`
  - pass
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TemplateBBackendGenerationFix'`
  - `11 passed, 266 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py -k 'template_b'`
  - `4 passed, 23 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_slot_contracts.py`
  - `2 failed, 4 passed`
  - failures are legacy synthetic Family B slot-contract expectations (`family_b_information_core`, `cta_slot`) outside the real `template_product_sheet_v1` path and were not widened in this PR

## Runtime Verification Payload / Result

Verification used the latest local Template B metadata path with:

- `template_id = template_product_sheet_v1`
- `brand_name = KitchenWorks`
- `agent_name = Dealer Team`
- `title = Product Sheet`
- `subtitle = Kitchen center hero`
- `sku_text = KW-201`
- 2 materials images
- primary + secondary product images
- `description_title = Product Highlights`
- `description_body = Two-image product sheet with materials strip.`

Observed result:

- `header_mode = "logo_banner_lockup"`
- `brand_logo_slot.rendered = true`
- `header_region.rendered = true`
- `title_owner_region = "top_copy_region"`
- `subtitle_owner_region = "top_copy_region"`
- `sku_rendered_excerpt = "KW-201"`
- `product_canvas_shell_bounds = {x:112, y:348, w:800, h:384}`
- `product_primary_slot = {x:112, y:348, w:800, h:384}`
- `product_text_shell_bounds = {x:0, y:0, w:0, h:0}`
- `product_layout_mode_reason = "single_hero_centered_with_secondary_inset"`
- `product_secondary_slot_rendered = true`
- `description_region.rendered = true`
- `bottom_contract_scope = "description_region_only"`
- `bottom title owner = "top_copy_region"`
- `region_render_status` now reports only Family B regions:
  - `logo_banner_region`
  - `top_copy_region`
  - `materials_strip_region`
  - `product_hero_region`
  - `description_region`

## Remaining Risks

- Local verification still ran through injected Puppeteer failure -> Pillow fallback for metadata inspection; this confirmed contract evidence but did not produce a fresh live Puppeteer browser artifact bundle in this workspace.
- Local font assets are still missing (`NotoSansSC-Regular.ttf`, `NotoSansSC-SemiBold.ttf`), so visual browser parity should be rechecked in an environment with the expected font pack.
- Legacy synthetic Family B slot-contract tests remain out of sync with the real `template_product_sheet_v1` family contract surface.

## One-Line State

Template B now resolves and reports as a Family B-owned logo-banner / top-copy / full-width-hero / description contract line, without reusing Family A title-band, brand-only, or narrow-canvas evidence.
