# Current Branch Execution Log v1

## Entry — PR-TB-D1: establish Template B design baseline v1 as an Industrial Sheet

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-08

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/template_dual_v2_architecture_business_definition.md`
- `docs/poster2/beautification_layer_plan_v1.md`
- `docs/poster2/external_reference_poster_design_review_and_migration_v1.md`
- latest local runtime metadata reproduction for `template_product_sheet_v1`

### Branch / doc inspection notes

- inspected first:
  - `claude/flamboyant-mclaren`
  - `claude/gracious-allen`
- both branches were older Template B lines and did not contain a newer Family B design baseline worth replaying onto current `main`
- a separate tracked "latest Template B design / product-sheet note" was not present in this workspace

### Scope

- Template B beauty-token and renderer presentation baseline only
- no ownership / Family A reopen
- no Template B region-order change
- no Family A behavior / geometry change
- docs + focused validation

### Root rules followed

- contract-first
- behavior before beautification
- renderer executes; renderer does not define template truth
- no Template A regression
- no Template B contract drift

### Problem reproduced

Template B ownership/evidence was corrected, but the page still looked like a pale scaffold:

- empty / placeholder atmosphere
- header shell existed but did not read as a brand entrance
- top copy hierarchy was weak
- materials strip read like leftover thumbnails
- product hero lacked a true stage
- description block felt generic

### Root cause found

1. Template B was still using a generic light-shell beauty preset
2. header / materials / hero / description CSS treatment remained close to scaffold-level defaults
3. Pillow fallback still lacked Family B-specific atmosphere, SKU drawing, agent rendering, and materials framing

### Files changed

- `app/templates/specs/template_product_sheet_v1.json`
- `app/templates_html/template_product_sheet_v1.html`
- `app/templates_html/template_product_sheet_v1.css`
- `app/services/poster2/template_behavior.py`
- `app/services/poster2/renderer.py`
- `tests/poster2/test_renderer.py`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/template_b_design_baseline_v1.md`
- `docs/poster2/README.md`

### Layer changed

- beautification
- renderer consumption
- validation
- docs

### Exact design-baseline changes

- switched Template B onto Family B-specific beauty tokens:
  - `industrial_sheet_dark_strip`
  - `precision_frame`
  - `sheet_depth`
  - `industrial_red`
  - `industrial_sheet_editorial`
- redesigned the banner as a dark brand strip with a separate logo plaque and subordinate agent chip
- strengthened top-copy hierarchy:
  - SKU chip
  - stronger title
  - quieter subtitle
- restyled materials as framed sample cards and centered sparse counts within the same frozen region
- added a restrained hero surface / halo / ground plane without changing product hero geometry
- restyled the description block as a calmer product-sheet panel
- aligned Pillow fallback with Family B baseline:
  - background atmosphere
  - SKU rendering
  - agent chip rendering
  - materials-card framing and sparse-count centering

### Validation run

- `./.venv/bin/python -m py_compile app/services/poster2/template_behavior.py app/services/poster2/renderer.py` -> `pass`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'TemplateBIndustrialSheet or pillow_beauty_tokens_change_shell_presentation'` -> `3 passed, 104 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TemplateBBackendGenerationFix or test_template_a_regression_path_remains_unchanged'` -> `11 passed, 266 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py -k 'template_b'` -> `4 passed, 23 deselected`

### Runtime verification payload / result

- payload:
  - `template_id = template_product_sheet_v1`
  - logo present
  - brand + agent present
  - SKU / title / subtitle present
  - 3 materials images
  - primary + secondary product images
  - description title + body present
- result:
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
  - `product_layout_mode_reason = single_hero_centered_with_secondary_inset`
  - `product_canvas_shell_bounds = {x:112, y:348, w:800, h:384}`
  - `description_region.rendered = true`
  - `deliverable = true`
- artifact:
  - `/tmp/template_b_design_manifest.json`

### Screenshot artifacts

- before: `/tmp/template_b_before.png`
- after: `/tmp/template_b_after.png`

### Remaining risks

- local font assets are still missing, so typography in the local artifacts under-represents the intended hierarchy
- local verification degraded to Pillow because Playwright is not installed in this workspace
- this pass intentionally did not mutate Family B geometry or add new Template B schema

---

## Entry — PR-TB-CONTRACT1: correct Template B ownership and evidence so Family B is contract-native

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-08

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/template_dual_v2_architecture_business_definition.md`
- `docs/poster2/template_family_region_matrix_v1.md`
- `docs/poster2/template_family_slot_contract_baseline_v1.md`
- latest local runtime metadata reproduction for `template_product_sheet_v1`

### Scope

- Template B header contract correction
- Template B top-copy ownership correction
- Template B product hero shell correction
- Template B description ownership correction
- Template B runtime evidence cleanup
- focused tests + status docs

### Root rules followed

- contract-first
- behavior before beautification
- renderer executes; renderer does not define template truth
- no Family A runtime behavior changes
- no bottom SOP redesign
- no email / storage / Stage3 changes

### Problem reproduced

The active Template B manifest still leaked Family A semantics even though Family B region routing already existed:

- `header_mode = brand_only`
- `brand_logo_slot.rendered = false`
- `title_text_layer.owner_region = title_band_region`
- `subtitle_text_layer.owner_region = title_band_region`
- rendered title / subtitle excerpts were empty
- `product_primary_slot.w = 800` while `product_canvas_shell_w = 300`
- `bottom_contract_review` still carried title / subtitle semantics

### Root cause found

1. Template B behavior resolution still hard-coded a Family A-style header mode
2. shared text-layer evidence builders still froze title / subtitle ownership to `title_band_region`
3. shared product review builders still emitted Family A canvas-shell and text-shell geometry
4. bottom review builders still assumed title-band ownership
5. renderer-side Template B layer evidence was incomplete, so final payloads still inherited some Family A fallback assumptions

### Files changed

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

### Layer changed

- contract
- validation
- resolver / behavior wiring
- renderer consumption
- evidence / metadata
- docs

### Exact contract corrections

- Template B header now resolves to `logo_banner_lockup`
- Template B logo slot remains renderable and no longer collapses under `brand_only`
- Template B title / subtitle evidence now belongs to `top_copy_region`
- added `top_copy_contract_review`:
  - `sku_text_layer`
  - `top_copy_title_layer`
  - `top_copy_subtitle_layer`
- Template B product canvas shell now matches the full-width hero geometry
- Template B product text shell now resolves to zero bounds with `reason_code = not_used_in_template_b`
- added `description_contract_review`:
  - `description_title_layer`
  - `description_body_layer`
- Template B `bottom_contract_review` now scopes to description-only ownership and explicitly excludes title / subtitle / SKU semantics

### Validation run

- `./.venv/bin/python -m py_compile app/services/poster2/template_behavior.py app/services/poster2/pipeline.py app/services/poster2/renderer.py app/main.py app/schemas/poster2.py app/services/poster2/slot_contracts.py` -> `pass`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TemplateBBackendGenerationFix'` -> `11 passed, 266 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py -k 'template_b'` -> `4 passed, 23 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_slot_contracts.py` -> `2 failed, 4 passed`
  - unrelated existing synthetic Family B expectations (`family_b_information_core`, `cta_slot`) remain out of sync with the real `template_product_sheet_v1` path

### Runtime verification payload / result

Representative local Template B metadata verification after the fix:

- payload:
  - `template_id = template_product_sheet_v1`
  - `brand_name = KitchenWorks`
  - `agent_name = Dealer Team`
  - `title = Product Sheet`
  - `subtitle = Kitchen center hero`
  - `sku_text = KW-201`
  - 2 materials images
  - primary + secondary product images
  - description title + body present
- result:
  - `header_mode = logo_banner_lockup`
  - `brand_logo_slot.rendered = true`
  - `title_owner_region = top_copy_region`
  - `subtitle_owner_region = top_copy_region`
  - `product_canvas_shell_bounds = {x:112, y:348, w:800, h:384}`
  - `product_text_shell_bounds = {x:0, y:0, w:0, h:0}`
  - `product_layout_mode_reason = single_hero_centered_with_secondary_inset`
  - `bottom_contract_scope = description_region_only`
  - `region_render_status` contains only Family B region ids

### Remaining risks

- no fresh live Puppeteer browser artifact bundle was generated in this workspace; local metadata verification used an injected Puppeteer failure and confirmed corrected fallback evidence
- local font assets are still missing, so visual parity should be rechecked in an environment with the expected font pack
- legacy synthetic Family B slot-contract tests remain a separate cleanup item

---

## Entry — PR-TB-LINE2: make Template B an independent Stage1->Stage2 working line

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-08

### What was read first
- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/product_region_annotation_contract_status_v1.md`
- `docs/poster2/bottom_behavior_contract_status_v1.md`

Additional read / inspection notes:
- `docs/poster2/template_b_kitchen_center_hero_status_v1.md` is missing in this workspace
- no tracked latest Stage2 screenshots / console / network payload artifact bundle was present in the workspace
- inspected first:
  - `claude/flamboyant-mclaren`
  - `claude/gracious-allen`

### Scope
- make Template B independent across:
  - Stage1 asset entry
  - Stage1 preview
  - Stage2 family-aware panel state
  - Template B serializer
  - `/api/v2/generate-poster` request path
- remove Family A piggyback assumptions from the active Template B line
- frontend/docs mirror sync
- targeted validation only

### Root rules followed
- contract-first
- no poster contract drift
- no geometry drift
- no ownership drift
- no Resend / Stage3 / email closure changes
- no Family A runtime behavior changes
- no bottom SOP baseline changes

### Problem reproduced
- Stage1 Material Preview / Layout Preview still rendered Family A dual-column composition for Template B
- Stage2 still exposed Family A copy/bottom assumptions for Template B
- generate could fail with `Cannot read properties of undefined (reading 'map')`
- Template B fields were collected, but not carried through a clean independent family path

### Root cause found
1. Template B had only a partial split from Family A
2. `updatePosterPreview()` and `buildLayoutPreview()` still rendered Family A scenario/gallery assumptions
3. `applyStage2TemplateFamilyVisibility()` hid only part of the Family A UI, but did not swap in a Template B summary model
4. Template B generate flow still fed later audit code that expected `posterPayload.gallery_items`
5. The prior Template B path still leaned on the older `/api/generate-poster` shape instead of using the already-compatible `/api/v2/generate-poster` contract

### Files changed
- `frontend/index.html`
- `frontend/stage2.html`
- `frontend/styles.css`
- `frontend/app.js`
- `docs/index.html`
- `docs/stage2.html`
- `docs/styles.css`
- `docs/app.js`
- `tests/poster2/test_api.py`
- `tests/test_frontend_docs_sync.py`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/template_b_line2_independent_flow_status_v1.md`
- `docs/poster2/README.md`

### Layer changed
- behavior
- docs
- validation

### Exact independent-flow fixes
- added dedicated Template B Stage1 preview surface instead of reusing Family A dual-column preview
- added dedicated Template B Stage2 summary block and hid Family A copy/bottom surfaces when `template_id == template_product_sheet_v1`
- disabled `puppeteer` selection for Template B at the Stage2 panel layer
- added `buildTemplateBPosterPayload(...)` and moved Template B generation onto `/api/v2/generate-poster`
- limited Template B payload to B-relevant fields only
- defaulted optional collections before `.map()` / count usage
- removed active `posterPayload.gallery_items.map(...)` crash path by guarding with `|| []`

### Validation run
- `node --check frontend/app.js` -> `pass`
- `bash scripts/sync_frontend_to_docs.sh` -> `synced index.html, stage2.html, app.js, styles.css`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` -> `5 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py` -> `25 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'single_primary'` -> `3 passed, 263 deselected`

### Remaining risks
- no tracked browser-console/network artifact bundle existed in the workspace, so this pass validated by code-path reproduction plus targeted tests rather than imported screenshot evidence
- this closes the independent-flow bug, not a broad Template B visual polish pass

### Exact acceptance
- Stage1 preview for Template B no longer uses Family A layout
- Stage2 no longer shows Family A copy/bottom controls for Template B
- no `undefined.map` crash remains in the Template B generate path
- Template B generate payload now contains only B-relevant fields
- backend acceptance verified through `/api/v2/generate-poster`
- 1-image path works
- 2-image path works
- `materials_images = []` path works
- Template A remains unchanged

---

## Entry — PR-TB-UI2: fix Template B preview path and wire Stage2 generate path

**Branch:** `claude/flamboyant-mclaren`
**Status:** Complete
**Last updated:** 2026-04-07

### What was read first
- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`

### Scope
- Remove `/templates/undefined` requests for template_product_sheet_v1
- Make Stage2 template-family-aware by template_id (hide Family A controls, show Family B label)
- Fix 422 from KitPosterDraft schema rejecting template_product_sheet_v1
- Add dedicated Template B posterPayload serializer (no Family A fields)
- Skip Family A prompt_bundle for Template B
- frontend/docs mirror sync

### Root rules followed
- contract-first
- no poster contract drift
- no resend / storage / email transport changes
- no backend schema changes (frontend-only fix)

### Problem reproduced (initial)
- Template B selection visible in Stage1
- Stage2 still requested `/templates/undefined` — registry entry lacks spec/preview
- Stage2 showed Family A controls (Bottom Region panel, hardcoded "template_dual_v2 · Family A" label)
- Generate returned 422: `buildKitPosterDraftFromSource` sent `draft.template_id: "template_product_sheet_v1"` but `KitPosterDraft.template_id: Literal["template_dual", "template_single"]`

### Problem reproduced (follow-up)
- `draft` still present in at least one path (buildGeneratePosterPayload debug build)
- `posterPayload` still carried all Family A fields (scenario_image, gallery_items, gallery_limit, gallery_allows_*, scenario_mode, scenario_key) via the undifferentiated `else if (MODE_S)` branch
- Stage2 Copy panel still showed "Bottom Support Copy" (Family A subtitle band field) for Template B
- Family A prompt_bundle slots sent for Template B

### Root cause found
1. `ensureTemplateAssets` fetched `templates/${entry.spec}` / `templates/${entry.preview}` without guarding undefined
2. Stage2 init had no template-family dispatch on mount
3. Draft builder ran unconditionally for all MODE_S requests
4. `triggerGeneration` had a single `else if (MODE_S)` branch — Template B entered the Family A path and built a Family A posterPayload
5. `applyStage2TemplateFamilyVisibility` (pass 1) only hid the Bottom Region panel — "Bottom Support Copy" in the Copy panel remained
6. `buildModeSPromptBundle` ran unconditionally for all MODE_S requests including Template B

### Files changed
- `frontend/app.js`
- `frontend/stage2.html`
- `docs/app.js`
- `docs/stage2.html`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed
- behavior
- docs

### Changes made
- `ensureTemplateAssets`: guard — if no spec/preview, return `{entry, spec: null, image: null}` stub
- standalone `refreshTemplatePreviewStage1`: guard null image — draws placeholder text
- `TEMPLATE_B_ID = 'template_product_sheet_v1'` constant at module level
- `applyStage2TemplateFamilyVisibility(stage1Data)`: new function
  - hides `s2-bottom-region-panel` (Bottom Region controls)
  - hides `s2-bottom-support-copy-field` (Bottom Support Copy in Copy panel)
  - shows `s2-features-section` (Product Callouts) for Template B
  - updates `s2-template-display` to "Family B" or "Family A" label
- `stage2.html`: added IDs: `s2-bottom-region-panel`, `s2-template-display`, `s2-bottom-support-copy-field`
- Stage2 init: call `applyStage2TemplateFamilyVisibility` after controls init
- `triggerGeneration`: added `else if (MODE_S && templateId === TEMPLATE_B_ID)` branch before general `else if (MODE_S)`:
  - normalises product images only (no scenario ref)
  - builds posterPayload with Template B fields only: `sku_text`, `description_title`, `description_body`, `materials_images`, product images, features from product_callouts
  - excludes: `scenario_image`, `scenario_key`, `scenario_asset`, `scenario_mode`, `gallery_items`, `gallery_limit`, `gallery_label`, `gallery_allows_*`
- Draft builder: skip for Template B (`stage1Data.template_id !== TEMPLATE_B_ID`)
- Prompt bundle: skip for Template B (`isTemplateBRequest` guard before `buildModeSPromptBundle`)

### Validation run
- `node --check frontend/app.js` → PASS
- `bash scripts/sync_frontend_to_docs.sh` → synced (4 files)
- `python -m pytest tests/poster2/test_api.py tests/test_frontend_docs_sync.py` → 27 passed + 4 passed

### Remaining risks
- Backend `/api/generate-poster` has no Template B handler — `run_kitposter_state_machine` may fail downstream for `template_product_sheet_v1`; this is step 5 (backend deployment verification)
- `PosterInput.scenario_image` is required (`min_length=1`) — Template B posterPayload intentionally omits it; backend will return PosterInput 422 until schema is relaxed or a separate endpoint is added for Template B

### Exact acceptance
- Template B never requests `/templates/undefined`
- Stage2 hides Bottom Region panel and Bottom Support Copy for Template B
- Stage2 shows Product Callouts section for Template B
- Stage2 shows "template_product_sheet_v1 · Family B" in template display field
- Generate request: no `draft`, no `prompt_bundle`, no Family A fields in posterPayload
- Generate request: contains `sku_text`, `description_title`, `description_body`, `materials_images`
- Template A (template_dual_v2) behavior, controls, and payload unchanged

---

## Entry — PR: close stage1 secondary-image delete and add product-callout input surface

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-06

### What was read first
- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/bottom_behavior_contract_status_v1.md`
- `docs/poster2/product_region_annotation_contract_status_v1.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`

### Scope
- Stage1 secondary product image removable
- Stage1 input split:
  - bottom support copy stays bottom-owned
  - dedicated product callout inputs feed product-owned annotation truth
- Stage2 operator label alignment for bottom support copy / product callouts
- frontend/docs mirror sync
- targeted validation only

### Root rules followed
- contract-first
- no poster contract drift
- no geometry drift
- no ownership drift
- no resend / storage / email transport changes
- Stage2/Stage3 remained backend-driven

### Problem reproduced
- secondary product image was optional in backend/runtime truth, but Stage1 had no explicit operator-facing remove action
- Stage1 still framed product explanation as generic bullets instead of dedicated product callouts
- bottom support copy risked being confused with product explanation input, even though bottom semantics are frozen

### Root cause found
- Stage1 input surfaces lagged behind the already-frozen product annotation ownership model
- the frontend request builder still depended on generic `features/bullets` fallback without a dedicated operator surface
- secondary image clearing existed only as an implicit file-input-empty path, not an explicit operator control

### Why subtitle was NOT repurposed
- bottom subtitle remains title-band / bottom support copy semantics
- product explanation remains product-owned and continues to normalize into canonical `features`
- this avoids mixing product annotation ownership into bottom-owned copy

### Files changed
- `frontend/index.html`
- `frontend/stage2.html`
- `frontend/app.js`
- `docs/index.html`
- `docs/stage2.html`
- `docs/app.js`
- `scripts/check_frontend_docs_sync.sh`
- `scripts/sync_frontend_to_docs.sh`
- `tests/test_frontend_docs_sync.py`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/stage1_operator_input_surface_bugfix_status_v1.md`
- `docs/poster2/README.md`

### Layer changed
- behavior
- docs
- validation

### Request mapping changes
- new Stage1 operator fields: `product_callouts[0..2]`
- frontend normalization prefers:
  - `product_callouts`
  - then legacy `features`
  - then legacy `bullets`
- canonical backend surface remains `features`
- bottom support copy still maps to canonical backend `subtitle`
- clearing secondary product image removes `product_image_2` from Stage1 state and keeps `/api/v2/generate-poster` compatible with `product_secondary_image: null`

### Validation run
- `node --check frontend/app.js` → `pass`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py` → `23 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'product or annotation or single_primary'` → `73 passed, 190 deselected`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `4 passed`

### Remaining risks
- no dedicated browser automation test exists for the button click path; validation is from source-path regression plus payload/path invariants
- Stage1 still lives in `index.html`, not a dedicated `stage1.html`; this was recorded explicitly and not treated as a blocker

### Exact acceptance
- Stage1 second product image can now be removed explicitly
- removing it leaves the payload compatible with single-primary fallback
- operator-facing subtitle is relabeled as bottom support copy
- product explanation now has a dedicated 3-input callout surface
- product explanation still feeds product-owned annotation truth
- bottom subtitle semantics remain unchanged
- frontend/docs mirror remains aligned

## Entry — PR-10B: poster2 copy quality phase 1

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-06

### Scope
- annotation copy compression
- title / subtitle style normalization
- deterministic marketing-safe subtitle fallback
- Gemini optimizer quality hardening

### What was read first
- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/product_region_annotation_contract_status_v1.md`

### Root rules followed
- contract-first; no poster structure contract drift
- no resend / attachment / transport changes
- no region-bounds or ownership changes
- no bottom mode or feature suppression changes
- state/docs were read first and written back after completion

### Problem reproduced
- annotation sell-point copy could still arrive too verbose for the fixed product annotation shell budget, causing avoidable truncation
- deterministic draft still used subtitle as the weak fallback but not yet as a normalized campaign-safe fallback
- Gemini success path was safe but not strict enough against low-quality subtitle-echo output

### Root cause found
- there was no shared copy policy for title / subtitle / feature / annotation text normalization across poster runtime and email draft generation
- annotation compression was not happening before poster runtime text budgets applied
- Gemini safety gates blocked invented claims, but not low-quality “subtitle echo” behavior when stronger product sell points already existed

### Files changed
- `app/services/email/copy_safety.py`
- `app/services/email/drafts.py`
- `app/services/email/copy_optimizer.py`
- `app/services/email/gemini_optimizer.py`
- `app/services/poster2/pipeline.py`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_api.py`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/copy_quality_phase1_status_v1.md`
- `docs/poster2/README.md`

### Layer changed
- behavior
- docs
- validation

### Validation run
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'email_draft or canonical_copy_input or product_annotation_copy_compression or gemini or deterministic_uses_clean_subtitle_fallback'` → `8 passed, 255 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py -k 'preview_uses_gemini_when_available or preview_falls_back_when_gemini_fails or preview_deterministic_uses_clean_subtitle_fallback_when_no_sell_points or preview_gemini_subtitle_echo_falls_back_to_deterministic'` → `4 passed, 19 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py` → `23 passed`

### Remaining risks
- live Gemini output still needs deployed-environment quality review
- copy compression is conservative by design and is not a geometry-budget rewrite
- a pre-existing out-of-scope feature dense-quad test baseline still expects `char_budget=24` instead of the current compacted `20`; this PR did not change feature suppression or feature behavior

### Exact acceptance
- annotation truncation rate is reduced through pre-budget copy compression, with no geometry drift
- title / subtitle tone is cleaner and more campaign-ready
- deterministic fallback no longer lets dirty subtitle dominate preview copy
- Gemini success path is hardened against low-quality subtitle echo
- no transport regressions were introduced
- no contract drift was introduced

## Entry — PR-bottom-final-last-mile: title_gallery_split dense_quad subtitle capacity closeout

**Branch:** `claude/recursing-joliot`
**Status:** Complete
**Last updated:** 2026-04-06

### Scope
- `title_gallery_split` dense_quad only: eliminate subtitle_truncation_applied by raising subtitle_char_budget to CSS 2-line capacity
- `text_only_expanded`: frozen, no changes
- No header / product / feature / beautification / storage / email changes

### Root rules followed
- contract-first; stay on the frozen bottom SOP baseline
- do not change text_only_expanded, gallery distribution, bottom_shell_top, or 20px product gap
- validate with metadata / truncation evidence, not visual estimate

### Problem reproduced
- `title_gallery_split` dense_quad with long subtitle: `subtitle_truncation_applied = True`
- PR-7B5 had raised `subtitle_char_budget` from 56 → 72 but budget=72 still fell below the test subtitle length (116 chars)
- `_apply_text_budget` hard-truncates at budget before passing text to renderer
- CSS `line-clamp:2` was never responsible for the truncation — the policy budget was the bottleneck

### Root cause
`subtitle_char_budget = 72` (PR-7B5 intermediate) is below the actual test subtitle length (116 chars).
`_apply_text_budget` returns `text[:budget]`, so `rendered_subtitle_excerpt != effective_spec.subtitle` → `subtitle_truncation_applied = True`.
Geometry was already sufficient: `available_height = 184 - 22 - 18 = 144`, `used_height = title_slot(72) + gap(4) + subtitle_slot(44) = 120 ≤ 144`. No slot overflow. Budget was the only constraint.

### Files changed
- `app/services/poster2/template_behavior.py` — `subtitle_char_budget` in dense_quad branch: `72 → 120`
- `tests/poster2/test_pipeline.py` — 4 assertion updates for dense_quad budget + truncation; 1 indentation fix (module-level test moved inside `TestBottomModeFamilyContractClosure`)
- `tests/poster2/test_renderer.py` — 2 stale assertions updated: `title_band_height 168 → 184`, `gallery_shell_top 896 → 912` (both were stale from PR-7B5 title_band_height change)

### Layer changed
- behavior (budget policy only, no geometry)
- validation

### Exact fields changed

| Field | Before | After |
|-------|--------|-------|
| `subtitle_char_budget` (dense_quad) | 72 | 120 |
| `test_pipeline.py:806` assertion | `== 72` | `== 120` |
| `test_pipeline.py:859` assertion | `== 72` | `== 120` |
| `test_pipeline.py:860` assertion | `len == 72` | `rendered_excerpt == requested_subtitle` |
| `test_pipeline.py:861` assertion | `is True` | `is False` |
| `test_renderer.py:1200` assertion | `== 168` | `== 184` (stale from PR-7B5) |
| `test_renderer.py:1201` assertion | `== 896` | `== 912` (stale from PR-7B5) |

### Frozen invariants confirmed unchanged
- `bottom_shell_top = 728` ✓
- `title_band_height = 184` ✓
- `title_content_pad_top = 22` ✓
- `title_content_pad_bottom = 18` ✓
- `title_stack_gap = 4` ✓
- `subtitle_line_clamp = 2` ✓
- `gallery_distribution_policy = dense_quad` ✓
- `gallery_strip_region = {x:96, y:912, w:832, h:68}` ✓
- `subtitle_slot = {x:152, y:838, w:720, h:44}` ✓
- product_secondary_bottom(708) + 20px gap ✓

### Validation run
- `.venv/bin/python3 -m pytest -q tests/poster2/test_pipeline.py -k "dense_quad or dense_bottom"` → `6 passed`
- `.venv/bin/python3 -m pytest -q tests/poster2/test_pipeline.py tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py` → `365 passed, 2 pre-existing failures (layout_density_mode, feature char_budget — out of scope)`

### Remaining risks
- Pre-existing failures in `TestPosterPipelineRun::test_renderer_metadata_includes_layer_render_status` (layout_density_mode) and `test_feature_contract_review_...` (feature char_budget) remain; not related to bottom or subtitle

### Final acceptance evidence
- `subtitle_char_budget = 120` (budget ≥ test subtitle length 116)
- `subtitle_truncation_applied = False` (rendered_subtitle_excerpt == full subtitle)
- `subtitle_overflow_policy = two_line_clamp_inside_expanded_split_title_band` unchanged
- `subtitle_line_clamp = 2` unchanged
- `gallery_distribution_policy = dense_quad` unchanged
- `bottom_shell_top = 728`, product gap ≥ 20px preserved
- `text_only_expanded` — no changes, frozen at PR-7B5 accepted baseline

## Entry — PR: Gemini Copy Optimizer And Optional Attachment Assets

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-05

### Scope
- Gemini-backed email copy optimization
- improved deterministic draft fallback
- optional backend-owned attachment assets
- optional resend attachment wiring
- Stage3 source/docs mirror alignment for draft source and attachment readiness

### What was read first
- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/bottom_behavior_contract_status_v1.md`
- task-relevant email closure files only after the state read

### Root rules followed
- contract-first
- no poster structure contract drift
- no bottom truth drift
- no product annotation truth drift
- Stage3 stayed backend-driven through live payload only
- frontend/docs mirror stayed aligned in the same PR

### Problem reproduced
- deterministic draft over-trusted subtitle and produced overly mechanical preview text
- current draft path had no optimizer layer above canonical business facts
- current closure path had no backend-owned optional attachment assets for resend readiness

### Root cause found
- email draft generation was still a single deterministic formatter instead of a structured canonical-input pipeline
- subtitle was treated too early as preview text source
- attachment readiness had no persisted backend asset model in `poster_record`

### Files changed
- `app/config.py`
- `app/main.py`
- `app/schemas/poster2.py`
- `app/services/poster_records.py`
- `app/services/email/drafts.py`
- `app/services/email/copy_optimizer.py`
- `app/services/email/gemini_optimizer.py`
- `app/services/email/attachments.py`
- `app/services/email/providers.py`
- `app/services/email/resend_provider.py`
- `frontend/stage3.html`
- `frontend/app.js`
- `docs/stage3.html`
- `docs/app.js`
- `tests/poster2/test_api.py`
- `tests/poster2/test_pipeline.py`
- `tests/test_stage3_email_closure_surface.py`
- `docs/poster2/email_copy_optimizer_and_optional_attachment_status_v1.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/README.md`
- `CLAUDE.md`

### Layer changed
- contract
- behavior
- docs
- validation

### Validation run
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py` → `18 passed`
- `./.venv/bin/python -m pytest -q tests/test_stage3_email_closure_surface.py` → `2 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'email or poster_record or attachment or draft'` → `3 passed, 254 deselected`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `2 passed`

### Remaining risks
- Gemini live optimization still needs deployed-environment validation with real credentials
- resend attachment delivery still needs real-provider validation
- local fallback attachment assets are backend-owned but server-local until object storage is configured

### Exact acceptance
- preview draft is business-cleaner than direct subtitle echo
- Gemini failure does not block preview and returns deterministic fallback
- attachment assets are backend-owned and inspectable in `poster_record`
- resend path is optional-attachment-ready
- `inline_only` safe default remains unchanged
- frontend/docs mirror remains aligned

## Entry — Storage / Copy / Email Closure Engineering

**Branch:** `main`
**Status:** In progress
**Last updated:** 2026-04-04

### Read state
- `README.md`
- `AGENTS.md`
- `docs/poster2/README.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/current_branch_execution_log_v1.md`

### Scope
- poster_record persistence
- backend email draft generation from poster_record
- Resend-backed send API
- Stage3 live backend closure

### Frozen unchanged
- poster structure contract
- bottom SOP baseline
- product annotation ownership/runtime truth
- beautification expansion
- editor-first workflow

### Engineering truth
- `/api/v2/generate-poster` now returns `poster_key`
- successful v2 generation now persists `poster_record`
- new backend truth endpoints:
  - `GET /api/v2/posters/{poster_key}`
  - `POST /api/v2/email/preview`
  - `POST /api/v2/email/send`
- Stage2 success path now writes `poster_key` into URL and Stage3 link
- Stage3 now restores poster + email draft from backend truth via `poster_key`
- Stage3 light editing is allowed for subject / preview_text / html / text
- frontend no longer uses `/api/send-email` in the Stage3 path
- `sessionStorage` remains cache only

### Files changed
- `app/config.py`
- `app/main.py`
- `app/schemas/poster2.py`
- `app/services/poster_records.py`
- `app/services/email/__init__.py`
- `app/services/email/drafts.py`
- `app/services/email/providers.py`
- `app/services/email/resend_provider.py`
- `frontend/app.js`
- `frontend/stage3.html`
- `docs/app.js`
- `docs/stage3.html`
- `tests/poster2/test_api.py`
- `tests/test_stage3_email_closure_surface.py`
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`

### Focused validation
- `.venv/bin/python -m pytest -q tests/poster2/test_api.py` → `13 passed`
- `.venv/bin/python -m pytest -q tests/test_stage3_email_closure_surface.py` → `2 passed`
- `.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py -k 'docs_publish_mirror_contains_same_guard_diagnostics'` → `1 passed, 5 deselected`

### Remaining risk
- Resend live delivery still needs deployed-environment validation with real credentials
- `inline_only` remains the default send mode until deployment config is present

## Entry — PR-7B-final-review: Bottom Mode Family Closeout Review And Smallest Next Plan

**Branch:** `main`
**Status:** Review only
**Last updated:** 2026-04-04

### Read state
- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/bottom_behavior_contract_status_v1.md`

### Runtime proofs inspected
- fresh local runtime proof: `title_gallery_split`
- fresh local runtime proof: `text_only_expanded`

Probe inputs used for both:
- `title = "Family A final alignment title"`
- `subtitle = "Validate canonical bottom layout mode, dual-image geometry, and annotation ownership through the real runtime route."`
- `product_secondary_image` present
- `title_gallery_split` proof used 4 gallery items

Hashes:
- `title_gallery_split` final hash: `b629689bdad3153fcb2a8744424b7e9385a7a7e62f9c0d51a0297eab0d71a54e`
- `text_only_expanded` final hash: `315f00786d6750b72c815d7d1c1d77b86c58598c05e3b80d219f88b88d9a1ede`

### What actually improved

`title_gallery_split`
- bottom shell top is now `728`
- product secondary bottom is `708`
- visible gap below product secondary is now `20px`
- subtitle policy is no longer single-line ellipsis in the active split path
- current proof resolves:
  - `subtitle_overflow_policy = two_line_clamp_inside_expanded_split_title_band`
  - `subtitle_line_clamp = 2`
  - `subtitle_char_budget = 56`
  - `subtitle_slot_height = 44`
- structure stayed intact:
  - `title_band_region = {x:112,y:728,w:800,h:168}`
  - gallery distribution unchanged

`text_only_expanded`
- upper overlap is gone:
  - `bottom_shell_top = 728`
  - product secondary bottom = `708`
  - gap = `20px`
- full-width parity is closed:
  - `title_band_region = {x:96,y:728,w:832,h:240}`
  - `title_text_layer.slot_bounds = {x:96,y:792,w:832,h:88}`
  - `subtitle_text_layer.slot_bounds = {x:136,y:888,w:752,h:64}`
- subtitle non-truncation is closed in the current primary proof:
  - `subtitle_truncation_applied = false`
  - `subtitle_line_clamp = 3`
  - `subtitle_char_budget = 160`

### What is still not closed

`title_gallery_split`
- subtitle is still truncating in the dense quad proof
- current proof:
  - `subtitle_truncation_applied = true`
  - rendered subtitle length `56`
  - sanitized subtitle length `116`
- the gap closure is done, but dense subtitle capacity is still too tight under the current split-band stack

`text_only_expanded`
- contract/evidence parity is closed, but the active vertical anchoring is visually too bottom-heavy
- current proof:
  - `title_content_pad_top = 20`
  - `title_content_pad_bottom = 16`
  - `title_slot_y = 792`
  - `subtitle_slot_y = 888`
- because `text_only_expanded` is lower-anchored, the live vertical result is driven mainly by bottom clearance; current content sits too close to the lower edge of the shell

### Smallest contract-first improvement plan

Next PR scope only:
- `PR-7B5` — bottom copy-capacity and vertical-allocation micro-closure
- no header
- no product geometry
- no feature delegation
- no beautification
- no email/save workflow
- no bottom structure redesign

#### A. `title_gallery_split`

Target only the dense quad split branch.

Exact fields to change:
- `subtitle_char_budget`: `56 -> 72`
- `subtitle_slot_height`: `44 -> 48`
- `title_band_height`: `168 -> 184`
- `title_stack_gap`: `6 -> 4`

Reason:
- keep the current `20px` product gap and current split structure
- buy the smallest extra subtitle capacity without reopening gallery distribution
- absorb the added subtitle height mostly by band growth, while taking back `2px` from inter-line spacing

Acceptance criteria:
- `subtitle_truncation_applied = false` for the current dense-quad proof
- `subtitle_overflow_policy` stays `two_line_clamp_inside_expanded_split_title_band`
- `subtitle_line_clamp = 2` stays unchanged
- `gallery_distribution_policy = dense_quad` unchanged
- bottom shell still clears product secondary by at least `16px`

Tests to add/update:
- update dense quad pipeline assertions for:
  - `subtitle_char_budget`
  - `subtitle_slot_height`
  - `title_band_height`
  - `title_stack_gap`
- add a dense-quad proof test that asserts `subtitle_truncation_applied is False`
- update renderer HTML-var assertions for:
  - `--title-band-height`
  - `--subtitle-line-clamp`
  - `--title-stack-gap`

#### B. `text_only_expanded`

Keep full-width and non-truncation intact.
Change only vertical allocation for subtitle-present cases.

Exact fields to change:
- `title_content_pad_top`: `20 -> 24`
- `title_content_pad_bottom`: `16 -> 24`
- expected `title_slot_y`: `792 -> 784`
- expected `subtitle_slot_y`: `888 -> 880`

Reason:
- move the text stack up by `8px`
- preserve full-width x/w truth and current 3-line support-copy capacity
- avoid reopening shell top or horizontal geometry

Acceptance criteria:
- `subtitle_truncation_applied = false` remains true for the current primary proof
- `title_text_layer.slot_bounds.x/w` and `subtitle_text_layer.slot_bounds.x/w` remain full-width truth
- upper gap to product secondary remains `20px`
- final render reads less bottom-heavy while keeping the same shell envelope

Tests to add/update:
- update subtitle-present `text_only_expanded` y/pad assertions in pipeline tests
- add one explicit vertical-allocation test asserting:
  - `title_content_pad_top = 24`
  - `title_content_pad_bottom = 24`
  - `title_slot_y = 784`
  - `subtitle_slot_y = 880`
- keep existing full-width parity assertions unchanged

### Review outcome
- `title_gallery_split`: improved, but not closed
- `text_only_expanded`: contract closure is done; only vertical micro-balance remains
- smallest next step is a bounded bottom-only micro-closure PR, not a broader bottom redesign

## Entry — PR-7C: Bottom Mode Contract Tuning (A+B)

**Branch:** `pr6-clean`
**Status:** Complete
**Last updated:** 2026-04-05

### What changed

- `app/services/poster2/template_behavior.py`
  - `_resolve_bottom_text_slot_metrics`: removed `text_only_expanded` lower-anchor branch (PR-7B3 revert); all modes now use center-packing (`offset = available_height - used_height) // 2`)
  - `text_gallery_expanded` dense ≤2 items: `subtitle_char_budget` 60→72
  - `text_gallery_expanded` dense 3 items: `subtitle_char_budget` 56→72
  - `text_gallery_expanded` dense ≥4 items: `subtitle_char_budget` 56→80; `title_band_height` 168→176; `title_content_pad_top` 22→20; `title_content_pad_bottom` 18→16; `title_stack_gap` 6→8
  - `text_gallery_expanded` subtitle-not-dense: `subtitle_char_budget` 56→72
  - `_resolve_gallery_strip_vertical_metrics`: 4-item entries both modes: `(68, 52)` → `(76, 60)` (shell_height, item_height)
- `tests/poster2/test_pipeline.py` — updated 7 stale y-assertions in `TestBottomPR7B3TextOnlyExpandedVerticalAnchoring` (lower-anchor→center-pack); updated 2 dead-space tests in `TestBottomModeFamilyContractClosure`; updated 3 geometry_evidence assertions for dense quad
- `tests/poster2/test_renderer.py` — updated `title_band_height` 168→176, `gallery_shell_top` 896→904, `gallery_items_height` 52→60; updated 4-item height 52→60; updated dense quad HTML assertions

### Focused validation run

```
python3 -m pytest -q tests/poster2/test_pipeline.py tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py
→ 2 failed (pre-existing), 361 passed
```

### Contract carry-forward

**A. title_gallery_split:**

| Branch | Field | Before | After |
|--------|-------|--------|-------|
| dense ≤2 items | `subtitle_char_budget` | 60 | 72 |
| dense 3 items | `subtitle_char_budget` | 56 | 72 |
| dense ≥4 items | `subtitle_char_budget` | 56 | 80 |
| dense ≥4 items | `title_band_height` | 168 | 176 |
| dense ≥4 items | `title_content_pad_top` | 22 | 20 |
| dense ≥4 items | `title_content_pad_bottom` | 18 | 16 |
| dense ≥4 items | `title_stack_gap` | 6 | 8 |
| subtitle not-dense | `subtitle_char_budget` | 56 | 72 |
| gallery 4-item | `gallery_shell_height` | 68 | 76 |
| gallery 4-item | `gallery_items_height` | 52 | 60 |

Canvas check (dense ≥4): 728 + 176 + 76 = 980 ≤ 1024 ✓

**B. text_only_expanded:**

Center-packing replaces lower-anchoring. New slot positions (band_top=728):

| Sub-case | band_h | title_slot_y | subtitle_slot_y | offset_above = dead_below |
|----------|--------|--------------|-----------------|--------------------------|
| compact | 160 | 770 | — | 22px |
| standard | 176 | 763 | 845 | 15px |
| moderate | 196 | 765 | 847 | 17px |
| dense | 240 | 770 | 866 | 22px |

---

## Entry — Bottom Final Architecture Review

**Branch:** `pr6-clean`
**Status:** Review complete (no code changes)
**Last updated:** 2026-04-05

### Review conclusion

Bottom is **structurally closed** after the PR-6 through PR-7B-final series. No final PR required.

- **Problem type**: remaining issues are acceptance/visual-goal alignment only — not partition, contract, or render parity
- **title_gallery_split**: shell_top=728 clears product_secondary_slot(708) with 20px gap; subtitle wraps (clamp>=2) for all gallery counts; gallery shell top derived correctly; 15 dedicated tests pass
- **text_only_expanded**: shell_top=728; shell_height=title_band_height (content-proportionate 160-240); lower-anchored (dead space above, not below); full-width x=96/w=832; uniform pad (20/16); 11 dedicated tests pass
- **Partition judgment**: keep current `title_band_region` / `gallery_strip_region` hierarchy — no redesign needed
- **4 tracked bugs** (rule-based gallery distribution, conservative text emphasis, minimum-viable supporting_packshots, operator presentation clarity) remain as known issues per section 23 of `bottom_behavior_contract_status_v1.md`

### Recommendation

Treat bottom as known-issue, not blocker. Move to next priority (PR-B: product text shell sibling).

---

## Entry — PR-7B-final: Bottom Mode Family Contract Closure

**Branch:** `pr6-clean`
**Status:** Complete
**Last updated:** 2026-04-04

### What changed
- `app/services/poster2/template_behavior.py` — `_EXPANDED_BOTTOM_SHELL_TOPS["title_gallery_split"]` 680→728; `_EXPANDED_BOTTOM_SHELL_TOPS["text_only_expanded"]` 640→728; comments updated to state 20px design gap above product_secondary_slot bottom (708)
- `tests/poster2/test_pipeline.py` — updated 20+ stale y-assertions across 6 test classes (bottom_region, title_band_region, gallery_strip_region, gallery_slot, subtitle_slot, CSS vars); added `TestBottomModeFamilyContractClosure` (15 tests)
- `tests/poster2/test_renderer.py` — updated 2 stale gallery_shell_top assertions (872→920, 848→896); updated 1 gallery_items_y assertion (882→930)
- `docs/poster2/bottom_mode_family_contract_closure_status_v1.md` — created

### Focused validation run
- `python3 -m pytest -q tests/poster2/test_pipeline.py::TestBottomModeFamilyContractClosure` → `15 passed`
- `python3 -m pytest -q tests/poster2/test_pipeline.py tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py` → `2 failed (pre-existing), 361 passed`

### Contract change summary

| Field | Before | After |
|-------|--------|-------|
| `_EXPANDED_BOTTOM_SHELL_TOPS["title_gallery_split"]` | 680 | 728 |
| `_EXPANDED_BOTTOM_SHELL_TOPS["text_only_expanded"]` | 640 | 728 |

`product_secondary_slot` bottom = y(564) + h(144) = 708. Shell top 728 → 20px design gap (satisfies ≥ 16px).

### Invariants closed
- `title_gallery_split`: shell_top(728) ≥ product_secondary_bottom(708) + design_gap(16) = 724 ✓
- `text_only_expanded`: same ✓
- subtitle wrap: `subtitle_line_clamp=2` via text_gallery_expanded alias (unchanged, already correct) ✓
- lower-anchor occupation: dead space above only, subtitle_bottom == band_bottom − pad_bottom ✓
- all sub-cases fit within canvas (max 728+192+100=1020 ≤ 1024) ✓

---

## Entry — PR-7B4: text_only_expanded Bottom Lower-Anchor Closure

**Branch:** `pr6-clean`
**Status:** Complete
**Last updated:** 2026-04-04

### What changed
- `app/services/poster2/template_behavior.py` — all four text_only_expanded sub-cases: `title_content_pad_top` 24–40 → 20; `title_content_pad_bottom` 24–40 → 16 (uniform)
- `tests/poster2/test_pipeline.py` — updated PR-7B3 test class docstring and 9 stale y/pad assertions; updated 2 stale y assertions in `TestBottomPR6ETextOnlyFullWidthClosure`
- `docs/poster2/bottom_vertical_anchoring_closure_status_v1.md` — updated to reflect PR-7B4

### Focused validation run
- `python3 -m pytest -q tests/poster2/test_pipeline.py tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py` → `2 failed (pre-existing), 346 passed`

### Before/after pad values (text_only_expanded, all sub-cases)

| Sub-case | pad_top before→after | pad_bottom before→after | title_slot_y before→after | sub_slot_y before→after | gap_below before→after |
|----------|----------------------|--------------------------|--------------------------|------------------------|------------------------|
| compact  | 40→20                | 40→16                    | 680→704                  | —                      | 40→16 |
| standard | 32→20                | 32→16                    | 673→690                  | 755→772                | 32→16 |
| moderate | 30→20                | 30→16                    | 675→694                  | 757→776                | 30→16 |
| dense    | 24→20                | 24→16                    | 680→704                  | 776→800                | 24→16 |

---

## Entry — PR-7B3: text_only_expanded Vertical Anchoring Closure

**Branch:** `pr6-clean`
**Status:** Complete
**Last updated:** 2026-04-04

### What changed
- `app/services/poster2/template_behavior.py` — `_resolve_bottom_text_slot_metrics`: added branch for `bottom_mode == "text_only_expanded"` to compute `offset = max(available_height - used_height, 0)` instead of `(available_height - used_height) // 2`; all other modes remain center-packed
- `tests/poster2/test_pipeline.py` — updated 1 stale y assertion in `TestBottomPR6ETextOnlyFullWidthClosure::test_text_layers_follow_full_width_expanded_bottom_truth` (title y: 673→674, subtitle y: 755→756); added `TestBottomPR7B3TextOnlyExpandedVerticalAnchoring` (11 tests)
- `docs/poster2/bottom_vertical_anchoring_closure_status_v1.md` — created

### Focused validation run
- `python3 -m pytest -q tests/poster2/test_pipeline.py::TestBottomPR7B3TextOnlyExpandedVerticalAnchoring` → `11 passed`
- `python3 -m pytest -q tests/poster2/test_pipeline.py tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py` → `2 failed (pre-existing), 346 passed`

### Before/after vertical slot positions (band_top=640)

| Sub-case | title_slot_y before | title_slot_y after | subtitle_slot_y before | subtitle_slot_y after | Dead below (before→after) |
|----------|--------------------|--------------------|------------------------|-----------------------|--------------------------|
| compact | 680 | 680 | 760 (no sub) | 760 (no sub) | 0→0 |
| standard | 673 | 674 | 755 | 756 | 1→0 |
| moderate | 675 | 680 | 757 | 762 | 5→0 |
| dense | 680 | 696 | 776 | 792 | 16→0 |

Policy change: center-packed `offset = dead//2` → lower-anchored `offset = dead` for `text_only_expanded` only.

---

## Entry — PR-7A2: Header Agent Truncation Closure

**Branch:** `pr6-clean`
**Status:** Complete
**Last updated:** 2026-04-04

### What changed
- `app/services/poster2/template_behavior.py` — `identity_left_agent_right`: `agent_line_clamp` 1→2; `agent_char_budget` 28→52; `agent_slot_h` 18→36; `resolve_header_behavior`: added `if agent_line_clamp > 1: css_classes = (*css_classes, "header-agent-wrap")`
- `app/services/poster2/renderer.py` — `_agent_text_slot`: `max_lines=1` (hardcoded) → `max_lines=header_policy.agent_line_clamp` (resolver-driven)
- `app/templates_html/template_dual_v2.css` — added `.header-agent-wrap .text-agent-secondary` wrap rule using `var(--header-agent-line-clamp)` (activates only when `header-agent-wrap` present on header banner)
- `tests/poster2/test_pipeline.py` — updated 7 stale assertions from PR-7A (agent_line_clamp 1→2, --header-agent-line-clamp "1"→"2", agent_slot_h h=18→36, truncation test input "A"*40→"A"*60); added `TestHeaderAgentTruncationClosurePR7A2` (12 tests)
- `docs/poster2/header_agent_truncation_closure_status_v1.md` — created

### Focused validation run
- `python3 -m pytest -q tests/poster2/test_pipeline.py` → `226 passed`
- `python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py` → `109 passed`

### Before / after truncation evidence

| | before | after |
|--|--------|-------|
| input | "STARLIGHT CHANNEL SERVICE CENTER" (33 chars) | same |
| `agent_char_budget` | 28 | 52 |
| `agent_line_clamp` | 1 | 2 |
| `rendered_excerpt` | "STARLIGHT CHANNEL SERVICE CE" (truncated) | "STARLIGHT CHANNEL SERVICE CENTER" (full) |
| `truncation_applied` | `True` | **`False`** |

### Contract carry-forward — `identity_left_agent_right`

| field | value |
|-------|-------|
| `agent_line_clamp` | 2 |
| `agent_char_budget` | 52 |
| `agent_slot_h` | 36 |
| `header-agent-wrap` in css_classes | present |
| `--header-agent-line-clamp` | `"2"` |
| Pillow `max_lines` | resolver-driven |

`brand_block_two_line` and `brand_only`: agent fields unchanged (line_clamp=1, budget=28).

## Entry — PR-7A3: Header Wrap Render Parity Closure

**Branch:** `main`
**Status:** In progress
**Last updated:** 2026-04-04

### Engineering truth only
- Real rendered header agent node traced to `.layer-header-banner -> .layer-header-agent-zone -> .layer-agent-name-text -> .slot-agent-name-text -> .text-agent-secondary`
- Root cause closed: resolver header vars were only on `#poster-root`, but `.layer-header-banner` carried local defaults (`--header-side-width: 228px`, `--header-agent-line-clamp: 1`) that masked the live banner path; `.text-agent-secondary` therefore stayed on the single-line ellipsis path in final render
- `identity_left_agent_right` now resolves `agent_line_clamp = 2` and emits `header-agent-wrap`
- Header banner now receives resolved header behavior vars directly on the real rendered banner node
- Wrapped agent lane bounds remain aligned to the established header contract path: `{x:684, y:96, w:228, h:36}`
- Live browser evidence after fix: banner sees `--header-side-width: 228px`, `--header-agent-line-clamp: 2`; `.text-agent-secondary` computes `white-space: normal`, `text-overflow: clip`, `-webkit-line-clamp: 2`
- Before/after live Puppeteer final hash (probe case `agent_name="Smart Kitchen Upgrade Team Service Center"`):
  - before: `ae48f545cb650c5cc2bad1f5f81c527516bf10eccfd90128949ffc3c5dcaaa62`
  - after: `2b14ddda8a29dbfe3006170f05daa8346803d2d80a4af058a3370dcca08e6ec7`
- Focused validation:
  - `.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'HeaderTextContractPR7A or header_contract_review or header_text_layer or renderer_metadata_includes_layer_render_status'` → `19 passed, 195 deselected`
  - `.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'HeaderAndTitleBandLayoutControl or header_two_line_mode_emits_two_line_brand_class_and_vars_in_html'` → `5 passed, 98 deselected`
  - `.venv/bin/python -m pytest -q tests/poster2/test_contracts.py -k 'TemplateSpecLoading or structured_template_assets_exist'` → `12 passed, 5 deselected`
  - `.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py tests/poster2/test_renderer.py tests/poster2/test_contracts.py -k 'header and not bottom and not product and not scenario and not feature'` → `26 passed, 308 deselected`

---

## Entry — PR-7A: Header Text Contract / Propagation / Wrapping Closure

**Branch:** `pr6-clean`
**Status:** Complete
**Last updated:** 2026-04-04

### What changed
- `app/services/poster2/template_behavior.py` — `ResolvedHeaderBehavior`: added `agent_line_clamp: int` field (after `brand_char_budget`); added to `as_dict()`; set `agent_line_clamp = 1` in all three modes (`identity_left_agent_right`, `brand_block_two_line`, `brand_only`); `resolve_header_behavior`: adds `header-brand-wrap` to `css_classes` when `brand_line_clamp > 1`; `_resolve_header_behavior_vars`: added `"--header-brand-line-clamp"` and `"--header-agent-line-clamp"` to emitted CSS vars
- `app/services/poster2/pipeline.py` — `_build_header_contract_review`: added `"agent_line_clamp"` to `behavior_policy`; `_build_header_text_layer_evidence`: `agent_text_slot.line_clamp` changed from hardcoded `1` to `header.agent_line_clamp`
- `app/templates_html/template_dual_v2.css` — `.layer-header-banner`: added `--header-brand-line-clamp: 1` and `--header-agent-line-clamp: 1` defaults; replaced `.header-mode-brand_block_two_line .text-brand { -webkit-line-clamp: 2 }` with `.header-brand-wrap .text-brand { -webkit-line-clamp: var(--header-brand-line-clamp) }` (behavior-class-driven, CSS-var-driven)
- `tests/poster2/test_pipeline.py` — added `TestHeaderTextContractPR7A` (15 tests)
- `docs/poster2/header_text_contract_and_wrap_status_v1.md` — created

### Focused validation run
- `python3 -m pytest -q tests/poster2/test_pipeline.py` → `214 passed`
- `python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py` → `109 passed` (1 test in test_renderer.py updated: stale assertion `header-mode-brand_block_two_line` with underscores replaced by correct `header-mode-brand-block-two-line` + new `header-brand-wrap` + `--header-brand-line-clamp: 2` assertions)

### Contract fields now aligned

| field | brand_text_slot | agent_text_slot |
|-------|----------------|----------------|
| `requested_text` | ✓ | ✓ |
| `sanitized_text` | ✓ | ✓ |
| `rendered_excerpt` | ✓ | ✓ |
| `truncation_applied` | ✓ | ✓ |
| `line_clamp` | ✓ resolver | ✓ resolver (was hardcoded) |
| `char_budget` | ✓ | ✓ |
| `slot_bounds` | ✓ | ✓ |

### Propagation alignment
- `--header-brand-line-clamp` and `--header-agent-line-clamp` now emitted from resolver into inline style
- `header-brand-wrap` CSS class added by resolver when `brand_line_clamp > 1` (brand_block_two_line mode)
- CSS clamp value for brand wrap is now `var(--header-brand-line-clamp)` instead of hardcoded `2`
- `agent_line_clamp` present in `header_contract_review.behavior_policy`
- `agent_line_clamp` present in `header_text_layer.agent_text_slot.line_clamp`

### Wrap / truncation
- Brand text `identity_left_agent_right`: no wrap class (clamp=1), `white-space: nowrap` unchanged
- Brand text `brand_block_two_line`: wrap governed by `header-brand-wrap` class + `var(--header-brand-line-clamp)` = 2 (was hardcoded mode-class + hardcoded `2`)
- Agent text all modes: `agent_line_clamp=1` explicit; CSS unchanged (`white-space: nowrap`)

---

## Entry — PR-6E: text_only_expanded Full-Width Closure

**Branch:** `pr6-clean`
**Status:** Complete
**Last updated:** 2026-04-04

### What changed
- `app/services/poster2/pipeline.py` — `_title_band_region_bounds`: `x`/`w` now read from `layout.get("title_band_x", 112)` / `layout.get("title_band_w", 800)` instead of hardcoded constants; `_title_slot_bounds`: same pattern using `title_band_x`/`title_band_w`; `_subtitle_slot_bounds`: `x`/`w` from `layout.get("subtitle_slot_x/w", template.subtitle_slot.x/w)`
- `app/templates_html/template_dual_v2.css` — `.layer-title-subtitle`: `left: 112px` → `left: var(--title-band-left)`; `width: 800px` → `width: var(--title-band-width)`
- `tests/poster2/test_pipeline.py` — added `TestBottomPR6ETextOnlyFullWidthClosure` (9 tests); updated 2 existing geometry_evidence assertions in `test_renderer_metadata_includes_layer_render_status` to reflect full-width truth for no-gallery case (x=96/w=832 for title_band_region; x=136/w=752 for subtitle_slot)

### Focused validation run
- `python3 -m pytest -q tests/poster2/test_pipeline.py` → `199 passed`
- `python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py` → `109 passed`

### Carry-forward geometry

**text_only_expanded — unified full-width truth:**
- `layout_metrics["title_band_x"] = 96`, `layout_metrics["title_band_w"] = 832` (unchanged)
- `geometry_evidence.region_bounds.title_band_region` → `{x:96, y:640, w:832, h:<band_height>}` (was x=112/w=800)
- `geometry_evidence.slot_bounds.title_slot` → `{x:96, w:832, ...}` (was x=112/w=800)
- `geometry_evidence.slot_bounds.subtitle_slot` → `{x:136, w:752, ...}` (was x=152/w=720)
- CSS `.layer-title-subtitle` → `left: var(--title-band-left)`, `width: var(--title-band-width)` (was hardcoded 112/800)
- Pillow renderer: unchanged (was already consuming layout_metrics correctly)
- All four sub-cases (compact/short/moderate/dense): full-width x/w applies in all

**Side effect — no-gallery cases for other modes:**
- `title_gallery_split` / `text_gallery_expanded` with `gallery_strip_rendered=False` now also report x=96/w=832 in geometry_evidence (correct by contract; previously masked by hardcoded constants)
- Modes with gallery present (`gallery_strip_rendered=True`): x=112/w=800 unchanged

---

## Entry — PR-6D: Bottom Mode Parity and Rebalance Closure

**Branch:** `pr6-clean`
**Status:** Complete
**Last updated:** 2026-04-03

### What changed
- `app/services/poster2/template_behavior.py` — `_EXPANDED_BOTTOM_SHELL_TOPS["title_gallery_split"]`: 660 → 680; `_resolve_bottom_shell_height` for `text_only_expanded`: `return 1024 - bottom_shell_top` → `return title_band_height`; comments updated
- `app/templates_html/template_dual_v2.css` — `.state-title-only` fallback: `--bottom-shell-height` and `.region-shell-bottom height` 384px → 160px; comment updated
- `tests/poster2/test_pipeline.py` — updated all title_gallery_split y-values +20px (shell_top 660→680; gallery_strip, title_band, subtitle_slot, gallery_slot coordinates shifted); updated text_only_expanded shell-height tests (now expects `shell_height == title_band_height`); updated PR-6C class docstring and `test_toe_shell_still_fills_to_canvas_bottom` → `test_toe_shell_height_equals_title_band_height`; updated `test_toe_title_band_is_smaller_than_shell` → `test_toe_title_band_equals_shell_for_all_sub_cases`; added `TestBottomPR6DModeParityClosure` (16 tests)
- `tests/poster2/test_renderer.py` — `gallery_shell_top` 852→872, 828→848; `gallery_items_y` 862→882

### Focused validation run
- `python3 -m pytest -q tests/poster2/test_pipeline.py` → `192 passed`
- `python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py` → `109 passed`

### Carry-forward geometry

**title_gallery_split:**
- `bottom_shell_top`: 680 (was 660; cumulative +40px from original 640; eliminates bottom-image overlap)
- All gallery/title heights, widths, distribution rules: unchanged

**text_only_expanded:**
- `bottom_shell_top`: 640 (unchanged)
- `bottom_shell_height`: = `title_band_height` (160 / 176 / 196 / 220 per sub-case)
- `shell_top + shell_height`: 800 / 816 / 836 / 860 (dead canvas eliminated)
- `title_band_x = 96`, `title_band_w = 832` (unchanged)
- `layout_metrics["bottom_shell_height"] == layout_metrics["title_band_height"]` for all sub-cases
- CSS vars and layout_metrics unified: no separate geometry_evidence vs layout_metrics divergence

---

## Entry — PR-6C: Bottom Mode Rebalance

**Branch:** `pr6-clean`
**Status:** Complete
**Last updated:** 2026-04-03

### What changed
- `app/services/poster2/template_behavior.py` — `_EXPANDED_BOTTOM_SHELL_TOPS["title_gallery_split"]`: 640 → 660; comment updated; `text_only_expanded` branch: `title_band_height` per sub-case 384 → 160/176/196/220; `title_content_pad_top`/`pad_bottom` updated to 28–40; `_resolve_bottom_shell_height` comment updated
- `app/templates_html/template_dual_v2.css` — `.layer-bottom-region.state-title-only`: `--title-band-height` 384px → 160px; `--title-content-height` 384px → 160px; comment updated
- `tests/poster2/test_pipeline.py` — `title_gallery_split` shell_top assertion 640 → 660; `TestBottomPR6BExpandedSpaceClosure` title_band_height test updated; CSS var `--title-band-height` assertion updated to 160px; 8 geometry y-values shifted +20px; added `TestBottomPR6CModeRebalance` (16 tests)
- `tests/poster2/test_renderer.py` — 3 gallery geometry y-values shifted +20px

### Focused validation run
- `python3 -m pytest -q tests/poster2/test_pipeline.py` → `177 passed`
- `python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py` → `109 passed`

### Carry-forward geometry

**title_gallery_split:**
- `bottom_shell_top`: 660 (was 640; +20px shift eliminates bottom-image overlap)
- All gallery/title heights unchanged; everything inside the shell shifts +20px

**text_only_expanded:**
- `bottom_shell_top`: 640 (unchanged)
- `bottom_shell_height`: 384 (unchanged; fills to canvas bottom)
- `title_band_height`: 160 (no subtitle) / 176 (short subtitle) / 196 (moderate subtitle >28) / 220 (dense subtitle >48)
- `title_band_x = 96`, `title_band_w = 832` (PR-6 full-width carry-forward, unchanged)
- `title_band_expansion_policy = "full_width_title_band_no_gallery"` (unchanged)

---

## Entry — PR-6B: Bottom Expanded Space / Text Expansion / Overlap Closure

**Branch:** `pr6-clean`
**Status:** Complete
**Last updated:** 2026-04-02

### What changed
- `app/services/poster2/template_behavior.py` — `_EXPANDED_BOTTOM_SHELL_TOPS["text_only_expanded"]`: 656 → 640; `text_only_expanded` branch: `title_band_height = 384` (all 4 sub-cases, was 164–220), `pad_top`/`pad_bottom` updated to 80–112 for centering; `_resolve_bottom_shell_height` for `text_only_expanded`: `return title_band_height` → `return 1024 - bottom_shell_top`
- `app/templates_html/template_dual_v2.css` — `.layer-bottom-region.state-title-only` CSS fallback vars and shell height updated to match new geometry (top 728→640, height 160→384)
- `tests/poster2/test_pipeline.py` — updated `bottom_shell_top == 656` assertion to `== 640`; added `TestBottomPR6BExpandedSpaceClosure` (13 tests)

### Focused validation run
- `python3 -m pytest -q tests/poster2/test_pipeline.py` → `161 passed`
- `python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py` → `109 passed`

### Carry-forward geometry for text_only_expanded
- `bottom_shell_top`: 640 (was 656)
- `bottom_shell_height`: 384 (= 1024 − 640; fills to canvas bottom)
- `title_band_height`: 384 (all sub-cases; title band = full shell)
- `shell_top + shell_height = 1024` ✓ (no dead canvas below)
- `title_band_x = 96`, `title_band_w = 832` (PR-6 full-width carry-forward, unchanged)

---

## Entry — PR-6: Bottom Optional Subtitle Closure

**Branch:** `claude/festive-heisenberg`
**Status:** Complete
**Last updated:** 2026-04-02

### What changed
- `app/services/poster2/template_behavior.py` — `ResolvedBottomBehavior`: added `title_band_expansion_policy: str` field + `as_dict()` update; `_resolve_bottom_layout_policies`: added PR-6 horizontal expansion block computing `title_band_x`, `title_band_w`, `subtitle_slot_x`, `subtitle_slot_w`, `title_band_expansion_policy` (full_width_title_band_no_gallery when `title_slot_rendered and not gallery_strip_rendered`, else standard/no-band); `_resolve_bottom_behavior_vars`: added `--title-band-left` and `--title-band-width`
- `app/templates_html/template_dual_v2.css` — `#poster-root`: added `--title-band-left: 112px` and `--title-band-width: 800px`; `.region-shell-title-band`: `left: 112px` → `left: var(--title-band-left)`, `width: 800px` → `width: var(--title-band-width)`
- `app/services/poster2/renderer.py` — `_title_band_shell_bounds`: uses `layout_metrics["title_band_x"]` and `layout_metrics["title_band_w"]`; `_title_text_slot`: overrides `x` and `w` from layout_metrics; `_subtitle_text_slot`: overrides `x` and `w` from `layout_metrics["subtitle_slot_x"]` and `["subtitle_slot_w"]`
- `tests/poster2/test_pipeline.py` — added `TestBottomPR6OptionalSubtitleClosure` class (10 tests across 4 cases + CSS var evidence)

### Focused validation run
- `python3 -m pytest -q tests/poster2/test_pipeline.py` → `148 passed`
- `python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py` → `109 passed`

---
## Entry — PR-C: Text Capacity / Label Bounds / Clamp / Connector Tuning

**Branch:** `claude/festive-heisenberg`
**Status:** Complete
**Last updated:** 2026-04-02

### What changed
- `app/templates/specs/template_dual_v2.json` — slots 1-3 `label_box.h` 60→76; `label_box.max_lines` 2→3; slot 4 unchanged
- `app/templates_html/template_dual_v2.css` — added `.product-annotation-mode-product_anchor_callouts .feature-callout { -webkit-line-clamp: 3; line-clamp: 3; min-height: 76px; }`
- `app/services/poster2/renderer.py` — `_resolve_feature_callout_layout` template_anchor_fixed branch: `max_lines=2` → `max_lines=3`
- `app/services/poster2/template_behavior.py` — `_PRODUCT_TEXT_SHELL_H` 260→276; comment updated; `char_budget` map `{1:40,2:34,3:28}`→`{1:44,2:38,3:32}`; `anchor_char_budgets` same; `line_clamp` 2→3 and `text_budget_policy` `fixed_3_anchor_three_line_budget` for product_anchor branch; `truncation_policy` `three_line_clamp` and `line_clamp=3` in `resolve_feature_behavior`
- `tests/poster2/test_pipeline.py` — updated 4 assertions `h==260`→`h==276`; renamed `test_text_shell_bounds_unaffected` to `test_text_shell_bounds_after_prc`; added `TestProductTextCapacityPRC` (12 tests)

### Focused validation run
- `python3 -m pytest -q tests/poster2/test_pipeline.py` → `138 passed`
- `python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py` → `109 passed`

---
## Entry — PR-4: Product Geometry Rebalance

**Branch:** `claude/festive-heisenberg`
**Status:** Complete
**Last updated:** 2026-04-02

### What changed
- `app/services/poster2/template_behavior.py` — `_PRODUCT_DUAL_PRIMARY_SLOT` h 310→360; `_PRODUCT_DUAL_SECONDARY_SLOT` y 518→564 h 210→144; comment block updated
- `app/services/poster2/renderer.py` — stale comment updated (h:310→h:360)
- `tests/poster2/test_pipeline.py` — updated 8 existing assertions to new geometry; added `TestProductGeometryPR4Rebalance` (10 tests)

### Focused validation run
- `python3 -m pytest -q tests/poster2/test_pipeline.py` → `126 passed`
- `python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py` → `109 passed`

---

## Entry — PR-3: Product Text-Layer UI and Stage2 Driver Wiring

**Branch:** `claude/festive-heisenberg`
**Status:** Complete
**Last updated:** 2026-04-02

### What changed
- `frontend/stage2.html` · `docs/stage2.html` — `buildProductDetail` enhanced:
  - `text_shell` status chip (reads `product_text_shell_layer.rendered` / `.reason_code` from backend payload)
  - text shell bounds + owner row: `text_shell (x,y,w,h) · owner: product_region / product_text_shell_layer`
  - `no-compete-with-canvas` badge gated on `text_does_not_compete_with_canvas` backend truth
  - `char_budget` / `line_clamp` row from `productReview.behavior_policy`
  - Full annotation slot text chain: `requested_text` → `sanitized_text` (if sanitization) → `rendered_excerpt` (if truncated)
- `tests/test_stage2_guard_diagnostics_surface.py` — new test `test_frontend_stage2_surfaces_product_text_shell_evidence`

### Focused validation run
- `pytest -q tests/test_stage2_guard_diagnostics_surface.py` → `6 passed`
- `pytest -q tests/poster2/test_pipeline.py -k TestProductTextShellContract` → `9 passed`

---

## Mainline Replacement Note
- old `origin/main` archived before replacement:
  - branch: `archive/main-before-pra-product-outer-shell-20260401`
  - tag: `backup/main-before-pra-product-outer-shell-20260401`
- new `origin/main` points to `fix/pra-product-outer-shell` baseline commit `1b4d001`
- no merge commit was used
- future poster2 work starts from the new `main` only

## Current Active Workstream
- workstream: `product region contract upgrade`
- execution mode: `one function = one PR`
- current active PR: `PR-5 / PR-C complete`
- current PR status doc: `docs/poster2/product_region_pr5_text_capacity_tuning_status_v1.md`
- alias doc (internal): `docs/poster2/product_region_prc_text_capacity_tuning_status_v1.md`

## Frozen Unchanged
- bottom frozen as SOP baseline
- `feature_region` must stay delegated diagnostic when product annotation is active
- header/scenario behavior out of scope for current product-region PRs
- beautification out of scope
- old-main compatibility must not be reopened

## Carry-Forward Truth From PR-A
- `product_region` / `product_card_shell_layer` outer shell: `{x:456,y:188,w:472,h:540}`
- `product_canvas_shell_layer`: `{x:456,y:188,w:300,h:540}`
- `product_image_layer` anchors to `product_canvas_shell_layer`, not the widened outer shell
- fixed annotation lane remains on the right side and was intentionally not reopened in PR-A
- declared next priority after PR-A: add `product_text_shell` as a sibling shell and keep `feature_region` suppressed

## Last Accepted PR
- `PR-6E — text_only_expanded Full-Width Closure`
- status: complete
- status doc: `docs/poster2/bottom_region_pr6e_text_only_full_width_closure_status_v1.md`
- carry-forward result:
  - `geometry_evidence.region_bounds.title_band_region` x/w now reads from `layout_metrics["title_band_x/w"]` — no longer hardcoded 112/800
  - `geometry_evidence.slot_bounds.title_slot` x/w reads from `layout_metrics["title_band_x/w"]`
  - `geometry_evidence.slot_bounds.subtitle_slot` x/w reads from `layout_metrics["subtitle_slot_x/w"]`
  - CSS `.layer-title-subtitle`: `left: var(--title-band-left)`, `width: var(--title-band-width)`
  - Full-width truth unified: resolver → CSS vars → geometry_evidence → rendered slot bounds all agree at x=96/w=832 for text_only_expanded
  - No-gallery cases for other modes also report correct full-width geometry (was previously masked)

## Previous Last Accepted PR
- `PR-5 (PR-C) — Text Capacity / Label Bounds / Clamp / Connector Tuning`
- status: complete
- status doc: `docs/poster2/product_region_pr5_text_capacity_tuning_status_v1.md`
- carry-forward result:
  - `label_box.h` 60→76 for slots 1-3; slot 4 unchanged
  - `label_box.max_lines` 2→3 for slots 1-3
  - CSS: `-webkit-line-clamp: 3` for product_anchor_callouts mode
  - Pillow: `max_lines=3` for template_anchor_fixed
  - `_PRODUCT_TEXT_SHELL_H` 260→276 (slot_3 bottom 492 − slot_1 top 216)
  - `char_budget`: `{1:44, 2:38, 3:32}` (was `{1:40, 2:34, 3:28}`)
  - `line_clamp=3`, `text_budget_policy="fixed_3_anchor_three_line_budget"` for product_anchor
  - `truncation_policy="three_line_clamp"` in ResolvedFeatureBehavior
  - inter-slot gap: 40px→24px (slots use 16px more h, gaps tighten by same)
  - `product_primary_slot`, `product_secondary_slot`, outer shell, canvas shell — all unchanged

## Current PR Goal
`next: TBD` (PR-6E complete)

## Reading Rule For New Sessions
Do not read this whole file as a long archive.
Read only these sections:
1. `Mainline Replacement Note`
2. `Current Active Workstream`
3. `Last Accepted PR`
4. `Current PR Goal`

If deeper detail is needed, open the linked PR status doc instead of expanding this file.

## Archive Note
Detailed historical entries were moved out of the active working set.
Use an archive file or the per-PR status docs for full historical detail.
## Entry — PR-7B: Bottom Subtitle Wrapping And Expansion Closure

Scope:
- `title_gallery_split`: close remaining single-line subtitle overflow fallback by moving active subtitle-present split cases to controlled two-line clamp
- `text_only_expanded`: close text-layer propagation parity so title/subtitle slot bounds follow expanded bottom truth, not frozen template slot width

Files:
- `app/services/poster2/template_behavior.py`
- `app/services/poster2/pipeline.py`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_renderer.py`
- `docs/poster2/bottom_subtitle_wrap_and_expansion_status_v1.md`

Engineering truth:
- active `title_gallery_split` subtitle policy now resolves to `two_line_clamp_inside_expanded_split_title_band`
- active `title_gallery_split` subtitle clamp now resolves to `2`, and subtitle slot height to `44`
- `text_only_expanded` `title_text_layer.slot_bounds` now uses `title_band_x/w`
- `text_only_expanded` `subtitle_text_layer.slot_bounds` now uses `subtitle_slot_x/w`

Frozen unchanged:
- header
- product geometry
- feature delegation
- beautification
- email/save workflow
- bottom structure and gallery distribution

## Entry — PR-S2: Bottom Mode Switch Investigation And Closure

Branch / PR:
- `PR-S2 — bottom mode switch investigation and closure`

Scope:
- investigate the post-generate Stage2 bottom mode switch failure for `title_only`, `title_only_expand`, and `text_only_expanded`
- close the request-state / normalization / parity bug with the smallest frontend-state fix
- keep bottom in maintenance mode only

What was read first:
- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/bottom_behavior_contract_status_v1.md`
- latest stage2 screenshots / console / network payload evidence: not present as a tracked workspace artifact in this run
- latest runtime evidence for `text_only_expanded`: taken from the focused pipeline/runtime test path

Root rules followed:
- docs first
- contract/request-state first
- no bottom redesign
- no header/product/feature/email scope drift
- keep `frontend/` and `docs/` aligned

Problem reproduced:
- after a successful generate, switching bottom mode and regenerating could still leak a stale bottom token into the backend request
- `title_only` remained a legacy alias at the UI level
- stale `title_only_expand` could survive through local state even though it is not a valid backend runtime mode

Root cause found:
- the leaking code path was frontend request-state logic, not backend contract logic
- exact leaking path:
  - `ensurePoster2BottomContractState(...)`
  - `syncPoster2BottomContractFromControls(...)`
  - `buildPoster2BottomRequestState(...)`
  - `initPoster2BottomContractControls(...)`
- these paths forwarded raw `bottomMode` without canonicalization before request preview and final generate payload construction

Files changed:
- `frontend/app.js`
- `docs/app.js`
- `tests/poster2/test_api.py`
- `tests/test_stage2_guard_diagnostics_surface.py`
- `docs/poster2/bottom_mode_switch_closure_status_v1.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/README.md`
- `CLAUDE.md`

Layer changed:
- behavior
- docs
- validation

Validation run:
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py -k 'bottom or docs_publish_mirror_contains_same_guard_diagnostics'`
  - `2 passed, 4 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py -k 'title_only or bottom_mode or text_gallery_expanded or gallery_only'`
  - `2 passed, 17 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'requested_effective_and_override_reason or title_only_alias_canonicalized or gallery_only_bottom_mode_region_contract_marks_title_band_collapsed or text_only_expanded_bottom_mode_region_contract_marks_gallery_strip_collapsed or title_gallery_split_bottom_mode_region_contract_requires_title_band or text_gallery_expanded_bottom_mode_region_contract_requires_title_band or diagnostics_are_stable_for_all_modes'`
  - `6 passed, 251 deselected`

Exact acceptance:
- switching bottom mode after a successful generate no longer relies on stale raw mode tokens
- `title_only` now canonicalizes to `text_only_expanded` before runtime request construction
- stale `title_only_expand` now canonicalizes to `text_only_expanded` before runtime request construction
- Stage2 request preview and final generate payload both use the same canonical `bottom_mode`
- mixed-state, text-only, and gallery-only bottom modes retain the expected requested/effective/layout diagnostics and collapse rules
- `frontend/` and `docs/` remain aligned

Remaining risks:
- this closes the request-state / parity failure only
- any residual bottom text/layout tuning should remain a known maintenance issue while storage / copy / email work proceeds

## Entry — PR: Generation Quality And Copy Optimization

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-06

### Scope
- poster-facing text sanitization for title / subtitle / features / annotation-derived text
- deterministic draft quality tightening
- Gemini optimizer quality tightening
- explicit fallback preservation

### What was read first
- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/email_copy_optimizer_and_optional_attachment_status_v1.md`
- `docs/poster2/bottom_behavior_contract_status_v1.md`

### Root rules followed
- contract-first
- no poster contract drift
- no bottom truth drift
- no product annotation truth drift
- no resend / attachment transport scope drift
- no geometry or beautification work

### Problem reproduced
- current deterministic draft still treated subtitle as too strong a backup source
- prompt-like / internal / training-like text could enter copy inputs from subtitle, features, or annotation text
- Gemini path had no post-sanitization guard against unsafe invented claims
- Gemini success path did not yet enforce “cleaner than deterministic base”

### Root cause found
- copy quality logic had no dedicated poster-facing sanitization layer
- canonical input gathered raw business text too early
- Gemini output was trusted as long as the request succeeded, without grounded-claim filtering or material-improvement check

### Files changed
- `app/services/email/copy_safety.py`
- `app/services/email/drafts.py`
- `app/services/email/copy_optimizer.py`
- `app/services/email/gemini_optimizer.py`
- `tests/poster2/test_api.py`
- `tests/poster2/test_pipeline.py`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/generation_quality_and_copy_optimization_status_v1.md`
- `docs/poster2/README.md`
- `CLAUDE.md`

### Layer changed
- behavior
- docs
- validation

### Validation run
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py`
  - `21 passed`
- `./.venv/bin/python -m pytest -q tests/test_stage3_email_closure_surface.py`
  - `2 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'email or poster_record or attachment or draft'`
  - `5 passed, 255 deselected`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
  - `2 passed`

### Exact acceptance
- no dirty subtitle leaks into final marketing copy
- email copy and poster copy remain aligned without mechanically duplicating dirty subtitle text
- Gemini success path is accepted only when cleaner and safely grounded
- Gemini failure or unsafe output falls back to deterministic business-safe copy
- no contract drift

### Remaining risks
- live Gemini quality still needs deployed-environment review with real credentials
- this round intentionally does not touch send-provider transport or deployment-side delivery behavior

## Entry — PR-10A: poster2 visual polish phase 1

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-06

### Scope
- visual hierarchy polish only
- header optical balance
- scenario attention softening
- product primary-secondary hierarchy polish
- callout pill refinement
- bottom title/subtitle emphasis rebalance
- gallery strip evidence styling

### What was read first
- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/product_region_annotation_contract_status_v1.md`

### Root rules followed
- contract-first baseline preserved
- no geometry drift
- no ownership drift
- no resend / email / storage scope drift
- no contract expansion
- no header/product/bottom geometry rewrite

### Files changed
- `app/templates_html/template_dual_v2.css`
- `tests/poster2/test_renderer.py`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/visual_polish_phase1_status_v1.md`
- `docs/poster2/README.md`

### Layer changed
- beautification
- docs
- validation

### Visual changes
- softened scenario visual dominance so product reads as the stronger subject
- clarified product primary vs secondary hierarchy through shadow/opacity treatment only
- refined product annotation callout pills, connectors, and markers
- rebalanced bottom title/subtitle emphasis so subtitle no longer competes with title
- polished gallery strip shell and item evidence styling
- improved header optical balance without changing header structure or line-lane truth

### Validation run
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'template_css_exposes_peer_region_fit_policies or template_css_exposes_visual_polish_phase1_without_geometry_tokens_drift or HeaderAndTitleBandLayoutControl or template_html_marks_real_scenario_when_asset_exists or text_only_expanded_html_keeps_full_width_text_layer_vars'`
  - `8 passed, 97 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TestProductLayoutContract or TestTask2FinalProductGeometry or TestProductImageContract or TestBottomModeFamilyContractClosure'`
  - `32 passed, 228 deselected`

### Remaining risks
- production-like visual review is still needed to judge the final polish level
- one broader pipeline assertion outside PR-10A scope still fails on `template_layout_policy.layout_density_mode` mismatch; no geometry/ownership assertion failed in this PR

### Exact acceptance
- no geometry drift
- no ownership drift
- scenario is visually softer and no longer overpowers product
- product region hierarchy is clearer
- bottom subtitle no longer competes with title

## Entry — PR-11: poster2 product region closeout

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-06

### Scope
- product_anchor_callouts contract tune: label_box.w 144→176 for active slots 0-2
- char_budget widened: {1:44, 2:38, 3:32} → {1:52, 2:46, 3:44}
- _PRODUCT_TEXT_SHELL_W 144→176, _PRODUCT_REGION_OUTER_W 472→504
- annotation card visual reconstruction: card surface, connector, marker
- template version bump: 2.1.5 → 2.1.6

### What was read first
- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/product_region_annotation_contract_status_v1.md`
- `app/templates/specs/template_dual_v2.json`
- `app/services/poster2/template_behavior.py`
- `app/templates_html/template_dual_v2.css`

### Root rules followed
- contract-first: constants and JSON updated before visual CSS
- no anchor_x / label_box.x / y-position changes
- overflow-safety slot (index 3, y=516) label_box.w unchanged at 144
- no ownership drift: product region outer width updated in sync with text shell
- no bottom / email / storage / Stage2 / Stage3 scope
- no header / scenario region changes
- right edge invariant preserved: 784+176=960=456+504 ✓
- no-compete invariant preserved: text_shell_x (784) > canvas_right (756) ✓
- right margin: 1024−960=64px > safe_margin 48px ✓

### Files changed
- `app/templates/specs/template_dual_v2.json`
- `app/services/poster2/template_behavior.py`
- `app/services/poster2/template_registry.py`
- `app/templates_html/template_dual_v2.css`
- `app/templates_html/slot_spec.template_dual_v2.json`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_contracts.py`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed
- contract
- beautification
- validation
- docs

### Contract changes
- `template_dual_v2.json`: feature_callouts[0-2].label_box.w 144→176; version 2.1.5→2.1.6
- `template_behavior.py`: _PRODUCT_TEXT_SHELL_W 144→176, _PRODUCT_REGION_OUTER_W 472→504
- `template_behavior.py`: char_budget dict {1:44,2:38,3:32} → {1:52,2:46,3:44} (both resolve_product_behavior and resolve_feature_behavior locations)

### Visual changes
- annotation card: border-radius 12px (from base 18px), border opacity 0.12→0.18, dual-layer shadow + inset top highlight, letter-spacing, text-wrap: balance
- connector: solid accent line (background: var(--accent-tone)), opacity 0.72→0.88, height 2→1.5px
- marker: size 14→16px, outer glow ring added (5px at 16% opacity), shadow depth 0.18→0.28

### Validation run
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TestProductAnnotationGeometryPR4 or TestProductTextShellContractPR4 or TestProductTextCapacityPRC or TestProductLayoutContract or TestPosterPipelineRun' tests/poster2/test_contracts.py`
  - `52 passed, 4 pre-existing TestPosterPipelineRun failures (bottom layout_density_mode mismatch — not in scope)`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py tests/poster2/test_contracts.py tests/poster2/test_renderer.py`
  - `359 passed, 29 pre-existing failures (all TestBottom/TestHeader/TestBottomSplitBehavior — not in scope)`

### Remaining risks
- visual review needed: regenerate ChefCraft fryer poster to confirm truncation elimination and card quality
- Pillow renderer still uses bg_radius=8 (template JSON unchanged) — CSS and Pillow renderer diverge on border-radius; Pillow fallback path is maintenance-only

### Exact acceptance
- label_box.w=176 for slots 0-2, w=144 preserved for overflow slot 3
- right edge 960px, margin 64px
- char_budget 44 for 3 items — "Stainless steel finish with easy cleaning" (40 chars) fits without truncation
- all geometry invariants hold
- no ownership drift

## Entry — PR-TB-BE1: Template B backend generation fix

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-08

### Scope
- fix `template_product_sheet_v1` backend 500 on `/api/v2/generate-poster`
- keep Template A unchanged
- keep Stage3 / resend / email closure unchanged
- keep frozen bottom SOP baseline unchanged

### What was read first
- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/template_b_line2_independent_flow_status_v1.md`

### Additional inspection done first
- branches inspected:
  - `claude/flamboyant-mclaren`
  - `claude/gracious-allen`
- file inspected and missing:
  - `docs/poster2/template_b_kitchen_center_hero_status_v1.md` was not present in workspace

### Root rules followed
- contract-first
- no Template A runtime drift
- no resend / Stage3 / email closure drift
- no unrelated beautification changes
- no bottom SOP redesign
- kept the fix to payload normalization, renderer split, fallback safety, and error observability only

### Problem reproduced
- frontend Stage2 now sends valid Template B payloads
- backend no longer 422s
- runtime still failed with `poster2_generation_failed`
- local real-pipeline reproduction exposed the concrete crash chain

### Root cause found
- Puppeteer renderer still used Family A gallery assumptions for Template B and dereferenced `bottom_gallery_items_layer`
- Pillow fallback / pipeline evidence still assumed Family A `subtitle_slot_state.reason_code`
- quality guard only received `bottom_mode`, so Family B mandatory regions were mis-evaluated during fallback

### Files changed
- `app/main.py`
- `app/services/poster2/pipeline.py`
- `app/services/poster2/renderer.py`
- `app/services/poster2/template_behavior.py`
- `tests/poster2/test_api.py`
- `tests/poster2/test_pipeline.py`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/template_b_backend_generation_fix_status_v1.md`

### Layer changed
- behavior
- renderer
- validation
- docs

### Exact backend exception reproduced
- first failure:
  - `KeyError: 'bottom_gallery_items_layer'`
  - Template B Puppeteer path was still entering Family A gallery visibility logic
- second failure:
  - `KeyError: 'reason_code'`
  - Family B `description_block` bottom stub lacked `subtitle_slot_state.reason_code`
- third failure after the two direct crashes were fixed:
  - `fallback result does not satisfy minimum deliverable regions: logo_banner_region, product_hero_region, top_copy_region`
  - Family B binding inputs were missing in deliverability evaluation

### Validation run
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py`
  - `27 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'product or annotation or single_primary or template_b'`
  - `81 passed, 191 deselected`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
  - `5 passed`

### Remaining risks
- local environment still lacks Chromium and the full Noto font set, so Template B currently succeeds through clean Pillow fallback in local tests
- deployed environment still needs one live operator validation pass for Template B primary-only / secondary / materials-empty states

### Exact acceptance
- `/api/v2/generate-poster` succeeds for `template_product_sheet_v1`
- primary-only path works
- primary+secondary path works
- materials strip path works
- empty materials path works
- empty description path works
- Template A remains unchanged

## PR-TB-P1 — Template B parity / visual-contract closure

### Root rules followed
- contract-first
- backend evidence remains source of truth
- Template A untouched
- no Template B geometry redesign
- `frontend/` and `docs/` kept aligned

### Problem reproduced
- Template B metadata could report clean Family B ownership while final visible render still drifted from declared regions
- visible drift was most likely in banner content, top-copy placement, hero occupancy, and description containment
- Stage2 diagnostics did not expose backend visible-truth parity checks

### Root cause found
- Template B HTML mixed global poster-root slot coordinates with nested positioned Family B containers
- Puppeteer path emitted structural layer truth but not DOM/computed visible-truth evidence
- pipeline therefore could still report clean structure truth even when visible containment had drifted

### Files changed
- `app/services/poster2/renderer.py`
- `app/services/poster2/pipeline.py`
- `app/services/poster2/contracts.py`
- `app/schemas/poster2.py`
- `app/main.py`
- `app/templates_html/template_product_sheet_v1.html`
- `app/templates_html/template_product_sheet_v1.css`
- `frontend/app.js`
- `frontend/stage2.html`
- `frontend/index.html`
- `frontend/styles.css`
- `docs/app.js`
- `docs/stage2.html`
- `docs/index.html`
- `docs/styles.css`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/template_b_parity_and_visual_contract_status_v1.md`

### Layer changed
- renderer
- validation
- metadata / API payload
- Stage1 / Stage2 preview + diagnostics
- docs

### Validation run
- `./.venv/bin/python -m py_compile app/services/poster2/renderer.py app/services/poster2/pipeline.py app/services/poster2/contracts.py app/schemas/poster2.py app/main.py`
  - pass
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TemplateBBackendGenerationFix'`
  - `13 passed, 266 deselected`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py`
  - `6 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py -k 'template_b or generate_poster_v2_accepts_template_b'`
  - `4 passed, 23 deselected`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py -k 'template_b_independent_preview_and_generate_path_are_present or stage1_operator_surfaces_and_publish_mirror_are_aligned'`
  - `2 passed, 3 deselected`

### Remaining risks
- no fresh live before/after Chromium screenshot bundle was generated locally in this task
- parity enforcement applies to Puppeteer evidence; degraded Pillow fallback still relies on structural evidence only
- any future Template B DOM refactor must keep parity keys and backend target mapping aligned

## PR-TB-P0A — Template B expression contract closeout

### Root rules followed
- contract-first
- behavior before beautification
- Template B geometry frozen
- Template A untouched
- `frontend/` and `docs/` kept aligned

### Problem reproduced
- Template B already had clean Family B structure truth, but several expression behaviors still lived as implicit styling assumptions instead of explicit runtime contract
- Stage2 could not directly read Template B expression modes such as header visual treatment, top-copy hierarchy, secondary inset strategy, or short-description density
- short description states still resolved to a large generic block without explicit runtime density truth

### Root cause found
- Template B resolver exported structural ownership and parity truth, but not the Family B expression modes needed for a stable operator/runtime contract
- renderer consumed Template B content states, but not Family B-specific hierarchy/emphasis/density mode classes from backend behavior
- Stage2 diagnostics therefore lacked direct backend truth for the expression modes the operator needs to reason about

### Files changed
- `app/templates/specs/template_product_sheet_v1.json`
- `app/services/poster2/template_behavior.py`
- `app/services/poster2/pipeline.py`
- `app/services/poster2/renderer.py`
- `app/templates_html/template_product_sheet_v1.css`
- `frontend/stage2.html`
- `docs/stage2.html`
- `docs/app.js`
- `tests/poster2/test_contracts.py`
- `tests/poster2/test_pipeline.py`
- `tests/test_stage2_guard_diagnostics_surface.py`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/template_b_p0_expression_closeout_status_v1.md`

### Layer changed
- contract
- resolver / behavior wiring
- renderer consumption
- metadata / diagnostics
- minimal shell/text styling for short-copy density

### Validation run
- `./.venv/bin/python -m py_compile app/services/poster2/template_behavior.py app/services/poster2/pipeline.py app/services/poster2/renderer.py`
  - pass
- `./.venv/bin/python -m pytest -q tests/poster2/test_contracts.py -k 'product_sheet or behavior_modes'`
  - `4 passed, 14 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TemplateBBackendGenerationFix and (behavior_modes_surface_expression_closeout_truth or secondary_asset_reports_correct_layout_reason or description_evidence_emitted_when_description_fields_exist or product_hero_evidence_uses_consistent_full_width_owner_geometry)'`
  - `4 passed, 276 deselected`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py -k 'prefers_backend_product_and_bottom_runtime_evidence or docs_publish_mirror_contains_same_guard_diagnostics'`
  - `2 passed, 4 deselected`

### Remaining risks
- this PR only closes Template B P0A contract/expression truth; visual down-weighting and hero/materials/description visual refinement remain for the next Puppeteer expression pass
- `description_density_mode` currently uses a conservative short-copy heuristic based on current body/title length, so edge cases may still need tuning after real operator samples
- no live generated Template B sample payload was produced in this step; validation here is metadata/tests first

## PR-TB-P0B/P0C — Template B expression and operator-line closeout

### Root rules followed
- contract-first
- geometry frozen
- behavior before beautification
- no Template A behavior changes
- `frontend/` source and `docs/` mirror updated together

### Problem reproduced
- Template B still looked too heavy in the banner, too washed in the hero, and too loose in the description block even though Family B structure was already correct
- Stage1 hid the product image inputs when Template B was selected because the product asset fieldset was still gated by Family A visibility
- Stage2 still treated Template B as a partial pilot path by coercing `puppeteer` back to `auto`

### Root cause found
- Template B preview/final shell styling was still carrying placeholder-level visual weight and opacity from the initial baseline
- Stage1 operator controls still attached core product assets to a Family A-only visible group instead of a shared product asset surface
- Stage2 request wiring still contained a stale Template B renderer coercion path from the earlier pilot stage

### Files changed
- `app/templates_html/template_product_sheet_v1.css`
- `frontend/index.html`
- `frontend/stage2.html`
- `frontend/app.js`
- `frontend/styles.css`
- `docs/index.html`
- `docs/stage2.html`
- `docs/app.js`
- `docs/styles.css`
- `tests/test_frontend_docs_sync.py`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/template_b_p0_visual_and_operator_closeout_status_v1.md`

### Layer changed
- Template B HTML/CSS expression
- Stage1 operator flow
- Stage2 operator flow
- frontend/docs publish mirror

### Validation run
- `./.venv/bin/python -m py_compile app/services/poster2/template_behavior.py app/services/poster2/pipeline.py app/services/poster2/renderer.py`
  - pass
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
  - `5 passed`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py`
  - `6 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TemplateBBackendGenerationFix or test_template_a_regression_path_remains_unchanged'`
  - `14 passed, 266 deselected`

### Remaining risks
- no fresh live Chromium screenshot pair was generated in this closeout step, so the visual pass is still code/test validated rather than screenshot-validated
- Template B now allows explicit `puppeteer` selection again, but one live operator pass should still confirm that Stage2 and final generation visually align on real assets
- further palette exploration is intentionally deferred; this pass only tightened hierarchy and operator/runtime parity

## PR-AR1 — Family-aware evidence/parity isolation

### Root rules followed
- contract-first
- renderer executes family truth; renderer does not define cross-family truth
- isolation repair before beautification
- no Family A behavior/geometry changes
- no Template B contract/geometry changes

### Temporary priority override
- current temporary priority override = Family A isolation repair + family anti-crossline hardening

### Problem reproduced
- `template_dual_v2` runtime payload still carried Template B-only visible-truth keys such as `logo_banner_region`, `top_copy_region`, `materials_strip_region`, `product_hero_region`, and `description_region`
- Family A payload also surfaced `template_b_parity_review`, which made Stage2/runtime diagnostics look like A/B had a shared parity surface even while Family A behavior truth remained frozen

### Root cause found
- Puppeteer visible-truth collection was hard-coded to a Template B parity-key list and ran for every template
- pipeline manifest assembly forwarded raw `visible_truth_evidence` into the manifest without a family whitelist pass, so a mixed renderer payload could leak cross-family evidence keys

### Files changed
- `app/services/poster2/renderer.py`
- `app/services/poster2/pipeline.py`
- `tests/poster2/test_pipeline.py`
- `docs/poster2/current_branch_execution_log_v1.md`
- `CLAUDE.md`

### Layer changed
- evidence / metadata
- renderer consumption guardrail
- pipeline family dispatch
- regression tests
- shared state

### Validation run
- `./.venv/bin/python -m py_compile app/services/poster2/renderer.py app/services/poster2/pipeline.py tests/poster2/test_pipeline.py`
  - pass
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TemplateBBackendGenerationFix or test_template_a_regression_path_remains_unchanged'`
  - `15 passed, 266 deselected`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py`
  - `6 passed`

### Remaining risks
- `template_b_parity_review` is still part of the API/schema surface; this PR keeps it empty for Family A rather than removing the response field entirely
- Family A visible-truth evidence is now family-scoped, but AR2 still needs to verify A’s Puppeteer material/selector routing is independently clean end-to-end
- anti-crossline repo rules and stronger family routing gates still need the dedicated follow-up PRs

## PR-AR2 — Family-aware renderer/material isolation

### Root rules followed
- contract-first
- family routing must be explicit at renderer consumption boundaries
- no Family A geometry/header/bottom/annotation baseline changes
- no Template B five-region geometry changes
- no beautification used to mask routing drift

### Problem reproduced
- Family A and Family B were already loading different template files, but Puppeteer HTML/material assembly still ran through one mixed `_build_html(...)` path gated by `is_template_b`
- that meant one builder still owned both A bottom/title-band/gallery semantics and B top-copy/materials/description semantics, which kept the renderer consumption boundary vulnerable to future crossline regressions

### Root cause found
- HTML material assembly and asset-url preparation were sharing semantics instead of only sharing tools
- renderer family routing was implicit in local `if is_template_b` branches inside one builder, rather than explicit family-scoped dispatch with separate A/B material assembly surfaces

### Files changed
- `app/services/poster2/renderer.py`
- `tests/poster2/test_renderer.py`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed
- renderer consumption
- family-aware asset/material routing
- renderer routing regression tests

### Validation run
- `./.venv/bin/python -m py_compile app/services/poster2/renderer.py tests/poster2/test_renderer.py tests/poster2/test_pipeline.py`
  - pass
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'TestStructuredScenarioLayer or TestHeaderAndTitleBandLayoutControl or FamilyAwareStructuredHtmlRouting'`
  - `26 passed, 83 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TemplateBBackendGenerationFix or test_template_a_regression_path_remains_unchanged'`
  - `15 passed, 266 deselected`

### Remaining risks
- this PR hardens family-scoped render-material dispatch and HTML routing, but it does not yet re-baseline fresh Family A live Chromium artifacts
- formal anti-crossline repo rules and broader family routing gates still belong in the next rules-and-test PR

## PR-AR3 — Family anti-crossline rules + test gates

### Root rules followed
- contract-first
- family branch must be explicit at every boundary
- shared code may share tools, not semantics
- README remained index-only and only changed to register a new formal document

### Problem reproduced
- isolation repair existed in code, but the repo still lacked a formal family-isolation baseline and broad regression gates
- without whitelist/routing tests and a formal rule document, future PRs could reintroduce cross-family evidence or renderer drift without an explicit stop sign

### Root cause found
- anti-crossline guidance was implicit in recent PR language, not encoded as a formal architecture rule and test gate set
- family routing tests existed only for the exact bugs just fixed, not yet as a durable engineering baseline

### Files changed
- `docs/poster2/family_isolation_rules_v1.md`
- `docs/poster2/README.md`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_renderer.py`
- `tests/test_frontend_docs_sync.py`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed
- formal architecture guidance
- manifest whitelist regression tests
- renderer family routing tests
- docs/readme index coverage

### Validation run
- `./.venv/bin/python -m py_compile tests/poster2/test_pipeline.py tests/poster2/test_renderer.py tests/test_frontend_docs_sync.py`
  - pass
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TemplateBBackendGenerationFix or test_template_a_regression_path_remains_unchanged'`
  - `16 passed, 266 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'FamilyAwareStructuredHtmlRouting or TestStructuredScenarioLayer or TestHeaderAndTitleBandLayoutControl'`
  - `28 passed, 83 deselected`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
  - pass

### Remaining risks
- the API/schema surface still keeps `template_b_parity_review` for compatibility, so Family A protection remains “empty field + family-scoped content” rather than response-field removal
- Family A re-baseline artifacts and canonical runtime note still belong in the next PR

## PR-AR4 — Family A re-baseline

### Root rules followed
- contract-first
- Family A frozen behavior truth preserved
- Family A rebaseline recorded after isolation repair, not before
- README remained index-only; shared-state update stayed in `CLAUDE.md`

### Problem reproduced
- after AR1/AR2/AR3, Family A isolation was repaired, but the repo still lacked a formal current-good Family A runtime note, accepted output-key fixture, and deterministic smoke anchors for future freeze-gate work

### Root cause found
- Family A “current good” state still lived only in tests and branch knowledge, not as a named rebaseline artifact set

### Files changed
- `tests/poster2/fixtures/family_a_runtime_rebaseline_smoke.json`
- `tests/poster2/fixtures/family_a_visual_smoke.json`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_renderer.py`
- `tests/test_frontend_docs_sync.py`
- `docs/poster2/template_a_isolation_rebaseline_status_v1.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `CLAUDE.md`

### Layer changed
- Family A runtime baseline fixtures
- deterministic visual/runtime smoke regression
- formal baseline documentation
- shared state

### Validation run
- `./.venv/bin/python -m py_compile tests/poster2/test_pipeline.py tests/poster2/test_renderer.py tests/test_frontend_docs_sync.py`
  - pass
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'family_a_runtime_rebaseline_matches_fixture or test_template_a_regression_path_remains_unchanged or test_template_a_visible_truth_keys_match_family_a_whitelist'`
  - `3 passed, 280 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'FamilyAVisualRebaseline or FamilyAwareStructuredHtmlRouting'`
  - `5 passed, 107 deselected`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
  - `6 passed`

### Remaining risks
- the deterministic visual smoke uses local fallback fonts in this workspace, so future font-install changes may require fixture refresh
- no fresh live Chromium artifact bundle was stored in-repo; this rebaseline uses deterministic smoke fixtures plus repaired routing/tests as the acceptance anchor

## PR-TA-R1 — Template A renderer/material parity repair

### Read state
- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/template_dual_v2_architecture_business_definition.md`
- `docs/poster2/template_dual_v2_structural_rebuild_baseline_v1.md`
- `docs/poster2/product_region_annotation_contract_status_v1.md`
- `docs/poster2/bottom_behavior_contract_status_v1.md`
- `docs/poster2/beautification_layer_plan_v1.md`
- `docs/poster2/external_reference_poster_design_review_and_migration_v1.md`

### Scope
- Template A repair only
- repair Family A renderer/material parity without changing frozen A contract/control truth
- no Template B expansion
- no beautification reopen

### Root cause
- current Family A structured HTML builder localized `product` and `product_secondary` against a pseudo region root
- Template A product slots are already authored in poster-root absolute coordinates, so this extra localization broke image/material parity while leaving resolver truth intact

### Files changed
- `app/services/poster2/renderer.py`
- `tests/poster2/test_renderer.py`

### Layer changed
- renderer consumption
- Family A structured HTML parity regression coverage

### Validation run
- `./.venv/bin/python -m py_compile app/services/poster2/renderer.py tests/poster2/test_renderer.py`
  - pass
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'FamilyAwareStructuredHtmlRouting or FamilyAVisualRebaseline'`
  - pass

### Remaining risks
- this repaired the concrete Family A product slot drift in structured HTML, but does not by itself prove a fresh live Chromium artifact bundle
- Family A route/output cleanup still needed to remove B-family residue from the response surface

### Exact acceptance
- Template A product slot is consumed in absolute Family A coordinates again
- secondary/supporting product slot remains product-owned and family-correct
- no Template B geometry or behavior was touched

## PR-TA-R2 — Template A family output cleanup

### Read state
- reused the same Template A repair read set from PR-TA-R1

### Scope
- remove B-family parity residue from Template A payload/output surface
- keep Family A/TB behavior and quality-guard truth otherwise unchanged

### Root cause
- `template_b_parity_review` was still modeled as an always-present dict field, so Family A responses could carry an empty B-family residue even after family filtering

### Files changed
- `app/services/poster2/contracts.py`
- `app/schemas/poster2.py`
- `app/services/poster2/pipeline.py`
- `app/main.py`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_api.py`

### Layer changed
- manifest/output schema
- family-aware parity dispatch
- API response shaping
- Family A residue regression tests

### Validation run
- `./.venv/bin/python -m py_compile app/services/poster2/contracts.py app/schemas/poster2.py app/services/poster2/pipeline.py app/main.py tests/poster2/test_pipeline.py tests/poster2/test_api.py`
  - pass
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'test_template_a_payload_filters_out_template_b_visible_truth_and_parity_keys or test_family_a_runtime_rebaseline_matches_fixture or test_template_a_regression_path_remains_unchanged'`
  - `3 passed, 280 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py -k 'test_generate_poster_v2_route_is_backward_compatible'`
  - `1 passed, 26 deselected`

### Remaining risks
- API output is now clean for Template A, but broader live render revalidation still depends on a fresh canonical sample run
- Stage2/backend diagnostics still depend on the existing Family A evidence schema; this PR did not reopen those surfaces

### Exact acceptance
- `template_dual_v2` payload no longer carries `template_b_parity_review`
- Family A visible-truth output remains family-scoped
- Template B parity path remains available only on Family B

## PR-TA-R3 — Template A re-baseline refresh

### Read state
- reused the same Template A repair baseline and Family A fixtures from the prior rebaseline pass

### Scope
- refresh deterministic Family A smoke anchor after the renderer/material parity repair
- keep A frozen contract/control truth unchanged

### Root cause
- structured HTML changed intentionally as part of the Family A parity repair, so the stored deterministic smoke hash needed to be rebaselined to the repaired A shell

### Files changed
- `tests/poster2/fixtures/family_a_visual_smoke.json`
- `tests/poster2/test_renderer.py`
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed
- deterministic A smoke baseline
- shared state
- execution log

### Validation run
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'FamilyAwareStructuredHtmlRouting or FamilyAVisualRebaseline'`
  - pass

### Remaining risks
- no fresh live Chromium output artifact was committed; the rebaseline remains deterministic-test anchored
- README index was unchanged because no new formal document path was introduced in this repair-only pass

### Exact acceptance
- Family A deterministic structured HTML smoke now matches the repaired parity path
- shared state reflects `Template A repair only` as the temporary priority override

## PR-A0 — Template A re-baseline freeze

### Read state
- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/template_dual_v2_architecture_business_definition.md`
- `docs/poster2/template_dual_v2_structural_rebuild_baseline_v1.md`
- `docs/poster2/product_region_annotation_contract_status_v1.md`
- `docs/poster2/bottom_behavior_contract_status_v1.md`
- `docs/poster2/beautification_layer_plan_v1.md`
- `docs/poster2/external_reference_poster_design_review_and_migration_v1.md`

### Scope
- freeze the repaired Template A runtime before abstraction
- record canonical output keys and golden matrix
- keep A contract/control truth unchanged

### Root cause
- Template A had a repaired runtime but no explicit accepted output surface for the next abstraction step
- the branch needed a family-scoped baseline that operators and tests could anchor to before any freeze work

### Files changed
- `app/services/poster2/family_a_runtime.py`
- `app/services/poster2/pipeline.py`
- `app/services/poster2/template_behavior.py`
- `tests/poster2/fixtures/family_a_accepted_output_keys.json`
- `tests/poster2/fixtures/family_a_golden_sample_matrix.json`
- `tests/poster2/test_pipeline.py`
- `docs/poster2/template_a_rebaseline_status_v1.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed
- Family A baseline artifacts
- family-scoped structure/control abstraction entry points
- canonical whitelist and golden-matrix regression coverage

### Validation run
- `./.venv/bin/python -m py_compile app/services/poster2/family_a_runtime.py app/services/poster2/pipeline.py app/services/poster2/template_behavior.py tests/poster2/test_pipeline.py`
  - pass
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'family_a_runtime_rebaseline_matches_fixture or accepted_output_keys or family_control_surface or geometry_evidence_surfaces_family_structure_entry or golden_sample_matrix'`
  - `5 passed, 282 deselected`

### Remaining risks
- the baseline is deterministic-fixture anchored; no fresh live Chromium artifact bundle was stored in this step
- the broader full-file `tests/poster2/test_pipeline.py` suite still contains pre-existing bottom-related failures outside this A-only scope

### Exact acceptance
- Template A canonical output/evidence keys are frozen
- Family A structure/control entry points are explicit and family-scoped
- no Template B residue appears in the accepted Template A baseline surface

## PR-A4 — Template A beautification freeze

### Read state
- reused the same Template A baseline and freeze-plan read set from PR-A0

### Scope
- complete a bounded Family A beauty freeze on top of the repaired runtime
- keep geometry, ownership, and behavior unchanged

### Root cause
- Family A had a repaired runtime and explicit abstraction entry points, but the frozen A visual pack was still defined by older token families and incomplete token consumption across Puppeteer/Pillow paths

### Files changed
- `app/templates/specs/template_dual_v2.json`
- `app/services/poster2/template_behavior.py`
- `app/services/poster2/renderer.py`
- `app/templates_html/template_dual_v2.css`
- `tests/poster2/fixtures/family_a_visual_smoke.json`
- `docs/poster2/template_a_beautification_freeze_status_v1.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `CLAUDE.md`

### Layer changed
- Family A beauty-token freeze pack
- Puppeteer shell/text token consumption
- Pillow shell-surface consumption
- deterministic visual smoke rebaseline

### Validation run
- `./.venv/bin/python -m py_compile app/services/poster2/renderer.py app/templates/specs/template_dual_v2.json tests/poster2/test_renderer.py`
  - pass
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'FamilyAVisualRebaseline or test_template_a_html_keeps_product_slots_in_absolute_product_region_coordinates'`
  - `2 passed, 111 deselected`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py`
  - `6 passed`

### Remaining risks
- no fresh live Chromium artifact bundle was committed; the freeze is anchored by deterministic Pillow/structured HTML smoke
- the full `tests/poster2/test_renderer.py` and `tests/poster2/test_pipeline.py` files still include pre-existing failures outside this bounded Template A freeze scope

### Exact acceptance
- Template A now resolves to a frozen Family A beauty pack without changing geometry or behavior
- Puppeteer and Pillow both recognize the new Family A shell/text token family
- Template B remained untouched during the A-only freeze pass

## PR-A4A — Template A live acceptance note

### Scope
- one fresh local Chromium acceptance run for the frozen Family A baseline
- no contract/control/geometry changes
- evidence only

### Runtime command shape
- local `PosterPipeline` run with real `PuppeteerStructuredRenderer`
- mocked background builder and in-memory assets
- artifact bundle written to `/tmp/poster2-family-a-live-acceptance-afea38cb`

### Artifact bundle
- artifact root: `/tmp/poster2-family-a-live-acceptance-afea38cb`
- final image: `/tmp/poster2-family-a-live-acceptance-afea38cb/poster2__final__831ac09f-3bd7-43a7-ba93-c21d4c43ffc1.png`
- foreground image: `/tmp/poster2-family-a-live-acceptance-afea38cb/poster2__fg__831ac09f-3bd7-43a7-ba93-c21d4c43ffc1.png`
- metadata: `/tmp/poster2-family-a-live-acceptance-afea38cb/poster2__debug__metadata__831ac09f-3bd7-43a7-ba93-c21d4c43ffc1.json`
- summary: `/tmp/poster2-family-a-live-acceptance-afea38cb/acceptance_summary.json`

### Hashes
- final hash: `43dfd8f09ef5c771a2adf48c8f1ea663d8e9ba5002eddf561f1ce7eee812255c`
- foreground hash: `0b383ef6cfc56eb2cbc166458ff28457c73f5e0a92967a60c77174d75f75f7c1`
- metadata sha256: `7ef9854afc08802777d000bb2d986dbacc006c55d611aa1ad3e0fec32a7b933b`

### Acceptance result
- `render_engine_used = puppeteer`
- `degraded = false`
- `structure_complete = true`
- `deliverable = true`
- behavior modes remained frozen:
  - `hero_mode = scenario_cover_product_contain`
  - `feature_mode = product_anchor_callouts`
  - `product_annotation_mode = product_anchor_callouts`
  - `header_mode = identity_left_agent_right`
  - `bottom_mode = title_gallery_split`
  - `gallery_mode = strip_local_visible_only`
  - `product_layout_mode = single_primary`
  - `secondary_product_mode = inset_hidden_no_reserve`

### Fixture / golden-matrix comparison
- matches `family_a_runtime_rebaseline_smoke.json` expected engine/degraded/structure/deliverable truth
- matches `family_a_accepted_output_keys.json` Family A region whitelist
- no Template B residue present; `template_b_parity_review` absent
- live sample corresponds to golden-matrix case `annotation_triplet_gallery_triplet_subtitle_present`
- title/subtitle ownership remains `title_band_region`

### Remaining limits
- this acceptance run is local and artifact-rooted under `/tmp`, not persisted to remote storage
- full `tests/poster2/test_pipeline.py` still contains the existing bottom/text-only failures outside this A-freeze scope

## Template A narrow follow-up — bottom support copy alignment fix

### Read state
- Template A freeze and live acceptance were already complete before this task
- scope stayed on `template_dual_v2` only
- no Template B, geometry, ownership, or bottom-family redesign work was reopened

### Problem reproduced
- Stage2 diagnostics showed `bottom_mode = text_only_expanded` with subtitle/support copy present
- `gallery_strip` was correctly collapsed by mode
- final Template A structured renderer still kept subtitle visibility logic intact
- but the Stage2 preview continued to render the old static bottom/gallery composition, so support copy was missing or visually misaligned

### Root cause
- the legacy Stage2 preview path did not consume backend `bottom_contract_review` / `template_behavior.bottom_policy` for Template A
- preview bottom rendering stayed hard-wired to gallery-era assumptions:
  - gallery row stayed visible
  - gallery subtitle node stayed active
  - bottom support copy did not key off `subtitle_slot.rendered`
- this was a preview/render-consumption mismatch, not a resolver or ownership failure

### Files changed
- `frontend/app.js`
- `frontend/styles.css`
- `docs/app.js`
- `docs/styles.css`
- `tests/poster2/test_renderer.py`
- `tests/test_stage2_guard_diagnostics_surface.py`

### Layer changed
- Template A Stage2 preview render-consumption only
- preview/docs mirror alignment
- focused regression coverage for `text_only_expanded`

### Validation run
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py`
  - `114 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'bottom or family_a or accepted_output_keys'`
  - existing failures remain in the repo's older Template A bottom/text-only assertions; no new failure signature from this preview-only fix
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py`
  - `7 passed`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
  - `6 passed`

### Remaining risks
- this fix is intentionally local to Stage2 preview consumption; it does not attempt to resolve the older `tests/poster2/test_pipeline.py` bottom/text-only backlog
- no fresh Chromium artifact bundle was generated because the final render path was already structurally correct and unchanged in this task

### Exact acceptance
- when Template A uses `text_only_expanded` and support copy is present, Stage2 preview now keeps title + subtitle/support copy visible and aligned as a centered text stack
- gallery strip stays collapsed by mode in preview
- preview uses the same backend bottom truth already shown in diagnostics
- Template B remained untouched

## Template A narrow follow-up — title_gallery_split support-copy field mapping alignment

### Read state
- this was inserted after the preview alignment fix and before any new freeze-sequence work
- scope remained Template A only
- no geometry, ownership, bottom-mode structure, or Template B path was reopened

### Problem reproduced
- UI copy remained correct as `Bottom Support Copy`
- backend canonical field stayed `subtitle`
- but the Stage1 -> Stage2 -> preview state chain still carried a legacy `tagline` alias in parallel
- this made Template A bottom support copy mapping harder to reason about and risked misalignment between preview state and `requested_subtitle_text` / `sanitized_subtitle_text`

### Root cause
- front-end state hydration and preview state still treated `subtitle` and `tagline` as near-equivalent inputs
- Template A preview/runtime orchestration had no explicit helper that says "bottom support copy is canonically `subtitle`; `tagline` is legacy fallback only"
- Template A pipeline normalization also still ran support copy through the generic marketing-subtitle sanitizer, which stripped valid trailing punctuation in this bottom-owned field

### Files changed
- `frontend/app.js`
- `docs/app.js`
- `app/services/poster2/pipeline.py`
- `tests/poster2/test_pipeline.py`
- `tests/test_stage2_guard_diagnostics_surface.py`

### Layer changed
- Template A field mapping / normalization alignment
- narrow backend subtitle normalization for A bottom support copy
- regression coverage

### Validation run
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'title_gallery_split_preserves_support_copy_in_requested_and_sanitized_subtitle_fields or family_a_runtime_rebaseline_matches_fixture or accepted_output_keys'`
  - `3 passed, 285 deselected`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py`
  - `8 passed`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
  - `6 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py`
  - `114 passed`

### Remaining risks
- this does not attempt to clean up every historical `tagline` alias outside the bounded Template A poster2 path
- the broader existing bottom/text-only pipeline backlog remains separate from this support-copy mapping closure

### Exact acceptance
- Template A keeps `Bottom Support Copy` as the UI label while `subtitle` remains the canonical backend field
- Stage1 -> Stage2 -> preview -> generate now prefer canonical `subtitle` truth for Template A bottom support copy
- `title_gallery_split` with support copy present preserves `requested_subtitle_text` and `sanitized_subtitle_text`
- `subtitle_slot` remains rendered instead of being mis-collapsed
