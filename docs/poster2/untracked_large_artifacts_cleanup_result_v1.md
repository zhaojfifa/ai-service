# Untracked Large Artifacts — Cleanup Result v1

Part of POSTER2-CLEANUP-UNTRACKED-LARGE-ARTIFACTS-AND-PRODUCTIZATION-BASELINE-V1 (Part A).
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1` @ `032b946`.
Sizes report: `docs/poster2/untracked_large_artifacts_cleanup_result_sizes_v1.txt`.

## Result

| Item | Before | After |
| --- | ---: | ---: |
| `scripts/out/` (untracked render dumps) | **655 MB / 87 files** | **removed** |
| `docs/poster2/assets` (untouched this pass) | 3.6 MB | 3.6 MB |

`scripts/out/` was archived to
`~/poster_archive/poster2_cleanup_20260620/untracked_large_artifacts/scripts_out` (655 MB) **before** `rm -rf`.
It was confirmed untracked, so the deletion does not appear in git status and has zero git-history impact.

## Remaining working-tree files >5 MB

All remaining large files are **either tracked runtime dependencies (KEEP) or agent tooling (not repo content)**:

- `app/assets/fonts/NotoSansSC-Regular.ttf`, `NotoSansSC-SemiBold.ttf` (33 MB each) — KEEP (Pillow renderer fonts).
- `assets/fonts/NotoSansSC-SemiBold.ttf` (33 MB) — KEEP (tracked).
- `.claude/worktrees/**/NotoSansSC-SemiBold.ttf` (33 MB ×7) — agent worktree tooling, not repo content.

No untracked process artifacts >5 MB remain.

## ArchivoBlack — report only (not deleted)

`assets/fonts/ArchivoBlack-Regular.ttf` (92 KB, untracked, no references in `app/`/`frontend/`/`scripts/`) is left in
place and flagged REVIEW_NEEDED. Owner to confirm keep+track vs drop.

## Guarantees

- No `app/`, `frontend/`, `tests/` change. The only `scripts/` change is the deletion of untracked `scripts/out/`.
- No tracked file removed; no git history rewrite; no tag pushed.
- `docs/poster2/assets` baseline (3.6 MB, 18 evidence.json, source PSD, ttt.html/ttt2.html) unchanged.

## Recoverability

`~/poster_archive/poster2_cleanup_20260620/untracked_large_artifacts/scripts_out/` holds the full copy. (These files
were never tracked, so they are not in git history — the local archive is the only restore source.)
