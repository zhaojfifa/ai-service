# Family A Product Annotation Shell Micro-Structure v1

## Scope

Template A / Family A only.

This pass keeps:

- fixed 3 annotation slots
- product-owned annotation responsibility
- existing anchor positions
- renderer-executes-truth ownership flow

It only adds a bounded fryer-only variant to the fixed product text shell so commercial benefit phrases stay readable.

## Change

The fryer Family A path now resolves through a bounded right-lane variant under `product_policy`:

- product region width grows from `504` to `512`
- product text shell grows from `176x276` at `x=784,y=216` to `192x286` at `x=776,y=212`
- fixed label bounds grow from `176x76` to `192x82` for all 3 slots
- product slot contract resolves `char_budget = 54` with `line_clamp = 3` for the 3-slot fryer state
- copy-optimization fit pressure is raised so short commercial phrases like `Precise Thermostat Control` stay on the sanitized path
- both Pillow and structured HTML now consume the same fryer variant bounds from `product_policy`

## Intent

The goal is not to restyle Family A.

The goal is to stop short commercial benefit phrases from reading like emergency labels while preserving:

- slot identity
- slot bounds
- product ownership
- fixed-anchor diagnostics

## Non-Goals

- no freeform positioning
- no ownership changes
- no whole-template redesign
- no Template B adoption
