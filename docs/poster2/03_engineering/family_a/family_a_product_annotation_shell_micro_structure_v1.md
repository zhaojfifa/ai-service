# Family A Product Annotation Shell Micro-Structure v1

## Scope

Template A / Family A only.

This pass keeps:

- fixed 3 annotation slots
- product-owned annotation responsibility
- existing anchor positions
- existing outer geometry

It only increases the usable text capacity of the fixed product benefit cards.

## Change

The annotation shell remains `176x76` per fixed slot, but the text consumption layer is loosened inside that shell:

- annotation char budget raised to `56 / 52 / 48` for `1 / 2 / 3` visible slots
- product-anchor callout delegated feature diagnostics use the same raised budgets
- card inner padding tightened from `10/14` to `8/12`
- annotation line-height tightened to `1.24`

## Intent

The goal is not to restyle Family A.

The goal is to stop short commercial benefit phrases from reading cramped in the fixed-width right-side cards while preserving:

- slot identity
- slot bounds
- product ownership
- fixed-anchor diagnostics

## Non-Goals

- no geometry expansion
- no ownership changes
- no freeform product text layout
- no Template B adoption
