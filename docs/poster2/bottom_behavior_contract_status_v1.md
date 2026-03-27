# bottom behavior contract status v1

## 1. Task Objective

Promote bottom from early behavior into stable behavior so that bottom peer rebalance, count-driven gallery distribution, and mixed text-image layout response are contract-driven rather than fixed-layout driven.

This status is scoped to preserving:

- `bottom_region`
  - `title_band_region`
  - `gallery_strip_region`
- `bottom_mode`
- `gallery_mode`
- subtitle ownership in `title_band_region`
- gallery count / collapse semantics

while completing:

- title band growth behavior
- subtitle overflow behavior
- peer balance between title band and gallery strip
- `1 / 2 / 3 / 4` gallery item distribution
- content preservation priority under mixed text-image pressure
- metadata / evidence that explains the result

## 2. Startup Context Used

- Root anchor: `AGENTS.md`
- Poster2 anchor: `docs/poster2/README.md`
- Task doc: `docs/poster2/template_behavior_layer_plan_v1.md`

Blocked note:

- `AGENTS.md` requires the top-level baseline `docs/poster2/poster_generation_product_design_baseline_v1.md`
- this file is referenced by the local doc system but is not present as a tracked root-level file in the current worktree
- no additional doc was expanded in this run; the task proceeded against the required three startup anchors only

## 3. Exact Problem Reproduced

The original bottom contract already handled:

- region ownership
- `bottom_mode`
- `gallery_mode`
- visible count
- collapse state
- subtitle ownership

But bottom still behaved like a mostly fixed layout:

- subtitle length could change budget / line behavior
- gallery count could change visibility
- yet gallery strip distribution still depended on fixed slot assumptions
- title and subtitle slot metrics still had hard-coded positional branches
- title band growth and gallery density were not solved together as one bottom behavior policy

This meant bottom was explainable at the structure level, but not fully explainable at the peer-layout response level.

## 4. Root Cause

The root cause was split semantic ownership:

- resolver owned part of title/subtitle behavior
- renderer still owned gallery strip geometry through fixed slot math / fixed slot-spec usage
- resolver still contained hard-coded text-slot coordinate branches for several bottom states
- metadata exposed count and collapse, but not enough layout-response evidence to explain who yielded first under dense text-image cases

So bottom was only partially declarative: contract and visibility were explicit, but peer layout response was still partly renderer-shaped.

## 5. Changed Files

Current stable behavior is implemented in:

- `app/services/poster2/template_behavior.py`
- `app/services/poster2/pipeline.py`
- `tests/poster2/test_renderer.py`
- `tests/poster2/test_pipeline.py`
- `docs/poster2/bottom_behavior_contract_status_v1.md`

## 6. Behavior Policies Introduced Or Completed

Bottom now includes explicit behavior policy for:

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
- `content_priority_policy`
  - `gallery_priority_without_title_band`
  - `title_and_subtitle_priority_without_gallery`
  - `title_and_subtitle_priority_over_gallery_density`
  - `balanced_text_and_gallery_priority`
  - `gallery_count_priority_with_text_compaction`
  - `title_priority_with_gallery_support`
  - `gallery_support_with_compact_title`

The resolver now emits:

- `gallery_item_layouts`
- dynamic `gallery_shell_top`
- dynamic `gallery_shell_height`
- dynamic `gallery_items_top`
- dynamic `gallery_items_height`
- derived title / subtitle slot bounds without fixed per-mode coordinate branches

So both Pillow and Puppeteer consume the same bottom peer-layout result for `1 / 2 / 3 / 4` visible items.

## 7. Metadata / Evidence Additions

`template_behavior.bottom_policy` and `bottom_contract_review.behavior_policy` now expose:

- `title_band_sizing_mode`
- `subtitle_overflow_policy`
- `content_priority_policy`
- `peer_balance_policy`
- `gallery_distribution_policy`
- effective line clamps
- effective budgets
- dynamic shell / item geometry metrics
- `gallery_item_layouts`

`bottom_contract_review.gallery_slots` now exposes:

- `distribution_policy`
- `bounds`
- `local_bounds`

`geometry_evidence.slot_bounds.gallery_slot` now reflects resolved visible gallery-item geometry instead of only a fixed four-up slot assumption.

`geometry_evidence.slot_bounds.title_slot` and `geometry_evidence.slot_bounds.subtitle_slot` now reflect resolver-derived slot bounds rather than hard-coded branch positions.

This makes bottom output operator-reviewable under input variation.

## 8. Validation Steps And Observed Results

Executed:

```bash
./.venv/bin/python -m pytest tests/poster2/test_api.py tests/poster2/test_contracts.py tests/poster2/test_renderer.py tests/poster2/test_pipeline.py tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py
```

Observed result:

- `140 passed, 2 warnings in 10.93s`

Validated coverage includes:

- gallery distribution for `1 / 2 / 3 / 4`
- dense subtitle with light gallery allowing title growth
- dense subtitle with quad gallery constraining title growth
- dynamic strip height / item height / peer gap response under varying gallery density
- `gallery_only + supporting_packshots`
- metadata / evidence exposing resolved gallery slot bounds
- Stage2 diagnostics still surfacing:
  - `template_behavior`
  - `geometry_evidence`
  - `bottom_contract_review`

## 9. Remaining Risks

- gallery distribution is resolver-driven but still rule-based rather than measurement-optimized
- `supporting_packshots` has minimum distribution semantics, not a richer primary/secondary hierarchy yet
- the local doc system still references a top-level product baseline file that is not present as a tracked root-level file in this worktree

## 10. Next Recommended Step

Keep bottom behavior stable and move the next increment to preview-path parity: make Stage2 preview consume the same resolved bottom layout semantics directly, rather than depending mainly on diagnostics inspection.

## 11. Strategy Sentence

Strategy: make bottom behavior explicit and verifiable first; allow beautification only after behavior is stable under input variation.
