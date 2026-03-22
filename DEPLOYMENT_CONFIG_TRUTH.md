# Deployment Config Truth

This table reflects code truth in the current repository after recovery. Status meanings:

- `used`: active in at least one live code path
- `alias`: backward-compatibility alias for another canonical variable
- `ambiguous`: used, but only by a side path or with split naming that can mislead operators
- `dead`: not proven to affect current runtime behavior from inspected code

| Env var | Where read in code | Required | Current status | Recommended canonical name | Keep backward compatibility |
| --- | --- | --- | --- | --- | --- |
| `GCP_KEY_B64` | `app/services/vertex_imagen.py:18-32`, `app/services/vertex_imagen3.py:103`, `app/services/image_provider/vertex_provider.py:18-24` | Yes for current recovered Vertex auth path | used | `GCP_KEY_B64` | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | written by code in `vertex_imagen.py:31` and `vertex_imagen3.py:51`; consumed implicitly by Google ADC | No as primary input in current repo | ambiguous | none as direct operator input; prefer `GCP_KEY_B64` | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS_JSON` | `app/services/vertex_imagen3.py:39-52` | No | used | `GOOGLE_APPLICATION_CREDENTIALS_JSON` | Yes |
| `GCP_PROJECT_ID` | `app/services/vertex_imagen.py:42-48`, `app/services/vertex_imagen3.py:106`, `app/config.py:204-207` | Yes for main poster path | used | `GCP_PROJECT_ID` | Yes |
| `GCP_LOCATION` | `app/services/vertex_imagen.py:43`, `app/services/vertex_imagen3.py:107`, `app/config.py:206` | Yes for main poster path | used | `GCP_LOCATION` | Yes |
| `VERTEX_PROJECT_ID` | `app/services/image_provider/vertex_provider.py:26` | No for main poster path; only `/api/imagen/generate` side path | ambiguous | `GCP_PROJECT_ID` | Yes, until provider paths are unified |
| `VERTEX_LOCATION` | `app/services/image_provider/vertex_provider.py:27` | No for main poster path; only `/api/imagen/generate` side path | ambiguous | `GCP_LOCATION` | Yes |
| `VERTEX_IMAGEN_MODEL_GENERATE` | `app/services/vertex_imagen3.py:108`, `render.yaml:19-20` | Yes for main poster path in practice | used | `VERTEX_IMAGEN_MODEL_GENERATE` | Yes |
| `VERTEX_IMAGEN_GENERATE_MODEL` | `app/config.py:209-212` only | No proven runtime effect on poster generation | ambiguous | `VERTEX_IMAGEN_MODEL_GENERATE` | Yes for now |
| `VERTEX_IMAGEN_MODEL_EDIT` | `app/services/vertex_imagen3.py:109-112`, `render.yaml:21-22` | Required only if edit path is enabled | used | `VERTEX_IMAGEN_MODEL_EDIT` | Yes |
| `VERTEX_IMAGEN_EDIT_MODEL` | `app/services/vertex_imagen3.py:109-112` | No, alias-like precedence over `VERTEX_IMAGEN_MODEL_EDIT` | alias | `VERTEX_IMAGEN_MODEL_EDIT` | Yes |
| `VERTEX_IMAGEN_ENABLE_EDIT` | `app/services/vertex_imagen3.py:113`, `247-248` | Yes for intended kitposter edit path | used | `VERTEX_IMAGEN_ENABLE_EDIT` | Yes |
| `VERTEX_IMAGEN_MODEL` | `app/services/vertex_imagen.py:14`, `app/services/image_provider/vertex_provider.py:28` | No for main poster path; used by alternate provider implementation | ambiguous | `VERTEX_IMAGEN_MODEL_GENERATE` | Yes |
| `VERTEX_TIMEOUT_SECONDS` | `app/services/vertex_imagen3.py:115` | No | used | `VERTEX_TIMEOUT_SECONDS` | Yes |
| `VERTEX_SAFETY_FILTER_LEVEL` | `app/services/vertex_imagen3.py:116` | No | used | `VERTEX_SAFETY_FILTER_LEVEL` | Yes |
| `VERTEX_SEED` | `app/services/vertex_imagen3.py:117-118` | No | used | `VERTEX_SEED` | Yes |
| `R2_ENDPOINT` | `app/services/r2_client.py:34` | Required for R2 when using `R2_*` naming | alias/used | `R2_ENDPOINT` | Yes |
| `R2_ACCESS_KEY_ID` | `app/services/r2_client.py:35` | Required for R2 when using `R2_*` naming | alias/used | `R2_ACCESS_KEY_ID` | Yes |
| `R2_SECRET_ACCESS_KEY` | `app/services/r2_client.py:36` | Required for R2 when using `R2_*` naming | alias/used | `R2_SECRET_ACCESS_KEY` | Yes |
| `R2_REGION` | `app/services/r2_client.py:37` | No | alias/used | `R2_REGION` | Yes |
| `R2_BUCKET` | `app/services/r2_client.py:71`, `97`, `116`, `131`; `app/main.py:886`; `app/services/glibatree.py:157`, `217`, `227` | Required for storage-backed upload/generation | alias/used | `R2_BUCKET` | Yes |
| `R2_PUBLIC_BASE` | `app/services/r2_client.py:62-66`; `app/main.py:586`; `app/services/glibatree.py:245-246` | No, but strongly recommended for stable URLs | alias/used | `R2_PUBLIC_BASE` | Yes |
| `R2_SIGNED_GET_TTL` | `app/services/r2_client.py:100-102` | No | alias/used | `R2_SIGNED_GET_TTL` | Yes |
| `S3_ENDPOINT` | `app/services/r2_client.py:34`; `app/config.py:229` | Required if using legacy S3-style names | alias/used | `R2_ENDPOINT` | Yes |
| `S3_ACCESS_KEY` | `app/services/r2_client.py:35`; `app/config.py:230` | Required if using legacy S3-style names | alias/used | `R2_ACCESS_KEY_ID` | Yes |
| `S3_SECRET_KEY` | `app/services/r2_client.py:36`; `app/config.py:231` | Required if using legacy S3-style names | alias/used | `R2_SECRET_ACCESS_KEY` | Yes |
| `S3_REGION` | `app/services/r2_client.py:37`; `app/config.py:232` | No | alias/used | `R2_REGION` | Yes |
| `S3_BUCKET` | `app/services/r2_client.py:71`, `97`, `116`, `131`; `app/config.py:233`; `app/main.py:886`; `app/services/glibatree.py:157`, `218`, `228` | Required if using legacy S3-style names | alias/used | `R2_BUCKET` | Yes |
| `S3_PUBLIC_BASE` | `app/services/r2_client.py:63`; `app/config.py:234`; `app/main.py:586`; `app/services/glibatree.py:246` | No, but recommended | alias/used | `R2_PUBLIC_BASE` | Yes |
| `S3_SIGNED_GET_TTL` | `app/services/r2_client.py:100` | No | alias/used | `R2_SIGNED_GET_TTL` | Yes |
| `CORS_ALLOW_ORIGINS` | `app/config.py:183-187`; `app/main.py:233-256` | No for same-origin deployment; yes for cross-origin browser use | used | `CORS_ALLOW_ORIGINS` | Yes |
| `ALLOWED_ORIGINS` | `app/config.py:48-64`, `183-187`; `app/main.py:233-236` | No | alias | `CORS_ALLOW_ORIGINS` | Yes |
| `PYTHON_VERSION` | `render.yaml:9-10` | Required by Render blueprint, not app code | used in deployment config only | `PYTHON_VERSION` | N/A |
| `LOG_LEVEL` | `app/main.py:81-91` | No | used | `LOG_LEVEL` | Yes |
| `UPLOAD_MAX_BYTES` | `app/main.py:184`, `194`; upload validation at `875-878` | No | used | `UPLOAD_MAX_BYTES` | Yes |
| `UPLOAD_ALLOWED_MIME` | `app/main.py:195-199`; upload validation at `875-876` | No | used | `UPLOAD_ALLOWED_MIME` | Yes |
| `GLIBATREE_API_URL` | `app/config.py:120`, `2001-2025` gate via `settings.glibatree.is_configured` | No for current kitposter path when Vertex works | used | `GLIBATREE_API_URL` | Yes |
| `GLIBATREE_BASE_URL` | `app/config.py:120` | No | alias | `GLIBATREE_API_URL` | Yes |
| `GLIBATREE_API_KEY` | `app/config.py:119`; `2033-2036` | No for current recovered path | used | `GLIBATREE_API_KEY` | Yes |
| `OPENAI_API_KEY` | `app/config.py:119`, `215`; OpenAI helper modules | No for current observed path | ambiguous | keep only where OpenAI paths are still required | Yes |
| `OPENAI_BASE_URL` | `app/config.py:125`, `216` | No | ambiguous | keep only where OpenAI paths are still required | Yes |
| `FIREFLY_CLIENT_ID` | `render.yaml:30-31`; `app/services/poster2/background.py:275-288` | No for `/api/generate-poster`; only poster2 background service | used | `FIREFLY_CLIENT_ID` | Yes |
| `FIREFLY_CLIENT_SECRET` | `render.yaml:32-33`; `app/services/poster2/background.py:276-288` | No for `/api/generate-poster`; only poster2 background service | used | `FIREFLY_CLIENT_SECRET` | Yes |

## Notes

- The main recovered poster route is `POST /api/generate-poster` in `app/main.py`. Its true Vertex path uses `app/services/vertex_imagen3.py`, not `app/services/image_provider/vertex_provider.py`.
- The `/api/imagen/generate` route uses `app/services/image_provider/factory.py`, which currently points at `app/services/image_provider/vertex_provider.py`. That is why `VERTEX_PROJECT_ID` / `VERTEX_LOCATION` are still listed as `ambiguous`, not fully dead.
- `render.yaml` is not the sole truth source. Some values there are now misleading unless matched against the active code paths above.
