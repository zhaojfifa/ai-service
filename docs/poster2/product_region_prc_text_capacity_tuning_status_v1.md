# PR-C — Text Capacity / Label Bounds / Clamp / Connector Tuning Status v1

**Branch:** `claude/festive-heisenberg`
**Status:** Complete
**Date:** 2026-04-02

---

## 1. Scope

PR-C tunes product-owned annotation readability on top of the PR-4 geometry baseline.

In scope:
- Increase annotation label box height from 60 → 76 for active slots 1-3
- Increase line clamp from 2 → 3 for product_anchor_callouts (CSS + Pillow renderer)
- Expand `_PRODUCT_TEXT_SHELL_H` from 260 → 276 (tracks slot_3 bottom at y=416+h=76=492; 492−216=276)
- Raise char_budget floor: `{1:40, 2:34, 3:28}` → `{1:44, 2:38, 3:32}`
- Update `line_clamp` contract field: 2 → 3 for product_anchor_callouts annotation mode
- Update `text_budget_policy` label: `fixed_3_anchor_two_line_budget` → `fixed_3_anchor_three_line_budget`
- Update `truncation_policy` label: `two_line_clamp` → `three_line_clamp` for product_anchor_callouts feature behavior
- Update tests to reflect new h=276 text_shell bounds

Not in scope for PR-C:
- `product_region` outer shell — unchanged: `{x:456, y:188, w:472, h:540}`
- `product_canvas_shell_layer` — unchanged: `{x:456, y:188, w:300, h:540}`
- Slot 4 label_box (anchor_y=550) — excluded by max_items=3; left at h=60 to keep region_bottom stable for HTML repositioning path
- Bottom / header / scenario — unchanged
- beautification — unchanged
- `feature_region` delegation — unchanged (remains delegated diagnostic)
- PR-4 slot geometry — unchanged

---

## 2. Before / After Label Box Table

| Surface | x | y | w | h (before) | h (after) | max_lines (before) | max_lines (after) |
|---|---|---|---|---|---|---|---|
| slot_1 label_box | 784 | 216 | 144 | **60** | **76** | 2 | **3** |
| slot_2 label_box | 784 | 316 | 144 | **60** | **76** | 2 | **3** |
| slot_3 label_box | 784 | 416 | 144 | **60** | **76** | 2 | **3** |
| slot_4 label_box (excluded) | 784 | 516 | 144 | 60 | **unchanged** | 2 | **unchanged** |

### Gap analysis after change

| Pair | Gap (before h=60) | Gap (after h=76) |
|---|---|---|
| slot_1 bottom → slot_2 top | 40px (276→316) | 24px (292→316) |
| slot_2 bottom → slot_3 top | 40px (376→416) | 24px (392→416) |

24px gap is clear visual separation.  The old 40px gap was unused vertical slack.

### Text shell bounds update

| Constant | Before | After | Derivation |
|---|---|---|---|
| `_PRODUCT_TEXT_SHELL_H` | 260 | **276** | slot_3_bottom (416+76=492) − slot_1_top (216) = 276 |
| text_shell bottom edge | 476 | **492** | 216 + 276 = 492 |

Both are within `product_region` bottom (188+540=728) ✓

### Char budget update

| Item count | Before | After |
|---|---|---|
| 1 | 40 | **44** |
| 2 | 34 | **38** |
| 3 | 28 | **32** |

---

## 3. Design Rationale

**3-line clamp**: w=144 at font_size=15 (Poster2Feature / Noto Sans SC) fits ~16-18 chars per line in CJK mode.  With 2-line clamp, max visible content ≈ 32-36 chars; 3-line clamp raises that to ~48-54 chars.  This directly reduces truncation for medium-length feature callout copy.

**Label box h 60→76**: Vertical padding at 8px top + 8px bottom = 16px.  3 lines at line_height=1.3 × font_size=15 ≈ 58.5px rendered height + 16px padding = 74.5px → rounded to 76px.  This ensures 3 lines render without overflow within the box bounds.

**Gap reduction 40→24px**: The 40px inter-slot gap was larger than the padding inside the box.  Reducing to 24px is still a clear visual break while recovering 16px per slot for content.

**Char budget**: Raised to match the physical capacity of the label box (w=144, 2-3 lines at font_size=15).  The char_budget field is a contract/diagnostic signal — actual rendering is controlled by CSS line-clamp and Pillow max_lines.  Raising the budget closes the gap between the declared budget and actual box capacity.

**Slot 4 unchanged**: anchor_y=550 is excluded by `_PRODUCT_ANCHOR_CALLOUTS_MAX_ITEMS=3`.  Leaving slot_4 label_box at h=60 preserves the `region_bottom` calculation in the HTML repositioning path (`_resolve_feature_callout_map`), preventing unintended y-position drift for regular count_driven_callout_stack mode.

---

## 4. Files Changed

1. `app/templates/specs/template_dual_v2.json`
   - Slots 1-3: `label_box.h` 60 → 76
   - Slots 1-3: `label_box.max_lines` 2 → 3

2. `app/templates_html/template_dual_v2.css`
   - Add `.product-annotation-mode-product_anchor_callouts .feature-callout { -webkit-line-clamp: 3; line-clamp: 3; min-height: 76px; }` after the feature-mode-4 rule block

3. `app/services/poster2/renderer.py`
   - `_resolve_feature_callout_layout`: `max_lines=2` → `max_lines=3` in the `template_anchor_fixed` branch (product_anchor_callouts Pillow path)

4. `app/services/poster2/template_behavior.py`
   - `_PRODUCT_TEXT_SHELL_H`: 260 → 276
   - Comment update: `h=276: bottom_of_slot_3 (y=416+h=76=492) − top_of_slot_1 (y=216) = 276`
   - `char_budget` dict in `resolve_product_behavior`: `{1:40, 2:34, 3:28}` → `{1:44, 2:38, 3:32}`
   - `anchor_char_budgets` in `resolve_feature_behavior`: same update
   - `line_clamp = 3` for `product_anchor_callouts` branch in `resolve_product_behavior`
   - `text_budget_policy = "fixed_3_anchor_three_line_budget"` (was `two_line_budget`)
   - `truncation_policy = "three_line_clamp"` (was `two_line_clamp`) in `resolve_feature_behavior`
   - `line_clamp=3` in `ResolvedFeatureBehavior` return for product_anchor_callouts

5. `tests/poster2/test_pipeline.py`
   - `TestProductGeometryPR4Rebalance.test_text_shell_bounds_unaffected`: h 260 → 276 (PR-C updates this)
   - `TestProductTextShellContract.test_product_text_shell_constants_geometry`: h 260 → 276
   - `TestProductTextShellContract.test_product_text_shell_bounds_in_layout_metrics`: h 260 → 276
   - `TestProductTextShellContract.test_product_text_shell_layer_in_product_contract_review`: bounds h 260 → 276
   - Add `TestProductTextCapacityPRC` class (8 tests)

---

## 5. Frozen Unchanged

- `product_region` outer shell: `{x:456, y:188, w:472, h:540}`
- `product_canvas_shell_layer`: `{x:456, y:188, w:300, h:540}`
- `product_primary_slot`: `{x:456, y:188, w:300, h:360}`
- `product_secondary_slot`: `{x:456, y:564, w:300, h:144}`
- `_PRODUCT_TEXT_SHELL_X`, `_PRODUCT_TEXT_SHELL_Y`, `_PRODUCT_TEXT_SHELL_W`: unchanged (784, 216, 144)
- `_PRODUCT_ANCHOR_CALLOUTS_MAX_ITEMS = 3`: unchanged
- `_FROZEN_PRODUCT_OWNER_SURFACES`: unchanged
- Connector anchor_x=764, anchor_y positions (250/350/450): unchanged
- Slot 4 label_box (excluded): unchanged
- Bottom / header / scenario: unchanged
- `feature_region` delegation: unchanged

---

## 6. Before / After Text-Capacity Evidence

### Before (PR-4 baseline)
- label_box: `w=144, h=60, max_lines=2`
- CSS: `-webkit-line-clamp: 2`
- Pillow: `max_lines=2` in `_resolve_feature_callout_layout`
- char_budget at 3 items: 28
- line_clamp (contract): 2
- Effective capacity: ≈ 2 lines × ~16 CJK chars/line = ~32 chars before clamp; budget: 28
- Truncation: any callout text > 28 chars or 2 lines is clipped

### After (PR-C)
- label_box: `w=144, h=76, max_lines=3`
- CSS: `-webkit-line-clamp: 3` for product_anchor_callouts mode
- Pillow: `max_lines=3` in `_resolve_feature_callout_layout`
- char_budget at 3 items: 32
- line_clamp (contract): 3
- Effective capacity: ≈ 3 lines × ~16 CJK chars/line = ~48 chars before clamp; budget: 32
- Truncation: callouts up to 32 chars (contract) / 48 chars (physical box) survive intact

### Improvement summary
| Metric | Before | After | Change |
|---|---|---|---|
| line capacity | 2 | 3 | +50% |
| char_budget (3 items) | 28 | 32 | +14% |
| label_box h | 60px | 76px | +27% |
| text_shell_h | 260px | 276px | +6% |
| inter-slot gap | 40px | 24px | −16px (recovered) |

---

## 7. Acceptance Evidence

- `_PRODUCT_TEXT_SHELL_H == 276` ✓
- `text_shell_bottom = 216 + 276 = 492 < product_region_bottom (728)` ✓
- `text_shell_right = 784 + 144 = 928 = product_region_right (456+472=928)` ✓
- `text_shell_x (784) > canvas_right (456+300=756)` ✓ no-compete unchanged
- Slot gaps: slot_1 bottom (292) < slot_2 top (316); slot_2 bottom (392) < slot_3 top (416) ✓
- CSS: `.product-annotation-mode-product_anchor_callouts .feature-callout { -webkit-line-clamp: 3 }` ✓
- Pillow: `max_lines=3` for template_anchor_fixed ✓
- `char_budget == 32` at 3 items ✓
- `line_clamp == 3` for product_anchor annotation mode ✓
- `python3 -m pytest -q tests/poster2/test_pipeline.py` → **138 passed**
- `python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py` → **109 passed**

---

## 8. Risks / Follow-up

- HTML repositioning path (`_resolve_feature_callout_map`) recomputes y positions from `region_top/region_bottom` using `box_h` from `feature_policy` — for product_anchor_callouts with `box_h=72`, slots are repositioned to [288, 360, 432] rather than the template-spec fixed positions. This is pre-existing behavior; PR-C does not change it.
- Slot 4 kept at h=60 intentionally to preserve `region_bottom=576` for the HTML path. If slot 4 is ever made live (max_items raised to 4), this constraint should be re-evaluated.
- 3-line CSS clamp is scoped to `.product-annotation-mode-product_anchor_callouts` only; regular count_driven / uniform_callout modes retain 2-line clamp.
