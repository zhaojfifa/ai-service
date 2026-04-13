# Current Branch Execution Log v1

## Entry — PR-OP2-v2: Stage1 combined preview + staged copy suggestions

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-13

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- then task-relevant frozen-state docs:
  - `docs/poster2/poster_generation_product_design_baseline_v1.md`
  - `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
  - `docs/poster2/05_validation/bottom_behavior_contract_status_v1.md`
  - `docs/poster2/05_validation/bottom_mode_switch_closure_status_v1.md`
  - `docs/poster2/05_validation/product_region_annotation_contract_status_v1.md`
  - `docs/poster2/03_engineering/email_copy_optimizer_and_optional_attachment_status_v1.md`
- then minimum task files only:
  - `frontend/index.html`
  - `frontend/app.js`
  - `frontend/styles.css`
  - `docs/index.html`
  - `docs/app.js`
  - `docs/styles.css`

### Scope

- PR-OP2-v2 only
- Stage1 operator experience only
- family-aware read-only combined preview
- staged copy suggestion surface with explicit accept/apply/recover flow
- frontend/docs mirror sync
- branch execution log write-back
- no backend routing, renderer routing, Stage2 replay/result rendering, Stage3 truth, ownership, bottom contract, or request-builder change

### Root rules followed

- contract-first
- keep work on the requested layer
- preserve family isolation and do not mix Family A / Family B request lines
- do not reuse Stage2 result/replay rendering for Stage1 preview
- do not silently mutate canonical Stage2 request truth
- keep source and published mirror aligned in the same task

### Problem reproduced

- Stage1 previously had only the existing template preview / poster-style preview surface
- it did not provide a family-aware read-only combined operator summary for current inputs
- it also had no staged suggestion layer that cleanly separated:
  - raw operator input
  - suggestion
  - accepted suggestion

### Root cause found

- Stage1 had no independent read-only combined-preview model
- existing dual-poster / result preview helpers are Stage2-oriented and unsafe to reuse here because they couple to post-generate / replay semantics
- Stage1 persistence also had no dedicated accepted-suggestion layer, so any suggestion feature would have risked silently overwriting visible source fields unless a separate Stage1-only state model was introduced

### Exact Stage1 combined preview model implemented

- added a new Stage1-only combined preview section with two cards:
  - `Visual Inputs Preview`
  - `Copy Inputs Preview`
- implemented through new Stage1-only helpers in `frontend/app.js` / `docs/app.js`:
  - `buildStage1CombinedPreviewModel(...)`
  - `renderStage1CombinedPreview(...)`
- preview derives only from current Stage1 form/state data
- Family A combined preview shows only:
  - template
  - brand / logo
  - scenario image
  - primary / secondary product images
  - bottom thumbnails
  - Product Series
  - title
  - Product Callouts
  - Bottom Support Copy
- Family B combined preview shows only:
  - template
  - brand / logo
  - primary / secondary product images
  - materials / detail images
  - Product Series
  - SKU
  - title
  - subtitle
  - description
- the new Stage1 preview path does not call:
  - `renderPosterResult()`
  - `buildTemplateAPreviewModel(...)`
  - `renderDualPosterPreview(...)`
  - `buildDualPosterData(...)`

### Exact staged AI suggestion behavior implemented

- added a separate Stage1 suggestion panel with explicit state separation:
  - raw input
  - suggestion layer
  - accepted layer
- implemented through new Stage1-only helpers in `frontend/app.js` / `docs/app.js`:
  - `buildStage1SuggestionDraft(...)`
  - `renderStage1SuggestionPanel(...)`
  - `normaliseStage1SuggestionState(...)`
- implemented as frontend-only staged suggestion plumbing in this PR:
  - no backend endpoint added
  - no canonical Stage2 request truth change
- family-specific suggestion targets:
  - Family A:
    - `title`
    - `product_callouts`
    - `bottom_support_copy`
    - `email_subject`
    - `email_opening`
  - Family B:
    - `title`
    - `subtitle`
    - `description_summary`
    - `email_subject`
    - `email_opening`
- operator flow:
  - generate suggestion
  - check which targets to accept
  - accept checked suggestions into Stage1 accepted layer only
  - optionally apply accepted poster-copy targets back to visible Stage1 inputs by explicit button
  - optionally restore the pre-apply raw snapshot
  - optionally clear accepted layer
- email subject/opening suggestions remain staged-only in this PR; they do not silently backfill any canonical Stage1 request field
- accepted suggestion state is persisted under Stage1 storage only:
  - `staged_copy_suggestions`

### Files changed

- `frontend/index.html`
- `frontend/app.js`
- `frontend/styles.css`
- `docs/index.html`
- `docs/app.js`
- `docs/styles.css`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage1 frontend operator surface only
- frontend/docs publish mirror only
- branch execution/state log only

### Focused validation run

- syntax:
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
- mirror sync:
  - `bash scripts/sync_frontend_to_docs.sh`
  - `bash scripts/check_frontend_docs_sync.sh`
  - direct no-index diffs between `frontend/` and `docs/` for:
    - `index.html`
    - `app.js`
    - `styles.css`
- existing sync/static test:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
- source inspection for forbidden Stage1 preview reuse:
  - `rg -n "buildStage1CombinedPreviewModel|renderStage1CombinedPreview|renderStage1SuggestionPanel|buildStage1SuggestionDraft|renderPosterResult|buildTemplateAPreviewModel|renderDualPosterPreview|buildDualPosterData" frontend/app.js`

### Focused validation result

- `frontend/app.js` syntax passed
- `docs/app.js` syntax passed
- frontend/docs publish mirror check passed after sync
- `tests/test_frontend_docs_sync.py` passed: `8 passed`
- source inspection confirms the new Stage1 combined preview path is isolated to:
  - `buildStage1CombinedPreviewModel(...)`
  - `renderStage1CombinedPreview(...)`
- no backend file or route changed in this pass

### Remaining risks

- this PR implements frontend-only staged suggestion drafting rather than a backend-backed suggestion endpoint, so suggestion quality is deterministic/local in the current pass
- email subject / opening suggestions are staged for operator review only in this PR and are not yet wired into later-stage backend-owned email truth
- focused validation covered syntax, mirror sync, and source-path isolation; no browser automation run was added in this pass

### Exact acceptance state

- Stage1 now shows a family-aware read-only combined preview
- Stage1 combined preview is separate from Stage2 result/replay rendering
- staged suggestions remain distinct from raw input and accepted state
- accepted suggestions require explicit operator action
- applying accepted suggestions back into visible inputs requires an explicit operator action
- original visible Stage1 copy is recoverable through the stored pre-apply snapshot
- Family A and Family B preview content remains isolated by family
- no Stage2 request/routing/runtime truth changed
- frontend/docs mirror is aligned
- `CLAUDE.md` was not updated by this task

## Entry — P0 SVG preview-asset hotfix from repo-visible reference

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-13

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`

### Scope

- selector preview SVG asset replacement only
- mirror replacement to `docs/templates/` only
- focused asset validation only
- branch execution log write-back
- no registry, HTML, JS, CSS, request builder, renderer, ownership, Stage2, Stage3, or backend change

### Root rules followed

- contract-first
- keep work on the requested layer
- follow the frozen selector-preview spec and repo-visible reference only
- no runtime truth change
- keep source and published mirror copies aligned in the same task

### Problem reproduced

- the current local selector preview SVGs still needed to be redrawn against the repo-visible reference image rather than the prior abstract / structural card language

### Root cause found

- selector preview correction required an asset-only redraw using the reference file on `origin/main`:
  - `frontend/assets/selector_preview_reference.png`
- no surrounding registry or UI/runtime change was needed

### Exact selector preview asset decision

- redrew only:
  - `frontend/templates/template_marketing_poster_preview.svg`
  - `frontend/templates/template_product_sheet_preview.svg`
- mirrored the same redraw to:
  - `docs/templates/template_marketing_poster_preview.svg`
  - `docs/templates/template_product_sheet_preview.svg`
- matched the repo-visible reference language:
  - pale gray page background
  - warm off-white rounded card
  - pale pink header/support bands
  - restrained coral accent
  - low-detail rounded structural blocks only
- template cue kept minimal:
  - `Marketing Poster`: top band, hero block, selling-point list, bottom support strip
  - `Product Sheet`: banner, SKU/top-copy block, main product block, detail strip, lower info block

### Files changed

- `frontend/templates/template_marketing_poster_preview.svg`
- `frontend/templates/template_product_sheet_preview.svg`
- `docs/templates/template_marketing_poster_preview.svg`
- `docs/templates/template_product_sheet_preview.svg`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- selector preview SVG assets only
- publish mirror alignment
- branch execution/state log

### Focused validation run

- mirror equality:
  - `cmp -s frontend/templates/template_marketing_poster_preview.svg docs/templates/template_marketing_poster_preview.svg`
  - `cmp -s frontend/templates/template_product_sheet_preview.svg docs/templates/template_product_sheet_preview.svg`
- asset fingerprint:
  - `shasum frontend/templates/template_marketing_poster_preview.svg frontend/templates/template_product_sheet_preview.svg docs/templates/template_marketing_poster_preview.svg docs/templates/template_product_sheet_preview.svg`
- published URL probe before publish:
  - `curl -sS -I -m 20 https://zhaojfifa.github.io/ai-service/templates/template_marketing_poster_preview.svg`
  - `curl -sS -I -m 20 https://zhaojfifa.github.io/ai-service/templates/template_product_sheet_preview.svg`
  - direct content fetch of both published SVG URLs

### Focused validation result

- frontend/docs mirror checks passed
- matched SHA values:
  - marketing preview: `6983b2b28c4be135b85170743be60dca10f07208`
  - product sheet preview: `7daed8e69814df02c919c156d8516a56d4bb6c76`
- published URL content fetch succeeded, but still returned the previous remotely published SVG content at the time of this local hotfix pass
- therefore:
  - local asset replacement is complete
  - mirror replacement is complete
  - published URL state had not yet advanced to this local hotfix during this validation snapshot

### Remaining risks

- published URL validation here reflects pre-push / pre-publish remote state, so the remote SVGs still showed the older published asset at check time
- `CLAUDE.md` had an unrelated local shared-state modification already present in the workspace and was not changed further by this task

### Exact acceptance state

- only the four requested SVG preview files were replaced
- frontend/docs selector preview assets are identical
- no registry mapping changed
- no UI layout or runtime truth changed
- remote published SVG URLs still reflected older content at validation time because this task had not yet been published when checked
- `CLAUDE.md` was not updated further by this task

## Entry — Frozen spec: selector preview SVG design spec v1

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-13

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`

### Scope

- shared-state freeze only
- selector preview SVG design-spec freeze only
- branch execution log write-back
- no asset, registry, UI, runtime, request, renderer, ownership, Stage2, Stage3, or backend change

### Root rules followed

- contract-first
- keep work on the requested layer
- no implementation change without explicit request
- record shared state separately from rules and separately from index docs

### Problem reproduced

- future selector preview asset tasks needed a frozen style/spec baseline so asset changes do not drift by interpretation across passes

### Root cause found

- selector preview expectations had been restated across multiple passes, but not yet frozen as a single explicit shared-state rule for future work

### Frozen selector preview SVG design spec v1

- flat, simple, minimal, low-detail, low-contrast selector-card style
- not wireframe
- not skeleton/loading style
- not abstract logic diagram
- not final poster render
- consistent fidelity, density, color system, and rounded-card language across templates
- maximum 2 visual hierarchy levels
- about 6-10 major structural blocks only
- only light gray base, pale accent, and one restrained dark support tone

### Frozen template implication limits

- `Marketing Poster` preview may only imply:
  - top area
  - hero/main visual area
  - selling-point emphasis area
  - bottom support area
- `Product Sheet` preview may only imply:
  - banner
  - SKU/top-copy area
  - main product area
  - detail/material strip
  - lower description/info area

### Future task default from this freeze

- draw only against this frozen spec
- if a requested preview cannot be confidently drawn within this spec, stop and ask before proceeding
- selector preview tasks default to SVG asset changes only unless explicitly requested otherwise
- mirror `frontend/templates/` and `docs/templates/`
- do not touch registry, app.js, runtime logic, request builder, renderer, ownership, Stage2, Stage3, or backend schema unless explicitly requested

### Files changed

- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- shared state only
- branch execution/state log only

### Validation run

- no code/runtime validation required; this pass records frozen design-state only

### Remaining risks

- future preview work must follow this spec exactly; if a request conflicts with it, clarification should be requested before drawing

### Exact acceptance state

- selector preview SVG design spec v1 is now frozen as shared state
- future selector preview asset work has an explicit non-drifting baseline
- `docs/poster2/README.md` remained index-only
- `AGENTS.md` remained rules-only

## Entry — SVG asset hotfix: selector-card preview refresh

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-13

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- task-relevant asset files only:
  - `frontend/templates/template_marketing_poster_preview.svg`
  - `frontend/templates/template_product_sheet_preview.svg`
  - `docs/templates/template_marketing_poster_preview.svg`
  - `docs/templates/template_product_sheet_preview.svg`

### Scope

- SVG asset hotfix only
- selector preview asset replacement only
- docs mirror sync only
- focused mirror validation only
- branch execution log write-back
- no registry, HTML, JS, CSS, request builder, renderer, ownership, Stage2, Stage3, or backend work

### Root rules followed

- contract-first
- keep work on the requested layer
- no redesign outside selector preview assets
- no runtime truth or request truth change
- keep source and published copies aligned in the same task

### Problem reproduced

- selector previews needed an asset-only refresh to stay in a simple, minimal, clean selector-card mode rather than drifting toward abstract / schematic reading

### Root cause found

- current fix path only required asset-level tuning; no surrounding registry or UI logic change was needed

### Exact selector preview asset decision

- replaced only these two source assets:
  - `frontend/templates/template_marketing_poster_preview.svg`
  - `frontend/templates/template_product_sheet_preview.svg`
- mirrored the exact same replacements to:
  - `docs/templates/template_marketing_poster_preview.svg`
  - `docs/templates/template_product_sheet_preview.svg`
- kept the same visual direction as the current minimal selector-card baseline, but reduced detail density further:
  - `Marketing Poster` reads as a simple marketing card with top band, hero stage, callout emphasis, and bottom support strip
  - `Product Sheet` reads as a simple catalog card with top banner, SKU block, product hero, detail strip, and lower description block

### Files changed

- `frontend/templates/template_marketing_poster_preview.svg`
- `frontend/templates/template_product_sheet_preview.svg`
- `docs/templates/template_marketing_poster_preview.svg`
- `docs/templates/template_product_sheet_preview.svg`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- selector preview assets only
- publish mirror alignment
- branch execution/state log

### Focused validation run

- `cmp -s frontend/templates/template_marketing_poster_preview.svg docs/templates/template_marketing_poster_preview.svg`
- `cmp -s frontend/templates/template_product_sheet_preview.svg docs/templates/template_product_sheet_preview.svg`
- `shasum frontend/templates/template_marketing_poster_preview.svg frontend/templates/template_product_sheet_preview.svg docs/templates/template_marketing_poster_preview.svg docs/templates/template_product_sheet_preview.svg`

### Focused validation result

- marketing preview mirror check passed
- product sheet preview mirror check passed
- matched SHA values:
  - marketing preview: `7acc68562683ae4fa55a8c947bee31dafb910fd7`
  - product sheet preview: `0b547a7b402ca2a150b1c6eef63370f6238024b2`

### Remaining risks

- this pass validated mirror equality only, by request; it did not perform browser/runtime verification

### Exact acceptance state

- only the two requested selector preview SVG assets were replaced
- docs mirror copies match the frontend assets exactly
- no registry mapping changed
- no UI layout or runtime truth changed
- `CLAUDE.md` left unchanged because this pass introduced no new shared-state fact beyond branch-local execution state

## Entry — Hotfix verification: selector rollback and bottom flow no-op

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-13

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- task-relevant implementation files re-checked:
  - `frontend/index.html`
  - `frontend/app.js`
  - `frontend/styles.css`
  - `frontend/templates/registry.json`
  - `frontend/templates/template_marketing_poster_preview.svg`
  - `frontend/templates/template_product_sheet_preview.svg`
  - `docs/index.html`
  - `docs/app.js`
  - `docs/styles.css`
  - `docs/templates/registry.json`
  - `docs/templates/template_marketing_poster_preview.svg`
  - `docs/templates/template_product_sheet_preview.svg`

### Scope

- hotfix verification only
- no-op confirmation against current selector-preview and bottom-placement state
- focused validation only
- branch execution log write-back
- no request builder, backend schema, renderer behavior, routing, Stage2, Stage3, or ownership work

### Root rules followed

- contract-first
- keep work on the requested layer
- no redesign
- preserve runtime truth, request construction, renderer truth, and ownership truth
- keep source and published copies aligned

### Problem reproduced

- hotfix request asked to ensure selector previews are rolled back from abstract / wireframe mode and that `Bottom Support Copy` is fully in the `Bottom Area` reading flow

### Root cause found

- no new defect remained in the current working tree
- the requested rollback and field-placement correction were already present from the latest selector-preview correction pass

### Exact selector preview hotfix state

- `Marketing Poster` currently uses `template_marketing_poster_preview.svg`
- `Product Sheet` currently uses `template_product_sheet_preview.svg`
- both previews are already simple/minimal card-style SVGs rather than abstract wireframes
- internal ids remain unchanged:
  - `template_dual`
  - `template_product_sheet_v1`

### Exact Bottom Support Copy placement state

- `Bottom Support Copy` remains inside `s1-bottom-thumbs` under `Bottom Area`
- `Product Callouts` remains inside `s1-core-assets` under `Main Product`
- static order remains:
  - `Product Callouts (optional, up to 3)`
  - `id="s1-bottom-thumbs"`
  - `Bottom Support Copy (optional)`

### Files changed

- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- branch execution/state log only

### Focused validation run

- `bash scripts/check_frontend_docs_sync.sh`
- `node --check frontend/app.js`
- `node --check docs/app.js`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
- focused static assertions:
  - selector registry count = `2`
  - selector ids remain `template_dual` and `template_product_sheet_v1`
  - preview assets remain:
    - `template_marketing_poster_preview.svg`
    - `template_product_sheet_preview.svg`
  - registry descriptions remain minimal-preview descriptions
  - bottom-field order check remains true

### Remaining risks

- validation here is static and mirror-focused only; no live browser screenshot was captured in this hotfix verification pass

### Exact acceptance state

- exactly two operator-facing templates remain
- both selector previews already read as simple, minimal, and visually comparable
- Marketing Poster remains a simple marketing-card preview
- Product Sheet remains a simple catalog-card preview
- Bottom Support Copy is already fully in the Bottom Area reading flow
- Product Callouts remains in Main Product only
- no runtime truth changed
- `frontend/` and `docs/` remain aligned
- `CLAUDE.md` left unchanged because no new shared-state fact was introduced

## Entry — PR-OP1C-REV: minimal selector preview correction and bottom flow separation

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-13

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- latest completed branch state entries re-read in this log:
  - `PR-OP1A`
  - `PR-OP1B`
  - `PR-OP1C`
- task-relevant implementation files:
  - `frontend/index.html`
  - `frontend/app.js`
  - `frontend/styles.css`
  - `frontend/templates/registry.json`
  - `frontend/templates/template_marketing_poster_preview.svg`
  - `frontend/templates/template_product_sheet_preview.svg`
  - `docs/index.html`
  - `docs/app.js`
  - `docs/styles.css`
  - `docs/templates/registry.json`
  - `docs/templates/template_marketing_poster_preview.svg`
  - `docs/templates/template_product_sheet_preview.svg`

### Scope

- selector preview style correction only
- Stage1 Bottom Support Copy visual-placement clarification only
- static selector asset redraw only
- shallow Stage1 boundary / spacing / helper adjacency tuning only
- `frontend/` and `docs/` mirror alignment on touched files
- focused validation only
- branch execution log write-back
- no request builder, backend schema, renderer behavior, routing, Stage2 result/replay, or Stage3 truth work

### Root rules followed

- contract-first
- keep work on the requested layer
- preserve frozen renderer truth, request truth, ownership truth, and family routing truth
- keep Product Callouts product-owned and Bottom Support Copy bottom-owned
- use selector asset correction instead of runtime rendering changes
- keep source and published copies aligned in the same task

### Problem reproduced

- PR-OP1C corrected selector parity, but pushed the previews too far toward structure-diagram / logic-block language
- the result was more consistent than before, but still read too technical and too close to wireframe-style selector art
- Bottom Support Copy was already moved under `Bottom Area`, but the opening of that section still felt too close to the product reading flow

### Root cause found

- both selector previews used the same static-SVG mechanism, but the SVG language still emphasized bounded structural blocks over simple minimal card presentation
- the `Bottom Area` fieldset had the right ownership, but needed a clearer top-of-section boundary and lighter flow treatment so the bottom reading lane started more explicitly

### Exact selector preview correction decision

- kept both remaining selector previews as static SVG assets
- corrected both previews from structure-diagram emphasis to minimal selector-card emphasis
- normalized both previews to the same lighter comparison language:
  - soft outer background
  - restrained accent colors
  - fewer content blocks
  - lower detail density
  - similar visual weight
  - simple card-style shapes instead of wireframe-feeling schematic blocks
- preserved purpose differentiation only:
  - `Marketing Poster`: header, hero composition, marketing-copy emphasis, bottom support strip
  - `Product Sheet`: banner, SKU/top-copy block, product hero, materials/detail strip, description area
- kept internal ids and selector wiring unchanged:
  - `template_dual`
  - `template_product_sheet_v1`

### Exact Bottom Support Copy layout move

- kept `Bottom Support Copy` inside `s1-bottom-thumbs` under `Bottom Area`
- added a `bottom-area-flow` wrapper with a top divider and extra top padding so the bottom reading flow starts as its own lane
- converted the touched subsection headings / hints in the bottom block to Chinese:
  - `底部辅助文案`
  - `底部缩略图`
- kept `Product Callouts` in `s1-core-assets`
- kept the underlying field name as `subtitle`; no ownership remap or request-mapping change was made

### Files changed

- `frontend/index.html`
- `frontend/styles.css`
- `frontend/templates/registry.json`
- `frontend/templates/template_marketing_poster_preview.svg`
- `frontend/templates/template_product_sheet_preview.svg`
- `docs/index.html`
- `docs/styles.css`
- `docs/templates/registry.json`
- `docs/templates/template_marketing_poster_preview.svg`
- `docs/templates/template_product_sheet_preview.svg`
- `tests/test_frontend_docs_sync.py`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage1 operator selector presentation
- Stage1 bottom-area reading-flow presentation
- publish mirror alignment
- focused static validation
- branch execution/state log

### Focused validation run

- `bash scripts/check_frontend_docs_sync.sh`
- `node --check frontend/app.js`
- `node --check docs/app.js`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
- mirror assertions:
  - `cmp -s frontend/templates/registry.json docs/templates/registry.json`
  - `cmp -s frontend/templates/template_marketing_poster_preview.svg docs/templates/template_marketing_poster_preview.svg`
  - `cmp -s frontend/templates/template_product_sheet_preview.svg docs/templates/template_product_sheet_preview.svg`
- focused static assertions:
  - selector registry count = `2`
  - selector ids remain `template_dual` and `template_product_sheet_v1`
  - registry descriptions now read as `Minimal ... preview ...`
  - `Product Callouts` still appears before `id="s1-bottom-thumbs"`
  - `Bottom Support Copy` still appears after `id="s1-bottom-thumbs"`
  - `bottom-area-flow`, `底部辅助文案`, and `底部缩略图` are present in `frontend/index.html`

### Direct proof captured

- selector preview correction proof:
  - both selector assets were redrawn in-place as minimal SVG cards rather than structure-diagram-heavy blocks
  - registry descriptions now explicitly describe both choices as `Minimal ... preview ...`
- bottom placement proof:
  - static order check in `frontend/index.html` verified:
    - `Product Callouts (optional, up to 3)`
    - `id="s1-bottom-thumbs"`
    - `Bottom Support Copy (optional)`
  - `bottom-area-flow` wrapper now marks the start of the bottom-owned lane

### Remaining risks

- this PR again used focused static validation only; no live browser screenshot capture was attached in this workspace
- selector-card quality here is still asset-based judgment; if future operator testing asks for further tuning, it should remain a static selector-asset pass rather than a runtime render change

### Exact acceptance state

- exactly two operator-facing templates remain
- both selector previews now read as simple/minimal template options rather than abstract logic diagrams
- the two previews are comparable in fidelity level
- Product Sheet preview remains present and non-missing
- Marketing Poster preview no longer reads as underpowered or placeholder-like
- Bottom Support Copy clearly reads as bottom-owned by placement
- Product Callouts remain clearly product-owned by placement
- no request/routing/runtime truth changed
- `frontend/` and `docs/` touched files remain aligned
- `CLAUDE.md` left unchanged because this PR did not introduce a new shared-state fact beyond branch-local execution state

## Entry — PR-OP1C: selector preview parity and bottom placement clarity

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-13

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- latest completed branch state entries re-read in this log:
  - `PR-OP1A`
  - `PR-OP1B`
- poster2 baseline / architecture anchors re-read before edits:
  - `docs/poster2/poster_generation_product_design_baseline_v1.md`
  - `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
- task-relevant implementation files:
  - `frontend/index.html`
  - `frontend/app.js`
  - `frontend/styles.css`
  - `frontend/templates/registry.json`
  - `frontend/templates/template_dual_template.b64`
  - `frontend/templates/template_product_sheet_preview.svg`
  - `docs/index.html`
  - `docs/app.js`
  - `docs/styles.css`
  - `docs/templates/registry.json`
  - `docs/templates/template_product_sheet_preview.svg`

### Scope

- Stage1 operator-facing selector preview parity only
- Stage1 Bottom Support Copy placement / section-boundary clarity only
- static selector asset replacement only
- `frontend/` and `docs/` mirror alignment on touched files and selector assets
- focused validation only
- branch execution log write-back
- no request builder, backend schema, renderer behavior, routing, Stage2 result/replay, or Stage3 truth work

### Root rules followed

- contract-first
- keep work on the requested layer
- preserve frozen renderer truth, ownership truth, request construction, and routing
- keep Product Callouts product-owned and Bottom Support Copy bottom-owned
- use layout clarification rather than payload or contract remapping
- keep source and published copies aligned in the same task

### Problem reproduced

- selector comparison was still unfair because `Marketing Poster` used the older poster-like base64 preview while `Product Sheet` used a newer structure-first SVG preview
- this made operators compare apparent preview maturity instead of actual template structure
- `Bottom Support Copy` still sat inside the `Main Product` reading flow near `Product Callouts`, so the page layout kept implying shared ownership

### Root cause found

- PR-OP1A completed Product Sheet preview coverage, but `template_dual` still pointed at the old `template_dual_template.b64` selector asset
- Stage1 HTML still rendered the `subtitle` field inside the `s1-core-assets` block, so helper-copy changes alone could not fully overcome the visual ownership cue

### Exact selector preview parity decision taken

- normalized both selector previews to the same structure-oriented static SVG language
- replaced the `Marketing Poster` selector asset reference from `template_dual_template.b64` to a new static SVG:
  - `frontend/templates/template_marketing_poster_preview.svg`
  - mirrored to `docs/templates/template_marketing_poster_preview.svg`
- kept `Product Sheet` on the existing structure-first SVG preview
- kept internal ids unchanged:
  - `template_dual`
  - `template_product_sheet_v1`
- kept selector fidelity intentionally parallel:
  - same aspect ratio
  - same abstraction level
  - same neutral shell-first block language
  - same limited accent usage
- made the Marketing Poster preview show structure only:
  - header
  - scenario panel
  - hero product panel
  - callout lane
  - title block
  - bottom gallery area

### Exact Bottom Support Copy layout move

- removed `Bottom Support Copy` from the `Main Product` field grid inside `s1-core-assets`
- moved the same `subtitle` input into `s1-bottom-thumbs` under `Bottom Area`
- added a shallow `Bottom Support` subsection and a bordered `bottom-support-block` container ahead of bottom thumbnails
- kept `Product Callouts` in `Main Product`
- kept the underlying field name as `subtitle`; no ownership remap or request-mapping change was made

### Files changed

- `frontend/index.html`
- `frontend/styles.css`
- `frontend/templates/registry.json`
- `frontend/templates/template_marketing_poster_preview.svg`
- `docs/index.html`
- `docs/styles.css`
- `docs/templates/registry.json`
- `docs/templates/template_marketing_poster_preview.svg`
- `tests/test_frontend_docs_sync.py`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage1 operator selector presentation
- Stage1 field layout / section-boundary presentation
- publish mirror alignment
- focused static validation
- branch execution/state log

### Focused validation run

- `bash scripts/check_frontend_docs_sync.sh`
- `node --check frontend/app.js`
- `node --check docs/app.js`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
- mirror assertions:
  - `cmp -s frontend/templates/registry.json docs/templates/registry.json`
  - `cmp -s frontend/templates/template_marketing_poster_preview.svg docs/templates/template_marketing_poster_preview.svg`
  - `cmp -s frontend/templates/template_product_sheet_preview.svg docs/templates/template_product_sheet_preview.svg`
- focused static assertions:
  - selector registry count = `2`
  - selector ids remain `template_dual` and `template_product_sheet_v1`
  - selector previews now resolve to:
    - `template_marketing_poster_preview.svg`
    - `template_product_sheet_preview.svg`
  - `Product Callouts` still appears in `s1-core-assets`
  - `Bottom Support Copy` now appears after `id="s1-bottom-thumbs"` in `frontend/index.html`

### Static proof captured

- selector parity proof:
  - registry now maps both operator templates to SVG structure previews instead of mixing SVG with the older poster-like base64 asset
  - `frontend/templates/registry.json` preview list verified as:
    - `template_marketing_poster_preview.svg`
    - `template_product_sheet_preview.svg`
- bottom placement proof:
  - static position check in `frontend/index.html` verified ordering:
    - `s1-core-assets`
    - `Product Callouts`
    - `s1-bottom-thumbs`
    - `Bottom Support Copy`

### Remaining risks

- this PR used focused static validation only; no live browser screenshot capture was attached in this workspace
- the new Marketing Poster selector preview is intentionally structural and simplified; if later operator testing asks for even tighter parity tuning, that should stay limited to selector assets rather than runtime rendering

### Exact acceptance state

- exactly two operator-facing templates remain
- the two selector previews now use the same structure-oriented comparison language and no longer mix obviously mismatched fidelity levels
- Product Sheet preview remains present and non-missing
- Marketing Poster preview no longer reads as materially more finalized than Product Sheet
- Bottom Support Copy now reads as bottom-owned by placement under `Bottom Area`
- Product Callouts remain in `Main Product`
- no request/routing/runtime truth changed
- `frontend/` and `docs/` touched files remain aligned
- `CLAUDE.md` left unchanged because this PR did not introduce a new shared-state fact beyond branch-local execution state

## Entry — PR-OP1B: Stage1 operator input clarity

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-13

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- task-relevant implementation files:
  - `frontend/index.html`
  - `frontend/app.js`
  - `frontend/styles.css`
  - `docs/index.html`
  - `docs/app.js`
  - `docs/styles.css`
- re-checked risk / closure docs before wording changes:
  - latest relevant request-lifecycle / isolation note found in `docs/poster2/current_branch_execution_log_v1.md`
  - requested root paths were not present in this workspace, so the formal validation-path files were used instead:
    - `docs/poster2/05_validation/bottom_behavior_contract_status_v1.md`
    - `docs/poster2/05_validation/product_region_annotation_contract_status_v1.md`

### Scope

- Stage1 operator-facing labels only
- Stage1 helper / instruction copy only
- shallow Stage1 grouping / section-heading clarity only
- upload constraint messaging visibility only
- `frontend/` and `docs/` mirror alignment on touched files
- branch execution log write-back
- no request builder, renderer, routing, backend schema, Stage2 result, or Stage3 truth work

### Root rules followed

- contract-first
- keep work on the requested layer
- preserve frozen product annotation ownership and bottom ownership
- keep Product Callouts and Bottom Support Copy as separate operator surfaces
- no request/routing/runtime truth change
- keep source and published copies aligned in the same task

### Problem reproduced

- Stage1 still read like a mixed engineering/input form instead of an operator configuration page
- the operator-facing label `Agent / Channel name` no longer matched the intended product meaning
- Product Callouts and Bottom Support Copy were both present, but their ownership boundary was not explicit enough for operators
- upload constraints were mostly implicit or buried inside per-field hints instead of surfaced early in the flow

### Root cause found

- Stage1 copy had grown incrementally around internal template/runtime work, so the surface still exposed older wording and section titles
- section legends emphasized implementation buckets like `Brand`, `Core Assets`, and `Bottom thumbnails` rather than operator tasks
- the page lacked one early, concise upload-guidance block

### Exact Stage1 wording / grouping changes

- renamed `Agent / Channel name (optional)` to `Product Series (optional)` without changing the underlying `agent_name` wiring
- changed the Stage1 intro to `Operator Setup`
- added an early `上传说明` block with:
  - supported file types: `PNG / JPG / JPEG / WEBP`
  - suggested single-file limit: `20MB`
  - recommended quality guidance: clear original images, intact subject, long edge `1200px+`
- regrouped and retitled operator sections to read more clearly:
  - `Template Preview`
  - `Brand & Series`
  - `Main Product`
  - `Product Sheet Details`
  - `Bottom Area`
- added shallow subgroup headings inside the main product block:
  - `Scenario / Visuals`
  - `Main Product`
- clarified ownership wording:
  - `Bottom Support Copy` now explicitly says it only feeds the bottom-owned support area
  - `Product Callouts` now explicitly says it only feeds the product-owned annotation area
  - bottom thumbnails now explicitly state they belong to the bottom area and remain separate from Product Callouts
- updated preview placeholder wording from `Channel` / `Agent` to `Series`

### Files changed

- `frontend/index.html`
- `frontend/app.js`
- `frontend/styles.css`
- `docs/index.html`
- `docs/app.js`
- `docs/styles.css`
- `tests/test_frontend_docs_sync.py`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage1 operator presentation
- Stage1 helper copy / grouping
- publish mirror alignment
- focused mirror validation
- branch execution/state log

### Focused validation run

- `bash scripts/check_frontend_docs_sync.sh`
- `node --check frontend/app.js`
- `node --check docs/app.js`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
- focused static assertions:
  - old `Agent / Channel name` label absent
  - new `Product Series` label present
  - `Product Callouts` and `Bottom Support Copy` remain separate and explicitly distinguished
  - `template_id` and hidden `template_variant` payload wiring strings unchanged
- mirror check:
  - `cmp -s frontend/index.html docs/index.html`
  - `cmp -s frontend/app.js docs/app.js`
  - `cmp -s frontend/styles.css docs/styles.css`

### Remaining risks

- validation here is static/mirror-focused; no live browser capture was added for operator readability
- this PR intentionally did not rename deeper Stage2 / Stage3 engineering diagnostics, request traces, or backend field names

### Exact acceptance state

- Stage1 now reads more clearly as an operator configuration flow
- `Agent / Channel name` no longer appears on the Stage1 operator surface
- `Product Callouts` and `Bottom Support Copy` remain separate and are more clearly distinguished by ownership wording
- no internal template ids or runtime payload construction changed
- no request/routing/runtime truth changed
- `frontend/` and `docs/` touched files are aligned
- `CLAUDE.md` left unchanged because this PR did not add a new shared-state fact beyond branch-local progress

---

## Entry — PR-OP1A: selector reduction and Product Sheet preview completion

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-13

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- task-relevant implementation files:
  - `frontend/index.html`
  - `frontend/app.js`
  - `docs/index.html`
  - `docs/app.js`

### Scope

- Stage1 operator-facing template selector only
- static selector preview completion for `template_product_sheet_v1`
- `frontend/` and `docs/` mirror alignment on touched selector assets
- branch execution log write-back
- no renderer, routing, backend schema, request-builder, bottom contract, or Stage2 replay/result work

### Root rules followed

- contract-first
- keep work on the requested layer
- reversible UI reduction over deeper deletion
- no Family A geometry / ownership / routing truth changes
- no Family B backend routing reopen
- keep source and published copies aligned in the same task

### Problem reproduced

- the operator surface still exposed three template lines overall:
  - `template_dual`
  - `template_focus`
  - the separate Variant B / product-sheet path
- the current Product Sheet / Family B selector preview still fell back to the missing-preview placeholder state

### Root cause found

- Stage1 selector truth came from `frontend/templates/registry.json`, which still listed `template_focus`
- the operator surface also exposed the engineering-facing `template_variant` selector instead of collapsing to product-facing template names
- the selector preview loader required both `spec` and `preview`, so `template_product_sheet_v1` could not load a static preview asset unless selector-side loading allowed preview-only entries

### Files changed

- `frontend/index.html`
- `frontend/app.js`
- `frontend/templates/registry.json`
- `frontend/templates/template_product_sheet_preview.svg`
- `docs/index.html`
- `docs/app.js`
- `docs/templates/registry.json`
- `docs/templates/template_product_sheet_preview.svg`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage1 selector presentation
- selector-side preview asset loading
- published mirror alignment
- branch execution/state log

### Exact selector reduction performed

- removed the `template_focus` entry from the Stage1 registry
- renamed operator-facing selector entries to:
  - `Marketing Poster` -> internal id stays `template_dual`
  - `Product Sheet` -> internal id stays `template_product_sheet_v1`
- hid the engineering-facing Variant control from the operator UI
- synchronized the hidden `template_variant` value from the chosen template id so:
  - `template_dual` resolves to Variant A / existing marketing-poster path
  - `template_product_sheet_v1` resolves to Variant B / existing product-sheet path
- kept internal ids and request-family mapping unchanged

### Preview asset decision for Product Sheet

- added a new static SVG preview asset:
  - `frontend/templates/template_product_sheet_preview.svg`
  - mirrored to `docs/templates/template_product_sheet_preview.svg`
- used a structure-oriented preview, not a photoreal mockup
- the preview explicitly shows:
  - top brand/banner area
  - SKU/top-copy area
  - large hero product area
  - materials/detail strip
  - description block
- no renderer/template runtime logic was changed for this preview completion

### Validation run

- `bash scripts/check_frontend_docs_sync.sh`
- `cmp -s frontend/templates/registry.json docs/templates/registry.json`
- `cmp -s frontend/templates/template_product_sheet_preview.svg docs/templates/template_product_sheet_preview.svg`
- `node --check frontend/app.js`
- `node --check docs/app.js`
- registry assertion:
  - exactly 2 selector entries remain
  - names are `Marketing Poster` and `Product Sheet`
  - `template_focus` is absent
  - `template_product_sheet_v1` points to `template_product_sheet_preview.svg`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`

### Remaining risks

- focused validation here is registry/static/mirror coverage; no live browser capture was attached for the selector canvas
- Stage2 still contains internal family/template diagnostics by design; this PR intentionally did not rename those deeper engineering/debug surfaces

### Exact acceptance state

- selector registry now exposes exactly two operator-facing template choices
- removed focused-subject entry is no longer selectable from the operator UI path
- Product Sheet now has a real static preview asset instead of the missing-preview placeholder
- internal ids remain `template_dual` and `template_product_sheet_v1`
- hidden Variant sync preserves existing Family A / Family B request mapping without reopening routing
- `frontend/` and `docs/` touched files are aligned
- `CLAUDE.md` left unchanged because this PR did not introduce a new shared-state fact beyond branch-local execution state

---

## Entry — PR-S2-STABILITY-1: lock Stage2 gallery count to Stage1 truth and clear post-success bottom-mode contamination

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-12

### Scope

- Stage2 frontend state / request lifecycle only
- no backend contract change
- no renderer change
- no Template A geometry / ownership reopen
- keep supported bottom modes:
  - `title_gallery_split`
  - `gallery_only`
  - `text_only_expanded`

### Root rules followed

- contract-first
- Stage2 consumes Stage1 gallery asset truth; Stage2 does not invent gallery count
- success-derived preview/runtime state must be invalidated before the next request can reuse it
- `frontend/` and `docs/` publish mirror stay aligned in the same task

### Problem reproduced

- after one successful generate, switching bottom mode in the same session could leave success-derived bottom truth, output references, or accepted copy state available to later requests
- Stage2 also needed to ignore any stale local / hydrated thumbnail-count override and derive gallery count only from current Stage1 gallery assets

### Root cause found

- canonical invalidation depended on mixed sources: current form truth plus residual success-derived frontend state
- request diagnostics only logged hashes, not the canonical signature and request payload signature themselves
- gallery count was mostly derived correctly, but the canonical signature / request lifecycle still accepted stale count-shaped state as input instead of forcing Stage1 asset truth

### Files changed

- `frontend/app.js`
- `frontend/stage2_request_helpers.js`
- `tests/frontend/test_stage2_request_helpers.js`
- `tests/test_frontend_docs_sync.py`
- `docs/app.js`
- `docs/stage2_request_helpers.js`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage2 frontend request lifecycle
- Stage2 frontend canonical invalidation / diagnostics
- Stage2 frontend publish-mirror alignment

### Validation run

- `node --test tests/frontend/test_stage2_request_helpers.js`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
- `bash scripts/sync_frontend_to_docs.sh`

### Remaining risks

- no browser-session capture is attached in this entry, so the multi-step UI flow is covered by request-helper invariants and mirror checks rather than a live DOM replay
- no backend/runtime contract was changed in this task, so backend integration was not rerun here

---

## Entry — PR-FA-POLISH-2: lighter annotation cards and airier bottom strip

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-11

### Scope

- Template A / Family A fryer only
- bounded beautification / layout-metrics pass
- no Template B work
- no ownership, annotation anchor, product geometry, bottom mode, gallery count, or caption semantic change

### Root rules followed

- contract-first
- renderer consumes resolver metrics and scoped style tokens
- fixed product annotation ownership stayed under `product_region`
- bottom stayed `title_gallery_split`
- gallery stayed 4 items with `semantic_detail_caption_row`

### Problem reproduced

The active fryer polish baseline still read slightly heavy in the right annotation cards and bottom strip. The gallery row was structurally correct, but the four detail cards still felt a bit attached.

### Root cause found

The fryer-only visual token values remained a step too opaque after PR-FA-FRYER-POLISH-1, and the detail-row spacing used a 24px card gap inside a 740px shell.

### Files changed

- `app/services/poster2/template_behavior.py`
- `app/services/poster2/renderer.py`
- `app/templates_html/template_dual_v2.css`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_renderer.py`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- bounded Family A fryer beautification tokens
- bottom resolver layout metrics
- renderer fallback consumption
- evidence / metadata
- tests

### Validation run

- `./.venv/bin/python -m py_compile app/services/poster2/template_behavior.py app/services/poster2/pipeline.py app/services/poster2/renderer.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'title_gallery_split_fryer_dense_quad_detail_row_adds_breathing or template_a_fryer_bottom_contract_review_exposes_caption_truth or fryer_annotation_contract_review_uses_resolved_positions_source or template_a_regression_path_remains_unchanged or non_fryer_bottom_keeps_caption_mode_none'`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'template_css_exposes_family_a_product_region_observability_freeze_tokens or template_css_exposes_family_a_bottom_region_practical_closure_tokens or fryer_dense_quad_gallery_markup_emits_semantic_captions or resolve_feature_callout_map_uses_fryer_variant_annotation_bounds or product_annotation_wait_uses_resolved_fryer_label_bounds'`
- before/after runtime capture:
  - before screenshot: `/tmp/pr_fa_polish2_before/before.png`
  - before metadata: `/tmp/pr_fa_polish2_before/metadata.json`
  - after screenshot: `/tmp/pr_fa_polish2_after/after.png`
  - after metadata: `/tmp/pr_fa_polish2_after/metadata.json`
  - comparison sheet: `/tmp/pr_fa_polish2_after/before_after.png`
  - metric delta: `/tmp/pr_fa_polish2_after/metric_delta.json`

### Exact runtime delta

- `structure_complete = true`
- `deliverable = true`
- `bottom_mode = title_gallery_split`
- `gallery_caption_mode = semantic_detail_caption_row`
- gallery captions unchanged: `Basket Detail`, `Single Tank`, `Lid Detail`, `Dual Tank`
- annotation card surface reduced from `rgba(... 0.58/0.38)` to `rgba(... 0.50/0.32)`
- annotation card border reduced from `rgba(... 0.07)` to `rgba(... 0.05)`
- annotation card shadow reduced from `0 6px 12px rgba(... 0.025)` to `0 5px 10px rgba(... 0.018)`
- title-band surface reduced from `rgba(... 0.76/0.54)` to `rgba(... 0.68/0.46)`
- title-band border reduced from `rgba(... 0.06)` to `rgba(... 0.045)`
- title-band shadow reduced from `0 10px 20px rgba(... 0.045)` to `0 8px 16px rgba(... 0.032)`
- gallery shell surface reduced from `rgba(... 0.68)` to `rgba(... 0.58)`
- title-band bounds unchanged: `{x:112, y:728, w:800, h:172}`
- peer gap: `16 -> 18`
- gallery shell bounds: `{x:142, y:916, w:740, h:116} -> {x:133, y:918, w:758, h:116}`
- gallery item size unchanged: `156x90`
- gallery item x positions spread from `164/344/524/704` to `155/341/527/713`
- gallery item internal gap: `24 -> 30`
- gallery media bounds remain `140x56`

### Remaining risks

- local screenshot generation used fallback system fonts because `NotoSansSC` is not installed in this workspace
- screenshot capture used the Pillow renderer path; CSS token parity is covered by focused renderer tests

---

## Entry — PR-FA-FRYER-POLISH-1: lighter annotation cards and airier bottom strip

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-11

### Scope

- Template A / Family A fryer only
- bounded beautification / layout-metrics pass
- no Template B work
- no ownership, annotation anchor, product geometry, bottom mode, gallery count, or caption semantic change

### Root rules followed

- contract-first
- renderer consumes resolver metrics and scoped style tokens
- fixed product annotation ownership stayed under `product_region`
- bottom stayed `title_gallery_split`
- gallery stayed 4 items with `semantic_detail_caption_row`

### Problem reproduced

The fryer annotation cards read too solid against the product region, and the bottom title/gallery treatment felt visually heavy with the four thumbnail cards too attached.

### Root cause found

The active fryer visual treatment still used relatively opaque annotation card/title-band surfaces and a dense detail-row gap/shell frame, even though the slot, caption, and ownership contracts were already correct.

### Files changed

- `app/services/poster2/template_behavior.py`
- `app/services/poster2/pipeline.py`
- `app/services/poster2/renderer.py`
- `app/templates_html/template_dual_v2.css`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_renderer.py`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- bounded Family A fryer beautification tokens
- bottom resolver layout metrics
- renderer consumption
- evidence / metadata
- tests

### Validation run

- `./.venv/bin/python -m py_compile app/services/poster2/template_behavior.py app/services/poster2/pipeline.py app/services/poster2/renderer.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'fryer_annotation_contract_review_uses_resolved_positions_source or title_gallery_split_fryer_dense_quad_detail_row_adds_breathing or template_a_fryer_bottom_contract_review_exposes_caption_truth or fryer_secondary_asset_keeps_single_primary_hero_and_supporting_inset or template_a_regression_path_remains_unchanged or non_fryer_bottom_keeps_caption_mode_none'`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'template_css_exposes_family_a_product_region_observability_freeze_tokens or template_css_exposes_family_a_bottom_region_practical_closure_tokens or fryer_dense_quad_gallery_markup_emits_semantic_captions or resolve_feature_callout_map_uses_fryer_variant_annotation_bounds or product_annotation_wait_uses_resolved_fryer_label_bounds'`
- before/after runtime capture:
  - before screenshot: `/tmp/fryer_polish_before/before.png`
  - before metadata: `/tmp/fryer_polish_before/metadata.json`
  - after screenshot: `/tmp/fryer_polish_after/after.png`
  - after metadata: `/tmp/fryer_polish_after/metadata.json`
  - comparison sheet: `/tmp/fryer_polish_after/before_after.png`
  - metric delta: `/tmp/fryer_polish_after/metric_delta.json`

### Exact runtime delta

- `structure_complete = true`
- `deliverable = true`
- `bottom_mode = title_gallery_split`
- `gallery_caption_mode = semantic_detail_caption_row`
- gallery captions unchanged: `Basket Detail`, `Single Tank`, `Lid Detail`, `Dual Tank`
- annotation card effective surface reduced from `rgba(... 0.74/0.54)` to `rgba(... 0.58/0.38)`
- annotation card border reduced from `rgba(... 0.10)` to `rgba(... 0.07)`
- annotation card shadow reduced from `0 8px 16px rgba(... 0.04)` to `0 6px 12px rgba(... 0.025)`
- title-band height: `176 -> 172`
- peer gap: `12 -> 16`
- gallery shell bounds: `{x:155, y:916, w:714, h:116} -> {x:142, y:916, w:740, h:116}`
- gallery item width/height unchanged: `156x90`; x positions spread from `173/347/521/695` to `164/344/524/704`
- gallery media bounds remain `140x56`

### Remaining risks

- local screenshot generation used fallback system fonts because `NotoSansSC` is not installed in this workspace
- Puppeteer was unavailable locally and the capture used the renderer fallback path

---

## Entry — PR-FA-SPS-1: Family A single-primary support surface

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-11

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
- `docs/poster2/02_architecture/template_family_slot_contract_baseline_v1.md`

### Scope

- Template A / Family A fryer only
- optional support surface under `product_region`
- no Template B work
- no product ownership or annotation slot logic change
- no bottom family or bottom gallery/caption path change
- no new operator inputs

### Root rules followed

- contract-first
- renderer consumes resolved behavior truth
- bottom gallery item 1 remains bottom-owned and is reused as source only
- annotations remain product-region fixed-slot truth

### Problem reproduced

Family A fryer single-primary/no-secondary resolution could leave the lower product canvas visually underweighted while the main hero, annotation lane, and bottom gallery paths stayed otherwise healthy.

### Root cause found

The product-region contract had no optional subordinate support surface for the single-primary/no-secondary case, so the resolver could only collapse the secondary slot and leave the lower support zone empty.

### Files changed

- `app/services/poster2/template_behavior.py`
- `app/services/poster2/pipeline.py`
- `app/services/poster2/renderer.py`
- `app/templates_html/template_dual_v2.html`
- `app/templates_html/template_dual_v2.css`
- `tests/poster2/test_pipeline.py`
- `docs/poster2/02_architecture/template_family_slot_contract_baseline_v1.md`
- `docs/poster2/03_engineering/family_a/family_a_single_primary_support_surface_v1.md`
- `docs/poster2/05_validation/family_a/family_a_single_primary_support_surface_status_v1.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- product-region slot contract
- resolver behavior truth
- renderer consumption
- evidence / metadata
- bounded Family A fryer presentation
- docs

### Validation run

- `./.venv/bin/python -m py_compile app/services/poster2/template_behavior.py app/services/poster2/pipeline.py app/services/poster2/renderer.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'support_surface or fryer_secondary_asset_keeps_single_primary_hero_and_supporting_inset or template_a_fryer_bottom_contract_review_exposes_caption_truth or template_a_regression_path_remains_unchanged'`

### Exact runtime delta

- active only when:
  - `product_layout_mode = single_primary`
  - `secondary_product_mode = inset_hidden_no_reserve`
  - `product_secondary_slot_rendered = false`
  - Family A fryer variant is active
  - bottom gallery item 1 has a resolved asset
- source: `bottom_gallery_item_1_asset`
- fallback source evidence: `bottom_gallery_item_1_unavailable`
- mode: `family_a_fryer_single_primary_bottom_gallery_1_support_surface`
- bounds: `{x:472, y:594, w:136, h:104}`
- caption: reuses `gallery_caption_slot_1.caption_text` when available

### Remaining risks

- focused structural tests were run; full screenshot capture was not run in this pass

---

## Entry — PR-FA-WYSIWYG-1: Family A fryer truth-parity and footer-caption closeout

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-10

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
- `docs/poster2/05_validation/bottom_behavior_contract_status_v1.md`
- `docs/poster2/05_validation/product_region_annotation_contract_status_v1.md`

### Scope

- Template A / Family A only
- fryer-only closeout
- no Template B work
- no Stage1/Stage2 request-state reopen
- no bottom redesign

### Root rules followed

- contract-first
- renderer consumes truth; renderer does not define truth
- product annotations stayed fixed-slot and product-owned
- bottom stayed `title_gallery_split`
- gallery stayed `strip_local_visible_only`

### Problem reproduced

Two WYSIWYG gaps remained open after the parity fix:

1. fryer annotation evidence was still split between resolved product truth and stale review-time `template_spec_fixed` evidence
2. HTML preview already expressed fryer footer as thumbnail + caption, but Pillow final still rendered an image-only strip

### Root cause found

1. `product_annotation_contract_review` still rebuilt slot evidence from template defaults instead of resolved `product_policy.annotation_items`
2. fryer footer caption semantics existed in HTML markup flow but were not formalized in bottom behavior or consumed by Pillow `_draw_gallery`
3. Pillow fryer callout card treatment was still visually heavier than the approved preview treatment

### Files changed

- `app/services/poster2/template_behavior.py`
- `app/services/poster2/pipeline.py`
- `app/services/poster2/renderer.py`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_renderer.py`
- `docs/poster2/03_engineering/family_a/family_a_fryer_truth_parity_and_footer_caption_closeout_v1.md`
- `docs/poster2/05_validation/family_a/family_a_fryer_truth_parity_and_footer_caption_closeout_status_v1.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `CLAUDE.md`

### Layer changed

- contract / resolver truth
- evidence / metadata
- renderer consumption
- bounded fryer-only presentation
- docs

### Validation run

- `./.venv/bin/python -m py_compile app/services/poster2/template_behavior.py app/services/poster2/pipeline.py app/services/poster2/renderer.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'fryer_annotation_contract_review_uses_resolved_positions_source or fryer_dense_quad_detail_row_adds_breathing or non_fryer_bottom_keeps_caption_mode_none or template_a_fryer_bottom_contract_review_exposes_caption_truth or annotation_contract_review_product_region_bounds_from_product_policy or fryer_variant_expands_product_text_shell_and_annotation_capacity or fryer_secondary_asset_keeps_single_primary_hero_and_supporting_inset'`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'fryer_dense_quad_gallery_markup_emits_semantic_captions or fryer_caption_helper_leaves_non_fryer_gallery_status_unchanged or resolve_feature_callout_map_uses_fryer_variant_annotation_bounds or fryer_variant_annotation_bounds or product_shell_boundary_closure'`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'template_a_regression_path_remains_unchanged or non_fryer_bottom_keeps_caption_mode_none'`
- identical-input before/after runtime capture:
  - before: `/tmp/pr_fa_wysiwyg_before/*`
  - after: `/tmp/pr_fa_wysiwyg_after/*`

### Exact runtime delta

- `structure_complete = true`
- `deliverable = true`
- `header_mode = identity_left_agent_right`
- `product_annotation_owner = product_region`
- `bottom_mode = title_gallery_split`
- `gallery_mode = strip_local_visible_only`
- fryer annotation `positions_source`:
  - before: `template_spec_fixed`
  - after: `family_a_fryer_fixed_variant`
- fryer footer caption truth:
  - before: `gallery_caption_mode = none`
  - after: `gallery_caption_mode = semantic_detail_caption_row`
- final footer now renders real thumbnail + caption cards in fryer order:
  - `Basket Detail`
  - `Single Tank`
  - `Lid Detail`
  - `Dual Tank`

### Remaining risks

- local screenshot generation used fallback system fonts because `NotoSansSC` is not installed in this workspace
- this pass closes fryer-only truth/parity gaps and does not reopen broader Family A redesign

---

## Entry — poster2 doc path cleanup: finalize legacy root-level markdown removals

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-09

### Scope

- docs path governance only
- no poster runtime changes
- no Template A or Template B behavior changes

### Problem reproduced

Legacy root-level `docs/poster2/*.md` files had already been migrated into layered directories, but the root deletions were still left unstaged in the working tree.

That caused repeated noisy scans on every `git status` / task pass.

### Root cause found

The formal doc path migration had been applied in content and indexing, but the repository state had not yet been cleaned up by committing the corresponding root-level removals.

### Files changed

- root-level legacy `docs/poster2/*.md` entries removed from git tracking
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- docs housekeeping only

### Validation run

- verified all migrated formal docs already exist under:
  - `01_product/`
  - `02_architecture/`
  - `03_engineering/`
  - `04_skills/`
  - `05_validation/`
  - `99_archive/`
- verified `docs/poster2/README.md` already points to layered formal paths

### Remaining risks

- `docs/.DS_Store` remains separate workspace noise and is not part of this poster2 root markdown cleanup

---

## Entry — PR-A-TEXT1..4: Template A text contract repair and product-region text closure

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-09

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
- `docs/poster2/05_validation/bottom_behavior_contract_status_v1.md`
- `docs/poster2/05_validation/bottom_mode_switch_closure_status_v1.md`
- `docs/poster2/05_validation/template_a_beautification_freeze_status_v1.md`
- `docs/poster2/05_validation/template_a_rebaseline_status_v1.md`

### Scope

- Template A text contract repair only
- no geometry changes
- no ownership changes
- no Template B work
- feature_region remains delegated diagnostic

### Root rules followed

- contract-first
- renderer executes truth; renderer does not define truth
- no geometry drift
- no ownership drift
- no Template B expansion

### Problem reproduced

Template A text lifecycle still had three practical failures:

1. annotation `sanitized_text` was destructive for slot 3
2. accepted optimization did not fully and explicitly drive final rendered text
3. subtitle cleanup / fit handling still allowed clipped or noisy output

### Root cause found

1. `pipeline._normalize_contract_text_spec()` still compressed Template A annotation inputs during sanitization
2. `copy_optimizer.resolve_copy_optimization()` did not model cleanup / fit rewrite as explicit pre-render stages
3. metadata/UI lineage stopped too early and did not expose final render source clearly

### Files changed

- `app/services/poster2/pipeline.py`
- `app/services/poster2/copy_optimizer.py`
- `frontend/app.js`
- `frontend/stage2.html`
- `docs/app.js`
- `docs/stage2.html`
- `tests/poster2/test_pipeline.py`
- `tests/test_stage2_guard_diagnostics_surface.py`
- `docs/poster2/03_engineering/family_a/template_a_text_contract_repair_and_product_region_text_closure_v1.md`
- `docs/poster2/05_validation/family_a/template_a_text_contract_repair_and_product_region_text_closure_status_v1.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `CLAUDE.md`

### Layer changed

- contract
- validation
- resolver / behavior wiring
- evidence / metadata
- Stage2 renderer consumption
- docs

### Validation run

- `./.venv/bin/python -m py_compile app/services/poster2/pipeline.py app/services/poster2/copy_optimizer.py tests/poster2/test_pipeline.py tests/test_stage2_guard_diagnostics_surface.py` -> `pass`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'copy_optimization or annotation_sanitization or subtitle_cleanup_and_fit_rewrite'` -> `8 passed, 291 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py` -> `116 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py -k 'copy_optimization or generate_poster_v2_route_is_backward_compatible'` -> `2 passed, 26 deselected`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py` -> `17 passed`

### Exact acceptance

- annotation slot 3 no longer collapses from `Smart controls for daily convenience` to `Smart controls` during sanitize
- Template A subtitle and annotation now expose:
  - `cleanup_text`
  - `fit_rewrite_text`
  - `fit_rewrite_applied`
  - `fit_rewrite_reason`
  - `accepted_text`
  - `rendered_text_source`
- accepted optimization can become the actual rendered candidate
- Stage2 now shows the final text-source chain without reopening layout or geometry

### Remaining risks

- this pass did not reopen Family A bottom structure or geometry backlog
- old root-level poster2 doc deletions remain unstaged workspace residue and were intentionally left untouched

---

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

## Template A freeze continuation — follow-up local acceptance attempt

### Read state
- after the two narrow Template A bottom follow-ups, the task returned to the existing Family A freeze sequence
- scope remained Template A only
- no Template B, geometry, ownership, or bottom structure changes were introduced in this continuation step

### Objective
- refresh the Family A freeze acceptance with a fresh local canonical sample run
- verify that the inserted bottom follow-ups did not disturb frozen Family A control truth

### Runtime command shape
- local `PosterPipeline` run with real `PuppeteerStructuredRenderer`
- mocked background service, mocked asset loader, local artifact bundle
- canonical sample: `annotation_triplet_gallery_triplet_subtitle_present`

### Artifact bundle
- artifact root: `/var/folders/yx/bczfw6c57yn9sz87824v9ts40000gn/T/poster2-family-a-live-acceptance-s2z18xnv`
- final image: `/var/folders/yx/bczfw6c57yn9sz87824v9ts40000gn/T/poster2-family-a-live-acceptance-s2z18xnv/poster2__final__0bdbe781-3a96-4e3e-a57f-6da8e52d8bb2.png`
- foreground image: `/var/folders/yx/bczfw6c57yn9sz87824v9ts40000gn/T/poster2-family-a-live-acceptance-s2z18xnv/poster2__fg__0bdbe781-3a96-4e3e-a57f-6da8e52d8bb2.png`
- metadata: `/var/folders/yx/bczfw6c57yn9sz87824v9ts40000gn/T/poster2-family-a-live-acceptance-s2z18xnv/poster2__debug__metadata__0bdbe781-3a96-4e3e-a57f-6da8e52d8bb2.json`
- summary: `/var/folders/yx/bczfw6c57yn9sz87824v9ts40000gn/T/poster2-family-a-live-acceptance-s2z18xnv/acceptance_summary.json`

### Hashes
- final hash: `a192147df0c0b5802e302054900e67b63cab31882a105525ac1e78bdfbc9ced6`
- foreground hash: `097791436fa582611343344bb4c0f7b89a3034090e738d6bd7337bafac3aeb24`
- metadata sha256: `4f7acd6eea8cbbca0897af14eae9e35cd8f36a1995456a32716bd2f8586136f6`

### Result
- frozen Family A control truth remained aligned:
  - `hero_mode = scenario_cover_product_contain`
  - `feature_mode = product_anchor_callouts`
  - `product_annotation_mode = product_anchor_callouts`
  - `header_mode = identity_left_agent_right`
  - `bottom_mode = title_gallery_split`
  - `gallery_mode = strip_local_visible_only`
  - `product_layout_mode = single_primary`
  - `secondary_product_mode = inset_hidden_no_reserve`
- `structure_complete = true`
- `deliverable = true`
- `template_b_parity_review` remained absent

### Chromium acceptance blocker
- local Chromium launch failed in this workspace
- runtime therefore degraded with:
  - `render_engine_used = pillow`
  - `degraded = true`
  - `degraded_reason = puppeteer_missing_chromium`

### Validation run
- local canonical acceptance command completed and produced the artifact bundle above
- existing regression status from the narrow bottom follow-ups remains:
  - `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'title_gallery_split_preserves_support_copy_in_requested_and_sanitized_subtitle_fields or family_a_runtime_rebaseline_matches_fixture or accepted_output_keys'`
    - `3 passed, 285 deselected`
  - `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py`
    - `8 passed`
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
    - `6 passed`
  - `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py`
    - `114 passed`

### Remaining risks
- this step refreshed local acceptance evidence for Family A control truth, but did not produce a fresh non-degraded live Chromium artifact
- a Chromium-ready environment is still required for the full live acceptance refresh

### Exact acceptance
- the inserted Template A bottom follow-ups did not disturb frozen Family A control truth
- Family A freeze remains valid at the contract/control layer
- fresh live Chromium acceptance remains pending only because of the local browser environment

## Template A freeze continuation — Chromium-ready non-degraded acceptance

### Read state
- this step moved the canonical Template A acceptance run into a Chromium-available environment
- no Template A logic, Template B logic, geometry, ownership, or bottom structure was reopened
- scope was environment verification only

### Objective
- replace the local environment-blocked acceptance attempt with a fresh non-degraded Puppeteer acceptance bundle
- confirm the frozen Family A baseline still holds after the narrow bottom follow-ups

### Runtime command shape
- canonical `PosterPipeline` run for `template_dual_v2`
- real `PuppeteerStructuredRenderer`
- mocked background service, mocked asset loader, local artifact bundle
- canonical sample: `annotation_triplet_gallery_triplet_subtitle_present`

### Artifact bundle
- artifact root: `/var/folders/yx/bczfw6c57yn9sz87824v9ts40000gn/T/poster2-family-a-live-acceptance-ge_l0dts`
- final image: `/var/folders/yx/bczfw6c57yn9sz87824v9ts40000gn/T/poster2-family-a-live-acceptance-ge_l0dts/poster2__final__9e228b8c-3fd2-49b3-a70b-1758d9b9603f.png`
- foreground image: `/var/folders/yx/bczfw6c57yn9sz87824v9ts40000gn/T/poster2-family-a-live-acceptance-ge_l0dts/poster2__fg__9e228b8c-3fd2-49b3-a70b-1758d9b9603f.png`
- metadata: `/var/folders/yx/bczfw6c57yn9sz87824v9ts40000gn/T/poster2-family-a-live-acceptance-ge_l0dts/poster2__debug__metadata__9e228b8c-3fd2-49b3-a70b-1758d9b9603f.json`
- summary: `/var/folders/yx/bczfw6c57yn9sz87824v9ts40000gn/T/poster2-family-a-live-acceptance-ge_l0dts/acceptance_summary.json`

### Hashes
- final hash: `194a61c2df4638038e0b61effd5c63b70a17fcb53bf404d4c68e0b03cd4f04b0`
- foreground hash: `e6caf28f449511751014934745a59e4a5094ce2c17caf3a9554d0d4c42e9320e`
- metadata sha256: `3698cb8da09c5ecda05eaacfc33e1669201e1a85598787b6942253357ea575ae`

### Acceptance result
- `render_engine_used = puppeteer`
- `degraded = false`
- `degraded_reason = null`
- `structure_complete = true`
- `deliverable = true`
- frozen Family A behavior modes remained aligned:
  - `hero_mode = scenario_cover_product_contain`
  - `feature_mode = product_anchor_callouts`
  - `product_annotation_mode = product_anchor_callouts`
  - `header_mode = identity_left_agent_right`
  - `bottom_mode = title_gallery_split`
  - `gallery_mode = strip_local_visible_only`
  - `product_layout_mode = single_primary`
  - `secondary_product_mode = inset_hidden_no_reserve`

### Fixture / baseline comparison
- canonical sample still matches golden-matrix case `annotation_triplet_gallery_triplet_subtitle_present`
- sample semantics are aligned across fixture / summary / attached metadata:
  - canonical sample name = `annotation_triplet_gallery_triplet_subtitle_present`
  - `product_layout_mode = single_primary`
  - `secondary_product_mode = inset_hidden_no_reserve`
  - subtitle is present and rendered, not collapsed:
    - `requested_subtitle_text` non-empty
    - `sanitized_subtitle_text` non-empty
    - `subtitle_slot.state = rendered`
- no Template B residue present; `template_b_parity_review` absent
- acceptance refreshed on a non-degraded Puppeteer path after the narrow Template A bottom follow-ups

### Remaining risks
- artifact bundle is local-environment output under `/tmp`/temp storage and is not persisted to remote object storage
- no new contract/control debt was introduced in this verification step

### Exact acceptance
- Family A freeze is now both code-complete and acceptance-complete on a non-degraded Puppeteer path
- next sequence can proceed to Family A anchored shared-skill extraction

## Family A anchored shared-skill extraction — rules and storage baseline

### Read state
- Family A freeze acceptance is complete
- this step defines only the formal skill rules and storage baseline
- no shared-skill implementation extraction is done in this step
- scope remains Family A anchored only

### Problem reproduced
- the repo had accepted Family A runtime truth but no formal shared-skill registration/storage system
- there was no canonical rules document for layer classification, registry fields, admission gates, or forbidden mutations
- there was no dedicated poster2 shared-skill code/test/fixture storage root

### Root cause
- shared-skill extraction had not yet been formalized into repo governance and storage layout
- without a formal baseline, future extraction work could drift across docs, fixtures, family scope, and registration shape

### Files changed
- `docs/poster2/skill_rules_and_storage_v1.md`
- `docs/poster2/README.md`
- `app/services/poster2/skills/__init__.py`
- `app/services/poster2/skills/structure/__init__.py`
- `app/services/poster2/skills/control/__init__.py`
- `app/services/poster2/skills/beautification/__init__.py`
- `app/services/poster2/skills/evidence/__init__.py`
- `app/services/poster2/skills/registry.py`
- `tests/poster2/skills/__init__.py`
- `tests/poster2/skills/test_registry.py`
- `tests/poster2/fixtures/skills/family_a_skills_registry_v1.json`

### Layer changed
- formal skill rules
- formal skill storage baseline
- Family A-only registration baseline
- fixture-backed registry gate

### Validation run
- `./.venv/bin/python -m pytest -q tests/poster2/skills/test_registry.py`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`

### Remaining risks
- this step only registers the Family A anchored skill baseline; it does not yet extract shared skill implementation
- Template B is intentionally not registered in the shared-skill system yet

### Exact acceptance
- poster2 now has a formal skill-rules document and formal storage path
- `app/services/poster2/skills/` and matching test/fixture roots now exist
- the initial skill registry is Family A-only across structure / control / beautification / evidence
- the repo is ready for the first Family A anchored shared-skill implementation step

## Family A anchored shared-skill extraction — first implementation batch

### Read state
- the skill rules/storage baseline is already landed
- scope remains Family A only
- this step extracts only the first callable shared-skill implementations:
  - structure
  - control
  - evidence
- beautification remains registry/preset consumption only; no broad shared beautification refactor is included

### Problem reproduced
- the shared-skill registry existed, but the Family A entries were still registration-only pointers
- structure/control/evidence were still consumed straight from `family_a_runtime.py`
- there was no registry -> implementation -> Family A runtime closure test

### Root cause
- the first extraction step had not yet created family-scoped implementation modules under `app/services/poster2/skills/`
- runtime consumption had not yet been rewired to take the extracted Family A skill entrypoints

### Files changed
- `app/services/poster2/skills/registry.py`
- `app/services/poster2/skills/structure/family_a_structure_surface_v1.py`
- `app/services/poster2/skills/control/family_a_control_surface_v1.py`
- `app/services/poster2/skills/evidence/family_a_evidence_surface_v1.py`
- `app/services/poster2/template_behavior.py`
- `app/services/poster2/pipeline.py`
- `app/services/poster2/renderer.py`
- `tests/poster2/skills/test_registry.py`
- `tests/poster2/skills/test_family_a_implementations.py`

### Layer changed
- Family A shared structure skill implementation
- Family A shared control skill implementation
- Family A shared evidence helper implementation
- registry implementation binding
- focused extraction closure tests

### Validation run
- `./.venv/bin/python -m py_compile app/services/poster2/skills/registry.py app/services/poster2/skills/structure/family_a_structure_surface_v1.py app/services/poster2/skills/control/family_a_control_surface_v1.py app/services/poster2/skills/evidence/family_a_evidence_surface_v1.py app/services/poster2/template_behavior.py app/services/poster2/pipeline.py app/services/poster2/renderer.py tests/poster2/skills/test_registry.py tests/poster2/skills/test_family_a_implementations.py`
- `./.venv/bin/python -m pytest -q tests/poster2/skills/test_registry.py tests/poster2/skills/test_family_a_implementations.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'family_a or accepted_output_keys or visible_truth_keys_match_family_a_whitelist or family_control_surface or geometry_evidence_surfaces_family_structure_entry'`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py`

### Remaining risks
- `family_a_runtime.py` still remains the Family A oracle; this step wraps and binds it, but does not yet decompose that oracle into finer shared helpers
- beautification is intentionally still registry/preset-consumption only and is not yet extracted into a shared implementation surface
- Template B remains intentionally outside this extraction wave

### Exact acceptance
- `family_a_structure_surface_v1` is now a callable Family A skill implementation
- `family_a_control_surface_v1` is now a callable Family A skill implementation
- `family_a_evidence_surface_v1` now exposes actual helper behavior for visible-truth filtering and Family A evidence guards
- `registry.py` now binds Family A skills to explicit implementation modules/symbols
- Template A runtime continues to consume Family A structure/control/evidence through Family A-scoped skill entrypoints without changing Family A behavior truth

## Family A anchored shared-skill extraction — beautification skill implementation

### Read state
- Family A structure/control/evidence skill implementations are already landed
- Family A runtime remains the oracle
- beautification was still only registry/preset-consumption and had not yet been extracted into a Family A skill implementation
- scope remains Family A only

### Problem reproduced
- `family_a_beautification_freeze_pack_v1` existed in the registry, but it did not point to a formal Family A skill module
- Template A beautification resolution still lived as scattered token preset/constants inside `template_behavior.py`
- renderer consumed resolved Family A beauty output, but runtime did not yet consume it through a Family A beautification skill entrypoint

### Root cause
- the first shared-skill extraction wave deliberately stopped at structure/control/evidence
- Family A beautification presets had not yet been wrapped into a family-scoped callable implementation with registry binding and runtime consumption

### Files changed
- `app/services/poster2/skills/registry.py`
- `app/services/poster2/skills/beautification/family_a_beautification_freeze_pack_v1.py`
- `app/services/poster2/template_behavior.py`
- `tests/poster2/skills/test_family_a_implementations.py`

### Layer changed
- Family A beautification skill implementation
- registry binding for the frozen Family A beautification pack
- Template A resolver consumption path for Family A freeze tokens
- focused beautification skill closure tests

### Validation run
- `./.venv/bin/python -m py_compile app/services/poster2/skills/beautification/family_a_beautification_freeze_pack_v1.py app/services/poster2/skills/registry.py app/services/poster2/template_behavior.py tests/poster2/skills/test_family_a_implementations.py`
- `./.venv/bin/python -m pytest -q tests/poster2/skills/test_registry.py tests/poster2/skills/test_family_a_implementations.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'family_a or accepted_output_keys or visible_truth_keys_match_family_a_whitelist or family_control_surface or geometry_evidence_surfaces_family_structure_entry'`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py`

### Remaining risks
- Family A oracle still retains non-beautification control/geometry logic in `template_behavior.py`; this step extracts the frozen beauty pack consumption path, not the full oracle
- Template B remains intentionally outside beautification skill adoption
- no new visual exploration was done; only the existing Family A freeze pack and supported A token variants were wrapped into the skill layer

### Exact acceptance
- `family_a_beautification_freeze_pack_v1` is now a formal callable Family A skill implementation
- registry now resolves Family A beautification to `app/services/poster2/skills/beautification/`
- Template A resolver consumes the Family A beautification freeze pack through the skill entrypoint
- Family A accepted output/evidence keys remain unchanged
- Family A frozen visual semantics remain stable without geometry, ownership, or control truth changes

## poster2 documentation path and naming governance — first migration batch

### Read state
- `poster_generation_product_design_baseline_v1.md` remains the single product anchor at `docs/poster2/` root
- `README.md` remains index only
- `current_branch_execution_log_v1.md` remains the active log only
- current code mainline remains Family A four-layer closure; no new engineering implementation is in scope for this doc pass

### Problem reproduced
- formal poster2 docs were still mixed at `docs/poster2/` root
- formal path and actual storage no longer matched the intended layered governance model
- `README.md` still indexed root-level paths instead of the layered storage target
- there was no formal Family A four-layer verification matrix bound to the accepted live sample

### Root cause
- document growth had outpaced path governance
- the repo had already established product / architecture / engineering / skills / validation concepts, but the formal doc path was not yet normalized to those layers

### Files changed
- `docs/poster2/README.md`
- `docs/poster2/01_product/*`
- `docs/poster2/02_architecture/*`
- `docs/poster2/03_engineering/*`
- `docs/poster2/04_skills/*`
- `docs/poster2/05_validation/*`
- `docs/poster2/99_archive/*`
- `docs/poster2/05_validation/family_a_four_layer_verification_matrix_v1.md`
- `CLAUDE.md`

### Layer changed
- documentation path governance only
- formal README index path correction
- first migration batch into layered directories
- Family A four-layer verification matrix skeleton
- shared-state alignment

### Validation run
- verified the first migration batch landed under:
  - `01_product/`
  - `02_architecture/`
  - `03_engineering/`
  - `04_skills/`
  - `05_validation/`
  - `99_archive/`
- verified root-level exceptions remain:
  - `poster_generation_product_design_baseline_v1.md`
  - `README.md`
  - `current_branch_execution_log_v1.md`
- verified the Family A verification matrix binds the accepted canonical sample:
  - `annotation_triplet_gallery_triplet_subtitle_present`
  - final hash `194a61c2df4638038e0b61effd5c63b70a17fcb53bf404d4c68e0b03cd4f04b0`
  - metadata sha256 `3698cb8da09c5ecda05eaacfc33e1669201e1a85598787b6942253357ea575ae`

### Remaining risks
- this pass does not rewrite cross-doc relative links inside every migrated historical document
- older legacy grouped directories may still exist as nonformal historical material in this workspace
- no engineering implementation changed in this pass, so any future Family A practical closure still depends on the already accepted code baseline

### Exact acceptance
- poster2 now has a layered formal doc path while keeping the product baseline, index, and active log at root
- `README.md` now points to the layered formal paths
- the first migration batch is landed
- `CLAUDE.md` now aligns shared state with doc-governance-first before the next Family A practical closure step
- Family A now has a formal four-layer verification matrix skeleton bound to the accepted live sample

## Family A practical closure PR1 — product region beautification + observability

### Read state
- Template A remains the active oracle line
- structure / control / evidence / beautification skill adoption already exist for Family A
- this step is limited to product-region practical closure and observability

### Problem reproduced
- Family A product-region polish was still effectively blind from the operator side
- backend already knew `product_layout_mode`, `secondary_product_mode`, `product_annotation_owner`, and annotation visibility truth
- Stage2 did not surface those product-region facts as explicit diagnostics cards
- Family A product shell and annotation shell had frozen baseline semantics but still lacked the practical closure pass for shell / leader / marker expression

### Root cause
- product-region backend truth existed in resolver and contract review, but not all fields were surfaced clearly for operator review
- Family A visual freeze pack did not yet carry the small product/annotation token refinements needed for practical closure
- Pillow product annotation polish had a missing helper after the local visual pass, which broke the renderer regression suite until restored

### Files changed
- `app/services/poster2/pipeline.py`
- `app/services/poster2/renderer.py`
- `app/services/poster2/skills/beautification/family_a_beautification_freeze_pack_v1.py`
- `app/templates_html/template_dual_v2.css`
- `frontend/stage2.html`
- `docs/stage2.html`
- `frontend/styles.css`
- `docs/styles.css`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_renderer.py`
- `tests/test_stage2_guard_diagnostics_surface.py`
- `tests/test_frontend_docs_sync.py`
- `tests/poster2/fixtures/family_a_visual_smoke.json`
- `docs/poster2/03_engineering/family_a/product_region_practical_beautification_observability_v1.md`
- `docs/poster2/05_validation/family_a/product_region_practical_closure_status_v1.md`
- `docs/poster2/README.md`
- `CLAUDE.md`

### Layer changed
- Family A product-region beautification only
- product-region metadata observability
- Stage2 diagnostics visibility
- Family A practical-closure docs / validation anchor

### Validation run
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'product or family_a or accepted_output_keys'`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py`

### Remaining risks
- Family A live Chromium acceptance was not re-run in this step; the refresh anchor is the visual smoke fixture plus existing accepted live sample
- bottom-region observability remains a separate PR and is not included here
- Gemini copy optimizer integration remains out of scope for this product-region pass

### Exact acceptance
- `product_contract_review` now surfaces `secondary_product_mode` and `visible_annotation_count`
- Stage2 product diagnostics now surface:
  - `product_layout_mode`
  - `secondary_product_mode`
  - `product_annotation_owner`
  - `visible_annotation_count`
- Family A product shell / annotation shell / leader line / marker polish landed without geometry or ownership drift
- Family A visual smoke fixture was refreshed to the new practical-closure baseline

## Family A practical closure PR2 — bottom region beautification + observability

### Read state
- Family A product-region practical closure is already landed
- bottom contract remains frozen and in maintenance mode
- this step is limited to title/subtitle hierarchy, gallery-shell polish, and bottom diagnostics visibility

### Problem reproduced
- Stage2 already carried bottom metadata, but bottom-region truth was not surfaced as operator-readable diagnostics cards
- title/subtitle hierarchy still read too flat for a practical closure pass
- title-band and dense-quad gallery shell/items still needed bounded polish inside the frozen geometry

### Root cause
- bottom runtime truth existed in backend review and behavior policy, but was still presented mostly as raw prose rows
- Family A freeze pack did not yet carry bottom-specific inset / outline / support-copy accent tokens
- broad bottom regression tests still include older geometry/history assertions outside this practical-closure scope

### Files changed
- `app/services/poster2/pipeline.py`
- `app/services/poster2/skills/beautification/family_a_beautification_freeze_pack_v1.py`
- `app/templates_html/template_dual_v2.css`
- `frontend/stage2.html`
- `docs/stage2.html`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_renderer.py`
- `tests/test_stage2_guard_diagnostics_surface.py`
- `tests/poster2/fixtures/family_a_visual_smoke.json`
- `docs/poster2/03_engineering/family_a/bottom_region_practical_beautification_observability_v1.md`
- `docs/poster2/05_validation/family_a/bottom_region_practical_closure_status_v1.md`
- `docs/poster2/README.md`
- `CLAUDE.md`

### Layer changed
- Family A bottom-region beautification only
- bottom-region observability surface
- Stage2 bottom diagnostics visibility
- Family A bottom practical-closure docs / validation anchor

### Validation run
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py`
- focused Family A bottom observability tests passed
- broad command `tests/poster2/test_pipeline.py -k 'bottom or family_a or accepted_output_keys'` still includes pre-existing bottom geometry/history failures outside this step

### Remaining risks
- this step intentionally does not reopen legacy bottom geometry/history failures
- live Chromium acceptance was not rerun in this PR
- Gemini copy optimizer and validation closeout remain separate next steps

### Exact acceptance
- Stage2 bottom diagnostics now surface:
  - `bottom_mode`
  - `subtitle_slot.state`
  - `title_rendered`
  - `subtitle_rendered`
  - `gallery_distribution_policy`
- Family A bottom shell/title-band/gallery visual polish landed without changing geometry or ownership
- structured HTML visual smoke fixture was refreshed for the bounded bottom practical-closure pass

---

## Entry — PR-A-PRACTICAL-3: Family A Gemini copy optimizer integration with observability

**Branch:** `main`
**Status:** In progress
**Last updated:** 2026-04-09

### Read state

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/05_validation/family_a/bottom_region_practical_closure_status_v1.md`
- `docs/poster2/03_engineering/family_a/product_region_practical_beautification_observability_v1.md`

### Scope

- Template A only
- Gemini copy optimizer integration for:
  - `title`
  - `subtitle`
  - `annotation`
- operator accept / reject trace
- backend metadata + Stage2 diagnostics visibility
- no geometry / ownership / control-truth changes

### Root cause

Family A practical closure had product and bottom observability, but copy optimization was still opaque:

- no Family A-scoped `copy_optimization_review`
- no operator accept / reject state in Stage2
- no raw → sanitized → optimized → rendered lineage in poster2 metadata

### Files changed

- `app/schemas/poster2.py`
- `app/services/poster2/contracts.py`
- `app/services/poster2/gemini_copy_optimizer.py`
- `app/services/poster2/copy_optimizer.py`
- `app/services/poster2/pipeline.py`
- `app/main.py`
- `frontend/app.js`
- `frontend/stage2.html`
- `docs/app.js`
- `docs/stage2.html`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_api.py`
- `tests/test_stage2_guard_diagnostics_surface.py`
- `docs/poster2/03_engineering/family_a/gemini_copy_optimizer_integration_v1.md`
- `docs/poster2/05_validation/family_a/gemini_copy_optimizer_closure_status_v1.md`
- `docs/poster2/README.md`
- `CLAUDE.md`

### Validation run

- `./.venv/bin/python -m py_compile app/schemas/poster2.py app/services/poster2/contracts.py app/services/poster2/gemini_copy_optimizer.py app/services/poster2/copy_optimizer.py app/services/poster2/pipeline.py app/main.py tests/poster2/test_pipeline.py tests/poster2/test_api.py tests/test_stage2_guard_diagnostics_surface.py` -> pass
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'copy_optimization or family_a or accepted_output_keys'` -> `5 passed, 287 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py -k 'copy_optimization or generate_poster_v2_route_is_backward_compatible'` -> `2 passed, 26 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py` -> `116 passed`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py` -> `17 passed`
- broad command `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'bottom or family_a or accepted_output_keys'` still surfaces the existing legacy bottom geometry/history failures outside this PR-3 scope

### Remaining risks

- Gemini live-network optimization was not exercised in this workspace; the integration path is implemented and test-covered through deterministic / fallback-safe surfaces
- broad legacy bottom geometry/history failures remain out of scope and unchanged
- validation closeout PR still remains after this step

### Exact acceptance

- Family A now emits backend-owned `copy_optimization_review`
- Stage2 can expose optimization mode / decision / optimizer used / changed fields
- operator can accept or reject optimization without changing geometry or ownership
- annotation optimization is count-preserving and cannot create new control truth

---

## Entry — PR-A-PRACTICAL-4: Family A validation closeout

**Branch:** `main`
**Status:** In progress
**Last updated:** 2026-04-09

### Read state

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/05_validation/family_a_four_layer_verification_matrix_v1.md`
- `docs/poster2/05_validation/template_a_beautification_freeze_status_v1.md`
- `docs/poster2/05_validation/template_a_rebaseline_status_v1.md`

### Scope

- Template A only
- validation closeout only
- bind final image + metadata + contract review + UI diagnostics
- no new renderer / behavior / geometry work

### Root cause

The Family A practical-closure sequence was implemented step by step, but the final acceptance binding still lived across multiple separate docs and log entries.

That made the accepted sample, hashes, diagnostics set, and contract-review set harder to verify as one closure pack.

### Files changed

- `tests/poster2/fixtures/family_a_practical_closure_acceptance_v1.json`
- `tests/poster2/test_validation_docs.py`
- `docs/poster2/05_validation/family_a/family_a_practical_closure_status_v1.md`
- `docs/poster2/05_validation/family_a/family_a_practical_closure_verification_matrix_v1.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `CLAUDE.md`

### Validation run

- `./.venv/bin/python -m pytest -q tests/poster2/test_validation_docs.py` -> pass
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py tests/test_stage2_guard_diagnostics_surface.py` -> pass
- no Family A runtime logic was reopened in this step

### Remaining risks

- the acceptance artifact bundle remains referenced from the existing execution log rather than stored in repo
- this closeout pass does not resolve the older out-of-scope bottom geometry/history failures already documented elsewhere

### Exact acceptance

- Family A practical closure now has:
  - a dedicated acceptance fixture
  - a dedicated practical-closure status doc
  - a dedicated practical-closure verification matrix
- canonical sample name, hashes, frozen modes, and UI diagnostics are now tied together in one formal validation set

---

## Entry — PR-A-CO2 + PR-A-PA2: Template A copy optimization value closure + product annotation text closure

**Branch:** `main`
**Status:** In progress
**Last updated:** 2026-04-09

### Read state

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/05_validation/bottom_behavior_contract_status_v1.md`
- `docs/poster2/03_engineering/family_a/gemini_copy_optimizer_integration_v1.md`
- `docs/poster2/05_validation/family_a/gemini_copy_optimizer_closure_status_v1.md`

### Scope

- Template A only
- PR-A-CO2: copy optimization value closure
- PR-A-PA2: product annotation text closure
- no geometry / ownership / control-truth changes
- no Template B work

### Problem reproduced

Family A practical closure still had two operator-blind gaps:

- copy optimization could still read like an empty shell:
  - mode-off showed dead accept / reject controls
  - mode-on lineage and diffs were too thin
- product annotation text stayed fixed and product-owned, but slot-level truncation / budget / rendered state were not directly operator-visible

### Root cause

The remaining gap was consumption and review structure, not contract truth:

- backend review for copy optimization did not always emit a meaningful disabled or diff surface
- Stage2 summary rendered a compact summary instead of full lineage
- product annotation slot review kept most useful fields, but not as a direct fixed-slot practical surface

### Files changed

- `app/services/poster2/copy_optimizer.py`
- `app/services/poster2/pipeline.py`
- `frontend/app.js`
- `frontend/stage2.html`
- `docs/app.js`
- `docs/stage2.html`
- `tests/poster2/test_pipeline.py`
- `tests/test_stage2_guard_diagnostics_surface.py`
- `docs/poster2/03_engineering/family_a/copy_optimization_value_closure_v1.md`
- `docs/poster2/03_engineering/family_a/product_annotation_text_closure_v1.md`
- `docs/poster2/05_validation/family_a/copy_optimization_value_closure_status_v1.md`
- `docs/poster2/05_validation/family_a/product_annotation_text_closure_status_v1.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `CLAUDE.md`

### Layer changed

- metadata / review structure
- Stage2 diagnostics consumption
- Family A practical validation docs

### Validation run

- `./.venv/bin/python -m py_compile app/services/poster2/copy_optimizer.py app/services/poster2/pipeline.py tests/poster2/test_pipeline.py tests/test_stage2_guard_diagnostics_surface.py` -> pass
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'copy_optimization or annotation_slots_surface_fixed_budget_and_truncation_fields'` -> `5 passed, 290 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py -k 'copy_optimization or generate_poster_v2_route_is_backward_compatible'` -> `2 passed, 26 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py` -> `116 passed`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py` -> `17 passed`

### Remaining risks

- live Gemini output was not exercised in this workspace; suggestion quality still depends on deployed-optimizer availability
- broader out-of-scope bottom geometry/history failures remain unchanged

### Exact acceptance

- mode-off copy optimization now surfaces a disabled reason and no dead controls
- mode-on copy optimization now surfaces full lineage and changed-field evidence
- annotation optimization remains wording-only and count-preserving
- fixed 3-slot product annotation surface now exposes requested / sanitized / rendered / truncation / char_budget / line_clamp directly in Stage2
- feature region remains delegated diagnostic only

---

## Entry — PR-A-CQ1: Template A copy quality closure

**Branch:** `main`
**Status:** In progress
**Last updated:** 2026-04-09

### Read state

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
- `docs/poster2/03_engineering/family_a/gemini_copy_optimizer_integration_v1.md`
- `docs/poster2/05_validation/family_a/copy_optimization_value_closure_status_v1.md`

### Scope

- Template A only
- subtitle quality closure
- product annotation text quality closure
- no geometry / ownership / control-truth changes
- no Template B work

### Problem reproduced

Family A observability was already closed, but copy quality still lagged:

- subtitle candidates were often verbose and still truncation-prone
- annotation compression could collapse into weak phrases like `Smart controls`
- copy optimization still defaulted to `off`, so suggest flow was not the main operator path

### Root cause

The remaining issue was quality logic, not structure or control:

- deterministic optimization did not understand the practical subtitle / annotation budget well enough
- candidate sanitization could wash out better annotation rewrites
- Stage2 still treated `off` as the initial path

### Files changed

- `app/services/poster2/copy_optimizer.py`
- `frontend/app.js`
- `docs/app.js`
- `tests/poster2/test_pipeline.py`
- `tests/test_stage2_guard_diagnostics_surface.py`
- `docs/poster2/03_engineering/family_a/copy_quality_closure_v1.md`
- `docs/poster2/05_validation/family_a/copy_quality_closure_status_v1.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `CLAUDE.md`

### Layer changed

- Family A copy optimization quality logic
- Stage2 default suggestion path
- Family A quality-validation docs

### Validation run

- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'copy_optimization or product_annotation_copy_compression_reduces_truncation_for_verbose_sell_points'`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py`

### Remaining risks

- live Gemini quality still depends on deployed optimizer availability
- this step improves candidate quality and operator path, but does not reopen layout or budget contracts

### Exact acceptance

- subtitle optimized candidate is materially shorter and more usable
- annotation slot 3 preserves more meaning than `Smart controls`
- Stage2 now treats `suggest` as the default Family A operator path
- final image, metadata, and `copy_optimization_review` remain aligned through accept / reject

---

## Entry — PR-A-CO3 + PR-A-AR3: Template A copy optimization UI fold + apply-to-render closure

**Branch:** `main`
**Status:** In progress
**Last updated:** 2026-04-09

### Read state

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
- `docs/poster2/03_engineering/family_a/copy_quality_closure_v1.md`

### Scope

- Template A only
- copy optimization UI fold
- apply-to-render closure for accepted optimized copy
- no geometry / ownership changes
- no Template B work

### Problem reproduced

Two narrow follow-ups remained after copy-quality closure:

- Stage2 copy optimization still occupied too much vertical space by default
- accepted optimized subtitle could fail to fall back to the suggested candidate when no explicit accepted subtitle was provided

### Root cause

- the UI still rendered full lineage in the primary panel instead of summary-first with on-demand expansion
- backend `_pick_applied_candidate(...)` fell back for title and features, but not for subtitle
- docs mirror also needed to stay aligned after the Stage2 fold change

### Files changed

- `app/services/poster2/copy_optimizer.py`
- `frontend/app.js`
- `frontend/stage2.html`
- `docs/app.js`
- `docs/stage2.html`
- `tests/poster2/test_pipeline.py`
- `tests/test_stage2_guard_diagnostics_surface.py`
- `docs/poster2/current_branch_execution_log_v1.md`
- `CLAUDE.md`

### Layer changed

- Stage2 diagnostics consumption
- copy optimization apply path

### Validation run

- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'copy_optimization'` -> `6 passed, 291 deselected`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py` -> `17 passed`

### Remaining risks

- this step folds the UI and closes accept/render parity, but does not create a new live artifact bundle
- old unrelated root doc deletions in the working tree remain out of scope

### Exact acceptance

- copy optimization panel is summary-first and default-folded
- full lineage is on-demand only
- no-actionable state no longer consumes the main operator path with dead controls
- accepted optimized subtitle / annotation text now closes into `rendered_text`

---

## Entry — Family A minimal-delta commercial fryer refinement

**Branch:** `main`
**Status:** In progress
**Last updated:** 2026-04-09

### Read state

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
- `docs/poster2/03_engineering/beautification_layer_plan_v1.md`
- current Family A practical-closure and validation docs

### Scope

- Template A / Family A only
- contract-first
- minimal-delta only
- UI structure unchanged
- 3-column header unchanged
- no geometry changes
- no ownership changes
- no Template B work

### Rollback anchor

- pre-change rollback tag created and pushed before code changes:
  - `Poster2-FamilyA-MinDelta-PreCommercialRefine`
  - sha `cdb3216cbb1b95630c9afbb27a9ada9c90af37a7`

### Problem reproduced

The repaired Family A runtime was structurally healthy, but the commercial electric fryer sample still read like a generic kitchen poster:

- default copy was not the fryer-specific English set
- product callout reading was more cramped than necessary for the commercial case
- bottom strip semantics still encouraged repetitive fallback behavior
- Family A token bias still leaned too warm/pink for a stainless commercial appliance

### Root cause

- Stage1 defaults still carried generic kitchen copy
- Family A Mode S payload fallback only lived at the UI-display layer, not cleanly in the request path
- Family A poster2 gallery fallback did not use semantic product-asset ordering for sparse bottom strips
- Family A frozen token pack had not been minimally shifted from warm campaign tones toward a neutral fryer language

### Files changed

- `frontend/app.js`
- `docs/app.js`
- `app/services/poster2/skills/beautification/family_a_beautification_freeze_pack_v1.py`
- `app/templates_html/template_dual_v2.css`
- `tests/test_frontend_docs_sync.py`
- `tests/poster2/skills/test_family_a_implementations.py`
- `tests/poster2/test_renderer.py`
- `tests/poster2/fixtures/family_a_visual_smoke.json`
- `docs/poster2/03_engineering/family_a/family_a_commercial_fryer_min_delta_refinement_v1.md`
- `docs/poster2/05_validation/family_a/family_a_commercial_fryer_min_delta_refinement_status_v1.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `CLAUDE.md`

### Layer changed

- Stage1 default input wiring
- Family A request/consumption path
- Family A minimal beautification token pack
- Family A validation fixture baseline

### Validation run

- `bash scripts/sync_frontend_to_docs.sh`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` -> `7 passed`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py` -> `11 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/skills/test_family_a_implementations.py` -> `4 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'TestFamilyAVisualRebaseline or test_template_behavior_resolver_uses_template_metadata or test_template_a_html_keeps_product_slots_in_absolute_product_region_coordinates'` -> `3 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'family_a_runtime_rebaseline_matches_fixture or accepted_output_keys or test_template_a_payload_filters_out_template_b_visible_truth_and_parity_keys or test_template_a_regression_path_remains_unchanged'` -> `4 passed`

### Remaining risks

- this remains a minimal-delta commercial refinement, not a reopened Family A redesign track
- a fresh live fryer artifact bundle has not yet been captured in this pass
- local non-poster2 noise remains:
  - `docs/.DS_Store`

### Exact acceptance

- default Family A fryer copy is injected through the existing input flow
- header remains the same 3-column layout
- product annotation remains fixed-slot and product-owned
- bottom remains `title_gallery_split`
- bottom gallery semantics no longer default toward repeated logo fallback
- Family A token language is more neutral/commercial without changing layout structure

---

## Entry — Family A fryer live-diagnosis micro-refinement

**Branch:** `main`
**Status:** In progress
**Last updated:** 2026-04-09

### Read state

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
- `docs/poster2/03_engineering/family_a/family_a_commercial_fryer_min_delta_refinement_v1.md`
- `docs/poster2/05_validation/family_a/family_a_commercial_fryer_min_delta_refinement_status_v1.md`
- `docs/poster2/05_validation/bottom_behavior_contract_status_v1.md`

### Scope

- Template A / Family A only
- contract-first
- 3-column header unchanged
- Stage1 / Stage2 UI structure unchanged
- no geometry changes
- no ownership changes
- no Template B work

### Problem reproduced

The latest fryer live diagnosis showed that the previous pass mostly changed token tone and gallery asset preference, but the poster still read too close to the old Family A baseline:

- live header still carried service-center semantics in the right column
- subtitle could stay empty/collapsed through the persisted bottom-contract path
- fixed product annotation was traceable but still too cramped for commercial benefit cards
- 4-image bottom strip still read as a dense repeated row

### Root cause

- Family A fryer right-column text was defaulted in Stage1, but generic service-center strings could still survive through existing stored state and request consumption
- bottom-contract state treated a persisted blank subtitle as canonical, so the fryer default support copy could remain collapsed
- structured HTML annotation consumption still used the stale Family A `anchor_map` dimensions (`144x60`) instead of the current fixed-slot contract (`176x76`)
- dense-quad strip distribution used full-width `196x4 + 16x3`, leaving no outer breathing

### Files changed

- `frontend/app.js`
- `docs/app.js`
- `app/services/poster2/renderer.py`
- `app/services/poster2/template_behavior.py`
- `app/templates_html/anchor_map.template_dual_v2.json`
- `tests/poster2/test_renderer.py`
- `tests/poster2/test_pipeline.py`
- `tests/test_frontend_docs_sync.py`
- `tests/poster2/fixtures/family_a_visual_smoke.json`
- `docs/poster2/03_engineering/family_a/family_a_fryer_live_diagnosis_micro_refinement_v1.md`
- `docs/poster2/05_validation/family_a/family_a_fryer_live_diagnosis_micro_refinement_status_v1.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `CLAUDE.md`

### Layer changed

- Family A request/default carry-through
- Family A structured-render annotation consumption
- Family A dense-quad bottom strip distribution policy
- Family A validation fixture baseline

### Validation run

- `bash scripts/sync_frontend_to_docs.sh`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py` -> `117 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'test_metadata_dense_quad_split_uses_expanded_quad_policies or test_template_a_payload_filters_out_template_b_visible_truth_and_parity_keys or family_a_runtime_rebaseline_matches_fixture or test_template_a_product_annotation_slots_surface_fixed_budget_and_truncation_fields'` -> `3 passed`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py` -> `18 passed`

### Before / after runtime evidence

Before

- live diagnosis still showed old service-center carry-through in the right header lane
- subtitle could remain collapsed under a blank persisted bottom-contract state
- structured HTML annotation path still consumed old `144x60` anchor-map boxes
- dense-quad strip used a full-width `196/16` layout with no side breathing

After

- `header_mode = identity_left_agent_right`
- `header_requested_agent_text = Commercial Electric Fryer Series`
- `header_rendered_agent_excerpt = Commercial Electric Fryer Series`
- `subtitle_slot.state = rendered`
- `rendered_subtitle_excerpt = Fast heating · precise control`
- `product_annotation_owner = product_region`
- annotation slot bounds now remain `176x76` for the 3 active fixed slots
- `gallery_distribution_policy = dense_quad`
- dense-quad item layouts now resolve to:
  - `x = 106 / 314 / 522 / 730`
  - `w = 188`
  - `h = 60`
- `structure_complete = true`
- `deliverable = true`

### Remaining risks

- this is still a bounded micro-refinement, not a reopened Family A redesign track
- a fresh external live artifact bundle is still separate from this local runtime verification
- local non-poster2 noise remains:
  - `docs/.DS_Store`

### Exact acceptance

- header remains 3-column and now carries the fryer right-column semantics into render
- subtitle is rendered instead of collapsing empty in the fryer path
- product annotation remains fixed-slot and product-owned, but structured render now respects the current slot contract
- bottom remains `title_gallery_split`
- 4-item strip keeps gallery ownership while reading less crowded through bounded dense-quad spacing changes

## 2026-04-10 — Family A fryer product annotation shell micro-structure

### Root rules followed

- Template A only
- contract-first
- no geometry changes
- no ownership drift
- no Template B work

### Problem reproduced

- the latest fryer live result was contract-safe but the fixed-width product benefit cards still read cramped
- slot geometry and anchor positions were healthy; the issue was shell text capacity, not placement

### Root cause

- Family A fixed-slot product annotations still used the older `56/46/44`-era text consumption balance inside unchanged `176x76` cards
- inner padding and line-height left too little usable room for short commercial benefit phrases

### Files changed

- `app/services/poster2/template_behavior.py`
- `app/templates_html/template_dual_v2.css`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/fixtures/family_a_visual_smoke.json`
- `docs/poster2/03_engineering/family_a/family_a_product_annotation_shell_micro_structure_v1.md`
- `docs/poster2/05_validation/family_a/family_a_product_annotation_shell_micro_structure_status_v1.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `CLAUDE.md`

### Layer changed

- Family A fixed-slot product annotation shell consumption only

### Validation run

- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'char_budget_raised or annotation_sanitization_remains_hygiene_only or product_annotation_slots_surface_fixed_budget_and_truncation_fields'` -> passed
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'family_a_visual_smoke_hashes_match_fixture or four_item_positions'` -> passed after fixture refresh

### Remaining risks

- this is a fixed-card capacity refinement only, not a product-region redesign
- live Chromium fryer verification remains separate

### Exact acceptance

- annotation remains fixed-slot and product-owned
- slot geometry remains unchanged
- `char_budget` now resolves to `56 / 52 / 48`
- structured HTML smoke updated without Pillow geometry drift

## 2026-04-10 — Family A fryer bottom text finalization

### Root rules followed

- Template A only
- contract-first
- no geometry changes
- no ownership drift
- no Template B work

### Problem reproduced

- fryer bottom subtitle was present again, but the final rendered sentence still collapsed into an under-finished support-copy fragment
- metadata lineage existed, but the rendered candidate was not yet product-grade enough for freeze

### Root cause

- subtitle cleanup already worked, but the fit rewrite path did not preserve the three fryer benefits as a complete short sentence

### Files changed

- `app/services/poster2/copy_optimizer.py`
- `tests/poster2/test_pipeline.py`
- `docs/poster2/03_engineering/family_a/family_a_bottom_text_finalization_v1.md`
- `docs/poster2/05_validation/family_a/family_a_bottom_text_finalization_status_v1.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `CLAUDE.md`

### Layer changed

- Family A subtitle cleanup / fit rewrite / rendered-source selection

### Validation run

- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'fryer_dense_quad_split_keeps_product_grade_subtitle_in_render or subtitle_cleanup_and_fit_rewrite_flow_are_visible'` -> passed

### Remaining risks

- this closes the current fryer subtitle path only
- broader bottom backlog remains unchanged and out of scope

### Exact acceptance

- fryer subtitle fit rewrite now resolves to:
  - `Fast heating, precise control, and stainless steel durability.`
- `rendered_text_source = fit_rewrite_text`
- `subtitle_truncation_applied = false` for the tested fryer path

## 2026-04-10 — Family A fryer blocker closeout

### Root rules followed

- Template A only
- contract-first
- header remains 3-column
- product annotations remain fixed-slot and product-owned
- `bottom_mode = title_gallery_split`
- renderer executes truth
- no Template B work

### Problem reproduced

- the right-side fryer benefit cards were still too narrow for commercial phrases and slot 2 could collapse to `Precise Thermostat`
- the fryer bottom still rendered the weaker compact subtitle path instead of the required commercial sentence
- the 4-item strip still read like a dense thumbnail row with no breathing room between the title band and the strip

### Root cause

- product-region fixed-slot truth still used the old default right-lane shell and default structured-HTML anchor-map bounds instead of a fryer-specific bounded capacity variant
- copy optimization still computed subtitle/render budgets without a true fryer-only closeout path, so the commercial default sentence fell back to the older compact rewrite lineage
- the expanded dense-quad strip had no fryer-specific peer-gap or detail-row distribution policy, so the bottom stayed visually crowded even when structurally valid

### Files changed

- `app/services/poster2/copy_optimizer.py`
- `app/services/poster2/template_behavior.py`
- `app/services/poster2/renderer.py`
- `app/services/poster2/pipeline.py`
- `app/templates_html/template_dual_v2.css`
- `frontend/app.js`
- `docs/app.js`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_renderer.py`
- `tests/poster2/fixtures/family_a_visual_smoke.json`
- `tests/test_frontend_docs_sync.py`
- `docs/poster2/03_engineering/family_a/family_a_product_annotation_shell_micro_structure_v1.md`
- `docs/poster2/05_validation/family_a/family_a_product_annotation_shell_micro_structure_status_v1.md`
- `docs/poster2/03_engineering/family_a/family_a_bottom_text_finalization_v1.md`
- `docs/poster2/05_validation/family_a/family_a_bottom_text_finalization_status_v1.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `CLAUDE.md`

### Layer changed

- Family A product-region fixed-slot shell contract
- Family A subtitle truth selection
- Family A bottom detail-row distribution only

### Validation run

- `./.venv/bin/python -m py_compile app/services/poster2/copy_optimizer.py app/services/poster2/template_behavior.py app/services/poster2/renderer.py app/services/poster2/pipeline.py` -> passed
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'fryer_dense_quad_split_keeps_product_grade_subtitle_in_render or fryer_accepted_subtitle_candidate_enters_rendered_output or fryer_product_annotation_keeps_short_commercial_phrase_without_fit_rewrite or fryer_variant_expands_product_text_shell_and_annotation_capacity or fryer_dense_quad_detail_row_adds_breathing'` -> passed
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'fryer_variant_annotation_bounds or family_a_visual_smoke_hashes_match_fixture'` -> passed after fixture refresh
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py -k 'template_a_family_a_fryer_defaults_and_gallery_semantics_are_wired'` -> passed

### Before / after runtime evidence

Before bundle:

- summary: `/tmp/fryer_before/before_fryer_summary.json`
- image: `/tmp/fryer_before/before_fryer_pillow.png`

After bundle:

- summary: `/tmp/fryer_after/after_fryer_summary.json`
- image: `/tmp/fryer_after/after_fryer_pillow.png`

Measured deltas:

- `structure_complete = true` before and after
- `deliverable = true` before and after
- `header_mode = identity_left_agent_right` before and after
- `product_annotation_owner = product_region` before and after
- product text shell:
  - before `x=784,y=216,w=176,h=276`
  - after `x=776,y=212,w=192,h=286`
- slot 2 text:
  - before `Precise Thermostat` from `fit_rewrite_text`
  - after `Precise Thermostat Control` from `sanitized_text`
- rendered subtitle:
  - before `Fast heating, precise control, and stainless steel durability.`
  - after `Fast heating, precise control, and durable stainless steel construction for everyday commercial use.`
- rendered subtitle source:
  - before `fit_rewrite_text`
  - after `sanitized_text`
- bottom strip:
  - before `gallery_distribution_policy = dense_quad`
  - after `gallery_distribution_policy = dense_quad_detail_row`
  - before `peer_gap = 0`
  - after `peer_gap = 12`
  - before item geometry `188x60`
  - after item geometry `180x56`

### Remaining risks

- this closes the current fryer blockers only inside the existing Family A system; it is not a Family A redesign track
- local runtime evidence used deterministic local assets for repeatability; external commercial acceptance should still use the live fryer asset pack
- local non-poster2 noise remains:
  - `docs/.DS_Store`

### Exact acceptance

- header remains 3-column
- product annotation remains fixed-slot and product-owned
- fryer benefit cards now render with the bounded Family-A-only wider shell and no longer collapse to emergency-label copy
- final fryer bottom copy now renders the required commercial sentence
- accepted optimization still changes rendered subtitle truth when explicitly selected
- 4-item strip remains in `title_gallery_split` but now reads as a semantic detail row with breathing room

## 2026-04-10 — Family A fryer hero/footer blocker removal

### Root rules followed

- Template A only
- contract-first
- header remains 3-column
- product annotations remain fixed-slot and product-owned
- `bottom_mode = title_gallery_split`
- renderer executes truth
- no Template B work

### Problem reproduced

- the fryer poster was structurally healthy, but the main fryer image still read too weakly because the stage was split into a dual-stack composition
- the footer still felt compressed because the title band dominated while the 4-item strip stayed too shallow

### Root cause

- the fryer path still inherited the generic `single_primary -> primary_secondary_dual` auto-promotion, which turned the supporting model into a second full-width tray
- the fryer canvas shell stayed too narrow relative to the annotation lane, so the product image never became the dominant poster hero
- the fryer footer used the earlier detail-row tuning, but the strip height and item height were still too small for a premium detail band

### Files changed

- `app/services/poster2/template_behavior.py`
- `app/services/poster2/pipeline.py`
- `app/services/poster2/family_a_runtime.py`
- `app/services/poster2/renderer.py`
- `app/templates_html/template_dual_v2.css`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_renderer.py`
- `docs/poster2/03_engineering/family_a/family_a_fryer_hero_footer_blocker_removal_v1.md`
- `docs/poster2/05_validation/family_a/family_a_fryer_hero_footer_blocker_removal_status_v1.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `CLAUDE.md`

### Layer changed

- Family A fryer product-region resolver geometry
- Family A fryer structured/Pillow shell parity
- Family A fryer footer strip balance inside `title_gallery_split`

### Validation run

- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'fryer_dense_quad_detail_row_adds_breathing or fryer_variant_expands_product_text_shell_and_annotation_capacity or fryer_secondary_asset_keeps_single_primary_hero_and_supporting_inset or annotation_contract_review_product_region_bounds_from_product_policy'` -> passed
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'fryer_variant_annotation_bounds or product_shell_boundary_closure or resolve_feature_callout_map_uses_fryer_variant_annotation_bounds'` -> passed
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'fryer_dense_quad_split_keeps_product_grade_subtitle_in_render or fryer_accepted_subtitle_candidate_enters_rendered_output or fryer_product_annotation_keeps_short_commercial_phrase_without_fit_rewrite or fryer_variant_expands_product_text_shell_and_annotation_capacity or fryer_dense_quad_detail_row_adds_breathing or fryer_secondary_asset_keeps_single_primary_hero_and_supporting_inset'` -> passed

### Before / after runtime evidence

Before bundle:

- summary: `/tmp/fryer_blocker_before/before_fryer_summary.json`
- image: `/tmp/fryer_blocker_before/before_fryer_pillow.png`

After bundle:

- summary: `/tmp/fryer_blocker_after/after_fryer_summary.json`
- image: `/tmp/fryer_blocker_after/after_fryer_pillow.png`
- comparison: `/tmp/fryer_blocker_after/fryer_before_after_comparison.png`

### Measured deltas

- `structure_complete = true` before and after
- `deliverable = true` before and after
- `header_mode = identity_left_agent_right` before and after
- `product_annotation_owner = product_region` before and after
- hero stage:
  - before `product_layout_mode = primary_secondary_dual`
  - after `product_layout_mode = single_primary`
  - before `product_geometry_mode = primary_secondary_dual_v2`
  - after `product_geometry_mode = family_a_fryer_hero_supporting_inset_v1`
  - before primary slot `300x360`
  - after primary slot `324x540`
  - before secondary slot `300x144`
  - after secondary slot `120x120`
- annotation lane:
  - before `x=776,w=192`
  - after `x=792,w=184`
- footer strip:
  - before `title_band_height = 184`
  - after `title_band_height = 172`
  - before `gallery_shell_height = 84`
  - after `gallery_shell_height = 90`
  - before `gallery_items_height = 56`
  - after `gallery_items_height = 66`
  - before `peer_gap = 12`
  - after `peer_gap = 14`

### Remaining risks

- this closes the current fryer hero/footer blockers only inside the existing Family A system
- it is still not a Family A redesign track
- live commercial acceptance should still be rechecked with the full current fryer asset pack if external signoff is needed
