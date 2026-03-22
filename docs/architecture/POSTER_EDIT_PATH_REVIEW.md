# Poster Edit Path Review (P0)

## Intended path

1. `POST /api/generate-poster` (`app/main.py`) enters kitposter render mode.
2. `run_kitposter_state_machine(...)` (`app/services/glibatree.py`) calls `generate_poster_asset(...)`.
3. `generate_poster_asset(...)` builds locked frame + edit mask.
4. `_generate_poster_with_vertex(..., force_edit=True)` calls `VertexImagen3.edit_bytes(...)`.
5. Edited output is composited with `_apply_locked_frame(...)` so locked zones remain deterministic.

## Current runtime gates for edit availability

Resolved in `app/services/vertex_imagen3.py`:

- `VERTEX_IMAGEN_ENABLE_EDIT` controls enable flag.
- `VERTEX_IMAGEN_EDIT_MODEL` / `VERTEX_IMAGEN_MODEL_EDIT` resolve edit model name.
- If edit model load fails, edit is disabled with reason.
- Startup log prints:
  - project/location
  - generate_model
  - edit_model
  - enabled
  - disabled reason

## Exact fallback chain

If edit path fails in `_generate_poster_with_vertex(...)`:

1. `generate_poster_asset(...)` catches exception.
2. Adds warning (`vertex_edit_failed_fallback` or quota warning).
3. For kitposter, falls back to deterministic local locked-frame render.
4. Returns output with `fallback_used=true` and optional `degraded=true`.

## Warnings currently emitted by poster path

- `scenario_fallback_used`
- `creative_failed_fallback_to_stable`
- `vertex_quota_exhausted_fallback`
- `vertex_edit_failed_fallback`
- `vertex_unavailable_fallback`
- `kitposter1_locked_frame_fallback`
- `gallery_fallback_filled` (added in this P0 pass for explicit slot-padding visibility)

## Why quality can still degrade when deployment is healthy

1. Deployment/config can be healthy while model output is semantically noisy.
2. Quality depends on mask strictness + prompt hardening + slot fallback behavior.
3. If gallery/scenario inputs are sparse, deterministic fallback fill can reduce visual diversity.
4. Placeholder-like operator values (e.g. `email`) can leak into poster text without sanitization; this pass adds both frontend and backend guardrails.

## Minimal safe fixes already landed in P0

- Kept strict scenario-only editable mask and protected slot carve-outs.
- Kept forced negative hardening for edit path.
- Added runtime font and config observability.
- Added explicit gallery fallback warning/log.
- Added agent-name placeholder sanitization on both frontend payload build and backend write-in prep.
