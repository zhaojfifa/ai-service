# REVIEW_NEEDED — Cleanup Decisions (Phase 3)

Part of POSTER2-CLEANUP-DELETE-PROCESS-ASSETS-V1.
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.
Local archive for anything removed: `~/poster_archive/poster2_cleanup_20260620/`.

The audit flagged 5 directories as REVIEW_NEEDED. Owner decisions applied:

| Directory | Tracked | Decision applied | Result |
| --- | --- | --- | --- |
| `email_campaign_composite_ui_v1` (11 MB) | yes (7 files) | **Archive external, then `git rm`** | Whole dir archived to `~/poster_archive/.../email_campaign_composite_ui_v1/`, then `git rm -r`. (Dominated by ~9 MB base64-bloated `_records/*.json`.) |
| `announcement_remote_ui_validation_v1` (848 KB) | yes (9 files) | **Keep docs (md/json), remove screenshots** | `git rm` 4 PNG; kept 5 md/json. |
| `announcement_ui_closure_v1` (652 KB) | yes (7 files) | **Keep docs, remove screenshots** | `git rm` 3 PNG; kept 4 md/json. |
| `announcement_runtime_v1` (104 KB) | yes (4 files) | **Keep docs, remove screenshots** | `git rm` 1 PNG; kept 3 md/json. |
| `announcement_live_e2e_diagnosis_v1` (16 KB) | yes (3 files) | **Keep docs, remove screenshots** | No PNG present; kept all 3 md/json unchanged. |

## Source PSD — kept (no change this pass)

`docs/poster2/assets/cuistance_psd_email_container_last_mile_v1/source/产品海报.psd` (~3.3 MB) is **kept**. It sits
inside the active CUISTANCE baseline lineage and is the container source. Per owner instruction, the PSD is not
deleted in this pass.

## Notes

- All removed announcement PNGs were copied to `~/poster_archive/poster2_cleanup_20260620/announcement_screenshots/`
  before `git rm`, and remain recoverable from git history at `fa028e2`.
- The announcement md/json evidence (decision logs, evidence.json) is preserved in-repo.
