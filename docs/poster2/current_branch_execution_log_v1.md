# Current Branch Execution Log v1

## Entry — Family B Product Announcement Variant Contract Review

**Task:** `POSTER2-FAMILY-B-ANNOUNCEMENT-CONTRACT-REVIEW`
**Status:** Complete — review only, no runtime implementation
**Last updated:** `2026-06-15`

### Scope

- Independently reviewed the docs-only Catalog Campaign Poster Set orchestration spec and the canonical
  Family B Product Announcement Variant Contract before any runtime slice.
- No runtime code, template spec, renderer, API, Stage3, registry, or email-send path changed.

### Root rules followed

- Read repo/poster2 anchors first, including `AGENTS.md`, `CLAUDE.md`, `README.md`,
  `docs/poster2/README.md`, product baseline, Family A architecture anchor, product annotation status,
  bottom behavior status, current branch log, Family B historical status, orchestration spec, variant
  contract, and real `.eml` grammar assessment.
- Stayed contract-first and review-only; did not inspect or modify renderer/runtime for implementation.

### Problem reproduced

- The proposed Announcement contract correctly reuses dormant Family B and avoids mega-poster,
  Stage3/send-action, `.eml` shell, renderer, and API scope creep.
- Review found the proposed structure completeness too narrow for existing Family B governance:
  mandatory slots were framed as logo/title/SKU/primary hero only, while Family B requires a core
  information area via spec or copy. Since Announcement excludes spec, the copy-region claim/body path must
  be required for structure completeness.

### Root cause found

- The new variant contract treated the three commercial copy slots as the main delta but did not fully carry
  forward Family B's broader "spec or copy region" completeness rule into `announcement_variant_contract_review`.
- The contract also needs explicit acceptance evidence for `materials_strip_region = collapsed_by_design`,
  `tariff_mode = on_request` only in v1, and display-only CTA / no Stage3 action binding.

### Files changed

- `docs/poster2/family_b_product_announcement_variant_contract_review_v1.md`
- `docs/poster2/current_branch_execution_log_v1.md`

### Layer changed

- Documentation / architecture review only.

### Validation run

- Document review only; no automated tests run because no runtime code changed.

### Verdict

- **APPROVE WITH REQUIRED CHANGES**

### Remaining risks

- Family B remains dormant and parity-sensitive; runtime should not start until the variant contract requires
  copy-region core information, collapsed-materials evidence, Family B parity target-map additions for the
  three new slots, and explicit no-Stage3 CTA proof.

## Entry — Composition Priority Layer + template_dual_v2_product_hero

**Branch:** `poster2-composition-priority-v1`
**Status:** Complete (all gates green; committed, not pushed; awaiting Owner approval)
**Last updated:** `2026-06-14`

### Scope

- Add the request-level Composition Priority Layer ("海报风格策略": Balanced / Studio /
  Product Hero / Catalog Clean) that re-prioritises the poster (product first, scenario
  atmosphere, gallery evidence, strong title, premium) via a non-geometric CSS-var bundle,
  plus the `template_dual_v2_product_hero` variant. Target studio ~4.3 -> >=4.5; reached.

### Exact changes

- NEW `app/services/poster2/composition.py`: closed-enum strategies -> bundle of
  `--scenario-image-treatment` / `--product-primary-shadow` / `--title-stack-gap`;
  `balanced` = {}; non-geometry whitelist + report.
- `contracts.py`: `PosterSpec.composition_strategy`; `RenderManifest.composition_strategy`.
- `template_behavior.py`: `composition_strategy` kwarg + merge LAST (Family A); threaded at
  the renderer (x3) + pipeline call sites. `schemas/poster2.py` + `main.py`: additive request
  + response field; `pipeline.py`: manifest report.
- NEW template `template_dual_v2_product_hero` (full/un-floated product + studio CSS
  title-52/light-gallery; html/svg/slot_spec/anchor_map byte-identical to base); registry
  entry + `CAMPAIGN_EXPLAINER_TEMPLATE_IDS`; registry snapshot test updated.
- Stage2 UI: `#poster2-composition-strategy` "海报风格策略" select (stage2.html) -> payload
  `(template_id, composition_strategy)` (app.js); frontend + docs mirrored byte-identically.
- NEW `scripts/poster2_composition_review.py`; NEW `tests/poster2/test_composition.py`;
  review package `docs/poster2/composition_priority_layer_review_v1.md`.

### Layer changed

- Composition (request-level, non-geometric CSS-var bundle) + one bounded Family A template
  variant. No region geometry/ownership, bottom SOP, annotation truth, or visible_item_count
  change. Base/airy/studio unaffected.

### Validation performed

- Stability 10x base/studio/product_hero (real Puppeteer, stubbed R2): 100% / deterministic /
  validator pass. 26/26 geometry-ownership-composition invariants PASS (composition proven
  non-geometric). Scenario saturation receded to 0.54x base.
- Operator review: product_hero product focus 4.6, scenario 2.5, bottom 2.5, title 4.5,
  premium 4.6 — all targets met.
- node/sync/py_compile pass; 60 focused tests pass; zero new suite failures vs main baseline;
  browser selector can choose the strategy (Playwright-verified).

### One-line execution summary

- Added a non-geometric Composition Priority Layer + `template_dual_v2_product_hero`, raising
  Product Hero to ~4.6/5 with every protected geometry/ownership guard proven unchanged.

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

## HX-20260615-POSTER2-EMAIL-GRAMMAR-REVIEW (assessment only)

### Type

- `assessment_only` / `review` — no runtime, renderer, registry, Stage3, or API change.

### Input inspected directly

- `/Users/tylerzhao/harness-x/input/poster2_email_samples/20260615/`
  - `Fw_ Fwd_ Quand les plats ont besoin d'un petit coup de chaud !.eml`
  - `NOUVEAUTÉ ! LES BLENDERS … CUISTANCE.eml`
  - `NOUVEAUTÉ ! LES COUPES FRITES … CUISTANCE.eml`
  - `NOUVEAUTÉ ! LES CUISEURS À RIZ … CUISTANCE.eml`
- Parsed MIME parts (text/plain + text/html), decoded image roles, links, tracking pixels.

### Key findings

- The three `NOUVEAUTÉ` emails are **one Mailchimp template filled with three products**
  (blender / coupe-frites / cuiseur à riz): stable section order + stable 5-image role map
  (shared banner img0, unique product hero img1, unique detail img2, shared footer logo img3,
  1×1 tracking pixel img4). This is the strongest "stable repeatable poster grammar" evidence.
- The `coup de chaud` email is the **same Technitalia/Codimatel campaign already analyzed**
  as `catalog_hero_v1` (`reference_analysis_v1` / `template_classification_v1`). It is a
  catalog-hero mega-poster that folds Hero Explanation + Product Matrix into one image.

### Verdict

- Stable poster grammar: **YES** (strongest on the single-product `NOUVEAUTÉ` Product Sheet).
- Existing strategy compatible: **PARTIAL** (NOUVEAUTÉ → Family B Product Sheet anatomy match;
  catalog hero → unreachable on frozen square canvas, needs portrait family already gated).
- New flow needed: **PARTIAL** — no new renderer; "Catalog Campaign Poster Set" is best an
  **orchestration layer above Families A/B**, not a new template engine.

### Net gaps recorded

- No structured spec-table contract (dims/volume/power/reference rows).
- No reference/SKU slot; no tariff/"price on request" slot.
- No portrait canvas / RegionDefinition (blocks Catalog Hero variant A).
- No campaign-level orchestration (shared bundle → N posters).
- Family B (Product Sheet) is dormant and would need re-activation for variants B/C.

### Output

- New formal doc: `docs/poster2/real_email_to_poster_grammar_assessment_v1.md`
- `docs/poster2/README.md` updated (new review-only index entry).

### Owner decision pending

- Approve Poster Set as orchestration layer (docs-only first); choose Announcement-first vs
  Spec-first; re-activate Family B; keep portrait Catalog Hero gated.

### Confirmation

- No implementation code was changed. Stop point honored after report + execution log.

## Owner decision + orchestration spec (2026-06-15, docs-only)

### Owner decision

- APPROVE **Catalog Campaign Poster Set** as the next product direction.
- Do not implement runtime code yet.
- First implementation candidate = **Product Announcement / Family B reactivation**.
- Do not build portrait Catalog Hero mega-poster now.
- Do not redesign Stage3 email. Do not use `.eml` HTML as a runtime template.

### Deliverable (docs-only)

- New formal architecture doc:
  `docs/poster2/02_architecture/catalog_campaign_poster_set_orchestration_spec_v1.md`
- Turns `real_email_to_poster_grammar_assessment_v1.md` into a formal product architecture:
  shared product input bundle → multiple simple poster variants → per-variant contract + diagnostics,
  rolled up under a campaign manifest. **Fan-out, not fusion** (no mega-poster). Orchestration layer sits
  above Families A/B; it never renders and has no authority over their geometry/ownership/SOP/annotation truth.

### Grounding correction recorded

- Family B (`template_product_sheet_v1`) is **dormant, not greenfield**. It already has a frozen region order
  (`logo_banner_region → top_copy_region → materials_strip_region → product_hero_region → description_region`),
  an existing **SKU slot** (`sku_text`), `template_b_parity_review` + visible-truth diagnostics, and an
  API-routable independent path. "Reactivation" = reopen-not-redesign.
- Announcement variant needs only **three new text/copy slots** inside frozen Family B regions:
  availability badge ("EN STOCK"), tariff line ("Tarif = Nous contacter", enum price|on_request), and
  on-poster CTA text ("Nous contacter" mailto display — copy only, NOT a Stage3 send action).
- The structured **spec-table** (Dimensions/Volume/Puissance/Référence labeled rows) is the only genuinely new
  contract; it is **deferred** to the Featured Spec variant, gated on its own contract doc.

### Index

- `docs/poster2/README.md` updated with the new 02_architecture index entry.

### Next docs-gated steps (not started)

- Family B Announcement variant contract doc (bundle→slot map, 3 new copy slots, collapse rules, diagnostics).
- Campaign manifest + variant-selection contract doc (roll-up schema, per-variant diagnostics, shared palette_token).

### Confirmation

- No runtime/template/registry/API/Stage3 code changed. Docs-only.

## Orchestration approved + two docs-gated contracts authored (2026-06-15, docs-only)

### Owner action

- APPROVE the docs-only orchestration spec. **Catalog Campaign Poster Set** is now the approved product
  direction for real-email-derived poster generation.
- Approved invariants: orchestration layer is above Family A / Family B; it does not render; does not own
  geometry; does not change bottom SOP; does not change product annotation truth; does not redesign Stage3
  email; each variant must still run through the existing single-poster contract path.
- Next approved work is docs-gated only: (1) Family B Announcement Variant Contract,
  (2) Campaign Manifest + Variant Selection Contract. No runtime implementation yet.

### Deliverables (docs-only)

- `02_architecture/catalog_campaign_poster_set_orchestration_spec_v1.md` — status stamped **APPROVED (Owner, 2026-06-15)**.
- `02_architecture/family_b_announcement_variant_contract_v1.md` — NEW.
  - Reactivate-not-redesign on `template_product_sheet_v1`; frozen region order preserved.
  - Reuses existing logo/SKU(`sku_text`)/title/subtitle/hero(+inset)/description slots.
  - Adds only three optional **copy** slots: `availability_badge_slot`, `tariff_line_slot`
    (enum price|on_request), `cta_text_slot` (display-only; not a Stage3 send).
  - Spec-table excluded (deferred to Featured Spec). Diagnostics = `announcement_variant_contract_review`.
- `02_architecture/campaign_manifest_and_variant_selection_contract_v1.md` — NEW.
  - Closed-enum variant selection → fan-out (one existing single-poster resolve per variant; layer never renders).
  - `campaign_manifest` references per-variant diagnostics (never merges); no-silent-drop / partial-set semantics.
  - Shared non-geometric `palette_token` (Composition Priority pattern); per-variant `poster_record` reused
    read-only + thin referencing manifest; no Stage3/closure change.

### Index

- `docs/poster2/README.md` updated with both new 02_architecture entries and the APPROVED stamp.

### Confirmation

- No runtime/template/registry/API/Stage3 code changed. All field/id names are proposed (docs-only), not committed API.

## POSTER2-FAMILY-B-ANNOUNCEMENT-VARIANT-CONTRACT-V1 (docs-only)

### Owner gate

- Catalog Campaign Poster Set orchestration is approved as docs-only architecture; runtime implementation NOT
  approved yet. This task defines the first implementable poster variant contract and stops for Owner approval
  of an implementation slice.

### Required reading completed

- `AGENTS.md`, `CLAUDE.md`, `docs/poster2/README.md`, `current_branch_execution_log_v1.md`,
  `catalog_campaign_poster_set_orchestration_spec_v1.md`, `real_email_to_poster_grammar_assessment_v1.md`,
  `poster_generation_product_design_baseline_v1.md`, `template_b_design_baseline_v1.md`,
  `05_validation/template_b_contract_correction_status_v1.md`,
  `05_validation/template_b_line2_independent_flow_status_v1.md`.

### Grounding facts confirmed from Family B status docs

- Family B template `template_product_sheet_v1` is an independent, contract-driven line.
- Frozen region order: `logo_banner_region → top_copy_region → materials_strip_region → product_hero_region → description_region`.
- `header_mode = logo_banner_lockup`; emits `top_copy_contract_review` (`sku_text_layer`/`top_copy_title_layer`/
  `top_copy_subtitle_layer`), `description_contract_review` (`description_title_layer`/`description_body_layer`),
  `bottom_contract_review` scoped `description_region_only`.
- Real Template B v2 payload fields (dedicated serializer): `brand_name`, `agent_name`, `title`, `subtitle`,
  `sku_text`, `description_title`, `description_body`, `product_image`, `product_secondary_image`, `materials_images`.
- Product hero bounds `{x:112,y:348,w:800,h:384}`; reason codes `single_hero_centered_without_secondary_asset` /
  `…_with_secondary_inset`. Puppeteer disabled in the Template B renderer selector (Pillow operator path today).

### Deliverable

- NEW canonical doc: `02_architecture/family_b_product_announcement_variant_contract_v1.md`.
  - Defines: purpose; mapping to the Cuistance `NOUVEAUTÉ` grammar; required shared + variant fields; the three
    minimal new copy slots (`availability_badge`, `tariff_line`, `on_poster_cta_text` — display-only, not a Stage3
    send); reused Family B regions/slots; field→SKU/title/subtitle/materials/product/description mapping; explicit
    non-goals; `announcement_variant_contract_review` diagnostics; first-slice acceptance criteria; stop point.
  - Spec-table excluded (deferred to Featured Spec). Reactivate-not-redesign; no geometry/ownership/region-order change.
- SUPERSEDED: `02_architecture/family_b_announcement_variant_contract_v1.md` (earlier short sibling) banner-marked
  and folded into the canonical doc to avoid two competing contracts.
- `docs/poster2/README.md` index updated (canonical entry + superseded note).

### Confirmation

- No code, template spec, renderer, API, registry, or Stage3 change. Docs-only. All field/id names proposed, not committed.

## Family B Announcement contract — Owner-required doc-fix slice (2026-06-15, docs-only)

### Owner verdict

- APPROVE WITH REQUIRED CHANGES. Do not start runtime. Apply four required doc changes, then return for approval.

### Four required changes applied to `family_b_product_announcement_variant_contract_v1.md`

1. `structure_complete` now anchored on a named **Family B core information area** (§6.1):
   brand_logo_slot + sku_text_layer + top_copy_title_layer + primary hero must render; gaps listed in
   `missing_core_information_members`. Reflected in diagnostics (§9) and acceptance (§10.2a).
2. `materials_strip_region` collapse is now **explicit `collapsed_by_design` evidence** (reason_code + count:0),
   never silent, never a structure failure (§7, §9, §10.3a).
3. **tariff v1 = `on_request` only**; `price` deferred and rejected (no silent fallback) (§4, §5.2, §10.3b, §11.3).
4. `on_poster_cta_text` now **provably display-only**: evidence carries `render_kind: display_text_only` +
   `stage3_binding: none`; acceptance requires a with/without test proving identical Stage3 behavior (§5.3, §9, §10.4).

### Housekeeping

- §11 open decisions 3 and 6 marked RESOLVED by changes 3 and 2.
- §12 compliance checklist extended with the four required-change rows.
- Cross-references normalized (evidence consolidated in §9; no phantom §9.1/§9.2).

### Confirmation

- Docs-only. No code, template spec, renderer, API, registry, or Stage3 change. Doc returns for Owner approval before runtime.

### Alignment with reviewer doc (`family_b_product_announcement_variant_contract_review_v1.md`)

- The Owner review artifact was found in the workspace (`docs/poster2/family_b_product_announcement_variant_contract_review_v1.md`,
  created by the reviewer — left untouched). Re-read its §4 to align the four changes to the reviewer's exact intent.
- Correction made: review §4.1 requires the core to ALSO include a `description_region` copy core (>=1 of
  `description_title_layer` from `copy.feature_claims[0]` or `description_body_layer` from `copy.description`).
  §6.1 updated so a poster with only brand + SKU + headline + product image FAILS structure. §3 footnote added
  (at least one of those two fields must render). §9 diagnostics + §10.2a updated accordingly.
- CTA evidence aligned to the reviewer's named fields: `cta_action_bound: false` + `stage3_send_untouched: true`
  (replacing the earlier `stage3_binding`), plus `render_kind: display_text_only`.
- Materials acceptance (§10.3a) strengthened per review §4.2: region order unchanged on collapse; no spec-table/
  contact/gallery routed into `materials_strip_region`; parity reports the collapsed state.
- Added reviewer Owner-decision items to §11 (phone/contact footer deferred — not a 4th slot; palette_token
  default = existing `industrial_sheet_*`) and a matching §8 non-goal.

### Confirmation

- Docs-only. No code, template spec, renderer, API, registry, or Stage3 change. Reviewer artifact left untouched.
  Doc returns for Owner approval before runtime.

## Family B Product Announcement variant — FIRST RUNTIME SLICE implemented (2026-06-15)

### Owner gate

- APPROVE FIRST RUNTIME SLICE WITH STRICT SCOPE. Implementation landed exactly inside the approved allowed list.

### Files changed (code)

- `app/schemas/poster2.py` — request fields `availability_badge`, `tariff_mode` (Literal["on_request"], price
  rejected at schema), `on_poster_cta_label`, `on_poster_cta_email`; response `announcement_variant_contract_review`.
- `app/services/poster2/contracts.py` — PosterSpec fields + RenderManifest field + pure helper
  `resolve_announcement_copy_slots()` + budgets + `TEMPLATE_B_TARIFF_ON_REQUEST_TEXT`.
- `app/main.py` — thread the 4 new request fields into PosterSpec; pass `announcement_variant_contract_review`
  into the response.
- `app/services/poster2/renderer.py` — 3 Pillow draw blocks; 3 visible-truth selectors; HTML builder placeholders.
- `app/services/poster2/pipeline.py` — `_build_announcement_variant_contract_review()`; 3 parity targets +
  `announcement_copy_in_region` summary; 3 visible-truth keys; manifest wiring.
- `app/templates_html/template_product_sheet_v1.html` / `.css` / `slot_spec.template_product_sheet_v1.json` —
  3 new optional slots (availability badge in top_copy; tariff + CTA in description lower band).
- `tests/poster2/test_pipeline.py` (+5 tests), `tests/poster2/test_api.py` (+1 schema test).

### Scope honored

- existing `template_product_sheet_v1` only; existing `/api/v2/generate-poster` path only; 3 additive copy slots
  only; tariff `on_request` only (price rejected, no silent fallback); display-only CTA (no Stage3 binding);
  announcement diagnostics; parity target-map additions; with/without tests; explicit materials collapse evidence;
  explicit `cta_action_bound=false` + `stage3_send_untouched=true`.
- Not done by design (out of approved list): no Stage1/Stage2 operator UI; no new renderer/family/registry; no
  Stage3/email change; no price; no phone/contact footer; no spec-table; no Product Matrix; no portrait Catalog
  Hero; no Family A/bottom/product-annotation truth change; `.eml` HTML not used as runtime template.

### Validation

- `py_compile` of all changed backend modules: OK.
- New tests: 6 passed (3 slots render-when-supplied; collapse-by-design when absent; materials collapse evidence;
  structure_complete requires description copy core — fail + pass; tariff on_request accepted / price rejected).
- Full `tests/poster2/` + `test_stage2_guard_diagnostics_surface.py`: baseline = 53 failed / 550 passed;
  after change = 53 failed / 556 passed. Failure-set diff (baseline vs change) = EMPTY -> **zero regressions**,
  +6 new passing. The 53 failures are pre-existing on branch `poster2-heavy-reconstruction-v1` (e.g. `_build_html`
  signature-drift tests), unrelated to this slice.

### Returns for Owner approval

- Slice is implemented and green. Optional follow-ups noted for Owner: Stage1/Stage2 operator UI for the 3 fields;
  localization of the on_request tariff phrase.

## Family B Product Announcement — runtime RESULT VALIDATION (2026-06-15)

### Task

- POSTER2-FAMILY-B-ANNOUNCEMENT-RESULT-VALIDATION-V1 — render the implemented variant through the existing
  /api/v2/generate-poster path and visually validate operator-usability. No contract/slot/Stage3 change.

### What was done

- Added helper `scripts/poster2_announcement_runtime_validation.py` (runs the real PosterPipeline on
  `template_product_sheet_v1`, Pillow operator path, with a synthesized recognizable rice-cooker packshot + logo).
- Saved artifacts under `docs/poster2/assets/announcement_runtime_v1/`: `sample_payload.json`, `final_poster.png`
  (1024x1024), `diagnostics.json`, `visual_review.md`.
- Stage2 browser screenshot: NOT produced (conditional) — the 3 new fields have no Stage2 input surface in this
  slice (operator UI deferred), so a capture would not exercise the variant; justification recorded in the review.

### Result

- `structure_complete=true`, `deliverable=true`; announcement core information area intact; all three copy slots
  render ("EN STOCK", "Tarif : nous contacter", "Nous contacter · commercial@cuistance.eu"); materials
  collapsed_by_design; CTA proven display-only (cta_action_bound=false, stage3_send_untouched=true).
- Visual review (all 9 questions answered in visual_review.md): reads as a product announcement; product
  undistorted; SKU/availability/title/claim/tariff/CTA all visible; title hierarchy strong.

### Environment finding (not a template limitation)

- The workspace `app/assets/fonts/` lacked the font pack, and a stale `NotoSansSC-Regular.ttf` rendered Latin
  advance-widths with no outlines (invisible small text). Aligning Regular to the working variable font (exactly
  what `scripts/fetch_fonts.sh` intends — both names = the same VF) fixed it. Operator deployments must have the
  font pack present. Font files are untracked/ignored (not committed).

### Verdict

- **OPERATOR-TRIAL READY** (with documented, non-blocking polish opportunities). Higher campaign-style punch
  (product prominence, denser composition) is template-geometry-bound and intentionally out of this slice's scope.

### Scope compliance

- No new template family / Poster Set runtime / Stage3-email / price / phone-contact-footer / Product Matrix /
  portrait Catalog Hero / Family A-bottom-product-annotation change. No `.eml` HTML used as a template.
  This validation task added zero runtime-code modifications (only a helper script + artifacts + local font assets).

## Family B Product Announcement — OPERATOR UI CLOSURE (2026-06-15)

### Branch

- `poster2-family-b-announcement-ui-closure-v1` (branched from `poster2-heavy-reconstruction-v1` @ 1d99fdd).
- Not pushed; no PR. Owner performs human validation before remote push.

### Scope (operator UI only; existing Family B + existing /api/v2/generate-poster path)

- Stage1 (`index.html`): Family-B-only fieldset `#s1-template-b-announcement` (`data-variant-visible="b"`):
  `availability_badge`, `tariff_on_request` checkbox (→ `tariff_mode=on_request`; no price entry),
  `on_poster_cta_label`, `on_poster_cta_email`.
- `app.js`: state defaults/reads/rehydrate; `collectStage1Data` + `serialiseStage1Data` carry the 4 fields;
  `buildTemplateBPosterPayload` + the Template B `posterPayload` map them into the v2 request; Stage2 summary
  (`buildTemplateBStage2State` / `renderTemplateBStage2Summary`) shows them.
- `stage2.html`: read-only `#s2-b-availability` / `#s2-b-tariff` / `#s2-b-cta`.
- `stage2_request_helpers.js`: request summary surfaces the fields.
- Mirrored to `docs/` via `sync_frontend_to_docs.sh`; sync check passes.

### Validation

- `node --check` frontend/docs app.js + stage2_request_helpers.js: OK. Frontend/docs sync: in sync.
- Browser (Playwright, static frontend, mocked endpoints) — `announcement_ui_closure_v1/ui_validation_result.json`:
  Family B announcement fields visible, Family A bottom/callouts hidden; all 4 fields fillable; the persisted
  Stage1 snapshot (the object Stage2 consumes) carries `availability_badge/tariff_mode/on_poster_cta_label/email`;
  no JS errors (only offline resource 404/DNS). Literal /api/v2/generate-poster request capture not obtained
  (offline multi-base probe aborts before POST) — snapshot proof + reviewed mapping + backend render cover it.
- Backend render of the same payload → `announcement_ui_closure_v1/final_poster.png` + `diagnostics.json`:
  structure_complete, 3 slots rendered, CTA display-only (cta_action_bound=false, stage3_send_untouched=true),
  materials collapsed_by_design.
- Focused tests: `tests/test_family_b_announcement_ui_wiring.py` (new) + docs-sync + announcement backend = 15 passed.
- Regression delta (tests/poster2 + stage2 + frontend-sync + new UI test): before slice 53 failed; after slice
  **53 failed / 573 passed** — failure-set unchanged, **zero regressions** (53 are pre-existing on the
  heavy-reconstruction branch); passed grew from the added test files.

### Artifacts

- `docs/poster2/assets/announcement_ui_closure_v1/`: stage1_or_stage2_input_screenshot.png,
  stage2_request_preview_screenshot.png, final_poster.png, diagnostics.json, sample_payload.json,
  validation_notes.md, ui_validation_result.json.

### Hard-forbidden compliance

- No remote push / PR / deploy. No Poster Set runtime / campaign_manifest runtime / multi-poster. No new template
  family / renderer. No Stage3/email/send change. No price. No phone/contact footer. No Product Matrix / portrait
  Catalog Hero. No Family A / bottom SOP / product-annotation change. `.eml` HTML not used as runtime template.
  No `.DS_Store` / local fonts committed.

## Family B Announcement — LIVE E2E GAP DIAGNOSIS (2026-06-15)

### Verdict: DEPLOYMENT MISMATCH (stop at Step 1)

- Deployed backend `ai-service-leob.onrender.com` reports `build-info`: branch `kit1.0`, sha `0cbaf65`,
  built 2026-01-24 — predates announcement work (and even `main` @ 21ebba2).
- Deployed OpenAPI: `availability_badge` / `tariff_mode` / `on_poster_cta_label` / `on_poster_cta_email` /
  `announcement_variant_contract_review` = ALL ABSENT (sku_text/description_title present → older Template-B build).
- Deployed served `/index.html`: announcement fieldset + input ids ABSENT.
- Git: `origin/poster2-family-b-announcement-ui-closure-v1` = `1fdeb84` (pushed), but Render is NOT serving it.

### Root cause

- Old deployed backend has no announcement schema → Pydantic silently drops the fields (extra=ignore) → poster
  renders without EN STOCK / Tarif / CTA; response has no `announcement_variant_contract_review`. The "UI appears
  present" was a different (newer) frontend build than the Render-served one.

### Remediation (Owner)

- Repoint/redeploy Render to commit `1fdeb84` (currently pinned to `kit1.0`/`0cbaf65`); publish the matching
  `docs/` frontend; then re-run live E2E. Verify via `/build-info.json` + `/openapi.json` grep `availability_badge`.

### Evidence artifacts (untracked, not committed)

- `docs/poster2/assets/announcement_live_e2e_diagnosis_v1/live_e2e_gap_diagnosis.md`
- `docs/poster2/assets/announcement_live_e2e_diagnosis_v1/live_e2e_probe_evidence.json`
- `docs/poster2/assets/announcement_live_e2e_diagnosis_v1/remote_build_info.json`

### Compliance

- Evidence-only. No code change, no push, no deploy. No Stage3 / Poster Set / Catalog Hero / Family A / bottom SOP
  / geometry change.

## Family B Announcement — REMOTE UI FILL VALIDATION + operator-clarity fix (2026-06-15)

### Trigger

- Remote redeployed correct code (OpenAPI now has announcement fields), but operators typed generic product text
  into the announcement fields because labels/guidance were not explicit enough.

### Change (frontend copy + minimal CSS only)

- Stage1 fieldset relabeled 「公告展示条 · Announcement strip」 with a "not product description" warning; bilingual
  field labels (库存徽标 · Availability badge / 报价行 · Tariff line / 联系按钮文案 · CTA label / 联系邮箱 · CTA email);
  placeholders set to the exact examples (EN STOCK / Nous contacter / commercial@cuistance.eu); removed
  邮件/Stage3/发送 wording; red-accent card + tinted warning for visual distinction. Stage2 summary labels clarified.
  No field-name / mapping / backend-schema / geometry change.

### Validation

- node --check frontend+docs app.js: OK. Frontend/docs sync: in sync. Focused tests (UI wiring + docs sync +
  announcement backend): 15 passed.
- Local Playwright: improved labels asserted; exact sample filled; Stage1 snapshot carries the 4 values; Stage2
  summary shows EN STOCK / 按需报价 (Tarif : nous contacter) / Nous contacter · commercial@cuistance.eu / SKU.
- Backend render (real pipeline): announcement_variant_contract_review present; 3 slots rendered; cta_action_bound
  false; stage3_send_untouched true; materials collapsed_by_design. final_poster.png shows EN STOCK / Tarif / CTA.
- Live remote: backend confirmed current via OpenAPI; authenticated live generate is the Owner step
  (POST /api/v2/generate-poster returns 401 ops_auth_required; no prod credentials here). build-info.json is a
  stale static file.

### Artifacts

- `docs/poster2/assets/announcement_remote_ui_validation_v1/` (stage1/stage2 screenshots, request payload,
  response diagnostics, final_poster.png + page screenshot, remote_build_info.json, validation_notes.md).
- `docs/poster2/assets/announcement_live_e2e_diagnosis_v1/` (prior deploy-gap diagnosis evidence).

### Compliance

- No backend schema / renderer geometry / template family / Stage3 / price / phone-footer / Poster Set / Family A /
  bottom SOP / product-annotation change. Not pushed, not deployed, no PR/merge.

## POSTER2-CATALOG-HERO-ADDITIVE-FAMILY + 1TO1-REPLICATION-P1 (2026-06-15)

### catalog_hero_v1 additive family (READY_TO_REVIEW; HOLD deploy)
- Additive portrait family `catalog_hero_v1` (family `catalog_hero_portrait`) registered in
  `template_registry.py`; dedicated render path `app/services/poster2/catalog_hero.py` dispatched by an
  additive branch in `generate_poster_v2` — never enters PosterPipeline (Family A/B byte-unchanged).
- Portrait spec `app/templates/specs/catalog_hero_v1.json` (1240x1754). Reuses request schema + slot vocabulary;
  food hero owner-gated (scenario_image only, no runtime AI); annotation frozen at 3; CTA display-only.
- Response: optional `catalog_hero_contract_review` + `catalog_hero_grammar_profile` (12-dim). Frontend Stage1
  card + Stage2 selector entry added to `frontend/` + `docs/` registry (byte-identical) + preview svg.
- Tests: `tests/poster2/test_catalog_hero.py` 18/18 pass; registry snapshot updated additively.
- Regression: post-change poster2 suite 51 failures == clean-base 51 failures (set-diff empty) → ZERO new
  failures; the 51 are pre-existing branch-state failures. Proof:
  `docs/poster2/assets/catalog_hero_productization/family_b_unchanged_proof.txt`.
- Visual: `catalog_hero_generated.png` (chromium) reads as catalog-hero grammar, not Family B sheet;
  end-to-end HTTP handler verified (200, valid PNG data URL, storage ok).

### 1:1 replication P1 (PPT route; docs/artifacts only)
- Applied PPT 1:1 method (reference dimension extraction -> fillable contract). Target reference =
  Technitalia LES RECHAUDS GAZ page_1 (present; no new reference needed).
- Score: current synthetic output ~3.0/5 (NOT commercial); implemented grammar ~4.4; real-asset ceiling
  ~4.3-4.7 (reconstruction proved 4.47). Gap is ASSET-bound, not grammar-bound.
- Missing dims classified: asset-related (food hero, product cutout, gallery, logo) dominate; template/typography
  (title per-line escalation, callout 3-vs-6 owner gate, mass balance, leader polish) are minor in-grammar.
- Deliverables: `05_validation/catalog_hero_1to1_replication_gap_review_v1.md`,
  `02_architecture/catalog_hero_1to1_replication_plan_v1.md`,
  `05_validation/catalog_hero_p1_hardening_acceptance_v1.md`,
  artifacts under `assets/catalog_hero_1to1_replication_v1/` (annotated ref+current, scorecard, owner-assets,
  dimension mapping).
- Recommendation: Option B (collect real assets A1-A4 + decision D1) THEN run a real-asset static trial of the
  unchanged grammar; harden (Option A) only after the trial reaches >=4.3. No runtime change, no deploy, no push.

### Compliance
- No Family A/B / Stage3 / Poster-Set / renderer-geometry / runtime-AI-asset change. Not merged, not pushed,
  not deployed.

## POSTER2-CATALOG-HERO-REAL-ASSET-STATIC-TRIAL-V1 (2026-06-15)

- Ran the real-asset static trial: UNCHANGED catalog_hero_v1 grammar
  (`app/services/poster2/catalog_hero.py`) fed REAL operator assets (CUISTANCE fryer line at
  /Users/tylerzhao/poster/: golden-food lifestyle scene, double-basket fryer cutout, 3 real
  range fryers, CUISTANCE logo). Offline harness `scripts/poster2_catalog_hero_real_asset_trial.py`;
  chromium engine, not degraded. D1=3 callouts, D3=food/title high mass + product secondary.
- Result: ~3.8/5, BELOW the 4.3 gate (large lift over ~3.0 synthetic). Family reads correctly.
- Failure class (per acceptance, <4.3 → no runtime hardening): NOT asset quality and NOT a
  fundamental grammar limit — three IN-GRAMMAR defects exposed by real assets:
  (1) logo renders as white block (white-bg JPG x white-on-charcoal filter) = renderer asset-handling;
  (2) left callout labels collide with the food rail = layout; (3) title line crowding / no
  per-line escalation = typography. Plus one asset/content gap: golden food vs red-leaning food
  (caps food-title color coupling).
- Recommendation: bounded STATIC grammar-refinement pass (logo normalization, callout-vs-food
  re-anchor, title line-height/escalation) + re-trial; HOLD runtime hardening until re-trial >=4.3.
  Optionally a red-leaning food asset for the 4.3->4.6 ceiling.
- Artifacts: docs/poster2/assets/catalog_hero_real_asset_trial_v1/ (input_assets_manifest.md,
  real_asset_static_output.png, real_asset_vs_reference.png, real_asset_vs_synthetic.png,
  real_asset_scorecard.md, dimension_pass_fail_matrix.md, owner_decision_needed.md, trial_diagnostics.json).
- Compliance: no production renderer / pipeline / Stage1-2-3 / Family A/B / runtime-AI change;
  real assets only (no synthetic-as-real, no AI assets); callout count not increased; not merged,
  not pushed, not deployed.

## POSTER2-CATALOG-HERO-REAL-ASSET-GRAMMAR-REFINEMENT-V1 (2026-06-16)

- Bounded STATIC grammar-refinement pass on the offline catalog-hero render (same real CUISTANCE
  assets; D1=3; D3 food/title high mass, product secondary). Refinements live ONLY in
  `scripts/poster2_catalog_hero_refine_trial.py`; production `app/services/poster2/catalog_hero.py`
  is byte-UNCHANGED (still HOLD).
- R1 logo normalization (polarity-aware white chip for dark-on-light logos; no destructive invert)
  -> CUISTANCE logo reads (was white block). R2 callout anchoring (3 labels stacked in the
  food<->product gap, leaders to product edge, clamped out of the food rail) -> callouts belong to
  product (was colliding with food). R3 title per-line escalation + safe line-height (LES 56 ->
  FRITEUSES/ELECTRIQUES 134, no overlap) -> clean dominant title (was crowded). Each maps to a
  grammar dimension (#7/#10, #9/#2, #3) with before/after artifacts.
- Re-score vs Technitalia reference: ~3.8 -> ~4.16/5. Still BELOW the 4.3 gate. Lifts: title
  3.8->4.5, callout 2.5->4.0, readiness 3.0->4.0. Remaining drag = food-title COLOR COUPLING
  (criterion 1 = 3.0): golden food vs reference red-leaning food.
- Remaining-blocker class = ASSET QUALITY (food color coupling), not typography/layout/callout-system
  (those now PASS). Per acceptance (<4.3): do NOT recommend runtime hardening yet. Recommend Owner
  supply ONE red-leaning food asset (no AI), re-trial; if >=4.3, approve porting R1/R2/R3 into
  catalog_hero.py (runtime hardening).
- Artifacts: docs/poster2/assets/catalog_hero_real_asset_refinement_v1/ (before/after/refined/
  vs-reference PNGs, refinement_scorecard.md, dimension_delta_matrix.md, logo/callout/title notes,
  owner_decision_needed.md, refine_diagnostics.json).
- Compliance: static harness + artifacts only; no production renderer/pipeline/Stage1-2-3/Family A/B
  change; no runtime AI asset; callout count = 3; not merged, not pushed, not deployed.

## POSTER2-CATALOG-HERO-RED-FOOD-ASSET-GATE-V1 (2026-06-16)

- Asset-gate + static validation. Defined food-hero acceptance criteria (C1-C8: red/warm,
  cooked/appetite, portrait-croppable, left-rail, couples #E1002A title, not overpower product,
  no embedded text, licensed+owner-approved).
- Surveyed the Owner asset kit (/Users/tylerzhao/poster/): only ONE red-leaning candidate exists,
  demo图/tomato-600x600.jpg (vivid red, but RAW produce, stock/unlicensed, thematically off for
  fryers). Other food images = golden fryer scenes (not red) or AI mockups with embedded text
  (the kitchen-1/2 -> rejected C7+AI).
- Ran a static trial reusing the EXACT refined grammar (R1+R2+R3) + same product/logo/gallery/
  title/3-callouts, swapping ONLY the food hero to the red tomato candidate (analysis-only, not
  commercial, not runtime truth). Production catalog_hero.py byte-UNCHANGED.
- Result: food-title color coupling 3.0 -> 4.4; overall 7-crit ~4.09 -> ~4.27/5 (right AT the gate).
  VALIDATES the red-food hypothesis: a red food clears the coupling blocker with zero grammar change.
- But NOT a deploy recommendation: the candidate fails C8 (stock/unlicensed/unapproved), C2 partial
  (raw not cooked), theme partial (tomato<->fryer incoherent). Remaining blocker reclassified =
  a LICENSED, COOKED, thematically-matched red-leaning food asset (asset provenance/theme), NOT
  grammar/typography/callout/product. Do NOT recommend runtime hardening on the tomato.
- Recommendation: Owner supplies/approves a licensed red-leaning cooked on-theme food (ODN-1) or an
  approved offline AI candidate (ODN-2, prompts provided, candidate-only), re-trial; if >=4.3,
  approve hardening (port R1/R2/R3 into catalog_hero.py).
- Artifacts: docs/poster2/assets/catalog_hero_red_food_asset_gate_v1/ (food_asset_acceptance_criteria.md,
  candidate_food_asset_review.md, red_food_static_output.png, red_food_vs_previous.png,
  red_food_vs_reference.png, red_food_scorecard.md, owner_decision_needed.md, red_food_diagnostics.json).
- Compliance: static harness + artifacts only; no production renderer/pipeline/Stage1-2-3/Family A/B
  change; no runtime AI asset; candidate marked analysis-only pending approval; callout count = 3;
  not merged, not pushed, not deployed.

## POSTER2-REFERENCE-REPLICATION-COMPOSITE-ROUTE-REVIEW-V1 (2026-06-16)

- Route-level architecture review (docs only; no runtime/Family A/B/Stage3/deploy). Compared three
  routes: A Master/PPT 1:1 (extraction, flat ceiling), B Product Sheet/Family B (stability+operator,
  ~4/10 campaign ceiling), C Catalog Hero (campaign grammar, ~4.16 static / ~4.27 red-food / 4.47
  reconstruction). Verdict: none reaches 4.8 alone -> COMPOSITE.
- Composite route: Reference -> PPT 1:1 extraction (offline, advisory) -> visual grammar dimensions
  -> replication_kernel (blueprint, proposal) -> operator approval -> contract runtime family ->
  owner-gated asset layer -> Puppeteer precision render -> diagnostics+score gate. Ownership split:
  PPT owns extraction; grammar owns typography/color/beauty/annotation vocab; contract owns
  region_graph + frozen truth + A/B isolation; Puppeteer owns precision render; asset layer owns
  asset_semantic_profile (owner-gated); operator owns owner_gates+diagnostics.
- Defined the replication_kernel data structure (canvas/object_graph/region_graph/typography/color/
  asset_semantic/layer_stack/annotation_graph/beauty_tokens/fillable_contract/owner_gates/diagnostics)
  with risk classes E/V/O/F/U; mapped it to Family B, Catalog Hero, Product Hero, Studio,
  Reference->Seed, Poster Set (each family = a kernel profile). Incremental build (formalize
  catalog_hero's existing 12-dim profile + contract review first; object_graph/PPT last).
- 4.8 requirements: residual 4.27->4.8 dominated by ASSET semantic match (licensed cooked on-theme
  red food) + PRODUCTION PARITY (runtime port + storage + live render); callout radial-ring + logo
  prominence are minor. Not grammar.
- Recommended next slice: P1a port R1/R2/R3 into production catalog_hero.py + P1b owner-gated Asset
  Gate (gated on cooked-red food asset ODN-1) + P1c runtime parity. Defer Reference->Seed (P3) and
  Poster Set; do NOT build a separate Product Announcement Hero family; keep Family B as-is.
- Deliverables: 02_architecture/poster2_composite_replication_route_v1.md,
  02_architecture/poster_replication_kernel_v1.md,
  05_validation/poster2_route_decision_matrix_v1.md,
  05_validation/catalog_hero_to_4_8_gap_plan_v1.md. README index updated.
- Compliance: docs only; no runtime/Family A/B/Stage3 change; not merged/pushed/deployed.

## POSTER2-REFERENCE-INSPIRED-HYBRID-GENERATION-ROUTE-V1 (2026-06-16)

- Route/design task (docs only; no runtime/external-gen/Family A/B/Stage3/deploy). Reframes Poster2
  from 1:1 reference COPY to reference-INSPIRED controlled generation.
- Key insight: Poster2 already does background-gen + deterministic-foreground composite. The hybrid
  route makes the background a reference-inspired, grammar-guided MODEL generation (warm on-theme
  scene/food) and keeps ALL business elements (logo/title/SKU/CTA/feature text/product identity) as
  DETERMINISTIC overlays via the contract renderer. This dissolves the dominant 4.8 blocker (asset
  semantic matching / cooked-red on-theme food) without sacrificing controllability.
- Firewall: AI output candidate-only until OPERATOR approval; required text/logo never model-rendered;
  product identity preserved (real cutout composited; model renders the zone only); no runtime AI truth;
  no external gen calls without Owner authorization.
- 6-step pipeline: reference/style analysis -> generation plan -> AI scene candidates (no text/logo) ->
  deterministic overlay (Catalog Hero foreground) -> validation (text exact-match, logo presence,
  product identity, visual score, commercial safety, operator approval) -> finalization.
- Output contract reference_inspired_generation_plan {style_profile, composition_intent,
  generated_layers, locked_overlay_layers, prompt, negative_prompt, asset_constraints, validation_rules,
  diagnostics} = a replication-kernel profile split by provenance (generated vs locked).
- Route comparison: hybrid takes B's control + D's visual quality, rejects D's hallucinated
  text/logo/product. Recommended as the MAIN 4.8 path, as an additive third render mode
  (hybrid_generated_bg); deterministic Catalog Hero stays as overlay engine + fallback; Family B
  unchanged; PPT 1:1 = offline style/grammar extractor (conditioning, not truth).
- MVP: 1 line (CUISTANCE fryers), 1 style target (Technitalia grammar), 3-5 generated scenes,
  deterministic overlay, before/after vs deterministic Catalog Hero, >=4.3 + beats baseline + 100%
  text accuracy + operator approval. Needs Owner authorization of a generation model before running.
- Deliverables: 02_architecture/reference_inspired_hybrid_generation_route_v1.md,
  02_architecture/hybrid_generation_contract_v1.md,
  05_validation/hybrid_vs_replication_route_review_v1.md,
  05_validation/hybrid_generation_mvp_plan_v1.md. README index updated.
- Compliance: docs only; no runtime/external-gen/Family A/B/Stage3 change; not merged/pushed/deployed.

## POSTER2-HYBRID-REAL-ASSET-MVP-HEAVY-VALIDATION-V1 (2026-06-16)

- Heavy real-asset MVP for the reference-inspired hybrid route. Parsed the target .eml truth
  (~/poster/SOP/Fw_ Fwd_ Quand les plats...coup de chaud.eml): Technitalia/Codimatel "LES RÉCHAUDS GAZ"
  campaign forwarded via Cuistance; slogan "QUAND LES PLATS ONT BESOIN D'UN PETIT COUP DE CHAUD!",
  brand CUISTANCE, CTA www.cuistance.eu / gabriel.tau@cuistance.eu.
- TWO findings: (1) MODEL-ACCESS BLOCKER — no generation backend configured (Vertex project/creds unset,
  OPENAI_API_KEY unset, no local torch/diffusers, no .env); no external call attempted (rules). (2)
  TRUTH-vs-ASSET MISMATCH — email = gas stoves, kit = electric fryers (no gas-stove cutouts). Ran the
  fryer line with the email's transferable truth (slogan/CTA/brand/theme), title LES FRITEUSES ÉLECTRIQUES.
- Delivered Steps 1-3 (truth_copy_extract, asset_manifest, generation_plan.json + generation_prompts) +
  generation_blocker_report + a FALLBACK static composition: 3 real scene photos (Golden fries/scene02/
  scenes03) darkened+blurred as background proxy + deterministic Catalog Hero foreground overlay
  (R1/R2/R3 + legibility scrims). Harness scripts/poster2_hybrid_mvp_fallback.py (no production code touched;
  catalog_hero.py unchanged).
- Result: all 3 fallback candidates PASS all HARD gates (title/slogan/CTA exact, logo present & non-AI,
  product real & non-AI, 3 callouts, scene no text/logo, identity preserved, commercial-safe). Advisory
  best ~4.1 (indicative); ≈ TIE with deterministic Catalog Hero ~4.16; did NOT reach >=4.3 or beat baseline
  — capped by the proxy artifact (real scenes contain fryers -> opaque white panels). A true generated
  empty-zone scene would integrate cleaner.
- VERDICT: HYBRID_MVP_BLOCKED_BY_MODEL_ACCESS. Route not disproven; deterministic-overlay firewall validated;
  generative half untested. Next slice: unblock generation (Owner credential) + resolve truth/asset mismatch,
  then re-run for a real verdict. Route verdict doc: 05_validation/hybrid_real_asset_mvp_result_v1.md.
- Compliance: no deploy/merge/push; no Stage3; no Family A/B mutation; no Poster Set; AI output candidate-only
  (none generated); no external service called; source assets read-only (not overwritten); no secrets printed.

## POSTER2-MODEL-COMPOSED-HYBRID-POSTER-MVP-V2 (2026-06-16)

- Heavier MVP: test the Xingliu-like model-COMPOSED full-poster route (not background-only, not 1:1).
- Re-verified generation access: NONE available (OpenAI/Vertex/Gemini/Stability/Replicate creds all
  unset; no local torch/diffusers; no .env; no agent image tool; no owner-pre-placed candidates).
- Per the task's hard rule ("If generation access is unavailable, stop with blocker report. Do not
  fake success with background proxies"), NO generation attempted and NO proxy candidates fabricated
  (unlike v1's fallback, which this task forbids).
- VERDICT: HYBRID_V2_BLOCKED_BY_GENERATION_ACCESS. Route untested (not disproven). Delivered the
  non-generation artifacts: generation_access_report.md (blocker + unblock options),
  model_prompt_pack.md (full image-to-image + text-to-image prompt pack, locked-element correction
  spec reusing R1/R2/R3, negative constraints incl. "no gas stoves / electric fryer", 3-5 variation
  plan), route_verdict.md, owner_decision_needed.md, validation_diagnostics.json. Generation-dependent
  artifacts (raw/corrected candidates, contact sheets, best_vs_*) explicitly documented as blocked.
- Next slice: Owner configures ONE generation path (recommend OpenAI gpt-image-1 image-to-image) +
  resolves truth-vs-asset mismatch (email=gas stoves, kit=fryers); then run the prompt pack for a real verdict.
- Compliance: no generation call; no proxy faking; no deploy/merge/push; no Stage3; no Family A/B mutation;
  no production code touched (catalog_hero.py unchanged); no runtime truth; no secrets printed; assets read-only.

## POSTER2-HYBRID-GEMINI-REAL-GENERATION-VALIDATION-V1 (2026-06-16)

- Step 0 presence-only check (no secret values printed): GEMINI_API_KEY / GOOGLE_API_KEY NOT visible
  to the agent's profile-initialized non-interactive shell (login shell also unset -> not in profile).
  Owner's interactive-shell export does not propagate to the agent's Bash tool (fresh shell per call).
- Found: google.genai SDK installed + repo provider app/services/image_provider/genai_provider.py
  (reads GOOGLE_API_KEY, model imagen-3.0-generate-001, client.images.generate). No dotenv.
- Wrote a ready-to-run harness scripts/poster2_hybrid_gemini_mvp.py: probe -> 3 reference-inspired
  poster candidates (text-to-image) -> deterministic overlay/correction (logo/title/slogan/product/
  3 callouts/gallery/CTA over the model composition) -> contact sheets + comparisons + diagnostics.
  It maps GEMINI_API_KEY->GOOGLE_API_KEY in-process (never printed) and, with no key, writes honest
  BLOCKED presence/probe reports and exits WITHOUT fabricating candidates (no proxy/fake; ran now -> blocked).
- VERDICT: BLOCKED_KEY_NOT_ON_EXECUTION_PROFILE. Real generation did not run; 0 candidates; no fakes;
  no secret printed/logged/persisted. Unblock (secret-safe): persist export GOOGLE_API_KEY=... to
  ~/.zshrc/~/.zprofile (Owner has the value), then re-run the harness; one command yields real candidates.
- Artifacts: docs/poster2/assets/hybrid_gemini_real_generation_validation_v1/ (generation_env_presence.json,
  route_verdict.md, validation_diagnostics.json, operator_review_form.md [pending]) +
  docs/poster2/assets/hybrid_real_generation_probe_v1/generation_probe_report.json.
- Compliance: no commit/push/merge/deploy; no Stage3; no Family A/B mutation; no production code touched;
  no runtime truth; no proxy/fake candidates; no secret value printed/logged/persisted.

## POSTER2-HYBRID-GEMINI-REAL-GENERATION-VALIDATION-V1 — re-run from Tyler-local CLI (2026-06-16)

- Re-ran from the Tyler-local Claude CLI session (not Harness-X tmux) per Owner: the Owner exported the
  key in THIS shell. Presence (booleans only, no value): GEMINI_API_KEY=True, GOOGLE_API_KEY=True,
  GENAI_IMAGEN_MODEL=imagen-3.0-generate-002. This advances past the prior "key not visible" blocker.
- SDK-surface fix (validation-only; NO production change): installed google-genai is 1.2.0, which uses
  client.models.generate_images(...) + GenerateImagesConfig + aspect_ratio — the app provider
  (app/services/image_provider/genai_provider.py) still targets the older client.images.generate(... size=...)
  surface (AttributeError: 'Client' has no attribute 'images'). Added validation-only shim
  scripts/poster2_genai_imagen_shim.py with the same interface over the correct API; harness now imports it.
  app/ production runtime left unchanged.
- With the shim the harness reached Google's API cleanly. Real probe generate_images -> HTTP 400
  API_KEY_INVALID (service generativelanguage.googleapis.com). Independent client.models.list() against the
  same service ALSO returns 400 API_KEY_INVALID -> the rejection is the credential itself, not the image call.
- Non-exposing structural diagnostics (no value printed): GOOGLE==GEMINI True; no whitespace/quotes;
  matches standard Gemini AIza{39} format = False; length bucket long(>39); Vertex path absent
  (GOOGLE_APPLICATION_CREDENTIALS / GCP_PROJECT_ID / GCP_LOCATION all unset).
- VERDICT: BLOCKED_CREDENTIAL_INVALID. Real generation did NOT run; 0 candidates; no fakes; fallback
  proxy NOT used as proof; no secret value printed/logged/persisted. Hardening NOT recommended (premature
  on zero real output; app provider SDK-surface mismatch must be fixed first).
- Unblock (secret-safe): Option A — supply a Gemini-Developer-valid AIza... key (AI Studio) as
  GOOGLE_API_KEY in this shell, re-run the one harness command. Option B — Vertex: export
  GOOGLE_APPLICATION_CREDENTIALS/GCP_PROJECT_ID/GCP_LOCATION and switch shim to genai.Client(vertexai=True).
- Artifacts: docs/poster2/assets/hybrid_gemini_real_generation_validation_v1/ (route_verdict.md [updated],
  credential_validity_probe.json, scorecard.md, generation_env_presence.json) +
  docs/poster2/assets/hybrid_real_generation_probe_v1/generation_probe_report.json +
  docs/poster2/assets/model_composed_hybrid_mvp_v2/real_generation_run_status_v1.md +
  scripts/poster2_genai_imagen_shim.py.
- Compliance: no commit/push/merge/deploy; no Stage3 change; no Family A/B mutation; no production code
  touched; AI output remains candidate-only; no proxy/fake candidates; no secret value printed/logged/persisted.

## POSTER2-HYBRID-GEMINI — harness fix + execution-context env mismatch found (2026-06-16)

- Task: "Fix Poster2 Gemini Hybrid MVP Harness Only" (allowed files: the two scripts + log + validation
  diagnostic artifacts). No app/ / Stage1-3 / Family A-B / renderer changes; no deploy/merge/push/PR.
- Harness FIXED to the exact verified google-genai 1.x surface:
  - scripts/poster2_genai_imagen_shim.py: default model imagen-4.0-generate-001;
    client.models.generate_images(model, prompt, GenerateImagesConfig(number_of_images=1, aspect_ratio))
    ONLY; dropped imagen-3.0-only knobs (negative_prompt/seed/safety_filter_level/person_generation/
    add_watermark) that imagen-4.0 rejects; api_key = GOOGLE_API_KEY or GEMINI_API_KEY.
  - scripts/poster2_hybrid_gemini_mvp.py: prints PROVIDER, MODEL, GOOGLE/GEMINI presence booleans,
    ERROR_TYPE, ERROR message (first 3000 chars); writes the exact non-secret Google error to
    diagnostics (no longer masked as bare "ClientError"); per-candidate OK/FAILED diagnostics; 5 variants;
    optional in-process credential file loader (POSTER2_GENAI_ENV_FILE or ~/.config/poster2/genai.env)
    to override a stale launch env.
- ROOT CAUSE (proven, no secret values): EXECUTION_CONTEXT_ENV_MISMATCH, not a harness/model/surface bug.
  - Agent context shows GENAI_IMAGEN_MODEL=imagen-3.0-generate-002; Owner shell shows imagen-4.0-generate-001.
  - Agent-context key: does NOT match AIza{39}; length nonAIza_long; GOOGLE==GEMINI.
  - With the agent-context key, client.models.list() (no model involved) -> HTTP 400 API_KEY_INVALID;
    generate_images forced to imagen-4.0-generate-001 -> HTTP 400 API_KEY_INVALID. So it is the KEY, not
    the model/surface. Owner's direct manual imagen-4.0 probes pass -> Google access works with Owner's key.
  - The Claude CLI / agent process was launched with a STALE env (old invalid key + imagen-3.0); the Owner's
    later interactive-shell exports do not reach the already-running process, so each Bash call inherits the
    stale key. No fakes; fallback proxy NOT used as proof; no secret printed/logged.
- Unblock: (A) relaunch the CLI session from the shell holding the working exports so the agent inherits them,
  then re-run; or (B) write working values to ~/.config/poster2/genai.env (the harness now loads them in
  process, file wins) and re-run. Either yields real candidates in one command.
- Artifacts: docs/poster2/assets/hybrid_gemini_real_generation_validation_v1/ (execution_context_env_mismatch.json,
  generation_probe_report.json, route_verdict.md, credential_validity_probe.json, scorecard.md) +
  docs/poster2/assets/hybrid_real_generation_probe_v1/generation_probe_report.json.
- Compliance: harness-only edits; no app/ or Stage1-3 or Family A/B or renderer changes; no deploy/merge/push/PR;
  no fake/proxy candidates; no secret value printed/logged/persisted.

## POSTER2-HYBRID-GEMINI — image extraction fix; REAL generation runs end-to-end (2026-06-16)

- Task: "Fix Imagen Response Image Extraction Only" (allowed files: the two scripts + validation diagnostics
  + log). No app/, Stage1-3, Family A/B, renderer-geometry, or prompt-route changes; no deploy/merge/push/PR.
- Symptom: PIL.UnidentifiedImageError on candidate 1 despite CANDIDATE_OK — a decode-path defect, NOT a
  credential/model/access issue (credential-file override works; imagen-4.0-generate-001 returns real bytes).
- Fix (scripts/poster2_genai_imagen_shim.py): robust extract_image_bytes() that walks every SDK nesting
  (image.image_bytes / image.data / image.bytes / image.bytes_base64_encoded / inline_data.data /
  generated_image.*), base64-decodes string payloads, and validates magic bytes (PNG 89504e47 / JPEG ffd8ff /
  RIFF..WEBP / GIF) before returning (bytes, format); plus a diagnose() that emits SAFE structural info only
  (type names, field presence, length, first-16-byte hex, magic verdict) — never binary, never secrets.
- Harness (scripts/poster2_hybrid_gemini_mvp.py): prints IMAGE_DIAG + writes image_extraction_diagnostics.json;
  saves raw model bytes by detected format (raw_candidate_XX.png) then opens with PIL; per-candidate format/
  length/header_hex/magic_valid diagnostics; decode-failure branch writes raw_candidate_XX_extraction_failure
  .json with full structural diag instead of crashing.
- RESULT: generation_ran=True; provider google-genai Imagen / imagen-4.0-generate-001; probe valid PNG
  (~1.25MB, magic 89504e47); 5 raw candidates (valid PNG, 0.58-0.85MB) + 5 corrected overlays + both contact
  sheets + hybrid_vs_catalog_hero_baseline.png + hybrid_vs_reference.png. No UnidentifiedImageError.
- QUALITY (honest, not the slice goal): best corrected ~3.8/5; does NOT beat deterministic Catalog Hero
  (~4.16) and does NOT reach >=4.3. Cause: imagen-4.0 (verified surface) rejects negative_prompt, so the
  model bakes in garbled placeholder text (e.g. "CAMPAIGN POSTER"/"PREMIUM HEADLINE"/"CLOER") that clashes
  with the deterministic locked overlay. Route now unblocked + exercised; hardening NOT yet recommended.
- Next slice (separate, prompt-route change -> out of scope here): suppress/mask model-generated text
  (e.g. mask/inpaint the AI text regions, or shift to an image-to-image/scene-only background route).
- Compliance: harness-only edits; no app/ / Stage1-3 / Family A-B / renderer-geometry / prompt-route change;
  no deploy/merge/push/PR; no fake/proxy candidates; no secret value printed/logged; no binary printed.

## POSTER2 Template-A Reference-Style Hybrid 4.8 Validation (2026-06-16)

- Goal: prove/disprove that the system can preserve the REFERENCE email-poster's style/quality while
  replacing ALL business truth with Template A inputs. Reference EML = STYLE ONLY (Technitalia/Codimatel
  "LES RÉCHAUDS GAZ" gas stoves — forbidden as final content). Template A = Cuistance electric fryers.
- Method: fetched + analyzed the reference style banners (header bandeau, hero banniere_1, range
  banniere_2); extracted grammar (dark hex header, red skew title + accent word, warm-food co-anchor,
  bright product stage + radial callouts, range/gallery rhythm, contact footer). Generated TEXTLESS warm
  food atmosphere via the validation shim (imagen-4.0-generate-001); fed each as the food-hero into
  app/services/poster2/catalog_hero.py (driven from the harness, NOT modified) so logo/title/product/
  callouts(3)/gallery/CTA stay 100% deterministic Template A. AI produces no text/logo/product.
- Harness (validation-only, candidate-only): scripts/poster2_refstyle_hybrid_4_8_mvp.py. Reuses the
  credential-file loader + genai shim. 3 corrected candidates produced (2 variants hit transient 429
  capacity, not code errors).
- RESULT: route PROVEN VIABLE. Every hard gate passes — reference logo/product/title replaced; no AI fake
  text/logo (AI is textless food only); deterministic overlay owns all business truth; quality rises
  WITHOUT losing content control; no Technitalia/Codimatel/gas leakage. Content-control dims = 5.0.
  Overall best ≈4.1/5 (kitchen_glow); does NOT reach 4.8 this pass. Gap (~0.7) is deterministic-overlay
  polish only: (1) title auto-fit (long 3-line title overlaps), (2) left-callout lane vs food zone
  legibility, (3) white logo chip on the dark header — all in catalog_hero.py (production) => out of scope.
- Artifacts: docs/poster2/assets/template_a_refstyle_hybrid_4_8_v1/ — reference_style_profile.json,
  template_a_input_manifest.md, style_to_template_a_mapping.md, generation_prompt_pack.md,
  raw_atmos_*.png (raw model candidates), corrected_candidate_*.png (deterministic corrected),
  reference_vs_candidate_contact_sheet.png, 4.8_scorecard.md, route_verdict.md, owner_decision_needed.md,
  validation_diagnostics.json.
- Compliance: candidate-only AI; NO app/ production change (catalog_hero driven, not edited); no Stage1-3;
  no Family A/B mutation; no renderer-geometry edit; no deploy/merge/push/PR; no reference business truth
  carried; no secret value printed/logged. Stopped after candidates + scorecard + route verdict.

## POSTER2 email_campaign_composite_v1 — heavy composite build + visual validation (2026-06-16)

- Owner decision: heavy engineering validation slice (not docs-only). Route decided: Puppeteer/HTML
  layered composition = reference style kernel + Template A truth + AI textless visual substrate +
  deterministic layered overlay + screenshot validation. Chose Option C (real additive validation harness;
  no production pipeline/renderer rewrite — those are 170KB+ and out of scope).
- Built: scripts/poster2_email_campaign_composite_v1.py — own layered build_html() with 5 regions
  (banner / campaign_visual / truth_overlay / gallery / footer) on the 1240x1754 catalog-hero canvas;
  reuses app/services/poster2/catalog_hero.py HELPERS ONLY (asset prep/fonts/tokens) — catalog_hero.py
  read+reused, NOT modified. AI substrate via the genai shim + credential loader (~/.config/poster2/
  genai.env, no secret printed); model fallback ladder imagen-4.0-generate-001 -> -fast- -> -ultra-.
  Playwright/Chromium render @2x; emits layer_debug.png + contact sheets.
- Fixed the 3 polish gaps from template_a_refstyle_hybrid_4_8_v1 (~4.1): (1) callouts moved onto the WHITE
  product stage (food substrate confined to a left 430px column) -> readable; (2) title AUTO-FIT
  (min(124, 730/(maxlen*0.54)), lh .90) -> long 3-line title no longer overlaps, ink/red/ink accent;
  (3) CUISTANCE logo on a WHITE rounded chip -> crisp (was a faint inverted box).
- RESULT: route PROVEN & visually ready. Real generation ran (4 substrates: 3x imagen-4.0-generate-001,
  1x fell back to imagen-4.0-fast on a transient 429). 4 composites. Best =
  composite_candidate_02_fries_hero.png at ~4.5/5. Beats deterministic Catalog Hero (~4.16): YES. >=4.3
  YES, >=4.5 YES(boundary), >=4.8 NO. AI = textless substrate only; no leaked text/logo; no
  Technitalia/Codimatel/gas; 100% Template A truth. Gate band 4.5-4.7 -> recommend runtime hardening.
- Next slice (recommended): productionize as an ADDITIVE email_campaign_composite_v1 template family
  (mirror catalog_hero_v1 registration), reuse this build_html; keep AI substrate operator-gated/flagged
  (never truth). Bounded 4.5->4.8 polish: soften food<->white seam, widen callout breathing room, add an
  optional range/spec strip, nudge title lane right. No new AI / no content-control risk.
- Artifacts: docs/poster2/assets/email_campaign_composite_v1/ — raw_substrate_01..04_*.png,
  composite_candidate_01..04_*.png, layer_debug.png, reference_vs_baseline_vs_candidate.png,
  candidate_contact_sheet.png, raw_substrate_contact_sheet.png, scorecard.md, route_verdict.md,
  implementation_notes.md, validation_diagnostics.json.
- Compliance: additive validation harness only; NO production runtime change (catalog_hero/pipeline/
  renderer unmodified); no Stage3/email change; no Family A/B route touched; no deploy/merge/push/PR;
  candidate-only AI; no AI text/logo as truth; no secret printed/logged/persisted.

## POSTER2 email_campaign_composite_v1 — P1 deterministic polish (2026-06-16)

- Owner-approved bounded deterministic polish on the SAME route (no architecture change, no route switch).
  scripts/poster2_email_campaign_composite_v1_p1.py (additive). Reused the 4 REAL textless Imagen
  substrates from the v1 run (operator-gated; no new generation, no secret use this pass). catalog_hero.py
  helpers reused, NOT modified.
- Polish landed + screenshot-validated: (1) soft feathered food->white seam (food layer +150px feather,
  gradient 40->100%, no hard edge); (2) wider callout breathing room (food column 430->392, product left
  600->648, callout lanes pulled off the seam); (3) title lane nudged right (left 470->524, "LES" clears
  the column); (4) optional feature/range strip restating the 3 real sell-points (A/B'd vs no-strip; kept).
- RESULT: best = p1_candidate_02_fries_hero_strip.png ~4.65/5 (up from v1 ~4.5). Beats v1 and Catalog Hero
  (~4.16). >=4.3 / >=4.5 yes; >=4.7 borderline; >=4.8 no. Truth 100% Template A; no fabricated specs; no
  Technitalia/gas; AI textless substrate only.
- Gap to 4.8 is now Owner-gated CONTENT truth (real product specs/dimensions/power + gallery captions to
  make the strip additive rather than a callout recap), not geometry. Recommend runtime hardening:
  productionize as an additive email_campaign_composite_v1 template family (mirror catalog_hero_v1).
- Artifacts (docs/poster2/assets/email_campaign_composite_v1/): p1_candidate_*.png (5),
  p1_candidate_contact_sheet.png, p1_layer_debug.png, p1_reference_vs_baseline_vs_v1_vs_p1.png,
  p1_scorecard.md, p1_route_verdict.md, p1_validation_diagnostics.json.
- Compliance: bounded deterministic polish only; no production runtime change; no Stage3; no Family A/B;
  no deploy/merge/push/PR; AI candidate-only & reused; no secret printed/logged/persisted.

## POSTER2-SOP-SOURCE-MATERIALIZATION-V1 (2026-06-16)

- Read-only materialization of /Users/tylerzhao/poster/SOP into a structured 2-route asset package.
  scripts/poster2_sop_source_materialize_v1.py (additive, read-only source; writes ONLY under
  docs/poster2/assets/sop_source_materialization_v1/). NO poster generation; NO Imagen/Gemini/OpenAI/Vertex
  or any external model/network call; NO production code touched; safe-fail per file. 48 files materialized.
- Classification (6 roles): target_email_style_source = "Fw_ Fwd_ Quand les plats..." .eml (Technitalia GAS
  — STYLE ONLY, business truth rejected); catalogue_style_reference = Catalogue-target.pdf (found to be a
  TECHNITALIA catalogue, commercial@technitalia.com — texture/quality only, truth rejected);
  cuistance_product_truth_source = Cuistance_our (Planche).pdf (CUISTANCE 2023 catalogue), 目标海报1/2.jpg
  (CUISTANCE coupe-frites poster), logo_01.jpg, 产品图/产品图2, Electric Fryer1-2, lit1-4 (CUISTANCE fryer);
  fallback_email_reference = 3x NOUVEAUTÉ CUISTANCE emails (also truth); reference_only = food scenes;
  unknown_needs_owner_review = logo_02.png (SANDRIVER AI — NOT CUISTANCE, excluded as brand logo).
- Evidence-backed CUISTANCE truth extracted (NO fabrication): Coupe-frites FC001/1210025 (L380xP260xH250);
  Cuiseur riz RC10L (L485xP420xH400, 10/6L; ref discrepancy 311001 vs 311011 -> owner); Blender CBG2000/
  8010002 (L240xP220xH500, 2L, 1.8kW); Friteuses électriques EF series from Planche p09 (EF101V/EF131V
  1-cuve, EF102V/EF132V 2-cuve, full dims/power/capacity/price). Contact commercial@cuistance.eu /
  +33 (0)1 71 84 11 20 / cuistance-europe.com (vs www.cuistance.eu in target chain -> owner confirm canonical).
- macOS Unicode bug fixed: blender filename is NFD vs NFC -> normalize("NFC") so all 3 NOUVEAUTÉ files
  classify + dump correctly.
- Package: source_inventory/, target_email_style_pack/, catalogue_target_style_pack/ (PDF pages rendered
  via PyMuPDF), fallback_email_reference_pack/, cuistance_our_product_truth_pack/ (manifest + specs/images
  index + copy candidates + source_evidence + missing_truth_report + logo/product/gallery/planche assets),
  route_target_map/ (campaign_explainer + product_sheet + fallback), generation_ready_cases/ (5 cases),
  owner_review_needed.md, _package_manifest.json.
- Routes: A Campaign Explainer (Template A-like; AI = textless atmosphere only; deterministic truth overlay);
  B Product Sheet (Template B-like; Catalogue texture; deterministic specs; no fabrication); + deterministic
  fallback. Strongest ready case = case_001 friteuse électrique (strong images + spec-complete from Planche
  p09; pending only owner image->ref match EF102V vs EF132V).
- Compliance: no generation; no external model call; no production/Stage1-3/Family A-B change; no
  deploy/merge/push/PR; every product claim evidence-backed or marked missing; no secrets. STOP after
  materialization (no poster generation), per task.

## POSTER2-CASE001-CAMPAIGN-EXPLAINER-HEAVY-GENERATION-V1 (2026-06-16)

- First REAL poster-generation slice after SOP materialization. case_001 friteuse électrique via the
  Campaign Explainer route. scripts/poster2_case001_campaign_explainer_heavy_v1.py (additive, validation-only;
  reuses P1 composite geometry + catalog_hero HELPERS + genai shim + credential loader). NO production code
  modified; Playwright/Chromium render; candidate-only.
- Real generation: imagen-4.0-generate-001 — 6 TEXTLESS atmosphere substrates, all 6 accepted (no readable
  text/logo/fake labels/gas stoves/Technitalia/Codimatel/brand leakage; gate = textless prompts + visual
  review, OCR unavailable in env -> documented). 6 composite candidates rendered.
- Deterministic CUISTANCE truth only: logo_01, fryer 产品图, owner's 3 callouts, EVIDENCE-BACKED EF132V spec
  strip (RÉF. EF132V · 2 cuves 13+13 L · 3+3 kW/230V · L630×P520×H345 mm, Planche p09), gallery, contact
  (commercial@cuistance.eu · +33 (0)1 71 84 11 20 · cuistance-europe.com). AI owns ZERO truth.
- Owner decisions honored: fryer = EF132V; exactly 3 callouts; CUISTANCE brand/logo/contact only; target
  email style-only; Technitalia/gas fully rejected.
- TWO truth flags raised (no fabrication by me): (1) owner callout "Thermostat réglable 0–200°C" CONTRADICTS
  Planche p09 "température réglable jusqu'à 190°C" -> rendered as owner-instructed but flagged for
  reconciliation; (2) strapline "Cuisson professionnelle, croustillant maîtrisé" is generic marketing copy ->
  owner-confirm. EF132V vs EF102V image->ref match also pending owner.
- RESULT: best = composite_candidate_01_fries_hero.png ~4.7/5 (target reached, boundary). Beats Catalog Hero
  (~4.16) and prior composite (~4.65); lift from the evidence-backed spec strip + correct CUISTANCE truth.
  Gates: real gen yes; >=3 candidates yes (6); truth deterministic+evidence-backed yes; no leakage; product/
  logo correct; >=4.5 yes; >=4.7 yes (boundary); 4.8 no. Gap = minor typography/layout (title/callout lanes)
  + the 0–200°C truth flag (content) — NOT a route flaw.
- Recommend runtime hardening (additive email_campaign_composite_v1 template) AFTER owner reconciles the 4
  decisions. Artifacts: docs/poster2/assets/case001_campaign_explainer_heavy_v1/ (input_case_manifest,
  business_truth_lock, generation_prompt_pack, raw_substrate_*, substrate_rejection_report,
  composite_candidate_*, contact sheets, reference_vs_catalog_hero_vs_best_candidate, layer_debug,
  scorecard, validation_diagnostics, route_verdict, owner_review_needed).
- Compliance: candidate-only AI; no production/Stage1-3/Family A-B/Product Sheet change; no deploy/merge/
  push/PR; no fabricated specs (one unsupported figure is owner-supplied + flagged); no secret printed.
  STOP after candidates+screenshots+scorecard+verdict+owner_review.

## POSTER2-CASE001-P2-PRODUCTIONIZATION-PREP-V1 (2026-06-16)

- Bounded productionization-prep on the case_001 Campaign Explainer best (~4.7). Additive harness
  scripts/poster2_case001_campaign_explainer_p2_v1.py (imports the case001 harness; reuses the ALREADY-
  generated fries_hero substrate — NO new AI call). NO production code / Stage1-3 / Family A-B / Product
  Sheet / email change. Candidate-only.
- Owner decisions applied: thermostat -> evidence-backed "Thermostat réglable jusqu'à 190°C" (Planche p09;
  the unsupported "0–200°C" REMOVED); EF132V kept (image↔ref still owner-review); strapline "Cuisson
  professionnelle, croustillant maîtrisé" approved; canonical contact commercial@cuistance.eu · +33 (0)1 71
  84 11 20 · cuistance-europe.com.
- Bounded geometry nudges (deterministic only): title lane right (524->548), left callout lane right
  (410->448), fries_hero locked, EF132V spec strip preserved.
- RESULT: p2_composite_candidate_best.png ~4.75/5 (no regression vs case001 ~4.7; truth now fully
  evidence-backed/owner-approved + cleaner lanes). Gates: >=4.7 yes; >=4.75 yes; 4.8 stretch not yet;
  no unsupported 0–200°C; no target-business leakage; no AI text/logo/spec. Residual to 4.8: title "LES"
  still grazes food blend; plain gallery; low-res logo (400×80).
- Recommend runtime hardening (separate slice, owner go-ahead required): additive email_campaign_composite_v1
  template family (register in template_registry.py + templates/specs + app/templates_html), reuse this
  build_html; AI substrate operator-gated. P2 does NOT wire production.
- Artifacts: docs/poster2/assets/case001_campaign_explainer_p2_v1/ (p2_composite_candidate_best.png,
  p2_reference_vs_p1_vs_p2.png, p2_layer_debug.png, p2_scorecard.md, p2_business_truth_lock.md,
  p2_route_verdict.md, p2_owner_review_needed.md, validation_diagnostics.json).
- Compliance: candidate-only (reused substrate); no deploy/push/merge/PR; no Stage1-3/Family A-B/Product
  Sheet/email change; no fabricated specs (0–200°C removed); no secret printed. STOP after screenshot +
  scorecard + verdict + productionization recommendation.

## POSTER2-EMAIL-CAMPAIGN-COMPOSITE-V1-RUNTIME-HARDENING (2026-06-17)

- Owner-authorized ADDITIVE productionization of the validated P2 Campaign Explainer design (~4.75) as a
  new isolated template family `email_campaign_composite_v1`. Mirrors the catalog_hero additive pattern;
  does NOT alter Family A/B, Product Sheet, Catalog Hero, the shared PosterPipeline/RendererSelector, or
  Stage1/2/3. (The shared HTTP-endpoint dispatch branch in main.py was intentionally NOT added — flagged as
  the final exposure step requiring explicit owner go-ahead.)
- Files added/changed:
  - NEW app/services/poster2/email_campaign_composite.py — render module (6-region contract: banner /
    campaign_visual(operator-gated substrate, never truth) / truth_overlay / restated_band / gallery /
    footer); P2 geometry; deterministic CUISTANCE case001 truth defaults; build_html + Playwright render +
    Pillow offline fallback; business_truth_lock + build_contract_review (leakage gate + 0–200°C gate).
  - NEW app/templates/specs/email_campaign_composite_v1.json — spec/contract truth (regions/slots/canvas +
    business_truth_lock; thermostat default "jusqu'à 190°C"; 0–200°C forbidden; rejected target-business list).
  - EDIT app/services/poster2/template_registry.py — ADDITIVE only: family CAMPAIGN_COMPOSITE_PORTRAIT,
    template metadata email_campaign_composite_v1 (v1.0.0), EMAIL_CAMPAIGN_COMPOSITE_TEMPLATE_IDS +
    is_email_campaign_composite_template(). Existing entries untouched.
  - NEW tests/poster2/test_email_campaign_composite.py (14 tests). EDIT tests/poster2/test_template_registry.py
    snapshot set to include the new additive id (existing ids unchanged).
  - NEW scripts/poster2_email_campaign_composite_v1_runtime_smoke.py (drives the production module).
- Truth defaults (deterministic, evidence-backed/owner-approved): brand CUISTANCE; product electric
  double-basket fryer; ref EF132V (owner-review flag retained); spec strip RÉF. EF132V · 2 cuves 13+13 L ·
  3+3 kW/230V · L630×P520×H345 mm; callouts [2 cuves inox amovibles · Thermostat réglable jusqu'à 190°C ·
  Construction inox / usage professionnel]; strapline "Cuisson professionnelle, croustillant maîtrisé";
  contact commercial@cuistance.eu · +33 (0)1 71 84 11 20 · cuistance-europe.com. AI substrate operator-gated,
  never business truth (substrate_source = operator_upload|absent; ai_runtime_asset_used=False).
- Tests: new + registry + catalog_hero = 30 passed. app.main imports cleanly. The 52 failing tests in
  test_renderer.py / test_slot_contracts.py are PRE-EXISTING and unrelated (those files are UNMODIFIED;
  failure is a committed `_build_html() gallery_items_status` signature mismatch — no path from my additive
  registry/module change).
- Runtime smoke (production module, case001 data + reused fries_hero substrate): ENGINE=chromium,
  structure_complete=True, callouts=3, leakage_clean=True, unsupported_0_200C=False, ai_substrate_is_truth=
  False. Output VISUALLY IDENTICAL to the P2 design (runtime_vs_p2_no_regression.png) — no regression.
  Artifacts: docs/poster2/assets/email_campaign_composite_v1_runtime/ (runtime_smoke_case001.png,
  runtime_contract_review.json, runtime_vs_p2_no_regression.png).
- Remaining owner decisions: EF132V vs EF102V image↔ref match; higher-res CUISTANCE logo; explicit go-ahead
  to wire the main.py endpoint dispatch branch (additive _generate_email_campaign_composite_v1, mirroring
  _generate_catalog_hero_v1) to expose the family over the API.
- Compliance: additive + isolated; no Stage1-3/Family A-B/Product Sheet/Catalog Hero/email change; no shared
  endpoint dispatch change; AI substrate operator-gated/candidate-only; no fabricated specs; no
  target-business leakage; no deploy/merge/push/PR; no secret printed. STOP after smoke + tests + log.

## POSTER2-EMAIL-CAMPAIGN-COMPOSITE-V1-API-SMOKE (2026-06-17)

- Owner-approved bounded ADDITIVE API smoke for email_campaign_composite_v1. Mirrors the catalog_hero_v1
  endpoint branch pattern; no shared-behavior change.
- Files changed (additive only):
  - app/main.py: import is_email_campaign_composite_template; allow renderer_mode=puppeteer for the new
    family in _validate_poster2_renderer_request (OR clause); NEW _generate_email_campaign_composite_v1()
    (dedicated render path via app/services/poster2/email_campaign_composite.render_async, reuses
    AssetLoader; scenario image = operator-gated substrate, never truth); NEW dispatch branch
    `if is_email_campaign_composite_template(payload.template_id)` right after the catalog_hero branch.
    Family A/B / Product Sheet / Catalog Hero dispatch unchanged.
  - app/schemas/poster2.py: ADD optional GeneratePosterV2Response.email_campaign_composite_contract_review
    (default None; omitted for other families) — mirrors catalog_hero_contract_review.
  - NEW tests/poster2/test_email_campaign_composite_api.py (2 API smoke tests, AssetLoader mocked w/ case001
    images + operator-upload substrate; no network/AI/secrets).
  - NEW scripts/poster2_email_campaign_composite_v1_api_smoke.py (artifact producer via TestClient).
- API smoke result (real /api/v2/generate-poster via TestClient): HTTP 200; template_id routes to
  email_campaign_composite_v1; render_engine_used=chromium; contract review structure_complete=True,
  callout_count=3, thermostat_uses_unsupported_0_200C=False, leakage_clean=True, ai_substrate_is_truth=False,
  ai_runtime_asset_used=False, substrate_source=operator_upload. Output VISUALLY IDENTICAL to P2/runtime
  (api_smoke_vs_p2_no_regression.png) — no regression. Catalog-hero/Family-B review shells omitted.
- Tests: new module + API smoke + registry + catalog_hero = 32 passed. app.main imports cleanly. Existing
  template ids unchanged. The 7 failing test_api.py tests (CORS/timeout/error-handling for Family A/B) and
  the 52 renderer/slot tests are PRE-EXISTING and unrelated — PROVEN: stashing my tracked edits and re-running
  the sampled 3 still fails identically. Not fixed in this slice (out of scope per task).
- Artifacts: docs/poster2/assets/email_campaign_composite_v1_runtime/ api_smoke_case001.png,
  api_smoke_response_review.json, api_smoke_vs_p2_no_regression.png.
- Compliance: additive + isolated endpoint branch; no Stage1-3 UX / Family A-B / Product Sheet / Catalog
  Hero / email-sending change; AI substrate operator-gated/candidate-only; no fabricated specs; no
  target-business leakage; no deploy/merge/push/PR; no secret printed. Did NOT touch the pre-existing 52
  renderer tests. STOP after API smoke + artifact + tests + log.

## POSTER2-EMAIL-CAMPAIGN-COMPOSITE-BUSINESS-FLOW-MVP (2026-06-17)

- Proved the real business loop INPUT MATERIALS -> GENERATE POSTER -> SEND EMAIL through the EXISTING
  endpoints (no production code changed this slice; reused /api/v2/generate-poster, /email/preview,
  /email/send + the existing email provider infra). Single command:
  scripts/poster2_email_campaign_business_flow_mvp_v1.py (TestClient; AssetLoader mocked w/ case001
  CUISTANCE assets; no network/AI/secrets). Plus tests/poster2/test_email_campaign_business_flow.py.
- Results: (1) material input WORKS (case001 logo+fryer+gallery+operator-upload substrate + deterministic
  copy); (2) poster generation WORKS (HTTP 200, email_campaign_composite_v1, chromium, structure_complete,
  callouts=3 -> business_flow_poster.png); (3) email preview WORKS (deterministic CUISTANCE draft ->
  email_preview.html/.txt); (3b) send adapter WORKS (inline_only -> status preview_only); real external
  send BLOCKED: resend -> status error "Resend is not configured."
- Business truth review PASS: CUISTANCE only; no Technitalia/Codimatel/gas leakage; thermostat "jusqu'à
  190°C" (no 0–200°C); AI substrate NOT truth (substrate_source=operator_upload, ai_substrate_is_truth=false).
- Two exact operational blockers for real delivery: (1) Resend not configured -> set RESEND_API_KEY +
  verified from-email + real recipient; (2) poster hosting -> the generate endpoint returns a ~9.5MB inline
  data: URL which the email draft embeds (html+text), exceeding the 2 MiB body guard (MAX_BODY_BYTES) on
  send (guard hint: upload to R2/GCS, pass key/url). MVP sent a lean deterministic body; full poster-inline
  email saved as email_preview.html. The record-attachment builder also can't fetch data: URLs (http only).
- Next smallest step: post-generation upload the email_campaign_composite PNG to R2/GCS (reuse R2 client),
  set poster_record final_poster.url to the https URL, configure Resend env -> /email/send (resend,
  attachment_types=[poster_png]) delivers the real poster email.
- Artifacts: docs/poster2/assets/email_campaign_business_flow_mvp_v1/ (business_flow_poster.png,
  email_preview.html, email_preview.txt, send_attempt_result.json, business_flow_report.md).
- Tests: business_flow + composite + api = 15 passed.
- Compliance: no production code changed this slice; no Stage1-3 rewrite / old-flow refactor / Product
  Sheet / Catalog Hero change; AI substrate operator-gated/never truth; no fabricated specs; no
  target-business leakage; no deploy/merge/push/PR; no secret printed.

## POSTER2-EMAIL-CAMPAIGN-COMPOSITE-REMOTE-OPS-SMOKE-V2 (2026-06-17)

- Operational smoke of the deployed business loop for email_campaign_composite_v1. Remote = 
  https://ai-service-leob.onrender.com. scripts/poster2_remote_ops_smoke_v2.py (safe remote probe +
  local generation evidence; presence booleans only, no secret printed). No deploy/push/merge.
- REMOTE evidence: GET /health = 200 (up); POST /api/v2/generate-poster = HTTP 401 (auth-gated);
  email_campaign_composite_v1 NOT deployed (local/uncommitted: email_campaign_composite.py untracked,
  app/main.py modified-not-committed; last commit 148269f). => 2 hard blockers: (1) family not deployed
  (deploy needs push/merge -> forbidden w/o auth); (2) remote endpoint auth-gated (no remote creds; won't
  expose). Remote env (Gemini/R2/Resend) presence UNKNOWN — cannot read without auth, not fabricated.
- LOCAL env presence (this run): Gemini/Google=true; R2_configured=false; Resend_configured=false.
- ADDED (additive, this family only): R2 hosting bridge in _generate_email_campaign_composite_v1 — after
  render, r2_client.put_bytes(make_key("poster2/email_campaign_composite", trace.png), png, image/png);
  if R2 configured -> final_url/final_poster.url = HTTPS R2 URL + poster_hosting="r2"; else falls back to
  inline data: URL (poster_hosting="inline_data_url"). Reuses existing r2_client; never fails generation
  on hosting error. So on Render (R2 configured) the email draft references a small HTTPS URL (no 9.5MB
  data: URL) -> 2 MiB body guard no longer blocks /email/send. Tested:
  tests/poster2/test_email_campaign_composite_hosting.py (configured->https; unconfigured->data: fallback).
- LOCAL flow evidence (TestClient, AssetLoader mocked w/ case001 + operator substrate): generate 200,
  chromium, structure_complete=true, callouts=3, poster_hosting=inline_data_url (R2 absent locally) ->
  generated_poster.png (== accepted P2 design); preview OK (subject "CUISTANCE | Les Friteuses Électriques");
  send adapter inline_only=preview_only, resend=error "Resend is not configured." (local). NOT claiming a
  provider-accepted send.
- Business truth review PASS: CUISTANCE only; EF132V/fryer line; thermostat "jusqu'à 190°C" (not 0–200°C);
  no Technitalia/Codimatel/gas leakage; AI substrate not truth (operator_upload). Note: this family does NOT
  call Gemini at render (deterministic overlay over operator substrate).
- Files changed: app/main.py (additive R2 bridge for this family only) + app/schemas/poster2.py
  (email_campaign_composite_contract_review, from prior slice). New: scripts/poster2_remote_ops_smoke_v2.py,
  tests/poster2/test_email_campaign_composite_hosting.py, docs/poster2/assets/remote_ops_smoke_v2/*.
  Tests: 35 passed (composite+api+hosting+flow+registry+catalog_hero).
- Owner action to run the real remote loop: (1) deploy the family (push/merge — needs authorization);
  (2) provide remote ops auth (or run server-side); (3) confirm Render R2 + Resend env + approved recipient.
- Compliance: additive only; no Stage1-3 UX / Family A-B / Product Sheet / Catalog Hero change; no shared
  email-semantics change beyond the hosting bridge; AI substrate operator-gated/never truth; no fabricated
  specs; no secret printed/persisted; no deploy/push/merge/PR. Did not claim a real send success.

## POSTER2-EMAIL-CAMPAIGN-COMPOSITE-REMOTE-DEPLOY-SMOKE-V1 (2026-06-17)

- Deploy-branch validation. Pre-commit safety check PASSED: full tracked diff = 1102 insertions / 2
  deletions; the 2 deletions are a single import line replaced by a multi-import block + the
  renderer-validation `if` broadened to an OR (template_dual_v2 behavior preserved). Confirmed additive
  route-only; no Family A/B / Product Sheet / Catalog-Hero-behavior / renderer / Stage1-3 change.
- Created branch feature/poster2-email-campaign-composite-remote-smoke-v1; committed ONLY the additive
  route (16 files: app/main.py additive dispatch+R2 bridge, app/schemas/poster2.py optional field,
  template_registry.py additive entries, email_campaign_composite.py, catalog_hero.py [REQUIRED import
  dependency], 2 specs, 2 NotoSansSC fonts, 5 poster2 tests, execution log) as commit 2b36b01. PUSH to
  origin SUCCEEDED (github.com/zhaojfifa/ai-service). Branch is deploy-ready.
- DEPLOY BLOCKED (exact): render.yaml is a Blueprint with no `branch:` override -> Render auto-deploys the
  default branch (main) only; this env has no RENDER_API_KEY / deploy hook / service id / dashboard access,
  so I cannot trigger or configure a branch deploy. Did NOT merge main (forbidden w/o approval).
- REMOTE AUTH BLOCKED (exact): /api/auth/me={enabled:true,authenticated:false}; OPS_PASSWORD is a dashboard
  secret (sync:false); no creds locally and pulling Render secrets is forbidden -> remote endpoints not
  callable by me.
- R2/Resend on remote UNVERIFIABLE: render.yaml declares neither (only GCP/Vertex/Firefly + OPS); if present
  they were set in the dashboard. Cannot verify without auth. Remote /health=200, /version=404.
- Proof separation: LOCAL proof = REAL (same code; generate 200/chromium/structure_complete/3 callouts/
  truth PASS; R2 bridge unit-tested); DEPLOYED proof = BLOCKED; EMAIL PREVIEW = REAL (local); REAL SEND =
  BLOCKED (no provider message id; not claimed). generated_poster_remote.png is the byte-identical LOCAL
  render (visual reference), explicitly not remote-served.
- Owner actions to finish: (1) deploy the pushed branch (dashboard branch switch + manual deploy / staging
  service / deploy hook / approved merge); (2) provide ops auth or run server-side; (3) confirm Render R2 +
  Resend env + approved recipient.
- Deliverables: docs/poster2/assets/remote_deploy_smoke_v1/ (remote_deploy_smoke_report.md, deploy_evidence.md,
  remote_config_presence.json, generated_poster_remote.png, generated_poster_url.txt, email_preview_remote.html,
  email_preview_remote.txt, email_send_result_remote.json, business_truth_review_remote.json).
- Compliance: additive only; branch push authorized by owner; no merge to main; no Render secret pulled;
  no secret printed; no Stage1-3/Family A-B/Product Sheet/Catalog Hero change; no fabricated specs; AI
  substrate not truth; no claim of real send.

## POSTER2-EMAIL-CAMPAIGN-COMPOSITE UI exposure slice (2026-06-17)

- Diagnosis: email_campaign_composite_v1 absent from templates/registry.json (dropdown source) AND the
  Stage2 generate remapped non-pilot ids to template_dual_v2 via resolvePoster2PilotTemplateId/
  resolvePoster2CompositionTemplateId fallback -> selection would not reach the new backend route.
- Fix (additive, isolated; frontend/ + docs/ mirror kept in sync): (1) added email_campaign_composite_v1
  entry to frontend+docs templates/registry.json; (2) added POSTER2_DIRECT_TEMPLATE_IDS set
  {catalog_hero_v1, email_campaign_composite_v1} and made both resolvers pass those ids through unchanged.
  No backend renderer change; no UI redesign; no Stage1-3/Family A-B/Product Sheet/Catalog Hero behavior change.
- Validation: Playwright UI proof (served frontend/) — dropdown populated with all 5 options incl. the new
  "Email Campaign Composite · Campaign Explainer"; existing options preserved; selecting it -> value
  email_campaign_composite_v1 (ui_dropdown_option.png, ui_proof.json). Local backend route via TestClient:
  HTTP 200, template_id=email_campaign_composite_v1, structure_complete=true, callouts=3, leakage_clean=true,
  0_200C=false, ai_substrate_is_truth=false (api_response_review.json, generated_poster.png). Tests:
  frontend_docs_sync + api + registry = 17 passed.
- Remote: /health=200; POST /api/v2/generate-poster(email_campaign_composite_v1)=401 (ops-auth-gated) ->
  remote generation/email smoke NOT executable (no ops creds; pulling Render secrets forbidden). Live UI is
  GitHub Pages -> owner must publish docs/ for the option to show in production.
- Artifacts: docs/poster2/assets/email_campaign_composite_ui_v1/ (ui_dropdown_option.png, ui_full_page.png,
  ui_proof.json, generated_poster.png, api_response_review.json, ui_exposure_report.md).
- Compliance: additive only; frontend+docs in sync; no Stage1-3/Family A-B/Product Sheet/Catalog Hero/
  email-semantics/backend-renderer change; no fabricated specs; no secret printed; no deploy/merge/push (UI
  changes uncommitted on the working branch).

## POSTER2-EMAIL-CAMPAIGN-COMPOSITE-UI-PUBLISH-AND-REMOTE-FLOW-VERIFY-V1 (2026-06-17)

- Task A safety check: tracked diff since 2b36b01 = 184 insertions / 0 deletions; app.js +10 (resolver
  passthrough only), registry +12 (data entry); frontend↔docs byte-synced. Excluded .DS_Store + pre-existing
  docs/poster2/README.md (out of scope) + the ui_proof helper script. No backend/Stage/Family A-B/Product
  Sheet/Catalog Hero behavior change.
- Task B: committed 7374b37 "feat(poster2): expose email campaign composite template in UI" (frontend+docs
  app.js + registry.json + ui_v1 artifacts + log) and PUSHED to origin (2b36b01..7374b37). No merge to main.
- Task C (Pages mechanism, determined): .github/workflows/deploy-frontend.yml deploys frontend/ to Pages,
  triggered ONLY by push to main (frontend/**) or manual workflow_dispatch; last 3 runs all main. Live site
  https://zhaojfifa.github.io/ai-service/ currently exposes only [template_dual, template_dual_studio,
  template_product_sheet_v1] (live even predates catalog_hero_v1). Feature-branch push did NOT trigger Pages.
  New option goes live only via (A) merge to main (forbidden here) or (B) gh workflow run deploy-frontend.yml
  --ref <branch> (publishes branch frontend live without merge; also brings catalog_hero_v1 + any drift live).
  gh is authed (zhaojfifa, workflow scope); I did NOT run it (outward-facing publish is owner-gated).
- Task D (live UI verify): BLOCKED pending publish — live registry confirms 3 options only. Local UI proof of
  the committed code stands (email_campaign_composite_ui_v1/). Re-run after publish for the live screenshot.
- Task E (remote generation smoke): BLOCKED — POST /api/v2/generate-poster(email_campaign_composite_v1) =
  HTTP 401 ops_auth_required. No ops creds; auth not bypassed; no Render secret pulled; remote generation NOT
  claimed. Local proof of same code = 200 + all truth gates pass.
- Task F (remote business flow): BLOCKED (depends on E + R2/Resend + approved recipient). No send claimed.
- Artifacts: docs/poster2/assets/email_campaign_composite_ui_publish_v1/ (publish_verification_report.md,
  live_registry_current.json, remote_generation_blocker.json).
- Compliance: additive; pushed (authorized); no merge to main; no UI redesign / Stage1-3 / Family A-B /
  Product Sheet / Catalog Hero / backend-render / Gemini-prompt change; no fabricated specs; no 0–200°C; no
  Technitalia/Codimatel/gas; no secret printed; no production email send.

## POSTER2-OPS-MANUAL-TEST-PACK-V1 (2026-06-17)

- Built an operator-facing manual test package for email_campaign_composite_v1 (case001 CUISTANCE
  Friteuses Électriques / EF132V) under docs/poster2/assets/ops_manual_test_pack_v1/. COPY-ONLY of
  already-validated assets; NO image generation, NO model calls, NO new poster generation, NO remote
  smoke/R2/email/Pages/deploy, NO production code change.
- Copied (source -> package): cuistance_logo_01.jpg -> upload_assets/brand_logo.jpg; fryer_产品图.jpg ->
  product_hero_fryer.jpg; Electric Fryer1.jpg/fryer_产品图2.jpg/Electric Fryer2.jpg -> gallery_01..03.jpg;
  case001_..._heavy_v1/raw_substrate_01_fries_hero.png -> atmosphere_substrate_fries_hero.png (style-only,
  ai_substrate_is_truth=false); p2_composite_candidate_best.png -> accepted_expected_output.png +
  expected_output/accepted_p2_poster.png; runtime_smoke_case001.png -> expected_output/runtime_smoke_poster.png;
  p2_reference_vs_p1_vs_p2.png -> expected_output/comparison_*.png. All 10 verified openable (PIL).
- Authored: README_OPERATOR_TEST.md, input_fields_case001.json (valid) + .md, upload_checklist.md,
  business_truth_lock.md, operator_test_steps.md, qa_acceptance_sheet.md, package_manifest.json (valid).
- Truth locked: CUISTANCE only; EF132V (image↔ref still owner-review); thermostat "jusqu'à 190°C" (0–200°C
  forbidden); Technitalia/Codimatel/gas = style-only, business-truth rejected; AI substrate = operator
  upload, never truth. Operator entry point: operator_test_steps.md.
- Compliance: no generation/model calls; no remote smoke/send/R2/Pages/deploy/merge/push; no production code
  / Stage1-3 / template geometry change; no fabricated specs; no 0–200°C; no Technitalia/Codimatel/gas; no
  secret printed.

## POSTER2-OPS-UI-FLOW-HEAVY-V1-LOCAL-CLI (2026-06-17)

- Built a dedicated, isolated operator page frontend/ops_campaign.html + ops_campaign.js (mirrored to docs/)
  for the CUISTANCE Email Campaign Composite 3-step flow (input → generate → email preview/send-prep). It
  sends template_id=email_campaign_composite_v1 + renderer_mode=puppeteer DIRECTLY to /api/v2/generate-poster
  (bypasses the Stage2 pilot/composition resolvers entirely → cannot be remapped to template_dual_v2). No
  Stage1-3/Family A-B/Product Sheet/Catalog Hero change; no backend renderer/geometry change.
- Runtime-heavy validation: launched local uvicorn (auth off; body/base64 limits raised LOCAL-ONLY) + a local
  static asset server; Playwright drove load-pack → prefill case001 → select 6 assets → generate → Chinese
  contract review → email preview. Assets fetched by URL (mirrors R2; the RejectHugeOrBase64 guard blocks
  data: URLs by design — documented, not bypassed). ui_flow_validation.json = ALL TRUE: routes to
  email_campaign_composite_v1, structure_complete, callout_count=3, leakage_clean, thermostat 190°C (not
  0–200°C), ai_substrate_is_truth=false, send_owner_gated, email_preview_ok. Backend response (HTTP 200,
  chromium, all gates) matches the UI-rendered Chinese contract review.
- Email preview works (/api/v2/email/preview, subject "CUISTANCE | Les Friteuses Électriques", poster inline
  in iframe). Send button disabled/Owner-gated; no real email sent.
- Tests: frontend_docs_sync + email_campaign(composite/api/hosting/business_flow) + registry + catalog_hero =
  43 passed; new tests/poster2/test_ops_campaign_ui.py = 4 passed (page exists+synced, routes directly,
  resolver passthrough present, registry option in both mirrors; old options preserved).
- Files changed: frontend/ops_campaign.html, frontend/ops_campaign.js, docs/ops_campaign.html,
  docs/ops_campaign.js (new); tests/poster2/test_ops_campaign_ui.py (new); scripts/
  poster2_ops_campaign_ui_smoke.py (new); docs/poster2/assets/ops_campaign_ui_flow_heavy_v1/* (artifacts);
  execution log. No backend code changed this slice.
- Compliance: no AI generation; no real send; no deploy/merge/push; no Stage1-3/Family A-B/Product Sheet/
  Catalog Hero/geometry/Gemini change; no fabricated specs; no 0–200°C; no Technitalia/Codimatel/gas; no
  secret printed/pulled. Local test env knobs (auth off, raised limits) not committed to production config.

## POSTER2-OPS-CAMPAIGN-UI-REMOTE-404-FIX-V1 (2026-06-17)

- Root cause: Render serves frontend/ via StaticFiles mount at / (app/main.py: FRONTEND_DIR=<repo>/frontend,
  app.mount("/", StaticFiles(frontend, html=True))) — serves any file in frontend/. But ops_campaign.html/.js
  were never committed (untracked; not in deployed HEAD 7374b37) -> /ops_campaign.html 404. Dropdown worked
  because templates/registry.json WAS committed in 7374b37. Not a mount/SPA bug.
- Fix (minimal additive, no code change): committed existing static files (frontend + docs mirror) + guard
  test as 3f8ce02. Files: frontend/ops_campaign.html, frontend/ops_campaign.js, docs/ops_campaign.html,
  docs/ops_campaign.js, tests/poster2/test_ops_campaign_ui.py. No app/ / static-mount / geometry / backend
  render / Family A-B / Product Sheet / Catalog Hero change.
- Local verify (uvicorn serving frontend/): /ops_campaign.html=200 (contains "CUISTANCE 邮件营销海报"),
  /ops_campaign.js=200, /=200 (index intact), generate email_campaign_composite_v1 still works (chromium),
  guard test 4 passed. Screenshots: ops_campaign_remote_route_local_200.png, ops_campaign_after_generate.png
  under docs/poster2/assets/ops_campaign_remote_404_fix_v1/.
- Remote still 404 (3f8ce02 not pushed/deployed); remote / still 200. Needs push + Render redeploy of the
  branch -> NOT done (awaiting Owner approval per stop point). Diff scope = 5 additive files only.
- Remaining remote blockers unchanged: /api/v2/generate-poster ops-auth-gated (401); prod assets via R2;
  Resend env + approved recipient for real send (send stays Owner-gated).
- Compliance: no real send; no secrets read/printed; no Gemini/R2/Resend config change; no Stage1-3 refactor;
  no poster geometry change; no push/deploy without approval.

## POSTER2-OPS-CAMPAIGN-UI-REMOTE-404-FIX-V1-PUSH-AND-VERIFY (2026-06-17)

- Owner approved push of 3f8ce02. Verified HEAD contains 3f8ce02 (branch
  feature/poster2-email-campaign-composite-remote-smoke-v1). PUSH SUCCEEDED: 7374b37..3f8ce02 -> origin.
- No merge to main, no PR, no deploy, no code change.
- Remote verify after push (curl, ~6 min polling): /ops_campaign.html = 404 (title_count 0),
  /ops_campaign.js = 404, / = 200 throughout. => Render has NOT yet redeployed 3f8ce02; it is still serving
  an older commit (consistent with 7374b37: dropdown option present from committed registry.json, but
  ops_campaign.html absent because it only landed in 3f8ce02). NOT claiming remote success (still 404).
- Judgment: "Render 尚未 redeploy" (most likely) — the branch render.yaml buildCommand runs
  `pip install + playwright install chromium` (slow; redeploy can take many minutes), and/or auto-deploy on
  this branch needs a manual trigger. No /version endpoint to read the live commit; inference from
  dropdown-present + ops_campaign.html-absent indicates the live commit is 7374b37, not 3f8ce02.
- Next: await Render auto-redeploy OR Owner triggers a manual deploy of this branch to 3f8ce02, then re-run:
  curl -sS -o /dev/null -w '%{http_code}\n' https://ai-service-leob.onrender.com/ops_campaign.html  (expect 200)
- Compliance: no merge/PR/deploy/code change; no real send; no secrets read/printed; no Gemini/R2/Resend
  change; no geometry change; no ops-auth bypass; no false remote-success claim.

## POSTER2 ops_campaign R2 upload bridge fix (2026-06-17)

- Root cause: ops_campaign.js read each File via FileReader.readAsDataURL and put the data: URL straight
  into the generate payload; it never called /api/r2/presign-put. The BodyGuard (RejectHugeOrBase64)
  rejects any inline data:image/base64 in /api/* requests by design -> 422 REQUEST_BODY_BLOCKED reason=base64.
  (Main Stage1/2 avoids this via /api/r2/presign-put + presigned PUT, sending only url/key.) The console 404s
  were only the optional repo-local input_fields_case001.json fetch (cosmetic; inline defaults cover it) —
  not the generate blocker.
- Fix (additive, minimal; commit d41fc88, NOT pushed): ops_campaign.js now uploads each selected file via
  /api/r2/presign-put + presigned PUT and sends ONLY {url,key} (mirrors main app.js r2PresignPut). Adds a
  product-required preflight (empty -> blocks, no generate call) and an explicit "R2 upload unavailable" hard
  stop with NO base64 fallback when presign/upload fails. Removed readAsDataURL and the 404-noisy JSON fetch
  (inline case001 defaults). Added guard test test_ops_campaign_uses_r2_presign_not_base64. frontend+docs
  synced. No backend/renderer/geometry/case001-truth/190°C change.
- before payload: product_image.url = "data:image/jpeg;base64,<~1MB>" -> 422 base64.
  after payload : product_image = {url:"http(s).../key", key:"ops/..."}, payload_contains_base64=false -> 200.
- Local validation (uvicorn :8015 default guards + auth off; presign+PUT mocked to local asset server for the
  success path; real presign -> 503 for the unavailable path): ALL 7 acceptance true —
  1 empty preflight blocks (no generate call); 2 presign called on upload (6 calls); 3 no base64 in payload;
  4 assets url/key only; 5 no REQUEST_BODY_BLOCKED (generate 200, chromium); 6 R2 unavailable shows
  "R2 upload unavailable" and blocks (no base64); 7 enters contract review (structure_complete, callouts=3,
  leakage_clean, 190°C not 0–200°C, ai_substrate_is_truth=false). Tests: ops_campaign_ui + frontend_docs_sync
  + email_campaign_api = 15 passed.
- Artifacts: docs/poster2/assets/ops_campaign_r2_bridge_v1/ (preflight_blocks_empty.png, r2_unavailable.png,
  r2_success_after_generate.png, generate_payload_after.json, ui_r2_validation.json).
- Remaining blockers: prod needs R2 env configured (presign currently 503 locally — expected); /api/v2/
  generate-poster remote still ops-auth-gated (401); Resend env + approved recipient for real send.
- Compliance: no BodyGuard relaxation; generate never receives base64; no renderer/geometry/truth change; no
  Gemini runtime substrate; no real send; no secrets; commit not pushed (awaiting Owner approval).

## POSTER2 ops_campaign R2 bridge — push d41fc88 + remote verify (2026-06-17)

- Owner approved push. PUSH SUCCEEDED: 3f8ce02..d41fc88 -> origin (branch
  feature/poster2-email-campaign-composite-remote-smoke-v1). No merge/PR/deploy/code change.
- Remote verify (curl, ~14 min total incl. ~7 min polling):
  - /ops_campaign.html = 200, /ops_campaign.js = 200, / = 200.
  - BUT deployed /ops_campaign.js is the OLD 3f8ce02 version: r2UploadFile=0, /api/r2/presign-put=0,
    readAsDataURL=1, differs from local d41fc88. => Render has NOT redeployed d41fc88 (still serving 3f8ce02).
  - /api/r2/presign-put (direct curl) = 401 ops_auth_required (auth-gated; cannot reach R2-config/503 check
    without ops auth).
- Answers: (1) pushed d41fc88; (2) Render deployed to d41fc88 = NO (still 3f8ce02, old base64 JS);
  (3) html 200; (4) js 200 but old; (5) presign not called by deployed old JS (it uses readAsDataURL);
  direct presign reachable; (6) presign = 401 (not 503/200); (7) deployed old JS would still send base64
  (the no-base64 fix is in d41fc88, verified locally, NOT yet live remotely); (8) contract review not
  reached remotely; (9) failure point = Render redeploy lag (d41fc88 not deployed) + behind it ops auth on
  presign (401) + R2 env unverifiable until authed.
- The R2 bridge fix is correct & locally validated (7/7 acceptance); remote verification BLOCKED on Render
  redeploy of d41fc88 (likely needs manual deploy, as with 3f8ce02) and then ops auth + R2 env.
- Compliance: no BodyGuard relaxation; no renderer/case001/190°C change; no Gemini substrate; no real send;
  no secrets; only the approved push performed.

## POSTER2-OPS-CAMPAIGN-REMOTE-GENERATE-502-DIAG-V1 (2026-06-17)

- Gemini ruled OUT: no genai/vertex/imagen in email_campaign_composite.py / catalog_hero.py render path
  (deterministic Chromium overlay over operator substrate). Gemini = startup init noise only.
- Root cause (high confidence): Chromium render exceeds Render free-tier time/memory -> worker timeout/OOM
  -> Render proxy HTML 502 -> frontend "Unexpected token '<'". Local lifecycle trace: chromium_success
  dur_ms=26262 (~26s at scale=2) on a fast dev box; Render free tier slower -> 502. Not 404/422/base64/
  missing-asset.
- Minimal fix (email_campaign route only; no renderer rewrite / no geometry / no truth change):
  (1) bounded render asyncio.wait_for(POSTER2_ECC_RENDER_TIMEOUT_MS=45000) -> hang/slow becomes TimeoutError
  -> Pillow fallback -> 200 degraded (no 502); (2) low-memory Chromium args (--single-process/--no-sandbox/
  --disable-gpu/--disable-dev-shm-usage/--disable-extensions); (3) POSTER2_ECC_DEVICE_SCALE knob (default 2;
  set 1 on Render for ~4x speed); (4) stage-tracked dispatch returns JSON {ok,request_id,stage,error_type,
  message} on any catchable failure (no HTML); (5) structured lifecycle logging (entry/asset_fetch/render/
  chromium start+success+duration+fail/upload) — no signed-URL tokens logged.
- Files: app/services/poster2/email_campaign_composite.py (render_async timeout+logging+hardening,
  render_async(request_id=)); app/main.py (_generate_email_campaign_composite_v1 stage logging + JSON
  exception wrapper); tests/poster2/test_email_campaign_composite_502_diag.py (NEW: failure->JSON,
  chromium-fail->pillow 200). Trace artifact: docs/poster2/assets/ops_campaign_generate_502_diag_v1/.
- Tests: 502_diag + composite + api + hosting + ops_ui = 23 passed. App imports clean.
- Remote: not reproduced (ops-auth 401) / needs Render redeploy of this commit; after deploy a slow render
  degrades to 200 (pillow) JSON instead of 502; recommend POSTER2_ECC_DEVICE_SCALE=1 on Render.
- Compliance: no BodyGuard relaxation; no base64 fallback restored; no renderer architecture rewrite; no
  geometry/case001/190°C change; no Gemini substrate; no real send; no secret/signed-URL token printed.

## POSTER2-OPS-CAMPAIGN-COMPARE-MAIN-GENERATE-PATH-V1 (2026-06-17)

- Path compare (origin/main vs branch): the whole email_campaign/ops stack is branch-only. main Stage2
  (Family A, works on Render) renders Chromium at device_scale_factor=1 (renderer.py:1859) with args
  ["--disable-dev-shm-usage","--font-render-hinting=none"]; ops_campaign email_campaign_composite rendered
  at device_scale_factor=2 (4x pixels 2480x3508) -> higher peak memory -> OOM on 512MB Render free tier ->
  worker killed -> Render proxy HTML 502. b8cc7fb DOES wrap the route (template_id -> _generate_email_
  campaign_composite_v1 with JSON wrapper + bounded render), but an OS OOM kill is not a Python exception so
  the JSON wrapper never runs and asyncio.wait_for can't stop it. Frontend then blind-parsed the HTML 502
  (resp.json()) -> "Unexpected token '<'". No X-Request-ID -> untraceable.
- Fix (minimal): (backend email_campaign_composite.py) default POSTER2_ECC_DEVICE_SCALE=1 (match Family A) +
  launch args identical to Family A -> lower peak memory; (frontend ops_campaign.js) fetchSafe() never
  blind-parses -> on non-JSON/HTML shows HTTP status + content-type + body excerpt + request_id; sends
  X-Request-ID ops-ecc-<ts> on presign/generate/preview. No geometry/truth/renderer-arch change; no
  BodyGuard relax; no base64; no Gemini.
- Local evidence: request_id ops-ecc-... flows through entry/asset_fetch/render/chromium/upload lines;
  chromium_start scale=1; chromium_success dur_ms~26000 (time dominated by shared CJK font embedding, not
  raster scale; scale=1's win is peak memory = the OOM lever); 200 + contract review. Tests: 31 passed
  (composite incl. scale-default + ops_ui incl. non-JSON/X-Request-ID guard + 502_diag + api + sync).
- HONEST: I cannot reach Render logs or call remote generate (ops-auth 401) -> remote ecc.generate-entry /
  request_id verification is an OWNER action (X-Request-ID added to enable it). If 502 persists at scale=1 =>
  confirmed OOM on 512MB tier => Owner Decision: upgrade RAM / async render job / font subsetting.
- Files: app/services/poster2/email_campaign_composite.py, frontend/ops_campaign.js, docs/ops_campaign.js,
  tests/poster2/test_email_campaign_composite.py, tests/poster2/test_ops_campaign_ui.py,
  docs/poster2/assets/ops_campaign_path_compare_v1/main_vs_ops_path_compare.md.
- Compliance: no real send; no case001/190°C change; no BodyGuard relax; no base64; no Gemini; no UI
  beautify / geometry polish / renderer rewrite; commit not pushed (awaiting Owner approval).

## POSTER2-OPS-CAMPAIGN-COMPARE ... push 11ece26 + remote verify (2026-06-17)

- Owner approved push. PUSH SUCCEEDED: b8cc7fb..11ece26 -> origin (branch
  feature/poster2-email-campaign-composite-remote-smoke-v1). No merge/PR/deploy/code change.
- Remote verify (~11 min polling): /ops_campaign.html=200, /ops_campaign.js=200, but deployed js has
  fetchSafe=0, X-Request-ID=0, ops-ecc=0, readAsDataURL=0 => Render is serving d41fc88, NOT 11ece26. After
  ~9.5 min of 70s polls fetchSafe never appeared => Render has NOT redeployed 11ece26 (consistent with prior
  commits needing a manual Render deploy). NOT claiming remote success.
- Verification status vs the 11-item checklist:
  1 html=200 OK; 2 js=200 OK (but OLD d41fc88); 3 fetchSafe live = NO (await redeploy); 4 X-Request-ID
  ops-ecc live = NO (await redeploy); 5-7 presign/generate/non-JSON remotely = cannot drive (ops-auth 401 +
  need 11ece26); 8-11 Render logs (request_id / ecc.generate entry / chromium_start scale=1 / chromium_success
  / pillow_fallback / OOM / worker exited) = I have NO Render log access -> OWNER action.
- Next: Owner triggers Render Manual Deploy -> 11ece26, then (a) curl ops_campaign.js | grep fetchSafe (=1),
  (b) authed generate with X-Request-ID: ops-ecc-<ts>, (c) read Render logs for the ecc.* lifecycle lines.
- Owner Decision Needed (pending): only if, after 11ece26 deploys, scale=1 STILL 502s and Render logs show
  OOM/worker killed -> request Owner approval to scale up Render RAM (or async render job).
- Compliance: only the approved push performed; no real send / no secrets / no Gemini / no BodyGuard relax /
  no base64 / no geometry-renderer change.

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-PRODUCT-DESIGN-V1 (2026-06-17)

- DESIGN ONLY (no code change). Authored docs/poster2/cuistance_commercial_trial_product_design_v1.md:
  reframes the proven POSTER2/CUISTANCE backend as the "CUISTANCE Campaign Production Platform" (NOT a poster
  generator). Grounded in the proven run (poster_key=p2_7f7d2f3649024ceb, trace_id=ops-ecc-1781683072440-4206,
  email_campaign_composite_v1, chromium, degraded=false, structure_complete/deliverable=true, R2 final_url,
  email preview returns subject/html/text/summary_points/email_assets) AND the client workflow research
  (文件1 工作流确认与AI替代评估图 / 文件2 工作流细节调研表, 2026-06-17, ~/poster/SOP).
- Covers all 13 required sections: positioning (Campaign Production Platform; non-technical fr operators +
  Owner approver + Admin); core scenarios; the 6-step main flow (Create→Materials→TruthLock→PosterPackage→
  EmailPackage→Review&Owner-gated Send) with per-step input/output/UI/error/owner-review; 7 data objects
  (CampaignJob/AssetPack/TruthLock/PosterPackage/EmailPackage/ApprovalRecord/SendRecord); UI IA (Dashboard +
  Materials/TruthLock/Poster/Email/Review&Send/History tabs); 3 roles; ops_campaign.html demo->product
  migration (absorb, reuse r2UploadFile/fetchSafe/contract-review; keep as internal smoke; remove demo-only
  test mode); v1 scope + explicit non-scope; A/B/C employee replacement (A green full-auto, B yellow draft+
  review, C green auto + send approval); 4 Mermaid diagrams (overall workflow / A-B-C replacement / data
  lifecycle / approval-send gate); v1 validation metrics; backend capability ledger; next engineering slice;
  open Owner decisions (pricing Q1, brand Q2, single-vs-series Q3, EF132V↔image, Render redeploy/RAM).
- Index updated: docs/poster2/README.md (01 Product). No code, no real send, no renderer/case001/190°C change,
  no Gemini-as-truth, ops_campaign.html not wrapped as final product, no UI beautify / 4.8 polish / multi-
  product generation.

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-V1-MULTI-ROLE-DESIGN-REVIEW (2026-06-18)

- DESIGN / REVIEW ONLY (no code change, no email sent). Authored
  docs/poster2/cuistance_commercial_trial_v1_multi_role_design_review.md, which scopes-DOWN the platform
  blueprint (cuistance_commercial_trial_product_design_v1.md) per the Owner/PM ruling: v1 = a result-oriented
  commercial-trial workbench, NOT the full Campaign Production Platform.
- v1 core = single-product new-launch promotion email; 4-step flow (Créer / Importer / Générer l'affiche /
  Assembler & envoyer). Two key revisions captured: (1) send is MANUAL operator-confirmed multi-recipient only
  (no address-book / no Excel import / no CRM/Mailchimp/Sendinblue / no grouping / no scheduling / no open-click
  analytics / no mass automation); (2) Logo/Banner are DECOUPLED from the poster body into a separate Email
  Assembly HTML layer.
- Route A (primary) = poster body (email_campaign_composite_v1, no logo inside) + Email Assembly. Route B
  (fallback only) = HTML product sheet sharing the same assembly header/footer; used when assets insufficient /
  Chromium render fails / degraded / quick note needed.
- Covers all 12 required sections: Owner Summary; Product Designer view (4-step pages/input/output/failure,
  Route A/B, Email Assembly, manual-recipient send); Engineering review (capability ledger TABLE vs live code);
  Operator view (10–15 min feasibility, French fixed strings); Scope Controller ruling (must/can/won't/future/
  safety/creep); v1 IA (5 tabs); 7 lightweight data objects (TrialCampaign/AssetInputs/PosterBodyPackage/
  EmailAssemblyPackage/RecipientInput/SendAttempt/EvidenceRecord); Route A/B decision rules; Email Assembly
  design; 4 Mermaid diagrams; 3-PR slice plan; final verdict.
- Engineering findings grounded in live code: HAVE = R2 presign (/api/r2/presign-put), generate
  (/api/v2/generate-poster email_campaign_composite_v1), contract review, /api/v2/email/preview, PNG/PDF assets
  (build_email_assets_for_record), send (/api/v2/email/send, inline_only+resend). GAPS = G1 logo/banner baked
  into the composite poster body (banner_region + logo chip) — conflicts with "strip logo/banner"; G2 Email
  Assembly missing (current email HTML is poster image + title + bullets only, no header/CTA/footer/social);
  G3 send is single-recipient (EmailSendV2Request.recipient: EmailStr) — needs manual multi-recipient; G4 no
  Route B HTML product sheet; G5 no TrialCampaign persistence (only poster_record); G6 explicit confirm gate +
  SendAttempt/EvidenceRecord.
- 3-PR plan: PR-1 docs + lightweight 4-tab UI shell/state (reuse r2UploadFile/fetchSafe/contract render);
  PR-2 decouple logo + build Email Assembly composer; PR-3 manual multi-recipient confirmed send + Route B +
  evidence. Verdict: APPROVE → enter engineering plan; START with PR-1, do NOT code PR-2/PR-3 before PR-1 lands.
  Biggest risk = G1 logo decoupling without disturbing contract gates / 190°C / case001 truth / geometry.
- Index updated: docs/poster2/README.md (01 Product). Compliance: no code change, no real send, no address-book/
  Excel/CRM/scheduling/analytics, no full Campaign Dashboard, no multi-role permission system, no multi-product
  generation, no 4.8 polish, HTML fallback kept as fallback (not main), logo/banner not re-bound to poster body,
  case001/190°C truth unchanged, Gemini stays suggestion-only (never business truth).

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-BRANCH-AWARE-HEAVY-ENGINEERING-DESIGN-V1 (2026-06-18)

- DESIGN / REVIEW ONLY (no code change, no branch merge, no push, no email sent). Authored
  docs/poster2/cuistance_commercial_trial_branch_aware_heavy_engineering_design_v1.md.
- VERIFIED GIT REALITY (inspected, not assumed): current branch =
  feature/poster2-email-campaign-composite-remote-smoke-v1; merge-base with main = 21ebba2; main..HEAD = 9
  commits; HEAD..main = 0 commits. => feature is a STRICT SUPERSET of main (merge would be a fast-forward, not a
  divergent reconciliation).
- The 9 feature commits add: catalog_hero (experiment), family-b announcement UI, email_campaign_composite_v1
  family + R2 hosting bridge, ops_campaign static page, R2-presign upload (no base64), bounded render + JSON-on-
  failure, scale=1 render, tests. These are FEATURE-ONLY (absent on main): confirmed email_campaign_composite /
  catalog_hero / ops_campaign do not exist on main.
- Product Sheet (template_product_sheet_v1.{json,html,css,svg,slot_spec,anchor_map}) EXISTS ON MAIN and therefore
  also in the feature tree (feature superset). So "reuse Product Sheet from main" needs NO cherry-pick — it is
  already present. /api/v2/generate-poster already DISPATCHES by template_id (catalog_hero / email_campaign_
  composite dedicated paths at main.py:2077/2083; else PosterPipeline handles template_dual_v2* and
  template_product_sheet_v1). => Route B (Product Sheet) is reachable at the API level today; only the email-chain
  SELECTION of it is missing. email_campaign_composite.py never references product_sheet (fallback NOT integrated).
- Honest correction surfaced in the doc: the Owner framing "Product Sheet not yet merged with the activity chain"
  is true at the INTEGRATION level (not selected as Route B) but NOT at the TREE level (Product Sheet files
  already coexist with the email chain on the feature branch). main does NOT contain feature work (consistent),
  but feature DOES contain main's Product Sheet.
- Gaps (branch-located): G1 logo/banner baked into BOTH bodies (email_campaign_composite.banner_region +
  template_product_sheet_v1.logo_banner_region) -> must move to Email Assembly; G2 Email Assembly HTML missing
  (current draft = poster image + title + bullets, app/services/email/drafts.py); G3 send single-recipient
  (EmailSendV2Request.recipient: EmailStr) -> need manual recipients[]; G4 Route B not selected by email chain;
  G5 no TrialCampaign/recipient persistence (only poster_record); G6 confirm gate + SendAttempt/EvidenceRecord.
- Recommendation: Option A (build v1 on feature branch first, then controlled fast-forward merge to main after
  PR-3 gates pass). Rejected B (would promote experimental catalog_hero + binaries into main prematurely) and C
  (cherry-pick unnecessary given linear history + Product Sheet already present). 3-PR plan: PR-1 docs + 4-step UI
  shell/state; PR-2 Email Assembly + logo decoupling (both templates) + Route B selection; PR-3 manual recipient
  send + evidence + A->B fallback rule. Biggest risk = G1 decoupling without disturbing contract gates / 190°C /
  case001 / geometry. Verdict: APPROVE.
- Commit-hygiene note for any future merge: working tree has many UNTRACKED docs (02_architecture/*,
  05_validation/*, this review, harness-x/, asset dirs) + .DS_Store churn that are NOT part of the 9 commits and
  must be committed deliberately (and .DS_Store ignored) before merge.
- Index updated: docs/poster2/README.md (01 Product). Compliance: no code, no merge, no push, no real send, no
  contact/Excel/CRM import, no scheduling/analytics/automation, no multi-product generation, no 4.8 polish, HTML/
  Product-Sheet kept as fallback (not main), logo/banner not re-bound to body, case001/190°C truth unchanged,
  Gemini stays suggestion-only.

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-BASELINE-AND-UI-FLOW-DESIGN-V1 (2026-06-18)

- DOCS-ONLY (no code, no branch merge, no push, NO TAG created, no email sent, PR-1 NOT started). Owner re-
  prioritization: UI flow BEFORE engineering — past passes produced heavy backend but no operator-usable product.
- Authored docs/poster2/cuistance_commercial_trial_ui_flow_design_v1.md with Part A (baseline freeze plan) +
  Part B (operator UI flow).
- PART A baseline facts (verified): branch=feature/poster2-email-campaign-composite-remote-smoke-v1; HEAD=
  11ece2616ad9664480e8468deebd8cf3efe416a7 (11ece26); merge-base w/ main=21ebba2; ahead=9 behind=0 (feature is a
  STRICT SUPERSET of main, fast-forward). Proven remote pass anchor: poster_key=p2_7f7d2f3649024ceb,
  trace_id=ops-ecc-1781683072440-4206, email_campaign_composite_v1, chromium, degraded=false,
  structure_complete=true, deliverable=true, poster_hosting=r2, R2 final_url; committed in-tree proof under
  docs/poster2/assets/email_campaign_composite_ui_v1/ shows chromium + structure_complete but inline_data_url
  (local capture). Dirty tree: 4 modified-tracked (2 are .DS_Store noise, 2 are intended doc updates), 87
  untracked docs/assets NOT part of the 9 commits — must be committed deliberately before any merge; add .DS_Store
  to .gitignore.
- PROPOSED baseline tag (DO NOT create without explicit Owner approval): 
  baseline/poster2-cuistance-commercial-trial-remote-pass-v1 at 11ece26. Exact git tag/push commands documented;
  merge of main DEFERRED. Stop point = no tag, no merge, no PR-1.
- PART B UI flow (operator-first): single workbench + 4-step stepper (① Créer la tâche ② Importer les éléments
  ③ Générer l'affiche produit ④ Assembler l'email & envoyer) + optional ⓘ Diagnostic drawer. Route A (affiche
  produit) default; Route B (fiche produit simplifiée) shown as fallback only on degraded/échec/thin-assets, flows
  into the SAME Step 4. Logo/Banner presented as Email Assembly header element ("Logo (pour l'email)"), NOT inside
  the poster body. Manual recipient chip input + Test/Réel send with explicit confirm dialog (no contact import /
  Excel / CRM / segmentation / scheduling / analytics / automation). Error table maps each failure to an operator
  message + next action (never raw "Unexpected token '<'"). Documented French fixed strings, CAN-edit vs CANNOT-
  edit vs business-truth-locked (spec/contact/190°C/case001/ambiance≠fait; Gemini=suggestion only), text+Mermaid
  wireframes, engineering implications mapped to the existing 3-PR plan (after approval only), and 10 open
  questions for Owner/PM/operator.
- Index updated: docs/poster2/README.md (01 Product). Compliance: no code change, no merge, no push, no tag, no
  real send, no renderer change, no TrialCampaign/Email-Assembly/Route-B/multi-recipient implementation, no
  contact import / scheduling / analytics / CRM, no full Campaign Dashboard, no Gemini-as-truth, case001/190°C
  truth unchanged, doc not backend-heavy (operator-facing flow is the focus).

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-BASELINE-AND-UI-FLOW-DESIGN-V1 — REVISE (4→3 steps + 商用化, 2026-06-18)

- DOCS-ONLY (no code, no merge, no push, NO TAG, no email sent, PR-1 NOT started). Owner REVISE applied to
  docs/poster2/cuistance_commercial_trial_ui_flow_design_v1.md (full rewrite).
- LANGUAGE: doc is now Chinese-primary / internal-review oriented; English only for technical identifiers
  (branch/API/template_id/request_id/poster_key); French ONLY as UI copy examples (no separate French document).
- FLOW: 4 steps -> 3 steps. Old Step1(create)+Step2(materials) MERGED into new Step1 "产品与素材 / Produit &
  éléments" (task name + product name + ref/model + product hero 1-2 [>=1 required, gates Step2] + gallery 0-3 +
  logo-for-email + optional atmosphere + upload states; logo marked "en-tête de l'email, pas dans l'affiche";
  atmosphere marked "Visuel uniquement"). Old Step3 -> new Step2 "生成产品海报主体 / Affiche produit". Old Step4
  -> new Step3 "拼接邮件、预览并发送 / Email & envoi". All stepper labels, wireframes, Mermaid, Chinese
  explanations, French copy examples, open questions, engineering implications updated for 3 steps.
- COMMERCIAL-FACING RULE: operator screens hide ALL engineering language (branch, git tag, template_id,
  renderer_mode, chromium, R2, Route A/B, API paths, JSON, contract_review, request_id, poster_key, Gemini,
  internal fallback names). These appear ONLY in the ⓘ diagnostics drawer / engineering appendix / Part A (marked
  engineering-internal). Business-language replacements documented: Affiche produit (main poster), Fiche produit
  simplifiée (fallback, not "Route B"), Vérification / Informations vérifiées / Prêt pour l'email (not
  "contract review"), Téléversement terminé / Image prête (not "R2 upload"), Version simplifiée disponible (not
  "degraded").
- KEPT: poster route PRIMARY + simplified product sheet SECONDARY/fallback; Logo/Banner separated into Email
  Assembly (not poster body); manual one-or-many recipient send with explicit confirm; no contact import / no
  Excel / no CRM / no segmentation / no scheduling / no analytics / no automation.
- ADDED per Owner structure: 14-section internal-review layout; French UI copy table (中文含义 / French UI label /
  internal note) covering all required labels incl. Confirmer l'envoi à N destinataire(s); visible-vs-internal
  split; business-language error table; 3-step engineering implications (PR-1 = 3-step commercial trial workbench
  shell, NOT 4-step); 11 open questions (incl. baseline tag approval).
- Part A baseline freeze UNCHANGED in facts (branch feature/...remote-smoke-v1, HEAD 11ece26, ahead=9 behind=0,
  proposed tag baseline/poster2-cuistance-commercial-trial-remote-pass-v1 — propose only, defer main merge) but
  explicitly marked ENGINEERING/INTERNAL ONLY.
- Index updated: docs/poster2/README.md (01 Product). Compliance: no code/tag/merge/push/send/PR-1; no
  TrialCampaign / Email-Assembly / fallback-route / multi-recipient implementation; no renderer/case001/190°C
  change; Gemini not a truth source; no separate French doc; no engineering language on operator-facing screens;
  no full Campaign Dashboard / no contact import / scheduling / analytics / CRM.

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-UI-FLOW — REVISE (Email Banner Module + parameter truth, 2026-06-18)

- DOCS-ONLY (no code, no merge, no push, NO TAG, no email sent, PR-1 NOT started). Owner REVISE applied to
  docs/poster2/cuistance_commercial_trial_ui_flow_design_v1.md. 3-step flow UNCHANGED.
- CORRECTION 1 — Email Banner Module is FIRST-CLASS (not removed): Logo/Banner is SEPARATED from the Product
  Poster Body and designed as an independent "Module Bannière / Email Banner Module" (logo + dark/brand
  background + pattern/texture + optional channel name + optional group/partner mark + optional campaign label),
  reused across the main poster route AND the simplified product-sheet route. Email Package = (1) Email Banner
  Module (2) Product Poster Body (3) Body Copy/CTA (4) Footer Contact/Social (5) Attachments (6) Recipients/Send.
  Operator-facing wording forbidden to say "removed / not part of product / no banner in final email"; must say
  "banner is the email header / poster focuses on product / final email contains BOTH banner and poster".
  Updated: Owner Summary, design-principle table (+row "不说移除"), Step1 (added Bannière de l'email fond/motif +
  Contact/Réseaux), Step2 (poster body PAS de bannière email; brand colors ok but banner not baked in), Step3
  (defined Banner Module as 1st block w/ logo + fond/motif + canal/campagne), both Mermaid (added Email Package
  structure with Banner as first block), French copy table (+Bannière/En-tête/Fond·motif/Nom du canal/Libellé de
  campagne), visible-content, engineering implications (PR-2 = Email Banner Module + Assembly), open questions
  (+banner style / channel·campaign label / logo source / banner wording).
- CORRECTION 2 — product parameter truth: REMOVED hard-coded "Thermostat jusqu'à 190°C" as a platform rule.
  Product parameters now come from CONFIRMED INPUT (manual / imported material pack / future PDF·manual
  extraction / confirmed product data). AI may organize wording but must NOT invent or change technical
  parameters. 190°C is ONLY a case001 / EF132V sample validation fact, not a per-product rule. UI now uses
  generic "Caractéristiques techniques" / "Paramètres produit" / "Informations confirmées" / "Information
  vérifiée"; replaced "Thermostat locked 190°C" with "Technical parameters confirmed from input". Internal note
  retained: for EF132V/case001, 190°C remains a sample truth gate (engineering-only, not shown to operators).
- KEPT: 3 steps (① 产品与素材/Produit & éléments ② 生成产品海报主体/Affiche produit ③ 拼接邮件、预览并发送/Email &
  envoi); poster route PRIMARY + simplified product sheet SECONDARY/fallback; manual one-or-many recipient send
  w/ explicit confirm; engineering language hidden from operator screens (diagnostics drawer / appendix only);
  no contact import / no Excel / no CRM / no segmentation / no scheduling / no analytics / no automation.
- Index updated: docs/poster2/README.md (01 Product). Compliance: no code/tag/merge/push/send/PR-1; no
  Email-Banner-Module / Email-Assembly / fallback-route / multi-recipient implementation; no renderer/case001/
  EF132V-sample-truth change; Gemini not a truth source; banner NOT removed from final email; 190°C NOT
  hard-coded as a platform-wide rule.

## ENGINEERING-SKILL-BASELINE-AND-INSTALLATION-REVIEW (2026-06-18)

- CUISTANCE commercial UI design PAUSED by Owner (do not continue UI design; do not create/use a custom
  poster2-commercial-ui-design skill — unverified, must not drive the critical product-design baseline).
- REPORT ONLY (no config change, no skill/plugin install, no marketplace add, no product code touched, no UI
  design continued). Authored docs/poster2/engineering_skill_baseline_review_v1.md.
- Skill setup inspected on disk: user skills ~/.claude/skills = {harness-x-workflow} only; project .claude/skills
  = none; ~/.claude/plugins = empty (no marketplaces); no Superpowers/external pack local. All other Skill-tool
  entries (code-review, simplify, verify, run, review, security-review, init, deep-research, claude-api,
  update-config, keybindings-help, fewer-permission-prompts, loop) are Claude Code BUILT-INS, already enabled.
  Planning covered by Plan subagent + plan mode + Explore agent. settings: ~/.claude/settings.json =
  {skipWorkflowUsageWarning:true}; project settings.local.json = Bash permission allowlist only (no skill config).
- Recommendation: INSTALL NOTHING — minimal verified set (code-review/simplify/verify/run/security-review +
  Plan/Explore + harness-x-workflow) already installed/enabled. DEFER external brainstorming/writing-plans/UX
  packs (not local, unverified) until Owner vets a trusted marketplace. Do NOT create the custom commercial-UI
  skill. Install/marketplace commands documented as PROPOSED only (config change → Owner approval required;
  none executed).
- Compliance: no product code change, no UI design continuation, no custom skill, no renderer change, no merge,
  no tag, no push, no email send, no PR-1.

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-CLAUDE-DESIGN-UI-V1 (2026-06-18) — SUBMITTED FOR OWNER REVIEW

- Owner decision: start commercial UI design; process = Design -> Verify -> Submit (do NOT self-approve; final
  status must be SUBMITTED FOR OWNER REVIEW, not PASS). Skill baseline: existing verified Claude Code
  capabilities only (read approved flow doc); no external/custom skill installed or created.
- DOCS-ONLY: no code, no UI implementation, no renderer change, no merge, no tag, no push, no email sent, no
  PR-1. Authored docs/poster2/cuistance_commercial_trial_claude_design_ui_v1.md (commercial VISUAL UI design over
  the approved 3-step flow).
- Read source docs: cuistance_commercial_trial_ui_flow_design_v1.md (approved 3-step flow + semantics),
  branch_aware_heavy_engineering_design_v1.md, README.md, this log (in context).
- Design content: positioning = single-product promotional EMAIL WORKBENCH (not a poster generator); visual
  direction = clean B2B SaaS / modern-European, preview-first, strong whitespace + hierarchy, neutral palette
  (#F6F7F9/#FFF/#E6E8EC, ink #1F2024, muted #6B7178) + CUISTANCE red #E1002A accent ONLY on active step/primary
  CTA; calm cards, no debug dashboards. IA = single workbench, top bar (brand + 3-step + état chip + ⓘ), left
  edit / right live preview, bottom single primary CTA. 3 screens (Produit & éléments / Affiche produit / Email &
  envoi) each with one primary action. Email Banner Module = first-class (logo + dark/brand fond + motif +
  optional canal/groupe/campagne; reused across poster + simplified-sheet routes; final email = bannière +
  affiche produit). Simplified product sheet = amber, useful OPTION not a failure (no Route B/degraded wording).
  Product params from confirmed input; 190°C = case001/EF132V sample only (internal note isolated), not a
  platform rule; AI/Gemini = "suggestion" only, never a truth source.
- Self-verification (A-G) performed and reported IN the doc: A commercial usability (1-min understandable,
  10-15 min first email [conditional on generation time, mitigated by simplified option], B2B look, one primary
  action/screen) = satisfied; B 3-step (Step1 merges product+materials, no separate create-task step) =
  satisfied; C banner first-class/not removed/separate/final email shows both = satisfied; D params confirmed
  input / 190°C not platform rule / Gemini not truth source = satisfied; E no engineering leakage on operator
  screens (terms isolated to ⓘ drawer/internal notes) = satisfied; F French operator copy + business-friendly
  errors + simplified sheet as useful option = satisfied; G scope control (no contact import/scheduling/
  analytics/CRM/full dashboard/code) = satisfied. Open design risks + 9 open questions left for Owner.
- Status: NOT self-approved. STATUS: SUBMITTED FOR OWNER REVIEW.
- Index updated: docs/poster2/README.md (01 Product).

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-STATIC-UI-MOCKUP-V1 (2026-06-18) — STATIC UI MOCKUP SUBMITTED FOR OWNER REVIEW

- Owner decision: Claude Design UI doc accepted for visualization -> move to static UI mockup / visual prototype.
  NOT production implementation, NOT PR-1 engineering. Design artifact for Owner/PM/operator review.
- DOCS/ARTIFACT-ONLY: no app/frontend production code changed, no backend API connected, no real upload/
  generate/send, no renderer change, no tag/merge/push, no PR-1. Read approved design + flow docs first.
- Created static prototype under docs/poster2/ui_mockups/cuistance_commercial_trial_v1/:
  index.html (single page, 3 screens + banner module + confirm modal + hidden diagnostics drawer; local
  view-switching JS only, no network), styles.css (B2B SaaS tokens: neutral surfaces + CUISTANCE red #E1002A
  accent only on active step/primary CTA, quiet cards, subtle borders, restrained shadows, preview-first
  two-column), assets/product.svg + assets/gallery.svg (SVG placeholders), README.md (purpose / covered / not
  implemented / how-to-view / Owner-PM-operator review checklist).
- Screens: (1) Produit & éléments — campaign/product fields, confirmed Caractéristiques techniques, product +
  gallery + ambiance uploads, Logo de l'email + Bannière fond/motif uploads, contact/social, Image prête state;
  (2) Affiche produit — title/accroche/arguments editor, confirmed params (read-only inflow), poster body
  preview WITHOUT banner, Vérification card (business sentences + Prêt pour l'email), Générer/Régénérer,
  simplified product sheet as AMBER useful option (not red); (3) Email & envoi — Module Bannière editor, full
  email preview (banner -> poster body -> copy+CTA -> footer/social), Objet/Intro (suggestion), PNG/PDF toggles,
  recipient chips (incl. one invalid example), Envoi test/Envoyer, confirm modal, per-recipient results.
- Email Banner Module = first-class (dark charcoal header + hex/dot pattern + white logo chip + red filet +
  optional canal/campagne), SEPARATE from poster body; final email preview shows banner + poster body.
- Self-review (10 pts) result: commercial look ✓; 1-min understandable 3 steps ✓; banner first-class ✓; poster
  body separate from banner ✓; final email shows banner+poster ✓; simplified sheet as useful amber option ✓;
  operator labels business French ✓; engineering language absent from main UI ✓ (grep scan = NONE FOUND on
  index.html); send clearly confirmed (modal + per-recipient results) ✓; ready for Owner/PM/operator visual
  review ✓. HTML well-formedness check = OK (no unclosed/stray tags); all referenced assets exist.
- 190°C not present as a platform rule (UI uses generic "Informations confirmées / Caractéristiques techniques");
  Gemini not shown (intro labeled "suggestion"); no contact import / scheduling / analytics / CRM / full
  dashboard.
- Index updated: docs/poster2/README.md (01 Product). Status: SUBMITTED FOR OWNER REVIEW (not self-approved).

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-STATIC-UI-MOCKUP-V1 — REVISE (real logo/banner + zh/fr test UI, 2026-06-18)

- Owner REVISE: replace placeholder logo/banner with REAL assets; UI language = Chinese-primary explanatory +
  French UI labels (system supports zh/fr; not French-only). Still static design, NOT production / NOT PR-1.
- ARTIFACT-ONLY: no production app/frontend code changed, no backend API connected, no real upload/generate/send,
  no renderer change, no tag/merge/push, no PR-1.
- Real assets materialized into docs/poster2/ui_mockups/cuistance_commercial_trial_v1/assets/:
  - logo_01.jpg = copied from ~/poster/SOP/logo_01.jpg (real CUISTANCE logo; PNG content 400x80, .jpg name).
  - banner_option_01.jpg = real CUISTANCE NOUVEAUTÉ Mailchimp email header (image 0a50184e-…png, PNG 2451x457),
    referenced by the target .eml "NOUVEAUTÉ … COUPES FRITES …"; set as DEFAULT banner.
  - banner_option_02.jpg = real Technitalia banner (…banniere_1_(6).png, PNG 1080x720) referenced by the
    "Fw_ … coup de chaud …" .eml. Provenance: .eml banners are REMOTE-hosted (Mailchimp/Zoho), not embedded;
    "extract" = fetch the .eml-referenced URLs and save under the Owner-required filenames. .jpg names carry PNG
    content (browsers render by content). Provenance table written into the mockup README.md.
- index.html revised: real logo in Logo de l'email cell + email-header preview; Email Banner Module on Screen 3
  shows TWO real banner options (Option 1 default-selected) with a live JS swap that updates BOTH the editor
  preview and the final email preview; final email preview = real banner (en-tête) + product poster body
  (separate) + copy + CTA + footer; added a top "internal test-review" note + Chinese explanatory hints (.zh /
  .zh-hint) alongside French UI labels + Chinese sub-labels under each stepper step.
- styles.css revised: polished real-banner styling (.banner-real / .email-banner with brand red filet, restrained
  shadow), .banner-opt selector with red selected ring, .logo-real, review-note bar, zh accent styling, stepper
  wrap for zh sub-labels; clean B2B SaaS kept, CUISTANCE red restrained.
- Self-review (10): real logo ✓; real banner candidates (2, default selected) ✓; final email shows banner +
  poster body ✓; zh/fr test UI ✓ (Chinese explanatory + French UI); clean European B2B SaaS ✓; no engineering
  language in main UI ✓ (grep on index.html = NONE FOUND); banner module visibly first-class ✓; placeholder
  logo/banner avoided (real used) ✓; README updated with asset provenance ✓; still static design (no backend/
  upload/generate/send) ✓. HTML well-formedness = OK; all 5 referenced assets exist; real assets verified as
  valid PNG images; no stale placeholder banner refs.
- Semantics kept: 3-step flow; banner first-class & not removed; final email = banner + poster body; poster body
  separate from banner; params from confirmed input; 190°C not a platform rule (UI uses generic Informations
  confirmées / Caractéristiques techniques); simplified product sheet = useful amber option; manual recipients
  only; no contact import / scheduling / analytics / CRM.
- Index updated: docs/poster2/README.md (01 Product). Status: SUBMITTED FOR OWNER REVIEW (not self-approved).

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-STATIC-UI-MOCKUP-V1 — V2 REVISE (lang switch + structured params + description + 2-image sheet + real assets, 2026-06-18)

- Owner REVISE V2 of docs/poster2/ui_mockups/cuistance_commercial_trial_v1/. ARTIFACT-ONLY: no production code,
  no backend, no real upload/generate/send, no renderer change, no tag/merge/push, no PR-1.
- (1) LANGUAGE SWITCH: header toggle 中文 / Français; Chinese is the DEFAULT for this test; French is the target
  operator language. Implemented via data-zh/data-fr attributes + JS textContent swap (verified: 0 data-zh
  parents have child elements, so swap is safe). No longer permanently mixed. Email PREVIEW content stays French
  (the email is a French deliverable). Stepper/bar/etat strings switch via JS dictionaries.
- (2) REAL LOGO (assets/logo_01.jpg) applied to workbench header (brand-logo), Step 1 "邮件 Logo" cell + asset
  preview, Step 3 Email Banner Module + final email preview (the real banner image itself carries CUISTANCE
  branding/logo).
- (3) REAL BANNERS: banner_option_01 (CUISTANCE NOUVEAUTÉ header, default) + banner_option_02 (Technitalia),
  extracted from the target .eml-referenced remote URLs (provenance in mockup README). Live swap updates editor
  preview + final email preview.
- (4) STRUCTURED PARAMETERS (not free textarea): import/recognition entry button + param-table with 8 rows
  (Référence/型号, Capacité/容量, Puissance/功率, Tension/电压, Dimensions/尺寸, Matière/材质, Thermostat/温控,
  Autres/其他) each with value input + confirm state badge; format-requirements hint; truth-model explain block
  (params from confirmed input; AI wording-only, never invents/changes technical params; 190°C = case001 sample
  only, NOT a platform rule — thermostat row tagged "样例(case001)/Exemple (case001)").
- (5) PRODUCT DESCRIPTION (产品介绍 / Description produit) as a separate editable card, explicitly separated from
  confirmed technical parameters; purpose documented (email intro / sheet body / poster support copy / optimizer
  weak input).
- (6) SIMPLIFIED PRODUCT SHEET upgraded to a real product-sheet visual: shared Email Banner + 1–2 real product
  images + description + confirmed params (Capacité/Puissance/Tension/Matière) + CTA; presented as an AMBER
  "useful option" (badge 有用选项/Option utile); no fallback/degraded/Route B wording.
- (7) REAL PRODUCT IMAGES added: product_01.jpg / product_02.jpg copied from ~/poster/SOP/Electric Fryer1/2.jpg
  (1280×1280 JPEG), used in poster hero, simplified sheet (two images), and Step 1 preview.
- (8) REFERENCE ALIGNMENT CHECKLIST added to mockup README (Technitalia target + 3 CUISTANCE fallback emails +
  Email Campaign Composite): top banner strength / real logo clarity / dark brand header / restrained red /
  product explanation area / product-sheet fallback visual / footer-contact pattern / final email looks like an
  email (sectioned email layout, not a generic SaaS card).
- styles.css V2 additions: .brand-logo, .lang-switch/.lang, .param-import/.param-table/.input.cell/.badge.sample,
  .explain, .email-banner small/mini, .sheet/.sheet-body/.sheet-imgs/.sheet-title/.sheet-desc/.sheet-specs,
  .p-hero img, segmented preview label. Clean B2B SaaS kept; CUISTANCE red restrained.
- Self-review (10): lang switch + Chinese default ✓; French mode available ✓; real logo ✓; 2 real banners ✓;
  structured params (8 rows, not free textarea) ✓; description present & separated ✓; simplified sheet supports
  1–2 product images ✓; final email aligns better w/ target + fallback emails ✓; no engineering leakage (grep on
  index.html = NONE FOUND) ✓; still static mockup ✓. HTML well-formedness = OK; all 5 referenced assets exist
  (all real); 190°C not a platform rule.
- Kept: 3-step flow; banner first-class & separate from poster body; final email = banner + poster/sheet body;
  manual recipients only; no contact import / scheduling / analytics / CRM.
- Index updated: docs/poster2/README.md (01 Product). Status: SUBMITTED FOR OWNER REVIEW (not self-approved).

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-STATIC-UI-MOCKUP — V2 Step 2 selection/save mechanism (2026-06-18)

- ARTIFACT-ONLY (no production code / backend / upload / generate / send / renderer / tag / merge / push / PR-1).
  Updated docs/poster2/ui_mockups/cuistance_commercial_trial_v1/{index.html,styles.css,README.md} per Owner.
- Step 2 now has a clear SELECT/SAVE mechanism: both previews (Affiche produit card #card-affiche, Fiche produit
  simplifiée card #card-sheet) are .selectable with a "选为邮件主体 / Choisir pour l'email" button + a hidden
  "已选用 / Sélectionné" badge; the in-card notice buttons also act as selectors (选用海报主体 / 选用简化产品页).
- Only ONE visual can be selected (selecting one clears the other); selected card shows red ring + corner ✓ +
  badge. selectedVisual = 'affiche' | 'sheet'.
- "Continue ▶" (nextBtn) is GATED on Step 2: disabled until a visual is selected; action-bar hint switches to
  "请先选择邮件主体 / Choisissez d'abord le visuel de l'email" while unselected. Step 1 and Step 3 unaffected.
- The selected visual reflects into the Step 3 final email preview body: #emailBodyAffiche vs #emailBodySheet
  toggled (only one shown), under the shared real banner.
- "Régénérer / Regenerate" remains available and CLEARS the current selection (forces re-select). NO version
  history / NO multi-version management added (only a code comment notes their intentional absence).
- styles.css: .card.selectable(.selected) red ring + corner ✓, .btn.select-visual (becomes primary when its card
  is selected), .selected-badge shown only when selected. Clean B2B SaaS kept; red restrained.
- Verify: HTML well-formedness = OK; gating line present (nextBtn.disabled = step===2 && !selectedVisual);
  selectVisual fn + .select-visual wiring + Régénérer-clears wiring present; emailBody swap present; no
  engineering-language leak (grep = NONE FOUND). Real assets unchanged.
- Status: SUBMITTED FOR OWNER REVIEW (not self-approved).

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-BACKEND-ALIGNMENT-PLAN-V1 (2026-06-18) — SUBMITTED FOR OWNER REVIEW

- Owner: UI Mockup V2 approved as the product-interaction baseline for backend alignment. Produce a backend
  alignment + heavy-engineering plan FIRST; do NOT start heavy implementation / PR-1.
- DOCS-ONLY (no code / no backend / no renderer / no send / no tag / no merge / no push / no PR-1; mockup NOT
  connected to backend). Authored docs/poster2/cuistance_commercial_trial_backend_alignment_plan_v1.md.
- Reading note (surfaced honestly): two Owner-listed must-read docs are MISSING in-tree —
  docs/poster2/poster2_generation_routes_design_baseline_v1.md (absent) and root
  docs/poster2/email_copy_optimizer_and_optional_attachment_status_v1.md (absent; content lives under
  03_engineering/). Planned against ACTUAL backend code instead (main.py, schemas/poster2.py, poster_records.py,
  services/email/*, poster2/email_campaign_composite.py, template_product_sheet_v1, r2_client.py) + AGENTS.md /
  CLAUDE.md / README / log.
- Verified backend reality: /api/v2/generate-poster dispatches by template_id — email_campaign_composite_v1 =
  Affiche produit candidate (logo baked into banner_region), template_product_sheet_v1 = Fiche produit
  simplifiée (ALREADY 2-image via product_image + product_secondary_image; logo in logo_banner_region). Each
  generate -> create_poster_record(poster_key) (R2 JSON + /tmp fallback). GET /api/v2/posters/{poster_key};
  /api/v2/email/preview (deterministic draft + optional Gemini non-truth + PNG/PDF via build_email_assets_for_
  record, flag-gated); /api/v2/email/send single-recipient (EmailStr), inline_only+resend; /api/r2/presign-put
  url/key only.
- 5 real gaps: (1) workbench/TrialCampaign + structured product params (rows + pending/confirmed/locked) +
  separate product description; (2) Step-2 two candidates + selected_email_body_visual persistence + regenerate
  reset; (3) Email Banner Module decoupling (logo out of banner_region/logo_banner_region) + Email Assembly
  preview; (4) manual multi-recipient confirmed send + send_attempts evidence; (5) small items (language pref).
- Proposed: minimal records (workbench_record/product_truth/product_assets/email_banner/poster_candidates/
  selected_email_body_visual/email_package/recipients·send_attempts) layered OVER poster_record (reference, not
  copy); endpoint REUSE (only 2 thin new: POST/PATCH /api/v2/workbench; reuse generate-poster for both candidates
  by template_id, reuse preview/send extended); asset flow url/key no base64; parameter truth (AI wording-only,
  never invents/changes params; 190°C = case001 sample, not platform rule); Email Assembly (banner module +
  selected body visual consumed deterministically by poster_key); PR-0..PR-4 sequence w/ per-PR files/tests/
  smoke/owner-gates/forbiddens; 10 risks (no dashboard overbuild, no poster_record duplication, no frontend-as-
  truth, no banner-in-body, no fail-looking sheet, no hard-coded 190°C, no engineering leakage, no premature
  renderer change).
- Index updated: docs/poster2/README.md (01 Product). Status: SUBMITTED FOR OWNER REVIEW (not self-approved).

## POSTER2-DOCS-INDEX-ROUTER-SKILL-PILOT-V1 (2026-06-18) — SUBMITTED FOR OWNER REVIEW

- docs-index-router skill pilot STARTED + COMPLETED (docs-governance only). NO product code changed
  (no app/**, frontend/**, renderer, email behavior, mockup files, deployment config). PR-1 REMAINS PAUSED
  until Owner approves docs governance.
- Skill availability (honest record): the `docs-index-router` skill is NOT installed/invokable here (absent
  from the Skill list and ~/.claude/skills). Router + script authored from the task's explicit spec (used as
  the skill template), adapted to the real repo layout.
- Created: docs/DOCS_INDEX_AND_ROUTER.md (repo-level routing/governance, 15 sections; does NOT replace
  docs/poster2/README.md — that remains the formal POSTER2 index); scripts/check_docs_router.py (git-aware
  governance check); PROJECT_STATUS.md (governance ACTIVE + router/script/poster2-index pointers + PR-1 paused).
- Missing-file honesty: required-read docs/poster2/template_dual_v2_architecture_business_definition.md does NOT
  exist at the poster2 root; real formal path = docs/poster2/02_architecture/...; legacy duplicate at
  01_architecture/... (reference-only). Recorded in the router; missing root path NOT treated as truth.
- Validation: `python3 scripts/check_docs_router.py --all` -> RESULT: PASS, EXIT=0, OK=5 WARN=15 ERROR=0.
  First run produced 1 ERROR on a pre-existing legacy file (docs/harness-x/ai_service_harness_x_pilot_status_
  20260609.md, untracked, not created by this task). Per Owner guidance (warnings for legacy, errors for new),
  the metadata-ERROR rule was narrowed to the GOVERNANCE HOME only (top-level docs/*.md + root governance);
  auxiliary/legacy docs/ subdirs (harness-x, architecture, execution, ...) and the docs/poster2/** corpus are
  advisory (warn). Did NOT mass-move or archive any file.
- Warnings recorded (legacy/advisory, non-blocking): 8 legacy root one-offs (archive-later: APPLY_EDIT_ENABLE_
  PATCH.md, DEPLOYMENT_CONFIG_TRUTH.md, KITPOSTER_EDIT_QUALITY_AUDIT.md, POSTER_EDIT_PATH_REVIEW.md, POST_
  RECOVERY_AUDIT.md, SAFE_PATCH_PLAN.md, VERIFICATION_CHECKLIST.md, task4_handoff.md); 1 auxiliary harness-x
  doc; 6 CUISTANCE active docs missing the new metadata block (advisory — add when next touched).
- docs/poster2/README.md left UNCHANGED (no strictly-needed index entry; router/PROJECT_STATUS point to it).
- Status: SUBMITTED FOR OWNER REVIEW. PR-1 may resume only after Owner approves this docs governance.

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-PR1-WORKBENCH-TRUTH-MODEL (2026-06-18) — SUBMITTED FOR OWNER REVIEW

- Owner lifted the PR-1 pause (docs router pilot approved; documentation governance ACTIVE). Implemented PR-1:
  minimal backend-owned workbench truth model ONLY.
- Docs router preflight: `python3 scripts/check_docs_router.py --all` -> PASS (EXIT=0, ERROR=0, legacy/advisory
  warnings only).
- Files changed: app/schemas/poster2.py (workbench models + model_validator import); app/services/
  workbench_records.py (NEW: R2 JSON + /tmp fallback store, mirrors poster_records); app/main.py (import models +
  store; 3 endpoints); tests/poster2/test_workbench_truth_model.py (NEW: 19 tests); docs status + README + log.
- Endpoints: POST /api/v2/workbench, GET /api/v2/workbench/{workbench_key}, PATCH /api/v2/workbench/{workbench_key}.
- Model fields: workbench_key/created_at/updated_at/language(zh|fr)/status(draft|assets|candidates|email_ready|
  sent)/product_truth/product_assets/email_banner + PR-2..PR-4 placeholders (poster_candidates={}, 
  selected_email_body_visual=null, email_package_ref=null, recipients=[], send_attempts=[]). product_truth =
  product_name/reference/description/parameters[]/parameters_locked. parameter row = key(reference|capacity|power|
  voltage|dimensions|material|thermostat|other)/label/value/source(manual|imported|recognized)/state(pending|
  confirmed)/locked. product_assets = product_images(<=2)/gallery_images(<=3)/atmosphere(is_truth false only).
  email_banner = logo/background/pattern/channel_name/campaign_label/selected_banner_ref.
- Validation: url/key only (base64/data: rejected); locked row requires confirmed; parameters_locked requires >=1
  row all-confirmed; invalid param key/state rejected; atmosphere is_truth=true rejected; >2 product images
  rejected; invalid status rejected; unknown/missing workbench -> 404; 190°C accepted as ordinary thermostat value
  AND a product with no thermostat row is valid (190°C NOT a platform rule); round-trip read returns identical
  truth. Tests: 19 passed. Regression: with CORS_ALLOW_ORIGINS set, test_workbench + test_api = 54 passed.
- Pre-existing artifact recorded: 6 generate-poster error/timeout/CORS tests assert access-control-allow-origin ==
  origin; without CORS_ALLOW_ORIGINS env they get '*' and fail — reproduced with my changes stashed out, so
  PRE-EXISTING + unrelated to PR-1. (Also: a pre-existing unrelated git stash "WIP on PosterSop06-beautification-
  phase1" was observed and left intact/parked — NOT created or dropped by this task.)
- Not implemented (boundaries kept): no Affiche/Fiche candidate generation; selected_email_body_visual nullable
  placeholder only; no Email Banner decoupling / Email Assembly; no renderer change (email_campaign_composite /
  template_product_sheet_v1 untouched); no /api/v2/email/preview or send change; no multi-recipient; no real
  email; no tag/merge/push; no deployment config; 190°C not hard-coded as platform rule; no contact import /
  scheduling / analytics / CRM / dashboard / automation.
- PR-2 readiness: READY to request after Owner approval (workbench base + placeholders in place).

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-PR2-CANDIDATES-AND-SELECTED-VISUAL (2026-06-18) — SUBMITTED FOR OWNER REVIEW

- Owner approved PR-1; start PR-2 only. Implemented Step-2 candidate generation + selected-visual persistence.
- Docs router preflight + final: `python3 scripts/check_docs_router.py --all` -> PASS (ERROR=0).
- Files changed: app/schemas/poster2.py (CandidateType + WorkbenchSelectVisualRequest); app/services/
  workbench_candidate_generation.py (NEW: build_candidate_payload, pure truth->payload, no renderer); app/services/
  workbench_records.py (set_poster_candidate + select_email_body_visual); app/main.py (2 endpoints, reuse
  generate_poster_v2); tests/poster2/test_workbench_candidates.py (NEW: 15 tests); docs status + README + log.
- Endpoints added (thin orchestration, REUSE /api/v2/generate-poster, no renderer fork):
  POST /api/v2/workbench/{workbench_key}/candidates/{candidate_type}/generate ;
  PATCH /api/v2/workbench/{workbench_key}/selected-visual.
- Candidate types: affiche -> template_id=email_campaign_composite_v1 (renderer_mode=puppeteer, business truth
  deterministic case001); fiche -> template_id=template_product_sheet_v1 (renderer_mode=auto, primary +
  product_secondary_image when 2 images present). Input mapping from workbench truth (product_name/reference/
  description/product_images/gallery/atmosphere is_truth=false/banner.logo kept in path — banner decoupling is
  PR-3). features=[] so candidates keep their validated default contract gates (composite callout_count=3).
- Candidate model fields: poster_candidates[type] = {poster_key (REF only; truth stays in poster_record), status
  (ready|failed), generated_at, template_id, contract_review_summary (lightweight)}. selected_email_body_visual:
  null|affiche|fiche (scalar, exactly one).
- Selection rules: cannot select candidate without poster_key or not ready (422 candidate_not_ready); selecting
  one replaces previous; regenerating the SELECTED candidate clears selected_email_body_visual to null;
  regenerating the NON-selected candidate keeps the selection; no version history; manual selection only.
- Validation: test_workbench_candidates.py = 15 passed (generate affiche/fiche store poster_key; fiche primary+
  secondary + single-image no-secondary; poster_key loadable via /api/v2/posters/{key}; select affiche/fiche;
  cannot select unready; select replaces; regen-selected clears; regen-unselected keeps; GET returns candidates+
  selection; 190°C ordinary param incl. no-thermostat product also generates; product_image_required 422;
  invalid_candidate_type 422; unknown workbench 404). Regression: test_workbench_truth_model.py = 19 passed;
  test_api.py = 35 passed (CORS_ALLOW_ORIGINS set). Pre-existing CORS env artifact unchanged (PR-1 recorded).
- Not implemented (boundaries kept): no Email Banner decoupling / Email Assembly (PR-3); no /api/v2/email/preview
  or send change; no multi-recipient; no real email; no renderer-internal change; no email_campaign_composite
  truth-gate or template_product_sheet_v1 contract change; 190°C not a platform rule; no contact import /
  scheduling / analytics / CRM / dashboard / automation; no tag/merge/push/deploy-config.
- PR-3 readiness: READY to request after Owner approval (selected candidate poster_key available for Assembly).

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-PR3-EMAIL-BANNER-AND-ASSEMBLY-PREVIEW (2026-06-18) — SUBMITTED FOR OWNER REVIEW

- Owner approved PR-2; start PR-3 only. Implemented email-level Email Banner Module + Email Assembly preview.
- Docs router preflight + final: `python3 scripts/check_docs_router.py --all` -> PASS (ERROR=0).
- Files changed: app/schemas/poster2.py (EmailAssemblyBannerView/EmailAssemblyBodyVisual/EmailAssemblyPreview
  Response); app/services/email/assembly.py (NEW: build_email_assembly — email-level banner + selected visual +
  intro/CTA + footer, no renderer); app/main.py (import + 1 thin endpoint, reuse draft + attachment path);
  tests/poster2/test_workbench_email_assembly.py (NEW: 12 tests); docs status + README + log.
- Endpoint added: POST /api/v2/workbench/{workbench_key}/email/preview. Existing POST /api/v2/email/preview
  (poster_key) and /api/v2/email/send UNTOUCHED (backward compatible).
- Email Banner Module: source = workbench.email_banner (logo/background/pattern/channel_name/campaign_label/
  selected_banner_ref); assembled at the email layer (dark brand header + logo + channel/campaign + red filet);
  NOT poster-body truth; shared by affiche + fiche; echoed in response.banner + present in assembled html.
- Selected visual consumption (deterministic): read workbench.selected_email_body_visual (affiche|fiche) ->
  poster_candidates[selected].poster_key -> load_poster_record -> final_poster.url as the body visual image.
  Gemini/frontend never choose. Failures: no selection -> 422 no_selected_email_body_visual; selected not ready
  -> 422 selected_candidate_not_ready; poster_record missing -> 404 selected_poster_record_not_found.
- Subject/preview from build_email_draft_for_poster_record (deterministic + optional grounded Gemini); intro
  from product_truth.description (fallback draft preview); CTA default Nous contacter; attachment readiness
  reuses build_email_assets_for_record (flag-gated) + available/buildable types. Preview-ready only; no send.
- AI/parameter safety: canonical copy input excludes product_truth.parameters by construction -> Gemini cannot
  invent/change technical parameters (test asserts canonical has no 'parameters'/no '190'; workbench params
  unchanged after preview). 190°C remains an ordinary parameter, not a platform rule.
- Banner decoupling boundary: done ADDITIVELY at the email-assembly layer, NO renderer change. Candidate bodies
  still carry their own baked banner today -> documented transitional state, surfaced via
  body_visual_contains_own_banner flag. Full body-only render = renderer contract change, explicitly out of PR-3.
  NO Owner Decision Needed (boundary not crossed).
- Validation: test_workbench_email_assembly.py = 12 passed; test_workbench_truth_model.py + test_workbench_
  candidates.py = 34 passed; test_api.py = 35 passed (CORS_ALLOW_ORIGINS set; pre-existing CORS env artifact
  unchanged). Existing email preview/send tests compatible.
- Not implemented (boundaries kept): no PR-4; no /api/v2/email/send change; no multi-recipient; no real email;
  no renderer-internal change; no email_campaign_composite_v1 / template_product_sheet_v1 rewrite; no composite
  truth-gate change; 190°C not a platform rule; no contact import/scheduling/analytics/CRM/dashboard/automation;
  no tag/merge/push/deploy-config.
- PR-4 readiness: READY to request after Owner approval (assembly preview package available for manual send).

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-PR3R-REFERENCE-EMAIL-HTML-EXTRACTION-PATCH (2026-06-18) — SUBMITTED FOR OWNER REVIEW

- Owner approved PR-3; small PR-3R patch before PR-4. Inspected reference emails ~/poster/SOP/ttt.html (CUISTANCE
  Mailchimp NOUVEAUTÉ, 22.7KB/666L/31 tables) + ttt2.html (Technitalia Zoho, 114KB/2091L/40 tables). Both are
  table-based 600px emails. Code+docs (minimal additive); did NOT start PR-4.
- Docs router preflight + final: `python3 scripts/check_docs_router.py --all` -> PASS (ERROR=0).
- Files changed: docs/poster2/cuistance_commercial_trial_reference_email_html_extraction_v1.md (NEW extraction
  doc); app/services/email/assembly.py (minimal alignment); tests/poster2/test_workbench_email_assembly_
  reference.py (NEW: 7 tests); PR-3 status doc (PR-3R note) + README + log.
- Extracted email grammar: 600px container; top banner module; red/orange filet (#df3004 / #db4b38 / #eb7a00 ->
  platform keeps #E1002A); title/intro; body-visual placement; CTA; contact/footer + 4-icon contact row
  (telephone/email/catalogue/site) + FB/LinkedIn/Instagram social row; legal/unsubscribe placeholder; asset-URL
  inventory (mailchimp 0a50184e header + product imgs; zoho bandeau_technitalia / banniere_1 / banniere_2 /
  rechauds / contact+social icons).
- Adopted assembly changes (assembly.py only): container 640px -> 600px wrapped in a table-safe shell
  (<table role="presentation" width="600" max-width:600px>); explicit red filet <div height:3px background:#E1002A>;
  footer legal/unsubscribe placeholder (non-functional href="#", "Se désabonner" + "contact professionnel").
  Preserved: Email Banner Module, selected body visual, intro/CTA, attachment readiness; endpoint
  POST /api/v2/workbench/{key}/email/preview unchanged; /api/v2/email/send untouched.
- NOT copied: Zoho/Mailchimp scripts, tracking pixels, list-manage/campaign-image tracking, share/comment
  widgets, view-in-browser overlays, hidden campaign IDs, third-party unsubscribe implementation, raw email HTML
  wholesale. Test asserts assembled html has NO <script/list-manage/mcusercontent/campaign-image/zoho/mailchimp/
  track.
- Validation: test_workbench_email_assembly_reference.py = 7 passed (600px table-safe shell; banner module; red
  filet; selected body visual; CTA; footer+legal placeholder; no third-party tracking). Regression: PR-3
  assembly 12 + PR-3R 7 = 19; PR-1+PR-2 = 34; test_api.py = 35 (CORS env). Existing PR-3 assembly tests still
  pass (preserved #1f2329 / logo / channel / body url / intro / cta substrings).
- Future work (documented, not done): contact icon row + social icon row (need workbench contact/social model);
  real body-only banner decoupling (renderer contract change, out of scope).
- PR-4 readiness: READY to request after Owner approval.

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-PR3S-EMAIL-BODY-PLAN-BEFORE-SEND (2026-06-18) — SUBMITTED FOR OWNER REVIEW

- Owner PAUSED PR-4; added PR-3S (Email Body Plan before send). Reason: email body needs a planned deterministic
  structure; the selected poster/product visual must enter a planned slot, not loose concatenation.
- BACKOUT of prematurely-started PR-4: removed the workbench send endpoint + WorkbenchEmailSend* schemas +
  app/services/email/workbench_send.py + workbench_records.append_send_attempts + their main.py imports. Branch
  now has NO send path; existing single-recipient /api/v2/email/send UNTOUCHED. Verified grep clean.
- Docs router preflight + final: `python3 scripts/check_docs_router.py --all` -> PASS (ERROR=0).
- Files changed: app/schemas/poster2.py (SelectedBodyVisualSlot/EmailBodyPlanModule/EmailBodyPlanCta/
  EmailBodyPlanView + email_body_plan on EmailAssemblyPreviewResponse); app/services/email/assembly.py
  (build_email_assembly now generates HTML FROM the plan order; +poster_key param; returns email_body_plan);
  app/main.py (preview passes poster_key + returns email_body_plan); tests/poster2/test_workbench_email_body_
  plan.py (NEW: 11 tests); docs status + README + log.
- EmailBodyPlan fields: layout_type=single_product_promo; container_width=600; modules[order,key,present] with
  fixed order email_banner -> title_intro -> selected_body_visual -> product_description -> cta -> contact_footer
  -> legal_footer; selected_body_visual_slot{source=workbench.selected_email_body_visual, candidate_type,
  poster_key, final_poster_url}; cta{label=Nous contacter, href=#}.
- selected_body_visual_slot behavior: backend-only selection -> poster_candidates[selected].poster_key ->
  load_poster_record -> final_poster.url; the URL enters HTML ONLY via the selected_body_visual module (test
  asserts single occurrence + banner precedes it). Gemini/frontend never choose; final_poster_url from loaded
  poster_record not request input.
- Validation: test_workbench_email_body_plan.py = 11 passed; PR-3+PR-3R assembly = 19; +PR-1+PR-2 = 53;
  test_api.py = 35 (CORS env). Existing /api/v2/email/preview + /send compatible. Pre-existing CORS env artifact
  unchanged (PR-1 recorded). PR-3/PR-3R assertions preserved (plan-driven refactor kept #1f2329/logo/channel/
  body-url/Nous contacter/#E1002A/height:3px/Se désabonner/contact professionnel/width=600/role=presentation).
- Not implemented (boundaries kept): no PR-4; no send endpoint; no /api/v2/email/send change; no multi-recipient;
  no real email; no renderer change; no email_campaign_composite_v1 / template_product_sheet_v1 rewrite; 190°C
  not a platform rule; no contact import/CRM/scheduling/analytics/dashboard/automation; no tag/merge/push/deploy.
- PR-4 readiness: NOW READY to request — PR-4 will send the planned package (email_body_plan + deterministic
  assembly), auditable + reproducible. Awaiting Owner approval.

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-PR4-MANUAL-MULTI-RECIPIENT-SEND-EVIDENCE (2026-06-18) — SUBMITTED FOR OWNER REVIEW

- Owner approved PR-3S; resumed PR-4. Implemented manual multi-recipient confirmed send of the deterministic
  PR-3S package + per-recipient evidence. Completes the v1 commercial backend loop.
- Docs router preflight + final: `python3 scripts/check_docs_router.py --all` -> PASS (ERROR=0).
- Files changed: app/schemas/poster2.py (SendMode/WorkbenchEmailSendRequest [no html/subject override]/
  WorkbenchSendAttempt [+layout_type +deduplicated]/WorkbenchEmailSendResponse); app/services/email/
  workbench_send.py (RE-ADDED: normalize_recipients + is_valid_email); app/services/workbench_records.py
  (RE-ADDED: append_send_attempts); app/main.py (NEW _resolve_workbench_email_package shared by preview+send;
  preview refactored to reuse it; NEW send endpoint); tests/poster2/test_workbench_email_send.py (NEW: 14 tests);
  docs status + README + log.
- Endpoint added: POST /api/v2/workbench/{workbench_key}/email/send. UNCHANGED: /api/v2/email/send (single
  recipient, backward compatible); /api/v2/workbench/{key}/email/preview (refactored to reuse resolver, same
  behavior).
- Send confirmation: confirm_send must be true (test AND real); no implicit send. Guard order: resolve
  deterministic package (no_selected_email_body_visual / selected_candidate_not_ready / email_body_plan_
  unavailable / selected_poster_record_not_found) -> confirm_send_required -> recipients_required.
- Recipient handling: manual recipients[] only (free-text, not EmailStr); empty -> 422; case-insensitive
  order-preserving dedup with deduplicated_count; per-recipient isolation (invalid_recipient / provider_exception
  do not erase others' evidence). No contact import/Excel/CRM/scheduling/segmentation/analytics.
- EmailBodyPlan consumption: send consumes the SAME package as preview via _resolve_workbench_email_package
  (email_body_plan + subject/preview_text/html/text). Send does NOT reconstruct body, NOT choose candidate,
  NOT call Gemini to change facts, NOT generate a new poster; request accepts NO arbitrary html/subject override.
- Evidence fields (workbench.send_attempts, no provider secrets): recipient, mode, status(sent|error|skipped),
  provider, provider_message_id, error_code, error_message, attachment_types, at(ISO), selected_email_body_visual,
  body_visual_poster_key, layout_type(=email_body_plan.layout_type), subject snapshot, deduplicated. Response:
  total/sent_count/failed_count/skipped_count/deduplicated_count/attempts[]. inline_only -> preview_only -> skipped;
  resend -> sent; real+sent marks workbench status=sent.
- Validation: test_workbench_email_send.py = 14 passed (no-selection 422; not-ready 422; plan-unavailable 422;
  empty recipients 422; confirm_send false 422 [test+real]; valid recipients produce attempts; mixed valid/invalid
  isolate; dedup deterministic; attempt has selected_visual+poster_key; layout_type; subject+timestamp; unknown
  404; real marks sent). NO real email sent (inline / fake provider). Regression: workbench PR-1..PR-4 = 78
  passed; test_api.py = 35 passed (CORS env). Existing /api/v2/email/send compatible.
- Not implemented (boundaries kept): no contact import/Excel/CRM/scheduling/analytics/open-click/dashboard/
  automation; no renderer change; no email_campaign_composite_v1 / template_product_sheet_v1 rewrite; no arbitrary
  HTML/subject override; 190C not platform rule; no tag/merge/push/deploy; tests do not send real email.
- v1 commercial backend loop: COMPLETE (PR-1 truth -> PR-2 candidates+selection -> PR-3 banner+assembly -> PR-3R
  reference grammar -> PR-3S body plan -> PR-4 confirmed manual send + evidence).
- Operator trial: READY to request (backend complete/deterministic/auditable). Pre-trial ops config (not code):
  real resend provider + verified sender domain; test-mode dry run; then real send to small manual list.

## POSTER2-CUISTANCE-COMMERCIAL-TRIAL-FULL-FLOW-SMOKE-V1 (2026-06-18) — SUBMITTED FOR OWNER REVIEW

- Runtime-heavy full-flow smoke (in-process FastAPI TestClient against the real app; no new features). Docs
  router preflight + final: PASS (ERROR=0). Secret-safe config inspection only (no secrets printed).
- Environment (no secrets): Resend is_configured=False (NO real delivery possible); Vertex Imagen3 not
  initialised; R2 not configured (poster hosting -> inline_data_url, records -> /tmp); Gemini optimizer disabled;
  attachments disabled; network + Chromium available (affiche real render feasible).
- Flow ran end-to-end on the affiche main route: create wb_33656232431e46a4 -> patch product_truth (EF132V; 190C
  as ordinary confirmed thermostat param) -> patch product_assets + email_banner (real public image URLs) ->
  generate affiche + fiche -> select affiche -> preview -> test send -> read send_attempts.
- affiche: poster_key p2_4fb82bb4ba5e4120, status=ready, render_engine=chromium, degraded=false,
  structure_complete=true, callout_count=3 (REAL Chromium composite render).
- fiche: HTTP 422 FAILED, stage=material_prepare, code=background_prepare_failed, detail="Vertex Imagen3 client
  is not initialised" -> poster_candidates.fiche.status=failed (no poster_key). affiche unaffected.
- selected_email_body_visual=affiche. Preview HTTP 200, ALL checks pass: email_body_plan present;
  layout_type=single_product_promo; container_width=600; slot.poster_key=p2_4fb82bb4ba5e4120; final_poster_url
  present (data: URL, R2 unconfigured); 600px table shell; banner module (#1f2329); red filet (#E1002A); CTA
  (Nous contacter); footer/legal (Se désabonner). body_visual.url from loaded poster_record, not frontend.
- Send (test, inline_only): recipients [owner-internal-test@cuistance.eu, dup@, DUP@, bad@@]; total unique=3,
  deduplicated_count=1, sent_count=0, skipped_count=2 (preview_only), failed_count=1 (bad@@ invalid_recipient).
  Each attempt carries layout_type=single_product_promo, body_visual_poster_key, subject snapshot, at timestamp.
  workbench status stayed draft (test mode). Resend probe (delivery_mode=resend): status=error,
  error_message="Resend is not configured.", no provider_message_id.
- REAL EMAIL SENT: NO (no provider_message_id from any attempt; inline_only=preview_only, resend=not configured).
  real mode NOT run (Resend unconfigured + no Owner-approved address).
- Blockers (runtime config only, NOT workbench logic): (1) Resend not configured -> no real send; (2) Vertex
  Imagen3 not initialised -> fiche candidate fails (affiche does not need it); (3) R2 not configured -> inline
  data URL hosting; (4) non-blocking: Gemini/attachments disabled.
- Validation: check_docs_router --all PASS; pytest test_workbench_email_send.py + test_workbench_email_body_plan.py
  = 25 passed.
- Recommendation: HOLD for real customer send -> GO after configuring Resend (API key + verified sender domain),
  Vertex (only if fiche needed; affiche works without), R2 (HTTPS poster URLs); then test-mode dry run to confirm
  provider_message_id, then real mode to a small Owner-approved internal list; re-run smoke.
- Evidence doc: docs/poster2/cuistance_commercial_trial_full_flow_smoke_result_v1.md. No tag/merge/push; no
  secrets printed; internal test recipient only; no customer list.

## POSTER2-CUISTANCE-V1-OPERATOR-TRIAL-BRANCH-PREP (2026-06-18) — SUBMITTED FOR OWNER REVIEW

- Prepared (NOT created) operator-trial branch trial/poster2-cuistance-v1-operator-trial off base
  feature/poster2-email-campaign-composite-remote-smoke-v1 @ 11ece26. Docs-only + validation package; no branch
  create/commit/push/merge/tag; no deploy change; no secrets printed.
- Docs router: PASS (ERROR=0). Trial tests: test_workbench_truth_model + candidates + email_assembly +
  email_assembly_reference + email_body_plan + email_send = 78 passed. Existing test_api.py = 35 with
  CORS_ALLOW_ORIGINS set (pre-existing CORS-env caveat unchanged).
- Scope confirmed clean: app/ changes are ONLY workbench/email PR-1..PR-4 files (main.py, schemas/poster2.py [M];
  services/workbench_records.py, services/workbench_candidate_generation.py, services/email/assembly.py,
  services/email/workbench_send.py [new]). NO tracked frontend modifications; NO deploy/render/CI/requirements/
  .env changes.
- Runtime config (secret-safe, this env): EMAIL_PROVIDER/EMAIL_SEND_ENABLED/EMAIL_PREVIEW_ENABLED/
  EMAIL_OUTBOX_ENABLED unset; RESEND_API_KEY missing; RESEND_FROM_EMAIL/EMAIL_FROM/EMAIL_FROM_NAME missing/unset;
  resend.is_configured=False; R2 configured=False; Vertex configured=False; attachment enabled=False; gemini
  optimizer enabled=False.
- Known limitations: fiche fails without Vertex; real send unavailable without Resend; inline data URL without R2.
  affiche main route + preview + test-send(inline)/evidence are validatable in this env.
- KEY FINDING: PR-1..PR-4 + governance + CUISTANCE docs are UNCOMMITTED in the working tree (HEAD still 11ece26)
  amid heavy unrelated untracked churn (catalog_hero/hybrid docs, .DS_Store, fonts, harness-x). A clean trial
  branch needs a precise SCOPED commit (NOT git add -A). Exact proposed commands documented in the prep doc;
  held for Owner approval. Recommend adding .DS_Store to .gitignore.
- Recommendation: logic GO (loop complete/deterministic/auditable; tests pass); real-customer send HOLD until
  Resend + verified sender (and Vertex if fiche needed, R2 for HTTPS posters) configured. Push/deploy NOT
  requested; awaiting Owner approval to create the scoped branch+commit.
- Evidence doc: docs/poster2/cuistance_commercial_trial_operator_validation_branch_prep_v1.md.

## POSTER2-CUISTANCE-V1-TRIAL-BRANCH-PUSH-AND-REMOTE-SMOKE (2026-06-18) — SUBMITTED FOR OWNER REVIEW

- Phase A: created branch trial/poster2-cuistance-v1-operator-trial off feature@11ece26; staged ONLY the 25
  approved files (no git add -A); verified staged set (no .DS_Store/.env/deploy/frontend/unrelated churn);
  router PASS; 78 trial tests passed; committed 972bdc3f5190a7cde73377b2e2dad06ff84084b9 "poster2: prepare
  cuistance v1 operator trial loop" (25 files, +4706/-1).
- Phase B: pushed trial branch to origin (https://github.com/zhaojfifa/ai-service) — new branch. NO merge, NO
  tag, NO main push.
- Phase C: render.yaml = single service marketing-poster-api, NO branch pin, NO validation service -> Render
  won't auto-deploy trial/*; deploy needs a dashboard action (no console/API access; deploy-config change
  forbidden). Live host ai-service-leob.onrender.com /health=200 but serves dashboard branch (not trial);
  ai-service-x758 /health=404. All /api/v2/* return 401 (OPS auth gated); /api/auth/me=200. No OPS credentials
  used/printed.
- Phase D: remote full-flow smoke NOT executed (blocked: trial branch not deployed + OPS 401 + Resend/R2 not
  declared remotely). No workbench created remotely; no email sent; no provider_message_id.
- Secret-safe remote config inference (render.yaml env NAMES only): Vertex (GCP_*/VERTEX_*) + Firefly
  (FIREFLY_*) + Chromium (playwright install in buildCommand) declared -> affiche/fiche may render remotely;
  RESEND_* and R2_/S3_ NOT declared -> real send + HTTPS posters likely unavailable; OPS_* declared (matches
  401).
- OWNER DECISION NEEDED (deploy target): Option A new Render validation service pinned to trial branch (+env +
  OPS cred delivery) [recommended]; Option B temporarily repoint marketing-poster-api to trial branch
  (changes prod; needs explicit approval); Option C Render PR-preview env. All require Resend (+ R2 optional)
  config in the target.
- Recommendation: code/branch GO (pushed, scoped, local green); remote operator validation HOLD pending Owner
  deploy choice + provider config + OPS credentials. Then re-run remote smoke: test mode (verify
  provider_message_id) then real mode to Owner-approved internal address only (no customer list).
- Evidence doc: docs/poster2/cuistance_commercial_trial_remote_full_flow_smoke_result_v1.md.

## POSTER2-CUISTANCE-V1-EXPOSE-OPERATOR-TRIAL-UI (2026-06-18) — SUBMITTED FOR OWNER REVIEW
- Added static operator page /cuistance_trial.html (frontend/cuistance_trial.html + docs/ mirror), served by the
  existing StaticFiles mount. NO backend API change; NO route added; NO renderer/send-behavior/deploy-config
  change. Title "CUISTANCE v1 · Operator Trial · 商业试用工作台", explicitly distinct from / and /ops_campaign.html.
- Page drives the full v1 loop via existing endpoints: create workbench -> patch EF132V product_truth -> patch
  product_assets+email_banner (URL/key) -> generate affiche -> generate fiche (allowed to fail w/o Vertex,
  shown as failure, non-blocking) -> select (default affiche) -> email/preview (shows EmailBodyPlan: layout_type/
  container_width/selected_body_visual_slot/final_poster_url + HTML iframe) -> email/send (default test+inline;
  real requires Mode=real + Confirmer checkbox) -> send_attempts table. Shows workbench_key/affiche poster_key/
  fiche status/selected visual/preview status/send mode/provider result/whether real email sent (only 'yes' if
  provider_message_id present).
- Safety: default test mode (not real), manual single internal recipient only, double confirm for real send, no
  contact import/Excel/CRM/scheduling/analytics/dashboard, URL/key assets only, OPS-login affordance for gated
  /api/v2/*, no secrets hard-coded.
- Validation (local, in-process): GET /cuistance_trial.html=200 (title + 商业试用工作台 present); API wiring
  create->affiche(ready, p2_25fdb43b2e5f4ad8)->select->preview(200, layout=single_product_promo, width=600,
  slot poster_key match, 600px shell) green. Example workbench_key wb_7d17dce109fc475f. Send: local inline_only
  -> preview_only (no real delivery); real send is remote-capability pending Resend config.
- Docs router: PASS (ERROR=0). Files: frontend/cuistance_trial.html, docs/cuistance_trial.html,
  docs/poster2/cuistance_commercial_trial_operator_ui_exposure_status_v1.md, README, log.
- Blockers: remote real send needs Resend+verified sender on target service; fiche remote needs Vertex; remote
  /api/v2/* OPS-gated (operator logs in on page); new page visible remotely only after trial-service deploy
  refresh.
- Operator manual validation: READY (test mode) after deploy refresh; real internal send HOLD pending Resend +
  Owner-approved internal address.
