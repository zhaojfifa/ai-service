<!-- Copilot / AI agent instructions for contributors working on this repo -->

# Quick Orientation

- **What this repo is**: a FastAPI backend (`app/`) plus a static frontend (`frontend/` & `docs/`) that together implement a 3-step marketing-poster workflow (input → AI generation → email).
- **Primary runtime**: Python (see `requirements.txt`). The API entrypoint is `app.main:app` (FastAPI). Frontend is a static site intended for GitHub Pages.

# Key files & directories (quick map)

- `app/main.py` — API routes, request validation, orchestrates generation pipeline (Glibatree → Vertex/OpenAI → storage). Use this to understand logging and error handling.
- `app/config.py` — centralized environment parsing (CORS, SMTP, R2/S3, Glibatree/Vertex/OpenAI). Look here for env var names and defaults.
- `app/schemas/` — Pydantic models used across the API. Note the code contains compatibility fallbacks for Pydantic v1 vs v2 (`model_validate` / `model_dump`).
- `app/services/` — implementation of storage, image provider, Glibatree prompt building, Vertex integration, e-mail sending. Use these when modifying generation or storage logic.
- `frontend/` and `docs/` — static UI and prompt/template assets. `frontend/app.js` implements the client-side workflow, prompt inspector, and sessionStorage usage.
- `frontend/prompts/presets.json` — prompt presets loaded by the Prompt Inspector (both front and back rely on this structure).
- `frontend/templates/` — template specs, mask/base64 assets and `spec.json` that drive slot rules (allowsPrompt/allowsUpload, count, label).

# Run & test (developer commands)

- Create venv and install:
  - Windows PowerShell: `python -m venv .venv; .venv\Scripts\activate; pip install -r requirements.txt`
- Run API locally:
  - `uvicorn app.main:app --reload` (or with host/port when needed: `--host 0.0.0.0 --port 8000`).
- Run tests:
  - `pytest -q` (project has `pytest.ini` and tests under `tests/`).
- Quick curl smoke tests:
  - `curl -s http://127.0.0.1:8000/health`
  - `curl -s http://127.0.0.1:8000/api/imagen/generate -H 'Content-Type: application/json' -d '{"prompt":"a hummingbird","size":"512x512"}'`

# Important patterns and conventions (project-specific)

- Environment-first config: `app/config.py` contains `get_settings()`—always consult it before adding new env flags. Many behaviors are toggled by env vars (e.g., `RETURN_BINARY_DEFAULT`, `UPLOAD_MAX_BYTES`, `S3_*`, `GLIBATREE_*`).
- Storage vs inline images: canonical data exchanged to backend is an object storage `key` / `url` (not raw binary). Frontend uses `POST /api/r2/presign-put` to get a PUT URL and then uploads directly to Cloudflare R2.
- Template-driven rendering: templates define slot metadata (`materials`) that drive both frontend forms and backend generation decisions. When adding a new template update both `frontend/templates/` and any back-end fallbacks.
- Pydantic compatibility: models may be used with either Pydantic v2 (`model_validate` / `model_dump`) or v1 fallbacks (`parse_obj` / `.dict()`); prefer changes that preserve both paths or update all callsites consistently.
- Defensive startup: `app/main.py` uses optional middleware imports (e.g., `RejectHugeOrBase64`) and guarded Vertex init. When adding optional integrations keep the same try/except + logging pattern.

# Integration points & external dependencies

- Vertex (Google) — `app/services/vertex_imagen.py` and `app/services/vertex_imagen3.py` are responsible for calling Vertex Imagen models. Configure via GCP envs in `config.py` (project, location, model names).
- Glibatree/OpenAI — prompts composed in `app/services/glibatree.py`. Env vars: `GLIBATREE_API_URL`, `GLIBATREE_API_KEY`, `GLIBATREE_CLIENT`, `GLIBATREE_MODEL` (or OpenAI fallbacks).
- Object storage (Cloudflare R2 / S3) — adapters in `app/services/r2_client.py` and `app/services/storage_bridge.py`. Env vars: `S3_*`, `R2_BUCKET`, `S3_PUBLIC_BASE`.
- SMTP — `app/services/email_sender.py`; configured via `SMTP_*` / `EMAIL_*` env vars parsed in `config.py`.

# Code-change guidance (do's & don'ts for an AI agent)

- Do reference `app/schemas` when modifying request/response shapes; ensure tests in `tests/` remain consistent.
- Do not assume Pydantic v2-only; keep compatibility helpers or migrate all callsites in a single PR and update `requirements.txt` + CI accordingly.
- When adding a new template or prompt preset, update both `frontend/prompts/presets.json` or `frontend/templates/*` and any backend fallbacks in `app/services/template_variants.py` or `app/templates/*`.
- When touching upload/size handling, prefer to update `BodyGuardMiddleware` limits (env var `UPLOAD_MAX_BYTES`) rather than hardcoding new values throughout code.

# Debugging tips

- Logs: app uses `ai-service` logger and uvicorn levels respect `LOG_LEVEL` env var. Search for `generate_poster request received`, `generate_poster completed`, and Vertex trace headers (`X-Vertex-Trace`) to trace generation flows.
- Reproduce front→back flow locally by: 1) run backend; 2) open `frontend/index.html` (file:// or simple static server); 3) use devtools network to inspect presign and upload; 4) call `POST /api/generate-poster` with the same payload.
- If imports fail for optional integrations (Vertex, R2), the app logs the error and continues without that feature — mimick the same safe import pattern when adding optional modules.

# When you need more info

- Look at `README.md` for high-level run & deploy instructions. If an env var or a run command isn't documented, check `app/config.py` and `render.yaml` for Render defaults.
- If you want to change generation providers, inspect `app/services/image_provider/factory.py` and concrete providers under `image_provider/`.

---
If any part of these instructions is unclear or you want more detail (example request payloads, test coverage lines, or template JSON shapes), tell me which area to expand.  
Mention any missing env var values you expect and I will add them to the doc.
