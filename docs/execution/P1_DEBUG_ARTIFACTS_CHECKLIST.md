# P1 Debug Artifacts Checklist

## Expected artifact set per run

Trace root:

- local: `/tmp/ai-service-debug/<trace>/`
- optional storage: `debug/<trace>/...`

Expected files:

1. `locked_frame.png`
2. `edit_mask.png`
3. `prompt_bundle.json`
4. `vertex_raw_edit.png` when `edit_attempted=true`
5. `final_composited.png` when backend produced a deterministic composited PIL result

## Expected API metadata

`POST /api/generate-poster` response now includes:

- `render_path_used`
- `edit_attempted`
- `edit_succeeded`
- `fallback_reason`
- `debug_artifacts`

## Healthy edit-path example

- `render_path_used = "experimental_edit"`
- `edit_attempted = true`
- `edit_succeeded = true`
- `fallback_reason = null`
- `debug_artifacts` contains at least:
  - `locked_frame.png`
  - `edit_mask.png`
  - `vertex_raw_edit.png`
  - `final_composited.png`
  - `prompt_bundle.json`

## Safe fallback example

- `render_path_used = "safe_locked_fallback"`
- `edit_attempted = false` when blocked by scene gate
- `edit_attempted = true` and `edit_succeeded = false` when edit tried then failed
- `fallback_reason` contains exact code, for example:
  - `scene_input_gate_blocked:people+text`
  - `edit_model_not_enabled`
  - `vertex_edit_failed`
  - `quota_exhausted`
  - `vertex_unavailable`
  - `locked_frame_fallback`

## Manual spot checks

1. Trigger one safe scene run and inspect JSON response metadata.
2. Trigger one intentionally risky scene description containing people/text/screen keywords and confirm:
   - `scene_input_gate_fallback` warning exists
   - `render_path_used = "safe_locked_fallback"`
   - `fallback_reason` starts with `scene_input_gate_blocked:`
3. Open one returned local artifact path from `debug_artifacts` and confirm files exist.
4. If R2 is configured, confirm artifact `url`/`key` are populated.
