# Product Region Final Geometry Status v1

**Date:** 2026-03-31
**Task:** Task-2 — Final product region geometry decision from v2 healthy baseline
**Commit scope:** `fix(poster2): finalize product region geometry from v2 healthy baseline`
**Status:** COMPLETE

---

## Baseline entering Task-2

| Field | Value |
|---|---|
| `degraded` | `false` |
| `structure_complete` | `true` |
| `deliverable` | `true` |
| `product_geometry_mode` | `primary_secondary_dual_v2` |
| `product_region` | `{x:456, y:188, w:300, h:520}` |
| `product_primary_slot` | `{x:456, y:188, w:300, h:310}` |
| `product_secondary_slot` | `{x:456, y:506, w:300, h:202}` |
| gap (primary bottom → secondary top) | 8px |

---

## Step A: Lane model decision

**Decision: External right lane** (frozen)

Annotation label boxes are at x=784+, which is outside the product region's right boundary at x=456+300=756. The product region right edge never overlaps with label bounds.

Consequences:
- `product_primary_slot` and `product_secondary_slot` are sized by image area only
- `annotation_shell` is computed from label_bounds but does not affect image-slot sizing
- `annotation_owner_slot = product_primary_slot` is unchanged
- `secondary_slot_annotation_ownership = False` is unchanged

---

## Step B: Geometry decision

### Changes

| Slot | Before | After |
|---|---|---|
| `product_region` (outer shell) | `{x:456, y:188, w:300, h:520}` | `{x:456, y:188, w:300, h:540}` |
| `product_primary_slot` | `{x:456, y:188, w:300, h:310}` | **unchanged** |
| `product_secondary_slot` | `{x:456, y:506, w:300, h:202}` | `{x:456, y:518, w:300, h:210}` |
| `_PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT` | `h:520` | `h:540` |
| gap (primary bottom → secondary top) | 8px | 20px |

### Internal consistency

```
primary h + gap + secondary h = product_region h
310 + 20 + 210 = 540 ✓
```

Primary slot bottom: 188+310 = 498. Secondary slot top: 518. Gap: 20px. No overlap. ✓

---

## Files changed

| File | Change |
|---|---|
| `app/services/poster2/template_behavior.py` | `_PRODUCT_DUAL_SECONDARY_SLOT` y:506→518, h:202→210; `_PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT` h:520→540; both hero mode `product_region_h` 520→540; comments updated |
| `app/templates/specs/template_dual_v2.json` | `product_slot.h` 520→540; version 2.1.3→2.1.4 |
| `app/templates_html/slot_spec.template_dual_v2.json` | All product-region h entries 520→540 (regions, layers, layer_contracts, protected_zones, slots) |
| `app/services/poster2/template_registry.py` | `template_version` 2.1.3→2.1.4 |
| `tests/poster2/test_pipeline.py` | Updated geometry assertions; added `TestTask2FinalProductGeometry` (8 tests) |
| `tests/poster2/test_contracts.py` | Version assertion 2.1.3→2.1.4 |
| `tests/poster2/test_region_matrix.py` | `product_region.h` assertion 520→540 |

---

## Ownership unchanged

| Field | Value |
|---|---|
| `annotation_owner_slot` | `product_primary_slot` (unchanged) |
| `secondary_slot_annotation_ownership` | `False` (unchanged) |
| `geometry_frozen` | `True` |
| annotation callout anchor range | y=250/350/450, within primary [188,498] (unchanged) |
| callout 4 guard | anchor_y=550 is in secondary territory [518,728] (unchanged) |

---

## Test results

- `TestTask2FinalProductGeometry`: 8 new floor-assertion tests, all pass
- Scoped regression: 148/148 pass
  - `tests/poster2/test_pipeline.py`
  - `tests/poster2/test_contracts.py`
  - `tests/poster2/test_region_matrix.py`
  - `tests/poster2/test_slot_contracts.py`

---

## What is NOT changed

- No bottom work
- No text budget tuning
- No beautification
- No ownership rewrites
- No annotation callout positions
- No annotation label_box coordinates
- No annotation shell computation logic
