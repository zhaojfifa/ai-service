# DOCS_INDEX_AND_ROUTER

Purpose: Repository-level documentation governance + routing layer.
Status: ACTIVE (pilot — submitted for Owner review).
Scope: Routing/governance only. Does NOT replace `docs/poster2/README.md` (the formal POSTER2 index).
Source dependencies: AGENTS.md; CLAUDE.md; README.md; docs/poster2/README.md; docs/poster2/current_branch_execution_log_v1.md.
Owner gate: Owner approval to keep this router active and to resume PR-1.
Next action: Owner reviews; if approved, implementation (PR-1) may resume under this governance.

> Skill note: this task invoked the `docs-index-router` skill, which is **not installed/invokable** in this
> environment (absent from the Skill list and from `~/.claude/skills`). This router + `scripts/check_docs_router.py`
> were authored from the task's explicit specification (used as the skill template) and adapted to the real repo
> layout. No product code was touched.

---

## 1. Purpose

POSTER2 / CUISTANCE has accumulated a large, evolving documentation surface (253 markdown files under
`docs/poster2/` plus historical root-level docs). This file is a **canonical routing layer**: it tells any
reader (human or agent) **where the truth lives** and **which index governs which area**, so later migration,
extraction, and engineering handoff do not inherit drifted/garbage context.

It is **governance and routing only** — it does not restate product architecture, does not move/delete files,
and does not override the formal POSTER2 index.

## 2. Core conclusion

- **POSTER2 truth is already indexed** by `docs/poster2/README.md` (formal index) + governed by `AGENTS.md`
  (rules) and `CLAUDE.md` (shared state). This router **points to** that index; it does not replace it.
- **The drift is at the edges**: legacy root-level markdown and historical `docs/poster2/` material that is
  superseded or duplicated. Those are marked **reference-only / archive-later** here — **not** physically moved.
- **Repository documentation governance is now centralized** through this router + `PROJECT_STATUS.md` +
  `scripts/check_docs_router.py`. **PR-1 implementation stays paused** until Owner approves this governance.

## 3. Source hierarchy (authority order)

1. **`AGENTS.md`** — repository operating rules (rules only).
2. **`CLAUDE.md`** — shared state (shared state only).
3. **`docs/poster2/README.md`** — formal POSTER2 index + reading order (for all poster2 work).
4. **`docs/poster2/current_branch_execution_log_v1.md`** — active POSTER2 branch state log.
5. **`docs/DOCS_INDEX_AND_ROUTER.md`** (this file) — repo-level routing/governance (routes you TO the right
   index; does not override poster2 truth).
6. **Individual formal docs** under the layered `docs/poster2/` directories.

Rule: for any conflict, the **higher** item wins. For poster2 content specifically, `docs/poster2/README.md`
is authoritative over this router.

## 4. Current repository documentation map (as-is, observed)

- **Root governance / index** (authoritative): `AGENTS.md`, `CLAUDE.md`, `README.md`, `PROJECT_STATUS.md`,
  `PROJECT_INDEX.md`, `docs/DOCS_INDEX_AND_ROUTER.md` (this file).
- **Root legacy / one-off** (reference-only · archive-later, **not moved**): `APPLY_EDIT_ENABLE_PATCH.md`,
  `DEPLOYMENT_CONFIG_TRUTH.md`, `KITPOSTER_EDIT_QUALITY_AUDIT.md`, `POST_RECOVERY_AUDIT.md`,
  `POSTER_EDIT_PATH_REVIEW.md`, `SAFE_PATCH_PLAN.md`, `task4_handoff.md`, `VERIFICATION_CHECKLIST.md`.
- **`docs/` (mixed surface):** `docs/` is **also the published frontend mirror** (per `AGENTS.md`): it contains
  `app.js`, `stage2.html`, `ops_campaign.*`, `styles.css`, etc. — **those are mirror artifacts, NOT
  documentation** and are out of this router's scope. Documentation lives in the subdirectories below.
- **`docs/poster2/`** — the **formal POSTER2 corpus** (253 md), governed by `docs/poster2/README.md`. Layered
  dirs: `01_product/`, `02_architecture/`, `03_engineering/`, `04_skills/`, `05_validation/`, `99_archive/`
  (plus **legacy** grouped dirs `01_architecture/`, `02_engineering/`, `execution/` that are no longer the
  formal path — reference-only).
- **Other `docs/` doc dirs** (legacy/auxiliary, reference-only): `docs/architecture/`, `docs/execution/`,
  `docs/harness-x/`, `docs/prompts/`, `docs/templates/`, `docs/kit1.1_*.md`, `docs/review-render-recovery.md`.

## 5. POSTER2 source-of-truth path

Do **not** duplicate the poster2 reading order here. The single source is **`docs/poster2/README.md`**
("Entry Order" + "Formal Document Path"). Canonical anchors it points to:

- `docs/poster2/poster_generation_product_design_baseline_v1.md` (product baseline)
- `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md` (Family A architecture anchor)
- `docs/poster2/02_architecture/template_family_*` / `renderer_routing_*` / `quality_guard_*` / `family_isolation_*`
- `docs/poster2/04_skills/skill_rules_and_storage_v1.md`
- `docs/poster2/05_validation/family_a_four_layer_verification_matrix_v1.md`

> **Path correction (honest record):** the task listed
> `docs/poster2/template_dual_v2_architecture_business_definition.md` (poster2 root) — that path **does not
> exist**. The real formal location is `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
> (a **legacy duplicate** also exists at `docs/poster2/01_architecture/…`, reference-only). The missing root
> path is **not** treated as architecture truth.

## 6. CUISTANCE commercial trial — active docs (current phase)

The current product line. Routed here for fast handoff (all under `docs/poster2/`, poster2-governed):

| Doc | Role |
|---|---|
| `cuistance_commercial_trial_product_design_v1.md` | Platform blueprint (long-term positioning) |
| `cuistance_commercial_trial_v1_multi_role_design_review.md` | Multi-role design review (scoped v1) |
| `cuistance_commercial_trial_branch_aware_heavy_engineering_design_v1.md` | Branch-aware engineering design |
| `cuistance_commercial_trial_ui_flow_design_v1.md` | Approved 3-step UI flow + semantics |
| `cuistance_commercial_trial_claude_design_ui_v1.md` | Commercial visual UI design (submitted) |
| `cuistance_commercial_trial_backend_alignment_plan_v1.md` | **Backend alignment + PR-0…PR-4 plan (current)** |
| `ui_mockups/cuistance_commercial_trial_v1/` | **Approved static UI Mockup V2** (index interaction baseline) |

Current active head-of-line for engineering = the **backend alignment plan** + the **approved Mockup V2**.

## 7. Engineering-state records

- **Active branch state:** `docs/poster2/current_branch_execution_log_v1.md` (the live working log).
- **Shared state:** `CLAUDE.md` (current poster2 baseline / established state).
- **Engineering status docs:** `docs/poster2/03_engineering/**` and `docs/poster2/05_validation/**`.
- This router does **not** carry branch history or progress notes — those belong in the execution log.

## 8. Current-phase artifacts

- Approved interaction baseline: `docs/poster2/ui_mockups/cuistance_commercial_trial_v1/` (HTML/CSS/real assets).
- Current plan of record: `docs/poster2/cuistance_commercial_trial_backend_alignment_plan_v1.md`.
- Governance pilot (this task): `docs/DOCS_INDEX_AND_ROUTER.md`, `scripts/check_docs_router.py`,
  `PROJECT_STATUS.md`.

## 9. Directory router

| If you need… | Go to |
|---|---|
| Repository rules | `AGENTS.md` |
| Shared current state | `CLAUDE.md` |
| Repo-level "where is X documented" | `docs/DOCS_INDEX_AND_ROUTER.md` (this) → routes you onward |
| Project status + what's paused | `PROJECT_STATUS.md` |
| **All POSTER2 formal docs + reading order** | **`docs/poster2/README.md`** |
| POSTER2 active branch state | `docs/poster2/current_branch_execution_log_v1.md` |
| CUISTANCE commercial trial | §6 above (all under `docs/poster2/`) |
| Family A / template_dual_v2 architecture | `docs/poster2/02_architecture/` |
| Engineering / validation status | `docs/poster2/03_engineering/`, `docs/poster2/05_validation/` |
| Published frontend mirror (NOT docs) | `docs/*.html`, `docs/*.js`, `docs/*.css` (mirror of `frontend/`) |
| Legacy root one-offs | root `*.md` listed in §4 (reference-only · archive-later) |

## 10. Update-vs-create rule

- **Prefer UPDATE** an existing canonical doc over creating a new one. New docs are justified only for a
  genuinely new scope/phase.
- POSTER2 docs: add a one-line index entry in `docs/poster2/README.md` and (if branch-relevant) a short note in
  `current_branch_execution_log_v1.md`. Do **not** create parallel indexes.
- Repo-level governance docs: update `PROJECT_STATUS.md` and (if routing changes) this router.
- Never start a second alignment/design/status doc for the same scope — extend the existing one.

## 11. Duplicate / superseded docs policy

- Mark, don't move. Superseded/duplicate docs are flagged **reference-only** or **archive-later** in this
  router (and/or in `docs/poster2/README.md`), and are **not** physically archived/deleted in this task.
- Known duplicates/superseded (record, do not move):
  - `docs/poster2/01_architecture/template_dual_v2_architecture_business_definition.md` — **legacy duplicate**
    of the formal `02_architecture/…` copy (reference-only).
  - Legacy grouped dirs `docs/poster2/01_architecture/`, `02_engineering/`, `03_stage_assessment/`,
    `04_external_reference/`, `05_next_phase_plan/`, `docs/execution/`, `docs/architecture/` — superseded by
    the layered `docs/poster2/0X_*` path (reference-only).
  - Root one-offs in §4 — archive-later.
- Physical archiving requires **explicit Owner approval** (separate task).

## 12. Required metadata for new docs

Every **new** documentation file (outside the historical corpus) must begin with a metadata block:

```
Purpose: <one line>
Status: <draft | submitted | active | superseded>
Scope: <what it governs / excludes>
Source dependencies: <the docs/code it depends on>
Owner gate: <what Owner decision it waits on, if any>
Next action: <the next concrete step>
```

- ERROR-enforced for **new/changed markdown outside `docs/poster2/`** (repo-governance docs).
- ADVISORY (warning) for **current-phase CUISTANCE docs** that predate this rule (add metadata next time they
  are touched).
- The broad historical `docs/poster2/**` corpus is **exempt** (governed by `docs/poster2/README.md`).

## 13. Governance rules

1. `AGENTS.md` rules-only; `CLAUDE.md` shared-state-only; `docs/poster2/README.md` poster2-index-only — keep
   them in their lanes.
2. This router routes; it does not restate product truth.
3. No new root-level markdown except the governance/index allowlist (`AGENTS.md`, `CLAUDE.md`, `README.md`,
   `PROJECT_STATUS.md`, `PROJECT_INDEX.md`). New one-offs go under a `docs/` route.
4. No physical reorg/archive/delete of historical evidence without explicit Owner approval.
5. One scope → one canonical doc (update, don't fork).
6. `scripts/check_docs_router.py` is the automated guard (see §15).

## 14. Execution decision

- **Documentation governance: ACTIVE (pilot).**
- **PR-1 implementation: PAUSED** until Owner approves this docs router.
- No product code, renderer, email behavior, mockup, or deployment config changed by this task.
- After Owner approval, implementation may resume under this governance (the backend alignment plan's
  PR-1…PR-4).

## 15. Script check policy

`scripts/check_docs_router.py` enforces:

- **ERROR** (exit 1): this router missing; `PROJECT_STATUS.md` missing or not referencing the router; a
  **new/changed** root-or-`docs/`-level markdown (outside `docs/poster2/`, outside the allowlist) that is either
  not in an allowed route or missing the §12 metadata block.
- **WARN** (exit 0): legacy root one-offs (archive-later); current-phase CUISTANCE docs missing metadata;
  duplicate alignment-style docs; legacy poster2 grouped dirs.
- The broad `docs/poster2/**` corpus is **not** error-checked (governed by `docs/poster2/README.md`).
- Run: `python3 scripts/check_docs_router.py --all`. Legacy reality surfaces as **warnings**, not errors.
