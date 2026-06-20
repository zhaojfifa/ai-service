# POSTER2 Cleanup Result v1

Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`
Starting commit: `fa028e2` (audit)
Scope: `docs/poster2/assets/` process evidence. **No product code touched.**
Local archive of everything removed: `~/poster_archive/poster2_cleanup_20260620/`

## Headline

`docs/poster2/assets` went from **399 MB → 3.7 MB** (≈99% reclaimed). All historical docs and all `evidence.json`
(18) were preserved; only process screenshots, generated-image dumps, HTML render dumps, and base64-bloated record
dumps were removed.

## Phases

| Phase | Action | Removed | Method | Size after |
| --- | --- | --- | --- | --- |
| 1 | Delete 28 untracked DELETE_CANDIDATE dirs | ~244.5 MB | plain `rm` (untracked → no git history impact) | 155 MB |
| 2 | Archive + remove `reconstruction_v1` (tracked, 101 MB; 47M+45M HTML dumps) | ~101 MB | archive → `git rm -r` | 54 MB |
| 3 | `email_campaign_composite_ui_v1` archive+`git rm`; announcement_* PNGs `git rm` (docs kept) | ~13 MB | archive → `git rm` | 41 MB |
| 4 | Prune 139 process screenshots inside 11 active CUISTANCE evidence dirs | ~37 MB | archive → `git rm` (all tracked) | 3.7 MB |

Total git-staged deletions: **161 tracked files** (7 reconstruction + 7 composite_ui + 8 announcement PNG +
139 CUISTANCE PNG). Untracked deletions (Phase 1, 28 dirs) are not in git status (never tracked).

## Preserved (kept in repo)

- All `docs/poster2/*.md`, `*.json`, `*.txt` (baseline, audit, manifests, status docs).
- All `evidence.json` (18) inside CUISTANCE evidence dirs, plus their `*.md` decision logs and `manifest/*.json`.
- CUISTANCE source inputs: `cuistance_psd_email_container_last_mile_v1/source/产品海报.psd` (3.2 MB, kept per owner),
  `ttt.html` / `ttt2.html` (email container reference templates), `logo_01.jpg`.
- announcement_* md/json evidence (screenshots removed, docs kept).

## Largest remaining asset items

| Item | Size |
| --- | ---: |
| `cuistance_psd_email_container_last_mile_v1/` (mostly `source/产品海报.psd`) | 3.5 MB |
| `announcement_*` (4 dirs, md/json only) | ~112 KB total |
| other `cuistance_*` evidence dirs (json/md only) | ≤4 KB each |

## Recoverability

- Everything removed was copied to `~/poster_archive/poster2_cleanup_20260620/` before removal.
- Tracked removals remain in git history at `fa028e2` (e.g. `git checkout fa028e2 -- <path>`).
- See `reconstruction_v1_archive_manifest.md`, `review_needed_cleanup_decision_v1.md`,
  `cleanup_delete_manifest_v1.json`, `cuistance_screenshot_prune_manifest_v1.json`.

## Guarantees

- No `app/`, `frontend/`, `tests/`, `scripts/`, config, or root docs changed.
- No baseline/historical `.md`, no `evidence.json`/`manifest.json`, no source PSD deleted.
- No multi-product work; no main merge; no tag; real send unchanged.
