# Family A Single-Primary Support Surface v1

## Scope

- Template A / Family A fryer only
- contract-first optional surface under `product_region`
- no Template B work
- no product ownership change
- no annotation slot logic change
- no bottom family or bottom gallery/caption path change

## Contract

`product_region` now supports an optional `product_support_surface`.

It renders only when all runtime conditions hold:

- `product_layout_mode = single_primary`
- `secondary_product_mode = inset_hidden_no_reserve`
- `product_secondary_slot_rendered = false`
- Family A fryer variant is active
- bottom gallery item 1 has a resolved asset

Source policy:

- first choice: `gallery_images[0]`
- if unavailable: collapse, no placeholder

Caption policy:

- first choice: `gallery_caption_slot_1.caption_text`
- caption is optional, short, and weak

Presentation policy:

- bounded inside the lower product canvas support zone
- left/center of the lower support zone
- outside the annotation lane
- outside the title band
- light shell, light shadow, subordinate scale

## Evidence

The product contract review exposes:

- `product_support_surface_rendered`
- `product_support_surface_source`
- `product_support_surface_mode`
- `product_support_surface_bounds`
- `product_support_surface_caption_text`

The layer review exposes `product_support_surface_layer` with rendered state, source binding, reason code, and bounds.

## Non-Goals

- no second hero
- no secondary slot ownership change
- no annotation ownership change
- no bottom gallery/caption behavior change
- no new operator input
