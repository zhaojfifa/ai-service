# header + bottom text budget contract status v1

## Scope Of This Branch

This file records branch-local tuning on `fix/poster2-header-bottom-budget-guarded`.

This branch is limited to:

- header agent-lane budget tuning
- bottom dense-quad text-budget tuning

This branch does not allow:

- geometry changes
- clamp changes
- frozen-bottom schema changes
- frozen-bottom diagnostics field changes
- beautification drift
- frozen-baseline rewrites

## Budget Changes

- `header agent_char_budget`: `24 -> 32`
- `bottom dense-quad title_char_budget`: `20 -> 28`
- `bottom dense-quad subtitle_char_budget`: `24 -> 28`

## Explicit Non-Changes

- `title_line_clamp` unchanged
- `subtitle_line_clamp` unchanged
- `title_band_region` bounds unchanged
- `subtitle_slot` bounds unchanged
- `gallery_strip_region` bounds unchanged

## Interpretation

This is:

- not a geometry change
- not a beautification change
- not a frozen-baseline rewrite

## Validation Gate

This branch is only eligible for re-merge review when all remain green:

- guarded branch pytest suite
- frozen bottom evidence guard
- backend-evidence-only Stage 2 guard
- frontend/docs sync guard
- deployment smoke from GitHub Pages origin

## Live Backend Validation Snapshot

Runtime validation against current live host:

- host: `https://ai-service-leob.onrender.com`
- request id: `p2-header-bottom-guard`
- trace id: `ae115f79-7d3c-43ba-a0a5-3875fcc27d86`

Observed runtime status:

- `degraded = false`
- `structure_complete = true`
- `deliverable = true`
- `title_band_region` bounds unchanged
- `subtitle_slot` bounds unchanged
- `gallery_strip_region` bounds unchanged

Observed live-budget state:

- `header agent_char_budget = 24`
- `bottom dense-quad title_char_budget = 20`
- `bottom dense-quad subtitle_char_budget = 24`

Interpretation:

- deployment path is healthy
- GitHub Pages origin can reach backend
- current live host still reflects stable `main`, not this guarded branch
- therefore live runtime confirms frozen geometry and stability, but does **not** yet confirm the guarded budget improvements
