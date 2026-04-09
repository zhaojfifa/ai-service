# Bottom Mode Family Contract Closure Status v1

## PR-7B-final — Bottom Mode Family Contract Closure

**Branch:** `pr6-clean`
**Status:** Complete
**Date:** 2026-04-04

---

## Scope

Close the bottom mode family (`title_gallery_split` and `text_only_expanded`) against the final design target: no overlap with `product_secondary_slot`, subtitle wraps in `title_gallery_split`, and `text_only_expanded` remains lower-anchored at the correct shell position.

---

## Frozen Unchanged

- Header
- Product geometry (`product_secondary_slot`: `{x:456, y:564, w:300, h:144}`)
- Feature delegation
- Beautification
- `text_gallery_expanded` shell top (still 640)
- `gallery_only` shell top (still 728 via default)
- PR-7B3/7B4 lower-anchoring logic (`text_only_expanded` offset = `available_height - used_height`)
- PR-7B2 subtitle capacity / line clamps
- PR-6E full-width expansion (x=96, w=832 for text_only_expanded)

---

## Root Cause

`product_secondary_slot` bottom = y(564) + h(144) = **708**.

| Mode | Old `bottom_shell_top` | product_secondary_slot bottom | Old gap | Required |
|------|------------------------|-------------------------------|---------|----------|
| `title_gallery_split` | 680 | 708 | **−28px (overlap)** | ≥ 16px |
| `text_only_expanded` | 640 | 708 | **−68px (overlap)** | ≥ 16px |

Design requirement: visible blank space below the product secondary image before the bottom band.

---

## Contract Change

| Field | Before | After |
|-------|--------|-------|
| `_EXPANDED_BOTTOM_SHELL_TOPS["title_gallery_split"]` | 680 | **728** |
| `_EXPANDED_BOTTOM_SHELL_TOPS["text_only_expanded"]` | 640 | **728** |

**Gap after fix:** `728 − 708 = 20px` (satisfies `>= 16px design_gap`)

---

## Before/After Table

### title_gallery_split

| Sub-case | `bottom_shell_top` before | `bottom_shell_top` after | Gap before | Gap after |
|----------|--------------------------|--------------------------|------------|-----------|
| compact (no sub) | 680 | 728 | −28px (overlap) | +20px ✓ |
| standard subtitle | 680 | 728 | −28px (overlap) | +20px ✓ |
| dense subtitle (4 items) | 680 | 728 | −28px (overlap) | +20px ✓ |

gallery_shell_top (2-item expanded, title_band_height=192): 872 → **920**
gallery_shell_top (4-item dense, title_band_height=168): 848 → **896**

### text_only_expanded

| Sub-case | `bottom_shell_top` before | `bottom_shell_top` after | `title_slot_y` before | `title_slot_y` after |
|----------|--------------------------|--------------------------|----------------------|----------------------|
| compact | 640 | 728 | 704 | 792 |
| standard | 640 | 728 | 690 | 778 |
| moderate | 640 | 728 | 694 | 782 |
| dense | 640 | 728 | 704 | 792 |

All `subtitle_slot_y` values shift +88 (same delta as shell_top shift).

---

## No-Overlap Evidence

| Invariant | Before | After |
|-----------|--------|-------|
| `title_gallery_split`: shell_top >= 708 + 16 | FAIL: 680 < 724 | PASS: 728 >= 724 ✓ |
| `text_only_expanded`: shell_top >= 708 + 16 | FAIL: 640 < 724 | PASS: 728 >= 724 ✓ |
| `title_gallery_split` all sub-cases fit in canvas (top+height ≤ 1024) | — | PASS: max 728+192+100=1020 ≤ 1024 ✓ |
| `text_only_expanded` shell stays below canvas (top+height < 1024) | — | PASS: max 728+240=968 < 1024 ✓ |

---

## Subtitle Wrap Evidence (title_gallery_split)

`title_gallery_split` aliases to `text_gallery_expanded` in `_resolve_bottom_layout_policies`. All subtitle-present branches in `text_gallery_expanded` use `two_line_clamp_inside_expanded_split_title_band` with `subtitle_line_clamp = 2`. This is unchanged — the subtitle wrap was already correct via the alias path. No single-line ellipsis case exists for `title_gallery_split` in the active code path.

Evidence from new test class: `subtitle_line_clamp >= 2` for all gallery counts (1–4) with long subtitle.

---

## Lower-Anchor Occupation Evidence (text_only_expanded)

PR-7B3 lower-anchoring is intact after shell_top shift:
- `offset = max(available_height - used_height, 0)` (dead space above, not below)
- All sub-cases: `subtitle_bottom == band_bottom - pad_bottom` (subtitle touches band edge)
- Dead space below subtitle = 0 for all sub-cases

Evidence from new test class: `test_toe_dead_space_all_above_title_not_below` — passes for all sub-cases.

---

## Render Parity Evidence

- `layout_metrics["bottom_shell_top"]` == CSS var `--bottom-shell-top` (relational test)
- `geometry_evidence.region_bounds.title_band_region.y == layout_metrics["bottom_shell_top"]` (new parity test)
- `title_text_layer.slot_bounds.y == layout_metrics["title_slot_y"]` (new parity test)
- `gallery_shell_top == bottom_shell_top + title_band_height` (no peer_gap for alias path)

---

## Files Changed

| File | Change |
|------|--------|
| `app/services/poster2/template_behavior.py` | `_EXPANDED_BOTTOM_SHELL_TOPS["title_gallery_split"]` 680→728; `_EXPANDED_BOTTOM_SHELL_TOPS["text_only_expanded"]` 640→728; comments updated |
| `tests/poster2/test_pipeline.py` | Updated 20+ stale y-assertions across 6 test classes; added `TestBottomModeFamilyContractClosure` (15 tests) |
| `tests/poster2/test_renderer.py` | Updated 2 stale gallery_shell_top assertions (872→920, 848→896); updated 1 gallery_items_y assertion (882→930) |

---

## Exact Test Commands And Results

```
python3 -m pytest -q tests/poster2/test_pipeline.py::TestBottomModeFamilyContractClosure
→ 15 passed

python3 -m pytest -q tests/poster2/test_pipeline.py tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py
→ 2 failed (pre-existing), 361 passed
```

Pre-existing failures (unrelated to this PR):
- `TestPosterPipelineRun::test_renderer_metadata_includes_layer_render_status`
- `TestPosterPipelineRun::test_feature_contract_review_exposes_requested_sanitized_rendered_chain_with_empty_and_capped_items`

---

## Final Acceptance Evidence

1. **split no-overlap gap**: `bottom_shell_top=728 >= 708+16=724` ✓ (20px actual gap)
2. **expanded no-overlap gap**: same ✓
3. **split subtitle wrap**: `subtitle_line_clamp=2`, `two_line_clamp_inside_expanded_split_title_band` for all gallery counts ✓
4. **expanded occupation**: lower-anchored, dead space above only, subtitle_bottom == available_bottom ✓
5. **parity**: resolver → layout_metrics → geometry_evidence → text layers → CSS vars all agree ✓

---

## Next PR Only

- No remaining bottom mode family geometry work
- Bottom contract closed against product_secondary_slot
- Next: PR-B (product text shell sibling) or other priority per CLAUDE.md
