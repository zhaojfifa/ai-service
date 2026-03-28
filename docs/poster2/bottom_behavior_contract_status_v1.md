# bottom behavior contract status v1

## 1. Task Objective

Promote bottom from early behavior into stable behavior so that bottom peer rebalance, count-driven gallery distribution, and mixed text-image layout response are contract-driven rather than fixed-layout driven.

Current round objective:

- keep bottom contract and behavior stable
- close out the remaining designer-first coordination problems in `2 / 3` gallery cases
- improve pair / triplet mixed-content layout without leaving the contract-first path
- add the smallest shell/text refinement needed so bottom no longer feels like a residual full-width strip

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
- fixed read state remained limited to the three startup anchors above

Blocked note:

- `AGENTS.md` requires the top-level baseline `docs/poster2/poster_generation_product_design_baseline_v1.md`
- this file is now present as a tracked root-level file in the current worktree
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

In the current closeout round, the most visible remaining issue was narrower:

- protocol already worked
- but pair / triplet bottom layouts still felt too compressed or too mechanically even
- title band growth, gallery strip shift, and gallery sizing still lacked enough policy granularity to produce more natural designer-first mixed-content balance
- gallery shell still visually read too much like a leftover strip container even when item sizing improved

## 4. Root Cause

The root cause was split semantic ownership:

- resolver owned part of title/subtitle behavior
- renderer still owned gallery strip geometry through fixed slot math / fixed slot-spec usage
- resolver still contained hard-coded text-slot coordinate branches for several bottom states
- metadata exposed count and collapse, but not enough layout-response evidence to explain who yielded first under dense text-image cases

So bottom was only partially declarative: contract and visibility were explicit, but peer layout response was still partly renderer-shaped.

For the current round, the root cause was that some policy buckets were still too coarse:

- pair and triplet gallery cases reused overly similar strip sizing logic
- title-band growth policy was implicit in sizing mode, not explicit enough for review
- gallery shift / aspect / spacing decisions were resolved numerically, but not named as protocol-level behavior
- minimal shell framing and text emphasis were still inherited from generic bottom styling instead of reacting to bottom behavior

## 5. Changed Files

Current stable behavior is implemented in:

- `frontend/app.js`
- `docs/app.js`
- `app/services/poster2/template_behavior.py`
- `app/services/poster2/pipeline.py`
- `tests/poster2/test_renderer.py`
- `tests/poster2/test_pipeline.py`
- `tests/test_stage2_guard_diagnostics_surface.py`
- `docs/poster2/bottom_behavior_contract_status_v1.md`

## 6. Behavior Policies Introduced Or Completed

Bottom now includes explicit behavior policy for:

- `title_band_sizing_mode`
  - `compact`
  - `standard`
  - `expanded`
  - `collapsed`
- `title_band_growth_policy`
  - `grow_title_band_for_support_copy_priority`
  - `temper_growth_for_triplet_gallery_balance`
  - `hold_growth_under_dense_quad_pressure`
  - `hold_standard_title_band_with_balanced_gallery`
  - `keep_compact_title_band_for_light_copy`
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
- `bottom_peer_balance_policy`
  - `copy_priority_with_spacious_gallery`
  - `triplet_gallery_and_copy_co_balance`
  - `quad_gallery_priority_over_copy_growth`
  - `balanced_bottom_regions`
  - `gallery_only_bottom_rebalance`
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
- `gallery_strip_shift_policy`
  - `single_gallery_centered_shift`
  - `downshift_for_spacious_pair`
  - `balanced_triplet_shift`
  - `tight_quad_shift`
- `gallery_aspect_policy`
  - `single_gallery_focus_aspect`
  - `spacious_pair_aspect`
  - `balanced_triplet_aspect`
  - `compact_quad_aspect`
  - `single_packshot_aspect`
- `gallery_spacing_policy`
  - `centered_single_spacing`
  - `relaxed_pair_spacing`
  - `balanced_triplet_spacing`
  - `compact_quad_spacing`
  - `supporting_pair_spacing`
- `gallery_shell_frame_policy`
  - `single_showcase_frame`
  - `pair_showcase_frame`
  - `triplet_balanced_frame`
  - `quad_strip_frame`
- `bottom_text_emphasis_policy`
  - `copy_priority_strong_title`
  - `balanced_triplet_text_emphasis`
  - `compact_quad_text_emphasis`
  - `balanced_bottom_text_emphasis`
  - `gallery_only_neutral_text`

The resolver now emits:

- `gallery_item_layouts`
- dynamic `gallery_shell_top`
- dynamic `gallery_shell_height`
- dynamic `gallery_shell_x`
- dynamic `gallery_shell_w`
- dynamic `gallery_shell_radius`
- dynamic `gallery_items_top`
- dynamic `gallery_items_height`
- dynamic `gallery_item_radius`
- derived title / subtitle slot bounds without fixed per-mode coordinate branches

In this round, pair / triplet gallery distribution was further tuned so that:

- `2` items are no longer treated like a narrower strip remainder
- `3` items get their own balanced triplet behavior instead of inheriting over-compressed quad logic
- `balanced_pair` now resolves to `item_width = 280`, `item_height = 80`, `gap = 16`, `gallery_shell_height = 100`
- title-band growth now explains whether copy priority, triplet co-balance, or quad restraint won the decision
- copy-priority pair layouts now allow `title_char_budget = 36` when title is clamped to one line under dense subtitle pressure
- pair / triplet gallery shell framing now narrows around the actual composition instead of always reading as a full-width strip
- title / subtitle emphasis now varies minimally by resolved bottom text policy rather than staying visually identical across pressure states

So both Pillow and Puppeteer consume the same bottom peer-layout result for `1 / 2 / 3 / 4` visible items.

## 7. Metadata / Evidence Additions

`template_behavior.bottom_policy` and `bottom_contract_review.behavior_policy` now expose:

- `title_band_sizing_mode`
- `title_band_growth_policy`
- `subtitle_overflow_policy`
- `content_priority_policy`
- `peer_balance_policy`
- `bottom_peer_balance_policy`
- `gallery_distribution_policy`
- `gallery_shell_frame_policy`
- `gallery_strip_shift_policy`
- `gallery_aspect_policy`
- `gallery_spacing_policy`
- `bottom_text_emphasis_policy`
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

Current text evidence now also exposes:

- `requested_title_text`
- `requested_subtitle_text`
- `sanitized_title_text`
- `sanitized_subtitle_text`
- `rendered_title_excerpt`
- `rendered_subtitle_excerpt`
- `title_truncation_applied`
- `subtitle_truncation_applied`
- `title_source`
- `subtitle_source`

This round also introduced the smallest design optimization layer that still stays inside the behavior contract:

- pair gallery cards are allowed to become wider / taller
- triplet gallery cards are allowed to stay more balanced and less cramped
- strip shift is now an explicit policy rather than a hidden numeric consequence
- gallery shell frame can narrow and round differently for single / pair / triplet / quad states
- title letter-spacing and subtitle opacity can vary minimally by resolved bottom text policy

## 8. Validation Steps And Observed Results

Executed:

```bash
./.venv/bin/python -m pytest tests/poster2/test_renderer.py tests/poster2/test_pipeline.py
./.venv/bin/python -m pytest tests/poster2/test_api.py tests/poster2/test_contracts.py tests/poster2/test_renderer.py tests/poster2/test_pipeline.py tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py
```

Observed result:

- `145 passed, 2 warnings in 12.33s`

Validated coverage includes:

- gallery distribution for `1 / 2 / 3 / 4`
- dense subtitle with light gallery allowing title growth
- pair gallery widening / height increase under copy-priority behavior (`280x80`, shell height `100`)
- triplet gallery balancing under dense mixed-content behavior
- dense subtitle with quad gallery constraining title growth
- dynamic strip height / item height / peer gap response under varying gallery density
- dynamic gallery shell framing / radius response
- minimal bottom text emphasis response
- `gallery_only + supporting_packshots`
- metadata / evidence exposing resolved gallery slot bounds
- Stage2 diagnostics still surfacing:
  - `template_behavior`
  - `geometry_evidence`
  - `bottom_contract_review`

## 9. Remaining Risks

- gallery distribution is resolver-driven but still rule-based rather than measurement-optimized
- `supporting_packshots` has minimum distribution semantics, not a richer primary/secondary hierarchy yet
- this round improves pair / triplet naturalness, but does not yet make bottom a measurement-driven art direction engine
- minimal text emphasis is intentionally conservative and not a full typography system

## 10. Next Recommended Step

Freeze bottom as the first SOP baseline of poster2 and move new implementation work to Phase 3 region replication:

1. `header_region`
2. `scenario_region` / `product_region`
3. `feature_region`

Bottom stays in maintenance mode only:

- contract bugs
- request / normalization bugs
- resolver / renderer parity bugs
- evidence / diagnostics bugs
- narrow policy tuning that preserves the frozen structure and schema

## 11. Strategy Sentence

Strategy: make bottom behavior explicit and verifiable first; allow beautification only after behavior is stable under input variation.

## 12. Required Inputs

Bottom SOP is executed from these required operator inputs:

- `title`
- `subtitle`
- `bottom_mode`
- `gallery_mode`
- `gallery_count`
- `gallery_images`
- `auto_fill_gallery`

Stage 2 preview and backend request must resolve from the same bottom request state. Empty optional subtitle is allowed and must stay empty through request build and backend normalization.

## 13. Effective Policies

Bottom execution is considered SOP-complete only when the following are resolver-derived and visible in metadata:

- `title_band_sizing_mode`
- `title_band_growth_policy`
- `subtitle_overflow_policy`
- `content_priority_policy`
- `peer_balance_policy`
- `bottom_peer_balance_policy`
- `gallery_distribution_policy`
- `gallery_shell_frame_policy`
- `gallery_strip_shift_policy`
- `gallery_aspect_policy`
- `gallery_spacing_policy`
- `bottom_text_emphasis_policy`

## 14. Operator Review Checklist

For each bottom validation run, operator review must confirm:

- request preview shows the exact requested title / subtitle, not a fallback-contaminated value
- `bottom_contract_review` exposes requested / sanitized / rendered text chain
- `title_source` and `subtitle_source` identify request-field provenance
- `title_truncation_applied` and `subtitle_truncation_applied` match the rendered excerpts
- `subtitle_slot` state matches the effective subtitle text
- gallery slot states and `visible_item_count` match the chosen `gallery_mode` and input count
- `geometry_evidence` remains resolver-derived for `title_slot`, `subtitle_slot`, and `gallery_strip_region`

## 15. Acceptance Criteria

A bottom run is accepted only if:

- requested / effective / rendered text values are all inspectable
- subtitle is not polluted by title or any Stage 1 fallback field once operator input exists
- title / subtitle slot state is consistent with sanitized text and bottom mode
- renderer consumes the same sanitized text that evidence reports
- Stage 2 preview path and final generation path agree on request values
- no CSS-only workaround is needed to explain the final result

## 16. Failure Patterns

Known failure patterns that should be treated as contract regressions:

- empty subtitle in Stage 2 preview becomes non-empty in request payload
- `requested_subtitle_text` differs from operator-cleared subtitle without explicit operator action
- `rendered_subtitle_excerpt` contains text while `subtitle_slot.rendered` is false
- truncation flags disagree with rendered excerpts
- `docs/app.js` drifts from `frontend/app.js`, causing Stage 2 preview and published operator review to diverge

## 17. Baseline Freeze Confirmation

Bottom is now frozen as the first SOP baseline of poster2.

Frozen baseline means the following are fixed and should be treated as compatibility surfaces:

- `bottom_region`
- `title_band_region`
- `gallery_strip_region`
- `bottom_contract_review`
- `geometry_evidence`
- semantic text evidence fields
- diagnostics panel field names and operator review path

Allowed future changes:

- policy tuning only
- bug fixes that preserve structure
- bug fixes that preserve evidence schema
- bug fixes that preserve diagnostics field names
- renderer parity fixes

Disallowed future changes without a new architecture decision:

- bottom structure changes
- bottom evidence schema changes
- diagnostics field-name changes
- ad hoc CSS-only behavior fixes
- using beautification to mask contract or control failures

## 18. Remaining Bottom Bug List

Bottom is baseline-frozen, but the following issues remain tracked as bugs rather than as architecture work:

1. Pair / triplet / quad distribution is still rule-based rather than measurement-optimized.
2. `supporting_packshots` still uses minimum viable semantics rather than richer primary/secondary hierarchy logic.
3. Minimal text emphasis remains intentionally conservative and is not a full typography system.
4. Preview/evidence presentation can still be improved, but only by exposing existing frozen fields more clearly, not by changing the contract.

## 19. Phase 3 Implementation Order

Phase 3 should replicate the bottom SOP pattern to the remaining regions in this order:

1. `header_region`
   - complete contract-first resolver coverage first
   - preserve diagnostics / evidence parity from the start
2. `scenario_region` and `product_region`
   - treat them as the next peer-layout / mixed-asset control step
   - preserve shell/content separation and renderer-as-execution-layer stance
3. `feature_region`
   - apply the same request -> normalize -> resolver -> renderer -> evidence -> operator review loop

Phase 3 should reuse the bottom SOP pattern:

- request state must be inspectable
- normalization must be explicit
- resolver output must be the template truth-source
- renderer must consume resolved behavior
- evidence must explain requested / effective / rendered state
- operator review must be possible before and after generation
