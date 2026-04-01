# Current Branch Execution Log v1

**Branch:** `fix/poster2-task1-bottom-runtime-v2`
**Last updated:** 2026-03-30

This log records what has been completed on this branch in chronological order. Each entry names the commit scope, what changed, and what the acceptance evidence is.

---

## Entry 1 — Beautification Phase 1: Shell / Shadow / Connector Visual Refinement

**Commit:** `85405d4 feat(poster2): beautification phase 1 — shell/shadow/connector visual refinement`

### What changed
- `glass_light` shell variant applied to product/scenario shells
- `soft_line` border token
- `soft` shadow token
- Feature connector and marker visual refinement

### Acceptance
- Visual: renders correctly in production generate path
- Tests: 179/179 pass at time of merge
- Documented in: `docs/poster2/beautification_phase1_status_v1.md`

---

## Entry 2 — Product Anchor Callouts: Live Production Activation

**Commit:** `a2b61f6 feat(poster2): activate product_anchor_callouts as live production mode`

### What changed
- `template_dual_v2.json` `feature_mode` switched from `count_driven_callout_stack` → `product_anchor_callouts`
- `_build_product_annotation_contract_review()` added to pipeline
- `product_annotation_contract_review` field added to `RenderManifest`
- Stage 2 frontend: annotation chip + per-slot evidence panel
- `product_annotation_mode` exposed in `behavior_modes`

### Acceptance
- 179/179 tests pass
- Documented in: `docs/poster2/product_region_annotation_contract_status_v1.md`

---

## Entry 3 — Bottom SOP: Close Header Agent Lane and Bottom Text Budget Under Split Mode

**Commit:** `32839e8 fix(poster2): close header agent lane and bottom text budget under split mode`

### What changed
- Header agent lane collapse behavior fixed under split mode
- Bottom text budget correction under `title_gallery_split` mode

### Acceptance
- Tests pass

---

## Entry 4 — Scenario Region: Resolver Evidence Coverage and Renderer Parity Scoping

**Status:** In progress (current work)

### What changed

#### Backend
- `_build_scenario_contract_review()` added to `pipeline.py`
  - Emits: `hero_mode`, `scenario_enabled`, `scenario_render_policy`, source chain (`requested/sanitized/rendered`), `safe_fill_applied`, `source_binding`, `scenario_region` (rendered + bounds), `scenario_slot` (rendered + reason_code + source_binding + bounds), `behavior_policy` (render_policy, fit, anchor, peer_layout_policy, scenario layout_metrics), `renderer_path_parity` note, `evidence_source`
- `scenario_contract_review` field added to `RenderManifest` in `contracts.py`
- Wired into `renderer_metadata_payload` and `RenderManifest()` in `pipeline.py`

#### Frontend
- `app.js`: `setJson('poster2-scenario-contract-review', data?.scenario_contract_review, '{}')`
- `stage2.html`: `<pre id="poster2-scenario-contract-review">` element
- `stage2.html`: `buildScenarioDetail(scenarioReview)` function
- `stage2.html`: `scenario_region` display branch uses `buildScenarioDetail(scenarioReview)` when payload present; falls back to `buildHeroDetail(heroReview, 'scenario_region')` when absent
- `docs/`: synced via `scripts/sync_frontend_to_docs.sh`

#### Tests
- `tests/poster2/test_pipeline.py`:
  - `test_scenario_contract_review_exposes_full_evidence_for_scenario_cover_mode`
  - `test_scenario_contract_review_exposes_disabled_policy_for_single_product_focus`
- `tests/test_stage2_guard_diagnostics_surface.py`:
  - `test_frontend_stage2_surfaces_scenario_contract_review`

#### Docs
- `docs/poster2/scenario_region_resolver_and_renderer_parity_status_v1.md` — formal parity scope decision and open follow-up

### Acceptance criteria
- `scenario_region` has explicit contract review, bounds, source, and policy evidence ✓
- Stage 2 reads scenario evidence from backend payload ✓
- Renderer-path differences formally documented (safe_fill Pillow vs Puppeteer divergence) ✓
- Product annotation remains intact and backend-driven ✓
- 184/184 tests pass (182 poster2 + 2 mirror tests before new additions)

### Open follow-ups from this entry
- Align Pillow `scenario_safe_fill` to match Puppeteer conditional logic (evidence accuracy)
- `header_region`: complete `identity_zone_mode` resolver wiring
- `scenario_region`: renderer safe_fill parity test (blocked on Pillow fix above)
- Preview-path / generation-path parity (Puppeteer vs Pillow)

---

## What Remains on This Branch

- `header_region`: `identity_zone_mode` resolver wiring
- `scenario_region`: Pillow safe_fill parity fix + parity test
- Product secondary slot: Pillow renderer to consume `product_secondary_slot` for actual rendering
- Text layer evidence: Puppeteer parity (currently Pillow-only)
- Beautification layer planning (after all-region behavior stability confirmed)

---

## Entry 5 — Family A Structural Closeout: Bottom Expansion, Dual Product Contract, Text Layer Evidence

**Status:** Complete

### What changed

#### Diagnosis + Contract docs
- `docs/poster2/family_a_structural_closeout_diagnosis_v1.md` — structural root-cause analysis: why budget tuning cannot fix bottom text truncation; product slot hierarchy gap; text evidence gap
- `docs/poster2/family_a_structural_closeout_contract_v1.md` — new contract mode surface: expanded bottom modes, dual product slots, three text layer evidence targets

#### A. Bottom structural expansion (`template_behavior.py`)
- `text_only_expanded` added to `_SUPPORTED_BOTTOM_MODES`
  - `bottom_shell_top = 656` (72px higher than frozen baseline y=728)
  - `title_band_height` 164–220px (content-driven), `title_char_budget` 52–72, `subtitle_char_budget` 60–80
  - `gallery_strip_rendered` always False; no gallery geometry computed
- `text_gallery_expanded` added to `_SUPPORTED_BOTTOM_MODES`
  - `bottom_shell_top = 640` (88px higher than frozen baseline)
  - `title_char_budget` minimum 44 even under 4-item gallery (vs 20 in frozen baseline dense-quad)
  - `gallery_strip_rendered` True; gallery items layout alongside expanded text band
- `_EXPANDED_BOTTOM_SHELL_TOPS` dict drives the geometry dispatch
- `bottom_layout_mode` field exposed in `ResolvedBottomBehavior` and emitted in evidence
- Frozen baseline modes (`title_gallery_split`, `title_only`, `gallery_only`) are unchanged

#### B. Product region structural upgrade (`template_behavior.py`, `contracts.py`)
- `product_layout_mode` added to `TemplateBehaviorModesSpec` (default `single_primary`)
- `_SUPPORTED_PRODUCT_LAYOUT_MODES = {"single_primary", "primary_secondary_dual"}`
- `_PRODUCT_DUAL_PRIMARY_SLOT` and `_PRODUCT_DUAL_SECONDARY_SLOT` constants defined
- `ResolvedProductBehavior` extended with:
  - `product_layout_mode`, `product_primary_slot`, `product_secondary_slot`
  - `product_secondary_slot_rendered`, `product_secondary_asset_policy`
- `resolve_product_behavior` dispatches on mode; annotation shell remains on primary slot only
- `_build_product_contract_review` exposes all new fields as contract evidence

#### C. Text layer evidence (`pipeline.py`, `contracts.py`, `schemas/poster2.py`, `main.py`)
- Three new builder functions: `_build_title_text_layer_evidence()`, `_build_subtitle_text_layer_evidence()`, `_build_header_text_layer_evidence()`
- Each emits: `layer_id`, `rendered`, `slot_bounds`, `requested_text`, `sanitized_text`, `rendered_excerpt`, `truncation_applied`, `line_clamp`, `char_budget`, `owner_region`
- `header_text_layer` includes `brand_text_slot` and `agent_text_slot` sub-structures with slot bounds from `header_policy.layout_metrics`
- Wired into `renderer_metadata_payload` and `RenderManifest`
- `GeneratePosterV2Response` schema extended with the three new fields
- `main.py` response builder passes through all three fields

#### D. Schema update (`schemas/poster2.py`)
- `GeneratePosterV2Request.bottom_mode` now accepts `text_only_expanded` and `text_gallery_expanded`

#### Tests (`tests/poster2/test_pipeline.py`)
- `TestBottomStructuralExpansion`:
  - `test_text_only_expanded_resolves_with_larger_text_capacity_than_frozen_baseline`
  - `test_text_gallery_expanded_resolves_with_adequate_title_budget_for_dense_quad`
  - `test_frozen_baseline_modes_still_resolve_unchanged`
- `TestProductLayoutContract`:
  - `test_single_primary_mode_is_backward_compatible_default`
  - `test_primary_secondary_dual_exposes_named_slots`
  - `test_annotation_mode_unaffected_by_dual_product_layout`
- `TestTextLayerEvidence`:
  - `test_title_text_layer_emitted_with_correct_structure`
  - `test_subtitle_text_layer_emitted_with_correct_structure`
  - `test_header_text_layer_emitted_with_brand_and_agent_slots`
  - `test_title_text_layer_truncation_applied_flag_reflects_actual_truncation`

### Acceptance criteria
- `text_only_expanded` mode shell starts at y=656 with materially larger text budgets than frozen baseline ✓ (contract)
- `text_gallery_expanded` mode holds full 35-char title alongside 4 gallery items ✓ (contract)
- `primary_secondary_dual` exposes `product_primary_slot` and `product_secondary_slot` as named contract surfaces ✓
- `title_text_layer`, `subtitle_text_layer`, `header_text_layer` emitted per generation with `truncation_applied` field ✓
- Frozen baseline modes unchanged ✓ (contract additive)
- `product_annotation_mode = product_anchor_callouts` remains live ✓

### Test results
- 207/207 pass (196 prior + 11 new)
- New tests: 4 (bottom expansion) + 3 (product layout) + 4 (text layer evidence)

### Open follow-ups from this entry
- Renderer (Pillow) does not yet use `product_secondary_slot` for actual rendering — contract-only for now; rendering parity is a follow-up
- Preview-path (Puppeteer) does not yet emit text layer evidence — parity follow-up
- `header_region` `identity_zone_mode` resolver wiring still pending
- Beautification may start once this structural slice is confirmed stable in live generation

---

## Entry 6 — Family A Structural Closeout: Runtime Routing Takeover

**Status:** Complete

### What changed

#### A. Bottom mode routing closeout
- `bottom_contract_review` now exposes:
  - `requested_bottom_mode`
  - `effective_bottom_mode`
  - `bottom_mode_override_reason`
- Runtime request overrides no longer disappear into template defaults:
  - `title_only` remains `title_only`
  - `text_only_expanded` remains `text_only_expanded`
  - `text_gallery_expanded` remains `text_gallery_expanded`
- Stage 2 product/bottom region cards now display backend-provided bottom routing evidence; no frontend mode inference was added

#### B. Product dual-image runtime closeout
- `resolve_product_behavior()` now auto-promotes `single_primary` to `primary_secondary_dual` when a real secondary product asset is present
- `product_layout_mode_reason` is emitted so runtime can explain why dual mode became active
- Pillow now draws `product_secondary_image` into `product_secondary_slot`; dual-image is no longer HTML-contract-only
- `product_secondary_image_layer` is now explicit in `product_contract_review`

#### C. Product geometry closeout
- `geometry_evidence.slot_bounds.product_slot` now reflects the real primary product slot in dual mode, not the old single-image region box
- `geometry_evidence.slot_bounds.product_primary_slot` and `geometry_evidence.slot_bounds.product_secondary_slot` are both emitted
- `product_region` count now reflects both product image layers when dual mode is active

### Acceptance
- Bottom runtime reports requested/effective/override chain ✓
- `title_only` no longer silently resolves to `title_gallery_split` ✓
- `text_only_expanded` / `text_gallery_expanded` are selectable and verifiable in runtime ✓
- `product_secondary_image` is rendered by Pillow when present ✓
- `primary_secondary_dual` is activated in runtime when a secondary asset exists ✓
- `product_secondary_slot` carries real bounds in contract review and geometry evidence ✓
- Stage 2 remains backend-evidence-driven ✓

### Fresh runtime verification
- Local temporary runtime wrapper used only to bypass missing storage on the dev machine; request still hit real `/api/v2/generate-poster`
- Trace: `53b39768-7d18-46fe-bfd5-2d563584127a`
- Result:
  - `degraded = false`
  - `structure_complete = true`
  - `deliverable = true`
  - `requested_bottom_mode = text_gallery_expanded`
  - `effective_bottom_mode = text_gallery_expanded`
  - `bottom_mode_override_reason = request_override_applied`
  - `product_layout_mode = primary_secondary_dual`
  - `product_layout_mode_reason = auto_promoted_by_secondary_asset`
  - `geometry_evidence.slot_bounds.product_slot = {x:456,y:188,w:300,h:310}`
  - `geometry_evidence.slot_bounds.product_secondary_slot = {x:456,y:506,w:300,h:202}`

### Tests
- `180 passed, 2 warnings`
- Command:
  - `python -m pytest tests/poster2/test_api.py tests/poster2/test_contracts.py tests/poster2/test_renderer.py tests/poster2/test_pipeline.py tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py`

### What is now truly live
- Bottom mode selection is not just accepted by the request schema; it is now inspectable as requested/effective runtime routing
- Product secondary assets no longer stop at evidence-only contract surfaces; they activate dual layout and render into a real secondary slot

---

## Entry 7 — Family A Final Alignment: Canonical Bottom/Product Truth

**Status:** Complete

### What changed

#### A. Canonical bottom layout mode alignment
- `bottom_contract_review` now carries both semantic routing truth and layout truth:
  - `requested_bottom_mode`
  - `effective_bottom_mode`
  - `bottom_layout_mode`
  - `bottom_mode_override_reason`
- Canonical semantic modes are now stable:
  - `title_only`
  - `title_gallery_split`
  - `gallery_only`
- Expanded bottom variants are now treated as layout aliases instead of separate semantic runtime truth:
  - `text_only_expanded` -> semantic `title_only`
  - `text_gallery_expanded` -> semantic `title_gallery_split`

#### B. Bottom v2 geometry closeout
- Expanded bottom geometry is now the actual runtime geometry for Family A split/text-only paths
- Runtime no longer reports semantic `title_gallery_split` while silently staying on older split-shell geometry
- Stage 2 now shows both semantic mode and backend-provided layout mode without inventing any frontend routing

#### C. Product dual-image v2 geometry closeout
- `product_layout_mode = primary_secondary_dual` now activates a real `product_geometry_mode = primary_secondary_dual_v2`
- `product_secondary_slot` is emitted with real bounds in `geometry_evidence.slot_bounds`
- `product_secondary_image_layer` is now a live rendered layer, not only contract-only evidence

#### D. Feature vs product-annotation responsibility cleanup
- When `product_annotation_mode = product_anchor_callouts`, ownership now cleanly shifts to `product_region`
- `feature_contract_review` explicitly marks:
  - `responsibility_owner = product_region`
  - `delegated_to_product_annotation = true`
- `feature_region` no longer pretends it still rendered independent callouts in the same runtime

### Acceptance
- Canonical bottom routing and bottom layout mode are both inspectable in runtime ✓
- Expanded bottom runtime no longer silently hides behind old split geometry ✓
- Dual-image product runtime uses real secondary-slot geometry ✓
- Feature/product-annotation responsibility is no longer ambiguous in runtime evidence ✓
- Stage 2 remains backend-evidence-driven ✓

### Fresh runtime verification
- Temporary local runtime wrapper used only to provide fake assets and storage while hitting real `/api/v2/generate-poster`
- Request id: `p2-family-a-final`
- Trace: `64445219-4329-469c-85a4-1c521a0499ad`
- Result:
  - `degraded = false`
  - `structure_complete = true`
  - `deliverable = true`
  - `requested_bottom_mode = title_gallery_split`
  - `effective_bottom_mode = title_gallery_split`
  - `bottom_layout_mode = text_gallery_expanded`
  - `bottom_mode_override_reason = requested_matches_template_default`
  - `product_layout_mode = primary_secondary_dual`
  - `product_geometry_mode = primary_secondary_dual_v2`
  - `product_layout_mode_reason = auto_promoted_by_secondary_asset`
  - `product_geometry_mode_reason = dual_image_geometry_v2_selected`
  - `geometry_evidence.slot_bounds.product_secondary_slot = {x:456,y:506,w:300,h:202}`
  - `feature_contract_review.responsibility_owner = product_region`
  - `feature_contract_review.delegated_to_product_annotation = true`

### Tests
- `181 passed, 2 warnings`
- Command:
  - `python -m pytest tests/poster2/test_api.py tests/poster2/test_contracts.py tests/poster2/test_renderer.py tests/poster2/test_pipeline.py tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py`

### What is now truly live
- Family A bottom runtime tells the truth in two layers: semantic bottom mode and actual layout mode
- Family A dual-image product runtime uses dedicated v2 geometry instead of piggybacking on single-image geometry
- Product annotation ownership and feature delegation are now explicit in backend evidence and visible in Stage 2 diagnostics

---

## Entry 8 — Task-1: text_gallery_expanded and gallery_only runtime stabilization

**Status:** Complete

### Scope
- Task-1 only
- no beautification
- no geometry rewrite
- no product-region finalization
- no delivery/capacity tuning

### What changed
- Added API-path guards so `text_gallery_expanded` and `gallery_only` must preserve:
  - `requested_bottom_mode`
  - `effective_bottom_mode`
  - `bottom_layout_mode`
  - `bottom_mode_override_reason`
- Added Stage 2 diagnostics guards so the backend-driven panel must continue to surface:
  - requested/effective bottom runtime line
  - layout mode line
  - `text_gallery_expanded` / `gallery_only` controls
- Re-ran fresh local HTTP runtime verification for both modes without introducing any frontend layout inference

### Fresh runtime verification
- Temporary local runtime wrapper used only to provide fake assets/storage while hitting real `/api/v2/generate-poster`

#### `text_gallery_expanded`
- request id: `p2-task1-text-gallery`
- trace: `bb2c29ea-c595-4866-8c2a-89040aa4edcb`
- result:
  - `degraded = false`
  - `structure_complete = true`
  - `deliverable = true`
  - `requested_bottom_mode = text_gallery_expanded`
  - `effective_bottom_mode = text_gallery_expanded`
  - `bottom_layout_mode = text_gallery_expanded`
  - `bottom_mode_override_reason = request_override_applied`
  - `title_band_region.rendered = true`
  - `gallery_strip_region.rendered = true`

#### `gallery_only`
- request id: `p2-task1-gallery-only`
- trace: `dd3ef904-af95-4eb1-acd3-ecc2dfa34c71`
- result:
  - `degraded = false`
  - `structure_complete = true`
  - `deliverable = true`
  - `requested_bottom_mode = gallery_only`
  - `effective_bottom_mode = gallery_only`
  - `bottom_layout_mode = gallery_only`
  - `bottom_mode_override_reason = request_override_applied`
  - `title_band_region.rendered = false`
  - `gallery_strip_region.rendered = true`

### Acceptance
- `text_gallery_expanded` is verifiable end-to-end in runtime ✓
- `gallery_only` is verifiable end-to-end in runtime ✓
- Stage 2 remains backend-evidence-driven ✓
- No geometry or beauty drift introduced ✓

### Tests
- `103 passed, 2 warnings`
- Command:
  - `python -m pytest tests/poster2/test_api.py tests/poster2/test_pipeline.py tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py`

---

## PR-1 — Canonical bottom mode runtime truth unification (2026-03-30)

### Goal
Eliminate `title_only` as a first-class runtime mode and unify `requested_bottom_mode` / `effective_bottom_mode` / `bottom_layout_mode` so they are coherent (bottom_layout_mode always mirrors .mode).

### Changes

#### `app/services/poster2/template_behavior.py`
- Removed `"title_only"` from `_SUPPORTED_BOTTOM_MODES`
- Removed `_LEGACY_BOTTOM_MODE_CANONICAL` (new→old semantic mapping) and `_BOTTOM_LAYOUT_MODE_BY_EFFECTIVE_MODE` (effective→layout mapping)
- Added `_BOTTOM_MODE_ALIASES = {"title_only": "text_only_expanded"}` — applied before `_validate_token`; `title_only` never enters the resolver
- Added `"title_gallery_split": 640` to `_EXPANDED_BOTTOM_SHELL_TOPS` — makes `title_gallery_split` a first-class entry (y=640) instead of deriving it from the old layout mapping
- `resolved_bottom_layout_mode = bottom_mode` — always mirrors `.mode`; no separate layout-mode concept
- Added `text_only_expanded` + `text_gallery_expanded` branches to content-policy switch (replacing `title_only`)
- Added `title_gallery_split` normalization at top of `_resolve_bottom_layout_policies()` (still delegates to `text_gallery_expanded` policy — no geometry change)
- Removed dead `title_only` branch from `_resolve_bottom_layout_policies()`
- Removed `effective_bottom_mode == "title_only"` gallery-slot check
- `mode_override_reason = "legacy_alias_canonicalized"` when alias is applied

#### `app/services/poster2/pipeline.py`
- Added `bottom_mode_alias` field to `_build_bottom_contract_review()`: shows `"title_only → text_only_expanded"` when alias is applied

#### Tests
- `test_template_behavior_resolver_supports_bottom_mode_overrides`: `.mode` and assertions updated for `text_only_expanded` alias
- `test_template_behavior_resolver_promotes_bottom_into_behavior_policy` + `test_template_behavior_resolver_limits_title_growth_when_gallery_is_dense`: `bottom_layout_mode` updated to `"title_gallery_split"` (mirrors .mode)
- `test_renderer_metadata_includes_layer_render_status`: same
- `test_frozen_baseline_modes_still_resolve_unchanged`: same
- `test_bottom_contract_review_exposes_requested_effective_and_override_reason`: effective_mode and reason_code updated for alias path
- `test_legacy_expanded_request_is_canonicalized_into_semantic_bottom_mode`: `text_gallery_expanded` is now canonical (not canonicalized into `title_gallery_split`)

### Canonical bottom mode names (frozen)
- `title_gallery_split` — default split layout (y=640)
- `text_only_expanded` — expanded text, no gallery (y=656; absorbs `title_only` alias)
- `text_gallery_expanded` — explicit expanded text with gallery (y=640)
- `gallery_only` — gallery strip only (y=728)

### Acceptance
- `title_only` accepted in API; canonicalized to `text_only_expanded` via `_BOTTOM_MODE_ALIASES` ✓
- `bottom_layout_mode` always mirrors `.mode` ✓
- `bottom_mode_alias` field shows mapping when alias is applied ✓
- `bottom_mode_override_reason = "legacy_alias_canonicalized"` for alias requests ✓
- 204/204 tests pass ✓

---

## PR-2 — Bottom mode boundary freeze and completeness rules (2026-03-30)

### Goal
Freeze per-mode required/collapsed region rules for all four canonical bottom modes so that
collapsed-by-design regions never count as missing mandatory regions, completeness evaluation is
mode-aware, and diagnostics are fully explicit.

### Changes

#### `app/services/poster2/region_matrix.py`
- Removed unused `_GALLERY_ONLY_BOTTOM_MODES` constant
- Replaced `_TITLE_BAND_ABSENT_BY_MODE = {"gallery_only"}` with a comprehensive frozen contract map:
  - `_BOTTOM_MODE_COLLAPSED_BY_DESIGN: dict[str, frozenset[str]]` — one entry per canonical mode
  - `_BOTTOM_MODE_COLLAPSE_REASON_CODES` — reason codes emitted per mode per region
- Updated `_resolve_family_a_presence()`:
  - Uses `_BOTTOM_MODE_COLLAPSED_BY_DESIGN.get(bottom_mode, frozenset())` for all mode logic
  - Unknown modes fall back conservatively (no regions excused); no silent fallback
  - Adds `collapsed_by_design: bool` and `collapse_reason_code: str | None` to each presence state
  - `gallery_strip_region` presence now carries `collapsed_by_design` + reason code for `text_only_expanded`

#### `app/services/poster2/pipeline.py`
- Import `_BOTTOM_MODE_COLLAPSED_BY_DESIGN` from `region_matrix`
- `evaluate_deliverability` `binding_inputs` now uses `resolved_behavior.bottom_policy.effective_mode`
  instead of `effective_spec.bottom_mode` (which may be `None` when the spec omits `bottom_mode`)
- `_build_bottom_contract_review()` adds `bottom_mode_region_contract` field:
  - `effective_bottom_mode` — echoes the effective canonical mode
  - `title_band_region_required` — True for all modes except `gallery_only`
  - `gallery_strip_region_required` — always False (gallery_strip is never mandatory)
  - `title_band_region_collapsed_by_mode` — True only for `gallery_only`
  - `gallery_strip_region_collapsed_by_mode` — True only for `text_only_expanded`
  - `collapsed_by_design_regions` — sorted list of regions collapsed by this mode

#### Tests (`tests/poster2/test_region_matrix.py`)
- Added import of `_BOTTOM_MODE_COLLAPSED_BY_DESIGN`
- `TestBottomModeCollapsedByDesignContract` (5 tests):
  - Contract covers all four canonical modes
  - Each mode has the correct frozen collapsed-by-design set
- `TestModeAwareRegionCompleteness` (8 tests):
  - `gallery_only`: title_band absent → not missing_mandatory, collapsed_by_design=True
  - `text_only_expanded`: gallery_strip absent → not missing_mandatory, collapsed_by_design=True
  - `title_gallery_split` + `text_gallery_expanded`: title_band absent → structure failure
  - `text_only_expanded`: title_band absent → structure failure
  - Unknown mode: conservatively requires title_band (no silent fallback)
  - `gallery_only` with title present: no regression

#### Tests (`tests/poster2/test_pipeline.py`)
- `TestBottomModeBoundaryAndCompleteness` (8 tests):
  - End-to-end verification for `gallery_only` and `text_only_expanded` collapse-by-design
  - `bottom_mode_region_contract` field verified for all four modes
  - Diagnostics completeness test: all four modes expose `requested_bottom_mode`,
    `effective_bottom_mode`, `bottom_layout_mode`, `bottom_mode_override_reason`
  - `title_only` alias path verified end-to-end with explicit diagnostic fields

### Canonical bottom mode boundary rules (frozen)

| mode | title_band_region | gallery_strip_region |
|------|-------------------|----------------------|
| `title_gallery_split` | required | optional (absent when no gallery items) |
| `text_gallery_expanded` | required | optional (absent when no gallery items) |
| `text_only_expanded` | required | **collapsed_by_design** (always absent) |
| `gallery_only` | **collapsed_by_design** (always absent) | optional (renders when items present) |

### Acceptance
- Frozen per-mode contract covers all four canonical bottom modes ✓
- `gallery_only`: `title_band_region` absence → `missing_mandatory_regions = []` ✓
- `text_only_expanded`: `gallery_strip_region` absence marked `collapsed_by_design=True` ✓
- Unknown mode: no silent fallback; conservatively requires title_band ✓
- `bottom_mode_region_contract` emitted in every `bottom_contract_review` ✓
- `evaluate_deliverability` uses resolved effective mode (not raw spec field) ✓
- `requested_bottom_mode` / `effective_bottom_mode` / `bottom_layout_mode` / override reason always present ✓
- 213/213 tests pass ✓

---

## PR-3 — Freeze product owner surfaces and dual-image geometry (2026-03-30)

### Goal
Formally freeze the 7 product owner surfaces, enforce annotation ownership rules in contract evidence,
and declare `primary_secondary_dual_v2` geometry as the final frozen geometry for dual-image mode.

### Changes

#### `app/services/poster2/template_behavior.py`
- `_PRODUCT_ANCHOR_CALLOUTS_MAX_ITEMS = 3` comment updated: explains it enforces annotation items
  within primary slot y-range (callouts 0-2 at y=250/350/450 are inside primary [188,498];
  callout 3 at y=550 would enter secondary territory and is never activated)
- `_PRODUCT_DUAL_PRIMARY_SLOT` / `_PRODUCT_DUAL_SECONDARY_SLOT` / `_PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT`
  comments updated to reflect frozen v2 status and gap measurement
- `_FROZEN_PRODUCT_OWNER_SURFACES: frozenset[str]` added — the 7 canonical product region owner surfaces
- `_PRODUCT_ANNOTATION_OWNER_SLOT = "product_primary_slot"` added — explicit constant for annotation ownership

#### `app/services/poster2/pipeline.py`
- Import expanded: `_FROZEN_PRODUCT_OWNER_SURFACES`, `_PRODUCT_ANNOTATION_OWNER_SLOT`
  from `template_behavior`
- `_build_product_annotation_contract_review()` adds 4 new fields:
  - `owner_surfaces` — sorted list of all 7 frozen owner surfaces
  - `annotation_owner_slot` — always `"product_primary_slot"`
  - `secondary_slot_annotation_ownership` — always `False`
  - `geometry_frozen` — always `True`

#### Tests (`tests/poster2/test_pipeline.py`)
- `TestProductOwnerSurfaceFreeze` (9 tests):
  - `test_owner_surfaces_constant_is_frozen`: frozenset type + exactly 7 surfaces
  - `test_annotation_owner_slot_constant`: `_PRODUCT_ANNOTATION_OWNER_SLOT == "product_primary_slot"`
  - `test_product_contract_review_lists_all_owner_surfaces`: `owner_surfaces` field covers all 7
  - `test_annotation_owner_slot_in_contract_review`: `annotation_owner_slot` in evidence
  - `test_secondary_slot_annotation_ownership_is_false`: `secondary_slot_annotation_ownership = False` in dual mode
  - `test_geometry_frozen_flag_in_contract_review`: `geometry_frozen = True`
  - `test_v2_geometry_constants_are_final`: all slot bounds match expected values; no primary/secondary overlap
  - `test_single_primary_activates_when_no_secondary_asset`: runtime freeze rule verified
  - `test_primary_secondary_dual_activates_when_secondary_asset_present`: auto-promotion + v2 geometry

#### Docs
- `docs/poster2/product_region_contract_closure_status_v1.md` — formal closure record
- `docs/poster2/README.md` — entry added pointing to closure doc

### Frozen product geometry (primary_secondary_dual_v2)

| Slot | x | y | w | h |
|---|---|---|---|---|
| `product_primary_slot` | 456 | 188 | 300 | 310 |
| `product_secondary_slot` | 456 | 506 | 300 | 202 |
| `single_primary` fallback | 456 | 188 | 300 | 520 |

Gap between primary bottom (498) and secondary top (506): 8px. No geometry adjustment required.

### Acceptance
- `_FROZEN_PRODUCT_OWNER_SURFACES` frozenset contains exactly the 7 expected surfaces ✓
- `annotation_owner_slot = "product_primary_slot"` in all contract reviews ✓
- `secondary_slot_annotation_ownership = False` even in dual mode ✓
- `geometry_frozen = True` in all contract reviews ✓
- `primary_secondary_dual_v2` geometry constants match frozen values ✓
- Single-primary / dual auto-promotion runtime behavior unchanged ✓
- 242/242 tests pass ✓

### Open follow-ups from this entry
- Pillow renderer secondary slot parity (contract-only for now; rendering exists but not fully
  contract-driven from `ResolvedProductBehavior.product_secondary_slot` bounds)
- Stage 2 frontend: `owner_surfaces` / `annotation_owner_slot` / `secondary_slot_annotation_ownership`
  / `geometry_frozen` not yet surfaced in diagnostics panel (low priority)
- `header_region` `identity_zone_mode` resolver wiring still pending

---

## PR-5 — Post-freeze text capacity optimization (2026-03-30)

### Goal
Raise char_budget floors across three target areas — title_gallery_split bottom text,
product annotation callouts, and header agent pill — to match the expanded shell
geometry and slot dimensions that were established in PRs 1–4.

### Changes

#### `app/services/poster2/template_behavior.py`

**A. `text_gallery_expanded` branch (used by `title_gallery_split` default)**

All six capacity tiers raised by 8–12 chars each:

| Case | title (before) | title (after) | subtitle (before) | subtitle (after) |
|---|---|---|---|---|
| Dense copy, subtitle, 1–2 items | 60 | 72 | 56 | 60 |
| Dense copy, subtitle, 3 items | 52 | 60 | 52 | 56 |
| Dense copy, subtitle, 4 items | 44 | 52 | 44 | 48 |
| Subtitle only (not dense) | 52 | 60 | 36 | 40 |
| Long title (>20), no subtitle | 52 | 60 | — | — |
| Compact (short title, no subtitle) | 44 | 52 | — | — |

Rationale: expanded shell starts at y=640 (384px capacity vs old y=728 = 296px).
Title slot effective width ≈ 752px at 40px bold → ~33 chars/line × 2 = 66 chars cap.
Previous 44–60 range was conservative relative to available geometry.

**B. Product annotation `char_budget`**

`{1: 36, 2: 30, 3: 24}` → `{1: 40, 2: 34, 3: 28}` in both `resolve_product_behavior`
and `resolve_feature_behavior` (`product_anchor_callouts` branch).

Rationale: label box w=144, font_size=15, max_lines=2, auto_shrink=true → ~16 chars/line
× 2 = 32 chars fits without shrink. Previous 3-item cap of 24 was significantly
under-utilizing the available label area.

**C. Header agent `agent_char_budget`**

`24` → `28` for `identity_left_agent_right` and `brand_block_two_line`.

Rationale: agent_slot w=228, font_size=15, max_lines=1, auto_shrink=true →
228/9 ≈ 25 chars without shrink. Previous cap of 24 was at the bare minimum.
28 gives modest additional capacity with a comfortable auto_shrink margin.

#### Tests (`tests/poster2/test_pipeline.py`)

New class `TestPostFreezeTextCapacity` (10 tests):

| Test | What it verifies |
|---|---|
| `test_title_gallery_split_dense_quad_title_budget_raised` | dense-quad title_gallery_split title ≥ 52, subtitle ≥ 44 |
| `test_title_gallery_split_triplet_title_budget_raised` | triplet title_gallery_split title ≥ 60, subtitle ≥ 52 |
| `test_title_gallery_split_light_gallery_title_budget_raised` | light-gallery title_gallery_split title ≥ 72, subtitle ≥ 56 |
| `test_title_gallery_split_compact_title_budget_raised` | compact title_gallery_split title ≥ 52 |
| `test_product_annotation_char_budget_raised_three_items` | 3-item annotation char_budget ≥ 28 |
| `test_product_annotation_char_budget_raised_two_items` | 2-item annotation char_budget ≥ 34 |
| `test_product_annotation_char_budget_raised_one_item` | 1-item annotation char_budget ≥ 40 |
| `test_header_agent_char_budget_raised_identity_left_agent_right` | agent_char_budget ≥ 28 for identity_left_agent_right |
| `test_header_agent_char_budget_raised_brand_block_two_line` | agent_char_budget ≥ 28 for brand_block_two_line |
| `test_header_agent_budget_truncates_longer_name_at_new_floor` | 40-char name truncated at budget floor |

### Acceptance
- `title_gallery_split` dense-quad title_char_budget ≥ 52 (was 44) ✓
- `title_gallery_split` light-gallery title_char_budget ≥ 72 (was 60) ✓
- Product annotation 3-item char_budget ≥ 28 (was 24) ✓
- Header agent char_budget ≥ 28 (was 24) ✓
- No contract changes; no mode changes; no geometry changes ✓
- 262/262 tests pass (252 prior + 10 new) ✓

---



### Goal
Freeze text layer owner surfaces and feature delegation as declarative constants.
Eliminate inlined `owner_region` string literals. Enforce no-dual-ownership when annotation active.

### Changes

#### `app/services/poster2/template_behavior.py`
- `_TEXT_LAYER_OWNER_MAP` — maps `header_text_layer / title_text_layer / subtitle_text_layer` to their canonical `owner_region`
- `_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS` — tuple of exactly 3 slot IDs (`product_annotation_slot_1/2/3`)
- `_PRODUCT_ANNOTATION_TEXT_OWNER_REGION = "product_region"` — owner for all annotation slot text

#### `app/services/poster2/pipeline.py`
- Imports expanded: `_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS`, `_PRODUCT_ANNOTATION_TEXT_OWNER_REGION`, `_TEXT_LAYER_OWNER_MAP`
- Dead code removed: older no-`template` copies of `_build_title/subtitle/header_text_layer_evidence`
- `_build_title_text_layer_evidence()`: `owner_region` from constant; `ownership_frozen = True` added
- `_build_subtitle_text_layer_evidence()`: same
- `_build_header_text_layer_evidence()`: same
- `_build_feature_contract_review()`: `feature_view_mode = "delegated_diagnostic"` when annotation active, `"owner"` otherwise
- `_build_product_annotation_contract_review()`: `annotation_text_owner_region`, `annotation_slot_ids`, `ownership_frozen = True` added

#### Tests (`tests/poster2/test_pipeline.py`)
- `TestTextOwnershipFreeze` (10 tests):
  - `test_text_layer_owner_map_constant_shape`
  - `test_frozen_annotation_slot_ids_constant`
  - `test_product_annotation_text_owner_region_constant`
  - `test_title_text_layer_ownership_frozen`
  - `test_subtitle_text_layer_ownership_frozen`
  - `test_header_text_layer_ownership_frozen`
  - `test_feature_view_mode_is_delegated_diagnostic_when_annotation_active`
  - `test_feature_view_mode_is_owner_when_annotation_not_active`
  - `test_no_dual_ownership_when_annotation_active`
  - `test_annotation_contract_review_emits_frozen_slot_ids`

#### Docs
- `docs/poster2/text_layer_contract_closure_status_v1.md` — formal closure record
- `docs/poster2/README.md` — entry added pointing to closure doc; current phase updated

### Acceptance
- `_TEXT_LAYER_OWNER_MAP` declared with 3 entries ✓
- `_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS` is tuple of 3 IDs ✓
- `_PRODUCT_ANNOTATION_TEXT_OWNER_REGION = "product_region"` ✓
- All three text layers emit `ownership_frozen = True` ✓
- `feature_view_mode = "delegated_diagnostic"` when annotation active ✓
- `feature_region.visible_item_count = 0` when annotation active (no dual ownership) ✓
- `product_annotation_contract_review` emits `annotation_text_owner_region`, `annotation_slot_ids`, `ownership_frozen` ✓
- Dead code removed ✓
- 252/252 tests pass ✓

---

## Task-1 — Bottom Mode Stabilization: text_gallery_expanded + gallery_only (2026-03-30)

**Status:** Complete

### Goal

Bring `text_gallery_expanded` and `gallery_only` to the same health bar as `text_only_expanded`:
`degraded=false`, `structure_complete=true`, `deliverable=true`, all four diagnostic fields present.

### Root causes fixed

#### A. gallery_only gallery_shell_top geometry (`template_behavior.py`)
- `gallery_shell_top` was hardcoded to `888` when gallery renders without a title band
- Gallery items placed at y≈898–962; bottom shell CSS declared `top: 728px; height: ~84px` — mismatch
- Fix: `gallery_shell_top = title_band_top` (= `bottom_shell_top` = 728); items now at y≈738–802

#### B. title_slot always required in slot contracts (`slot_contracts.py`)
- `title_slot` was unconditionally `required=True`; `gallery_only` without title → `structure_complete=false`
- Added `_BOTTOM_MODE_EXCUSED_REQUIRED_SLOTS = {"gallery_only": frozenset({"title_slot"})}`
- `evaluate_slot_bindings` excuses `title_slot` when `binding_inputs["bottom_mode"] == "gallery_only"`

#### C. Preflight guard required title unconditionally (`quality_guard.py`)
- `run_preflight_guard` raised `QualityGuardError` for any `gallery_only` request without title
- Fix: mode-aware check using `spec.bottom_mode or template.behavior_modes.bottom_mode`

#### D. Title normalization guard unconditional (`pipeline.py`)
- `_normalize_contract_text_spec` raised `ValueError` for empty title unconditionally
- Fix: same mode-aware check; `template` now passed as optional parameter from call site

### text_gallery_expanded
No structural fixes needed. Already healthy when title is provided. Eight pipeline tests confirm.

### Tests (`TestBottomModeStabilization`, 8 new tests)
- `gallery_only` deliverable without title ✓
- `gallery_only` title_slot not in missing_required ✓
- `gallery_only` all 4 diagnostic fields present ✓
- `gallery_only` gallery_shell_top == bottom_shell_top ✓
- `gallery_only` gallery items within shell bounds ✓
- `text_gallery_expanded` deliverable with title + no gallery ✓
- `text_gallery_expanded` deliverable with title + 4 gallery items ✓
- `text_gallery_expanded` all 4 diagnostic fields present ✓

### Acceptance
- `gallery_only` without title: `degraded=False, structure_complete=True, deliverable=True` ✓
- `gallery_shell_top == bottom_shell_top` (728) for gallery_only ✓
- `text_gallery_expanded` deliverable with or without gallery items ✓
- All 4 diagnostic fields present for both modes ✓
- 270/270 tests pass (262 prior + 8 new) ✓

### Docs
- `docs/poster2/bottom_mode_stabilization_status_v1.md` — detailed root-cause and closure record

### 2026-03-30 revalidation — text_gallery_expanded only
- Narrow-scope recheck performed after user-reported failure limited to `text_gallery_expanded`
- Required fixed reads attempted before task:
  - `CLAUDE.md`
  - `docs/poster2/current_branch_execution_log_v1.md`
  - `project_poster2_baseline_2026-03-30.md` (file missing in repo; no extra doc expansion)
- Backend path rechecked only for:
  - resolver
  - quality_guard
  - renderer
  - deliverability
- Focused pipeline gate:
  - `python -m pytest tests/poster2/test_pipeline.py -q -k 'text_gallery_expanded and (deliverable or diagnostics or region_contract or full_health or bottom_mode)'`
  - result: `4 passed`
- Fresh local HTTP runtime proof:
  - trace: `266f4c50-f0ba-491f-b0d2-3e6cbf8db559`
  - `degraded=false`
  - `structure_complete=true`
  - `deliverable=true`
  - `requested_bottom_mode=text_gallery_expanded`
  - `effective_bottom_mode=text_gallery_expanded`
  - `bottom_layout_mode=text_gallery_expanded`
  - `bottom_mode_override_reason=request_override_applied`
- Fresh live runtime proof:
  - trace: `afdd09bc-b5dd-4550-982f-addee2d46310`
  - `degraded=false`
  - `structure_complete=true`
  - `deliverable=true`
  - `requested_bottom_mode=text_gallery_expanded`
  - `effective_bottom_mode=text_gallery_expanded`
  - `bottom_layout_mode=text_gallery_expanded`
  - `bottom_mode_override_reason=request_override_applied`
- Conclusion:
  - `text_gallery_expanded` is healthy in both local request-path and current live runtime
  - no silent fallback reproduced
  - no code change required in this revalidation slice

---

## Task-2 — Product Region Final Geometry Decision (2026-03-31)

**Status:** Complete

### Goal

Make one final product-region geometry decision from the healthy `primary_secondary_dual_v2` baseline.
Enlarge product_region outer shell, increase primary/secondary gap, enlarge secondary card area.

### Step A: Lane model decision

**Decision: External right lane** (frozen)

Annotation label boxes are at x=784+, outside the product_region right boundary at x=756.
Image-slot sizing is fully independent of label_bounds. No annotation coordinate changes required.

### Step B: Geometry changes

| Slot | Before | After |
|---|---|---|
| `product_region` outer shell | `{x:456, y:188, w:300, h:520}` | `{x:456, y:188, w:300, h:540}` |
| `product_primary_slot` | `{x:456, y:188, w:300, h:310}` | **unchanged** |
| `product_secondary_slot` | `{x:456, y:506, w:300, h:202}` | `{x:456, y:518, w:300, h:210}` |
| `_PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT` | `h:520` | `h:540` |
| gap (primary bottom → secondary top) | 8px | 20px |

Internal consistency: 310 + 20 + 210 = 540 ✓

### Ownership unchanged

- `annotation_owner_slot = product_primary_slot` ✓
- `secondary_slot_annotation_ownership = False` ✓
- `geometry_frozen = True` ✓
- Annotation callout anchors (y=250/350/450) still within primary [188,498] ✓

### Files changed

- `template_behavior.py`: secondary slot constants, single_primary fallback h, both hero modes `product_region_h`
- `template_dual_v2.json`: `product_slot.h` 520→540, version 2.1.3→2.1.4
- `slot_spec.template_dual_v2.json`: all product-region h entries 520→540
- `template_registry.py`: `template_version` 2.1.3→2.1.4
- `tests/poster2/test_pipeline.py`: geometry assertions updated; `TestTask2FinalProductGeometry` added (8 tests)
- `tests/poster2/test_contracts.py`: version assertion updated
- `tests/poster2/test_region_matrix.py`: product_region.h assertion updated

### Tests

- `TestTask2FinalProductGeometry`: 8 new tests, all pass
- Scoped regression: 148/148 pass
  - `tests/poster2/test_pipeline.py`
  - `tests/poster2/test_contracts.py`
  - `tests/poster2/test_region_matrix.py`
  - `tests/poster2/test_slot_contracts.py`

### Docs

- `docs/poster2/product_region_final_geometry_status_v1.md` — formal closure record

---

## PR-7 — Product image contract: bounds and fit authoritative from product_policy (2026-03-31)

### Goal

Close the split where `hero_policy` was the authority for product region bounds in two places,
and the image fit policy was scattered in renderer branches instead of declared in the product contract.

### Root causes

Three distinct contract gaps, same root cause:

| Location | Old (wrong) | New (correct) |
|---|---|---|
| `_build_product_annotation_contract_review()` | `hero_policy.layout_metrics["product_region_*"]` | `product_policy.layout_metrics["product_region_*"]` |
| `_product_image_slot()` single_primary path | bounds from `hero_policy.layout_metrics` | bounds from `product_policy.product_primary_slot` |
| renderer fit policy | `hero_policy.product_fit` hardcoded in renderer branches | `product_policy.product_primary_image_fit` declared in resolver |

### Changes

#### `app/services/poster2/template_behavior.py`
- `product_primary_image_fit: str` added to `ResolvedProductBehavior` dataclass
- Set from `hero_policy.product_fit` in `resolve_product_behavior()`
- Included in `as_dict()`

#### `app/services/poster2/renderer.py`
- `_product_image_slot()` restructured:
  - When `product_policy` present: always uses `product_policy.product_primary_slot` for bounds and `product_policy.product_primary_image_fit` for fit
  - Dual mode: reads from product_policy (unchanged behavior)
  - Single_primary: now reads bounds from product_policy (was hero_policy.layout_metrics — same values, correct authority)
  - No-product_policy fallback: unchanged (legacy hero-only path)

#### `app/services/poster2/pipeline.py`
- `_build_product_annotation_contract_review()`: `product_region.bounds` now from `product_policy.layout_metrics` (was `hero_policy.layout_metrics`)
- `_build_product_contract_review()`: `product_primary_image_fit` added as root-level field

#### Tests (`tests/poster2/test_pipeline.py`)
- `TestProductImageContract` (5 tests):
  - `test_resolve_product_behavior_declares_product_primary_image_fit`
  - `test_product_primary_image_fit_present_in_product_contract_review`
  - `test_annotation_contract_review_product_region_bounds_from_product_policy`
  - `test_product_primary_slot_bounds_match_single_primary_constant`
  - `test_product_primary_image_fit_consistent_with_hero_fit_for_both_hero_modes`

### Acceptance
- `product_policy.product_primary_image_fit == hero_policy.product_fit` (= `"contain"`) ✓
- `product_contract_review["product_primary_image_fit"] == "contain"` ✓
- `product_annotation_contract_review.product_region.bounds` now match `product_policy.layout_metrics` on the clean merge path ✓
- `_product_image_slot()` single_primary uses `product_policy.product_primary_slot` bounds ✓
- No geometry changes; no annotation slot changes; no text budget changes ✓
- Focused validation clean on the merge path ✓

---

## PR-8A — Safe product-geometry widening baseline with frozen bottom and annotation/text lane (2026-03-31)

### State read before coding

- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `project_poster2_baseline_2026-03-30.md` — missing in this workspace; recorded explicitly and did not block the PR

### Goal

Widen only the product geometry contract surfaces while keeping bottom, annotation ownership,
annotation lane, and non-product region behavior frozen.

This is an accepted intermediate product-geometry PR, not a final product-region closeout.

### Contract truth changed

| Surface | Before | After |
|---|---|---|
| `product_region` | `{x:456, y:188, w:300, h:540}` | `{x:456, y:188, w:320, h:540}` |
| `product_primary_slot` | `{x:456, y:188, w:300, h:310}` | `{x:456, y:188, w:320, h:310}` |
| `product_secondary_slot` | `{x:456, y:518, w:300, h:210}` | `{x:456, y:518, w:320, h:210}` |
| `_PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT` | `{x:456, y:188, w:300, h:540}` | `{x:456, y:188, w:320, h:540}` |
| template version | `2.1.4` | `2.1.5` |

Anchor derivation:
- Left anchor: `scenario_region_right(384) + gap(72) = 456`
- Right anchor: `annotation_shell_x(784) - gutter(8) = 776`
- Width: `776 - 456 = 320`

### What remained frozen

- `bottom_shell_top` unchanged
- `title_band_region` unchanged
- `gallery_strip_region` unchanged
- annotation ownership unchanged: `annotation_owner_slot = product_primary_slot`
- annotation lane unchanged: label boxes still start at `x=784`, leaving an 8px gutter from product right edge `x=776`
- annotation shell computation unchanged
- no text budget tuning, no header/scenario work, no beautification

### Files changed

- `app/services/poster2/template_behavior.py`
- `app/services/poster2/template_registry.py`
- `app/templates/specs/template_dual_v2.json`
- `app/templates_html/slot_spec.template_dual_v2.json`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_contracts.py`

### Focused tests run

- `.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TestProductLayoutContract or TestProductOwnerSurfaceFreeze or TestTask2FinalProductGeometry or TestProductImageContract'` → `29 passed`
- `.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'product and not header and not scenario and not bottom'` → `1 passed`
- `.venv/bin/python -m pytest -q tests/poster2/test_contracts.py -k 'TestTemplateSpecLoading'` → `12 passed`

### Next PR

- `PR-8B` only: annotation/text contract
- scope: annotation shell, anchors, connectors, markers, label bounds, text placement mode
- keep bottom frozen
- keep the widened product geometry as the new baseline

---

## PR-8B redo — Annotation/text runtime contract under product_policy (2026-03-31)

### State read before coding

- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `project_poster2_baseline_2026-03-30.md` — missing in this workspace; recorded explicitly and did not block the PR

### Goal

Redo PR-8B so annotation/text behavior is actual product-owned runtime contract, not
evidence surfacing only.

### Old path removed

- active annotation runtime no longer uses the old `feature_policy` / template `feature_callouts`
  path as placement truth when `product_annotation_mode == product_anchor_callouts`
- structured HTML annotation markup no longer defaults connector behavior to
  `feature_policy.connector_policy` for the active product-annotation path

### Contract fields that became runtime truth

- `product_policy.annotation_items[*].anchor_x`
- `product_policy.annotation_items[*].anchor_y`
- `product_policy.annotation_items[*].anchor_radius`
- `product_policy.annotation_items[*].leader_color`
- `product_policy.annotation_items[*].leader_width`
- `product_policy.annotation_items[*].label_bounds`
- `product_policy.annotation_items[*].connector_policy`
- `product_policy.annotation_items[*].marker_policy`
- `product_policy.annotation_items[*].text_placement_mode`
- `product_policy.annotation_text_placement_mode`
- `product_annotation_contract_review.annotation_shell.bounds`
- `product_annotation_contract_review.behavior_policy.{connector_policy, marker_policy, shell_policy, bounds_policy, text_placement_mode, char_budget, line_clamp}`

### Runtime behavior now aligned

- Pillow annotation rendering reads anchors and label bounds from `product_policy.annotation_items`
- structured HTML annotation rendering reads anchors and label bounds from `product_policy.annotation_items`
- active connector markup follows per-slot contract policy
- Stage2 diagnostics continue to reflect backend truth only

### Explicit verification

- no active annotation text placement path still reads placement inputs from `feature_policy`
- no active annotation placement path depends on `template_spec_fixed` except for the explicit
  active mode `template_label_box_fixed`
- product image sizing path remains isolated from annotation text bounds

### What remained frozen

- no product geometry changes beyond accepted PR-8A baseline
- no bottom changes
- no header/scenario changes
- no beautification
- no broad tuning

### Files changed

- `app/services/poster2/renderer.py`
- `tests/poster2/test_renderer.py`

### Focused tests run

- `.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'product_annotation or feature_markup_prefers_product_annotation_runtime_truth or template_behavior_resolver_supports_product_annotation_mode'` → `4 passed`
- `.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TestTextOwnershipFreeze or product_annotation or TestProductImageContract'` → `19 passed`
- `.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py -k 'annotation or docs_publish_mirror'` → `3 passed`

### Next

- merge gate only: broader validation before merge
- do not reopen product geometry, bottom, header/scenario, or beautification from PR-8B

---

## Gate-unblock PR — Glibatree OpenAI import compatibility (2026-03-31)

### State read before coding

- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `project_poster2_baseline_2026-03-30.md` — missing in this workspace; recorded explicitly and did not block the task

### Goal

Unblock the non-PR-8B merge gate failure in `tests/test_glibatree_openai.py` without
touching poster2 or reopening PR-8B.

### Investigation result

- `_request_glibatree_openai_edit` had been removed from `app/services/glibatree.py`
- `tests/test_glibatree_openai.py` still imports that symbol directly
- after restoring the symbol, the same test file still used an obsolete `GlibatreeConfig(client=...)`
  constructor that no longer matches the current config dataclass

### Smallest backward-compatible fix chosen

- restore `_request_glibatree_openai_edit` as a compatibility shim
- update the test to use the current `GlibatreeConfig` public shape instead of restoring the removed `client` config field

### Files changed

- `app/services/glibatree.py`
- `tests/test_glibatree_openai.py`

### Validation

- `.venv/bin/python -m pytest -q tests/test_glibatree_openai.py` → `2 passed`
- `.venv/bin/python -m pytest -q --collect-only tests/test_glibatree_openai.py` → `2 tests collected`

### Next

- merge this gate-unblock PR first
- then return to `fix/pr8b-annotation-text-contract`, rebase onto new `main`, rerun merge gate, and merge PR-8B only if full suite passes

---

## Gate-unblock PR — Full-suite follow-up test/runtime compatibility (2026-03-31)

### State read before coding

- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `project_poster2_baseline_2026-03-30.md` — missing in this workspace; recorded explicitly and did not block the task

### Goal

Unblock the remaining non-PR-8B full-suite failures revealed after the first gate-unblock PR,
without touching poster2 or reopening PR-8B.

### Investigation result

- `prepare_poster_assets()` still referenced legacy `GlibatreeConfig.use_openai_client`, but the property was missing from the current config dataclass
- several tests still expected forbidden inline base64 asset inputs to validate
- one schema test still expected `GeneratePosterResponse.results == []` while current default is `None`
- `tests/test_template_posters.py` was missing local test scaffolding (`base64` import, `fake_r2_storage` fixture) and still called current helpers with outdated parameters/assertions
- invalid template image bytes were bubbling into a 500 instead of producing the structured `INVALID_IMAGE` 400 detail path

### Files changed

- `app/config.py`
- `app/services/template_variants.py`
- `tests/test_poster_services.py`
- `tests/test_schemas.py`
- `tests/test_template_posters.py`

### Validation

- `.venv/bin/python -m pytest -q tests/test_poster_services.py tests/test_schemas.py tests/test_template_posters.py` → `21 passed`
- `.venv/bin/python -m pytest -q` → `319 passed`

### Next

- merge this full-suite gate-unblock PR first
- then return to `fix/pr8b-annotation-text-contract`, rebase onto new `main`, rerun merge gate, and merge PR-8B only if the full suite still passes

---

## PR-8B merge gate final rerun — PASSED (2026-03-31)

### State read before merge gate

- `README.md`
- `docs/poster2/README.md`
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `project_poster2_baseline_2026-03-30.md` — missing in this workspace; recorded explicitly and did not block the gate

### Gate run

- `.venv/bin/python -m pytest -q`

### Result

- `324 passed, 10 warnings, 3 subtests passed`

### Scope assessment

- PR-8B code path remained limited to product annotation contract work
- gate now passes after the separate non-PR-8B gate-unblock merges landed on `main`
- PR-8B is eligible to merge

---

## PR-9A — Product region contract upgrade: full product-content container baseline (2026-04-01)

### State read before coding

- `AGENTS.md`
- `CLAUDE.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/template_dual_v2_architecture_business_definition.md`

### Goal

Upgrade `product_region` from a narrow image-shell interpretation into a product-owned full
product-content container, without changing geometry values and without reopening annotation/text
mode work.

### Old path removed

- `geometry_evidence.region_bounds.product_region` no longer reads `hero_policy.layout_metrics`
- Pillow product shell runtime no longer reads `hero_policy.layout_metrics` for `product_region`
- formal HTML contract no longer describes `product_image_layer` as anchored only to the older
  `product_card_shell_layer`

### Contract/runtime truth added

- `ResolvedProductBehavior.product_region`
- `ResolvedProductBehavior.product_canvas_shell`
- `ResolvedProductBehavior.product_content_container`
- `ResolvedProductBehavior.product_content_container_policy = "full_product_region_container"`
- `product_contract_review.product_content_container`
- `product_contract_review.behavior_policy.product_content_container_policy`
- formal HTML contract layers:
  - `product_canvas_shell_layer`
  - `product_content_container_layer`

### Runtime alignment

- `product_region` bounds are now product-owned runtime truth in pipeline geometry evidence
- Pillow product shell uses product-owned `product_region` bounds
- product shell, content container, primary slot, and secondary slot remain aligned under
  `product_policy`
- no product geometry values changed in this PR

### What remained frozen

- PR-8A product geometry values
- bottom
- header/scenario
- beautification
- annotation shell / anchors / connectors / markers / label bounds / text placement mode

### Files changed

- `app/services/poster2/template_behavior.py`
- `app/services/poster2/pipeline.py`
- `app/services/poster2/renderer.py`
- `app/templates_html/template_dual_v2.html`
- `app/templates_html/slot_spec.template_dual_v2.json`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_contracts.py`

### Focused tests run

- `.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TestProductLayoutContract or TestProductImageContract or TestProductOwnerSurfaceFreeze'` → `18 passed`
- `.venv/bin/python -m pytest -q tests/poster2/test_contracts.py -k 'TemplateSpecLoading'` → `12 passed`
- `.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'single_product_focus_hero_mode_skips_scenario_render or primary_secondary_dual_renders_secondary_product_slot_in_pillow'` → `2 passed`
- `.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py tests/poster2/test_renderer.py tests/poster2/test_contracts.py -k 'product and not bottom and not header and not scenario and not annotation and not text'` → `24 passed`

### README update

- not needed; formal doc path did not change

### Next

- PR-9B only: move product annotation/text mode deeper onto the upgraded `product_region`
  container path
- do not reopen bottom, header/scenario, beautification, or geometry values from PR-9A
