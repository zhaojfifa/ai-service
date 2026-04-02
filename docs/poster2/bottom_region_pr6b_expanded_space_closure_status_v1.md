# PR-6B — Bottom Expanded Space / Text Expansion / Overlap Closure Status v1

**Branch:** `pr6-clean`
**Status:** Complete
**Date:** 2026-04-02

---

## 1. Scope

PR-6B closes out the `text_only_expanded` bottom mode geometry: the full canvas bottom area is now covered by the shell and title band, text is properly centered within the expanded space, and no dead canvas bottom remains.

In scope:
- `bottom_shell_top` for `text_only_expanded`: 656 → 640 (matches other expanded modes)
- `bottom_shell_height` for `text_only_expanded`: `title_band_height` (164–220px) → `1024 - bottom_shell_top` = 384
- `title_band_height` for all `text_only_expanded` sub-cases: fixed 384 (fills full shell)
- `title_content_pad_top` / `title_content_pad_bottom`: updated for text centering within 384px
- `_resolve_bottom_shell_height`: bug fixed — no longer returns bare `title_band_height` for `text_only_expanded`
- CSS `.layer-bottom-region.state-title-only` fallback defaults: aligned to new geometry
- 13 new tests (`TestBottomPR6BExpandedSpaceClosure`)

Not in scope for PR-6B:
- `product_region`, product text shell — unchanged
- header / scenario — unchanged
- beautification — unchanged
- `feature_region` delegation — unchanged
- `title_gallery_split`, `text_gallery_expanded`, `gallery_only` modes — unchanged
- PR-6 four-case contract (horizontal expansion) — unchanged

---

## 2. Before / After Bottom Geometry Table

| Metric | Before PR-6B | After PR-6B |
|---|---|---|
| `bottom_shell_top` | 656 | **640** |
| `bottom_shell_height` | 164–220 (= `title_band_height`) | **384** (= 1024 − 640) |
| `title_band_top` | 656 | **640** |
| `title_band_height` | 164 / 180 / 196 / 220 (varies by content) | **384** (all sub-cases) |
| `title_content_pad_top` | 20–28 | **80–112** (centered within 384px) |
| `title_content_pad_bottom` | 16–24 | **80–112** |
| Dead canvas below shell | 148–204px | **0px** |
| Shell covers canvas bottom | No (ends at ~820–876) | **Yes (ends at 1024)** |

**Canvas coverage:** `shell_top + shell_height = 640 + 384 = 1024` ✓

---

## 3. Root Cause of Fixed Bugs

**Bug 1 — Dead canvas bottom:**
`_resolve_bottom_shell_height` for `text_only_expanded` returned `title_band_height` (164–220px).
With `bottom_shell_top=656`, the shell ended at y=820–876, leaving 148–204px of uncovered canvas.

**Fix:** `return 1024 - bottom_shell_top` — shell always fills to canvas bottom.

**Bug 2 — Less space than other expanded modes:**
`_EXPANDED_BOTTOM_SHELL_TOPS["text_only_expanded"]` was 656 (72px above frozen baseline).
Other expanded modes (`title_gallery_split`, `text_gallery_expanded`) already used 640 (88px above baseline).
`text_only_expanded` (no gallery) had *less* space than modes that also carry a gallery strip.

**Fix:** Changed to 640 — consistent with all other expanded modes.

**Bug 3 — Title band undersized:**
The four `title_band_height` sub-case values (164/180/196/220) were compact legacy values.
The title band only covered part of the bottom shell, with no explicit intent for the remaining space.

**Fix:** All sub-cases set `title_band_height = 384`. Pads tuned to center text vertically.

---

## 4. Files Changed

1. `app/services/poster2/template_behavior.py`
   - `_EXPANDED_BOTTOM_SHELL_TOPS["text_only_expanded"]`: 656 → 640
   - Comment block updated to reflect new capacity
   - `text_only_expanded` branch: `title_band_height = 384` for all 4 sub-cases
   - `title_content_pad_top` / `title_content_pad_bottom`: updated per sub-case (80–112)
   - `title_stack_gap`: 8 → 10 for sub-cases with subtitle
   - `_resolve_bottom_shell_height` for `text_only_expanded`: `return title_band_height` → `return 1024 - bottom_shell_top`

2. `app/templates_html/template_dual_v2.css`
   - `.layer-bottom-region.state-title-only .region-shell-bottom`: height 160px → 384px
   - `.layer-bottom-region.state-title-only` vars: top 728→640, height 160→384, title_band 144→384, title_content 144→384

3. `tests/poster2/test_pipeline.py`
   - `test_text_only_expanded_resolves_with_larger_text_capacity_than_frozen_baseline`: `bottom_shell_top == 656` → `== 640`
   - Add `TestBottomPR6BExpandedSpaceClosure` (13 tests)

---

## 5. Frozen Unchanged

- `product_region`: `{x:456, y:188, w:472, h:540}` — unchanged
- `product_canvas_shell_layer`: `{x:456, y:188, w:300, h:540}` — unchanged
- `product_primary_slot`, `product_secondary_slot` — unchanged
- PR-6 four-case horizontal expansion contract (`title_band_x`, `title_band_w`, `subtitle_slot_x`, `subtitle_slot_w`) — unchanged
- `title_gallery_split`, `text_gallery_expanded`, `gallery_only` geometry — unchanged
- Gallery strip geometry and distribution — unchanged
- Header / scenario — unchanged

---

## 6. Test Commands and Results

```
python3 -m pytest -q tests/poster2/test_pipeline.py
→ 161 passed

python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py
→ 109 passed

python3 -m pytest -q tests/poster2/test_pipeline.py -k TestBottomPR6BExpandedSpaceClosure -v
→ 13 passed
```

---

## 7. text_only_expanded Acceptance Evidence

All 13 `TestBottomPR6BExpandedSpaceClosure` tests pass:

- `bottom_shell_top == 640` ✓
- `bottom_shell_height == 384` ✓
- `shell_top + shell_height == 1024` (canvas coverage) ✓
- `title_band_height == 384` ✓
- `title_band_top == bottom_shell_top` ✓
- `title_slot_y >= shell_top` and `title_slot_bottom <= shell_bottom` ✓
- `subtitle_slot_y >= shell_top` and `subtitle_slot_bottom <= shell_bottom` ✓ (when rendered)
- `gallery_strip_rendered == False` ✓
- `gallery_shell_height == 0` ✓ (no overlap)
- `title_band_expansion_policy == "full_width_title_band_no_gallery"` ✓ (PR-6 carry-forward)
- `title_band_x == 96`, `title_band_w == 832` ✓

---

## 8. No-Overlap Evidence

- `gallery_strip_rendered = False` for all `text_only_expanded` invocations (by mode design)
- `gallery_shell_height = 0` (confirmed by test)
- Title band = full shell; no second region inside the shell that could overlap
- Shell extends continuously from y=640 to y=1024 — no gap, no dead zone

---

## 9. Preview / Final Parity Evidence

- `--bottom-shell-top: 640px`, `--bottom-shell-height: 384px` injected from `_resolve_bottom_behavior_vars` for CSS/preview path ✓
- `--title-band-top: 640px`, `--title-band-height: 384px` same path ✓
- Pillow renderer reads `layout_metrics["bottom_shell_height"]` and `layout_metrics["title_band_height"]` — same source ✓
- CSS fallback `.layer-bottom-region.state-title-only` updated to match (backup correctness for edge cases) ✓

---

## 10. Remaining Risks

- `title_content_pad_top` / `title_content_pad_bottom` set at 80–112px for centering. Visual tuning of these padding values is deferred to a future beautification pass.
- Header truncation remains a future PR item (frozen unchanged, not in scope).
- `text_gallery_expanded` geometry unchanged — if similar full-coverage fix is desired there, that is a separate PR.
