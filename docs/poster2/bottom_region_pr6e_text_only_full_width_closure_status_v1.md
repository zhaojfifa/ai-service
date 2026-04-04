# PR-6E: text_only_expanded Full-Width Closure — Status

**Branch:** `pr6-clean`
**Status:** Complete
**Date:** 2026-04-04

---

## Scope

Close the gap between `layout_metrics` full-width truth and the three downstream consumers that were still using hardcoded standard-band values for `text_only_expanded`:

1. `geometry_evidence` — `_title_band_region_bounds`, `_title_slot_bounds`, `_subtitle_slot_bounds`
2. CSS — `.layer-title-subtitle` left/width

Frozen unchanged: `title_gallery_split`, product region, feature delegation, header, beautification.

---

## Root Cause

Since PR-6, `layout_metrics["title_band_x"]=96` and `layout_metrics["title_band_w"]=832` are resolved correctly for `text_only_expanded` (no gallery → `full_width_title_band_no_gallery`). The CSS var `--title-band-left`/`--title-band-width` were also emitted correctly.

Three consumers were not reading these values:

| Consumer | Bug | Impact |
|---|---|---|
| `pipeline._title_band_region_bounds` | `x: 112, w: 800` hardcoded | geometry_evidence reported wrong region x/w |
| `pipeline._title_slot_bounds` | `template.title_slot.x/w` (=112/800) | geometry_evidence reported wrong slot x/w |
| `pipeline._subtitle_slot_bounds` | `template.subtitle_slot.x/w` (=152/720) | geometry_evidence reported wrong subtitle x/w |
| CSS `.layer-title-subtitle` | `left: 112px; width: 800px` hardcoded | preview rendered standard-band width regardless of mode |

The Pillow renderer (`_title_text_slot`, `_subtitle_text_slot`, `_title_band_shell_bounds`) was already consuming `layout_metrics` correctly since PR-6. Only geometry_evidence and CSS preview were out of sync.

---

## Files Changed

| File | Change |
|---|---|
| `app/services/poster2/pipeline.py` | `_title_band_region_bounds`: `x`/`w` from `layout.get("title_band_x/w", 112/800)` |
| `app/services/poster2/pipeline.py` | `_title_slot_bounds`: `x`/`w` from `layout.get("title_band_x/w", template.title_slot.x/w)` |
| `app/services/poster2/pipeline.py` | `_subtitle_slot_bounds`: `x`/`w` from `layout.get("subtitle_slot_x/w", template.subtitle_slot.x/w)` |
| `app/templates_html/template_dual_v2.css` | `.layer-title-subtitle`: `left: var(--title-band-left)`, `width: var(--title-band-width)` |
| `tests/poster2/test_pipeline.py` | Added `TestBottomPR6ETextOnlyFullWidthClosure` (9 tests); updated 2 existing geometry assertions to reflect full-width truth for no-gallery case |

---

## Before / After Geometry Table (text_only_expanded, compact — no subtitle)

| Source | Field | Before | After |
|---|---|---|---|
| `layout_metrics` | `title_band_x` | 96 | 96 (unchanged) |
| `layout_metrics` | `title_band_w` | 832 | 832 (unchanged) |
| `layout_metrics` | `subtitle_slot_x` | 136 | 136 (unchanged) |
| `layout_metrics` | `subtitle_slot_w` | 752 | 752 (unchanged) |
| `geometry_evidence.region_bounds.title_band_region.x` | | **112** | **96** |
| `geometry_evidence.region_bounds.title_band_region.w` | | **800** | **832** |
| `geometry_evidence.slot_bounds.title_slot.x` | | **112** | **96** |
| `geometry_evidence.slot_bounds.title_slot.w` | | **800** | **832** |
| `geometry_evidence.slot_bounds.subtitle_slot.x` | | **152** | **136** |
| `geometry_evidence.slot_bounds.subtitle_slot.w` | | **720** | **752** |
| CSS var `--title-band-left` | | 96px (correct) | 96px (unchanged) |
| CSS var `--title-band-width` | | 832px (correct) | 832px (unchanged) |
| CSS `.layer-title-subtitle` left | | **112px (hardcoded)** | **var(--title-band-left) → 96px** |
| CSS `.layer-title-subtitle` width | | **800px (hardcoded)** | **var(--title-band-width) → 832px** |
| Pillow `_title_band_shell_bounds` x | | 96 (from layout_metrics) | 96 (unchanged) |
| Pillow `_title_text_slot` x | | 96 (from layout_metrics) | 96 (unchanged) |
| Pillow `_subtitle_text_slot` x | | 136 (from layout_metrics) | 136 (unchanged) |

**Note on no-gallery behavior for all modes:** When `gallery_strip_rendered=False` (regardless of mode), the expansion policy is `full_width_title_band_no_gallery` → `title_band_x=96, w=832`. This applies to `title_gallery_split` and `text_gallery_expanded` with empty gallery, as well as `text_only_expanded` always. Geometry evidence for these no-gallery cases now also reports x=96 (correct by contract; was previously masked by hardcoded fallback).

**Modes with gallery present:** `gallery_strip_rendered=True` → `title_band_x=112, w=800` (standard band) → geometry_evidence reports x=112/w=800 (unchanged).

---

## Evidence: layout_metrics == geometry_evidence == rendered slot bounds

From `TestBottomPR6ETextOnlyFullWidthClosure`:

```
test_geometry_evidence_title_band_region_x_is_96       PASS  → {x:96, y:640, w:832, h:160}
test_geometry_evidence_title_band_region_with_subtitle PASS  → {x:96, y:640, w:832, h:176}
test_geometry_evidence_title_slot_x_is_96              PASS  → {x:96, y:680, w:832, h:80}
test_geometry_evidence_subtitle_slot_x_is_136          PASS  → {x:136, y:755, w:752, h:28}
test_layout_metrics_equals_geometry_evidence_title_band_x_w   PASS
test_layout_metrics_equals_geometry_evidence_subtitle_slot_x_w PASS
test_css_vars_title_band_left_and_width_are_full_width  PASS  → --title-band-left:96px, --title-band-width:832px
```

CSS `.layer-title-subtitle` now uses `var(--title-band-left)` / `var(--title-band-width)`, which are emitted at 96px/832px by `_resolve_bottom_behavior_vars` for `text_only_expanded`. Preview and final rendering now consume the same geometry truth.

---

## Test Commands and Results

```
python3 -m pytest -q tests/poster2/test_pipeline.py
→ 199 passed

python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py
→ 109 passed
```

Total: **308 passed**, 0 failed.

---

## Remaining Risks

- None for this scope.
- CSS rendering is not unit-tested (no browser). Visual parity is implied by the CSS var chain: resolver → `_resolve_bottom_behavior_vars` → inline style → CSS var consumer.
