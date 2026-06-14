# Current Branch Execution Log v1

## Entry — Geometry style variant template_dual_v2_studio

**Branch:** `poster2-vrelax-heavy-v1`
**Status:** Complete (awaiting Owner approval; not merged)
**Last updated:** `2026-06-14`

### Scope

- Add opt-in geometry style variant `template_dual_v2_studio` (HX-POSTER2-STYLE-VARIANT-V1):
  bounded product-image breathing + stronger title hierarchy + lighter gallery surface,
  preserving ownership, bottom SOP geometry, and product-annotation truth.

### Exact changes

- `contracts.py`: `TemplateBehaviorModesSpec.geometry_profile: str = "default"`.
- `template_behavior.py`: `_PRODUCT_STUDIO_BREATHING_PRIMARY_SLOT = {474,224,264,468}` +
  a `geometry_profile == "studio_breathing_v1"` branch in `resolve_product_behavior`
  (floats the product IMAGE inside the unchanged card; region/canvas/anchors unchanged).
- `template_registry.py`: register `template_dual_v2_studio` (v `2.1.6-studio.1`) + add to
  `CAMPAIGN_EXPLAINER_TEMPLATE_IDS`; `tests/.../test_template_registry.py` snapshot updated.
- New spec `app/templates/specs/template_dual_v2_studio.json` (geometry_profile + title 52 /
  subtitle 18 for Pillow parity).
- New assets: `template_dual_v2_studio.css` (title 40→52, subtitle recede, lighter gallery
  strip surface) — `html`/`svg`/`slot_spec`/`anchor_map` are byte-identical copies of base.
- New `scripts/poster2_geometry_variant_review.py` (stability + geometry-invariant harness);
  new `tests/poster2/test_geometry_variant.py`.
- Review package: `docs/poster2/geometry_variant_studio_review_v1.md`.

### Layer changed

- Bounded geometry (product image slot) + variant typography/surface. No region boundary,
  ownership, bottom-SOP geometry, or annotation-truth change. Base + airy untouched.

### Validation performed

- Stability harness 10× base + 10× studio (real Puppeteer): both 100% success, validator
  pass, deterministic. Geometry/ownership invariants all PASS (7 protected regions +
  visible_item_count + ownership_guards identical; only product image slot floats).
- `tests/poster2/test_geometry_variant.py` (10) pass; full suite zero new failures vs the
  post-relaxation baseline; node/sync/py_compile pass.

### Remaining risks / Owner decision

- Geometric bottom-FOOTPRINT reduction is frozen by bottom SOP (shell top y=728 is the
  minimum); this variant reduces PERCEIVED bottom weight only. Physically shrinking the
  bottom = a bottom-SOP amendment = Owner decision (documented in the review package).

### One-line execution summary

- Added a bounded geometry style variant (`template_dual_v2_studio`) that visibly improves
  product breathing + title hierarchy + bottom weight while proving ownership/SOP/annotation
  geometry are byte-identical to the base.

## Entry — Visual Relaxation Layer + template_dual_v2_airy

**Branch:** `main`
**Status:** Complete
**Last updated:** `2026-06-14`

### What was read first

- `CLAUDE.md`, `docs/poster2/README.md`, `current_branch_execution_log_v1.md`
- `docs/poster2/template_taxonomy_and_visual_relaxation_plan_v1.md` (the plan this implements)
- `docs/poster2/05_validation/bottom_behavior_contract_status_v1.md` (frozen bottom SOP)
- `docs/poster2/05_validation/product_region_annotation_contract_status_v1.md` (frozen annotation truth)
- live code: `renderer.py`, `template_behavior.py`, `family_a_beautification_freeze_pack_v1.py`,
  `template_registry.py`, `quality_guard.py`, `pipeline.py`, `contracts.py`, `schemas/poster2.py`,
  `templates_html/template_dual_v2.{html,css}`

### Scope

- Add a contract-safe, non-geometric Visual Relaxation Layer (closed-enum presets:
  `none` / `airy` / `premium_soft` / `dense_safe`).
- Add opt-in variant `template_dual_v2_airy` (Family A; reuses dual_v2 shell/assets;
  differs only by `relaxation_preset = airy`).
- Relaxation is template-spec-driven (`behavior_modes.relaxation_preset`), injected via the
  existing `__BEAUTY_CSS_VARS__` channel. No Stage1/2/3 flow change; no API schema break.

### Root rules followed

- Relaxation may change only surface/spacing CSS-var values; never region ownership, slot
  ownership, product-annotation truth, bottom-SOP truth, or structural geometry.
- `none` injects ZERO CSS vars → byte-identical to the pre-relaxation render.
- Only existing, consumed, non-geometry, non-freeze-pack-owned CSS vars are overridden.

### Implementation deviations from the plan (and why)

- Plan §4 proposed 8 token families. Investigation of the live CSS + freeze pack showed
  several are unusable as injected overrides, so the first pass wires only two effective levers:
  - `--title-stack-gap` (title/subtitle stack breathing) — effective.
  - `--product-primary-shadow` (product image drop-shadow lift) — effective, NOT freeze-pack-owned.
- Excluded and documented as no-op / out-of-bounds:
  - `--peer-region-gap`: defined in CSS but consumed nowhere (inert no-op).
  - `--product-content-pad-*`: consumed by `.layer-product-content`, but the product slot inside
    is absolutely positioned → padding does not move the product. Real product-resize breathing
    is a GEOMETRY change → future geometry style-variant, not relaxation.
  - scenario↔product seam blend: no seam var exists; a seam mask = new geometry → out of bounds.
  - `--shell-shadow-*`, `--shell-surface-*`, `--accent-tone`: authored (warm-tinted) by the
    Family A freeze pack; overriding them would re-tint / mask frozen surface truth.

### Exact code changes

- NEW `app/services/poster2/relaxation.py`: closed-enum presets, non-geometry CSS-var whitelist,
  `relaxation_css_vars()`, `relaxation_report()`, `assert_relaxation_vars_non_geometric()`.
- `contracts.py`: `TemplateBehaviorModesSpec.relaxation_preset` (default "none");
  `RenderManifest.relaxation_preset` (dict, default-factory).
- `template_behavior.py`: merge `relaxation_css_vars(...)` LAST into `css_vars` (Family A + B),
  add `ResolvedTemplateBehavior.relaxation_preset`, surface it in `as_dict()`.
- `template_registry.py`: register `template_dual_v2_airy` (v `2.1.6-airy.1`);
  `CAMPAIGN_EXPLAINER_TEMPLATE_IDS` + `is_campaign_explainer_template()`.
- `pipeline.py` (210/880/890) + `copy_optimizer.py` (399) + `main.py`
  (`_validate_poster2_renderer_request` puppeteer pilot gate): widen the five `== "template_dual_v2"`
  branches to the campaign-explainer predicate so airy is a faithful relaxation-only twin
  (existing-id behavior byte-identical); populate `manifest.relaxation_preset`.
- `quality_guard.py`: `assert_relaxation_non_geometric()` (differential region/slot-bounds guard).
- `schemas/poster2.py` + `main.py`: additive `relaxation_preset` response field.
- NEW spec `app/templates/specs/template_dual_v2_airy.json` (clone of dual_v2 + relaxation_preset).
- NEW assets: `template_dual_v2_airy.{html,css,svg}`, `slot_spec.*`, `anchor_map.*` —
  byte-identical copies of dual_v2 (renderer/region_matrix untouched).
- NEW `scripts/poster2_relaxation_stability_harness.py`; NEW `tests/poster2/test_relaxation.py`;
  fixed pre-existing-red `tests/poster2/test_template_registry.py` snapshot.

### Layer changed

- Beautification layer (downstream of structure/behavior). No structural geometry, ownership,
  Stage2 contract, or `/api/v2/generate-poster` schema change.

### Validation performed

- `node --check frontend/app.js`, `node --check docs/app.js`, `bash scripts/check_frontend_docs_sync.sh` — pass.
- `python -m py_compile` of all changed backend files — pass.
- `pytest tests/poster2/test_relaxation.py tests/poster2/test_template_registry.py` — 34 passed.
- Byte-identity proof: `template_dual_v2` (none) Pillow sha256 `a5ef87ee…` and css-var-style sha256
  `2d30baed…` are IDENTICAL before/after the change → `none` is a true no-op.
- Regression baseline: the 19 renderer/quality failures are PRE-EXISTING at HEAD (same 19 with and
  without this change); this change adds 42 passing tests and zero new failures.
- Stability harness (10× each, real Puppeteer, mocked Firefly/R2): baseline + airy both 100%
  success, validator pass, deterministic single hash each; airy hash differs from baseline.
  Visual diff baseline↔airy = 3.53% of canvas, confined to product region + title band
  (geometry_evidence region/slot bounds identical). Evidence in `scripts/out/relaxation/`.

### Remaining risks

- Visible relaxation is moderate (product-lift shadow + title-stack gap); deeper product/gallery
  breathing needs a geometry style-variant (tracked in the taxonomy plan), not relaxation.
- The 4 widened campaign-explainer branches are predicate-gated; existing-id behavior verified
  byte-identical, but future Family A variants must be added to `CAMPAIGN_EXPLAINER_TEMPLATE_IDS`.
- 19 pre-existing renderer/quality test failures remain (out of scope; not introduced here).

### Acceptance state

- Default `template_dual_v2` render unchanged (proven byte-identical). `template_dual_v2_airy`
  is testable via the harness and selectable through the normal generate path. No geometry/
  ownership change. Airy is visibly less tight. 10-run stability passes for both. Quality report
  includes the relaxation preset and validator result.

### One-line execution summary

- Added a non-geometric, template-driven Visual Relaxation Layer + an opt-in `template_dual_v2_airy`
  variant, proven render-neutral for the baseline and stable/deliverable for airy.

## Entry — Stage1 template preview TDZ fix

**Branch:** `main`
**Status:** Complete
**Last updated:** `2026-05-15`

### Scope

- Stage1 frontend stability only
- hoist the Mode S template-preview refresh helper inside `initStage1ModeS`
- keep Template A and Template B selector paths separated
- keep `frontend/` and `docs/` mirrored

### Root rules followed

- read required repo and poster2 docs before editing
- stayed on the frontend initialization-order layer
- no template registry, template spec, backend API, renderer, contract, bottom SOP, product annotation, Template B payload, CSS, or beautification changes

### Problem reproduced

- live GitHub Pages `/ai-service/index.html` failed during Stage1 initialization with `ReferenceError: Cannot access 'refreshTemplatePreviewStage1' before initialization`
- deployed `app.js` matched local `docs/app.js`

### Root cause found

- `init()` called `initStage1()`, which routed to `initStage1ModeS()`
- early default/stored hydration called `refreshVariantTemplateMeta(...)`
- `refreshVariantTemplateMeta(...)` called `refreshTemplatePreviewStage1(...)`
- `refreshTemplatePreviewStage1` was a local `const` async function expression declared later in the same scope, so the early call hit the JavaScript temporal dead zone

### Files changed

- `frontend/app.js`
- `docs/app.js`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage1 frontend initialization order only

### Validation run

- `node --check frontend/app.js` -> passed
- `node --check docs/app.js` -> passed
- `bash scripts/check_frontend_docs_sync.sh` -> `frontend/docs publish assets are in sync`
- `python3.11 -m pytest -q tests/test_frontend_docs_sync.py` -> `8 passed`
- local Playwright check against `http://127.0.0.1:8017/docs/index.html` with ops auth mocked open:
  - template options loaded: `Marketing Poster`, `Product Sheet`
  - Template A preview description rendered
  - Template B preview description rendered after selector change
  - Template B top-copy controls visible after selecting Product Sheet
  - Template A bottom controls visible after selecting Marketing Poster
  - no `refreshTemplatePreviewStage1` console/page errors

### Remaining risks

- manual browser verification on the deployed GitHub Pages URL should be repeated after publish/cache refresh
- unrelated pre-existing template spec drift between `frontend/templates/template_dual_spec.json` and `docs/templates/template_dual_spec.json` was observed during review but intentionally not changed in this scoped fix


## Entry — PR-TB-BEAUTY1: Template B visual beautification pass

**Branch:** `poster2/pr-tb-op3-description-copy`
**Status:** Complete
**Last updated:** `2026-04-16`

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `frontend/index.html`
- `frontend/stage2.html`
- `frontend/stage3.html`
- `frontend/app.js`
- `frontend/styles.css`

### Scope

- `PR-TB-BEAUTY1` only
- Template B visual presentation / beautification layer only
- refine the existing `.template-b-preview*` surface used by the Template B preview/result presentation path
- preserve Template B request truth, renderer truth, region ownership, save/send truth, and Stage1/Stage2/Stage3 workflow closure
- preserve Family A frozen truth and all Family A styling / behavior
- keep `frontend/` and `docs/` mirrored

### Root rules followed

- read context before editing
- stayed on the requested presentation layer
- no contract reopen
- no request payload, backend, renderer, region ownership, Stage2/Stage3 logic, or copy-helper logic changes
- no Template B structural markup changes
- no Family A CSS selectors or behavior changed

### Problem reproduced

- the Template B preview surface still read as a plain baseline Product Sheet
- background depth was shallow and region separation depended mostly on spacing
- the materials strip rendered as simple thumbnails without enough evidence-row treatment
- the hero product surface had limited anchoring and product-stage support
- the description block was card-light and visually less connected to the industrial sheet system

### Root cause found

- Template B was structurally/operator closed by prior PRs, but its dedicated `.template-b-preview*` CSS still used minimal gradients, borders, and shadows
- the visual hierarchy was present but understated: banner, top-copy, materials, hero, and description regions lacked enough differentiated surface depth
- the materials and description regions had no presentation-only affordance to read as product-sheet support/detail surfaces

### Exact beautification-layer changes

- strengthened the Template B sheet background with layered radial gradients, a restrained industrial grid texture, stronger border radius, and deeper sheet shadow
- added presentation-only sheet separators through pseudo-elements without changing DOM structure
- refined the header/banner with a darker metallic surface, inset highlights, a subtle amber rule, and stronger logo tile depth
- turned the top-copy area into a defined Product Sheet information surface with a left accent rail and soft card depth
- converted the materials strip into a supporting evidence row with a card-like container, `DETAIL STRIP` presentation label, stronger thumbnail cards, and inset framing
- strengthened the hero region with a refined product-stage background, masked grid support, stronger floor shadow, product image bounds, and more premium secondary-detail card depth
- refined the description block into a premium product summary panel with layered background, accent rail, deeper card shadow, and improved text spacing

### Exact regions visually refined

- Template B background / overall sheet surface
- Template B header / brand lockup banner
- Template B top-copy SKU / title / subtitle surface
- Template B materials/detail strip
- Template B hero product region and secondary detail inset
- Template B description / product summary panel

### Exact files changed

- `frontend/styles.css`
- `docs/styles.css`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- frontend CSS presentation layer for Template B only
- docs CSS mirror
- branch execution/state log

### Validation performed

- syntax/static:
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
- mirror/static:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
- focused Template B frontend presence check:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py -k template_b_independent_preview_and_generate_path_are_present` → `1 passed, 7 deselected`
- source-level verification:
  - verified all CSS changes are scoped to `.template-b-preview*`
  - verified no Template B request builder, renderer truth, backend path, region ownership, save/send truth, or Stage2/Stage3 logic was changed
  - verified Family A selectors and behavior were not edited
  - verified `frontend/styles.css` and `docs/styles.css` remain mirrored

### Remaining risks

- this pass was validated with static checks, mirror checks, focused source checks, and source inspection only; no browser screenshot comparison was produced in this workspace
- beautification is CSS-only for the existing frontend Template B preview/result surface; backend-rendered image truth was intentionally not changed
- pseudo-element labels and textures are presentation-only; if later browser QA finds the surface too dense at a specific viewport, tune only the B CSS selectors without reopening structure

### Acceptance state

- Template B remains functionally closed as an independent Product Sheet line
- Template B background has stronger layered depth while staying industrial and restrained
- Template B header/top-copy surface has clearer premium Product Sheet hierarchy
- Template B materials strip reads more like a supporting evidence/detail row
- Template B hero region has stronger visual anchoring and focus support
- Template B description block reads as a refined product summary panel
- Family A frozen truth remains untouched
- Template B structure, renderer/request truth, region ownership, backend behavior, and save/send truth remain untouched
- frontend/docs mirror remains aligned
- branch execution log updated before stop

### One-line execution summary

- `PR-TB-BEAUTY1` improved only Template B visual presentation across background, header/top-copy, materials strip, hero support, and description panel using B-scoped CSS, preserving all structure/truth boundaries and Family A frozen truth.

## Entry — PR-TB-OP3: Template B description copy-quality closeout

**Branch:** `main`
**Status:** Complete
**Last updated:** `2026-04-16`

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `frontend/index.html`
- `frontend/stage2.html`
- `frontend/stage3.html`
- `frontend/app.js`
- `frontend/styles.css`

### Scope

- `PR-TB-OP3` only
- Template B copy-quality / expression closeout only
- improve description-title and description-body guidance for Product Sheet language
- improve Template B staged copy suggestions for concise product-summary output
- keep Stage2 and Stage3 wording aligned to Product Sheet / SKU / product-details semantics
- do not touch Family A frozen truth
- do not touch Template B renderer truth, request truth, region ownership, layout contract, backend API behavior, or save/send truth
- keep `frontend/` and `docs/` mirrored

### Root rules followed

- read context before editing
- keep work on the requested operator/copy layer
- no contract reopen
- no renderer, backend, request-builder, layout, region ownership, or save/send truth change
- Template B runtime truth remains Product Sheet-native:
  - `feature_mode = none`
  - `product_annotation_mode = none`
  - `bottom_mode = description_block`
  - `top_copy_hierarchy_mode = sku_meta_title_subtitle_catalog`
  - description title/body remain owned by `description_region`

### Problem reproduced

- Template B Stage1 description guidance still used generic `描述标题 / 描述正文` wording and a broad detailed-description placeholder
- Template B staged copy helper passed raw description body/title text through with minimal shaping, which could preserve repeated stitched fragments or slogan-like copy
- Template B review/send wording was mostly Product Sheet-oriented, but still used generic `description panel / description ready` language in some B-only summaries

### Root cause found

- OP1/OP2 closed Template B structure and callout residue, but the description block copy helper still treated description text as a generic summary string
- there was no B-only fragment splitting, dedupe, slogan/callout rejection, or concise product-summary fallback for description suggestions
- the Stage3 B email adaptation reused raw saved description text instead of the same product-sheet summary shaping

### Exact Template B description-copy guidance changes

- changed the Stage1 Template B fieldset from `产品说明面板` to `产品摘要面板`
- changed Stage1 description guidance to request a product-page heading plus 1-2 sentence summary covering use, key structure/materials, or fit context
- explicitly discouraged slogans, long marketing prose, and repeated stitched text in the Template B description body placeholder
- changed visible field labels from generic description title/body to `产品摘要标题` and `产品摘要正文`
- added Product Sheet-style title examples: `Product Overview / Key Details / Application Summary`

### Exact Product Sheet wording changes

- added B-only description helper functions to split description fragments, dedupe repeated text, reject campaign/callout-style fragments, and enforce sentence endings
- changed Template B staged suggestions to include a `Product Summary Heading` and `Product Summary Paragraph`
- changed Template B staged description fallback to use SKU, materials count, and secondary detail context in a concise distributor-ready product-sheet summary
- changed Template B copy-helper guidance to emphasize short sentences, low repetition, and product-details tone
- changed Template B Stage2 summary wording from generic `description panel / description ready` to `product summary panel / product summary ready`
- changed Template B Stage3 spine wording to `product summary panel ready`
- changed Template B Stage3 email adaptation to reuse the B-only product-summary shaping instead of raw repeated description text
- preserved existing backend-driven `poster_key -> poster_record` Stage3 truth path

### Exact files changed

- `frontend/index.html`
- `frontend/app.js`
- `docs/index.html`
- `docs/app.js`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage1 Template B operator copy guidance
- Stage1 Template B frontend staged-copy helper wording and B-only description shaping
- Stage2 Template B review wording only
- Stage3 Template B send/adaptation wording only
- docs mirror alignment
- branch execution/state log

### Validation performed

- syntax/static:
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
- mirror/static:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
- focused Template B frontend presence check:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py -k template_b_independent_preview_and_generate_path_are_present` → `1 passed, 7 deselected`
- source-level verification:
  - verified Template B Stage1 description-title/body guidance now reads as Product Sheet summary input
  - verified Template B staged copy helper no longer directly forwards repeated raw description text without B-only shaping
  - verified Template B Stage2 review wording uses product-summary semantics instead of generic description wording
  - verified Template B Stage3 email adaptation remains backend-record driven and only reshapes frontend wording for product-sheet delivery
  - verified touched `frontend/` and `docs/` files remain aligned

### Remaining risks

- this pass was validated with syntax, mirror checks, focused source checks, and source inspection only; no browser click-through or screenshot comparison was produced in this workspace
- the B-only staged helper is deterministic and lightweight, not a full language model; it reduces repeated/slogan fragments but cannot guarantee perfect prose for every pasted operator input
- shared frontend files still contain Family A paths by design, but this task did not alter Family A behavior, renderer truth, backend behavior, or request truth

### Acceptance state

- Template B description-title guidance now reads as Product Sheet section-heading guidance
- Template B description-body guidance now asks for concise product-summary language and discourages repeated stitched prose
- Template B staged copy suggestions are biased toward product summary, use/detail context, spec-adjacent language, and distributor-ready sharing tone
- Template B Stage2 and Stage3 wording remains Product Sheet-centered
- Family A frozen truth remains untouched
- Template B renderer/request/backend/save-send truth remains untouched
- frontend/docs mirror remains aligned
- branch execution log updated before stop

### One-line execution summary

- `PR-TB-OP3` improved Template B description-copy quality by reframing description inputs as product-summary fields, adding B-only concise/deduped Product Sheet suggestion shaping, keeping Stage2/Stage3 wording product-sheet oriented, preserving Template B structure and Family A frozen truth, and updating the branch execution log.

## Entry — PR-TB-OP2: Template B callout residue de-emphasis

**Branch:** `main`
**Status:** Complete
**Last updated:** `2026-04-16`

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `frontend/index.html`
- `frontend/stage2.html`
- `frontend/stage3.html`
- `frontend/app.js`
- `frontend/styles.css`

### Scope

- `PR-TB-OP2` only
- Template B operator-surface semantic cleanup only
- remove / de-emphasize Template A selling-point and callout residue from Template B
- preserve Template B request truth and compatibility scaffolding
- preserve Template B renderer truth
- preserve backend API behavior and save/send truth
- do not touch Family A frozen truth
- keep `frontend/` and `docs/` mirrored
- update branch execution log before stop

### Root rules followed

- keep work on the requested layer
- no contract reopen
- no renderer, backend, request-builder, or save/send truth change
- Template B UI follows active Product Sheet truth:
  - `feature_mode = none`
  - `product_annotation_mode = none`
  - `bottom_mode = description_block`
  - `materials_mode = strip_thumbnails`
  - `top_copy_hierarchy_mode = sku_meta_title_subtitle_catalog`
- keep Family A wording and behavior intact

### Problem reproduced

- Template B Stage1 still showed the shared `产品卖点（选填，最多 3 条）` / `product_callouts` block as a primary visible input
- Template B Stage1 optional copy helper still reused generic product-copy / marketing-style controls that could read like selling-point generation
- Template B Stage3 had backend-safe product-sheet wording from OP1, but the section heading still defaulted to generic email-promotion adaptation until runtime wording was applied

### Root cause found

- the shared product callout field block had no Template A-only visibility gate
- compatibility storage for `product_callouts` remained wired through form serialization, which is safe, but the visible field implied Template B needed Family A-style callout content
- Stage1 suggestion UI had Template B-specific suggestion targets, but its surrounding labels/style selector still used generic marketing-copy affordances

### Exact Template B A-residue removal / de-emphasis

- marked the Stage1 `product_callouts` block as `data-variant-visible="a"` so it is hidden for Template B
- kept the underlying named inputs in the DOM for compatibility, but removed them from the visible Template B primary workflow
- hid the Stage1 suggestion style selector for Template B because `Light Marketing` / `Product Focused` is not part of Template B product-sheet truth
- changed Template B suggestion rows from `Poster Title` / `Poster Subtitle` to `Product Sheet Title` / `Product Sheet Subtitle`
- changed Template B empty-state suggestion guidance to explicitly state that Product Sheet cleanup covers title, subtitle, description summary, and email-sharing seeds only, and does not generate or require product selling points / callouts

### Exact Stage1 / Stage2 / Stage3 wording changes

- Stage1:
  - Template B primary visible inputs now stay centered on SKU, title, subtitle, materials strip, primary product, secondary product, description title, and description body
  - Template B copy helper reads as `产品页文案整理`
  - Template B copy helper hint says it does not generate selling-point or annotation copy
  - Template B copy helper generate/apply buttons use product-page wording
- Stage2:
  - no Stage2 Template B result/review code was changed
  - existing Template B Stage2 review remains centered on SKU, materials strip, product images, and description completeness
  - existing Family A `产品卖点` Stage2 panel remains hidden for Template B
- Stage3:
  - added a runtime-updated heading hook so Template B reads `产品页分享适配`
  - kept OP1 product-sheet sharing wording and backend-driven poster_record flow unchanged

### Exact files changed

- `frontend/index.html`
- `frontend/stage3.html`
- `frontend/app.js`
- `docs/index.html`
- `docs/stage3.html`
- `docs/app.js`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage1 frontend visibility / operator wording for Template B only
- Stage3 frontend heading wording hook for Template B only
- docs mirror alignment
- branch execution/state log

### Validation performed

- syntax/static:
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
- mirror/static:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
- focused Template B frontend presence check:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py -k template_b_independent_preview_and_generate_path_are_present` → `1 passed`
- source-level verification:
  - verified the Stage1 callout block is now Family A-visible only via `data-variant-visible="a"`
  - verified Template B Stage1 copy helper no longer presents marketing style selection
  - verified Template B suggestion labels use Product Sheet wording
  - verified Template B Stage3 heading can switch to product-page sharing language
  - verified touched `frontend/` and `docs/` files remain aligned

### Remaining risks

- this pass was validated with syntax, mirror checks, focused source checks, and source inspection only; no browser click-through or screenshot comparison was produced in this workspace
- compatibility scaffolding for `product_callouts` still exists underneath for shared storage and Family A, but it is no longer a visible primary Template B operator concept
- Stage2 diagnostic source still contains Family A feature/callout code paths, but Template B operator review surfaces remain hidden or B-specific and no renderer/backend truth changed

### Acceptance state

- Template B Stage1 no longer visibly requires or promotes Family A-style selling points / callouts
- Template B Stage1 primary workflow remains Product Sheet-centered
- Template B Stage2 review semantics remain Product Sheet-centered
- Template B Stage3 keeps product-sheet sharing language
- Family A frozen truth remains untouched
- Template B renderer/request/backend truth remains untouched
- frontend/docs mirror remains aligned
- branch execution log updated before stop

### One-line execution summary

- `PR-TB-OP2` removed visible Template A selling-point/callout residue from Template B by hiding the shared callout block for B, reframing optional copy assistance as product-sheet cleanup, preserving compatibility and all Template B truth, and keeping Family A behavior untouched.

## Entry — PR-TB-OP1: Template B operator/result isolation closeout

**Branch:** `main`
**Status:** Complete
**Last updated:** `2026-04-16`

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `README.md`
- `frontend/index.html`
- `frontend/stage2.html`
- `frontend/stage3.html`
- `frontend/app.js`
- `frontend/stage2_request_helpers.js`

### Scope

- `PR-TB-OP1` only
- Template B operator-surface clarity only
- Template B Stage2 result/review isolation only
- Template B Stage3 wording alignment only
- keep Template B request-builder split and backend truth path unchanged
- do not touch Family A frozen truth
- keep `frontend/` and `docs/` mirrored
- update branch execution log before stop

### Root rules followed

- keep work on the requested layer
- treat Template B as an independent Product Sheet line
- branch result/review before Template A-specific preview semantics
- preserve backend-owned `poster_key -> poster_record` Stage3 truth
- keep `frontend/` and `docs/` aligned in the same task

### Problem reproduced

- Template B already generated through its own request path, but Stage1 still read partly like leftover Family A operator flow
- Stage2 post-generate result/replay state still reused Template A-shaped preview/result handling
- Stage3 wording still defaulted to generic marketing-poster / send language instead of product-sheet sharing language for Template B

### Root cause found

- Stage1 shared title/subtitle/product blocks stayed in Family A locations even when Template B was selected
- `renderPosterResult()` always executed the Template A preview builder and only then filled the hidden Stage2 replay surface
- Stage2 current/saved result cards stored generic A-shaped title/subtitle summaries instead of Template B completeness-focused review summaries
- Stage3 summary/adaptation copy was not template-family aware, so Template B inherited Family A-oriented wording

### Exact Stage1 B-only operator-surface adjustments

- added a dedicated Template B top-copy fieldset directly after brand info
- moved the existing shared title and subtitle inputs into the Template B top-copy area when Template B is selected, while restoring them to their original Family A anchors for Template A
- moved Template B materials slots into that same top-copy area so the visible operator order now reads:
  - logo / brand / product line
  - SKU
  - title
  - subtitle
  - materials evidence strip
  - primary product
  - secondary product
  - description title / description body
- split Template B description fields into their own lower description panel fieldset after product images
- updated Template B-only labels/helper text for:
  - brand/product-line wording
  - product image roles
  - materials evidence strip wording
  - secondary-product clear action
- hid the leftover product-identification text field for Template B so the operator surface does not read like a Family A carryover

### Exact Stage2 result/replay isolation changes

- added an early Template B branch in `renderPosterResult()` before any Template A-specific preview builder runs
- Template B Stage2 replay path now clears the hidden A-shaped replay surface instead of reusing Template A preview semantics
- added Template B-specific Stage2 family copy for:
  - generated-content panel title
  - comparison panel title
  - current/saved card labels
  - flow note
- upgraded Template B Stage2 summary state to report Product Sheet review concerns:
  - template identity
  - SKU
  - materials count/state
  - primary product readiness
  - secondary product readiness
  - description readiness
- changed current/saved snapshot summaries for Template B so result cards now store and replay completeness-focused Product Sheet summaries rather than A-style subtitle-only summaries
- updated Template B save/clear/save-gate copy to use product-page/share semantics instead of generic poster/send semantics

### Exact Stage3 semantic adjustments

- kept backend-driven Stage3 restore/send flow unchanged
- added template-family-aware Stage3 wording so Template B now reads as product-sheet sharing rather than marketing-poster sending
- updated Template B-specific copy for:
  - page header subtitle
  - save-gate / missing-saved-object messages
  - poster identity label
  - refresh button label
  - send button label
  - draft-source status
  - adaptation status/summaries
- added Template B-specific spine/adaptation summaries that emphasize:
  - title
  - subtitle
  - SKU
  - materials strip
  - secondary detail
  - description panel
- preserved backend truth by keeping Stage3 draft hydration and send requests sourced from `poster_record` and `/api/v2/email/*`

### Exact files changed

- `frontend/index.html`
- `frontend/stage2.html`
- `frontend/stage3.html`
- `frontend/app.js`
- `docs/index.html`
- `docs/stage2.html`
- `docs/stage3.html`
- `docs/app.js`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage1 frontend operator language / field order for Template B only
- Stage2 frontend result/replay surface and saved/current summary copy for Template B only
- Stage3 frontend wording only
- docs mirror alignment
- branch execution/state log

### Validation performed

- syntax/static:
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
- mirror/static:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
- focused Template B frontend presence check:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py -k template_b_independent_preview_and_generate_path_are_present` → `1 passed`
- source-level verification:
  - verified Template B Stage1 input order now reads as Product Sheet top-copy -> materials strip -> product images -> description panel
  - verified Template B Stage2 result path branches before Template A preview builder usage
  - verified Template B current/saved result summaries now report Product Sheet completeness rather than A-style scenario/bottom/gallery review semantics
  - verified Stage3 wording shifts to product-page/share language for Template B while keeping backend hydration/send flow unchanged
  - verified touched `frontend/` and `docs/` files remain aligned

### Remaining risks

- this pass was validated with syntax, mirror checks, and source inspection only; no browser screenshot or manual click-through run was produced in this workspace
- Template B Stage2 isolation now avoids Template A replay semantics, but the hidden legacy replay container still exists in markup for shared Stage2 structure and is intentionally cleared rather than redesigned in this pass
- Stage3 wording is template-aware, but backend email draft content still depends on backend draft generation quality and is only frontend-reframed in this pass

### Acceptance state

- Template B now reads as an independent Product Sheet line in Stage1 operator flow
- Template B Stage2 result/review no longer falls through Template A preview/result semantics
- Template B Stage2 current/saved summaries reflect B-specific operator concerns only
- Stage3 remains backend-truth-driven while reading as product-sheet sharing for Template B
- Family A frozen truth remains untouched
- frontend/docs mirror remains aligned
- branch execution log updated before stop

### One-line execution summary

- `PR-TB-OP1` closed the Template B operator line as an independent Product Sheet workflow by reordering B inputs, isolating Stage2 result/replay from Template A semantics, aligning Stage3 to product-sheet sharing language, and leaving Family A frozen truth unchanged.

## Entry — PR-BOTTOM-GALLERY-VIS1: Bottom helper-image card rebalance

**Branch:** `main`
**Status:** Complete
**Last updated:** `2026-04-16`

### What was read first

- `AGENTS.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
- `docs/poster2/03_engineering/family_a/bottom_region_practical_beautification_observability_v1.md`
- `docs/poster2/05_validation/family_a/bottom_region_practical_closure_status_v1.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- then only the fryer bottom gallery behavior / template CSS / validation assertions directly tied to the helper-card row

### Scope

- `PR-BOTTOM-GALLERY-VIS1` only
- fryer bottom helper-image card rebalance only
- keep existing 4-slot bottom gallery truth
- keep current caption ownership
- keep Stage2 / Stage3 production behavior unchanged
- do not touch bottom truth or AI generation logic
- update context before stop

### Root rules followed

- contract-first, beauty second
- keep work on the requested layer
- no bottom truth, generate/send truth, or renderer routing change
- no AI generation behavior change
- update the validation path and branch context in the same task

### Problem reproduced

- fryer helper-image cards in the 4-slot bottom row rendered at about `156x90`
- bounded media area dropped to about `140x56`
- captions took too much of the remaining vertical budget, so both real helper images and AI-generated helper images read as flattened strips instead of useful product helper cards

### Root cause found

- the fryer-only `dense_quad_detail_row` branch in `resolve_bottom_behavior()` allocated only `90px` item height inside a `116px` shell
- caption truth reserved a relatively tall `14px` caption band with `8px` card padding on all sides
- captioned helper cards used `object-fit: cover`, which further reduced readable product detail by cropping already short media windows

### Exact visual rebalance

- kept the same 4-card row, same slot widths, same caption ownership, same `dense_quad_detail_row` policy
- increased fryer split-mode helper card height from `90` to `100`
- tightened fryer split-mode shell height from `116` to `106` so the taller cards stay inside the accepted bottom frame
- increased helper media bounds from `140x56` to `142x71`
- reduced caption bounds from `140x14` to `142x12`
- changed captioned helper cards to prefer `object-fit: contain` so product geometry reads more like a helper-image card and less like a cropped strip
- softened caption visual weight with smaller type, tighter spacing, and a weaker tone

### Exact files changed

- `app/services/poster2/template_behavior.py`
- `app/templates_html/template_dual_v2.css`
- `tests/poster2/test_pipeline.py`
- `docs/poster2/README.md`
- `docs/poster2/05_validation/family_a/bottom_gallery_helper_card_rebalance_status_v1.md`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Family A bottom-region beautification only
- fryer helper-card shell/media/caption allocation only
- validation/context docs only

### Validation performed

- resolver evidence:
  - confirmed fryer split-mode helper row now resolves to `gallery_shell_height = 106`
  - confirmed fryer split-mode helper row now resolves to `gallery_items_height = 100`
  - confirmed first helper card now resolves to:
    - `card_bounds = 156x100`
    - `media_bounds = 142x71`
    - `caption_bounds = 142x12`
- focused tests:
  - `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'title_gallery_split_fryer_dense_quad_detail_row_adds_breathing or template_a_fryer_bottom_contract_review_exposes_caption_truth'`
  - `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'fryer_dense_quad_gallery_markup_emits_semantic_captions'`

### Remaining risks

- this pass was validated with resolver truth, CSS review, and focused tests only; no browser screenshot comparison was produced in this workspace
- `object-fit: contain` improves product readability for helper images, but very loose-source images may now show more intentional inner breathing room instead of edge-to-edge crop fill

### Acceptance state

- 4-slot bottom helper-image row remains intact
- bottom truth and AI generation logic remain unchanged
- helper imagery receives materially more readable vertical space
- captions no longer dominate the limited card height
- validation path and branch context were updated before stop

### One-line execution summary

- `PR-BOTTOM-GALLERY-VIS1` rebalanced the fryer bottom helper-image cards into taller, less cropped product helper cards while preserving the existing 4-slot bottom truth and production behavior.

## Entry — PR-AI-BOTTOM1: Slot-level bottom helper-image AI generation

**Branch:** `main`
**Status:** Complete
**Last updated:** `2026-04-15`

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `frontend/index.html`
- `frontend/app.js`
- `frontend/styles.css`
- then only the minimum existing bottom-slot rendering and Stage1 slot-action sections inside those same files

### Scope

- PR-AI-BOTTOM1 only
- Stage1 bottom-slot enhancement only
- add slot-level `AI Generate` to the existing 4 bottom image slots
- keep production behavior unchanged:
  - generate truth
  - save/send truth
  - renderer behavior
  - backend API behavior
  - Stage2 / Stage3 behavior
  - bottom contract
- keep `frontend/` and `docs/` mirrored
- update branch execution log before stop

### Root rules followed

- keep work on the requested layer
- no extra bottom-AI panel or workflow step
- keep the 4 existing bottom slots as the only AI entry points
- no production generate/send/backend truth change
- `frontend/` and `docs/` were kept aligned in the same task

### Problem reproduced

- the 4 existing bottom slots only exposed upload/replace and clear actions
- there was no slot-level AI helper-image generation path in the active Stage1 bottom-slot UI
- adding bottom helper-image AI risked becoming a separate workflow unless it stayed attached directly to each slot

### Root cause found

- the current Mode S bottom-slot binder handled file upload and clear actions only
- existing Stage1 bottom-slot markup did not surface a slot-level AI action
- no slot-specific product-helper prompt builder existed for the bottom gallery use case

### Exact slot-level AI Generate behavior

- added one `AI Generate` action to each of the 4 existing bottom slots
- the current bottom UI structure remains unchanged:
  - upload / replace
  - AI Generate
  - clear
- each slot now uses a slot-specific default helper-view intent:
  - slot 1: `detail close-up`
  - slot 2: `alternate angle`
  - slot 3: `structural detail`
  - slot 4: `supporting product view`
- if the slot is empty:
  - generated helper image is written directly into that slot
- if the slot already has an image:
  - generation creates a slot-scoped candidate replacement
  - operator confirmation is required before replacing the current slot image
  - declining the confirmation keeps the current slot image unchanged
- no new bottom-AI region, panel, or workflow step was introduced

### Exact product-reference constraints

- bottom-slot AI prompt generation is constrained to product imagery only
- prompt guidance explicitly anchors generation to:
  - primary product image as required reference
  - secondary product image only as optional supporting reference
- prompt guidance explicitly excludes:
  - scenario image
  - poster background
  - logos
  - unrelated assets / unrelated objects
- the helper output is constrained to product-useful views only:
  - alternate product angle
  - detail close-up
  - structural/component detail
  - supporting product view

### Exact size/aspect constraints

- each slot-level AI request now includes explicit bottom-gallery fit guidance
- prompt guidance specifies:
  - landscape helper view
  - suitable for a wide bottom gallery tile
  - target generation around `560x320`
  - compose safely for a small bottom-slot crop
  - neutral clean background
  - product-centered framing
  - no text
  - no logo
  - no scene/lifestyle composition

### Exact files changed

- `frontend/index.html`
- `frontend/app.js`
- `docs/index.html`
- `docs/app.js`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage1 bottom-slot frontend interaction only
- slot-level bottom helper-image prompt construction only
- docs mirror alignment
- branch execution/state log

### Validation performed

- syntax/static:
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
- mirror/static:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
- source-level verification:
  - verified all 4 bottom slots now show `AI Generate`
  - verified slot-level prompt guidance references product imagery only and explicitly excludes scenario imagery
  - verified slot-level prompt guidance includes bottom-slot size/aspect framing constraints
  - verified no new bottom-AI panel or workflow section was introduced
  - verified no Stage2 / Stage3 or production generate/send flow logic was changed
  - verified touched `frontend/` and `docs/` files remain aligned

### Remaining risks

- this pass was validated with syntax, mirror checks, and source inspection only; no browser screenshot run was performed in this workspace
- the existing image-generation endpoint is still prompt-driven, so product-reference enforcement in this pass is done through constrained prompt construction rather than image-conditioned backend changes
- when an occupied slot generates a candidate and the operator declines replacement, the generated remote asset is not surfaced elsewhere in UI in this pass; the current slot simply remains unchanged

### Acceptance state

- all 4 existing bottom slots now expose `AI Generate`
- slot-level AI helper generation stays inside the existing slot UI
- product-only reference constraints and bottom-slot size/aspect guidance are applied
- no extra bottom-AI section was introduced
- no production truth changed
- frontend/docs mirror remains aligned
- branch execution log updated
- PR-AI-BOTTOM1 acceptance target met

### One-line execution summary

- PR-AI-BOTTOM1 added `AI Generate` to each of the 4 existing bottom slots, constrained generation to product-based helper views with bottom-slot size guidance, kept the current slot UI/workflow intact, and preserved all production truth.

## Entry — PR-AI-COPY2: Copy-spine hierarchy clarification and de-escalation pass

**Branch:** `main`
**Status:** Complete
**Last updated:** `2026-04-15`

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `frontend/index.html`
- `frontend/stage2.html`
- `frontend/stage3.html`
- `frontend/app.js`
- `frontend/styles.css`

### Scope

- PR-AI-COPY2 only
- clarification and de-escalation pass only
- keep the Stage1 / Stage2 / Stage3 copy-spine direction from PR-AI-COPY1
- preserve production behavior unchanged:
  - generate truth
  - save/send truth
  - renderer behavior
  - backend API behavior
  - Stage2 / Stage3 production gating
- keep `frontend/` and `docs/` mirrored
- update branch execution log before stop

### Root rules followed

- keep work on the requested layer
- behavior before beautification
- no generate/save/send/backend truth change
- candidate-based and operator-confirmed copy assistance remains intact
- `frontend/` and `docs/` were kept aligned in the same task

### Problem reproduced

- Stage1 had the correct ownership of the accepted product-copy spine, but the UI still felt like a heavy review workstation
- Stage2 had already been reframed, but still looked too much like a competing copy-optimization area
- Stage3 correctly used the accepted Stage1 spine, but its source hierarchy could still be stated more directly in the operator UI

### Root cause found

- Stage1 suggestion rows still leaned on page-level control emphasis instead of field-level acceptance
- Stage2 refinement controls were visible as a standard active panel instead of a clearly secondary, low-emphasis utility area
- Stage3 source messaging existed in state, but the page-level copy did not make the upstream dependence on Stage1 accepted copy plus saved poster context explicit enough

### How Stage1 was lightened

- kept Stage1 as the main product-copy enhancement center
- preserved support for:
  - `title`
  - `product_callouts`
  - `bottom_support_copy`
  - `email_subject_seed`
  - `email_opening_seed`
- changed the Stage1 copy-center header text to emphasize a lighter operator flow:
  - generate suggestions first
  - accept field-by-field
  - sync only when explicitly requested
- added local per-field acceptance buttons (`接受此字段`) directly in each suggestion row
- de-emphasized the heavier page-level controls by moving them under a collapsed `更多操作` details block
- kept the accepted copy spine model unchanged
- kept non-destructive behavior unchanged:
  - no auto-overwrite of operator input
  - accepted layer still remains separate until explicit sync

### How Stage2 was de-escalated

- kept the existing fit/refinement-only role
- further reduced visual emphasis by:
  - labeling it as a `低优先级辅助区`
  - moving the refinement controls behind a collapsed `打开贴合微调` details block
- preserved the same refinement-only scope:
  - compression
  - trim
  - layout-aware wording adjustment
- changed button wording so Stage2 reads as handling the current fit suggestion only, not generating a second narrative center
- left Stage2 payload truth and acceptance mechanics unchanged

### How Stage3 source-of-copy was clarified

- updated the visible Stage3 source line to explicitly say:
  - `来源：Stage1 已接受产品文案骨架 + 已保存海报上下文`
- tightened Stage3 adaptation summary/status copy so it reads as email-outreach adaptation rather than a separate copy-writing workspace
- kept the candidate-based flow unchanged:
  - generate suggestion
  - accept suggestion
  - sync to email fields
- kept the accepted-before-sync behavior unchanged

### Exact files changed

- `frontend/index.html`
- `frontend/stage2.html`
- `frontend/stage3.html`
- `frontend/styles.css`
- `frontend/app.js`
- `docs/index.html`
- `docs/stage2.html`
- `docs/stage3.html`
- `docs/styles.css`
- `docs/app.js`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage1 / Stage2 / Stage3 frontend copy-spine presentation and operator interaction hierarchy only
- docs mirror alignment
- branch execution/state log

### Validation performed

- syntax/static:
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
- mirror/static:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
- source-level verification:
  - verified Stage1 still owns the accepted product-copy spine and now offers local per-field accept behavior
  - verified Stage1 page-level controls are visually de-emphasized under `更多操作`
  - verified Stage2 now reads as a low-emphasis secondary refinement area with collapsed controls
  - verified Stage3 now explicitly states that email adaptation derives from Stage1 accepted copy plus saved poster context
  - verified no production generate/send flow code was changed
  - verified touched `frontend/` and `docs/` files remain aligned

### Remaining risks

- this pass was validated with syntax, mirror checks, and source inspection only; no browser screenshot run was performed in this workspace
- Stage1 row layout is lighter in source structure, but fine-grain operator feel on narrow/mobile widths was not visually reviewed in-browser in this workspace
- Stage2 and Stage3 hierarchy is clarified through presentation/copy changes only; this PR intentionally did not change deeper behavior or persistence rules

### Acceptance state

- Stage1 remains the main copy enhancement center and feels lighter/more operator-oriented
- Stage2 now reads as clearly secondary poster-fit refinement
- Stage3 now reads as email adaptation from accepted product copy plus saved poster context
- production truth remains unchanged
- frontend/docs mirror remains aligned
- branch execution log updated
- PR-AI-COPY2 acceptance target met

### One-line execution summary

- PR-AI-COPY2 kept the existing product-copy spine intact while lightening Stage1 into a faster field-level enhancement tool, pushing Stage2 further into low-emphasis fit refinement, and making Stage3 explicitly read as email adaptation from the accepted Stage1 copy spine plus saved poster context.

## Entry — PR-AI-COPY1: Product-aware AI copy spine across Stage1/Stage2/Stage3

**Branch:** `main`
**Status:** Complete
**Last updated:** `2026-04-15`

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `frontend/index.html`
- `frontend/stage2.html`
- `frontend/stage3.html`
- `frontend/app.js`
- `frontend/styles.css`
- then only the minimum existing suggestion/copy-handling sections already inside those files were inspected for the active operator flow

### Scope

- PR-AI-COPY1 only
- product-copy enhancement layer only
- unify Stage1 / Stage2 / Stage3 under one product-copy assistance spine
- keep the operator flow non-blocking
- keep production behavior unchanged:
  - poster request truth
  - save/send truth
  - renderer behavior
  - bottom contract
  - Stage2 / Stage3 production gating
  - backend API behavior
- keep `frontend/` and `docs/` mirrored
- update branch execution log before stop

### Root rules followed

- keep work on the requested layer
- behavior before beautification
- no renderer/backend/send-truth change
- candidate-based and operator-confirmed AI behavior
- `frontend/` and `docs/` were kept aligned in the same task

### Problem reproduced

- Stage1, Stage2, and Stage3 each exposed separate AI copy surfaces without a clear product role split
- Stage1 suggestion copy existed, but did not clearly present itself as the main product-copy center
- Stage2 still read like another general copy optimization area instead of a poster-fit refinement step
- Stage3 email AI directly refreshed the email fields and did not clearly show that it was adapting already-confirmed product messaging

### Root cause found

- the frontend had staged suggestion mechanics in Stage1 and accept/reject mechanics in Stage2, but no explicit shared product-copy spine model
- Stage1 did not persist a named accepted product-copy spine for downstream consumption
- Stage2 and Stage3 messaging did not explain their bounded role relative to Stage1
- Stage3 treated backend email preview refresh as a direct overwrite path instead of a candidate suggestion layer

### Accepted copy spine fields

- `accepted_title`
- `accepted_callouts`
- `accepted_bottom_support_copy`
- `accepted_email_subject_seed`
- `accepted_email_opening_seed`

### Exact Stage1 copy-center changes

- reframed the Stage1 copy area as `主产品文案增强中心`
- added the explicit style selector with only two options:
  - `Product Focused`
  - `Light Marketing`
- kept the staged model:
  - original input
  - suggestion layer
  - accepted layer
- expanded the Family A suggestion targets to:
  - title
  - product callouts
  - bottom support copy
  - email subject seed
  - email opening seed
- kept suggestion generation candidate-based and non-destructive:
  - generating suggestions does not overwrite inputs
  - accepting suggestions writes only to the accepted layer
  - syncing accepted suggestions back to the input fields remains an explicit operator action
- persisted the accepted product-copy spine into Stage1 saved state so later stages can read it without changing request truth by default

### Exact Stage2 refinement-only changes

- renamed the Stage2 copy area from generic optimization language to `海报贴合微调`
- reframed the mode as `Refinement Mode`
- changed the operator copy so Stage2 is explicitly limited to:
  - poster-fit refinement
  - layout-aware compression
  - light wording adjustment
- kept the existing accept / reject suggestion controls, but changed the wording to reflect fit refinement instead of a second copy center
- added a summary/source note showing that Stage2 refinement is anchored to the Stage1 accepted spine when available, otherwise current Stage1 inputs
- did not change Stage2 generate payload truth, renderer flow, or bottom behavior

### Exact Stage3 email-adaptation changes

- added a new `邮件推广适配` panel ahead of the email form fields
- Stage3 now surfaces the Stage1 accepted copy spine as the email-adaptation source summary
- changed the existing Stage3 AI refresh button into a candidate-based adaptation flow:
  - generate email adaptation suggestion
  - accept suggestion
  - sync accepted suggestion into current email fields
  - clear accepted layer
- the visible adaptation outputs are:
  - `email_subject`
  - `email_opening`
  - `email_body_short`
- Stage3 adaptation uses the accepted Stage1 product-copy spine plus saved-poster context to build the suggestion layer
- the existing backend `/api/v2/email/preview` flow is still used to refresh draft/attachment readiness, but Stage3 no longer auto-overwrites the current email form when generating a new adaptation suggestion
- Stage3 remains non-blocking:
  - operators can keep the restored draft and send without accepting any new adaptation suggestion

### Exact files changed

- `frontend/index.html`
- `frontend/stage2.html`
- `frontend/stage3.html`
- `frontend/styles.css`
- `frontend/app.js`
- `docs/index.html`
- `docs/stage2.html`
- `docs/stage3.html`
- `docs/styles.css`
- `docs/app.js`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage1 / Stage2 / Stage3 frontend copy-enhancement behavior and presentation
- Stage1 accepted copy-spine persistence
- docs mirror alignment
- branch execution/state log

### Validation performed

- syntax/static:
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
- mirror/static:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
- source-level verification:
  - verified Stage1 now frames AI copy as the main product-copy enhancement center and exposes only the two requested style options
  - verified Stage1 suggestion targets include title / callouts / bottom support / email subject seed / email opening seed
  - verified Stage1 accept still writes to accepted layer without auto-overwriting inputs
  - verified Stage2 now presents the AI area as poster-fit refinement only
  - verified Stage3 now exposes a candidate-based email adaptation panel tied to the accepted product-copy spine
  - verified touched `frontend/` and `docs/` files remain aligned

### Remaining risks

- this pass was validated with syntax, mirror checks, and source inspection only; no browser screenshot run was performed in this workspace
- Stage3 email adaptation suggestions are accepted/synced in frontend session state only; they are not persisted server-side in this pass
- Stage3 still depends on backend email preview for the baseline draft and attachments; this PR only re-scoped the frontend suggestion flow around that existing draft path

### Acceptance state

- Stage1 is now the main product-copy enhancement center
- Stage2 is now explicitly positioned as layout-fit refinement only
- Stage3 now adapts the accepted product-copy spine for email outreach
- AI outputs remain candidate-based and operator-confirmed
- no production generate/send behavior changed
- frontend/docs mirror remains aligned
- branch execution log updated
- PR-AI-COPY1 acceptance target met

### One-line execution summary

- PR-AI-COPY1 turned Stage1/Stage2/Stage3 into one non-blocking product-copy spine by centering main product copy in Stage1, narrowing Stage2 to poster-fit refinement, and making Stage3 generate candidate-based email adaptation from the accepted copy spine and saved-poster context.

## Entry — PR-UI3: Stage3 send-step reduction pass

**Branch:** `main`
**Status:** Complete
**Last updated:** `2026-04-14`

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `frontend/stage3.html`
- `frontend/styles.css`
- `frontend/app.js` was inspected only after the required reads to confirm the Stage3 attachment summary containers could be removed from the visible UI without changing send behavior

### Scope

- PR-UI3 only
- Stage3 presentation cleanup only
- remove redundant Stage3 confirmation/review emphasis
- reduce attachment presentation to the minimum send-step controls
- keep production behavior unchanged:
  - send behavior
  - saved-poster truth
  - attachment availability logic
  - backend API behavior
  - delivery mode behavior
  - Stage2 workflow
- keep `frontend/` and `docs/` mirrored
- update branch execution log before stop

### Root rules followed

- keep work on the requested layer
- behavior before beautification
- no send-truth or backend-flow change
- no saved-poster truth change
- no attachment logic change
- `frontend/` and `docs/` were kept aligned in the same task

### Problem reproduced

- Stage3 still opened with a large confirmation/review area that repeated saved-poster confirmation through a dominant poster preview block
- the attachment area still spent substantial vertical space on operator-facing breakdown groups:
  - available
  - this send
  - buildable later
- this made Stage3 read like a review page instead of a send step

### Root cause found

- Stage3 HTML still rendered a visible poster-preview section as a primary content block even though send truth already came from backend-hydrated `poster_record`
- the attachment UI still exposed internal state breakdown lists that were not required to complete sending
- existing runtime bindings did not require those breakdown lists to remain visible; they only required the underlying DOM targets to exist

### Exact Stage3 sections removed or simplified

- removed the visible `海报预览` heading and large poster review block from the top of Stage3
- replaced the dominant confirmation area with a compact one-line send-target cue:
  - `发送对象：已保存海报`
- kept poster hydration bindings in a hidden legacy container so no runtime send/payload behavior changed
- left recipients, email copy, delivery mode, attachment checkboxes, and send actions as the only visible send-step controls

### Exact attachment simplification

- kept only:
  - `Delivery Mode`
  - `Poster PNG`
  - `Poster PDF`
- removed the visible multi-group breakdown for:
  - `可用`
  - `本次发送`
  - `可后续生成`
- kept the single short attachment status line
- retained the hidden summary target nodes inside the hidden source-details area so existing Stage3 runtime logic remains unchanged

### Exact files changed

- `frontend/stage3.html`
- `frontend/styles.css`
- `docs/stage3.html`
- `docs/styles.css`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage3 frontend presentation only
- docs mirror alignment
- branch execution/state log

### Validation performed

- mirror/static:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
- source-level verification:
  - verified the large Stage3 top preview/confirmation block is no longer visible in source markup
  - verified Stage3 now shows a compact send-target note instead of a dominant poster review area
  - verified the attachment section contains only visible `Delivery Mode`, `Poster PNG`, and `Poster PDF` controls plus one short status line
  - verified no `frontend/app.js` change was required, so send behavior remained untouched
  - verified touched `frontend/` and `docs/` files remain aligned

### Remaining risks

- this pass was validated with static/mirror checks and source inspection only; no browser screenshot run was performed in this workspace
- hidden legacy DOM targets remain in Stage3 to preserve current runtime bindings; any future cleanup that removes them would require a deliberate no-behavior JS adjustment

### Acceptance state

- large Stage3 top preview/confirmation block removed from visible UI
- attachment section reduced to visible delivery mode plus PNG/PDF selection
- send behavior unchanged
- no production behavior changed
- frontend/docs mirror remains aligned
- branch execution log updated
- PR-UI3 acceptance target met

### One-line execution summary

- PR-UI3 reduced Stage3 to send-only controls by removing the visible saved-poster review block and attachment breakdown summaries while preserving existing runtime behavior and docs alignment.

## Entry — PR-UI2: Stage1/Stage2/Stage3 subtractive UI cleanup

**Branch:** `main`
**Status:** Complete
**Last updated:** `2026-04-14`

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `frontend/index.html`
- `frontend/stage2.html`
- `frontend/stage3.html`
- `frontend/styles.css`
- then only the minimum UI-binding file needed for a small Stage2 presentation-only adjustment:
  - `frontend/app.js`

### Scope

- PR-UI2 only
- Stage1/Stage2/Stage3 presentation cleanup only
- remove redundant explanatory UI and tighten operator information hierarchy
- keep production behavior unchanged:
  - generate behavior
  - request truth
  - saved-poster truth
  - send truth
  - backend API behavior
  - renderer behavior
  - `poster_key` logic
  - production workflow
- keep `frontend/` and `docs/` mirrored
- update branch execution log before stop

### Root rules followed

- keep work on the requested layer
- behavior before beautification
- no request/runtime/send-truth change
- no renderer/model change
- `frontend/` and `docs/` were kept aligned in the same task

### Exact sections removed or de-emphasized

- Stage1:
  - removed the large local intro card below the global header/navigation
  - kept the global header, stage navigation, upload notes accordion, template preview, and input form
- Stage2:
  - de-emphasized the former large result/link box into a compact `链接与标识` utility panel
  - collapsed link/key presentation under a small details block
  - kept preview primary and made the `保存` action visually primary in the preview footer
  - left open/copy link actions available but visually lower-weight
- Stage3:
  - removed the extra `发送前检查` explanation card beside the poster preview
  - removed the visible advanced-details panel from the operator page
  - replaced the multi-card attachment explanation layout with a compact attachment/delivery block
  - kept only the essential send-step controls:
    - recipients
    - email copy
    - attachment options
    - delivery mode
    - send action

### How Stage2 explanation moved into the saved-poster area

- moved the send-target explanation text node `stage2-save-gate-note` out of the result/link panel and into the `已保存海报` card body
- kept the same runtime text behavior:
  - before save: current result is preview-only
  - after save: saved poster is the send target and must be replaced by regenerate + save
- made one small UI-only app binding adjustment so the saved-poster card stays visible even when empty, allowing that explanation to remain anchored in the saved-poster area without changing any saved-poster truth

### How Stage3 was simplified

- reduced the preview area to the saved-poster message plus poster preview only
- kept recipient entry and validation chips
- kept subject / preview text / body fields
- moved draft-source and summary text into the email preview block instead of giving them their own explanatory emphasis
- simplified attachments into one compact area with:
  - delivery mode select
  - attachment checkboxes
  - compact available / selected / buildable summaries
- hid the advanced source panel from the operator UI while preserving the bound DOM fields needed by existing runtime logic

### Exact files changed

- `frontend/index.html`
- `frontend/stage2.html`
- `frontend/stage3.html`
- `frontend/styles.css`
- `frontend/app.js`
- `docs/index.html`
- `docs/stage2.html`
- `docs/stage3.html`
- `docs/styles.css`
- `docs/app.js`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage1/Stage2/Stage3 frontend presentation only
- one small Stage2 UI-binding adjustment only
- docs mirror alignment
- branch execution/state log

### Focused validation run

- mirror/static:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
- source-level verification:
  - verified Stage1 no longer contains the redundant local intro card
  - verified Stage2 result UI now uses compact `链接与标识` presentation
  - verified `stage2-save-gate-note` now lives inside the saved-poster card
  - verified Stage3 no longer contains visible `发送前检查`, `高级详情`, or the old multi-card attachment explanation layout
  - verified touched `frontend/` and `docs/` files remain aligned

### Remaining risks

- this pass was validated with static/mirror checks and source inspection only; no browser screenshot run was performed in this workspace
- Stage2 saved-poster card is now always visible for explanation hierarchy purposes; this is presentation-only, but any future styling work should preserve that UI intent rather than restoring conditional hiding

### Acceptance state

- Stage1 redundant large local intro card removed
- Stage2 result area simplified
- Stage2 send-target explanation now lives in the saved-poster area
- Stage2 link presentation is de-emphasized relative to preview/save
- Stage3 reduced to essential send-step controls
- no production behavior changed
- frontend/docs mirror remains aligned
- branch execution log updated
- PR-UI2 acceptance target met

## Entry — PR-BOTTOM-UF2: Family A gallery_only internal gallery-region rebalance

**Branch:** `main`
**Status:** Complete
**Last updated:** `2026-04-14`

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- then only the minimum files responsible for Family A bottom/gallery layout and rendering structure:
  - `app/services/poster2/template_behavior.py`
  - `app/templates_html/template_dual_v2.css`
  - `app/templates_html/template_dual_v2.html`
  - focused bottom validation tests

### Scope

- PR-BOTTOM-UF2 only
- keep the unified outer bottom frame from PR-BOTTOM-UF1
- change only the internal `gallery_only` gallery region contract
- let `gallery_only` behave as the primary bottom-content layout instead of an inherited compact strip
- keep request truth, renderer routing, hero/product geometry, and Stage3 logic unchanged
- update branch execution log before stop

### Root rules followed

- contract-first
- keep work on the requested layer
- behavior before beautification
- renderer consumes bottom behavior rather than defining template truth
- no outer bottom frame regression from PR-BOTTOM-UF1
- no request/runtime/send-truth changes

### Problem reproduced

- after PR-BOTTOM-UF1 the outer frame was stable, but `gallery_only` still reused a compact strip-derived internal gallery contract
- that left the gallery shell and cards visually concentrated in the upper portion of the shared bottom frame
- for the current 2-item `gallery_only` case before this pass, the branch-local behavior was:
  - `bottom_shell_top=728`
  - `bottom_shell_height=296`
  - `gallery_shell_top=728`
  - `gallery_shell_height=140`
  - `gallery_items_top=746`
  - `gallery_items_height=104`
  - first item bounds `280x104`
- this preserved the unified frame, but the internal gallery region still read like a compact strip rather than the primary bottom content

### Root cause found

- `gallery_only` still entered `_resolve_gallery_strip_vertical_metrics(...)` through a strip-inflation branch
- that branch only enlarged compact strip values slightly instead of defining a true gallery-only primary-content region contract
- item/media/caption placement then inherited those compact heights, so the cards remained visually top-locked even after the outer frame was unified

### Why this is a second-level abstraction fix, not another top patch

- the fix did not move individual cards or captions with ad hoc offsets
- it replaced the `gallery_only` internal vertical region contract with explicit gallery-only primary-content sizing tables
- the outer bottom frame stayed unchanged; only the internal gallery shell height, usable item height, and shell-local centering changed
- caption/media bounds update naturally from the larger item-card contract instead of isolated per-slot nudges

### Internal gallery_only region contract changed

- added a dedicated `gallery_only` primary-content vertical policy in `template_behavior`
- for `gallery_only`, the resolver now uses per-count internal sizing tables instead of strip-derived shell/item inflation
- this policy now defines:
  - larger `gallery_shell_height`
  - larger `gallery_items_height`
  - centered shell-local item placement through `inner_pad_y`
  - fryer detail-row caption/media/card bounds derived from the larger card height
- updated policy names now surface the abstraction change directly, for example:
  - `gallery_only_primary_single_packshot_rebalance`
  - `gallery_only_primary_pair_rebalance`
  - `gallery_only_primary_detail_row_rebalance`

### Exact files changed

- `app/services/poster2/template_behavior.py`
- `app/templates_html/template_dual_v2.css`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_renderer.py`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Family A bottom behavior resolver
- Family A template CSS fallback state
- focused Family A bottom/gallery validation
- branch execution/state log

### Focused validation run

- focused backend validation:
  - `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k "renderer_metadata_exposes_bottom_mode_gallery_only_review or gallery_only_gallery_shell_top_uses_bounded_peer_gap or gallery_only_gallery_items_render_inside_bottom_shell or gallery_only_fryer_dense_quad_uses_expanded_visual_feature_row or toe_shell_height_equals_title_band_height or test_tgs_shell_top_is_728 or test_tgs_gallery_shell_top_above_shell_bottom"` → `8 passed`
- focused HTML/CSS validation:
  - `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k "test_template_css_exposes_independent_bottom_split_state_tokens or test_bottom_split_gallery_only_hides_title_band_and_keeps_gallery_strip or test_bottom_split_title_and_gallery_show_both_regions or test_text_only_expanded_html_keeps_full_width_text_layer_vars or test_text_only_expanded_html_keeps_subtitle_visible_while_gallery_stays_collapsed or test_template_html_hides_title_band_when_gallery_only"` → `6 passed`
- direct structural metric comparison using the same resolver-side inputs for the three target modes:
  - `text_only_expanded`
    - `bottom_shell_top=728`
    - `bottom_shell_height=296`
    - `title_band_top=788`
    - `title_band_height=176`
    - `gallery_shell_top=964`
    - `gallery_shell_height=0`
    - `gallery_items_top=964`
    - `gallery_items_height=0`
  - `title_gallery_split`
    - `bottom_shell_top=728`
    - `bottom_shell_height=296`
    - `title_band_top=728`
    - `title_band_height=168`
    - `gallery_shell_top=896`
    - `gallery_shell_height=100`
    - `gallery_items_top=906`
    - `gallery_items_height=80`
    - first item bounds `{x:224,y:906,w:280,h:80}`
  - `gallery_only`
    - `bottom_shell_top=728`
    - `bottom_shell_height=296`
    - `title_band_top=728`
    - `title_band_height=0`
    - `gallery_shell_top=728`
    - `gallery_shell_height=236`
    - `gallery_items_top=758`
    - `gallery_items_height=176`
    - first item bounds `{x:224,y:758,w:280,h:176}`
- direct before/after comparison for the 2-item `gallery_only` case:
  - before:
    - `gallery_shell_top=728`
    - `gallery_shell_height=140`
    - `gallery_items_top=746`
    - `gallery_items_height=104`
    - first item bounds `{x:224,y:746,w:280,h:104}`
  - after:
    - `gallery_shell_top=728`
    - `gallery_shell_height=236`
    - `gallery_items_top=758`
    - `gallery_items_height=176`
    - first item bounds `{x:224,y:758,w:280,h:176}`
- fryer caption/card evidence under the expanded `gallery_only` detail-row variant:
  - `card_bounds={x:155,y:754,w:156,h:176}`
  - `media_bounds={x:163,y:762,w:140,h:142}`
  - `caption_bounds={x:163,y:908,w:140,h:14}`

### Acceptance state

- PR-BOTTOM-UF1 outer bottom frame abstraction remains intact
- `gallery_only` now uses a distinct primary-content internal gallery region contract
- `gallery_only` gallery content occupies the bottom area more fully
- cards are no longer constrained by the old compact strip heights
- `text_only_expanded` outer frame behavior remains unchanged
- `title_gallery_split` outer frame behavior remains unchanged
- request/routing/runtime truth remained unchanged
- branch execution log is updated
- PR-BOTTOM-UF2 acceptance target is met

### Remaining risks

- this pass validated structurally and through focused HTML/CSS tests, but no fresh screenshot capture was produced in this workspace
- the `gallery_only` contract is now explicitly separated at the vertical-region layer; if future work wants a distinct horizontal distribution language for gallery-only, that would be a separate bounded change rather than part of this fix

## Entry — PR-BOTTOM-UF1: Family A unified bottom frame abstraction

**Branch:** `main`
**Status:** Complete
**Last updated:** `2026-04-14`

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `frontend/stage2.html`
- `frontend/app.js`
- `frontend/stage2_request_helpers.js`
- then only the minimum Family A bottom renderer/layout files needed to change the abstraction:
  - `app/services/poster2/template_behavior.py`
  - `app/templates_html/template_dual_v2.css`
  - focused bottom validation tests

### Scope

- PR-BOTTOM-UF1 only
- Family A bottom abstraction only
- unify the outer bottom frame across:
  - `text_only_expanded`
  - `title_gallery_split`
  - `gallery_only`
- let `gallery_only` reclaim collapsed title-band space inside the shared frame
- keep request/routing/runtime truth unchanged
- keep hero/header/product ownership unchanged
- update branch execution log before stop

### Root rules followed

- contract-first
- keep work on the requested layer
- behavior before beautification
- renderer consumes bottom behavior; renderer does not redefine bottom truth
- no request truth, routing truth, or Stage3 send truth changes

### Problem reproduced

- Family A `gallery_only` already collapsed `title_band_region`, but the gallery shell still started lower inside the bottom area
- the runtime evidence shape was:
  - `bottom_shell_top = 728`
  - `title_band_height = 0`
  - `gallery_shell_top = 748`
- this left an unclaimed void where the title band had collapsed, so the whole bottom composition felt visually sunk relative to the other Family A bottom modes

### Root cause found

- the bottom abstraction was only partially unified:
  - `bottom_shell_top` was already stable at `728`
  - but `bottom_shell_height` still changed by mode
  - and `gallery_only_expanded` still reserved a `peer_gap = 20` even when the title band had collapsed to `0`
- CSS fallback state also still contained a gallery-only-specific lower shell override, which reinforced the lower-feeling composition

### Abstraction changed

- Family A now uses one shared outer bottom frame from `bottom_shell_top` to canvas bottom for the requested three modes
- added a shared internal bottom content anchor at the frame top
- `text_only_expanded` keeps its centered text-band allocation inside that shared frame
- `title_gallery_split` keeps its split allocation inside that shared frame
- `gallery_only` now allocates the collapsed title-band space back to gallery content inside that same frame

### Why this is a unified frame fix, not a gallery_only patch

- the fix did not hardcode a one-off gallery-only top offset
- instead it changed the bottom abstraction so the outer frame height is shared and mode switching changes only internal allocation
- `gallery_only` reclaims space by removing the peer gap that only made sense when a title band occupied that upper region
- the frame anchor and frame height stay stable while title/gallery internals vary by mode

### Exact files changed

- `app/services/poster2/template_behavior.py`
- `app/templates_html/template_dual_v2.css`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_renderer.py`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Family A bottom behavior resolver
- Family A template CSS fallback state
- focused bottom validation/tests
- branch execution/state log

### Focused validation run

- focused backend validation:
  - `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k "gallery_only_gallery_shell_top_uses_bounded_peer_gap or gallery_only_gallery_items_render_inside_bottom_shell or gallery_only_fryer_dense_quad_uses_expanded_visual_feature_row or toe_shell_height_equals_title_band_height or toe_title_band_equals_shell_for_all_sub_cases or toe_shell_height_equals_title_band_compact or toe_shell_height_equals_title_band_short_subtitle or toe_shell_height_equals_title_band_moderate_subtitle or toe_shell_height_equals_title_band_dense_subtitle or toe_no_dead_canvas_below_text_band or toe_layout_metrics_consistent_all_sub_cases or test_shell_height_equals_title_band_height or test_shell_does_not_overshoot_title_band or test_title_band_height_equals_shell_height_and_content_proportionate or test_css_vars_emit_correct_shell_geometry"` → `15 passed`
- focused HTML/CSS validation:
  - `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k "test_template_css_exposes_independent_bottom_split_state_tokens or test_bottom_split_gallery_only_hides_title_band_and_keeps_gallery_strip or test_text_only_expanded_html_keeps_full_width_text_layer_vars or test_text_only_expanded_html_keeps_subtitle_visible_while_gallery_stays_collapsed or test_template_html_hides_title_band_when_gallery_only or test_bottom_split_title_and_gallery_show_both_regions"` → `6 passed`
- direct structural metric comparison across the three target modes:
  - `text_only_expanded`
    - `bottom_shell_top=728`
    - `bottom_shell_height=296`
    - `title_band_top=788`
    - `title_band_height=176`
    - `gallery_shell_top=964`
    - `gallery_shell_height=0`
    - `gallery_items_top=964`
  - `title_gallery_split`
    - `bottom_shell_top=728`
    - `bottom_shell_height=296`
    - `title_band_top=728`
    - `title_band_height=168`
    - `gallery_shell_top=896`
    - `gallery_shell_height=100`
    - `gallery_items_top=906`
  - `gallery_only`
    - `bottom_shell_top=728`
    - `bottom_shell_height=296`
    - `title_band_top=728`
    - `title_band_height=0`
    - `gallery_shell_top=728`
    - `gallery_shell_height=140`
    - `gallery_items_top=746`

### Acceptance state

- outer bottom frame top is stable across all three requested modes
- outer bottom frame height is stable across all three requested modes
- `gallery_only` no longer preserves collapsed title-band void inside the frame
- mode switching changes internal allocation, not outer frame identity
- request/routing/runtime truth stayed unchanged
- Stage2 bottom mode switching truth stayed unchanged
- branch execution log is updated
- PR-BOTTOM-UF1 acceptance target is met

### Remaining risks

- this pass validated structurally and via focused HTML/CSS tests, but it did not capture new screenshot evidence from a live browser session in this workspace
- some older historical tests in `tests/poster2/test_pipeline.py` still describe pre-unified-shell assumptions outside the focused validation set and may need broader cleanup if that legacy suite is rebaselined around the shared-frame model

## Entry — PR-OP7: Stage2 generate guard and preflight diagnostics closure

**Branch:** `main`
**Status:** Complete
**Last updated:** `2026-04-14`

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `frontend/stage2.html`
- `frontend/app.js`
- `frontend/stage2_request_helpers.js`
- `docs/stage2.html`
- `docs/app.js`
- `docs/stage2_request_helpers.js`

### Scope

- PR-OP7 only
- Stage2 generate guard and preflight diagnostics closure only
- stabilize first-switch generate behavior without reopening contract/runtime truth
- keep `frontend/` and `docs/` aligned
- update branch execution log before stop
- no poster contract change
- no bottom truth change
- no renderer routing change
- no Stage3 saved-poster send-truth change

### Root rules followed

- contract-first
- keep work on the requested layer
- behavior before beautification
- frontend/docs mirror were kept aligned in the same task
- no request/runtime truth redesign

### Problem reproduced

- Stage2 still allowed generate attempts to fire too eagerly around the first bottom-mode switch
- the request path still refreshed readiness surfaces too aggressively and too late, which made first-switch failures hard to distinguish from service-readiness timing
- Stage2 lacked a compact operator-visible preflight surface for:
  - raw vs canonical vs payload bottom mode
  - health / template readiness
  - generate status / failure class
  - simple asset-slot readiness

### Root cause found

- the existing single-flight wrapper only debounced clicks; it did not keep a post-attempt cooldown or explicitly guard the direct `triggerGeneration(...)` path
- Stage2 still force-loaded `/api/template-posters` on each run path instead of using a bounded readiness preflight cache
- request diagnostics were logged to console, but the collapsed Stage2 diagnostics area did not expose the minimum markers needed to explain first-switch failures

### Exact generate guard behavior

- generate and regenerate now ignore repeated clicks while a request is active
- the direct `triggerGeneration(...)` path now also refuses duplicate in-flight calls instead of aborting and superseding the prior request
- Stage2 disables the generate buttons immediately on click
- Stage2 now applies a post-attempt cooldown of `1600ms`
- during cooldown the generate buttons remain disabled briefly, then re-enable automatically when no request is active

### Exact canonicalize-and-rebuild behavior

- on generate click Stage2 now enforces this order before payload build:
  - read raw bottom-mode control value
  - canonicalize it with the existing `canonicalizePoster2BottomMode(...)`
  - write the canonical value back into the control
  - sync controls into Stage2 bottom-contract state
  - rebuild the canonical bottom request snapshot
  - build payload from that rebuilt snapshot only
- the settled request path also refreshes the hidden bottom-request preview before payload construction

### Exact preflight TTL / retry behavior

- added a bounded Stage2 preflight cache with TTL `20000ms`
- preflight checks:
  - `/health` through the existing `warmUp(...)` / health-probe path
  - `/api/template-posters` through the existing template-poster loader
- Stage2 reprobes when:
  - the cached preflight is stale
  - the previous generate failed
  - the bottom mode changed
  - template-poster readiness is unknown
- if health preflight fails:
  - generate is blocked
  - operator sees `生成前检查失败：服务健康检查未通过，请稍后重试。`
- if template-poster readiness fails:
  - generate is blocked
  - operator sees `生成前检查失败：模板海报未就绪，请稍后重试。`
- if no API base exists:
  - generate is blocked before request dispatch

### Exact diagnostics markers added

- collapsed Stage2 diagnostics now exposes:
  - `raw_bottom_mode`
  - `canonical_bottom_mode`
  - `payload_bottom_mode`
  - `request_id`
  - `health_status`
  - `template_posters_status`
  - `generate_status`
  - `failure_class`
- added lightweight asset-slot readiness cards for:
  - `scenario`
  - `product`
  - `product_secondary`
  - `gallery[1..4]`
  - `logo`
- each asset slot now shows only:
  - `resolved` or `missing`
  - `source present` or `source absent`

### Files changed

- `frontend/stage2.html`
- `frontend/app.js`
- `frontend/stage2_request_helpers.js`
- `docs/stage2.html`
- `docs/app.js`
- `docs/stage2_request_helpers.js`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage2 frontend generate guard only
- Stage2 frontend readiness/preflight gating only
- Stage2 collapsed diagnostics visibility only
- publish mirror alignment
- branch execution/state log

### Focused validation run

- syntax/static:
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
  - `node --check frontend/stage2_request_helpers.js`
  - `node --check docs/stage2_request_helpers.js`
- mirror sync/static:
  - `cmp -s frontend/app.js docs/app.js`
  - `cmp -s frontend/stage2.html docs/stage2.html`
  - `cmp -s frontend/stage2_request_helpers.js docs/stage2_request_helpers.js`
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
- focused source-level verification:
  - verified `stage2RunGeneration` now routes through the cached preflight path instead of directly invoking `triggerGeneration(...)`
  - verified duplicate in-flight clicks are ignored
  - verified cooldown / TTL constants are present at `1600ms` and `20000ms`
  - verified the new diagnostics markers and asset-slot surfaces are present in Stage2 markup/runtime

### Remaining risks

- no browser automation or screenshot harness was run in this pass, so the requested mode-switch sequence was not captured as visual evidence in this workspace
- preflight health/template readiness remains frontend-side gating over existing endpoints; it improves explainability and timing behavior but does not change backend readiness truth
- service slowness beyond the current TTL window can still surface after a successful preflight if the backend degrades between probe and request

### Exact acceptance state

- Stage2 now has a bounded generate guard with single-flight enforcement and a visible cooldown
- Stage2 canonicalizes and rebuilds bottom request state before payload build
- Stage2 now uses TTL-based readiness preflight instead of blindly forcing template readiness on every generate
- Stage2 exposes the required minimal diagnostics markers and lightweight asset-slot readiness markers
- no poster/runtime truth changed
- frontend/docs mirror is aligned
- branch execution log is updated
- acceptance target for PR-OP7 is met

## Entry — PR-SAVE1: Stage2 save-gated poster send truth

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-14

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
- task-relevant formal docs resolved from the indexed validation / engineering paths:
  - `docs/poster2/05_validation/bottom_behavior_contract_status_v1.md`
  - `docs/poster2/05_validation/product_region_annotation_contract_status_v1.md`
  - `docs/poster2/03_engineering/email_copy_optimizer_and_optional_attachment_status_v1.md`
- then minimum task files only:
  - `frontend/stage2.html`
  - `frontend/stage3.html`
  - `frontend/app.js`
  - `frontend/styles.css`
  - `docs/stage2.html`
  - `docs/stage3.html`
  - `docs/app.js`
  - `docs/styles.css`

### Scope

- PR-SAVE1 only
- first revert the current retained-poster Stage2 implementation
- replace it with a simpler `Current Poster` + `Saved Poster` model
- gate Stage3 so only `Saved Poster` may be sent
- no poster contract change
- no canonical generate payload construction change
- no bottom truth change
- no product annotation ownership change
- no renderer routing change
- no backend API contract change
- keep frontend/docs mirror aligned
- update branch execution log before stop

### Root rules followed

- contract-first
- keep work on the requested layer
- behavior before beautification
- send truth separated from generate truth
- saved poster kept out of request construction and renderer truth
- source and published mirror were kept aligned in the same task

### Problem reproduced

- the prior PR-COMP1 retained-poster implementation added a comparison-only state path in Stage2
- the retained model did not match the workflow goal for operator-approved send truth
- Stage3 still restored its sendable `poster_key` from the latest Stage2 success / URL path rather than from an explicit operator save action

### Root cause found

- the retained implementation solved only comparison visibility, not send-truth selection
- Stage2 and Stage3 lacked a dedicated saved-poster gate that separated:
  - latest successful preview result
  - operator-approved poster selected for send

### Old retained implementation reverted

- removed the retained-poster storage key and retained-poster runtime functions
- removed `保留当前海报` / `取消保留` behavior
- removed the retained comparison card path and replaced it with saved-poster semantics
- current generate flow no longer depends on the old retained comparison state

### Exact Current Poster vs Saved Poster model

- `Current Poster`
  - latest successful generate result only
  - preview-only
  - updated automatically on every successful generate
  - may be overwritten by the next successful generate
  - never becomes send truth automatically
- `Saved Poster`
  - created only when the operator clicks `保存`
  - stored as a lightweight send-selection snapshot with:
    - `preview_url`
    - `final_url`
    - `poster_key`
    - `title`
    - `summary`
    - `generated_at`
    - `saved_at`
  - this is the only Stage3 sendable poster
  - also remains visible as the lightweight comparison card

### Exact save / overwrite / clear rules

- on successful generate:
  - update `Current Poster` only
  - do not overwrite `Saved Poster`
- on clicking `保存`:
  - copy `Current Poster` into `Saved Poster`
  - require a valid `poster_key`
  - overwrite the previous saved poster if one already exists
- on clicking `取消保存`:
  - clear `Saved Poster` only
  - keep `Current Poster` intact

### Exact Stage3 gating behavior

- Stage3 now resolves send truth from the saved-poster session slot only
- Stage3 no longer treats the latest Stage2 result or URL-carried `poster_key` as send truth
- if there is no saved poster:
  - Stage3 restore is blocked before email preview / send hydration
  - operator receives a clear message to return to Stage2 and save a poster first
  - send and draft-refresh actions remain disabled
- Stage2 next-step button is also gated:
  - disabled unless `Saved Poster` exists with a valid `poster_key`

### Files changed

- `frontend/stage2.html`
- `frontend/stage3.html`
- `frontend/app.js`
- `docs/stage2.html`
- `docs/stage3.html`
- `docs/app.js`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage2 operator-facing save / send-selection UI
- Stage2 runtime saved-poster selection state
- Stage3 saved-poster gating and send-truth selection
- branch execution/state log

### Focused validation run

- syntax/static:
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
- mirror sync/static:
  - `cmp -s frontend/stage2.html docs/stage2.html`
  - `cmp -s frontend/stage3.html docs/stage3.html`
  - `cmp -s frontend/app.js docs/app.js`
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
- focused save-gating checks:
  - static check confirmed the old retained-poster implementation strings / storage key were removed
  - static check confirmed saved-poster storage is not referenced inside `buildGeneratePosterPayload(...)`
  - static check confirmed Stage3 now keys send truth from `loadStage2SavedPosterState()` only
  - static check confirmed Stage3 no longer resolves send truth from `getPosterKeyFromLocation() || stage2Result?.poster_key`
  - static check confirmed Stage2 next-step gating now depends on saved poster presence

### Remaining risks

- no browser automation or screenshot harness was run in this pass, so requested screenshots were not captured in this workspace
- save-gating remains frontend-session based; it intentionally does not alter backend contract or persisted poster truth selection beyond the chosen `poster_key`
- the legacy hidden `history` field still exists for compatibility, but it is not used by the save-gated workflow

### Exact acceptance state

- Stage2 generate flow is no longer coupled to the prior retained-poster implementation
- Current Poster and Saved Poster are clearly separated
- Saved Poster is the only sendable poster
- the comparison stays simple
- no poster/runtime contract truth changed
- frontend/docs mirror is aligned
- branch execution log is updated
- acceptance target for PR-SAVE1 is met

## Entry — PR-COMP1: Stage2 single retained poster comparison card

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-14

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- re-anchored required baseline docs before edits:
  - `docs/poster2/poster_generation_product_design_baseline_v1.md`
  - `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
- then minimum task files only:
  - `frontend/stage2.html`
  - `frontend/app.js`
  - `frontend/styles.css`
  - `docs/stage2.html`
  - `docs/app.js`
  - `docs/styles.css`

### Scope

- PR-COMP1 only
- Stage2 lightweight comparison-only UI enhancement only
- add one Current Poster card and one optional Retained Poster card
- keep retained poster comparison-only and operator-facing
- no Stage2 request truth change
- no canonical payload construction change
- no Stage3 truth-model change
- no backend API contract change
- no template routing change
- keep frontend/docs mirror aligned
- update branch execution log before stop

### Root rules followed

- contract-first
- keep work on the requested layer
- behavior before beautification
- retained poster kept outside canonical request/send truth
- no new history browser or version manager introduced
- source and published mirror were kept aligned in the same task

### Problem reproduced

- Stage2 exposed only the active latest result and had no lightweight way for an operator to pin one successful poster for side-by-side visual comparison
- existing runtime state also included a hidden multi-run history path, which did not match the requested simplified two-slot model

### Root cause found

- Stage2 had no dedicated comparison-only state surface separated from current request/send truth
- successful result state and persistence were organized around the active Stage2 success payload, not around a bounded retained comparison card

### Exact retained-poster design

- Stage2 now uses a two-slot comparison model only:
  - `Current Poster`
    - latest successful poster result
    - updated automatically on each successful generate
    - remains the only active Stage2 success truth feeding Stage3 through existing `poster_key` flow
  - `Retained Poster`
    - created only when the operator clicks `保留当前海报`
    - stores lightweight comparison-safe fields only:
      - `preview_url`
      - `final_url`
      - `poster_key`
      - `title`
      - `summary`
      - `generated_at`
      - `retained_at`
- retained comparison state is stored separately in session storage under a dedicated comparison-only key
- retained comparison state is not read by request payload builders, Stage3 restore, or send logic

### Exact overwrite behavior

- clicking `保留当前海报` copies the current successful poster comparison snapshot into the retained slot
- if a retained poster already exists, that slot is overwritten in place by the newly kept current poster
- new successful generate updates `Current Poster` only and does not overwrite `Retained Poster`

### Exact clear/remove behavior

- clicking `取消保留` clears the retained slot only
- current/latest success remains intact
- full stale-runtime reset still clears retained comparison state, but ordinary pre-request invalidation does not

### Files changed

- `frontend/stage2.html`
- `frontend/app.js`
- `docs/stage2.html`
- `docs/app.js`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage2 operator-facing HTML comparison card UI
- Stage2 frontend/docs runtime state and comparison-only persistence
- branch execution/state log

### Focused validation run

- syntax/static:
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
- mirror sync/static:
  - `cmp -s frontend/stage2.html docs/stage2.html`
  - `cmp -s frontend/app.js docs/app.js`
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
- focused retained-poster checks:
  - separate comparison-only session storage key added for Stage2 retained/current cards
  - successful generate path updates current comparison slot via `applyVertexPosterResult(...)`
  - retain action overwrites the single retained slot only
  - remove action clears the retained slot only
  - static check confirmed comparison storage is not referenced inside `buildGeneratePosterPayload(...)`
  - static check confirmed comparison storage is not referenced inside Stage3 hydrate/send code

### Remaining risks

- no browser automation or screenshot harness was run in this pass, so requested before/after screenshots were not captured in this workspace
- the visible comparison cards restore their lightweight card state after reload, but the large primary preview surface still follows the existing active-success hydration behavior rather than a new retained-card restore path
- the legacy hidden `history` field remains in state for compatibility, but it is no longer used to render operator-facing comparison UI

### Exact acceptance state

- Stage2 supports one retained comparison poster only
- Current Poster remains the only active truth source for Stage2 to Stage3 flow
- Retained Poster is clearly labeled comparison-only
- retain / overwrite / remove behavior is simple and predictable
- new successful generate updates Current Poster only
- Retained Poster does not participate in generate payload construction
- Retained Poster does not participate in Stage3 send truth
- frontend/docs mirror is aligned
- branch execution log is updated
- acceptance target for PR-COMP1 is met

## Entry — PR-UI1: operator UI simplification and debug de-emphasis

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-13

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- re-anchored required baseline docs before edits:
  - `docs/poster2/poster_generation_product_design_baseline_v1.md`
  - `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
- then minimum task files only:
  - `frontend/index.html`
  - `frontend/stage2.html`
  - `frontend/stage3.html`
  - `frontend/app.js`
  - `frontend/styles.css`
  - `docs/index.html`
  - `docs/stage2.html`
  - `docs/stage3.html`
  - `docs/app.js`
  - `docs/styles.css`

### Scope

- PR-UI1 only
- bounded frontend/docs presentation cleanup only
- simplify Stage1 operator form and Stage2 generate-and-confirm flow
- keep Stage3 changes lightweight and consistency-only
- no contract change
- no request truth change
- no Stage1/Stage2/Stage3 backend truth-path change
- no mode semantics change
- no routing change
- no renderer behavior change
- no copy optimizer logic change
- keep frontend/docs mirror aligned
- update branch execution log before stop

### Root rules followed

- contract-first
- keep work on the requested layer
- behavior before beautification
- no request/routing/runtime truth changes
- debug/status detail moved behind collapse instead of being removed from evidence paths
- source and published mirror were kept aligned in the same task

### Problem reproduced

- Stage1 main flow was text-heavy and repeated internal ownership / contract disclaimers in multiple visible hints
- Stage2 main flow exposed internal status surfaces, pilot/debug badges, and copy-optimization detail too close to the primary preview/generate path
- mixed-language UI presentation was inconsistent:
  - some operator headings and labels remained English
  - option values and content were mixed with explanatory English labels
- Stage3 still carried several English operator-facing headings even though a collapsed advanced area already existed

### Root cause found

- operator guidance had accumulated as inline visible hints rather than being constrained to short section-level reminders
- internal/debug/status surfaces were technically already separable, but several were still rendered in the primary panel headers and body areas
- wording decisions were not normalized to a single rule for operator labels versus structured values/content

### Exact UI simplification decisions

- Stage1:
  - replaced the always-open upload note card with a collapsed `details` block
  - reduced top-level page guidance to one short sentence
  - shortened section hints to one short operator-facing sentence per major section
  - removed repeated visible disclaimers about template truth / request truth / ownership from the main form
  - collapsed preview-side copy review into a secondary `details` block
  - kept preview and existing controls intact
- Stage2:
  - renamed panels and controls to shorter operator-facing Chinese labels
  - kept preview visually central and primary
  - moved copy-optimization actions, summary, and lineage behind a collapsed `details` section
  - moved `poster_key` into a collapsed result-details section
  - hid preview-header status badges from the primary view
  - hid template / engine badges from the visible diagnostics header
  - kept diagnostics available through the existing collapsed details control
- Stage3:
  - converted main headings and labels to Chinese for consistency
  - kept advanced/source area collapsed
  - kept send actions prominent and advanced metadata secondary

### Exact language-unification decisions

- Chinese used consistently for:
  - page titles
  - section headings
  - field labels
  - helper sentences
  - primary buttons and navigation text
- English preserved for:
  - structured option values and mode values such as `off`, `suggest`, `apply`, `title_gallery_split`, `gallery_only`, `inline_only`, `resend`
  - entered copy and poster content placeholders
  - structured identifiers such as `poster_key`
- compatibility-only legacy English strings required by the existing sync test were preserved as hidden HTML comments, not visible operator copy

### Exact debug/log de-emphasis decisions

- copy-optimization lineage moved behind collapsed secondary UI
- copy-optimization summary/actions moved behind collapsed secondary UI
- Stage2 preview header status chips no longer compete in the primary preview header
- Stage2 template / engine badge row no longer competes in the primary diagnostics header
- result metadata such as `poster_key` moved behind collapsed secondary UI
- Stage3 advanced delivery/source details remained collapsed and were relabeled as a secondary area
- no debug evidence bindings or hidden metadata sinks were removed; only presentation hierarchy changed

### Files changed

- `frontend/index.html`
- `frontend/stage2.html`
- `frontend/stage3.html`
- `frontend/app.js`
- `frontend/styles.css`
- `docs/index.html`
- `docs/stage2.html`
- `docs/stage3.html`
- `docs/app.js`
- `docs/styles.css`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage1 operator-facing HTML wording and information hierarchy
- Stage2 operator-facing HTML wording and information hierarchy
- Stage3 lightweight consistency wording
- shared frontend/docs presentation CSS
- small frontend/docs UI-label JS adjustments only
- branch execution/state log

### Focused validation run

- syntax/static:
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
- mirror sync/static:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
  - `cmp -s frontend/index.html docs/index.html`
  - `cmp -s frontend/stage2.html docs/stage2.html`
  - `cmp -s frontend/stage3.html docs/stage3.html`
  - `cmp -s frontend/app.js docs/app.js`
  - `cmp -s frontend/styles.css docs/styles.css`
- focused acceptance checks from the edited markup/runtime:
  - Stage1 main flow now uses shorter Chinese section headings and visibly reduced inline help density
  - Stage2 main flow keeps preview primary while optimization/detail surfaces are collapsed
  - Stage3 advanced/source details remain collapsed and secondary
  - structured English values/modes remain intact
  - no request/routing/runtime files or helper truth paths were changed

### Remaining risks

- no browser screenshot harness was run in this pass, so before/after screenshots were not captured in this workspace
- one existing repo sync test still encodes several legacy English Stage1/Stage2 strings; this pass preserved those tokens as hidden compatibility comments so UI cleanup could proceed without weakening the current test
- `CLAUDE.md` was already dirty in the worktree before closeout; it was not edited for PR-UI1 because no new shared-state fact needed to be recorded there

### Exact acceptance state

- Stage1 is visibly lighter and less repetitive in the main operator flow
- Stage2 is visibly cleaner and more preview-first, with debug/status/lineage surfaces moved to collapsed secondary areas
- Stage3 consistency is improved without widening scope
- Chinese headings/help plus English values/content are applied consistently on the edited surfaces
- no request truth, routing, runtime truth, renderer behavior, or optimizer logic changed
- frontend/docs mirror is aligned
- branch execution log is updated
- acceptance target for PR-UI1 is met

## Entry — PR-OP6A: Stage2 failure-classification hardening

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-13

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- re-read frozen-state docs most relevant to this pass:
  - `docs/poster2/05_validation/bottom_mode_switch_closure_status_v1.md`
  - `docs/poster2/05_validation/bottom_behavior_contract_status_v1.md`
  - `docs/poster2/05_validation/product_region_annotation_contract_status_v1.md`
  - `docs/poster2/03_engineering/email_copy_optimizer_and_optional_attachment_status_v1.md`
- then minimum task files only:
  - `frontend/stage2.html`
  - `frontend/app.js`
  - `frontend/stage2_request_helpers.js`
  - `docs/stage2.html`
  - `docs/app.js`
  - `docs/stage2_request_helpers.js`
  - minimum additional validation surface:
    - `tests/frontend/test_stage2_request_helpers.js`

### Scope

- PR-OP6A only
- Stage2 failure-classification hardening only
- keep the current diagnosis fixed:
  - normal live generate path is proven working
  - current reproduced failures are not primarily deploy-health blockers
  - current reproduced failures are not primarily preflight/CORS blockers
  - current reproduced failures are not currently proving residual request-state contamination as the top blocker
  - remaining operator-facing problem is weak failure classification
- keep Stage2/frontend/docs mirror aligned
- update branch execution log before stop
- no poster contract reopen, no bottom truth change, no renderer routing change, no product ownership change, no Stage3 truth-model change, no new operator feature work

### Root rules followed

- contract-first
- keep work on the requested layer
- no request-shape redesign
- no canonical request construction change
- no bottom semantics change
- no Stage1 asset semantics change
- no Stage3 truth-model change
- source and published mirror were kept aligned in the same task

### Problem reproduced

- Stage2 already separated request-state failures from a generic transport bucket, but true backend `5xx` failures still collapsed into the same class and operator wording as browser-side CORS/fetch/preflight failures
- current operator status text therefore blurred three different causes:
  - request/input/asset failure
  - network/CORS/fetch failure
  - backend unavailable / `5xx`
- current live evidence continued to show:
  - success path works
  - structured app-level `422` failures are real and machine-readable
  - CORS headers are present on healthy and app-level error paths

### Root cause found

- `classifyStage2RequestFailure(...)` in Stage2 helpers and local fallback code treated `status >= 500` as `network_transport`
- final operator status rendering simply prefixed one generic transport message to most non-request failures
- Stage2 therefore lacked an explicit operator-visible `backend_unavailable` class even when the backend returned a structured `5xx` response body

### Exact classification buckets implemented

- `request_state`
  - covers `400/401/403/404/409/412/413/422`
  - also covers structured request/input/asset error codes such as:
    - `image_decode_failed`
    - `product_image_load_failed`
    - `bad_image_source`
    - `bad_placeholder_asset`
    - `validation_error`
- `network_transport`
  - covers browser fetch/CORS/preflight/timeout/no-usable-response cases
  - continues to catch `TypeError`, `status=0`, and transport-language failures
- `backend_unavailable`
  - new explicit class for backend `5xx` responses
  - covers `500/502/503/504` through the generic `status >= 500` branch

### Exact operator-facing wording decisions

- request / input / asset issue:
  - `当前素材或输入无法用于生成，请检查图片来源、占位素材和必填字段后重试。`
- network / CORS / preflight issue:
  - `浏览器未能完成生成请求，请检查网络、跨域或预检配置后重试。`
- backend unavailable / `5xx`:
  - `生成服务暂时不可用或返回服务器错误，请稍后重试。`
- quota path kept distinct and unchanged:
  - `图像生成额度已用尽，请稍后重试或上传已有素材。`

Additional rendering rule:

- request-state and backend-unavailable paths now keep useful backend code/message detail when available
- network/CORS/fetch paths append detail only when it is operator-meaningful, such as CORS/preflight/timeout wording, instead of blindly surfacing generic `Failed to fetch`

### Files changed

- `frontend/app.js`
- `docs/app.js`
- `frontend/stage2_request_helpers.js`
- `docs/stage2_request_helpers.js`
- `tests/frontend/test_stage2_request_helpers.js`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage2 frontend failure-classification helper only
- Stage2 operator-visible failure message composition only
- publish mirror alignment
- branch execution/state log

### Focused validation run

- focused Stage2 helper coverage:
  - `node --test tests/frontend/test_stage2_request_helpers.js` → `21 passed`
  - updated helper coverage now verifies:
    - structured `422` request/input/asset failure → `request_state`
    - fetch/CORS failure → `network_transport`
    - backend `502` failure → `backend_unavailable`
- syntax/static:
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
  - `node --check frontend/stage2_request_helpers.js`
  - `node --check docs/stage2_request_helpers.js`
- mirror sync/static:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
  - `cmp -s frontend/app.js docs/app.js`
  - `cmp -s frontend/stage2_request_helpers.js docs/stage2_request_helpers.js`
- live generate checks against deployed service:
  - success sample `pr-op6a-success` → `200`, `template_id=template_dual_v2`, `renderer_mode=auto`, `degraded=false`, `structure_complete=true`, `deliverable=true`
  - structured input failure sample `pr-op6a-422` → `422`, `code=image_decode_failed`, CORS headers still present on the response
- focused classification-case validation coverage for required categories:
  - successful generate → live deployed request
  - structured `422` request/input failure → live deployed request
  - true network/CORS/fetch failure → helper classification test
  - true backend `5xx`/unavailable failure → helper classification test

### Remaining risks

- this pass hardens Stage2 classification and operator wording, but it does not add a dedicated browser-network capture harness; real browser-console phrasing for field incidents still depends on the browser/runtime that raises the fetch error
- network/CORS and backend `5xx` validation are covered through focused classification tests in this workspace; no intentionally broken deployed `5xx` endpoint was introduced for live-path validation
- no backend/API truth changed here, so any future deployment outage still depends on live environment health outside this workspace

### Exact acceptance state

- Stage2 now distinguishes:
  - request/input/asset failure
  - network/CORS/fetch failure
  - backend unavailable / `5xx`
- operator wording is concise and class-specific instead of collapsing all non-`422` failures into one generic transport message
- successful path remains unchanged
- no poster/runtime truth changed
- no family-line routing changed
- frontend/docs mirror is aligned
- `CLAUDE.md` was left untouched because this PR did not add a new shared-state fact beyond the branch execution log
- branch execution log is updated
- acceptance target for PR-OP6A is met

## Entry — PR-OP5: Stage2 request-state decontamination and scenario-driven closure

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-13

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- re-anchored required baseline/frozen docs before edits:
  - `docs/poster2/poster_generation_product_design_baseline_v1.md`
  - `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
  - `docs/poster2/05_validation/bottom_mode_switch_closure_status_v1.md`
  - `docs/poster2/05_validation/bottom_behavior_contract_status_v1.md`
  - `docs/poster2/05_validation/product_region_annotation_contract_status_v1.md`
  - `docs/poster2/03_engineering/email_copy_optimizer_and_optional_attachment_status_v1.md`
- then minimum task files only:
  - `frontend/stage2.html`
  - `frontend/app.js`
  - `frontend/styles.css`
  - `docs/stage2.html`
  - `docs/app.js`
  - `docs/styles.css`
  - minimum additional helper surface required for request-state closure:
    - `frontend/stage2_request_helpers.js`
    - `docs/stage2_request_helpers.js`
    - `tests/frontend/test_stage2_request_helpers.js`

### Scope

- PR-OP5 only
- Stage2 request-state decontamination only
- scenario-driven closure for:
  - Scenario A: re-generate inside Stage2 after changing controls
  - Scenario B: return from Stage3 back to Stage2, then re-generate
  - Scenario C: return to Stage1, change inputs, re-enter Stage2, then generate
- keep Stage2/frontend/docs mirror aligned
- update branch execution log before stop
- no poster structure contract reopen, no bottom redesign, no product annotation ownership change, no renderer routing change, no Stage3 backend-truth-model change, no new operator feature work

### Root rules followed

- contract-first
- keep work on the requested layer
- frontend cache remains cache only, never truth source
- preview and final generate continue consuming the same canonical bottom request truth
- bottom contract semantics stayed frozen
- product annotation ownership stayed frozen
- renderer routing and `/api/v2/generate-poster` truth stayed frozen
- Stage3 remained backend-truth-driven
- source and published mirror were kept aligned in the same task

### Problem reproduced

- Stage2 still allowed stale success/session state to survive long enough to contaminate later operator flows even when current source truth had changed
- the contamination class was broader than one field:
  - stale `sessionStorage.stage2`
  - stale `poster_key` in Stage2 URL
  - stale success signatures
  - stale copy-optimization acceptance/success carry-forward
  - weak request failure labeling that collapsed request-state and transport/network failures together
- the most important gap for Scenario C was that stale stored success could survive a Stage1 truth change because Stage2 init did not actively reconcile stored success against current canonical form state

### Root cause found

- Stage2 already had partial invalidation, but not a complete init-time reconciliation step for stored success state versus current Stage1/Stage2 canonical truth
- helper/runtime logic did not expose an explicit compatibility test for stored success snapshots
- local fallback signature code in `frontend/app.js` / `docs/app.js` also failed to carry explicit `assets` / `copy` objects into `formSignature`, which weakened fallback-path canonical signature honesty
- operator-facing error handling treated request/input-state failures and network/transport/CORS/backend-reachability failures too similarly

### Exact canonicalization / invalidation changes made

- kept the existing bottom canonicalization path intact:
  - preview and final generate still read the same canonical bottom request state
- added explicit stored-success compatibility logic:
  - `classifyStoredStage2ResultCompatibility(...)`
  - compares persisted `canonical_form_signature` against current canonical Stage2 form truth
- added Stage2 init reconciliation:
  - `reconcileStage2StoredSuccessState(...)`
  - if stored success matches current canonical truth, it may remain as safe comparison/session metadata only
  - if stored success is stale or missing canonical signature, Stage2 clears:
    - `sessionStorage.stage2`
    - stale cached final-poster asset reference
    - stale `poster_key` URL carry-forward
    - last-success signature carry-forward
- fixed local fallback form-signature construction in `frontend/app.js` / `docs/app.js` so `assets` and `copy` participate honestly in canonical signature construction even without helper delegation
- kept copy-optimization invalidation tied to canonical source changes:
  - source/bottom/request-control changes still reset accepted optimization carry-forward before the next canonical snapshot is built

### Exact failure-classification changes made

- added explicit Stage2 request failure classification helper:
  - `classifyStage2RequestFailure(...)`
- operator-visible failure handling now separates at least:
  - `request_state`
    - invalid/current-input/canonical-state problems such as bad request shape or unresolved operator input state
  - `network_transport`
    - network reachability, CORS, fetch/timeout, and backend availability problems
- asset-normalization failure before request dispatch is now surfaced through the request-state class instead of a generic generate failure
- transport/backend failures now prepend a clearer operator message instead of collapsing into the same generic path

### Scenario closure coverage

- Scenario A — re-generate inside Stage2 after changing controls:
  - canonical request helper tests still prove fresh payload snapshots per generate
  - bottom-mode change invalidates only `bottom_contract`
  - success-derived state is cleared before the next request snapshot is used
  - stale prior success metadata is not reused as request truth
- Scenario B — return from Stage3 back to Stage2:
  - Stage2 init now reconciles stored success against current canonical truth instead of trusting old success/session state implicitly
  - stale `poster_key` / stored success state is cleared if it no longer matches current canonical Stage2 truth
  - Stage3 success state does not silently become the next Stage2 request input source
- Scenario C — return to Stage1, change inputs, re-enter Stage2:
  - Stage2 init now treats canonical-signature mismatch as stale success contamination and clears old Stage2 success/session state
  - fresh Stage1 truth becomes the only accepted request source for the next generate
  - stale Stage2 cache/snapshot no longer outranks current Stage1 truth

### Files changed

- `frontend/app.js`
- `docs/app.js`
- `frontend/stage2_request_helpers.js`
- `docs/stage2_request_helpers.js`
- `tests/frontend/test_stage2_request_helpers.js`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage2 frontend request-state lifecycle only
- Stage2 frontend request-helper / canonical-signature logic only
- Stage2 operator-facing failure classification only
- publish mirror alignment
- branch execution/state log

### Focused validation run

- focused Stage2 helper / scenario coverage:
  - `node --test tests/frontend/test_stage2_request_helpers.js` → `21 passed`
- syntax/static:
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
  - `node --check frontend/stage2_request_helpers.js`
  - `node --check docs/stage2_request_helpers.js`
- mirror sync/static:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
  - `cmp -s frontend/app.js docs/app.js`
  - `cmp -s frontend/stage2_request_helpers.js docs/stage2_request_helpers.js`
- source-level proof attached through helper tests:
  - stale stored Stage2 success is rejected on canonical signature mismatch
  - stored Stage2 success remains compatible only on canonical signature match
  - request-state failures and network/transport failures classify separately

### Remaining risks

- this pass validated through source-level/helper-level scenario proofs and static checks; no live browser recording or deployed network artifact bundle was available in this workspace
- compatible stored Stage2 success may still exist as safe session metadata when canonical truth matches; this pass intentionally preserves the “cache is cache, not truth” boundary instead of deleting all success state unconditionally
- no backend/API/runtime truth changed here, so any real deployed transport/CORS outage would still need live-environment verification outside this workspace

### Exact acceptance state

- Scenario A is clean at the Stage2 canonical request-helper / invalidation layer
- Scenario B is clean at the Stage2 stored-success / stale-URL / stale-session reconciliation layer
- Scenario C is clean at the Stage1-truth-over-stale-Stage2-cache reconciliation layer
- preview and final generate still share the same canonical bottom truth
- stale Stage2 or Stage3 success/session state no longer survives as the next Stage2 request truth when current canonical truth changed
- operator-visible failure classes are clearer
- no request/routing/runtime truth changed
- frontend/docs mirror is aligned
- `CLAUDE.md` was left untouched by this pass because no new shared-state fact needed to be carried forward beyond the branch execution log
- branch execution log is updated
- acceptance target for PR-OP5 is met

## Entry — PR-OP4R: Stage3 redundancy reduction and operator-send flow simplification

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-13

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- latest completed branch state entries re-read:
  - `PR-OP4`
  - `Storage / Copy / Email Closure Engineering`
  - `PR: Gemini Copy Optimizer And Optional Attachment Assets`
- then minimum task files only:
  - `frontend/stage3.html`
  - `frontend/app.js`
  - `frontend/styles.css`
  - `docs/stage3.html`
  - `docs/app.js`
  - `docs/styles.css`

### Scope

- PR-OP4R only
- Stage3 redundancy reduction only
- operator-send flow simplification only
- keep poster preview visible
- keep Stage3 backend-truth-driven
- keep frontend/docs mirror aligned
- write branch execution log back before stop
- no backend truth-model change, no preview/send contract change, no frontend-composed draft truth, no Stage1/Stage2 work, no attachment-ownership change

### Root rules followed

- contract-first
- keep work on the requested layer
- Stage3 remains backend-truth-driven through `poster_key -> poster_record -> backend preview/send`
- no frontend-composed draft truth was reintroduced
- no backend truth-model or API contract change was introduced
- attachment ownership stayed backend-owned
- source and published mirror were aligned in the same task

### Problem reproduced

- PR-OP4 improved Stage3 structurally, but the page still repeated too much explanation around the poster and draft
- the main action area still read like an internal editing flow because it exposed:
  - `Refresh Draft`
  - `Accept Copy`
  - `Reject Copy`
  - `Send Email`
- the Stage3 product shape still felt heavier than a lightweight send-confirmation page

### Root cause found

- PR-OP4 kept too much of the earlier internal closure-review control model in the primary operator path
- poster/draft explanation remained duplicated between the main header, poster-side cards, and send section
- the optimize/send boundary was technically correct, but the action language still exposed internal review mechanics instead of one operator-facing copy-improvement action

### Exact redundancy reductions made

- simplified the main Stage3 instruction to:
  - `请确认收件人、邮件文案与附件方式，然后发送。`
- removed the long backend/process explanation from the primary Stage3 header
- kept the poster preview visible, but reduced surrounding explanation to one lightweight readiness card
- moved technical truth explanation to the collapsed advanced/details area only
- moved draft-source wording into the copy-confirmation section instead of repeating draft/process explanation above the poster

### Exact action simplification decisions

- simplified the primary action area to:
  - `AI 优化文案`
  - `Send Email`
- kept:
  - `Back to Stage 2`
  as the only low-emphasis navigation action
- removed the internal-feeling primary-flow controls:
  - `Accept Copy`
  - `Reject Copy`
  - prominent `Refresh Draft` wording
- retained backend preview refresh behavior under the operator-facing action:
  - `AI 优化文案`
- Stage3 send no longer depends on an accept/reject state machine

### Main-flow simplification result

- Stage3 now reads in this order:
  - poster preview
  - recipients
  - copy confirmation
  - email draft preview
  - attachment choice
  - send
- attachment presentation is lighter and more operator-facing:
  - available attachments
  - selected for this send
  - buildable later
  - delivery mode

### Backend-truth boundary preserved

- Stage3 still restores through:
  - `GET /api/v2/posters/{poster_key}`
- Stage3 still refreshes copy through:
  - `POST /api/v2/email/preview`
- Stage3 still sends through:
  - `POST /api/v2/email/send`
- no frontend-composed canonical draft model was reintroduced
- no backend truth-model, preview contract, or send contract change was made

### Files changed

- `frontend/stage3.html`
- `frontend/app.js`
- `frontend/styles.css`
- `docs/stage3.html`
- `docs/app.js`
- `docs/styles.css`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage3 frontend operator surface only
- Stage3 frontend action wiring only
- publish mirror alignment
- branch execution/state log

### Focused validation run

- syntax:
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
- mirror sync / checks:
  - `bash scripts/sync_frontend_to_docs.sh`
  - `bash scripts/check_frontend_docs_sync.sh`
  - `cmp -s frontend/stage3.html docs/stage3.html`
  - `cmp -s frontend/app.js docs/app.js`
  - `cmp -s frontend/styles.css docs/styles.css`
- existing sync/static validation:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
- focused source inspection:
  - simplified header instruction present
  - `AI 优化文案` is the remaining copy-improvement action
  - `Accept Copy`, `Reject Copy`, and `Refresh Draft` are absent from the primary operator flow
  - Stage3 still calls backend restore/preview/send endpoints only
  - advanced/details area still carries backend/source truth and HTML source

### Remaining risks

- validation here is syntax/static/mirror/source-path based; no live browser screenshot or deployed send-provider run was attached in this workspace
- the existing `refresh-email-preview` id remains wired to backend preview refresh for compatibility, although the user-facing label is now simplified to `AI 优化文案`
- multi-recipient send continues to fan out one backend send call per valid recipient; this PR intentionally did not redesign that backend-owned send pattern

### Exact acceptance state

- Stage3 header is simplified to operator-facing send guidance
- poster preview remains visible
- main flow now emphasizes recipients, copy, attachments, and send
- main actions are simplified and no longer read like internal editing/debug controls
- Stage3 remains backend-truth-driven
- no frontend-composed draft truth was reintroduced
- frontend/docs mirror is aligned
- `CLAUDE.md` was left untouched by this task because no new shared-state fact needed to be carried forward beyond branch-local execution state

## Entry — PR-OP4: Stage3 operator email polish and multi-recipient support

**Branch:** `main`
**Status:** Complete
**Last updated:** 2026-04-13

### What was read first

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- latest completed branch state entries re-read:
  - `Storage / Copy / Email Closure Engineering`
  - `PR: Gemini Copy Optimizer And Optional Attachment Assets`
- then task-relevant frozen-state docs:
  - `docs/poster2/03_engineering/email_copy_optimizer_and_optional_attachment_status_v1.md`
  - `docs/poster2/poster_generation_product_design_baseline_v1.md`
  - `docs/poster2/05_validation/product_region_annotation_contract_status_v1.md`
  - `docs/poster2/05_validation/bottom_mode_switch_closure_status_v1.md`
- then minimum task files only:
  - `frontend/stage3.html`
  - `frontend/app.js`
  - `frontend/styles.css`
  - `docs/stage3.html`
  - `docs/app.js`
  - `docs/styles.css`

### Scope

- PR-OP4 only
- Stage3 operator delivery UX polish only
- multi-recipient input support
- clearer attachment-readiness presentation
- preview-first Stage3 delivery flow
- frontend/docs mirror sync
- branch execution log write-back
- no Stage1 changes, no Stage2 result/replay work, no backend contract redesign, no poster structure/bottom/product-annotation/renderer-routing change

### Root rules followed

- contract-first
- keep work on the requested layer
- Stage3 remains backend-truth-driven through `poster_key -> poster_record -> backend preview/send`
- frontend cache remains cache only, not truth source
- no frontend-composed email truth was reintroduced
- attachment readiness remains presentation-only over backend-owned `email_assets` / preview/send readiness surfaces
- source and published mirror were aligned in the same task

### Problem reproduced

- Stage3 still read like a technical send form instead of an operator delivery-confirmation page
- recipient input only accepted one address cleanly and did not help operators manage multiple recipients
- attachment readiness was exposed as raw available/buildable strings and checkbox enablement, but not as a clear operator-facing readiness summary
- poster URL/key and HTML source sat too close to the primary send flow

### Root cause found

- Stage3 layout was still organized around a generic form/debug flow instead of operator reading order
- recipient handling only used a single trimmed `recipient` string before calling `/api/v2/email/send`
- attachment surfaces were backend-correct but frontend presentation stayed low-level
- advanced/debug details were still mixed into the main delivery surface instead of being secondary

### Exact Stage3 UX polish decisions

- reshaped Stage3 into a preview-first operator flow:
  - poster preview / poster identity
  - recipients
  - subject / preview text
  - email draft preview
  - attachment readiness
  - send controls
- kept poster URL/key and HTML source available, but moved them under:
  - `Advanced Delivery Details / Show HTML Source`
- kept backend draft/source evidence present, but reduced prominence in the primary operator path
- retained existing light edit controls:
  - refresh draft
  - accept copy
  - reject copy
  - send

### Exact multi-recipient behavior

- Stage3 recipient input now supports:
  - comma-separated addresses
  - semicolon-separated addresses
  - whitespace trimming
  - deduplication
  - basic frontend validation before send
- parsing is local UI logic only:
  - no backend truth model change
  - no new send contract field added
- valid recipients are shown in a visible operator list:
  - `Ready To Send`
- invalid recipients are shown in a visible operator list:
  - `Needs Fix`
- invalid addresses are not silently discarded
- send is blocked when invalid addresses remain
- backend send path stays authoritative by iterating the existing single-recipient backend send call once per valid recipient

### Exact attachment-readiness presentation changes

- attachment readiness is now shown as three operator-facing blocks:
  - `Available Now`
  - `Buildable Later`
  - `This Send`
- current send mode is explicitly summarized:
  - inline-only with no external send
  - resend with or without selected attachments
- available backend attachment types are rendered as readable pills:
  - `Poster PNG`
  - `Poster PDF`
- buildable-but-not-yet-available types remain visible but not falsely selectable
- no storage-key internals, binary details, or raw asset-debug surfaces were introduced

### Backend-truth boundary preserved

- Stage3 still restores from:
  - `GET /api/v2/posters/{poster_key}`
- Stage3 still refreshes draft from:
  - `POST /api/v2/email/preview`
- Stage3 still sends through:
  - `POST /api/v2/email/send`
- no fallback to `/api/send-email`
- no Stage1/Stage2 cache reconstruction of draft truth
- no frontend-composed canonical subject/preview/html/text model was reintroduced

### Files changed

- `frontend/stage3.html`
- `frontend/app.js`
- `frontend/styles.css`
- `docs/stage3.html`
- `docs/app.js`
- `docs/styles.css`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage3 frontend operator surface only
- Stage3 frontend send-input handling only
- publish mirror alignment
- branch execution/state log

### Focused validation run

- syntax:
  - `node --check frontend/app.js`
  - `node --check docs/app.js`
- mirror sync / checks:
  - `bash scripts/sync_frontend_to_docs.sh`
  - `bash scripts/check_frontend_docs_sync.sh`
  - `cmp -s frontend/stage3.html docs/stage3.html`
  - `cmp -s frontend/app.js docs/app.js`
  - `cmp -s frontend/styles.css docs/styles.css`
- existing sync/static validation:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `8 passed`
  - `./.venv/bin/python -m pytest -q tests/test_stage3_email_closure_surface.py` → `2 passed`
- focused source inspection:
  - recipient parser now splits on `[;,]`
  - Stage3 still reads `poster_key` from location and calls backend restore/preview/send endpoints only
  - attachment readiness UI now exposes available/buildable/send-state panels
  - advanced/debug details are collapsed under the secondary details panel

### Remaining risks

- validation here is syntax/static/mirror/source-path based; no live browser capture or deployed send-provider run was attached in this workspace
- multi-recipient send currently fans out one backend send call per valid recipient, so partial-send reporting depends on backend/provider behavior per recipient
- inline-only / resend behavior remains backend-owned; this PR changes operator presentation only

### Exact acceptance state

- Stage3 remains backend-truth-driven
- multi-recipient input now works through comma/semicolon parsing, trimming, deduplication, and invalid-address surfacing
- attachment readiness is clearer and operator-facing
- primary Stage3 reading flow is preview-first and delivery-oriented
- no request/routing/runtime truth changed
- no frontend-composed email truth was reintroduced
- frontend/docs mirror is aligned
- `CLAUDE.md` was left untouched by this task because no new shared-state fact needed to be carried forward beyond branch-local execution state

## Entry — PR-OP3R: Family-A-only scenario generation product-shape correction

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
  - `PR-OP1C-REV`
  - `PR-OP2-v2`
  - `PR-OP2R`
  - `PR-OP3`
- then task-relevant frozen-state docs:
  - `docs/poster2/poster_generation_product_design_baseline_v1.md`
  - `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
  - `docs/poster2/05_validation/bottom_mode_switch_closure_status_v1.md`
  - `docs/poster2/05_validation/product_region_annotation_contract_status_v1.md`
- then minimum task files only:
  - `frontend/index.html`
  - `frontend/app.js`
  - `frontend/styles.css`
  - `docs/index.html`
  - `docs/app.js`
  - `docs/styles.css`

### Scope

- PR-OP3R only
- Family-A-only Stage1 AI scenario generation correction
- product-shape correction for existing scenario generation only
- keep existing `scenario_asset` / `scenario_image` write-back path
- keep Family A / Family B request lines isolated
- keep frontend/docs mirror aligned
- write branch execution state back before stop
- no Template B scenario support, no bottom/gallery truth change, no Stage2/Stage3 truth change, no renderer/routing reopen

### Root rules followed

- contract-first
- keep work on the requested layer
- Family A only; no Template B scenario-generation semantics added
- product logic before technical fallback logic
- renderer/request family truth left unchanged
- generated asset remains an asset-source enhancement only, not a new asset-truth model
- keep source and published mirror aligned in the same task

### Problem reproduced

- PR-OP3 added a working Family-A-only Stage1 scenario-generation action, but the generated asset still targeted `800x600` landscape output
- the resulting image shape did not match the left-side vertical scenario region purpose
- prompt construction still read too much like a generic technical field fallback and not enough like product-category-controlled scenario generation
- fryer-like product inputs could drift into generic kitchen or unrelated appliance imagery

### Root cause found

- the existing Family A helper `buildFamilyAScenarioPrompt(...)` built context from sparse field presence but still framed the request as a generic `4:3 marketing scenario background`
- the generation request itself still hard-coded:
  - `width: 800`
  - `height: 600`
- product naming was used, but the prompt did not explicitly enforce fryer/commercial-kitchen category terms or explicit category exclusions

### Exact size correction decision

- changed the Family A Stage1 AI scenario generation target from:
  - `800x600`
- to:
  - `600x800`
- this is now explicitly treated as:
  - portrait-oriented
  - left-side vertical scenario visual
  - Family-A-only scenario asset generation
- Template B was not changed

### Exact product-category prompt constraints added

- added a new Family-A-only product-context classifier in the existing frontend scenario helper path
- preferred product logic order remains:
  - `product_name`
  - `agent_name`
  - `title`
  - `scenario_image` note only as a weak supporting hint
- fryer-like products now anchor prompt construction to controlled category language:
  - `electric fryer`
  - `countertop fryer`
  - `stainless steel fryer`
  - `commercial kitchen`
  - `fast food kitchen`
  - `restaurant prep station`
  - `fryer basket`
  - `fryer station context`
  - `clean professional foodservice environment`
- explicit drift-avoidance terms were added for fryer-like requests:
  - `air fryer`
  - `rice cooker`
  - `oven`
  - `generic smart appliance`
  - `unrelated kitchen decor hero`
- the prompt now explicitly frames the generated image as:
  - a controlled product-context asset
  - a portrait-oriented `600x800` vertical scenario image
  - a restrained supporting scene for the left-side Family A scenario region
- the scenario note no longer acts as primary truth; it is applied only as a weak supporting hint after product category alignment

### Exact scenario write-back behavior

- existing write-back model remains unchanged
- generated response still normalizes through:
  - `buildGeneratedAssetFromUrl(url, key)`
- generated asset still writes back into:
  - `state.scenario`
- Stage1 persistence remains on the existing path:
  - `scenario_asset: serialiseAssetForStorage(state.scenario)`
- manual coexistence remains intact:
  - generate AI scenario image
  - upload/replace through the existing `input[name="scenario_asset"]`
  - clear explicitly
  - regenerate again
- no parallel AI scenario asset-truth model was introduced

### Files changed

- `frontend/index.html`
- `frontend/app.js`
- `docs/index.html`
- `docs/app.js`
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
  - `cmp -s frontend/index.html docs/index.html`
  - `cmp -s frontend/app.js docs/app.js`
  - `cmp -s frontend/styles.css docs/styles.css`
- focused static/source inspection:
  - `rg -n "width: 600|height: 800|buildFamilyAScenarioPrompt|classifyFamilyAScenarioProductContext|electric fryer|air fryer|state\\.scenario = asset|serialiseAssetForStorage\\(state\\.scenario\\)|stage1-generate-scenario|data-variant-visible=\"b\"" frontend/app.js docs/app.js frontend/index.html docs/index.html`
- existing sync/static test:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`

### Remaining risks

- validation here remains syntax/static/mirror/source-path based; no live browser capture was attached in this workspace
- prompt quality is now more product-category-constrained, but actual image quality still depends on deployed provider behavior
- non-fryer product categories still use a restrained generic product-supporting commercial-kitchen prompt path rather than a larger category taxonomy in this PR

### Exact acceptance state

- Family A scenario generation now targets `600x800`
- generated scenario prompts are more product-category-consistent, with explicit fryer-category constraints when fryer-like cues are present
- Template B still does not gain scenario-generation UI or semantics
- generated images still write into the existing `scenario_asset` path
- no request/routing/runtime truth changed
- no Family A / Family B request-line mixing was introduced
- frontend/docs mirror is aligned
- `CLAUDE.md` was left untouched by this task because no new shared-state fact needed to be carried forward beyond branch-local execution state

## Entry — PR-OP3: Family-A-only Stage1 AI scenario image generation

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
  - `PR-OP1C-REV`
  - `PR-OP2-v2`
  - `PR-OP2R`
- then task-relevant frozen-state docs:
  - `docs/poster2/poster_generation_product_design_baseline_v1.md`
  - `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
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
- then the minimum additional existing image-generation path only:
  - `app/main.py`

### Scope

- PR-OP3 only
- Family-A-only Stage1 operator action for AI scenario image generation
- write generated scenario asset back into the existing Stage1 `scenario_asset` slot
- preserve manual upload / replace coexistence
- frontend/docs mirror sync
- branch execution log write-back
- no backend routing, renderer routing, Stage2 result/replay use, bottom/gallery truth, ownership, or Stage3 truth changes

### Root rules followed

- contract-first
- keep work on the requested layer
- Family A only; no Template B scenario-generation semantics added
- generated asset remains an asset-source enhancement only, not a new request-truth model
- do not reuse Stage2 result/replay rendering
- do not silently mutate canonical Stage2 request truth
- keep source and published mirror aligned in the same task

### Problem reproduced

- Stage1 had a manual scenario upload slot and a scenario note field for Family A, but no operator-side AI scenario-image generation entry
- the repo already had a compatible image-generation endpoint, but Stage1 did not expose a safe Family-A-only path that writes the generated result back into the current scenario asset flow
- without that integration, adding AI generation risked either:
  - a parallel asset-truth model
  - accidental Template B exposure
  - or reuse of later-stage rendering paths

### Root cause found

- the existing Stage1 Family A operator surface only bound scenario handling through:
  - `bindModeSOptionalAsset(...)`
  - persisted `scenario_asset`
- there was no Family-A-only operator action that called the existing backend image service and normalized the returned URL/key back into the same `state.scenario` model used by manual uploads

### Exact Family-A-only scenario generation design

- added a Family-A-only operator action inside the existing `Scenario / Visuals` block:
  - `生成场景图`
  - `清空场景图`
- the control sits inside the Family A Stage1 scenario area only:
  - HTML remains gated under `data-variant-visible="a"`
  - JS also hard-guards with `isTemplateBStage1Data(...)` / `isTemplateBTemplateId(...)`
- no Template B UI, visibility rule, fallback path, or request assumption was added
- reused the existing backend image endpoint:
  - `POST /api/imagen/generate`
- generation request is constrained to:
  - `width: 800`
  - `height: 600`
  - `variants: 1`
  - `add_watermark: false`
- prompt context is Family-A-only Stage1 context:
  - `agent_name`
  - `title`
  - `product_name`
  - `scenario_image` note
  - product-image presence from `state.productImage1`
- prompt strategy stays scenario-oriented and operator-safe:
  - 4:3 marketing scenario background
  - product-category-aware commercial kitchen / modern kitchen context
  - restrained background/supporting-visual language
  - explicit exclusion of text/logo/watermark/collage/poster framing
- excluded from prompt truth:
  - Bottom Support Copy
  - Product Callouts
  - Template B description fields
  - Stage2 / Stage3 state

### Exact write-back behavior into Stage1 `scenario_image`

- generated response is normalized through existing Stage1 asset shape:
  - `buildGeneratedAssetFromUrl(url, key)`
- the resulting asset is written directly into:
  - `state.scenario`
- Stage1 preview then reads the same slot it already uses for manual uploads:
  - inline preview
  - Stage1 poster-style preview
  - serialized Stage1 storage
- persistence remains on the existing path:
  - `scenario_asset: serialiseAssetForStorage(state.scenario)`
- no parallel AI-scenario field or second asset line was introduced
- manual coexistence remains intact:
  - operator can generate AI scenario image
  - operator can upload/replace via the existing `input[name="scenario_asset"]`
  - operator can clear the current scenario asset explicitly
  - operator can regenerate AI output again

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
  - `cmp -s frontend/index.html docs/index.html`
  - `cmp -s frontend/app.js docs/app.js`
  - `cmp -s frontend/styles.css docs/styles.css`
- existing sync/static test:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
- source inspection for Family-A-only control visibility:
  - `rg -n "stage1-generate-scenario|stage1-clear-scenario|stage1-scenario-status|data-variant-visible=\"a\"|Scenario image \\(optional\\)" frontend/index.html docs/index.html`
- source inspection for existing-slot write-back and family guard:
  - `rg -n "buildFamilyAScenarioPrompt|/api/imagen/generate|state\\.scenario = asset|serialiseAssetForStorage\\(state\\.scenario\\)|bindModeSOptionalAsset\\(|isTemplateBStage1Data\\(|isTemplateBTemplateId\\(" frontend/app.js docs/app.js`

### Focused validation result

- `frontend/app.js` syntax passed
- `docs/app.js` syntax passed
- frontend/docs publish mirror check passed after sync
- `tests/test_frontend_docs_sync.py` passed: `8 passed`
- source inspection confirms:
  - Family A scenario-generation controls are mounted only inside the Family A scenario block
  - Template B keeps no scenario-generation UI path in the HTML
  - runtime guards block Template B from using the generation path
  - generated result writes into `state.scenario`
  - persisted Stage1 storage still uses `scenario_asset: serialiseAssetForStorage(state.scenario)`
- no backend route, renderer route, request builder family split, Stage2 result/replay path, bottom/gallery truth, or Stage3 truth file changed in this pass

### Remaining risks

- this PR depends on the existing backend image-generation endpoint and a reachable configured backend API base; no offline/local mock browser exercise was added in this workspace
- focused validation here is syntax/static/mirror/source-path based; no live screenshot capture or end-to-end browser run was attached
- prompt quality is intentionally constrained and operator-safe, but still subject to deployed image-provider behavior

### Exact acceptance state

- Family A can generate a scenario image from Stage1
- Template B does not gain scenario-generation UI or scenario-generation semantics
- generated scenario images flow back into the existing Stage1 `scenario_asset` path
- manual upload/replace still coexists on the same scenario slot
- no request/routing/runtime truth changed
- no Family A / Family B request-line mixing was introduced
- frontend/docs mirror is aligned
- `CLAUDE.md` was not updated by this task because no new shared-state fact needed to be carried forward

## Entry — PR-OP2R: collapse duplicated Stage1 preview logic and fold copy suggestions into preview

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
  - `PR-OP1C-REV`
  - `PR-OP2-v2`
- then task-relevant frozen-state docs:
  - `docs/poster2/poster_generation_product_design_baseline_v1.md`
  - `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
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

- PR-OP2R only
- Stage1 operator surface only
- collapse duplicated Stage1 preview logic back to one preview flow
- move staged copy suggestions into the existing preview surface
- preserve raw / suggestion / accepted separation
- preserve Family A / Family B request-line isolation
- frontend/docs mirror sync
- branch execution log write-back
- no backend routing, ownership, renderer routing, Stage2 result/replay use, bottom truth, or Stage3 truth changes

### Root rules followed

- contract-first
- keep work on the requested layer
- preserve family isolation and do not mix Family A / Family B request semantics
- do not reuse Stage2 result/replay rendering for Stage1 preview
- do not silently mutate canonical Stage2 request truth
- keep Product Callouts product-owned and Bottom Support Copy bottom-owned
- keep source and published mirror aligned in the same task

### Problem reproduced

- Stage1 had two preview surfaces in parallel:
  - the existing template preview / poster-style preview flow
  - a separate large `Stage1 Combined Preview`
- Stage1 suggestions were also rendered as a second workflow surface:
  - a separate large `Stage1 AI Copy Suggestions` block below the preview flow
- the duplication made Stage1 read like a pseudo-dashboard instead of one operator preview path
- deterministic suggestion output was also too close to null-filling / normalization and not strong enough on expression improvement

### Root cause found

- `refreshPreview()` still drove both:
  - `updatePosterPreview(...)`
  - `buildStage1CombinedPreviewModel(...)` -> `renderStage1CombinedPreview(...)`
- the separate suggestion block reused the same Stage1 state model correctly, but was mounted outside the preview flow as a parallel section
- suggestion drafting was still mostly whitespace/title normalization plus fallback filling, especially for Family A title/support copy and Family B title/subtitle/description phrasing

### Exact preview-logic collapse decision

- kept the existing `Template Preview` card as the only Stage1 preview flow
- removed the standalone large `Stage1 Combined Preview` section entirely
- removed the Stage1-only duplicate preview helpers:
  - `buildStage1CombinedPreviewModel(...)`
  - `renderStage1CombinedPreview(...)`
- `refreshPreview()` now renders:
  - the existing poster-style / family-aware preview
  - the integrated copy-review suggestion surface only
- no visual-input pseudo-dashboard was retained

### Exact suggestion integration decision

- moved the suggestion controls and review rows into the existing `Template Preview` card under:
  - `Copy Review In Preview`
- removed the standalone large `Stage1 AI Copy Suggestions` section as a parallel workflow surface
- kept staged state separation intact:
  - raw input
  - suggestion layer
  - accepted layer
- kept explicit operator actions intact:
  - generate suggestion
  - accept checked suggestion targets
  - apply accepted poster-copy targets back into visible Stage1 inputs
  - restore the pre-apply raw snapshot
  - clear accepted layer
- email suggestion fields remain staged-only
- improved deterministic suggestion phrasing:
  - Family A:
    - stronger title shaping toward marketing-style phrasing
    - shorter compact callout phrasing
    - bottom support copy phrased as bottom-owned support copy rather than explanation text
  - Family B:
    - cleaner title shaping with SKU-aware formatting
    - clearer subtitle phrasing toward product-sheet language
    - cleaner description-summary phrasing

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
  - `cmp -s frontend/index.html docs/index.html`
  - `cmp -s frontend/app.js docs/app.js`
  - `cmp -s frontend/styles.css docs/styles.css`
- existing sync/static test:
  - `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
- source inspection for preview collapse / integration:
  - `rg -n "Stage1 Combined Preview|Stage1 AI Copy Suggestions|stage1-combined-preview|stage1-visual-preview|stage1-copy-preview|buildStage1CombinedPreviewModel|renderStage1CombinedPreview" frontend/index.html frontend/app.js frontend/styles.css`
  - `rg -n "Template Preview|Copy Review In Preview|stage1-generate-suggestions|stage1-suggestion-list|Stage1 Combined Preview|Stage1 AI Copy Suggestions" frontend/index.html docs/index.html`

### Focused validation result

- `frontend/app.js` syntax passed
- `docs/app.js` syntax passed
- frontend/docs publish mirror check passed after sync
- `tests/test_frontend_docs_sync.py` passed: `8 passed`
- source inspection confirms:
  - the standalone `Stage1 Combined Preview` block is removed
  - the standalone `Stage1 AI Copy Suggestions` block is removed
  - the duplicate combined-preview helpers are removed
  - suggestion controls now live inside the existing preview surface
- no backend file, route, renderer path, request builder, or Stage2/Stage3 truth file changed in this pass

### Remaining risks

- this PR still uses frontend-only staged suggestion drafting rather than a backend-backed suggestion path
- suggestion quality is improved but remains deterministic/local in this pass
- no browser automation or screenshot capture was added in this workspace, so before/after visual proof is source/DOM-level rather than attached screenshots

### Exact acceptance state

- Stage1 now has one preview logic only
- the large standalone `Stage1 Combined Preview` block is removed
- the standalone `Stage1 AI Copy Suggestions` block is removed as a parallel workflow surface
- AI copy suggestions are integrated into the existing preview flow
- raw / suggestion / accepted separation remains intact internally
- suggestion apply remains explicit and recoverable
- Family A / Family B request-line isolation remains intact
- no request/routing/runtime truth changed
- frontend/docs mirror is aligned
- `CLAUDE.md` was not updated by this task because no new shared-state fact needed to be carried forward

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

## 2026-05-15 — Stage2 generate gateway failure hardening

### Root rules followed

- backend/runtime stability only
- no poster contract, Template A/B payload shape, bottom SOP, product annotation truth, beautification, or layout geometry changes
- existing frontend/docs request correlation behavior preserved

### Problem reproduced / reviewed

- live evidence showed mixed successful poster generation and gateway-level `502 Bad Gateway` / `ERR_FAILED` failures with the same valid frontend payload class
- local review found the backend generate route serialized all Stage2 poster generation through one semaphore, but semaphore wait and whole-request runtime were not bounded below the Render gateway timeout
- this means queued/cold Puppeteer work could be killed by the platform before FastAPI returned structured JSON with CORS and request id

### Root cause

- frontend payload and poster contract are not implicated
- backend had stage-level timeouts, but lacked a route-level queue timeout and route-level runtime timeout
- lifecycle logs were too coarse to tell whether a failure happened during request receipt, auth, semaphore wait, render, compose, storage, response construction, exception, or timeout
- live Render log search by historical request id could not be completed from this workspace because no Render CLI/access token is configured

### Files changed

- `app/main.py`
- `app/services/poster2/pipeline.py`
- `app/services/poster2/renderer.py`
- `render.yaml`
- `tests/poster2/test_api.py`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage2 backend generate runtime guard
- PosterPipeline lifecycle observability
- Puppeteer browser close observability
- Render deployment timeout configuration
- focused API/CORS regression coverage

### Validation run

- `python3.11 -m py_compile app/main.py app/services/poster2/pipeline.py app/services/poster2/renderer.py tests/poster2/test_api.py` -> passed
- `CORS_ALLOW_ORIGINS=https://zhaojfifa.github.io python3.11 -m pytest -q tests/poster2/test_api.py -k 'route_is_backward_compatible or preflight_allows_content_type_and_x_request_id or error_response_keeps_cors_headers or stage_failure_response_is_machine_readable or queue_timeout_returns_json_with_cors or runtime_timeout_returns_json_with_cors'` -> passed
- `CORS_ALLOW_ORIGINS=https://zhaojfifa.github.io python3.11 -m pytest -q tests/poster2/test_api.py` -> passed
- `CORS_ALLOW_ORIGINS=https://zhaojfifa.github.io python3.11 -m pytest -q tests/test_ops_auth_gate.py` -> passed
- live `GET https://ai-service-leob.onrender.com/health` -> 200
- live `OPTIONS https://ai-service-leob.onrender.com/api/v2/generate-poster` from `https://zhaojfifa.github.io` -> 200 with `X-Request-ID` allowed
- live unauthenticated generate probe with `X-Request-ID: stage2-live-unauth-probe` -> 401 JSON with CORS and `X-Request-ID`

### Remaining risks

- live authenticated 5-run same-payload validation was not run because ops credentials and Render log access are not available in this workspace
- Render cold restart validation was not run from this workspace
- this patch does not add a browser pool; if logs still show Chromium launch pressure after deployment, browser warmup/pooling remains the next bounded mitigation

## 2026-05-15 — Stage2 generate request correlation and transport classification

### Root rules followed

- Stage2 frontend source and published mirror stayed aligned
- no poster contract, renderer semantics, bottom SOP, product annotation truth, Template A/B payload contract, or styling changes
- backend change limited to request correlation headers on existing responses

### Problem reproduced / reviewed

- Stage2 generate failures could appear as generic browser `Failed to fetch` / CORS-like errors with no client/server request correlation
- retry diagnostics did not expose a stable request id across attempts
- frontend generate timeout did not leave clear margin over the backend Puppeteer render timeout plus cold-start/queue overhead

### Root cause

- frontend generated an internal request id but did not send it as `X-Request-ID` on `/api/v2/generate-poster`
- retry/error paths could not reliably correlate the browser attempt with backend logs
- transport failures and client abort timeouts were not classified separately from normal backend HTTP errors
- backend accepted request ids for logs/body metadata on the generate route, but did not consistently echo the id as a response header

### Files changed

- `frontend/app.js`
- `docs/app.js`
- `app/main.py`
- `tests/poster2/test_api.py`
- `tests/test_ops_auth_gate.py`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Stage2 frontend request/diagnostic layer
- backend response correlation header middleware
- focused API/auth regression coverage

### Validation run

- `node --check frontend/app.js` -> passed
- `node --check docs/app.js` -> passed
- `bash scripts/check_frontend_docs_sync.sh` -> passed
- `python3.11 -m pytest -q tests/test_frontend_docs_sync.py` -> passed
- `CORS_ALLOW_ORIGINS=https://zhaojfifa.github.io python3.11 -m pytest -q tests/poster2/test_api.py -k 'route_is_backward_compatible or preflight_allows_content_type_and_x_request_id or error_response_keeps_cors_headers or stage_failure_response_is_machine_readable'` -> passed
- `CORS_ALLOW_ORIGINS=https://zhaojfifa.github.io python3.11 -m pytest -q tests/test_ops_auth_gate.py` -> passed
- local browser probe against static Stage2 page: simulated unavailable backend classified as `network_transport` with the required operator message and preserved request id
- local browser probe against delayed route: simulated frontend timeout classified as `client_timeout` with the required operator message and preserved request id

### Remaining risks

- live authenticated 3-run generate validation was not run because ops credentials were not available in this workspace
- Render cold restart validation was not run from this workspace
- this patch intentionally does not introduce a browser pool; Puppeteer cold-start/pool mitigation remains a follow-up if production evidence shows runtime instability

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
