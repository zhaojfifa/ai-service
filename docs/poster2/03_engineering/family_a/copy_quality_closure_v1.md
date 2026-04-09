# Family A Copy Quality Closure v1

## Scope

Template A only.

This step closes practical copy quality for the Family A live path.

Included:

- subtitle quality improvement under the existing bottom support-copy budget
- fixed 3-slot product annotation quality improvement under the existing annotation budget
- default suggestion-first operator path for copy optimization
- rendered candidate comparison in Stage2

Excluded:

- Template B
- geometry changes
- ownership changes
- control-truth changes
- renderer-defined truth

## Oracle

Family A runtime remains the oracle:

- `template_id = template_dual_v2`
- `product_annotation_mode = product_anchor_callouts`
- `product_annotation_owner = product_region`
- subtitle ownership remains under the existing bottom/title-band contract

Gemini or deterministic optimization may improve wording only.

## Quality Goals

1. Subtitle should fit the real Family A 2-line support-copy path more often.
2. Annotation text should preserve original meaning better than generic collapse such as `Smart controls`.
3. UI should treat `suggest` as the main operator path, while keeping `off` available as an explicit override.
4. Final image, metadata, and copy-optimization review must stay consistent.

## Quality Rules

- optimize only when text is over budget or obviously redundant
- prioritize subtitle and product annotation over title
- keep fixed annotation slot count = 3
- no slot movement, no ownership drift, no mode drift

## Practical Closure

This step introduces:

- budget-aware deterministic subtitle shortening
- budget-aware deterministic annotation shortening
- stronger phrase-preserving rewrites for verbose sell points
- suggest-first Stage2 operator path

## Acceptance

Accepted only when all hold:

1. subtitle optimization improves candidate completeness under the existing budget
2. annotation slot 3 no longer collapses to a weak generic phrase when a better short form is available
3. `copy_optimization_review` shows the improved candidate
4. accepted optimization can flow into rendered output without changing control truth
