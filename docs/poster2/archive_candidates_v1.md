# Cleanup Audit — ARCHIVE_EXTERNAL candidates

Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1` @ a175ee1
Scope: `docs/poster2/assets/` top-level evidence directories.
**Audit only — no file is deleted or moved by this document.**

Historically meaningful but heavy evidence that does not need to live in the repo. Recommend moving to external storage (object store / archive) and removing from the working tree **only after Owner authorizes a deletion/move pass**.

Total: **1 dirs / 100.8 MB**

| Directory | Size (MB) | Files | Git | Reason |
| --- | ---: | ---: | --- | --- |
| `reconstruction_v1` | 100.8 | 7 | tracked | Tracked but 101M, dominated by 47M+45M inlined catalog_hero HTML render dumps — move out of repo, keep externally. |
