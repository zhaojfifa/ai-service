# Deployment Config Truth (P0)

Status legend: `used` / `alias` / `ambiguous` / `dead`.

| Env var | Where read | Required | Status | Canonical | Keep compatibility |
| --- | --- | --- | --- | --- | --- |
| `GCP_KEY_B64` | `app/services/vertex_imagen.py::_ensure_credentials_from_b64` | Yes (current Vertex auth path) | used | `GCP_KEY_B64` | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | set by code after decoding key; consumed by ADC | No (primary input is `GCP_KEY_B64`) | used | `GCP_KEY_B64` + ADC | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS_JSON` | `app/services/vertex_imagen3.py::_ensure_gcp_auth_via_json_env` | Optional | used | `GOOGLE_APPLICATION_CREDENTIALS_JSON` | Yes |
| `GCP_PROJECT_ID` | `app/services/vertex_imagen.py`, `vertex_imagen3.py`, `app/config.py` | Yes | used | `GCP_PROJECT_ID` | Yes |
| `VERTEX_PROJECT_ID` | same modules as alias | Optional alias | alias | `GCP_PROJECT_ID` | Yes |
| `GCP_LOCATION` | `app/services/vertex_imagen.py`, `vertex_imagen3.py`, `app/config.py` | Yes | used | `GCP_LOCATION` | Yes |
| `VERTEX_LOCATION` | same modules as alias | Optional alias | alias | `GCP_LOCATION` | Yes |
| `VERTEX_IMAGEN_MODEL_GENERATE` | `vertex_imagen3.py`, `app/config.py` | Yes (practical) | used | `VERTEX_IMAGEN_MODEL_GENERATE` | Yes |
| `VERTEX_IMAGEN_GENERATE_MODEL` | `vertex_imagen3.py`, `app/config.py` | Optional alias | alias | `VERTEX_IMAGEN_MODEL_GENERATE` | Yes |
| `VERTEX_IMAGEN_MODEL` | `vertex_imagen3.py`, `vertex_imagen.py`, `app/config.py` | Optional alias | alias | `VERTEX_IMAGEN_MODEL_GENERATE` | Yes |
| `VERTEX_IMAGEN_MODEL_EDIT` | `vertex_imagen3.py` | Required only for edit path | used | `VERTEX_IMAGEN_MODEL_EDIT` | Yes |
| `VERTEX_IMAGEN_EDIT_MODEL` | `vertex_imagen3.py` | Optional alias | alias | `VERTEX_IMAGEN_MODEL_EDIT` | Yes |
| `VERTEX_IMAGEN_ENABLE_EDIT` | `vertex_imagen3.py`, startup summary in `app/main.py` | Yes for edit path | used | `VERTEX_IMAGEN_ENABLE_EDIT` | Yes |
| `R2_ENDPOINT` | `app/services/r2_client.py`, `app/config.py` | Yes for storage | used | `R2_ENDPOINT` | Yes |
| `R2_ACCESS_KEY_ID` | `r2_client.py`, `app/config.py` | Yes for storage | used | `R2_ACCESS_KEY_ID` | Yes |
| `R2_SECRET_ACCESS_KEY` | `r2_client.py`, `app/config.py` | Yes for storage | used | `R2_SECRET_ACCESS_KEY` | Yes |
| `R2_REGION` | `r2_client.py`, `app/config.py` | Optional | used | `R2_REGION` | Yes |
| `R2_BUCKET` | `r2_client.py`, `app/main.py`, `glibatree.py`, `app/config.py` | Yes for upload/output | used | `R2_BUCKET` | Yes |
| `R2_PUBLIC_BASE` | `r2_client.py`, `app/main.py`, `glibatree.py`, `app/config.py` | Optional but recommended | used | `R2_PUBLIC_BASE` | Yes |
| `S3_*` (`ENDPOINT`, `ACCESS_KEY`, `SECRET_KEY`, `REGION`, `BUCKET`, `PUBLIC_BASE`) | `r2_client.py`, `app/config.py` | Optional alias set | alias | corresponding `R2_*` | Yes |
| `CORS_ALLOW_ORIGINS` | `app/config.py`, `app/main.py` | Required for cross-origin frontend | used | `CORS_ALLOW_ORIGINS` | Yes |
| `ALLOWED_ORIGINS` | `app/config.py`, `app/main.py` | Optional alias | alias | `CORS_ALLOW_ORIGINS` | Yes |
| `POSTER_FONT_DIRS` | `app/services/glibatree.py::_load_font` | Optional | used | `POSTER_FONT_DIRS` | Yes |
| `KP_FONT_DIR` | `app/services/glibatree.py::_load_font` | Optional alias | alias | `POSTER_FONT_DIRS` | Yes |
| `POSTER_FONT_STRICT` | `app/services/glibatree.py::_load_font` | Optional | used | `POSTER_FONT_STRICT` | Yes |

## Runtime truth source

- Backend entrypoint: `app/main.py` (`FastAPI` app).
- Health endpoints: `GET /health`, `GET /healthz`, `GET/HEAD /`.
- Poster main path: `POST /api/generate-poster` -> `app/services/glibatree.py::run_kitposter_state_machine` / `generate_poster_asset`.
- Startup effective config logs:
  - `Runtime configuration resolved vertex=... storage=... fonts=...`
  - `poster.font.runtime=...`
