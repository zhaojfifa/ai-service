# AGENTS.md

## Purpose

This file is rules-only.
It defines the repository operating rules and document-entry rules.
It is not the place for branch history, pasted execution logs, or phase progress notes.

## Required Reading Order

Before editing:

1. `README.md`
2. `docs/poster2/README.md` for poster2 work
3. `docs/poster2/poster_generation_product_design_baseline_v1.md`
4. `docs/poster2/template_dual_v2_architecture_business_definition.md`
5. Then only the task-relevant contract / stage / plan documents

Do not jump directly into renderer logic, CSS, or local tuning without re-anchoring on the docs.

## Source And Publish Rules

- `frontend/` is the Stage2 source area
- `docs/` is the published mirror
- if Stage2 behavior or presentation changes, keep `frontend/` and `docs/` aligned in the same task

## poster2 Non-Negotiables

- contract-first
- no free collage model
- renderer executes; renderer does not define template truth
- shell and content stay separated
- behavior belongs in declarative contract / resolver output
- beautification must not hide structure or control failures

## Governance Order

poster2 is governed in this order:

1. Contract
2. Validation
3. Resolver / behavior wiring
4. Renderer consumption
5. Evidence / metadata
6. Beautification

Do not reverse this order.

## Scope Rules

- keep work on the requested layer
- do not merge nearby unrelated fixes into a bounded task
- do not treat sample render quality as proof of contract correctness
- do not use CSS-only tuning to bypass contract or control work
- do not silently change published behavior without updating the matching docs / validation path

## Validation Rules

- contract/control work must be validated with metadata, ownership, counts, collapse state, bounds, or other structural evidence
- Stage2 work must validate both page-side and final-generation paths when relevant
- edited-input flows must work for edited valid inputs, not only the default sample

## Reporting Minimum

For each engineering task, report:

1. Root rules followed
2. Problem reproduced
3. Root cause found
4. Files changed
5. Layer changed
6. Validation run
7. Remaining risks

## Practical Default

When in doubt:

- read the docs first
- stay on the baseline
- keep contract before engineering
- keep behavior before beautification
- keep source and published copies aligned
