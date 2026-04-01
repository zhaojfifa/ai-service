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

- Read first for this restart pass:
  - `AGENTS.md`
  - `CLAUDE.md`
  - `docs/poster2/README.md`
  - `docs/poster2/current_branch_execution_log_v1.md`
  - `docs/poster2/poster_generation_product_design_baseline_v1.md`
  - `docs/poster2/template_dual_v2_architecture_business_definition.md`
  - `docs/poster2/template_dual_v2_structural_rebuild_baseline_v1.md`
- PR-7 complete: product image bounds / fit authority unified under `product_policy`
- PR-8A accepted intermediate baseline: safe product-geometry widening baseline
- PR-8B complete and merged: product annotation/text runtime contract under `product_policy`
- Restart path established on `fix/pra-product-outer-shell`: code path rebased to `fix/pr7-product-truth-only` while keeping `AGENTS.md`, `CLAUDE.md`, `docs/poster2/README.md`, and `docs/poster2/current_branch_execution_log_v1.md` aligned to current main
- PR-A complete on `fix/pra-product-outer-shell`: add the visible enlarged `product_region` outer shell as the real product base plate and keep `product_canvas_shell_layer` separate
- PR-A does not add product text shell behavior; annotation text path remains on the old fixed lane for now by design
- Separate gate-unblock work merged for:
  - Glibatree OpenAI import compatibility
  - Remaining full-suite compatibility blockers

## Current branch-log facts

- `project_poster2_baseline_2026-03-30.md` is missing in this workspace
- `docs/poster2/current_branch_execution_log_v1.md` is the working execution/state log for branch-local progress
- PR-A contract truth changed:
  - `product_region` / visible `product_card_shell_layer` widen to `{x:456,y:188,w:472,h:540}`
  - `product_canvas_shell_layer` stays a separate image shell at `{x:456,y:188,w:300,h:540}`
  - product image continues to anchor inside `product_canvas_shell_layer`
- PR-A intentionally leaves untouched:
  - product text shell work
  - bottom
  - header/scenario
  - beautification
  - broad tuning

## Current document alignment target

- `AGENTS.md` should remain rules only
- `CLAUDE.md` should remain shared state only
- `docs/poster2/README.md` should remain index only
- process-heavy / one-off / duplicated branch-local materials should not define the formal document path

## Next code priority

- current priority: PR-B only
- next after PR-B: PR-C only for capacity / label bounds / clamp / connector tuning
- not yet: beautification
- not yet: opportunistic geometry drift
