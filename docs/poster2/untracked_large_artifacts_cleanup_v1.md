# Untracked Large Artifacts — Cleanup (pre-clean report)

Part of POSTER2-CLEANUP-UNTRACKED-LARGE-ARTIFACTS-AND-PRODUCTIZATION-BASELINE-V1 (Part A).
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1` @ `032b946`.
Machine-readable inventory: `docs/poster2/untracked_large_artifacts_inventory_v1.json`.

## Authorized target

`scripts/out/` — **655.1 MB, 87 files, UNTRACKED** — classified `DELETE_CANDIDATE` and now authorized for cleanup.

Dominated by one-off catalog-hero render dumps (base64-inlined HTML):

| File | Size |
| --- | ---: |
| `scripts/out/reference_grammar_v1/reconstruction/catalog_hero_v1.html` | 47 MB |
| `scripts/out/reference_grammar_v1/heavy/catalog_hero_v2_iter2..13.html` (12 files) | ~45 MB each |
| plus iteration PNGs (`iter_*.png`, ~2.4 MB each) | — |

These are process render output of an exploration route (`reference_grammar_v1`), not source, not active code, not
referenced by `app/` / `frontend/` runtime.

## Action

1. Archive the whole `scripts/out/` to `~/poster_archive/poster2_cleanup_20260620/untracked_large_artifacts/scripts_out`.
2. `rm -rf scripts/out` (untracked → no git impact, no commit entry).

Nothing else under the working tree is deleted in this pass.

## Other large files (working tree, >5 MB, excl `.git`/`.venv`/`node_modules`/`.claude`)

| File | Size | Tracked | Class | Action |
| --- | --- | --- | --- | --- |
| `app/assets/fonts/NotoSansSC-Regular.ttf` | 33.4 MB | yes | KEEP | Active Pillow renderer font. |
| `app/assets/fonts/NotoSansSC-SemiBold.ttf` | 33.4 MB | yes | KEEP | Active Pillow renderer font. |
| `assets/fonts/NotoSansSC-SemiBold.ttf` | 33.4 MB | yes | KEEP | Tracked font. |

No other untracked files >5 MB outside `scripts/out/` (and `.claude/worktrees/` agent tooling, which is not repo content).

## ArchivoBlack decision

`assets/fonts/ArchivoBlack-Regular.ttf` — **92 KB, UNTRACKED**, no references found in `app/`/`frontend/`/`scripts/`.
Classified **REVIEW_NEEDED**. **Report-only — NOT deleted** this pass (negligible size; owner to confirm whether to
track it for a future font need or drop it).
