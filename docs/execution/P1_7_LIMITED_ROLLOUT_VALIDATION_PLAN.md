# P1.7 Limited-Rollout Validation Plan

## Scope

Validate `template_dual_v2` for limited rollout readiness on the existing poster2 path.

Constraints:

- keep Pillow as the default renderer
- keep Puppeteer opt-in only
- do not add templates
- do not change architecture

## Current Starting Point

Known good signals already observed:

- Pillow path passed
- Puppeteer path passed a real staging run
- `render_engine_used=puppeteer`
- `degraded=false`
- `fallback_reason_code=null`

This means Puppeteer is no longer blocked at basic runtime viability. P1.7 is about repeated stability and rollout confidence.

## Validation Areas

### 1. Repeated-Run Stability

Goal: confirm deterministic behavior across repeated staging runs.

Run:

- 5 to 10 repeated `renderer_mode=puppeteer` requests on `template_dual_v2`
- same template geometry
- stable asset set for the first batch

Check:

- request succeeds every time
- `render_engine_used=puppeteer`
- `degraded=false`
- `fallback_reason_code=null`
- no title/subtitle/agent/callout/gallery drift
- renderer metadata artifact present for every run

### 2. Long-Copy Stress Tests

Goal: confirm structured text stays within slots and protected zones under harder copy.

Cases:

- long title near max length
- long subtitle near max length
- long agent label
- four longer feature strings

Check:

- no clipping beyond acceptable template limits
- no overlap into protected zones
- no hidden title or subtitle
- CTA pill remains legible

### 3. Multi-Asset Variation Tests

Goal: confirm structured foreground remains stable across realistic asset variation.

Cases:

- tall product cutout
- wide product cutout
- transparent product edges
- scenario image present vs absent
- 0, 2, and 4 gallery images
- logo present vs absent

Check:

- product remains within product slot
- gallery strip stays bounded
- missing optional assets do not destabilize layout
- foreground text remains deterministic

### 4. Forced-Fallback Safety Test

Goal: confirm opt-in Puppeteer requests still return valid posters when Puppeteer is intentionally broken.

Run:

- send `renderer_mode=puppeteer`
- force a browser/runtime failure in staging

Check:

- request still succeeds
- `render_engine_used=pillow`
- `degraded=true`
- `fallback_reason_code` is explicit
- `renderer_metadata_url` records fallback triggered and reason

## Pass Threshold For Limited Rollout

Recommend `ready for limited rollout` only when all of the following hold:

1. 5 to 10 staging runs are recorded and reviewed.
2. No blocking layout defects are found.
3. Long-copy stress cases remain acceptable.
4. Multi-asset variations remain acceptable.
5. Forced fallback safety is confirmed once.
6. Pillow remains default and Puppeteer remains opt-in only.
