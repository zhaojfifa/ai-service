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

- Read first for this PR-9C pass:
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
- PR-9A complete on `fix/pr9a-product-region-container`: `product_region` upgraded from image-first shell semantics to a product-owned full content container without changing geometry values
- PR-9B is not an acceptable merge result: it moved annotation/text under product ownership but kept the outer product container too narrow, so text competed with image-shell width
- PR-9C in progress on `fix/pr9c-product-region-boundary`: boundary correction widens `product_region` / `product_content_container` into a true outer container while keeping image-owned surfaces frozen
- Separate gate-unblock work merged for:
  - Glibatree OpenAI import compatibility
  - Remaining full-suite compatibility blockers

## Current branch-log facts

- `project_poster2_baseline_2026-03-30.md` is missing in this workspace
- `docs/poster2/current_branch_execution_log_v1.md` is the working execution/state log for branch-local progress
- PR-9C contract truth changed:
  - `product_region` / `product_content_container` widened to contain both the image shell and product text shell
  - `product_canvas_shell_layer`, `product_primary_slot`, and `product_secondary_slot` remain image-owned surfaces at frozen width
  - `product_text_shell`, `product_annotation_shell`, and `annotation_items` now consume the widened outer-container model instead of competing for the narrow image shell
- PR-9C old active path removed:
  - no active product annotation path that treats the narrow `320px` image shell as the annotation/text container

## Current document alignment target

- `AGENTS.md` should remain rules only
- `CLAUDE.md` should remain shared state only
- `docs/poster2/README.md` should remain index only
- process-heavy / one-off / duplicated branch-local materials should not define the formal document path

## Next code priority

- current priority: complete PR-9C only, then run merge-gate only
- next after PR-9C: merge-gate validation only; do not point-fix label coordinates or reopen other regions
- not yet: beautification
- not yet: opportunistic geometry drift
