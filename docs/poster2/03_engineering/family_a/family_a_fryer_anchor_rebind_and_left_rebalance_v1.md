# Family A Fryer Hero Lift And Anchor Rebind v1

## Scope

- Template A / Family A only
- fryer-only blocker pass
- contract-first
- no Template B work
- keep header 3-column
- keep fixed-slot, product-owned annotations
- keep `bottom_mode = title_gallery_split`
- no footer redesign
- no global visual polish

## Problem

The live fryer path still showed the older fryer geometry:

- primary slot overlapped the supporting inset reserve zone
- supporting inset could not read as a clean separate detail
- fryer annotation anchors still reused stale fixed coordinates from the older slot map

That left two linked failures:

1. the hero/inset vertical relationship was structurally wrong
2. slot 1 no longer pointed cleanly to the visible fryer hero body

## Change

## Change

### Phase 1: hero lift and reserve clearance

- fryer product family stays in the current live x-lane
- primary hero slot moves upward from `y=214` to `y=192`
- primary hero height reduces from `496` to `384`
- supporting inset remains at `x=486, y=596, w=104, h=104`

This creates a clear vertical gap:

- primary bottom = `192 + 384 = 576`
- secondary top = `596`
- separation = `20px`

### Phase 2: anchor rebind

- fryer annotation label cards remain in the fixed right lane
- fryer anchor coordinates no longer copy `template_spec` / stale fryer-fixed values
- fryer anchor positions are now derived from the active primary hero stage's visible contain-fitted product box
- `positions_source` now reports `family_a_fryer_visible_box_derived`

This keeps annotation ownership unchanged:

- owner remains `product_region`
- owner slot remains `product_primary_slot`
- fixed 3 slots remain fixed 3 slots

## Intent

The result should first fix the hero/inset structural separation, then restore semantic anchoring from the real visible hero box without reopening broader Family A layout work.
