# Template B Design Baseline v1

## Purpose

Establish a real Template B visual baseline for `template_product_sheet_v1` without reopening Family B ownership or drifting back into Family A semantics.

This pass is design-baseline work only:

- keep the frozen Family B region order
- keep contract / evidence truth intact
- strengthen visual hierarchy through Family B beauty tokens and renderer treatment

## Root Rules Followed

- contract-first
- behavior before beautification
- renderer executes; renderer does not define template truth
- no Family A geometry / behavior change
- no Template B region-order change
- no scenario / feature-callout reintroduction into Template B

## Read / Inspection Notes

Read first:

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/template_dual_v2_architecture_business_definition.md`
- `docs/poster2/beautification_layer_plan_v1.md`
- `docs/poster2/external_reference_poster_design_review_and_migration_v1.md`

Inspected first:

- `claude/flamboyant-mclaren`
- `claude/gracious-allen`

Workspace note:

- a separate "latest Template B design / product-sheet note" was not present as a tracked formal doc in this workspace
- the design pass was therefore anchored on the current Family B contract baseline plus a fresh local metadata reproduction for `template_product_sheet_v1`

## Problem Reproduced

Current Template B no longer leaked Family A ownership, but it still looked visually under-designed:

- background read as empty / placeholder
- banner shell existed but did not read as a brand entrance
- top copy had weak hierarchy and little product-sheet authority
- materials strip still read like leftover thumbnails
- product hero lacked atmosphere and containment
- description block felt like a generic white box, not a catalog/spec block

## Root Cause

Template B had a valid Family B structure and valid evidence, but its beauty-token selection and renderer presentation were still close to a neutral scaffold:

1. generic light shell tokens kept the page washed out
2. header shell and logo lockup had little internal contrast
3. Template B HTML/CSS treated materials and hero as minimal placeholders
4. Pillow fallback did not mirror key Family B visual cues such as background atmosphere, SKU line, or materials framing

## Design Philosophy Used

`Industrial Sheet`

- neutral warm-stone product-sheet atmosphere
- dark brand entrance at the top
- restrained industrial-red accent only where hierarchy needs a cue
- single dominant hero subject
- copy reduced to a structured reference stack, not a campaign slogan block
- description treated as calm spec-sheet support copy

## Files Changed

- `app/templates/specs/template_product_sheet_v1.json`
- `app/templates_html/template_product_sheet_v1.html`
- `app/templates_html/template_product_sheet_v1.css`
- `app/services/poster2/template_behavior.py`
- `app/services/poster2/renderer.py`
- `tests/poster2/test_renderer.py`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/template_b_design_baseline_v1.md`
- `docs/poster2/README.md`

## Layer Changed

- beautification
- renderer consumption
- Family B token wiring
- validation
- docs

## Exact Visual Changes

### Banner

- switched Template B onto Family B-specific beauty tokens:
  - `shell_surface = industrial_sheet_dark_strip`
  - `shell_border = precision_frame`
  - `shell_shadow = sheet_depth`
  - `accent_tone = industrial_red`
  - `text_emphasis = industrial_sheet_editorial`
- turned the banner into a dark lockup strip with a separate logo plaque and subordinate agent chip
- preserved `logo_banner_region` ownership and `logo_banner_lockup` header mode

### Top Copy

- strengthened the 3-level stack:
  - SKU as a compact industrial-red reference chip
  - title as the dominant line
  - subtitle quieter and lighter
- aligned title / subtitle / description copy to a product-sheet reading edge instead of keeping all copy visually equal
- added SKU draw parity in the Pillow path so fallback no longer drops the first hierarchy line

### Materials Strip

- replaced thumbnail-leftover styling with framed sample cards
- centered sparse counts and enlarged 1-2 item layouts inside the same frozen materials region
- kept semantics as `materials_strip_region`; no gallery logic was introduced

### Product Hero

- added a restrained hero surface, halo, and ground plane to make the product read as the sole subject
- kept full-width Family B hero geometry unchanged
- kept the secondary image as an inset detail card, not a second hero

### Description

- restyled the block as a calmer product-sheet/spec panel
- improved typographic contrast between description title and body
- kept ownership exclusively under `description_region`

### Pillow Alignment

- added background atmosphere to the fallback path
- added Family B SKU / agent rendering parity
- added materials-card framing and centered sparse materials layout in fallback

## Validation Run

- `./.venv/bin/python -m py_compile app/services/poster2/template_behavior.py app/services/poster2/renderer.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'TemplateBIndustrialSheet or pillow_beauty_tokens_change_shell_presentation'`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TemplateBBackendGenerationFix or test_template_a_regression_path_remains_unchanged'`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py -k 'template_b'`

Results:

- renderer tests: `3 passed`
- pipeline tests: `11 passed`
- Template B API tests: `4 passed`

## Runtime Verification Payload / Result

Local metadata verification used:

- `template_id = template_product_sheet_v1`
- logo present
- brand + agent present
- SKU / title / subtitle present
- 3 materials images
- primary + secondary product images
- description title + body present

Verified result:

- `header_mode = logo_banner_lockup`
- `beauty_tokens.shell_surface = industrial_sheet_dark_strip`
- `beauty_tokens.shell_border = precision_frame`
- `beauty_tokens.shell_shadow = sheet_depth`
- `beauty_tokens.accent_tone = industrial_red`
- `beauty_tokens.text_emphasis = industrial_sheet_editorial`
- `brand_logo_slot.rendered = true`
- `title_owner_region = top_copy_region`
- `subtitle_owner_region = top_copy_region`
- `materials_strip_region.rendered = true`
- `materials_strip_region.count = 3`
- `product_layout_mode_reason = single_hero_centered_with_secondary_inset`
- `product_canvas_shell_bounds = {x:112, y:348, w:800, h:384}`
- `description_title_layer.rendered = true`
- `description_body_layer.rendered = true`
- `deliverable = true`

Saved verification artifact:

- `/tmp/template_b_design_manifest.json`

## Screenshots

Local Pillow comparison artifacts:

- before: `/tmp/template_b_before.png`
- after: `/tmp/template_b_after.png`

Interpretation:

- before showed a black/empty fallback atmosphere, weak header presence, and gallery-like materials
- after shows a real sheet background, a dark brand entrance, framed materials samples, a contained hero stage, and a calmer description panel

## Remaining Gaps / Risks

- the workspace still lacks the expected font pack, so the current local screenshots understate the intended typography
- local runtime verification degraded to Pillow because Playwright is not installed in this environment; metadata and contract evidence still remained intact
- this pass intentionally did not change Family B geometry or add new Template B schema
