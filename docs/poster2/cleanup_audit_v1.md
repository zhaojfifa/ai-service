# POSTER2 Cleanup Audit v1 (documentation only — NO deletions)

Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1` @ `a175ee1`
Scope: `docs/poster2/` (evidence assets). **No file is deleted, moved, or modified by this audit.**
Trigger: CUISTANCE dual-mode single-product baseline accepted — see
`docs/poster2/cuistance_dual_mode_single_product_baseline_v1.md`.

## Companion artifacts

- `docs/poster2/assets_cleanup_inventory_v1.json` — machine-readable per-directory inventory + classification.
- `docs/poster2/large_files_report_v1.txt` — largest files, file-type totals, per-dir sizes.
- `docs/poster2/keep_candidates_v1.md` — KEEP_IN_REPO list.
- `docs/poster2/archive_candidates_v1.md` — ARCHIVE_EXTERNAL list.
- `docs/poster2/delete_candidates_v1.md` — DELETE_CANDIDATE + REVIEW_NEEDED lists.

## Totals

- `docs/poster2/assets/` ≈ **399 MB** across **45** top-level evidence directories.
- Heaviest file types: **PNG ≈ 262 MB / 305 files**, **HTML ≈ 102 MB / 7 files** (two 47M+45M inlined catalog_hero
  render dumps in `reconstruction_v1`), **JSON ≈ 28 MB / 92 files** (several 9 MB base64-bloated poster records).

## Classification summary (by directory)

| Class | Dirs | Size |
| --- | ---: | ---: |
| KEEP_IN_REPO | 11 | ~41 MB |
| ARCHIVE_EXTERNAL | 1 | ~101 MB |
| DELETE_CANDIDATE | 28 | ~245 MB |
| REVIEW_NEEDED | 5 | ~13 MB |

> ~245 MB of DELETE_CANDIDATE is overwhelmingly **untracked** exploration/smoke evidence (never committed → zero git
> history impact if removed in a future authorized pass). The single largest reclaimable tracked item is
> `reconstruction_v1` (~101 MB, ARCHIVE_EXTERNAL) dominated by two huge inlined HTML render dumps.

## Classification of the specific areas requested

| Area | Where | Classification | Note |
| --- | --- | --- | --- |
| **Operator screenshots** | `cuistance_psd_email_container_last_mile_v1/operator_screenshots/` (~3 MB) | KEEP_IN_REPO | Part of the accepted CUISTANCE baseline lineage. |
| **Remote evidence screenshots** | `cuistance_*/**/remote_validation/`, `remote_*_v1`, `remote_ops_smoke_v2` | KEEP (cuistance) / DELETE_CANDIDATE (standalone smoke) | CUISTANCE remote evidence stays; one-off remote smoke dumps are ephemeral. |
| **PSD exports / source** | `cuistance_psd_email_container_last_mile_v1/source/产品海报.psd` (3.3 MB) + `exports/` (empty) | REVIEW_NEEDED | Single source PSD; small. Keep if it is the canonical container source, else ARCHIVE_EXTERNAL. Flagged in REVIEW. |
| **Local proof screenshots** | `cuistance_*/**/fiche_*_v1/`, `local_validation/` | KEEP_IN_REPO | Accepted PASS proofs for the frozen baseline. |
| **Old failed evidence** | untracked `ops_campaign_generate_502_diag_v1`, `ops_campaign_remote_404_fix_v1`, `*_probe_v1` | DELETE_CANDIDATE | Diagnosis of resolved/abandoned issues; not baseline. |
| **Duplicate generated PNG/PDF** | `hybrid_*`, `case001_*`, `catalog_hero_*`, `template_a_*`, `email_campaign_composite_v1*` contact sheets/candidates | DELETE_CANDIDATE | Many 2–3 MB candidate/contact-sheet PNGs from generation experiments; superseded. |

## Method & rules

Classification is at **directory granularity** (not per-file) using these rules:

- `cuistance_*` → **KEEP_IN_REPO** (active dual-mode single-product baseline lineage / accepted PASS evidence).
- `reconstruction_v1` → **ARCHIVE_EXTERNAL** (tracked but ~101 MB of inlined HTML render dumps).
- `announcement_*`, `email_campaign_composite_ui_v1`, PSD source → **REVIEW_NEEDED** (tracked, out of current
  single-product scope, owner to confirm).
- untracked `hybrid_*`, `catalog_hero_*`, `case001_*`, `gemini_*`, `template_a_*`, `visual_grammar_*`,
  `reference_grammar_*`, `sop_*`, `model_composed_*`, `ops_*`, `remote_*`, `email_campaign_*` (non-ui_v1) →
  **DELETE_CANDIDATE** (one-off exploration/smoke/diagnosis; not in git history; superseded by the baseline).

## Recommended next pass (requires explicit Owner authorization — NOT done here)

1. ARCHIVE_EXTERNAL `reconstruction_v1` (≈101 MB) to object storage, then `git rm` from the tree.
2. Remove untracked DELETE_CANDIDATE directories (≈245 MB) from the local working tree (no commit needed; they are
   not tracked). Optionally archive a representative subset first.
3. Resolve REVIEW_NEEDED (`announcement_*`, `email_campaign_composite_ui_v1`, PSD source) with the owner.
4. Keep all `cuistance_*` baseline evidence in-repo.

No action in this task beyond producing these documents.
