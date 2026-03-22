# P0 KitPoster Controllability Report

## Scope

P0 only: restore controllability and operational predictability on the current Pillow + Vertex + R2 pipeline, without architecture refactor.

## What changed

1. Font determinism and observability
- File: `app/services/glibatree.py`
- Added runtime font summary helper `poster_font_runtime_summary()`.
- `_load_font()` now logs resolved font path at `INFO` and warns when falling back to `PIL default`.
- Added strict gate `POSTER_FONT_STRICT=1` to fail fast if no CJK-capable font is resolved.

2. Editable-region and locked-layer control (kept hardened)
- File: `app/services/glibatree.py`
- `editable_slots={"scenario"}` remains enforced in `_build_edit_mask_for_template()`.
- Protected slots (`logo`, `brand_name`, `agent_name`, `product`, `title`, `subtitle`) remain carved out with safety margin.
- Post-edit re-application of locked foreground remains in `_apply_locked_frame()`.

3. Prompt hardening (kept hardened)
- File: `app/services/glibatree.py`
- `KITPOSTER_NEGATIVE_HARDENING` remains appended for forced edit path (`force_edit=True`).

4. Operator-facing default cleanup
- Files: `frontend/app.js`, `app/services/glibatree.py`
- Added `sanitizeAgentName(...)` in frontend; no longer lets channel placeholders like `email` become poster `agent_name`.
- Added backend guard in `_prepare_writein_assets()` to sanitize placeholder agent names.

5. Gallery fallback predictability
- File: `app/services/glibatree.py`
- Added explicit warning `gallery_fallback_filled` when gallery slots are padded.
- Added structured log `"[poster] gallery fallback applied"` with filled slot count and source.

6. Env/runtime truth hardening
- Files: `app/config.py`, `app/main.py`
- Unified alias resolution in config for:
  - `GCP_*` / `VERTEX_*`
  - `R2_*` / `S3_*`
  - `VERTEX_IMAGEN_*` generate model aliases
- Startup now logs resolved vertex/storage/font runtime summary explicitly.

## Verified in this pass

- Python syntax check passed:
  - `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m compileall app/main.py app/config.py app/services/glibatree.py`
- Frontend syntax check passed:
  - `node --check frontend/app.js`

## Known residual risks

1. End-to-end image quality still depends on upstream model behavior and runtime prompt inputs.
2. Local test suite could not be fully executed here because this environment uses Python 3.9 while repo typing/runtime expects newer syntax in schemas (`|` unions).
3. `scenario_fallback_used` warning semantics are still broad; it is not a strict quality failure signal.
