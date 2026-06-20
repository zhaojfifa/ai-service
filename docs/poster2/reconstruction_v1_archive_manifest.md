# reconstruction_v1 — Archive Manifest

Part of POSTER2-CLEANUP-DELETE-PROCESS-ASSETS-V1 (Phase 2).
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.

## Original path

`docs/poster2/assets/reconstruction_v1/` (git-tracked, 7 files)

## Size

~101 MB total.

## Largest files

| File | Size |
| --- | ---: |
| `catalog_hero_v1.html` | 47 MB |
| `catalog_hero_v2.html` | 45 MB |
| `reconstruction_render_v2.png` | 2.4 MB |
| `reconstruction_render_v1.png` | 2.0 MB |
| `reference_vs_reconstruction_v2.png` | 1.9 MB |
| `reference_vs_reconstruction_v1.png` | 1.8 MB |
| `iteration_history.png` | 696 KB |

The two HTML files (≈92 MB combined) are one-off inlined catalog-hero render dumps (base64-embedded assets),
not source or active code.

## Reason for archive

Tracked but heavy one-off reconstruction experiment, superseded by the accepted CUISTANCE dual-mode single-product
baseline. Dominates the `docs/poster2/assets` footprint (~101 MB of ~399 MB). Removed from the repo working tree via
`git rm -r` to reclaim space; preserved externally for historical reference.

## External archive destination placeholder

- Local archive (this pass): `~/poster_archive/poster2_cleanup_20260620/reconstruction_v1/`
- External destination (to be filled by Owner): `<object-store/bucket path TBD>`

## Restore instruction

```bash
# from the local archive made during this cleanup pass:
cp -R ~/poster_archive/poster2_cleanup_20260620/reconstruction_v1 \
      docs/poster2/assets/reconstruction_v1
# (or fetch from the external destination once populated)
```

The file contents also remain recoverable from git history at commit `fa028e2` and earlier:

```bash
git checkout fa028e2 -- docs/poster2/assets/reconstruction_v1
```
