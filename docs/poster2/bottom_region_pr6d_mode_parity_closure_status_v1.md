# bottom_region_pr6d_mode_parity_closure_status_v1

## PR-6D — Bottom Mode Parity and Rebalance Closure

**Branch:** `pr6-clean`
**Status:** Complete
**Date:** 2026-04-03

---

## Scope

Bottom region only. Two targeted fixes to close visual and consistency issues left after PR-6C.

---

## Frozen Unchanged

- product region / product_text_shell / feature delegation
- header / scenario
- gallery distribution rules
- PR-6 optional subtitle contract (title_band_x / title_band_w / subtitle_slot_x / subtitle_slot_w)
- beautification
- text_only_expanded shell_top (stays at 640)

---

## Files Changed

| File | Change |
|---|---|
| `app/services/poster2/template_behavior.py` | `_EXPANDED_BOTTOM_SHELL_TOPS["title_gallery_split"]` 660→680; `_resolve_bottom_shell_height` for `text_only_expanded` returns `title_band_height` instead of `1024 - bottom_shell_top`; comments updated |
| `app/templates_html/template_dual_v2.css` | `.state-title-only` CSS fallback: `--bottom-shell-height` 384px→160px; `region-shell-bottom height` 384px→160px; comment updated |
| `tests/poster2/test_pipeline.py` | Updated geometry assertions for +20px title_gallery_split shift; updated text_only_expanded shell-height tests; updated PR-6C tests for new PR-6D truth; added `TestBottomPR6DModeParityClosure` (16 tests) |
| `tests/poster2/test_renderer.py` | `gallery_shell_top` 852→872, 828→848; `gallery_items_y` 862→882 |

---

## Before/After Geometry Table

### title_gallery_split

| Metric | Before (PR-6C) | After (PR-6D) | Delta |
|---|---|---|---|
| `bottom_shell_top` | 660 | 680 | +20px |
| `title_band_top` | 660 | 680 | +20px |
| `gallery_shell_top` (2 items, band_h=192) | 852 | 872 | +20px |
| `gallery_shell_top` (4 items, band_h=168) | 828 | 848 | +20px |
| `gallery_items_y` (2 items) | 862 | 882 | +20px |
| `title_band_height` | unchanged | unchanged | 0 |
| `title_band_x / title_band_w` | unchanged | unchanged | 0 |

### text_only_expanded

| Metric | Before (PR-6C) | After (PR-6D) | Delta |
|---|---|---|---|
| `bottom_shell_top` | 640 | 640 | 0 |
| `bottom_shell_height` | 384 (canvas-fill) | = title_band_height | −224 to −164 |
| `title_band_height` (compact) | 160 | 160 | 0 |
| `title_band_height` (short sub) | 176 | 176 | 0 |
| `title_band_height` (moderate sub) | 196 | 196 | 0 |
| `title_band_height` (dense sub) | 220 | 220 | 0 |
| `shell_top + shell_height` | 1024 | 800/816/836/860 | no longer reaches 1024 |
| Dead canvas below text band | 224–164px | 0px | eliminated |

---

## Consistency Evidence: layout_metrics == geometry_evidence

`bottom_shell_height` is now derived from `title_band_height` directly in `_resolve_bottom_shell_height`:

```python
if bottom_mode == "text_only_expanded":
    return title_band_height
```

CSS var `--bottom-shell-height` is emitted from `layout_metrics["bottom_shell_height"]` in `_resolve_bottom_behavior_vars`. There is no separate path. Preview (CSS) and final (Pillow) both read `layout_metrics`. All four sub-cases verified:

| Sub-case | `title_band_height` | `bottom_shell_height` | `--bottom-shell-height` | Consistent? |
|---|---|---|---|---|
| compact (no sub) | 160 | 160 | `"160px"` | ✓ |
| short sub (≤28) | 176 | 176 | `"176px"` | ✓ |
| moderate sub (29–48) | 196 | 196 | `"196px"` | ✓ |
| dense sub (>48) | 220 | 220 | `"220px"` | ✓ |

---

## No-Overlap Evidence: title_gallery_split

After PR-6D shift to shell_top=680, gallery is computed as:

```
gallery_shell_top = title_band_top + title_band_height + peer_gap
```

All gallery items sit at `y >= 680 + title_band_height`. The bottom canvas boundary is 1024. Shell height wraps gallery exactly. No item escapes the shell.

Confirmed by `test_tgs_gallery_strip_inside_shell_no_overlap` (2 items) and `test_tgs_gallery_strip_inside_shell_dense_quad` (4 items) in `TestBottomPR6DModeParityClosure`.

---

## Parity Evidence

- CSS vars and `layout_metrics` are set from the same dict at the same call site (`_resolve_bottom_behavior_vars` reads `policy.layout_metrics`).
- `test_toe_layout_metrics_equals_css_vars_parity` verifies `--bottom-shell-top`, `--bottom-shell-height`, `--title-band-top`, `--title-band-height` all match their `layout_metrics` counterparts at runtime.

---

## Test Commands and Results

```
python3 -m pytest -q tests/poster2/test_pipeline.py
→ 192 passed

python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py
→ 109 passed
```

---

## Carry-Forward Geometry

### title_gallery_split

- `bottom_shell_top`: 680 (was 660; cumulative +40px from original 640)
- All gallery/title heights, widths, distribution rules: unchanged

### text_only_expanded

- `bottom_shell_top`: 640 (unchanged)
- `bottom_shell_height`: = `title_band_height` (160 / 176 / 196 / 220)
- `shell_top + shell_height`: 800 / 816 / 836 / 860 (no longer fills to 1024)
- `title_band_x = 96`, `title_band_w = 832` (unchanged)
- `title_band_expansion_policy = "full_width_title_band_no_gallery"` (unchanged)
- layout_metrics and geometry_evidence unified: `bottom_shell_height == title_band_height` for all sub-cases
