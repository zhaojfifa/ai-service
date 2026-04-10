# Family A Fryer Hero Footer Blocker Removal v1

## Scope

Template A / Family A fryer path only.

This pass keeps:

- contract-first resolver truth
- header 3-column structure
- fixed-slot, product-owned annotations
- `bottom_mode = title_gallery_split`
- 4 footer items with unchanged gallery ownership

This pass removes only the last two fryer visual blockers:

1. weak product hero stage
2. over-compressed bottom detail strip

## Problem

The current fryer result was contract-safe, but the composition still failed poster fitness:

- the secondary asset auto-promoted the fryer into `primary_secondary_dual`, splitting the product stage into a top box plus bottom tray
- the annotation lane stayed too large relative to the product canvas, so the main fryer image did not read as the hero
- the footer kept the right semantic row, but the strip stayed too shallow and too dense to feel like a premium product band

## Change

### Product hero

The fryer path now uses a bounded Family-A-only hero variant instead of the generic dual split when a secondary asset exists:

- `product_layout_mode` stays `single_primary`
- `product_geometry_mode = family_a_fryer_hero_supporting_inset_v1`
- product region widens from `504` to `520`
- product canvas shell widens from `300` to `324`
- primary slot becomes `324 x 540`
- secondary asset stays present as a supporting inset at `120 x 120`
- fryer text shell shifts to `x=792, y=212, w=184, h=286`
- fryer annotation cards stay fixed-slot and product-owned, but move with the new right-lane bounds

This keeps resolver truth explicit:

- hero product first
- supporting inset second
- benefit cards third

No freeform positioning is reopened. The renderer still executes the resolver output.

### Footer strip

The fryer footer remains inside `title_gallery_split`, but uses a tighter title-to-strip balance and a taller strip:

- title band height reduces from `184` to `172`
- peer gap increases from `12` to `14`
- gallery shell height increases from `84` to `90`
- gallery item height increases from `56` to `66`
- gallery shell frame expands to `x=98, w=828, radius=24`
- 4 items remain visible in the same order and ownership model

## Intent

This is a bounded Family A control change, not a visual redesign.

The composition goal is:

- a stronger, more centered fryer hero
- a supporting inset that no longer splits the stage
- a footer row that feels breathable instead of thumbnail-like

## Non-Goals

- no Template B work
- no annotation ownership change
- no header restructure
- no gallery-count change
- no freeform layout editor behavior
