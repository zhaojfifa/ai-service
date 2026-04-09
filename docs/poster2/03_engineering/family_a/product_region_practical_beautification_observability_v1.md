# Family A Product Region Practical Beautification And Observability v1

## Scope

This document defines the first bounded practical-closure step for Family A under the repaired freeze baseline.

Scope is intentionally narrow:

- Template A only
- product region only
- no geometry changes
- no ownership changes
- no control-truth changes
- no Template B work

## Objective

Replace blind product-region visual tuning with a practical, observable closure loop:

1. polish the Family A product shell
2. polish annotation shell / leader line / marker
3. expose product-region runtime truth in operator diagnostics
4. keep renderer as truth consumer, not truth owner

## Product Region Runtime Truth To Surface

The UI and validation path must surface the same backend truth already resolved by Family A:

- `product_layout_mode`
- `secondary_product_mode`
- `product_annotation_owner`
- `visible_annotation_count`

These fields are observability outputs, not new control sources.

## Beautification Boundaries

Allowed:

- shell surface / outline / glow refinement
- annotation card surface / border / shadow refinement
- leader line polish
- marker polish
- product-region diagnostics chips in Stage2

Forbidden:

- product-region geometry drift
- annotation ownership drift
- feature-to-product responsibility remap
- Family B token adoption
- Gemini-driven layout or control changes

## Consumption Path

Family A runtime remains the oracle.
The practical closure step consumes Family A truth through:

- Family A beautification skill: `family_a_beautification_freeze_pack_v1`
- Template A resolver/runtime behavior output
- pipeline metadata / contract review
- Stage2 diagnostics renderers

## Acceptance

The product-region practical closure is accepted only when all of the following hold:

1. Family A image semantics remain frozen
2. product shell / annotation polish lands without geometry drift
3. Stage2 surfaces `product_layout_mode`
4. Stage2 surfaces `secondary_product_mode`
5. Stage2 surfaces `product_annotation_owner`
6. Stage2 surfaces `visible_annotation_count`
7. Family A accepted output / evidence keys remain unchanged
