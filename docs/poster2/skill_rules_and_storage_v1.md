# poster2 Skill Rules And Storage v1

## Purpose

This document defines the formal rules and storage baseline for poster2 shared skills.

The skill system exists to extract already-verified family-scoped runtime capability into
stable reusable units.

It does not authorize redesign.
It does not merge template families.
It does not let renderer code define template truth.

## Skill Positioning

A poster2 skill is a family-scoped reusable runtime unit derived from accepted contract and
behavior truth.

A skill may package:

- family-scoped structure helpers
- family-scoped control helpers
- bounded beautification packs
- family-scoped evidence helpers

A skill must always execute previously accepted truth.
It must not invent new truth through renderer-side heuristics.

## Four Skill Layers

### Structure

Structure skills define family-scoped reusable surfaces for:

- region matrix
- slot contract
- structure surface assembly
- family-specific render material entry points

Structure skills must preserve:

- region order
- slot ownership
- geometry truth

### Control

Control skills define reusable family-scoped behavior surfaces for:

- mode families
- policy surfaces
- request-state canonicalization
- family-scoped resolver helpers

Control skills must preserve:

- accepted behavior modes
- ownership rules
- mode remap rules
- collapse truth

### Beautification

Beautification skills define bounded visual packs only after structure and control are accepted.

Beautification skills may affect only:

- shell_surface
- shell_border
- shell_shadow
- accent_tone
- text_emphasis

Beautification skills must not change:

- region geometry
- slot ownership
- behavior truth
- deliverability semantics

### Evidence

Evidence skills define stable family-scoped evidence and diagnostics helpers for:

- region bounds
- slot bounds
- visible-truth surfaces
- contract review surfaces
- parity-friendly diagnostics

Evidence skills must preserve:

- family whitelist rules
- backend-owned diagnostics truth
- no cross-family residue

## Registration Fields

Every shared skill must register the following fields:

- `skill_id`
- `display_name`
- `family_id`
- `layer`
- `anchor_template_id`
- `status`
- `entry_module`
- `doc_path`
- `tests_path`
- `fixtures_path`
- `acceptance_gate`
- `forbidden_mutations`

Recommended optional fields:

- `depends_on`
- `notes`

## Frozen Admission Conditions

A skill may be registered as an anchored shared skill only when all of the following are true:

1. the source family runtime is already accepted at the contract/control layer
2. the source template has a current-good canonical sample
3. the source family has accepted output/evidence keys
4. cross-family residue tests are already passing
5. the extracted surface is family-scoped and does not merge A/B semantics
6. the skill can be validated without reopening unrelated product scope

## Forbidden Mutations

Shared-skill work must not:

- rewrite template families into one generic widget runtime
- merge Family A and Family B semantics into one builder with implicit branching
- let renderer define contract truth
- change geometry as a shortcut for behavior or evidence problems
- change ownership while claiming a structure-only extraction
- reopen frozen bottom/product annotation logic during beautification work
- register a skill without tests, fixture path, and doc path
- use DOM existence alone as final truth

## Acceptance Checks

Every skill registration and extraction must pass:

1. family-scoped registry validation
2. fixture-backed registration checks
3. family whitelist / no cross-family residue checks
4. renderer / pipeline regression checks relevant to the anchored family
5. docs storage path checks

For beautification skills, also require:

6. no geometry delta
7. no ownership delta
8. no behavior-mode delta

## Formal Storage Rules

### Docs

Formal skill rules and status documents live under:

- `docs/poster2/`

This document is the formal skill-rules baseline.

`docs/poster2/README.md` may index formal skill docs, but must not carry branch process logs.

### Code

Shared skill code lives under:

- `app/services/poster2/skills/structure/`
- `app/services/poster2/skills/control/`
- `app/services/poster2/skills/beautification/`
- `app/services/poster2/skills/evidence/`
- `app/services/poster2/skills/registry.py`

`registry.py` is the formal registration source for shared skills.

### Tests

Shared skill tests live under:

- `tests/poster2/skills/`

They must cover:

- registration validity
- family scope
- storage-path validity
- fixture consistency

### Fixtures

Shared skill fixtures live under:

- `tests/poster2/fixtures/skills/`

Fixtures must define:

- expected registry entries
- family whitelist expectations
- any accepted status metadata needed for extraction gates

## Initial Scope Baseline

The first registration wave is Family A anchored only.

This means:

- no Template B shared-skill extraction yet
- no cross-family generalized skill surface yet
- no widening of scope during the registration-baseline step

Family B may only be added after the Family A anchored extraction path is proven stable.
