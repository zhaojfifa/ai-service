# Current Branch Execution Log v1

**Branch:** `PosterSop06-beautification-phase1`
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
- Beautification layer planning (after structural closeout is confirmed stable in live generation)

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
