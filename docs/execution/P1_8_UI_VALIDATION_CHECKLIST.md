# P1.8 UI Validation Checklist

## Browser Flow

1. Open Stage 1.
2. Select `template_dual`.
3. Upload or confirm:
   - product image
   - optional logo
   - optional scenario image
   - optional gallery images
4. Save and continue to Stage 2.

## Stage 2 Checks

1. Confirm the Poster2 internal pilot panel is visible.
2. Confirm the UI copy says Puppeteer is internal-only pilot.
3. Confirm renderer selector options are:
   - `auto/default`
   - `pillow`
   - `puppeteer (pilot)`

## Run Sequence

1. Generate once with `auto/default`.
2. Generate once with `pillow`.
3. Generate once with `puppeteer`.

## Per-Run Checks

1. Final poster image renders.
2. Diagnostics panel shows:
   - `template_id`
   - `renderer_mode`
   - `render_engine_used`
   - `degraded`
   - `fallback_reason_code`
   - `foreground_renderer`
   - `total_ms`
   - `template_contract_version`
3. Debug links open for:
   - background layer
   - product/material layer
   - foreground layer
   - final composited poster
   - renderer metadata
4. Recent pilot runs list updates after each generation.

## Safety Check

For a forced Puppeteer failure:

1. Request still succeeds.
2. `render_engine_used` becomes `pillow`.
3. `degraded=true`.
4. `fallback_reason_code` is explicit.
