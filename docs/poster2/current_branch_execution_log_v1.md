# Current Branch Execution Log v1

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

## Entry — PR-7B5: Bottom Copy-Capacity And Vertical-Allocation Micro-Closure

**Branch:** `main`
**Status:** In progress
**Last updated:** 2026-04-04

### Scope
- `title_gallery_split`: keep stable two-line subtitle clamp and extend dense-quad excerpt capacity
- `text_only_expanded`: keep non-truncation and full-width parity; rebalance subtitle-present vertical allocation upward

### Engineering truth
- `title_gallery_split` dense-quad branch:
  - `subtitle_char_budget`: `56 -> 72`
  - `title_band_height`: `168 -> 184`
  - `title_stack_gap`: `6 -> 4`
  - keeps `subtitle_line_clamp = 2`
  - keeps quad gallery distribution unchanged
- `text_only_expanded` subtitle-present cases:
  - `title_content_pad_top`: `20 -> 24`
  - `title_content_pad_bottom`: `16 -> 24`
  - lower anchoring remains active
  - budgets and line clamps unchanged


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
