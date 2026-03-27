# bottom behavior contract status v1

## 1. Task Objective

Promote bottom peer layout from partial structural / budget control into contract-driven behavior so that:

- `bottom_region`
  - `title_band_region`
  - `gallery_strip_region`

continues to preserve ownership and collapse semantics, while also recomputing:

- gallery strip distribution under `1 / 2 / 3 / 4` visible items
- title band growth behavior
- peer balance between title band and gallery strip
- subtitle overflow behavior

without falling back to CSS-only tuning or renderer-defined semantics.

## 2. Startup Context Used

- Root anchor: `AGENTS.md`
- Root repo rules: `README.md`
- Poster2 anchor: `docs/poster2/README.md`
- Required task doc: `docs/poster2/template_behavior_layer_plan_v1.md`
- Additional doc read only because startup was blocked by a missing top-level baseline file on this synced branch:
  - `docs/poster2/01_architecture/template_dual_v2_architecture_business_definition.md`

## 3. Exact Problem Reproduced

Before this round, bottom behavior already handled:

- `bottom_mode`
- `gallery_mode`
- subtitle ownership
- gallery visible-count / collapse semantics

But bottom still behaved like a mostly fixed layout:

- subtitle length could change slot render state and line budget
- gallery count could change visible count
- yet gallery strip item distribution still remained fixed-slot driven
- title band growth and gallery strip density were not solved together

As a result, bottom updated ownership / count / collapse, but did not fully recompute peer layout response.

## 4. Root Cause

The root cause was split responsibility:

- resolver owned early title/subtitle budget behavior
- renderer still owned gallery strip geometry by fixed slot math / slot-spec consumption
- metadata exposed count and collapse, but not the resolved gallery distribution or per-slot bounds

This left bottom in a half-declarative state: structure and visibility were explainable, but peer layout response was not.

## 5. Changed Files

- `app/services/poster2/template_behavior.py`
- `app/services/poster2/renderer.py`
- `app/services/poster2/pipeline.py`
- `tests/poster2/test_renderer.py`
- `tests/poster2/test_pipeline.py`

## 6. Behavior Policies Introduced Or Completed

Bottom behavior now includes explicit peer-layout policy, not only budget / collapse policy.

Completed or added:

- `title_band_sizing_mode`
  - `compact`
  - `standard`
  - `expanded`
  - `collapsed`
- `subtitle_overflow_policy`
  - `single_line_ellipsis_inside_title_band`
  - `single_line_ellipsis_inside_split_title_band`
  - `two_line_clamp_inside_title_band`
  - `two_line_clamp_inside_split_title_band`
  - `subtitle_collapsed`
  - `suppressed_with_title_band`
- `peer_balance_policy`
  - `title_growth_allowed_with_light_gallery`
  - `balanced_dense_copy_with_triplet_gallery`
  - `gallery_priority_under_dense_quad`
  - `balanced_title_band_and_gallery_strip`
  - `title_band_only`
  - `gallery_strip_only`
- `gallery_distribution_policy`
  - `single_center_focus`
  - `balanced_pair`
  - `balanced_triplet`
  - `dense_quad`
  - `single_packshot_focus`
  - `supporting_pair`
  - `supporting_triplet`

The resolver now emits `gallery_item_layouts` so that both Pillow and Puppeteer consume the same distribution result under `1 / 2 / 3 / 4` visible items.

## 7. Metadata / Evidence Additions

`template_behavior.bottom_policy` and `bottom_contract_review.behavior_policy` now expose:

- `gallery_distribution_policy`
- `gallery_item_layouts`
- `title_band_sizing_mode`
- `subtitle_overflow_policy`
- `peer_balance_policy`
- effective line clamps and budgets

`bottom_contract_review.gallery_slots` now exposes:

- `distribution_policy`
- `bounds`
- `local_bounds`

`geometry_evidence.slot_bounds.gallery_slot` now reflects the resolved first visible gallery-item bounds instead of a fixed 4-up default slot.

This makes the operator-facing evidence sufficient to explain how bottom responded to input variation.

## 8. Validation Steps And Observed Results

Executed:

```bash
/Users/tylerzhao/Code/ai-service/.venv/bin/python -m pytest tests/poster2/test_api.py tests/poster2/test_contracts.py tests/poster2/test_renderer.py tests/poster2/test_pipeline.py tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py
```

Observed result:

- `140 passed, 2 warnings in 12.45s`

Validated cases include:

- gallery strip distribution under `1 / 2 / 3 / 4` items
- dense subtitle with light gallery allowing title growth
- dense subtitle with quad gallery limiting title growth
- `gallery_only + supporting_packshots`
- metadata / evidence exposing resolved gallery-slot bounds
- Stage2 diagnostics surface still exposing `template_behavior`, `geometry_evidence`, and `bottom_contract_review`

## 9. Remaining Risks

- Gallery distribution is now resolver-driven, but still rule-based rather than text-measured / image-measured optimization.
- `supporting_packshots` now has minimum count-driven distribution semantics, but not a richer primary/secondary packshot hierarchy yet.
- Stage2 validation currently proves the page-side path via diagnostics visibility rather than a separate pixel-parity preview engine.

## 10. Next Recommended Step

Continue bottom behavior closure by making Stage2 preview consume the same resolved bottom layout semantics directly, instead of relying only on metadata inspection for operator review.

## 11. Strategy Sentence

Strategy: first make bottom behavior contract-explicit and verifiable, then allow beautification only after behavior becomes stable under input variation.
