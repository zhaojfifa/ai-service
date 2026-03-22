# P1.5 Runtime Validation Plan

## Scope

Validate the existing `poster2` structured renderer pilot on `POST /api/v2/generate-poster` without changing the default renderer and without expanding beyond `template_dual_v2`.

## Validation Targets

1. Explicit `renderer_mode=puppeteer` works for `template_dual_v2`.
2. Default `renderer_mode=auto` continues to resolve to Pillow.
3. Pillow fallback remains intact if Chromium or Playwright fails.
4. Debug artifacts are visible for each staged render:
   - background layer
   - product/material layer
   - foreground layer
   - final composited poster
   - renderer metadata snapshot

## Required Runtime Checks

1. Deploy staging with Chromium installed.
2. Send one control request with `renderer_mode=pillow`.
3. Send one pilot request with `renderer_mode=puppeteer`.
4. Confirm response fields:
   - `renderer_mode`
   - `render_engine_used`
   - `foreground_renderer`
   - `background_renderer`
   - `debug_artifacts.*`
5. Open every debug artifact URL and verify that it is readable.
6. Inspect the renderer metadata snapshot JSON and confirm:
   - requested mode
   - effective engine
   - degraded flag
   - hashes
   - timings

## Expected Outcomes

- Pillow control request returns `render_engine_used=pillow`.
- Puppeteer pilot request returns `render_engine_used=puppeteer` in the healthy case.
- If Chromium launch fails, the request still completes with `render_engine_used=pillow` and `degraded=true`.
