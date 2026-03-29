# current branch execution log v1

## Branch

- `fix/poster2-header-bottom-budget-guarded`

## Latest Validated Milestone

### 2026-03-29 — guarded text-budget tuning start

Scope kept narrow:

- header agent-lane budget tuning
- bottom dense-quad split-mode text-budget tuning

Explicit non-goals preserved:

- no bottom geometry change
- no change to `title_band_region` bounds
- no change to `subtitle_slot` bounds
- no change to `gallery_strip_region` bounds
- no frozen bottom baseline doc semantic rewrite
- no beautification expansion

Implementation decisions:

- `identity_left_agent_right.agent_char_budget` relaxed from `24` to `32`
- `title_gallery_split + dense_quad` keeps frozen line clamps and frozen geometry, but raises:
  - `title_char_budget` from `20` to `28` when still in one-line title pressure
  - `subtitle_char_budget` from `24` to `28`

Validation target for this milestone:

- guarded branch pytest suite green
- frozen bottom evidence guard green
- backend-evidence-only Stage 2 guard green
- frontend/docs sync guard green
- deployment smoke already green from stable `main`

### 2026-03-29 — live backend validation snapshot

Real request executed against current live host:

- host: `https://ai-service-leob.onrender.com`
- request id: `p2-header-bottom-guard`
- trace id: `ae115f79-7d3c-43ba-a0a5-3875fcc27d86`

Observed:

- `degraded = false`
- `structure_complete = true`
- `deliverable = true`
- frozen bottom geometry evidence unchanged:
  - `title_band_region = {x:112,y:728,w:800,h:144}`
  - `subtitle_slot = {x:152,y:818,w:720,h:28}`
  - `gallery_strip_region = {x:96,y:882,w:832,h:64}`

Observed live budget values:

- `header agent_char_budget = 24`
- `bottom dense-quad title_char_budget = 20`
- `bottom dense-quad subtitle_char_budget = 24`

Interpretation:

- deployment path is recovered and healthy
- current live host still serves stable `main`
- guarded branch budget improvements are not yet observable on live runtime until a review deployment exists

### 2026-03-29 — branch-runtime API guard added

Added a backend-only API-path validation on this guarded branch.

What this guard proves:

- the `/api/v2/generate-poster` route can exercise the guarded branch budgets end-to-end
- `header_contract_review.behavior_policy.agent_char_budget = 32`
- `bottom_contract_review.behavior_policy.title_char_budget = 28`
- `bottom_contract_review.behavior_policy.subtitle_char_budget = 28`
- frozen bottom geometry evidence remains unchanged
- Stage 2 can continue to consume backend evidence only

Interpretation:

- branch-local runtime behavior is now covered without relying on live deployment state
- the remaining blocker before re-merge review is a review deployment or equivalent runtime that exposes this branch outside local test execution
