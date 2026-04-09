# Family A Bottom Text Finalization v1

## Scope

Template A / Family A only.

This pass keeps:

- `bottom_mode = title_gallery_split`
- existing bottom-region ownership
- existing title-band / gallery strip geometry

It only repairs the subtitle text lifecycle so the rendered support copy becomes product-grade.

## Change

The subtitle path now resolves in this order:

1. requested text
2. hygiene-only sanitize
3. cleanup
4. product-grade fit rewrite when needed
5. optimized / accepted candidate when operator applies optimization
6. rendered text

For the fryer commercial sentence, the fit rewrite now preserves the three product benefits in a complete short form:

`Fast heating, precise control, and stainless steel durability.`

## Intent

The bottom subtitle should no longer end in a clipped fragment or an unfinished keyword chain.

This is a render-source closure change, not a bottom redesign.

## Non-Goals

- no new bottom layout family
- no gallery ownership change
- no Template B work
