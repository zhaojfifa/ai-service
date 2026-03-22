# P1.5 Cutover Criteria

## Decision Levels

- `not ready`
- `ready for limited rollout`
- `ready for default`

## Hard Gates Before Any Cutover

1. `renderer_mode=puppeteer` is validated only on `template_dual_v2`.
2. Pillow fallback remains available and unchanged.
3. Debug artifacts are retained and readable for staging validation runs.
4. No AI is used for title, subtitle, agent, feature, or callout rendering.

## Gates For Limited Rollout

All of the following must be true:

1. Staging deploy succeeds with Chromium installed.
2. At least 20 successful staging renders using `renderer_mode=puppeteer`.
3. 0 blocking layout regressions in title, subtitle, agent pill, callouts, gallery, and safe margins.
4. 0 cases where `renderer_mode=puppeteer` silently hides text or overlaps protected zones.
5. Fallback behavior is verified at least once by forcing a Chromium failure and observing:
   - request completes
   - `render_engine_used=pillow`
   - `degraded=true`
6. Renderer metadata snapshot and all debug artifact URLs are present for every validation sample.

Result if all pass: `ready for limited rollout`.

## Gates For Default

All limited rollout gates must already pass, plus:

1. At least 100 pilot renders for `template_dual_v2` with `renderer_mode=puppeteer`.
2. Puppeteer success rate at or above 99%.
3. Fallback rate below 1%.
4. No unresolved staging or production defects involving structured text placement.
5. Render latency remains operationally acceptable versus Pillow for the intended traffic volume.
6. On-call operators can use debug artifacts and metadata snapshots to diagnose failures without code changes.

Result if all pass: `ready for default`.

## Current Recommendation Rule

If runtime validation has not yet been completed on a Chromium-capable staging deploy, the recommendation remains `not ready`.
