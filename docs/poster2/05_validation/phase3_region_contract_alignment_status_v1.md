# phase 3 region contract alignment status v1

## 1. Task Objective

Start Phase 3 from the frozen bottom SOP baseline and replicate the same contract-first, resolver-driven, evidence-backed pattern to the remaining regions.

Phase 3 scope starts on the backend:

1. `header_region`
2. `scenario_region` and `product_region`
3. `feature_region`
4. Stage2 backend-driven contract panel integration

## 2. Startup Context Used

- Root anchor: `AGENTS.md`
- Poster2 anchor: `docs/poster2/README.md`
- Bottom freeze anchor: `docs/poster2/bottom_behavior_contract_status_v1.md`
- fixed read state remained limited to the three startup anchors above

## 3. Baseline Assumption

Bottom is frozen as the first SOP baseline of poster2 under tag:

- `poster2-bottom-sop-baseline-v1`

Bottom freeze means:

- `bottom_region`
- `title_band_region`
- `gallery_strip_region`
- bottom resolver output fields
- `bottom_contract_review`
- `geometry_evidence`
- diagnostics panel compatibility

remain stable while Phase 3 starts elsewhere.

## 4. Execution Order

Phase 3 executes in this order:

1. `header_region`
   - move fully to resolver-driven behavior and evidence
   - make requested / effective / rendered chain inspectable
   - complete `region_render_status` and slot evidence
2. `scenario_region` and `product_region`
   - eliminate fixed-layout residue
   - keep geometry evidence resolver-derived
   - keep renderer as execution layer only
3. `feature_region`
   - align resolver, evidence, and diagnostics with the bottom SOP pattern
4. Stage2 integration
   - wire the page to live backend payload only
   - do not recompute layout logic on the frontend

## 5. Phase 3 Guardrails

Phase 3 must preserve:

- the existing five-region structure
- shell/content separation
- contract-first architecture
- renderer as execution layer, not template truth-source
- bottom frozen schema and diagnostics compatibility

Phase 3 must not:

- redesign Family A
- expand beautification as the main task
- use CSS-only behavior fixes
- let Stage2 invent bounds or policy names

## 6. Current Progress

Current status after `PR-3`:

- PR-0 complete: bottom frozen as SOP baseline
- tag created: `poster2-bottom-sop-baseline-v1`
- working branch: `PosterSop04-region-contract-alignment`
- PR-1 complete: `header_region` is now aligned to the backend contract loop
  - request / normalize / resolver / renderer / evidence chain is inspectable
  - `header_contract_review` is emitted in renderer metadata and API payload
  - requested / sanitized / rendered brand and agent values are visible
  - header geometry evidence is resolver-derived rather than fixed-slot-only
- PR-2 complete: `scenario_region` and `product_region` are now aligned to the backend contract loop
  - `hero_contract_review` is emitted in renderer metadata and API payload
  - requested / effective / rendered asset-source chain is visible for scenario/product
  - scenario/product geometry evidence is resolver-derived rather than template-static-only
  - renderer consumes resolver-derived scenario/product slot geometry and fit/anchor policy
- PR-3 complete: `feature_region` is now aligned to the backend contract loop
  - `feature_contract_review` is emitted in renderer metadata and API payload
  - requested / sanitized / rendered feature text chain is visible
  - feature truncation/collapse state is inspectable per feature slot
  - feature behavior policy now exposes explicit text budget policy and char budget
- Phase 3 backend implementation is now complete across `header`, `scenario/product`, and `feature`
- Stage2 live contract panel integration not started yet in this record

## 7. Next Recommended PR

`PR-4: Stage2 backend-driven contract panel integration`

Acceptance target:

- render live backend contract payload instead of mock/static region diagnostics
- surface behavior modes, requested/effective/rendered chains, region cards, slot cards, and evidence directly from payload
- keep Stage2 as UI shell only, without inventing bounds or policy names
