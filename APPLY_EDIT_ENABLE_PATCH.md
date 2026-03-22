# Apply Edit Enable Patch

## What changed

This patch is intentionally narrow and only covers edit enablement, health aliasing, and runtime observability.

1. Vertex edit gate + alias normalization
   - Updated [vertex_imagen3.py](/Users/tylerzhao/Code/ai-service/app/services/vertex_imagen3.py):
     - Added env alias resolver `_env_first(...)`.
     - Normalized project/location resolution:
       - `GCP_PROJECT_ID` -> fallback `VERTEX_PROJECT_ID`
       - `GCP_LOCATION` -> fallback `VERTEX_LOCATION`
     - Normalized generate model resolution:
       - `VERTEX_IMAGEN_MODEL_GENERATE`
       - fallback `VERTEX_IMAGEN_GENERATE_MODEL`
       - fallback `VERTEX_IMAGEN_MODEL`
     - Preserved edit model precedence:
       - `VERTEX_IMAGEN_EDIT_MODEL`
       - fallback `VERTEX_IMAGEN_MODEL_EDIT`
     - Added explicit `edit_disabled_reason` and clearer disabled error message in `edit_bytes()`.
     - Hardened edit-model init:
       - if `VERTEX_IMAGEN_ENABLE_EDIT=1` but edit model load fails, the service now logs reason and keeps generate path available instead of crashing edit setup silently.

2. Vertex init alias normalization
   - Updated [vertex_imagen.py](/Users/tylerzhao/Code/ai-service/app/services/vertex_imagen.py):
     - `init_vertex()` now resolves:
       - project via `GCP_PROJECT_ID` fallback `VERTEX_PROJECT_ID`
       - location via `GCP_LOCATION` fallback `VERTEX_LOCATION`

3. `/api/imagen/generate` provider alias normalization
   - Updated [vertex_provider.py](/Users/tylerzhao/Code/ai-service/app/services/image_provider/vertex_provider.py):
     - normalized project/location/model env resolution with the same alias pattern.

4. Operational hardening in API gateway
   - Updated [main.py](/Users/tylerzhao/Code/ai-service/app/main.py):
     - Added `GET /healthz` as alias to existing health handler.
     - Added startup runtime summaries:
       - vertex summary: project, location, generate model, edit model, edit enabled
       - storage summary: backend, configured flag, bucket, has public base
     - Extended `VertexImagen3 ready` log extra fields with `edit_enabled`.

## Why these changes

- The production symptom was `edit_model=None enabled=False` with healthy deploy and successful fallback image output.
- The direct gate is `VERTEX_IMAGEN_ENABLE_EDIT`; before patch, disabled state was visible but not diagnostic enough.
- The repo had split env naming between `GCP_*` and `VERTEX_*` branches; this patch normalizes resolution without removing backward compatibility.
- `GET /healthz` avoids false negatives from legacy probes while preserving existing `/health`.

## Exact env vars required for edit path

Minimum required to run edit path in kitposter:

- `VERTEX_IMAGEN_ENABLE_EDIT=1`
- `GCP_PROJECT_ID` (or legacy alias `VERTEX_PROJECT_ID`)
- `GCP_LOCATION` (or legacy alias `VERTEX_LOCATION`)
- `GCP_KEY_B64` (or pre-provisioned valid `GOOGLE_APPLICATION_CREDENTIALS`/ADC path)
- Edit model:
  - preferred `VERTEX_IMAGEN_MODEL_EDIT`
  - or `VERTEX_IMAGEN_EDIT_MODEL`

Generate model (recommended explicit):

- `VERTEX_IMAGEN_MODEL_GENERATE`

Storage (for artifact URL output):

- `R2_ENDPOINT` or `S3_ENDPOINT`
- `R2_ACCESS_KEY_ID` or `S3_ACCESS_KEY`
- `R2_SECRET_ACCESS_KEY` or `S3_SECRET_KEY`
- `R2_BUCKET` or `S3_BUCKET`
- optional `R2_PUBLIC_BASE` / `S3_PUBLIC_BASE`

## How to verify after deploy

1. Deploy and inspect startup logs
   - Confirm runtime summary log includes resolved vertex/storage fields.
   - Confirm vertex model log includes:
     - `generate_model=<name>`
     - `enabled=True`
     - `edit_model=<name>`
     - `reason=None`

2. Health checks
   - `GET /health` -> `200`
   - `GET /healthz` -> `200`

3. Poster generation behavior
   - Call `POST /api/generate-poster` with kitposter render mode.
   - Confirm response no longer includes:
     - `vertex_edit_failed_fallback`
     - `kitposter1_locked_frame_fallback`
   - Confirm `degraded` moves toward `false` for successful edit runs.

4. If still degraded
   - Check logs for `edit disabled` reason.
   - If reason indicates model load failure, validate edit model name and SDK compatibility before broader code changes.
