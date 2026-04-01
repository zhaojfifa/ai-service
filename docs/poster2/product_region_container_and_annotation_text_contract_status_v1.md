# Product Region Container And Annotation Text Contract Status v1

## Purpose

This note records the formal PR-9 closure state for `template_dual_v2` before merge-gate.

It covers:

- PR-9A: `product_region` upgraded to a full product-owned content container
- PR-9B: annotation/text moved under product-owned container truth

## PR-9A Established

`product_region` is no longer treated as a narrow image-shell interpretation.

The product-owned container path now includes:

- `product_region`
- `product_canvas_shell`
- `product_content_container`
- `product_content_container_policy = full_product_region_container`

What this means:

- runtime product container bounds are product-owned truth
- renderer shell consumption is aligned to product-owned truth
- contract evidence, renderer consumption, and diagnostics describe the same product container

## PR-9B Established

annotation/text is now a child contract of the upgraded `product_region` container.

The product-owned annotation/text path now includes:

- `product_text_shell`
- `product_text_shell_policy = product_region_text_shell`
- `product_annotation_shell`
- `annotation_items`

Active runtime truth now consumes from product-owned contract truth for:

- anchors
- connector policy
- marker policy
- label bounds
- text placement mode

Backend truth, renderer consumption, diagnostics, and Stage2 now tell the same story.

## Old Path Removed

The active old path is no longer in force:

- no external fixed `feature_region` attachment for active product annotation
- no active `template_spec_fixed` placement truth for `product_anchor_callouts`
- no active product annotation HTML routing through the external `feature_region` lane

## Frozen Unchanged

The following remain frozen through PR-9:

- PR-9A geometry values
- bottom
- header/scenario
- beautification
- broad tuning

## Remaining Step

Only one step remains for PR-9:

- merge-gate validation only
