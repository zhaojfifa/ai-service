# PR-4 — Product Geometry Rebalance Status v1

**Branch:** `claude/festive-heisenberg`
**Status:** Complete
**Date:** 2026-04-02

---

## 1. Scope

PR-4 rebalances product-side slot geometry under the existing contract-first path.

In scope:
- Increase `product_primary_slot` height from 310 → 360 (stronger visual weight)
- Reduce inter-slot gap from 20 → 16 (tight but clear)
- Reduce `product_secondary_slot` height from 210 → 144 so its bottom leaves 20px breathing room above `product_region` bottom
- Update `_PRODUCT_DUAL_SECONDARY_SLOT` y from 518 → 564 (follows primary growth + gap)
- Update constant block comment and `_PRODUCT_ANCHOR_CALLOUTS_MAX_ITEMS` comment
- Update renderer.py stale comment
- Update/add tests to reflect new geometry

Not in scope for PR-4:
- `product_region` outer shell — unchanged: `{x:456, y:188, w:472, h:540}`
- `product_canvas_shell_layer` — unchanged: `{x:456, y:188, w:300, h:540}`
- `product_text_shell_layer` — unchanged: `{x:784, y:216, w:144, h:260}`
- Annotation connector / marker / label bounds — unchanged
- No char_budget or line_clamp tuning
- No CSS / HTML structural changes
- No Stage2 / UI changes
- No feature_region ownership changes
- No bottom / header / scenario work
- No beautification

---

## 2. Before / After Geometry Table

| Surface | x | y | w | h | bottom edge | note |
|---|---|---|---|---|---|---|
| `product_region` | 456 | 188 | 472 | 540 | 728 | **unchanged** |
| `product_canvas_shell_layer` | 456 | 188 | 300 | 540 | 728 | **unchanged** |
| `product_primary_slot` (before) | 456 | 188 | 300 | **310** | **498** | PR-8B baseline |
| `product_primary_slot` (**PR-4**) | 456 | 188 | 300 | **360** | **548** | +50px, 67% of 540 |
| inter-slot gap (before) | — | 498 | — | **20** | **518** | |
| inter-slot gap (**PR-4**) | — | 548 | — | **16** | **564** | |
| `product_secondary_slot` (before) | 456 | **518** | 300 | **210** | **728** | bottom-stuck |
| `product_secondary_slot` (**PR-4**) | 456 | **564** | 300 | **144** | **708** | 20px breathing room |
| bottom breathing room (**PR-4**) | — | 708 | — | **20** | 728 | new — explicit gap |
| `product_text_shell_layer` | 784 | 216 | 144 | 260 | 476 | **unchanged** |

### Arithmetic check
```
primary_h + gap + secondary_h + bottom_breathing = canvas_h
360       + 16  + 144         + 20               = 540 ✓
```

Primary share: 360/540 = 66.7% (was 57.4%)
Secondary share: 144/540 = 26.7% (was 38.9%)
Bottom breathing: 20px (was 0px)

---

## 3. Design Rationale

**Primary visual weight**: raising primary from h=310 to h=360 increases the image surface by 50px vertically. The primary product now occupies two-thirds of the canvas height rather than slightly more than half. The change is meaningful without overshadowing the secondary.

**Secondary raised from bottom**: the previous secondary extended to y=728 = product_region bottom = canvas_shell bottom. Zero breathing room made the secondary appear glued to the floor. With h=144 and y=564, the secondary bottom is at y=708 — 20px clear of the product region edge. The secondary is visually floating rather than bottom-stuck.

**Gap reduction**: 20→16px is imperceptible at render scale but recovers 4px for the secondary slot. Both gaps (inter-slot and bottom breathing) are now 16/20, creating a clear rhythm without adding complexity.

**Annotation anchor coverage**: The 3 active annotation anchors (anchor_y 250, 350, 450) all fall within the new primary range [188, 548]. Callout 4 (anchor_y 550) remains correctly excluded — it now falls in the gap zone [548, 564] rather than secondary territory, but the exclusion logic (`_PRODUCT_ANCHOR_CALLOUTS_MAX_ITEMS = 3`) is unaffected.

**Text shell independence**: `product_text_shell_layer` is in the right lane (x=784) and is unaffected by canvas-side slot changes.

---

## 4. Files Changed

1. `app/services/poster2/template_behavior.py`
   - `_PRODUCT_DUAL_PRIMARY_SLOT` h: 310 → 360
   - `_PRODUCT_DUAL_SECONDARY_SLOT` y: 518 → 564, h: 210 → 144
   - Update constant block comment (gap, primary range)
   - Update `_PRODUCT_ANCHOR_CALLOUTS_MAX_ITEMS` comment (primary range now [188,548])

2. `app/services/poster2/renderer.py`
   - Update stale comment on `_product_slot()` (h:310 → h:360)

3. `tests/poster2/test_pipeline.py`
   - Update existing tests with old exact geometry values
   - Add new `TestProductGeometryPR4Rebalance` class

---

## 5. Frozen Unchanged

- `product_region` outer shell: `{x:456, y:188, w:472, h:540}`
- `product_canvas_shell_layer`: `{x:456, y:188, w:300, h:540}`
- `product_single_primary_slot`: `{x:456, y:188, w:300, h:540}`
- `product_text_shell_layer`: `{x:784, y:216, w:144, h:260}`
- `_PRODUCT_REGION_OUTER_W`, `_PRODUCT_CANVAS_SHELL_W`, `_PRODUCT_TEXT_SHELL_*` — all unchanged
- `_PRODUCT_ANCHOR_CALLOUTS_MAX_ITEMS = 3` — unchanged (value only; comment updated)
- Annotation lane / connector / marker / label bounds — unchanged
- `feature_region` delegation — unchanged
- CSS / HTML / Stage2 / UI — unchanged
- Bottom / header / scenario — unchanged

---

## 6. Acceptance Evidence

- `product_primary_slot h == 360` (up from 310) ✓
- `product_secondary_slot y == 564`, `h == 144` (raised from bottom) ✓
- `secondary_bottom = 564 + 144 = 708`; `product_region_bottom - secondary_bottom = 728 - 708 = 20px breathing room` ✓
- `360 + 16 + 144 + 20 = 540 ✓` (internal consistency) ✓
- `product_text_shell_layer` bounds unchanged: `{x:784, y:216, w:144, h:260}` ✓
- `text_does_not_compete_with_canvas`: canvas_right=756, text_shell_x=784 ✓
- `feature_region` remains delegated diagnostic ✓
- `python3 -m pytest -q tests/poster2/test_pipeline.py` → **126 passed**
- `python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py` → **109 passed**

---

## 7. Risks / Follow-up for Next PR Only

- PR-C (capacity / label bounds / clamp / connector tuning) remains next priority — not started here
- Annotation anchors (anchor_y 250/350/450) remain inside new primary range [188,548]; anchor_y 550 (slot 4) now falls in gap rather than secondary, but is excluded by `max_items=3` — no behavioral change
- Secondary at h=144 is compact; if future tuning wants more secondary height, bottom breathing would need to be reduced (trade-off owned by PR-C or later)
- No visual regression test run; changes are pure geometry constants, validated by focused pipeline tests
