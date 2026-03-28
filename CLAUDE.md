# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

FastAPI backend (`app/`) + static frontend (`frontend/` & `docs/`) implementing a 3-stage marketing-poster workflow: material input → AI poster generation → email sending.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# Run backend
uvicorn app.main:app --reload

# Run all tests
pytest -q

# Run a single test file
pytest tests/poster2/test_renderer.py -v

# Sync frontend/ to docs/ after frontend changes
bash scripts/sync_frontend_to_docs.sh
```

## Architecture

### Three-stage workflow

- **Stage 1** (`frontend/index.html`) — Material input + layout preview
- **Stage 2** (`frontend/stage2.html`) — AI poster generation with Prompt Inspector (source of truth is `frontend/`, mirror is `docs/`)
- **Stage 3** (`frontend/stage3.html`) — Marketing email sending

### Backend layout

- `app/main.py` — All API routes + orchestration logic
- `app/config.py` — Single source of truth for all env vars; always consult before adding new flags
- `app/schemas/` — Pydantic models (`poster.py`, `poster2.py`, `kitposter.py`)
- `app/services/` — Business logic; image providers, storage, email, Vertex, Glibatree
- `app/services/poster2/` — Advanced poster2 pipeline (contract → resolver → renderer → quality guard)
- `app/templates/` — Template specs and layout geometry

### poster2 pipeline (contract-first)

Default implementation order: **Contract → Validation → Resolver → Renderer → Evidence → Beautification**. Do not reverse this.

Two complementary views of the same system (not competing models):
- **Product governance**: Structure → Control → Beautification
- **Template execution**: Background → Shell → Content

Core rules:
- Shell and content are strictly separated; renderer is the execution layer, not the template truth-source
- Behavior must be lifted into declarative modes / resolver output, not scattered CSS or renderer branches
- Beautification must not compensate for missing contract or control behavior

### Key patterns

- **Environment-first config**: `app/config.py` → `get_settings()` — look here first for env var names and defaults
- **Storage as keys/URLs**: canonical data is an object-storage key or URL, not raw binary; use `POST /api/r2/presign-put` for uploads
- **Template-driven rendering**: templates define slot contracts (`materials`, `allowsPrompt`, `allowsUpload`) that drive both frontend forms and backend decisions
- **Pydantic v1/v2 compatibility**: models support both `model_validate`/`model_dump` (v2) and `parse_obj`/`.dict()` (v1) — preserve both or migrate all callsites in one PR
- **Defensive startup**: optional imports (Vertex, R2, middleware) are wrapped in try/except + logging; follow the same pattern for new optional integrations

## Publishing rule

`frontend/` is source; `docs/` is the GitHub Pages mirror. After any change to `frontend/stage2.html`, `frontend/app.js`, or related files, run `scripts/sync_frontend_to_docs.sh` and commit both together. Do not leave them diverged.

## Required reading for poster2 work

Before editing poster2 code, read in order:
1. `README.md`
2. `docs/poster2/README.md` (lists the full document reading order)
3. `docs/poster2/poster_generation_product_design_baseline_v1.md`
4. The architecture/stage/family docs relevant to the specific task

Do not jump directly into renderer or CSS without re-anchoring on the docs first.

## Validation rules

- A task is not complete because a sample image renders — validate the contract/control layer (metadata, slot ownership, collapse state, visible counts)
- For Stage 2 tasks: validate both the page-side preview path and the final generation path — they are independent
- For editable fields: edited valid inputs must work, not just the default happy path

## Integration points

| Service | Files | Key env vars |
|---------|-------|-------------|
| Google Vertex Imagen | `app/services/vertex_imagen*.py` | `GCP_PROJECT_ID`, `GCP_LOCATION`, `VERTEX_IMAGEN_MODEL_*` |
| Glibatree / OpenAI | `app/services/glibatree.py`, `app/services/openai_image.py` | `GLIBATREE_*`, `OPENAI_*`, `IMAGE_BACKEND` |
| Cloudflare R2 / S3 | `app/services/r2_client.py`, `storage_bridge.py` | `R2_*` or `S3_*` |
| SMTP email | `app/services/email_sender.py` | `SMTP_*`, `EMAIL_ENABLED` |

See `.env.example` for the full variable reference.

## poster2 phase state (as of 2026-03-28)

### Phase 2: bottom SOP baseline — ESTABLISHED + gallery pair tuned

- `bottom_region` behavior (`bottom_mode`, `gallery_mode`, `gallery_count`, title/subtitle) is the agreed SOP baseline for behavior-layer rollout
- **bottom mode selection bug — FIXED**: removed early-return eligibility gate from `initPoster2BottomContractControls` in `frontend/app.js`; controls now always wired regardless of `template_id`
- Stage 2 page refactored to two-column Resolver Layout design: bottom controls in left panel; Result Diagnostics and old CSS layout preview removed; Resolver Layout section shows all region rows post-generation
- **Bottom contract gallery pair UI upgraded** (`strip_local_visible_only` count=2): `gallery_shell_height` 88→100, `gallery_items_height` 68→80, `item_width` 260→280, `gap` 20→16; pair now shows as a proper showcase, not a compressed strip
- **Title char budget relaxed** for 1-line clamp + light gallery + dense subtitle: `title_char_budget` 22→36; visual truncation now deferred to CSS `line-clamp` + `text-overflow: ellipsis` instead of early Python cut
- 116 poster2 tests passing

### Phase 3: next

- Replicate bottom resolver pattern to remaining regions: header, scenario, product, feature
- Complete `header_identity_zone_mode` resolver wiring
- Preview-path / generation-path parity收口 (Puppeteer vs Pillow)
- Beautification layer planning (downstream of behavior stability)

---

## Scope discipline

When a task is bounded, respect the boundary. Don't silently fix unrelated things nearby, don't use beautification to compensate for structural failures, and don't present a working sample render as evidence that the contract layer is correct.
