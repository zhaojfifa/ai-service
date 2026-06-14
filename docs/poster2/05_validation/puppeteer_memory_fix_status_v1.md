# Puppeteer Memory Fix Status v1 — HX-POSTER2-PUPPETEER-MEMORY-FIX-V1

## Validation Outcome

Accepted. The generate-poster Puppeteer image-inlining memory explosion (Render
free-plan OOM → 502 on the full 7-asset payload) is fixed without changing any
contract, region geometry, ownership, bottom SOP, or visual output.

## Root Cause (confirmed)

`_image_to_data_url` (renderer) PNG-encoded each asset at full resolution and
inlined it as a base64 data URL. Chromium then decoded all 7 inlined images
(logo + scenario + product + product_secondary + gallery×4) at full resolution
(up to the 4096px asset-loader ceiling) simultaneously — while Python also held
the same bitmaps as PIL images. The poster canvas is only **1024px** at
`device_scale_factor=1`, so every asset was decoded far larger than any slot it
could ever fill. Peak RSS crossed the 512 MB free-plan ceiling → Linux OOM-killer
SIGKILL → raw 502 (not the app's bounded 504 timeout).

## Fix

Two complementary, scope-allowed levers — both stay **above** the 1024px poster
canvas, so they are visually lossless:

1. **Code (primary):** `_downscale_for_inline` bounds each inlined asset's longest
   edge to `POSTER2_INLINE_MAX_DIMENSION` (default **1280px**) with LANCZOS
   *before* base64 encoding, so Chromium decodes small bitmaps. Already
   slot-sized assets (gallery thumbnails) and small fixtures are returned
   untouched / byte-identical.
2. **Config stopgap (`render.yaml`):** `POSTER2_MAX_IMAGE_DIMENSION=1600` lowers
   the held-PIL floor (the AssetLoader load cap), and `POSTER2_INLINE_MAX_DIMENSION=1280`
   pins the inline cap. Config-only, reversible, no code-default change.

No change to Stage1/2/3 flow, `/api/v2/generate-poster` schema, bottom SOP,
`visible_item_count`, annotation truth, region bounds, or composition.

## Memory Evidence (full 7-asset payload, real Chromium, product_hero)

Harness: `scripts/poster2_puppeteer_memory_fix_harness.py`
Report: `scripts/out/puppeteer_memory_fix/puppeteer_memory_report.json`

Analytical (deterministic):

| Metric | Before | After | Reduction |
|---|---|---|---|
| Chromium decode (Σ w·h·4) | 172.6 MB | 34.3 MB | **5.03×** |
| Inlined data-URL HTML | 0.3 MB | 0.1 MB | 4.07× |
| Held PIL (load cap 1600) | 172.6 MB | 52.4 MB | 3.29× |

Real peak RSS (self+children, macOS — runs **higher** than Render's Linux):

| Scenario | inline cap | load cap | peak RSS | under 512 MB |
|---|---|---|---|---|
| before (no fix) | — | 4096 | **697.0 MB** | ✗ (reproduces OOM) |
| inline fix only | 1280 | 4096 | 553.9 MB | ✗ (near ceiling) |
| inline fix + config | 1280 | 1600 | **410.7 MB** | ✓ (~100 MB headroom) |

The inline fix cuts the Chromium decode spike 5×; the held-PIL floor is the
remaining driver, which the `POSTER2_MAX_IMAGE_DIMENSION` stopgap removes. Both
together keep peak RSS under the free-plan ceiling with measured headroom.
(Render's Linux RSS is lower than these macOS numbers, so this is conservative.
A `plan` bump to ≥1 GB remains available as an optional immediate unblock; not
applied here to avoid an unrequested billing change.)

## Stability Evidence (10-run, full 7-asset payload, real Puppeteer)

Report: `scripts/out/puppeteer_memory_fix/puppeteer_stability_report.json`

| Variant | runs | success | validator | distinct hashes |
|---|---|---|---|---|
| base (`template_dual_v2`) | 10 | 100% | pass | 1 |
| studio (`template_dual_v2_studio`) | 10 | 100% | pass | 1 |
| product_hero (`template_dual_v2_product_hero`) | 10 | 100% | pass | 1 |

All three lines: ≥95% success (achieved 100%), validator pass on every run, and a
single distinct final hash (deterministic). The product_hero final hash is
**identical** across the before/after memory scenarios — visual output is
byte-stable through the downscale at poster resolution. Run-0 PNGs saved under
`scripts/out/puppeteer_memory_fix/<variant>_final.png`.

## Guard / Regression Evidence

- `_downscale_for_inline` / `_image_to_data_url` unit tests added
  (`TestInlineDownscaleMemoryFix`, 4 passing): small image untouched & byte-stable,
  oversized image capped with aspect preserved, original not mutated, data-URL
  shrinks.
- Focused poster2 suites (renderer / quality / registry / composition / geometry /
  relaxation / pipeline): **no new failures vs the `main` baseline** — the
  pre-existing failure set is byte-identical with and without this change.
- `node --check frontend/app.js` + `docs/app.js`, `check_frontend_docs_sync.sh`,
  `py_compile` of changed backend file: all pass.

## Remaining Risks

- Real-RSS numbers are macOS; production is Linux (lower). Live Stage2 validation
  against the production memory plan should confirm 200 (no 502) on the real
  7-asset payload — flagged below as the only step not runnable from this
  workspace (no ops credentials / Render shell here).
- Byte-identical final hashes are shown on solid fixtures; for photographic assets
  output is *visually* identical (caps > canvas) but not guaranteed byte-identical.
