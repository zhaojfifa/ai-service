# Family A Product Annotation Text Closure v1

## Scope

Template A only.

This step closes the product callout text surface without reopening anchor placement or feature ownership.

Included:

- fixed 3-slot annotation text observability
- per-slot requested / sanitized / rendered / truncation visibility
- per-slot `char_budget` and `line_clamp`
- optimization lineage visibility for annotation wording only

Excluded:

- anchor editing
- slot-count changes
- ownership changes
- geometry changes
- Template B

## Oracle

Family A keeps:

- `product_annotation_mode = product_anchor_callouts`
- `product_annotation_owner = product_region`
- fixed annotation slot count = 3
- feature region remains delegated diagnostic only

## Closure Requirements

Stage2 must show each fixed slot directly:

1. `requested_text`
2. `sanitized_text`
3. `rendered_excerpt`
4. `truncation_applied`
5. `char_budget`
6. `line_clamp`

If optimization is enabled, Stage2 may also show optimized wording for the same slot.

Optimization may:

- rewrite wording

Optimization may not:

- add slots
- remove slots
- move anchors
- change ownership

## Acceptance

Accepted only when all hold:

1. slot count remains fixed at 3
2. each slot exposes budget and truncation observability
3. Stage2 makes compressed / clipped results operator-visible
4. feature region stays delegated, not a free right-stack editor
