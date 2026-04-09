# Product Region Contract Closure Status v1

**Branch:** `PosterSop06-beautification-phase1`
**Date:** 2026-03-30
**PR:** PR-3 — Freeze product owner surfaces and dual-image geometry

---

## Scope

PR-3 closes the product region contract by:

1. Formally freezing the 7 product owner surfaces
2. Enforcing annotation ownership rules in evidence
3. Freezing runtime auto-promotion behavior
4. Declaring `primary_secondary_dual_v2` geometry as final

This is contract-level closure. Pillow renderer parity for the secondary slot is a known open follow-up (tracked separately).

---

## Frozen Owner Surfaces

The following 7 surfaces are the canonical owner surfaces for `product_region` in `template_dual_v2`.

| Surface | Role |
|---|---|
| `product_canvas_shell_layer` | Outer structural shell spanning the full product region |
| `product_primary_slot` | Main product image owner; receives all annotation callouts |
| `product_secondary_slot` | Supporting image slot; no annotation ownership |
| `product_image_layer` | Primary product image rendering surface |
| `product_secondary_image_layer` | Secondary product image rendering surface (dual mode only) |
| `product_annotation_shell_layer` | Annotation shell anchored to primary slot only |
| `product_annotation_items_layer` | Annotation item rendering surface (primary slot only) |

These are declared as `_FROZEN_PRODUCT_OWNER_SURFACES: frozenset[str]` in `template_behavior.py`.

Every `product_contract_review` emits `owner_surfaces: list[str]` — a sorted snapshot of this constant.

---

## Ownership Rules

### Rule 1: Annotation shell anchors to primary slot only

`_PRODUCT_ANNOTATION_OWNER_SLOT = "product_primary_slot"`

- `product_annotation_shell_layer` and `product_annotation_items_layer` always bind to primary slot geometry
- `product_contract_review` exposes `annotation_owner_slot = "product_primary_slot"` in every generation

### Rule 2: Secondary slot never becomes annotation owner

- `product_contract_review` exposes `secondary_slot_annotation_ownership = False` unconditionally
- Enforced implicitly: `_PRODUCT_ANCHOR_CALLOUTS_MAX_ITEMS = 3` restricts callouts to indices 0–2
  - Anchor positions for callouts 0–2: y = 250, 350, 450 (within primary slot y-range [188, 498])
  - Callout index 3 has anchor_y = 550 (secondary slot territory [506, 708]); never activated

---

## Frozen Runtime Behavior

### Mode selection rules (frozen)

| Condition | Activated mode |
|---|---|
| No secondary asset | `product_layout_mode = single_primary` |
| Secondary asset present | `product_layout_mode = primary_secondary_dual` (auto-promoted) |

Auto-promotion reason code: `auto_promoted_by_secondary_asset`

When `primary_secondary_dual` is active:
- `product_geometry_mode = primary_secondary_dual_v2`
- Reason code: `dual_image_geometry_v2_selected`

---

## Frozen Geometry: `primary_secondary_dual_v2`

**Decision: `primary_secondary_dual_v2` is final.** Geometry was live-verified in Entry 7 of the branch execution log. No further geometry adjustment is needed.

### Slot bounds

| Slot | x | y | w | h |
|---|---|---|---|---|
| `product_primary_slot` | 456 | 188 | 300 | 310 |
| `product_secondary_slot` | 456 | 506 | 300 | 202 |
| Single-primary fallback | 456 | 188 | 300 | 520 |

Parent region: `product_region` at x=456, y=188, w=300, h=520 (unchanged).
Gap between primary bottom (498) and secondary top (506): 8px.

`product_contract_review` exposes `geometry_frozen = True` in every generation.

### Geometry relationship to single-primary

- `single_primary` uses the full 520px height region (backward-compatible with all prior renders)
- `primary_secondary_dual_v2` splits the region: primary receives the upper 310px, secondary the lower 202px with an 8px gap

---

## Evidence Fields Added

`product_contract_review` now includes:

| Field | Value |
|---|---|
| `owner_surfaces` | sorted list of all 7 frozen owner surfaces |
| `annotation_owner_slot` | `"product_primary_slot"` (always) |
| `secondary_slot_annotation_ownership` | `False` (always) |
| `geometry_frozen` | `True` (always) |

---

## Test Coverage

New test class: `TestProductOwnerSurfaceFreeze` (9 tests) in `tests/poster2/test_pipeline.py`.

| Test | What it verifies |
|---|---|
| `test_owner_surfaces_constant_is_frozen` | `_FROZEN_PRODUCT_OWNER_SURFACES` is a frozenset with exactly the 7 surfaces |
| `test_annotation_owner_slot_constant` | `_PRODUCT_ANNOTATION_OWNER_SLOT == "product_primary_slot"` |
| `test_product_contract_review_lists_all_owner_surfaces` | `owner_surfaces` field in contract review covers all 7 surfaces |
| `test_annotation_owner_slot_in_contract_review` | `annotation_owner_slot == "product_primary_slot"` in contract review |
| `test_secondary_slot_annotation_ownership_is_false` | `secondary_slot_annotation_ownership = False` even in dual mode |
| `test_geometry_frozen_flag_in_contract_review` | `geometry_frozen = True` in contract review |
| `test_v2_geometry_constants_are_final` | All slot bounds match expected v2 values; no primary/secondary overlap |
| `test_single_primary_activates_when_no_secondary_asset` | `single_primary` when no secondary |
| `test_primary_secondary_dual_activates_when_secondary_asset_present` | `primary_secondary_dual` + `v2` geometry when secondary asset present |

---

## What Is Not Done

- **Pillow renderer secondary slot parity**: Pillow draws into `product_secondary_slot` but the rendering path is not fully contract-driven from `ResolvedProductBehavior.product_secondary_slot` bounds. Tracked as an open follow-up.
- **Puppeteer text layer evidence parity**: Not in scope for this PR.
- **Stage 2 frontend freeze display**: The new `owner_surfaces`, `annotation_owner_slot`, `secondary_slot_annotation_ownership`, and `geometry_frozen` fields are emitted in backend evidence but not yet surfaced in Stage 2 diagnostics. Low priority; diagnostics panel already shows slot bounds and layout mode.

---

## Prior Product Region Work

This document closes the product region contract started in:

- `product_region_annotation_contract_status_v1.md` — annotation layer activation
- Entry 5 (family_a_structural_closeout) — product dual-image contract + slots defined
- Entry 6 — Pillow rendering into secondary slot; runtime auto-promotion wired
- Entry 7 — Product geometry_mode emitted; feature delegation cleanup
- PR-1 / PR-2 — Bottom mode freeze (separate scope)
