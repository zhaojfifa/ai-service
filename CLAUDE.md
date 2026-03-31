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

## poster2 phase state (as of 2026-03-30)

### PR-5 — Post-freeze text capacity optimization — COMPLETE (2026-03-30)

char_budget floors raised across three target areas. No contract changes, no mode changes, no geometry changes.

**title_gallery_split (text_gallery_expanded) — all six tiers raised:**
- Dense-quad: `title_char_budget` 44→52, `subtitle_char_budget` 44→48
- Triplet: `title_char_budget` 52→60, `subtitle_char_budget` 52→56
- Light gallery (1–2): `title_char_budget` 60→72, `subtitle_char_budget` 56→60
- Subtitle only (not dense): `title_char_budget` 52→60, `subtitle_char_budget` 36→40
- Long title, no subtitle: `title_char_budget` 52→60
- Compact: `title_char_budget` 44→52

**Product annotation char_budget:** `{1:36, 2:30, 3:24}` → `{1:40, 2:34, 3:28}`

**Header agent_char_budget:** 24→28 (`identity_left_agent_right` + `brand_block_two_line`)

`TestPostFreezeTextCapacity`: 10 new floor-assertion tests. 262/262 tests pass.

### PR-4 — Text ownership freeze and feature delegation — COMPLETE (2026-03-30)

- `_TEXT_LAYER_OWNER_MAP` / `_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS` / `_PRODUCT_ANNOTATION_TEXT_OWNER_REGION` declared as constants
- All three text layers emit `ownership_frozen = True`
- `feature_view_mode = delegated_diagnostic` enforces no dual ownership when annotation active
- 252/252 tests pass

### Family A structural closeout — COMPLETE (2026-03-30)

Three contract-level scopes closed. Ends the budget-tuning loop; places Family A on structurally sound path.

**Scope A — Bottom structural expansion**
- `text_only_expanded` (shell y=656, 368px capacity) and `text_gallery_expanded` (shell y=640, 384px capacity) added as first-class `bottom_layout_mode` values
- Dense-quad no longer forces `title_char_budget=20`; expanded mode allows `title_char_budget=44` minimum alongside 4 gallery items (raised to 52 in PR-5)
- `bottom_layout_mode` + `bottom_shell_top` emitted in `ResolvedBottomBehavior` evidence

**Scope B — Product layout contract + renderer parity**
- `product_layout_mode = single_primary | primary_secondary_dual` in `TemplateBehaviorModesSpec`
- `ResolvedProductBehavior` exposes `product_primary_slot`, `product_secondary_slot`, `product_secondary_slot_rendered`, `product_secondary_asset_policy`
- Annotation shell stays on `product_primary_slot` only; secondary slot is independent
- Puppeteer renderer wired end-to-end for dual-image path

**Scope C — Text layer evidence**
- `title_text_layer`, `subtitle_text_layer`, `header_text_layer` promoted to first-class `RenderManifest` fields
- Each field: `requested_text → sanitized_text → rendered_excerpt`, `truncation_applied`, `slot_bounds`, `line_clamp`, `char_budget`, `owner_region`

### Scenario region — resolver evidence COMPLETE

- `scenario_contract_review` emitted per generation: hero_mode, scenario_enabled, render_policy, source chain, safe_fill_applied, scenario_region bounds, scenario_slot, behavior_policy
- Stage 2 Resolver Layout: `buildScenarioDetail(scenarioReview)` reads from backend payload
- Known open gap: Pillow `safe_fill` always False vs Puppeteer conditional — documented, tracked

### Product annotation layer — ACTIVATED

- `feature_mode` in `template_dual_v2.json` is `product_anchor_callouts` (production default)
- `product_annotation_contract_review` emitted per generation
- Stage 2: annotation chip + detail panel for `product_region`

### Prior phases still established

- **PR-1 through PR-3**: bottom mode unification, boundary freeze, product owner surfaces freeze
- **Phase 2 (bottom SOP)**: `bottom_region` resolver baseline
- **Beautification Phase 1**: `glass_light` shell, `soft_line` border, `soft` shadow, feature connector/marker visual

### PR-7 — Product image contract: bounds and fit authoritative from product_policy — COMPLETE (2026-03-31)

Closes the split between `hero_policy` and `product_policy` as authority for product image geometry.

**Three gaps closed:**
1. `_build_product_annotation_contract_review()` was reading `product_region.bounds` from `hero_policy.layout_metrics` → now reads from `product_policy.layout_metrics`
2. `_product_image_slot()` single_primary path was using `hero_policy.layout_metrics` for slot bounds → now uses `product_policy.product_primary_slot` (same values, correct authority)
3. Image fit policy was scattered in renderer (`hero_policy.product_fit`) → lifted to `product_policy.product_primary_image_fit` declared at resolver level

**Changes:**
- `template_behavior.py`: `product_primary_image_fit: str` added to `ResolvedProductBehavior`; set from `hero_policy.product_fit` in `resolve_product_behavior()`
- `renderer.py`: `_product_image_slot()` — single_primary path now uses `product_policy.product_primary_slot` for bounds and `product_policy.product_primary_image_fit` for fit
- `pipeline.py`: `_build_product_annotation_contract_review()` bounds fixed to product_policy; `_build_product_contract_review()` exposes `product_primary_image_fit`

`TestProductImageContract`: 5 tests. 262/262 scoped tests pass.

### PR-8A — Safe product-geometry widening baseline with frozen bottom and annotation/text lane — ACCEPTED INTERMEDIATE (2026-03-31)

State read before coding:
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `project_poster2_baseline_2026-03-30.md` — missing in this workspace; recorded explicitly and did not block the PR

Contract truth changed:
- `product_region.w` widened `300 -> 320`
- `product_primary_slot.w` widened `300 -> 320`
- `product_secondary_slot.w` widened `300 -> 320`
- `_PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT.w` widened `300 -> 320`
- `template_dual_v2` version bumped `2.1.4 -> 2.1.5`

What remained frozen:
- `bottom_shell_top` unchanged
- `title_band_region` / `gallery_strip_region` unchanged
- annotation ownership unchanged: `annotation_owner_slot = product_primary_slot`
- annotation lane / annotation shell computation unchanged
- no text budget tuning, no header/scenario work, no beautification

Focused tests run:
- `.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TestProductLayoutContract or TestProductOwnerSurfaceFreeze or TestTask2FinalProductGeometry or TestProductImageContract'` → `29 passed`
- `.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'product and not header and not scenario and not bottom'` → `1 passed`
- `.venv/bin/python -m pytest -q tests/poster2/test_contracts.py -k 'TestTemplateSpecLoading'` → `12 passed`

### Next

- **PR-8B only**: Annotation/text contract — annotation shell, anchors, connectors, markers, label bounds, and text placement mode
- `product_secondary_slot`: Pillow renderer parity (contract-only for now)
- `scenario_region`: Pillow safe_fill parity fix (after annotation contract)
- Beautification layer planning (after all-region behavior stability)

### Gate-unblock PR — Glibatree OpenAI import compatibility (2026-03-31)

State read before coding:
- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `project_poster2_baseline_2026-03-30.md` — missing in this workspace; recorded explicitly and did not block the task

Scope:
- fix only the non-PR-8B merge-gate failure in `tests/test_glibatree_openai.py`
- no poster2 changes
- no PR-8A / PR-8B changes

What changed:
- restored `_request_glibatree_openai_edit` in `app/services/glibatree.py` as a backward-compatible OpenAI edit shim for the legacy import surface
- aligned `tests/test_glibatree_openai.py` with the current `GlibatreeConfig` dataclass by removing the obsolete `client` constructor field

Why this was the smallest backward-compatible fix:
- the gate failure started as an import error on a removed symbol
- restoring the symbol preserves backward compatibility for existing tests/callers
- updating the test’s config construction avoids reintroducing an obsolete public config field just for test compatibility

Validation:
- `.venv/bin/python -m pytest -q tests/test_glibatree_openai.py` → `2 passed`
- `.venv/bin/python -m pytest -q --collect-only tests/test_glibatree_openai.py` → `2 tests collected`

Next:
- merge this gate-unblock PR first
- then return to `fix/pr8b-annotation-text-contract`, rebase onto new `main`, rerun merge gate, and merge PR-8B only if the full suite passes

---

## Scope discipline

When a task is bounded, respect the boundary. Don't silently fix unrelated things nearby, don't use beautification to compensate for structural failures, and don't present a working sample render as evidence that the contract layer is correct.
