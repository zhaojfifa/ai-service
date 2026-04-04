# Bottom Vertical Anchoring Closure Status v1

## PR-7B4 — text_only_expanded Bottom Lower-Anchor Closure

**Branch:** `pr6-clean`
**Status:** Complete
**Date:** 2026-04-04

### What changed (PR-7B4)
- `title_content_pad_top`: 24–40 → **20** (uniform across all text_only_expanded sub-cases)
- `title_content_pad_bottom`: 24–40 → **16** (uniform; eliminates 40px dead space in compact)
- No change to `title_stack_gap`, `title_band_height`, slot heights, or clamp values

---

## PR-7B3 — text_only_expanded Vertical Anchoring Closure (superseded by PR-7B4)

**Branch:** `pr6-clean`
**Status:** Complete (pad values further tightened in PR-7B4)
**Date:** 2026-04-04

---

## Scope (combined PR-7B3 + PR-7B4)

- `text_only_expanded` only
- PR-7B3: layout policy → lower-anchored (`offset = available_height - used_height`)
- PR-7B4: pad_top / pad_bottom tightened (20 / 16 uniform), eliminating 40px compact dead space
- Subtitle sits at 16px from band bottom edge; title follows upward from subtitle
- Remaining dead space (offset) is above the content stack

## Frozen Unchanged

- `title_gallery_split` — still center-packed
- `text_gallery_expanded` — still center-packed
- `gallery_only` — unaffected
- bottom shell top / height contract
- title_band_height per sub-case
- pad_top / pad_bottom values
- title_slot_height / subtitle_slot_height per clamp
- overflow shrink logic
- expanded width contract (x=96, w=832)
- subtitle non-truncation result (PR-7B2)
- propagation parity (PR-7B)
- header, product geometry, feature delegation, beautification, email/save workflow

---

## Files Changed

| File | Change |
|------|--------|
| `app/services/poster2/template_behavior.py` | `_resolve_bottom_text_slot_metrics`: add branch for `text_only_expanded` to use `offset = available_height - used_height` instead of `(available_height - used_height) // 2` |
| `tests/poster2/test_pipeline.py` | Updated 1 stale absolute y assertion in `TestBottomPR6ETextOnlyFullWidthClosure`; added `TestBottomPR7B3TextOnlyExpandedVerticalAnchoring` (11 tests) |

---

## Exact Test Commands And Results

```
python3 -m pytest -q tests/poster2/test_pipeline.py::TestBottomPR7B3TextOnlyExpandedVerticalAnchoring
→ 11 passed

python3 -m pytest -q tests/poster2/test_pipeline.py tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py
→ 2 failed (pre-existing), 346 passed
```

Pre-existing failures unrelated to this PR:
- `TestPosterPipelineRun::test_renderer_metadata_includes_layer_render_status`
- `TestPosterPipelineRun::test_feature_contract_review_exposes_requested_sanitized_rendered_chain_with_empty_and_capped_items`

---

## Before/After Vertical Allocation Table

`band_top = 640`. "Before" = original center-packed pads. "After" = PR-7B3+PR-7B4 lower-anchored.

| Sub-case | band_h | pad_top before→after | pad_bottom before→after | avail_h before→after | offset before→after | title_slot_y before→after | sub_slot_y before→after | gap_below before→after |
|----------|--------|----------------------|--------------------------|----------------------|---------------------|--------------------------|------------------------|------------------------|
| compact  | 160    | 40→20                | 40→16                   | 80→124               | 0→44                | 680→704                  | — (no sub)             | 40→16 |
| standard | 176    | 32→20                | 32→16                   | 112→140              | 1→30                | 673→690                  | 755→772                | 32→16 |
| moderate | 196    | 30→20                | 30→16                   | 136→160              | 5→34                | 675→694                  | 757→776                | 30→16 |
| dense    | 240    | 24→20                | 24→16                   | 192→204              | 16→44               | 680→704                  | 776→800                | 24→16 |

---

## Visual Dead-Space Before/After Evidence

**Dense sub-case (worst-case original):**

| | Before | After (PR-7B3+PR-7B4) |
|-|--------|----------------------|
| band_top | 640 | 640 |
| pad_top | 24 | 20 |
| pad_bottom | 24 | 16 |
| available_top | 664 | 660 |
| available_bottom | 856 | 864 |
| title_slot_y | 680 | 704 |
| title_bottom | 768 | 792 |
| subtitle_slot_y | 776 | 800 |
| subtitle_bottom | 840 | 864 |
| Dead space above title | 16px | 44px (intentional: lower-anchor) |
| **Dead space below subtitle** | **16px** | **0px** |

**Compact sub-case (40px dead space eliminated):**

| | Before | After (PR-7B3+PR-7B4) |
|-|--------|----------------------|
| pad_top | 40 | 20 |
| pad_bottom | 40 | 16 |
| title_slot_y | 680 | 704 |
| title_bottom | 760 | 784 |
| band_bottom | 800 | 800 |
| **Dead space below title** | **40px** | **16px** |

---

## Exact Test Commands And Results (PR-7B4)

```
python3 -m pytest -q tests/poster2/test_pipeline.py::TestBottomPR7B3TextOnlyExpandedVerticalAnchoring
→ 11 passed

python3 -m pytest -q tests/poster2/test_pipeline.py tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py
→ 2 failed (pre-existing), 346 passed
```

## Final Acceptance Evidence

- `TestBottomPR7B3TextOnlyExpandedVerticalAnchoring` — 11 passed (updated for PR-7B4 pad values)
- All sub-cases: `subtitle_bottom == band_bottom - 16` (16px clearance, not 24–40)
- Compact: title_bottom = 784 = band_bottom(800) − 16 ✓
- `title_gallery_split` center-packing confirmed unchanged by explicit test
- No regressions beyond 2 pre-existing failures

---

## Next PR Only

- Next: `PR-7C` — text capacity / label bounds / clamp / connector tuning (if needed)
- Or: next product/header work depending on current priority
