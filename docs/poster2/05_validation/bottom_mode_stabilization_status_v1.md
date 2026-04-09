# Bottom Mode Stabilization Status v1

**Date:** 2026-03-30
**Scope:** Task-1 — Stabilize `text_gallery_expanded` and `gallery_only` runtime modes

---

## Goal

Bring `text_gallery_expanded` and `gallery_only` to the same health bar as `text_only_expanded`:
- `degraded = false`
- `structure_complete = true`
- `deliverable = true`
- no silent fallback
- all four diagnostic fields present (`requested_bottom_mode`, `effective_bottom_mode`, `bottom_layout_mode`, `bottom_mode_override_reason`)

---

## Root Causes Found and Fixed

### gallery_only — geometry bug

**File:** `app/services/poster2/template_behavior.py` `_resolve_bottom_layout_policies`

**Before:** `gallery_shell_top = 888` hardcoded when `gallery_strip_rendered and not title_slot_rendered`

**After:** `gallery_shell_top = title_band_top` (= `bottom_shell_top` = 728)

**Impact:** In `gallery_only` mode (no title band), gallery items were placed at absolute y≈898–962 while the
bottom shell CSS declared `top: 728px; height: ~84px` (y=728–812). The gallery rendered outside the visible
shell region. After fix, items render at y≈738–802, inside the shell.

---

### gallery_only — title_slot always required

**File:** `app/services/poster2/slot_contracts.py`

**Before:** `title_slot` was unconditionally `required=True`; `gallery_only` requests without a title
produced `missing_required_slots: ["title_slot"]` → `structure_complete = false` → `deliverable = false`.

**After:** Added `_BOTTOM_MODE_EXCUSED_REQUIRED_SLOTS = {"gallery_only": frozenset({"title_slot"})}`.
In `evaluate_slot_bindings`, `title_slot` is excused when `binding_inputs["bottom_mode"] == "gallery_only"`.

---

### gallery_only — preflight guard required title unconditionally

**File:** `app/services/poster2/quality_guard.py` `run_preflight_guard`

**Before:** `title` always required → `QualityGuardError` raised for any `gallery_only` request without title.

**After:** Checks `requested_mode != "gallery_only"` before requiring title. `requested_mode` is resolved
from `spec.bottom_mode` or `template.behavior_modes.bottom_mode` (same pattern as elsewhere).

---

### gallery_only — title normalization guard unconditional

**File:** `app/services/poster2/pipeline.py` `_normalize_contract_text_spec`

**Before:** `raise ValueError("title must not be empty after normalization")` unconditionally.

**After:** Same mode-aware check as preflight. `template` is now passed as an optional parameter from the
`run()` call site so the guard has access to the template default mode.

---

## text_gallery_expanded Health

No structural fixes required. `text_gallery_expanded` is already healthy when title is provided:
- `structure_complete = true`, `deliverable = true` ✓
- All four diagnostic fields emitted ✓
- `bottom_layout_mode` mirrors `.mode` ✓

### 2026-03-30 live revalidation

Narrow revalidation was run only for `text_gallery_expanded` after a user-reported failure.

Fresh local runtime proof:
- trace: `266f4c50-f0ba-491f-b0d2-3e6cbf8db559`
- `degraded = false`
- `structure_complete = true`
- `deliverable = true`
- `requested_bottom_mode = text_gallery_expanded`
- `effective_bottom_mode = text_gallery_expanded`
- `bottom_layout_mode = text_gallery_expanded`
- `bottom_mode_override_reason = request_override_applied`

Fresh live runtime proof:
- trace: `afdd09bc-b5dd-4550-982f-addee2d46310`
- `degraded = false`
- `structure_complete = true`
- `deliverable = true`
- `requested_bottom_mode = text_gallery_expanded`
- `effective_bottom_mode = text_gallery_expanded`
- `bottom_layout_mode = text_gallery_expanded`
- `bottom_mode_override_reason = request_override_applied`

Conclusion:
- no resolver fallback reproduced
- no quality-guard failure reproduced
- no renderer-path deliverability failure reproduced
- this revalidation slice required no code change

Eight pipeline tests confirm both modes at full health.

---

## Frozen Post-Fix Gallery_Only Contract

| Property | Value |
|---|---|
| `gallery_shell_top` | = `bottom_shell_top` (728) |
| `title_slot` required | `False` (excused for `gallery_only`) |
| `title_band_region_collapsed_by_design` | `True` |
| `gallery_strip_region_collapsed_by_design` | `False` |
| Preflight title required | `False` |

---

## Tests Added (`TestBottomModeStabilization`, 8 tests)

| Test | What it verifies |
|---|---|
| `test_gallery_only_deliverable_without_title` | `degraded=False, structure_complete=True, deliverable=True` |
| `test_gallery_only_title_slot_not_in_missing_required_when_absent` | `title_slot` not in `missing_required_slots` |
| `test_gallery_only_diagnostics_all_present_without_title` | All 4 diagnostic fields present |
| `test_gallery_only_gallery_shell_top_equals_bottom_shell_top` | `gallery_shell_top == bottom_shell_top` |
| `test_gallery_only_gallery_items_render_inside_bottom_shell` | Item bounds within shell region |
| `test_text_gallery_expanded_deliverable_with_title_and_no_gallery` | Deliverable without gallery items |
| `test_text_gallery_expanded_deliverable_with_title_and_gallery` | Deliverable with 4 gallery items |
| `test_text_gallery_expanded_diagnostics_all_present` | All 4 diagnostic fields present |

**Test count:** 270/270 pass (262 prior + 8 new)

---

## Open Follow-ups (out of Task-1 scope)

- `gallery_only` with no gallery items: `gallery_strip_region` absent and `bottom_region_rendered = false`
  — deliverable is still true (no mandatory regions missing), but the poster is visually empty at the bottom.
  Consider whether a warning should be surfaced in contract evidence.
- Pillow renderer: `gallery_only` gallery items now render at the correct position; Puppeteer path
  uses CSS variables (`--gallery-shell-top`) which are also fixed by the `gallery_shell_top` change.
