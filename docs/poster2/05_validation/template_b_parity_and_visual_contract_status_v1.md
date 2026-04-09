# Template B Parity And Visual Contract Status V1

## Scope

PR-TB-P1 closes the visible-truth gap for `template_product_sheet_v1` without reopening Template B family routing, region order, or broad beautification.

Frozen Family B region order remains:

1. `logo_banner_region`
2. `top_copy_region`
3. `materials_strip_region`
4. `product_hero_region`
5. `description_region`

## Root Rules Followed

- contract-first
- renderer executes; renderer does not define template truth
- backend evidence remains the source of truth
- Template A behavior and geometry left unchanged
- Stage2 source and `docs/` publish mirror updated together

## Problem Reproduced

Latest Template B runtime metadata reported a clean Family B contract path, but the final visible render still drifted from that truth:

- header content could escape or visually misalign from the banner
- top-copy layers could visually drift relative to their declared region
- product hero dominance could be diluted by shell/content rooting mismatch
- description content could visually read as competing with hero occupancy

The problem was parity between declared geometry and actual rendered DOM, not family ownership routing.

## Root Cause

Template B HTML used nested positioned containers while several inline slot styles still carried canvas-global coordinates.
That created a mixed coordinate-root situation:

- contract bounds were declared in poster-root coordinates
- visible DOM nodes were rendered inside nested Family B containers
- final Puppeteer output could therefore drift even while resolver metadata stayed nominally correct

The runtime also lacked DOM-derived visible-truth evidence, so it could still report clean structure truth when visible containment had drifted.

## Layer Changed

- renderer
- validation / metadata
- frontend Stage2 diagnostics
- Stage1 / Stage2 Family B preview projection
- docs

## Files Changed

- `app/services/poster2/renderer.py`
- `app/services/poster2/pipeline.py`
- `app/services/poster2/contracts.py`
- `app/schemas/poster2.py`
- `app/main.py`
- `app/templates_html/template_product_sheet_v1.html`
- `app/templates_html/template_product_sheet_v1.css`
- `frontend/app.js`
- `frontend/stage2.html`
- `frontend/index.html`
- `frontend/styles.css`
- `docs/app.js`
- `docs/stage2.html`
- `docs/index.html`
- `docs/styles.css`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`

## Exact Parity Fields Added

Backend now emits Template B visible-truth evidence for rendered DOM targets, including:

- `visible_bounds`
- `layout_bounds`
- `overflow_state`
- `clipping_state`
- `computed_opacity`
- `stacking_context`
- `transform_summary`

New manifest / API fields:

- `visible_truth_evidence`
- `template_b_parity_review`

Template B parity review now exposes:

- `header_in_banner`
- `top_copy_in_region`
- `hero_in_region`
- `description_in_region`
- `parity_failure_reasons`
- per-target containment details under `targets`

## Contract-Execution Fixes

### Family B HTML/CSS rooting

- Template B header, top-copy, product hero, and description slot positioning now localize to the correct Family B region root before HTML render.
- Family B markup now carries explicit parity keys for DOM evidence collection.
- Product hero no longer mixes root-relative shell truth with nested container-relative slot rendering.

### Visible-truth enforcement

- Puppeteer collects DOM/computed evidence after page stabilization and before screenshot capture.
- Pipeline builds Template B parity assertions from DOM visible bounds against backend geometry evidence.
- If parity fails on Puppeteer, the pipeline no longer reports clean structure truth.

### Evidence cleanup

- `sku_text` is now passed into slot-binding evaluation, removing the false `sku_text_slot` collapse case for Template B.
- suppressed Template B header agent no longer reports `agent_truncation_applied=true`

### Preview / diagnostics alignment

- Stage2 diagnostics now surfaces backend Template B parity chips:
  - header in-banner
  - top-copy in-region
  - hero in-region
  - description in-region
- Stage1 / Stage2 Family B preview now follows the same vertical product-sheet projection instead of a mixed banner/SKU/hero preview arrangement.

## Validation Run

- `./.venv/bin/python -m py_compile app/services/poster2/renderer.py app/services/poster2/pipeline.py app/services/poster2/contracts.py app/schemas/poster2.py app/main.py`
  - pass
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TemplateBBackendGenerationFix'`
  - `13 passed, 266 deselected`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py`
  - `6 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py -k 'template_b or generate_poster_v2_accepts_template_b'`
  - `4 passed, 23 deselected`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py -k 'template_b_independent_preview_and_generate_path_are_present or stage1_operator_surfaces_and_publish_mirror_are_aligned'`
  - `2 passed, 3 deselected`

## Remaining Risks

- local validation still does not produce a fresh live Chromium screenshot artifact bundle in this repo, so the before/after visual proof remains dependent on the next live Puppeteer run
- visible-truth parity is enforced only on actual Puppeteer renders, not on Pillow fallback
- if future Template B HTML adds new nested containers, parity keys must remain aligned with the backend target map or the new evidence will go stale
