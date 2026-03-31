# Product Region Final Geometry Status v1

**Date:** 2026-03-31  
**Scope:** Task-2 — Finalize product-region geometry and freeze it again

---

## Goal

Make one final contract-level geometry decision for `product_region` now that text ownership is already independent.

This task does not change:
- annotation ownership truth
- annotation owner slot
- secondary-slot annotation ownership policy
- bottom behavior
- beautification

---

## Final Decision

The product region is widened rightward from `300px` to `320px`.

Final frozen geometry:

- `product_region = {x:456, y:188, w:320, h:520}`
- `product_primary_slot = {x:456, y:188, w:320, h:310}`
- `product_secondary_slot = {x:456, y:506, w:320, h:202}`

Geometry mode versions after this decision:

- single-image: `single_primary_v2`
- dual-image: `primary_secondary_dual_v3`

---

## Why This Geometry Was Chosen

- It improves alignment with the header/banner envelope by letting the product mass extend further right.
- It does not require changing annotation ownership.
- It preserves a clear handoff to annotation text:
  - product right edge = `456 + 320 = 776`
  - annotation label boxes begin at `x = 784`
  - remaining gap = `8px`

This preserves the current product-annotation responsibility split.

---

## Ownership Truth Preserved

These stay frozen:

- `product_annotation_owner = product_region`
- `annotation_owner_slot = product_primary_slot`
- `secondary_slot_annotation_ownership = false`

Secondary product imagery remains a display-only surface, not an annotation owner.

---

## Runtime Proof

Fresh local HTTP runtime verification:

- trace: `6d73e12b-614d-42c6-8eab-4b1ca2601900`
- `degraded = false`
- `structure_complete = true`
- `deliverable = true`
- `product_layout_mode = primary_secondary_dual`
- `product_geometry_mode = primary_secondary_dual_v3`
- `product_primary_slot = {x:456, y:188, w:320, h:310}`
- `product_secondary_slot = {x:456, y:506, w:320, h:202}`
- `annotation_owner_slot = product_primary_slot`
- `secondary_slot_annotation_ownership = false`

---

## Validation

Focused Task-2 gate:

```bash
python -m pytest tests/poster2/test_pipeline.py -q -k 'product_layout_contract or product_owner_surface_freeze or product_region or annotation_owner_slot or secondary_slot_annotation_ownership or product_geometry_mode'
```

Result:

- `3 passed`

---

## Frozen After This Task

The following are now re-frozen:

- `product_region` bounds
- `product_primary_slot` bounds
- `product_secondary_slot` bounds
- `product_geometry_mode`
- `annotation_owner_slot`
- `secondary_slot_annotation_ownership`

Any later work should be delivery/capacity tuning only, not geometry redesign.
