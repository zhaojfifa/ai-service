# CUISTANCE Clean Baseline Packet v1

Status: **FROZEN clean asset baseline** for the next stage.
This packet is documentation only — no app/frontend/runtime behavior is changed.

## 1. Branch and tag

- Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`
- Local tag: `poster2-cuistance-dual-mode-clean-baseline-4ae307a` → `4ae307a` (**local only — not pushed**)

## 2. Current commit

`4ae307a` — accepted process-asset cleanup baseline.

Accepted lineage:

| Commit | Meaning |
| --- | --- |
| `83a58ee` | Fiche `product_sheet_email` local closure (no poster runtime) |
| `a175ee1` | Fiche selection / `product_sheet_email` preview truth fix |
| `fa028e2` | cleanup audit docs |
| `4ae307a` | process asset cleanup baseline (399MB → 3.7MB) |

## 3. Currently supported business modes

- **Affiche / `campaign_poster_email`** — target poster route (composite poster, no inner banner in email body).
- **Fiche / `product_sheet_email`** — **single-product only**, deterministic from Workbench truth (no poster runtime,
  no `poster_key`).

Email fill format always follows the selected body visual; mismatches are rejected.

## 4. Explicit NON-scope (not implemented / not in this packet)

- Real send (HOLD).
- Multi-product email (`products[]` contract deferred — see baseline doc).
- Clean repo export (`ai-service-clean`) — proposed only, not executed.
- Git history rewrite (BFG / filter-repo) — not run.

## 5. Cleanup result

- `docs/poster2/assets`: **399 MB → 3.7 MB**.
- **28 untracked** DELETE_CANDIDATE dirs deleted (~244.5 MB; no git-history impact).
- `reconstruction_v1` (101 MB, tracked) archived externally + `git rm -r`.
- `email_campaign_composite_ui_v1` (11 MB, tracked) archived externally + `git rm -r`.
- 139 CUISTANCE + 8 announcement process screenshots pruned (`git rm`).
- 161 tracked files removed total. No `app/`, `frontend/`, `tests/`, `scripts/`, config, or root-doc change.

## 6. Preserved artifacts

- All 18 `evidence.json` inside CUISTANCE evidence dirs.
- `manifest/*.json`, decision `*.md`, baseline/audit/cleanup docs (`docs/poster2/*.md`, `*.json`, `*.txt`).
- Source PSD `cuistance_psd_email_container_last_mile_v1/source/产品海报.psd` (3.2 MB).
- Email container reference templates `source/ttt.html`, `source/ttt2.html`, `source/logo_01.jpg`.

## 7. Working-tree large-file status (this verification pass)

| Item | Size | Tracked | Class | Action |
| --- | --- | --- | --- | --- |
| `scripts/out/reference_grammar_v1/**` (HTML/PNG render dumps) | **~655 MB** | untracked | DELETE_CANDIDATE | **DEFERRED** — outside `docs/poster2/assets` cleanup scope; owner to authorize a separate pass. |
| `app/assets/fonts/NotoSansSC-*.ttf` | 33 MB + 3.9 MB | tracked | KEEP | Active Pillow renderer runtime fonts. |
| `assets/fonts/NotoSansSC-*.ttf` | 33 MB + 3.9 MB | tracked | KEEP | Runtime fonts. |
| `assets/fonts/ArchivoBlack-Regular.ttf` | — | untracked | REVIEW_NEEDED | Owner to confirm keep/track or drop. |
| `.claude/worktrees/**` | ~295 MB | n/a (tooling) | KEEP | Agent worktrees — tooling state, not repo content. |

> The single biggest reclaimable item now is **`scripts/out/` (~655 MB, untracked)** — bigger than the entire
> `docs/poster2/assets` cleanup. It is intentionally NOT touched here (out of scope); flagged for a future
> owner-authorized pass.

## 8. Git history large-blob report

See `docs/poster2/git_large_blobs_report_v1.txt`. Largest history blobs are the now-removed
`reconstruction_v1/catalog_hero_v1.html` (49 MB) and `catalog_hero_v2.html` (47 MB) plus the tracked
`app/assets/fonts/NotoSansSC-Regular.ttf` (35 MB). The removed dumps remain in history (recoverable); purging them
from history would require a rewrite (BFG / filter-repo), which is **NOT** performed in this pass.

## 9. External archive status

- Current local archive: `~/poster_archive/poster2_cleanup_20260620/` (reconstruction_v1, email_campaign_composite_ui_v1,
  announcement screenshots, CUISTANCE screenshots).
- External destination (object store / bucket): **TBD — owner to provide.** Once populated, the local archive can be dropped.

## 10. Next-stage options (proposed — NOT executed)

1. **Keep developing on the cleaned trial branch** (default; lowest risk).
2. **Create a clean runtime branch** (proposed, not created):
   ```bash
   git checkout -b cleanup/poster2-cuistance-clean-runtime-v1
   ```
3. **Export a clean working tree** from the tagged baseline (proposed, requires owner approval):
   ```bash
   mkdir -p ../ai-service-clean
   git archive --format=tar poster2-cuistance-dual-mode-clean-baseline-4ae307a | tar -x -C ../ai-service-clean
   ```
4. **Optional future history rewrite** to shrink the `.git` directory (purge `reconstruction_v1` HTML dumps and the
   9.5 MB record JSON) — only with explicit owner authorization; not performed here.

## Recommendation

**Defer** branch/export/history-rewrite for now and keep developing on the cleaned trial branch. Before any
clone-size-sensitive milestone, run an owner-authorized pass to (a) clear `scripts/out/` (~655 MB untracked) and
(b) decide on a history rewrite for the already-removed large blobs.
