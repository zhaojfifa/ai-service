# Current Branch Execution Log v1

**Branch:** `PosterSop06-beautification-phase1`
**Last updated:** 2026-03-29

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

