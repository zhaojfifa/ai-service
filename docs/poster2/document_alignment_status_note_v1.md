# poster2 Document Alignment Status Note v1

## Purpose

This note records the current document-path alignment decision.
It is not a product baseline and not an execution log.

## Alignment status

The formal poster2 document path is now aligned around three roles:

- `AGENTS.md` -> repository rules only
- `CLAUDE.md` -> shared state only
- `docs/poster2/README.md` -> index only

## Product / architecture / progress alignment

The aligned reading stack is:

1. `poster_generation_product_design_baseline_v1.md`
2. `template_dual_v2_architecture_business_definition.md`
3. contract / guidance documents
4. validated engineering baseline and progress docs
5. active branch execution log

This keeps:

- product essence in the product baseline
- Family A system shape in the architecture definition
- branch-local progress in the execution log

## Current document-path problems addressed

- control rules, shared state, and progress notes had been mixed together
- the README index included both formal docs and branch-local path noise
- grouped copy folders looked too similar to the formal root-level path
- process-heavy branch materials were too easy to mistake for architecture anchors

## Branch-local materials stance

Grouped copy folders and one-off materials may remain in the repository, but they are not part of the formal document path unless they are explicitly indexed from the root-level `docs/poster2/README.md`.

## Current next code PR

- product region contract upgrade

## Out of scope for this alignment pass

- product geometry changes
- annotation geometry changes
- beautification changes
- contract/runtime code work
