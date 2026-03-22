# P0 Verification Checklist

## 1) Startup health

1. Deploy to Render (backend service).
2. Confirm logs include:
   - `app startup complete`
   - `Runtime configuration resolved vertex=... storage=... fonts=...`
   - `poster.font.runtime=...`
3. Verify endpoints:
   - `GET /` => `200`
   - `HEAD /` => `200`
   - `GET /health` => `200`
   - `GET /healthz` => `200`

Example:

```bash
curl -i https://<service>.onrender.com/health
curl -i https://<service>.onrender.com/healthz
```

## 2) Font resolution

Expected healthy log:

- `poster.font.runtime={'regular': '/.../NotoSansSC-Regular.ttf', 'semibold': '/.../NotoSansSC-SemiBold.ttf', 'using_pil_default': False, ...}`

If degraded:

- `using_pil_default=True` or `poster.font.selected=PIL default`

Recommended env (optional):

- `POSTER_FONT_DIRS=/opt/render/project/src/assets/fonts`
- `POSTER_FONT_STRICT=1` (fail fast if fonts are missing)

## 3) Edit enablement

Required env for edit path:

- `VERTEX_IMAGEN_ENABLE_EDIT=1`
- `GCP_PROJECT_ID` (or alias)
- `GCP_LOCATION` (or alias)
- valid edit model env (`VERTEX_IMAGEN_MODEL_EDIT` or alias)

Expected enabled log pattern:

- `[vertex3.model] ... edit_model=<name> enabled=True reason=None ...`

Expected disabled log pattern:

- `[vertex3.model] ... edit_model=None enabled=False reason=<reason> ...`

## 4) Poster behavior checks

Run one kitposter request and inspect response:

```bash
curl -sS -X POST https://<service>.onrender.com/api/generate-poster \
  -H 'Content-Type: application/json' \
  -d @examples/sample_workflow.json | jq .
```

Expect for healthy edit path:

- `degraded=false`
- no `vertex_edit_failed_fallback`
- no `kitposter1_locked_frame_fallback`

Possible controlled warning:

- `scenario_fallback_used` may still appear depending on draft flow.
- `gallery_fallback_filled` means gallery slots were padded due insufficient assets.

## 5) Protected-zone quality sanity check

Manual visual pass on returned poster:

1. Title/subtitle zone has no fake text pollution.
2. Brand/logo/agent/product zones remain aligned and locked.
3. Editable change is confined to scenario/background feel.
4. Bottom gallery fallback behavior is predictable (not silent).
