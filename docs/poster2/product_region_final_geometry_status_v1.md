# Product Region Final Geometry Status v1

**Date:** 2026-03-31  
**Scope:** Task-2 — Finalize product-region geometry and freeze it again

---

## Goal

Make one final contract-level geometry decision for `product_region` now that text ownership is already independent.

Read before implementation:
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `project_poster2_baseline_2026-03-30.md` was requested but is not present in the repository
- `docs/poster2/README.md`

This task does not change:
- annotation ownership truth
- annotation owner slot
- secondary-slot annotation ownership policy
- bottom behavior
- beautification

---

## Final Decision

The previous product shell was too conservative. The final decision is to replace it with a wider and slightly taller frozen geometry that gives the secondary card enough room and no longer lets annotation label bounds constrain image-slot sizing.

Final frozen geometry:

- `product_region = {x:456, y:188, w:344, h:544}`
- `product_primary_slot = {x:456, y:188, w:344, h:320}`
- `product_secondary_slot = {x:456, y:524, w:344, h:208}`

Geometry mode versions after this decision:

- single-image: `single_primary_v2`
- dual-image: `primary_secondary_dual_v3`

---

## Why This Geometry Was Chosen

- It improves alignment with the header/banner envelope by letting the product mass extend further right.
- It enlarges the pink product shell area without changing ownership truth.
- It increases the vertical separation between the primary and secondary cards.
- It enlarges the white secondary card area so it no longer feels cramped.
- Annotation label bounds are explicitly excluded from image-slot sizing logic.

This preserves the current product-annotation responsibility split.

---

## Ownership Truth Preserved

These stay frozen:

- `product_annotation_owner = product_region`
- `annotation_owner_slot = product_primary_slot`
- `secondary_slot_annotation_ownership = false`

Secondary product imagery remains a display-only surface, not an annotation owner.
Annotation label bounds remain evidence surfaces only, not sizing inputs for the product image slots.

---

## Runtime Proof

Fresh local HTTP runtime verification:

- trace: `79d40822-1cf6-4c3b-a880-efa33d9d25bf`
- `degraded = false`
- `structure_complete = true`
- `deliverable = true`
- `product_layout_mode = primary_secondary_dual`
- `product_geometry_mode = primary_secondary_dual_v3`
- `product_geometry_mode_reason = dual_image_geometry_v3_frozen_final_bounds`
- `product_region = {x:456, y:188, w:344, h:544}`
- `product_primary_slot = {x:456, y:188, w:344, h:320}`
- `product_secondary_slot = {x:456, y:524, w:344, h:208}`
- `annotation_owner_slot = product_primary_slot`
- `secondary_slot_annotation_ownership = false`

---

## Validation

Focused Task-2 gate:

```bash
python -m pytest tests/poster2/test_pipeline.py -q -k 'product_layout_contract or product_owner_surface_freeze or product_region or annotation_owner_slot or secondary_slot_annotation_ownership or product_geometry_mode'
python -m pytest tests/poster2/test_renderer.py -q -k 'product_secondary or product_slot or product_region or dual'
```

Result:

- `3 passed`
- `1 passed`

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
