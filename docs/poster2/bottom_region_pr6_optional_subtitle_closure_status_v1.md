# PR-6 — Bottom Optional Subtitle Closure Status v1

**Branch:** `claude/festive-heisenberg`
**Status:** Complete
**Date:** 2026-04-02

---

## 1. Scope

PR-6 closes out the optional subtitle and text-area adaptive expansion contract for `title_gallery_split` bottom mode.

In scope:
- Four-case acceptance: gallery+subtitle / gallery+no_subtitle / no_gallery+subtitle / no_gallery+no_subtitle
- `title_band_x` / `title_band_w`: horizontal expansion of title band shell when gallery is absent
- `subtitle_slot_x` / `subtitle_slot_w`: subtitle text slot horizontal bounds derived from expanded title band
- `title_band_expansion_policy`: explicit named policy for expansion state
- `--title-band-left` / `--title-band-width` CSS vars injected from resolver
- Pillow renderer: `_title_band_shell_bounds`, `_title_text_slot`, `_subtitle_text_slot` use dynamic x/w from layout_metrics
- Four-case test class `TestBottomPR6OptionalSubtitleClosure`

Not in scope for PR-6:
- `product_region`, product text shell — unchanged
- header / scenario — unchanged
- beautification — unchanged
- `feature_region` delegation — unchanged
- `text_only_expanded` mode policy changes — unchanged (expansion applies passively)
- gallery content or gallery shell geometry — unchanged

---

## 2. Four-Case Contract

| Case | gallery_strip_rendered | subtitle_slot_rendered | title_band_expansion_policy | title_band_x | title_band_w |
|---|---|---|---|---|---|
| gallery + subtitle | True | True | `standard_title_band_with_gallery` | 112 | 800 |
| gallery + no subtitle | True | False | `standard_title_band_with_gallery` | 112 | 800 |
| no gallery + subtitle | False | True | `full_width_title_band_no_gallery` | 96 | 832 |
| no gallery + no subtitle | False | False | `full_width_title_band_no_gallery` | 96 | 832 |

**Horizontal geometry derivation (no-gallery case):**
- `title_band_x = 96` — matches `gallery_slot.x` (full bottom shell left edge)
- `title_band_w = 832` — matches `gallery_slot.w` (full bottom shell width)
- `subtitle_slot_x = title_band_x + 40 = 136`
- `subtitle_slot_w = title_band_w − 80 = 752`

**Standard (gallery present) geometry unchanged:**
- `title_band_x = 112` — matches `title_slot.x` (frozen baseline)
- `title_band_w = 800` — matches `title_slot.w` (frozen baseline)
- `subtitle_slot_x = 152` — matches `subtitle_slot.x` (frozen baseline)
- `subtitle_slot_w = 720` — matches `subtitle_slot.w` (frozen baseline)

---

## 3. Carry-Forward Truth Entering PR-6

- Current bottom mode: `title_gallery_split` (default)
- Current subtitle: collapsed (`subtitle_slot_rendered=false, subtitle_slot_height=0`) as default (no subtitle text provided)
- Gallery renders when items present; no "optional subtitle + text area adaptive expansion" closure prior to this PR
- Header truncation left to future PR — not in PR-6 scope

---

## 4. Files Changed

1. `app/services/poster2/template_behavior.py`
   - `ResolvedBottomBehavior`: add `title_band_expansion_policy: str` field + `as_dict()` update
   - `_resolve_bottom_layout_policies`: add `title_band_x`, `title_band_w`, `subtitle_slot_x`, `subtitle_slot_w`, `title_band_expansion_policy` computation and emit into `layout_metrics`
   - `_resolve_bottom_behavior_vars`: add `--title-band-left`, `--title-band-width`

2. `app/templates_html/template_dual_v2.css`
   - `#poster-root`: add `--title-band-left: 112px` and `--title-band-width: 800px` defaults
   - `.region-shell-title-band`: change `left: 112px` → `left: var(--title-band-left)` and `width: 800px` → `width: var(--title-band-width)`

3. `app/services/poster2/renderer.py`
   - `_title_band_shell_bounds`: use `layout_metrics["title_band_x"]` and `layout_metrics["title_band_w"]`
   - `_title_text_slot`: use `layout_metrics["title_band_x"]` / `layout_metrics["title_band_w"]` instead of `spec.title_slot.x/w`
   - `_subtitle_text_slot`: use `layout_metrics["subtitle_slot_x"]` / `layout_metrics["subtitle_slot_w"]`

4. `tests/poster2/test_pipeline.py`
   - Add `TestBottomPR6OptionalSubtitleClosure` class (8 tests across 4 cases)

---

## 5. Frozen Unchanged

- `product_region`: `{x:456, y:188, w:472, h:540}` — unchanged
- `product_canvas_shell_layer`: `{x:456, y:188, w:300, h:540}` — unchanged
- `product_primary_slot`, `product_secondary_slot` — unchanged
- `_PRODUCT_TEXT_SHELL_H = 276` — unchanged
- Bottom mode alias (`title_gallery_split` → `text_gallery_expanded` inside `_resolve_bottom_layout_policies`) — unchanged
- Gallery strip geometry and distribution — unchanged
- Subtitle rendering condition (`subtitle_present and bottom_mode != "gallery_only" and title_present`) — unchanged
- Vertical slot metrics (`title_slot_y`, `title_slot_height`, `subtitle_slot_y`, `subtitle_slot_height`) — unchanged

---

## 6. Test Commands and Results

```
python3 -m pytest -q tests/poster2/test_pipeline.py
→ 148 passed

python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py
→ 109 passed
```

---

## 7. Four-Case Acceptance Evidence

All 10 `TestBottomPR6OptionalSubtitleClosure` tests pass.

### Case 1: gallery + subtitle
- `subtitle_slot_rendered == True` ✓
- `gallery_strip_rendered == True` ✓
- `title_band_expansion_policy == "standard_title_band_with_gallery"` ✓
- `title_band_x == 112`, `title_band_w == 800` ✓
- `subtitle_slot_x == 152`, `subtitle_slot_w == 720` ✓
- `--title-band-left: 112px`, `--title-band-width: 800px` ✓

### Case 2: gallery + no subtitle
- `subtitle_slot_rendered == False`, `reason_code == "subtitle_empty"` ✓
- `subtitle_slot_height == 0` ✓
- `gallery_strip_rendered == True` ✓
- `title_band_expansion_policy == "standard_title_band_with_gallery"` ✓

### Case 3: no gallery + subtitle
- `gallery_strip_rendered == False` ✓
- `subtitle_slot_rendered == True` ✓
- `title_band_expansion_policy == "full_width_title_band_no_gallery"` ✓
- `title_band_x == 96`, `title_band_w == 832` ✓
- `subtitle_slot_x == 136` (96+40), `subtitle_slot_w == 752` (832-80) ✓
- `--title-band-left: 96px`, `--title-band-width: 832px` ✓

### Case 4: no gallery + no subtitle
- `gallery_strip_rendered == False` ✓
- `subtitle_slot_rendered == False` ✓
- `title_band_expansion_policy == "full_width_title_band_no_gallery"` ✓
- `title_band_x == 96`, `title_band_w == 832` ✓
- `subtitle_slot_x == 136`, `subtitle_slot_w == 752` ✓
- `--title-band-left: 96px`, `--title-band-width: 832px` ✓

---

## 8. Preview/Final Parity Evidence

- CSS `--title-band-left` / `--title-band-width` injected from resolver, same for both preview and final generation paths
- Pillow `_title_band_shell_bounds` and `_title_text_slot` / `_subtitle_text_slot` consume same `layout_metrics` keys
- Both paths gate on same `gallery_strip_rendered` flag from resolver

---

## 9. Remaining Risks

- This PR does not address `text_only_expanded` horizontal expansion — it benefits passively from the CSS var change but gets `full_width_title_band_no_gallery` policy only when that mode has `gallery_strip_rendered=False` (always true for it). May need a separate policy name for text_only_expanded cases.
- Header truncation tracking remains a future PR item.
