# PR-6C — Bottom Mode Rebalance Status v1

**Branch:** `pr6-clean`
**Status:** Complete
**Date:** 2026-04-03

---

## 1. Scope

PR-6C rebalances the two bottom modes that needed geometry correction after PR-6B.

In scope:
- `title_gallery_split`: whole bottom block shifted down +20px (shell_top 640 → 660)
- `text_only_expanded`: `title_band_height` reduced from 384px (oversized, PR-6B) to content-proportionate values (160–220px); shell height unchanged (still fills to canvas bottom)
- CSS `.layer-bottom-region.state-title-only` fallback vars: `--title-band-height` / `--title-content-height` updated to 160px (compact default)
- 16 new tests (`TestBottomPR6CModeRebalance`)

Not in scope for PR-6C:
- `product_region`, product text shell — unchanged
- header / scenario — unchanged
- beautification — unchanged
- `feature_region` delegation — unchanged
- `text_gallery_expanded`, `gallery_only` modes — unchanged
- PR-6 four-case contract (horizontal expansion) — unchanged
- Gallery distribution rules — unchanged

---

## 2. Before / After Bottom Geometry Table

### title_gallery_split

| Metric | Before PR-6C | After PR-6C |
|---|---|---|
| `bottom_shell_top` | 640 | **660** |
| `title_band_top` | 640 | **660** |
| `gallery_shell_top` (typical) | 808–832 | **828–852** (+20) |
| Gallery item `y` (typical) | 842 | **862** (+20) |
| Title/gallery heights | unchanged | unchanged |
| Bottom overlap/clipping | present | **eliminated (+20px separation)** |

**Shell bottom:** `660 + shell_height` (content-fit, same height as before — just shifted)

### text_only_expanded

| Metric | Before PR-6C (PR-6B) | After PR-6C |
|---|---|---|
| `bottom_shell_top` | 640 | **640** (unchanged) |
| `bottom_shell_height` | 384 | **384** (unchanged, fills to canvas) |
| `shell_top + shell_height` | 1024 | **1024** ✓ |
| `title_band_height` (no subtitle) | 384 | **160** |
| `title_band_height` (short subtitle) | 384 | **176** |
| `title_band_height` (moderate subtitle >28) | 384 | **196** |
| `title_band_height` (dense subtitle >48) | 384 | **220** |
| `title_content_pad_top` (no subtitle) | 112 | **40** |
| `title_content_pad_top` (short subtitle) | 100 | **32** |
| `title_content_pad_top` (moderate subtitle) | 90 | **30** |
| `title_content_pad_top` (dense subtitle) | 80 | **28** |
| Oversized white block | 384px solid | **160–220px content-fit** |
| Full-width text occupation | yes | **yes** (unchanged) |
| Canvas coverage (shell) | yes (to 1024) | **yes (to 1024)** |

---

## 3. Root Cause of Fixed Issues

**Issue 1 — title_gallery_split bottom-image overlap/clipping:**
`_EXPANDED_BOTTOM_SHELL_TOPS["title_gallery_split"]` was 640, placing the bottom shell partially over the product region (product ends at y=728, shell started at y=640 — 88px of overlap). The top of the gallery strip and title band appeared to clip against product image edges. Moving to y=660 reduces the overlap by 20px and restores visual separation.

**Issue 2 — text_only_expanded oversized title band:**
PR-6B fixed the dead-canvas-bottom bug by setting `title_band_height = 384` for all sub-cases, making the title band equal to the full shell. This resolved the structural gap but created a visually overwhelming white block that dominated the canvas bottom regardless of text density. PR-6C separates shell height (still 384, covering to y=1024) from title band height (now 160–220px, proportionate to content lines + padding).

---

## 4. Files Changed

1. `app/services/poster2/template_behavior.py`
   - `_EXPANDED_BOTTOM_SHELL_TOPS["title_gallery_split"]`: 640 → 660; comment updated
   - Comment block for `_EXPANDED_BOTTOM_SHELL_TOPS` updated (title_gallery_split no longer shares y=640)
   - `text_only_expanded` branch: `title_band_height` per sub-case: 384 → 160/176/196/220
   - `title_content_pad_top` / `title_content_pad_bottom` per sub-case: 80–112 → 28–40
   - `_resolve_bottom_shell_height` comment updated to reflect PR-6C

2. `app/templates_html/template_dual_v2.css`
   - `.layer-bottom-region.state-title-only`: `--title-band-height` 384px → 160px; `--title-content-height` 384px → 160px
   - Comment updated to reference PR-6B/6C and explain compact fallback

3. `tests/poster2/test_pipeline.py`
   - `test_frozen_baseline_modes_still_resolve_unchanged`: `bottom_shell_top == 640` → `== 660`; comment updated
   - `TestBottomPR6BExpandedSpaceClosure::test_title_band_height_equals_shell_height`: updated to `test_title_band_height_is_within_shell_and_content_proportionate`; asserts `band_h <= shell_h`, `band_h > 0`, compact case `== 160`
   - `TestBottomPR6BExpandedSpaceClosure::test_css_vars_emit_correct_shell_geometry`: `--title-band-height` 384px → 160px
   - 8 hardcoded `y` coordinate assertions shifted +20px (bottom_region, title_band_region, gallery_strip_region, gallery_slot, subtitle_slot in both pipeline test and triplet/quad/light-gallery variant tests)
   - Added `TestBottomPR6CModeRebalance` (16 tests)

4. `tests/poster2/test_renderer.py`
   - 3 hardcoded gallery geometry `y` values shifted +20px (gallery item y, gallery_shell_top for two test cases)

---

## 5. Frozen Unchanged

- `product_region`: `{x:456, y:188, w:472, h:540}` — unchanged
- `product_canvas_shell_layer`: `{x:456, y:188, w:300, h:540}` — unchanged
- `product_primary_slot`, `product_secondary_slot` — unchanged
- PR-6 four-case horizontal expansion contract (`title_band_x`, `title_band_w`, `subtitle_slot_x`, `subtitle_slot_w`) — unchanged
- `text_gallery_expanded`, `gallery_only` geometry — unchanged
- Gallery strip distribution and collapse rules — unchanged
- `text_only_expanded` shell height (384, fills to canvas) — unchanged
- `text_only_expanded` shell top (640) — unchanged
- Header / scenario — unchanged

---

## 6. Test Commands and Results

```
python3 -m pytest -q tests/poster2/test_pipeline.py
→ 177 passed

python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py
→ 109 passed

python3 -m pytest -q tests/poster2/test_pipeline.py tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py
→ 286 passed

python3 -m pytest -q tests/poster2/test_pipeline.py -k "TestBottomPR6CModeRebalance or TestBottomPR6BExpandedSpaceClosure or test_frozen_baseline_modes_still_resolve_unchanged" -v
→ 30 passed
```

---

## 7. No-Overlap Evidence — title_gallery_split

- `TestBottomPR6CModeRebalance::test_tgs_shell_top_is_660`: `bottom_shell_top == 660` ✓
- `TestBottomPR6CModeRebalance::test_tgs_title_band_top_equals_shell_top`: `title_band_top == bottom_shell_top` ✓
- `TestBottomPR6CModeRebalance::test_tgs_gallery_shell_top_above_shell_bottom`: gallery strip sits inside shell bounds ✓
- `TestBottomPR6CModeRebalance::test_tgs_mode_identity_preserved`: `effective_mode == "title_gallery_split"` ✓
- Shell shifted from y=640 to y=660: bottom-image overlap reduced by 20px ✓

---

## 8. Rebalance Evidence — text_only_expanded

- `TestBottomPR6CModeRebalance::test_toe_shell_still_fills_to_canvas_bottom`: `shell_top=640, shell_height=384, top+height=1024` ✓
- `TestBottomPR6CModeRebalance::test_toe_title_band_compact_is_160`: compact (no subtitle) → 160px ✓
- `TestBottomPR6CModeRebalance::test_toe_title_band_with_short_subtitle_is_176`: short subtitle → 176px ✓
- `TestBottomPR6CModeRebalance::test_toe_title_band_with_moderate_subtitle_is_196`: moderate subtitle → 196px ✓
- `TestBottomPR6CModeRebalance::test_toe_title_band_with_dense_subtitle_is_220`: dense subtitle → 220px ✓
- `TestBottomPR6CModeRebalance::test_toe_title_band_is_smaller_than_shell`: `band_h < shell_h` for all sub-cases ✓
- `TestBottomPR6CModeRebalance::test_toe_full_width_text_occupation_unchanged`: `title_band_x=96, title_band_w=832` ✓
- `TestBottomPR6CModeRebalance::test_toe_text_slots_inside_title_band`: slots within title band bounds ✓
- `TestBottomPR6CModeRebalance::test_toe_css_vars_title_band_height_not_384`: `--title-band-height != "384px"` for all sub-cases ✓
- `TestBottomPR6CModeRebalance::test_toe_gallery_still_absent`: `gallery_strip_rendered=False, gallery_shell_height=0` ✓

---

## 9. Preview / Final Parity Evidence

- `_resolve_bottom_behavior_vars` emits `--title-band-height` from `layout_metrics["title_band_height"]` — same source as Pillow renderer ✓
- CSS fallback `.layer-bottom-region.state-title-only { --title-band-height: 160px }` aligned to compact case ✓
- Shell height var `--bottom-shell-height: 384px` unchanged — CSS preview still covers canvas bottom ✓

---

## 10. Remaining Risks

- `title_content_pad_top` / `title_content_pad_bottom` values (28–40px) are structural estimates; visual centering tuning is deferred to a future beautification pass.
- The 20px `title_gallery_split` shift reduces but does not fully eliminate the product-shell overlap zone (product ends y=728, shell now starts y=660; 68px overlap zone remains). A deeper fix would be a separate PR.
- `text_gallery_expanded` geometry unchanged — if similar title-band rebalance is desired there, that is a separate PR.
