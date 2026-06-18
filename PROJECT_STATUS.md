# PROJECT_STATUS

Purpose: Top-level project status + documentation-governance pointer.
Status: active.
Scope: Repo-level status and governance pointers. Not a product/architecture doc.
Source dependencies: docs/DOCS_INDEX_AND_ROUTER.md; docs/poster2/README.md; docs/poster2/current_branch_execution_log_v1.md.
Owner gate: Owner approval of the docs router to resume PR-1.
Next action: Owner reviews the docs router pilot; if approved, resume PR-1 under this governance.

---

## Documentation governance: ACTIVE (pilot — submitted for Owner review)

- **Active docs router:** [`docs/DOCS_INDEX_AND_ROUTER.md`](docs/DOCS_INDEX_AND_ROUTER.md)
- **Docs check script:** [`scripts/check_docs_router.py`](scripts/check_docs_router.py) — run
  `python3 scripts/check_docs_router.py --all`
- **POSTER2 formal index:** [`docs/poster2/README.md`](docs/poster2/README.md) (unchanged; remains authoritative
  for poster2 reading order)
- **POSTER2 active branch state:** [`docs/poster2/current_branch_execution_log_v1.md`](docs/poster2/current_branch_execution_log_v1.md)

## Implementation status

- **PR-1 implementation: PAUSED** until Owner approves this documentation governance.
- Current plan of record: [`docs/poster2/cuistance_commercial_trial_backend_alignment_plan_v1.md`](docs/poster2/cuistance_commercial_trial_backend_alignment_plan_v1.md)
  (PR-0…PR-4).
- Approved interaction baseline: [`docs/poster2/ui_mockups/cuistance_commercial_trial_v1/`](docs/poster2/ui_mockups/cuistance_commercial_trial_v1/)
  (static UI Mockup V2).

## Source hierarchy (authority order)

1. `AGENTS.md` (rules) → 2. `CLAUDE.md` (shared state) → 3. `docs/poster2/README.md` (POSTER2 formal index) →
4. `docs/poster2/current_branch_execution_log_v1.md` (active branch state) →
5. `docs/DOCS_INDEX_AND_ROUTER.md` (repo-level routing/governance) → 6. individual formal docs.

## Notes

- This task changed **no product code** (no `app/**`, no `frontend/**`, no renderer, no email behavior, no
  mockup production files, no deployment config).
- The `docs-index-router` skill was **not installed/invokable** here; the router + script were authored from the
  task's explicit specification and adapted to the real repo layout (recorded in the router).
