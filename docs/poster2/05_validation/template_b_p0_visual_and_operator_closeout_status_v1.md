# Template B P0 Visual And Operator Closeout Status v1

## Scope

This note records the combined closeout of:

- `PR-TB-P0B` — Puppeteer expression tightening
- `PR-TB-P0C` — Stage1 / Stage2 operator-line closure

It does not reopen Template B geometry, Family A behavior, Stage 3, or editor/runtime architecture.

## What Changed

### 1. Template B visual hierarchy tightened

- banner surface reduced one step in weight so the product hero remains first-read
- top-copy title/subtitle hierarchy tightened toward a product-sheet reading order
- materials strip softened into a supporting evidence strip
- hero wash / halo / plane reduced so the primary product reads more clearly
- secondary inset softened into a supporting detail role
- description panel tightened into a calmer information block

### 2. Stage1 Template B workline fixed

- product asset inputs are no longer hidden when Template B is selected
- `product_image_2` is now surfaced as an optional supporting detail image
- `materials_images` wording now frames the strip as accessory / sample / material evidence, not gallery
- Template B preview remains a Family B vertical product-sheet skeleton

### 3. Stage2 Template B workline fixed

- Template B summary labels now reflect Family B product-sheet semantics
- Stage2 no longer disables `puppeteer` for Template B
- Template B request build path now preserves the selected renderer mode instead of coercing `puppeteer` back to `auto`

## Files Changed

- `app/templates_html/template_product_sheet_v1.css`
- `frontend/index.html`
- `frontend/stage2.html`
- `frontend/app.js`
- `frontend/styles.css`
- `docs/index.html`
- `docs/stage2.html`
- `docs/app.js`
- `docs/styles.css`
- `tests/test_frontend_docs_sync.py`

## Validation

- `./.venv/bin/python -m py_compile app/services/poster2/template_behavior.py app/services/poster2/pipeline.py app/services/poster2/renderer.py`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TemplateBBackendGenerationFix or test_template_a_regression_path_remains_unchanged'`

## Remaining Gaps

- a live Template B run with real uploaded assets should still be checked after merge for final visual confirmation
- this pass intentionally avoids geometry change and broader style exploration
- if future product-sheet presets are added, Stage1 wording will need to remain Family B-specific and not drift back toward Family A gallery semantics
