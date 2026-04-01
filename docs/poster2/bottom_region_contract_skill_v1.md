# bottom_region_contract_skill_v1

## Status

Proposed reusable skill document.

## Why this should exist

The bottom-region path is the cleanest successful poster2 example of:

1. contract definition
2. resolver-declared behavior
3. renderer consumption
4. Stage2 evidence surfacing
5. scoped validation

It is the best candidate for a reusable implementation skill because it closed a real region with minimal architecture drift.

## Skill intent

Use the bottom-region path as the repeatable SOP for future region upgrades.

## Proposed contents

### 1. Entry conditions

- baseline and architecture docs read first
- target region identified
- contract surface named before renderer work starts

### 2. Contract checklist

- region exists as a named structural surface
- owner slots are explicit
- mandatory vs optional behavior is explicit
- collapse rules are explicit
- count rules are explicit
- emitted evidence fields are explicit

### 3. Resolver checklist

- mode names are declarative
- selected mode is emitted in resolved behavior
- count normalization happens before rendering
- fallback / degraded rules are explicit

### 4. Renderer checklist

- renderer consumes resolved behavior only
- renderer does not invent region semantics
- renderer parity notes are explicit if paths differ

### 5. Evidence checklist

- Stage2 reads backend truth only
- region_render_status is aligned with contract review
- visible counts, collapse state, and bounds are emitted where relevant

### 6. Validation checklist

- focused tests for resolver + pipeline + renderer path
- Stage2 diagnostics check when frontend/backend evidence is touched
- full suite only at merge gate

### 7. Anti-patterns to avoid

- CSS-first repair before contract closure
- renderer-local truth
- beautification used to hide contract gaps
- mixing branch-local notes into formal architecture docs

## Why bottom is the right model

The bottom region already proved the end-to-end path:

- contract-first
- stable mode resolution
- evidence-driven review
- successful merge gating

That makes it the strongest template for the upcoming product-region contract upgrade.
