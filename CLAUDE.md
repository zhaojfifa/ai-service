# CLAUDE.md

## Shared State

This file is shared state only.
Repository rules live in `AGENTS.md`.
poster2 document entry and grouping live in `docs/poster2/README.md`.

## Current poster2 baseline

- Product baseline: `docs/poster2/poster_generation_product_design_baseline_v1.md`
- Family A architecture anchor: `docs/poster2/template_dual_v2_architecture_business_definition.md`
- Branch execution log: `docs/poster2/current_branch_execution_log_v1.md`

## Current established state

- PR-7 complete: product image bounds / fit authority unified under `product_policy`
- PR-8A accepted intermediate baseline: safe product-geometry widening baseline
- PR-8B complete and merged: product annotation/text runtime contract under `product_policy`
- PR-9A complete on `fix/pr9a-product-region-container`: `product_region` upgraded from image-first shell semantics to a product-owned full content container without changing geometry values
- PR-9B in progress on `fix/pr9b-product-region-annotation-text`: product annotation/text is being moved deeper into the upgraded `product_region` container path
- Separate gate-unblock work merged for:
  - Glibatree OpenAI import compatibility
  - Remaining full-suite compatibility blockers

## Current branch-log facts

- `project_poster2_baseline_2026-03-30.md` is missing in this workspace
- `docs/poster2/current_branch_execution_log_v1.md` is the working execution/state log for branch-local progress

## Current document alignment target

- `AGENTS.md` should remain rules only
- `CLAUDE.md` should remain shared state only
- `docs/poster2/README.md` should remain index only
- process-heavy / one-off / duplicated branch-local materials should not define the formal document path

## Next code priority

- current code PR: product annotation/text follow-up inside the upgraded `product_region` container
- next after PR-9B: merge-gate validation first, then return to non-product region backlog only if gate is clean
- not yet: beautification
- not yet: opportunistic geometry drift
