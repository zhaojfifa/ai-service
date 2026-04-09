# Family Isolation Rules v1

This document defines the hard anti-crossline rules for poster2 template families.

These rules are formal engineering baseline, not branch-local notes.

## Core Rules

1. one family, one evidence schema
2. one family, one render material builder
3. one family, one selector registry
4. family branch must be explicit at every boundary
5. shared code may share tools, not semantics
6. no family-cross acceptance wording without regression gate
7. beautification cannot cross family boundaries
8. DOM existence is not final truth by itself

## Boundary Requirements

### Contract

- Family A and Family B contract surfaces must remain independently declared
- a family must not inherit another family's ownership semantics through renderer defaults
- geometry truth must stay family-scoped

### Validation And Quality Guard

- whitelist required/allowed evidence keys per family
- reject or strip cross-family evidence keys before manifest output
- parity reviews must only run for the family that defines them

### Resolver / Behavior

- family mode selection must be explicit from `template_id` / registry metadata
- behavior output must not multiplex unrelated family semantics into one shared mode surface

### Renderer Consumption

- family-specific render asset assembly must be explicit
- family-specific HTML replacement/material assembly must be explicit
- shared renderer helpers may only provide:
  - geometry math
  - text budget helpers
  - browser lifecycle and screenshot helpers
  - artifact and timing helpers

### Evidence / Metadata

- Family A payload must not emit Family B-only evidence/parity keys
- Family B payload must not emit Family A-only semantics or region keys
- backend remains the source of truth for diagnostics

### Beautification

- beautification is downstream of contract, validation, resolver, renderer, and evidence
- visual tuning must never be used to hide family routing or ownership drift

## Required Test Gates

The repo must keep these gates green:

1. manifest key whitelist tests
2. cross-family evidence absence tests
3. family routing tests
4. canonical Family A / Family B smoke regression
5. frontend/docs sync tests

## Current Family-Specific Expectations

### Family A

- `template_dual_v2`
- scenario + product peer shell remains Family A-owned
- header / feature / title-band / gallery semantics remain Family A-owned
- Template B parity and product-sheet evidence keys must not appear

### Family B

- `template_product_sheet_v1`
- vertical five-region product-sheet stack remains Family B-owned
- top-copy / materials / product-hero / description semantics remain Family B-owned
- Family A bottom/title-band/gallery semantics must not appear

## Enforcement Intent

If a future PR attempts to:

- share a universal evidence schema across families
- route both families through one semantic render-material builder
- add acceptance wording like "works for both families" without regression gates

that PR should be treated as incomplete until explicit family isolation tests are added or updated.
