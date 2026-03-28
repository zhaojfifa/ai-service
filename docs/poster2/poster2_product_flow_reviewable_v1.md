# poster2 product flow reviewable v1

## 1. Purpose

This document records the closure of the minimum poster2 operator loop:
Stage 1 intake → Stage 2 contract review → Stage 3 email send.

The goal is contract-driven, controllable-first closure — not feature richness.
This is a status record, not a new architecture.

## 2. Startup Context Used

- `CLAUDE.md`
- `AGENTS.md`
- `docs/poster2/README.md`
- `docs/poster2/bottom_behavior_contract_status_v1.md`

## 3. Scope Interpretation

Product scope as reviewed:

### Stage 1
- Asset + brief intake with fixed inputs only
- Features: 3 fixed input fields (no dynamic add/remove)
- No complex dynamic controls

### Stage 2 — Poster Contract Console
- UI reflects backend contract payload
- Shows requested / effective / rendered / evidence per region
- No drag-and-drop, no frontend layout recomputation, no free-form editor behavior
- Resolver Layout panel is a read-only review surface driven by backend data

### Stage 3
- Email draft + send foundation
- Basic architecture only — no complex campaign automation

## 4. Implementation Order Executed

1. Backend region contract alignment (Phase 3 PR-1 through PR-3) — already complete
2. Stage 2 live payload binding (PR-4) — completed in this round
3. Stage 1 request pack organization — existing baseline is adequate; no changes needed
4. Stage 3 email draft + send — existing foundation is adequate; no changes needed
5. Refinement deferred

## 5. Changed Files (PR-4)

- `frontend/app.js`
  - Added `setJson` calls for `header_contract_review`, `hero_contract_review`, `feature_contract_review`
  - All three are now written to hidden diagnostic elements on each generation response
- `frontend/stage2.html`
  - Added 3 hidden `<pre>` diagnostic elements: `poster2-header-contract-review`, `poster2-hero-contract-review`, `poster2-feature-contract-review`
  - Added builder functions: `buildHeaderDetail`, `buildHeroDetail`, `buildFeatureDetail`
  - Extended `tryRebuild` to parse all three new contract reviews
  - Extended `renderResolverLayout` signature and routing to show detail for all 5 regions
  - Added `slotStatusHtml` and `textRow` helpers for consistent evidence display
- `docs/app.js` — synced from `frontend/app.js`
- `docs/stage2.html` — synced from `frontend/stage2.html`

## 6. Stage 1 Progress

Stage 1 (`frontend/index.html`) is in baseline-adequate state:
- Asset intake (brand logo, scenario image, product image, gallery images) is functional
- Brief intake (brand name, agent name, features × 3, title, subtitle) is functional
- Features are fixed to 3 input fields per scope
- No dynamic add/remove
- No changes made in this round

## 7. Stage 2 Progress

**PR-4 complete: Stage 2 live contract panel integration.**

Resolver Layout panel now surfaces backend contract payload for all 5 regions:

| Region | Detail shown |
|---|---|
| `header_region` | mode, brand/agent requested → rendered chain, slot states (logo, brand, agent) |
| `scenario_region` | hero_mode, scenario source, safe_preset_fill flag, slot state |
| `product_region` | hero_mode, product source, slot state |
| `feature_region` | feature_mode, per-item requested → rendered text chain |
| `bottom_region` | bottom_mode, title_band + gallery_strip sub-regions (existing) |

All region rows in the Resolver Layout now show:
- Mode chip from `templateBehavior` or contract review (whichever resolves)
- Collapsed detail section with contract evidence
- Rendered/collapsed/not-rendered status from `region_render_status`

Stage 2 remains a read-only review surface. It does not recompute layout logic.

## 8. Stage 3 Progress

Stage 3 (`frontend/stage3.html`) has email draft + send foundation:
- Poster URL / key display from Stage 2 output
- Recipient, subject, body fields
- Send Email button
- No changes made in this round — foundation is adequate for the reviewed scope

## 9. Known Bugs Kept Out of Scope

From `bottom_behavior_contract_status_v1.md` §18:
- Pair/triplet/quad gallery distribution is rule-based, not measurement-optimized
- `supporting_packshots` uses minimum viable semantics
- Minimal text emphasis is not a full typography system

Additional:
- Preview-path / generation-path parity (Puppeteer vs Pillow) not yet closed
- Beautification layer not started — downstream of behavior stability confirmation

## 10. Next Recommendation

With the minimum operator loop now closed:

1. **Validation run**: generate a poster against the live backend, verify all 5 region detail cards populate in the Resolver Layout, confirm requested/rendered text chains are correct
2. **Stage 2 contract panel acceptance**: operator review checklist per `bottom_behavior_contract_status_v1.md` §14 — confirm behavior_policy, evidence, and slot states are inspectable for all regions
3. After acceptance: move to beautification layer planning per `docs/poster2/beautification_layer_plan_v1.md`

## 11. Architecture Stance Preserved

- Backend remains truth-source; Stage 2 does not recompute or invent bounds
- Contract-first order maintained: Structure → Control → Beautification
- Shell/content separation intact
- Renderer is execution layer, not template truth-source
- `frontend/` and `docs/` are in sync
