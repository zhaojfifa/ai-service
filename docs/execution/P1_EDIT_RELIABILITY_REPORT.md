# P1 Edit Reliability Report

## Scope

This pass implements P1-A and P1-B only:

- per-run debug artifacts for poster generation
- explicit edit-path / fallback metadata in API response
- conservative scene-input gate for the current kitposter template family

No deployment config changes, template redesign, or architecture refactor were made.

## What changed

### 1. Per-run debug artifacts

File: [app/services/glibatree.py](/Users/tylerzhao/Code/ai-service/app/services/glibatree.py)

Each `POST /api/generate-poster` run now writes a debug bundle under:

- local root: `/tmp/ai-service-debug/<trace>/`
- optional object storage upload: `debug/<trace>/...` key prefix when R2 is available

Artifacts written:

- `locked_frame.png`
- `edit_mask.png`
- `vertex_raw_edit.png` (only when experimental edit was actually attempted)
- `final_composited.png` (when backend had a deterministic final PIL composition in-hand)
- `prompt_bundle.json`

Debug persistence is best-effort and does not fail the request path.

### 2. Response metadata for safe dual-track operation

Files:

- [app/schemas/__init__.py](/Users/tylerzhao/Code/ai-service/app/schemas/__init__.py)
- [app/main.py](/Users/tylerzhao/Code/ai-service/app/main.py)
- [app/services/glibatree.py](/Users/tylerzhao/Code/ai-service/app/services/glibatree.py)

`GeneratePosterResponse` now includes:

- `render_path_used`
- `edit_attempted`
- `edit_succeeded`
- `fallback_reason`
- `debug_artifacts`

Current meaning for the active kitposter family:

- `experimental_edit`: Vertex edit path was attempted and succeeded
- `safe_locked_fallback`: backend returned the deterministic locked-template fallback track

### 3. Conservative scene-input gate

File: [app/services/glibatree.py](/Users/tylerzhao/Code/ai-service/app/services/glibatree.py)

For current template family:

- `template_dual`
- `template_focus`

and current edit render mode:

- `kitposter1_a`
- `kitposter1_b`

the backend now inspects declared scene text inputs:

- `poster.scenario_prompt`
- `poster.scenario_image`

If the text indicates risky scene classes, it blocks the experimental edit path and forces the safe locked fallback.

Signals currently checked:

- `people`
- `text`
- `screen`
- `noisy_indoor`

Returned fallback code example:

- `scene_input_gate_blocked:people+screen`

Warning emitted:

- `scene_input_gate_fallback`

## Why this is intentionally conservative

The current gate does not inspect uploaded pixels directly. It only uses declared scene text metadata that already exists in the request. That keeps the patch low-risk and avoids new model dependencies or image moderation pipelines.

## Verification completed in this pass

- Python syntax check passed with:
  - `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m compileall app/schemas/__init__.py app/main.py app/services/glibatree.py`

## Residual limits

1. Uploaded scene images can still be visually noisy even if text metadata is clean.
2. `final_composited.png` is guaranteed for the deterministic fallback path and Vertex edit path; other non-kitposter legacy paths may only have partial debug coverage.
3. This pass improves observability and safe fallback control, not visual quality beautification.
