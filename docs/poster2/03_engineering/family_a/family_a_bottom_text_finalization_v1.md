# Family A Bottom Text Finalization v1

## Scope

Template A / Family A only.

This pass keeps:

- `bottom_mode = title_gallery_split`
- 4-item strip
- existing bottom-region ownership
- existing Family A bottom system

It closes the remaining fryer bottom blockers only: final bottom copy and strip breathing.

## Change

The subtitle path now resolves in this order:

1. requested text
2. hygiene-only sanitize
3. cleanup
4. direct render when the actual bottom budget can carry the requested fryer sentence
5. optimized / accepted candidate when operator applies optimization
6. rendered text

For the fryer commercial default, the rendered truth is now the required full sentence:

`Fast heating, precise control, and durable stainless steel construction for everyday commercial use.`

If optimization produces a compact subtitle candidate and the operator accepts it, the rendered output switches to the accepted optimized text and `rendered_text_source` follows that decision.

The same bounded pass also rebalances the bottom strip for the fryer 4-item state:

- title band height increases from `176` to `184`
- peer gap increases from `0` to `12`
- strip distribution changes from `dense_quad` to `dense_quad_detail_row`
- item geometry changes from `188x60` to `180x56`
- gallery order is normalized to `Single Tank / Dual Tank / Basket Detail / Lid Detail`

## Intent

The bottom should no longer read as generic kitchen marketing copy with a crowded thumbnail row.

This is a render-source closure change, not a bottom redesign.

## Non-Goals

- no new bottom layout family
- no gallery ownership change
- no strip removal
- no Template B work
