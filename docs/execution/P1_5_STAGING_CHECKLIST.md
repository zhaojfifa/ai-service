# P1.5 Staging Checklist

## Deploy

1. Build with:
   `pip install -r requirements.txt && python -m playwright install chromium`
2. Confirm Chromium is present in the runtime image.
3. Keep default renderer behavior unchanged.
4. Do not change traffic to use `renderer_mode=puppeteer` by default.

## Request Matrix

1. Control request:
   - `template_id=template_dual_v2`
   - `renderer_mode=pillow`
2. Pilot request:
   - `template_id=template_dual_v2`
   - `renderer_mode=puppeteer`
3. Negative gate request:
   - non-pilot template
   - `renderer_mode=puppeteer`
   - expect `422`

## Verify Response Fields

For every successful request, inspect:

- `renderer_mode`
- `render_engine_used`
- `foreground_renderer`
- `background_renderer`
- `degraded`
- `degraded_reason`
- `debug_artifacts.background_layer_url`
- `debug_artifacts.product_material_layer_url`
- `debug_artifacts.foreground_layer_url`
- `debug_artifacts.final_composited_url`
- `debug_artifacts.renderer_metadata_url`

## Visual Checks

1. Title is centered and within safe bounds.
2. Subtitle is visible and not clipped.
3. Agent pill is centered and rounded.
4. Feature callouts align with the fixed anchors.
5. Gallery thumbnails stay within the lower protected band.
6. No foreground text is rasterized by the background generator.

## Failure Handling

If a Puppeteer request falls back to Pillow:

1. Save the response body.
2. Open the renderer metadata artifact.
3. Confirm `degraded=true`.
4. Confirm the route still returned a valid final poster.
5. Do not change the default renderer based on that run.
