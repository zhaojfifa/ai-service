# Scenario Region — Resolver Coverage and Renderer Parity Status v1

**Branch:** `PosterSop06-beautification-phase1`
**Date:** 2026-03-29
**Phase:** Post-beautification-phase1 — scenario resolver evidence coverage

---

## What This Document Records

This document records the addition of dedicated `scenario_contract_review` evidence to the poster2 pipeline and formally scopes the renderer-path parity assessment for `scenario_region`.

---

## What Was Done

### 1. `_build_scenario_contract_review()` — pipeline.py

A new dedicated contract review builder for `scenario_region`, parallel in quality to `_build_bottom_contract_review`, `_build_header_contract_review`, and `_build_product_annotation_contract_review`.

Fields emitted:

| Field | Description |
|---|---|
| `hero_mode` | Active hero mode string |
| `scenario_enabled` | Whether scenario_region is enabled for this mode |
| `scenario_render_policy` | Resolver-assigned render policy |
| `requested_source` | Raw URL from request |
| `sanitized_source` | URL after spec normalization (equals requested for URLs) |
| `rendered_source` | Actual rendered source; `"safe_preset_image"` if safe fill applied |
| `safe_fill_applied` | Whether safe-fill was used in place of the requested image |
| `source_binding` | Canonical binding label: `"request.scenario_image.url"` |
| `scenario_region` | `{rendered, bounds}` — region-level render status and geometry |
| `scenario_slot` | `{rendered, reason_code, source_binding, bounds}` — slot-level status |
| `behavior_policy` | Resolver policy subset: render_policy, fit, anchor, peer_layout_policy, scenario layout_metrics |
| `renderer_path_parity` | Named parity note (see below) |
| `evidence_source` | Always `"resolver_layer_status"` |

### 2. `RenderManifest.scenario_contract_review` — contracts.py

New field exposed on `RenderManifest`. Default: `{}`.

### 3. Frontend read-through — app.js + stage2.html

- `app.js` binds `data?.scenario_contract_review` to `poster2-scenario-contract-review` element.
- `stage2.html` parses it as `scenarioReview` in `tryRebuild()`.
- `buildScenarioDetail(scenarioReview)` displays mode, render_policy, source, safe_fill badge, slot status.
- Fallback to `buildHeroDetail(heroReview, 'scenario_region')` when payload is absent (backward compatibility).

---

## Renderer-Path Parity Assessment

### Scope of This PR

This PR claims **resolver coverage** for `scenario_region`. It does **not** claim full renderer parity.

### Evidence Shape

Both Puppeteer and Pillow foreground renderers call the same `_build_renderer_layer_render_status()` function. The evidence *shape* (set of fields) is identical across both renderer paths.

### Known Value Divergence — safe_fill

| Condition | Pillow | Puppeteer |
|---|---|---|
| `scenario_cover_product_contain`, scenario image provided | `reason_code=None`, `safe_fill_applied=False` | `reason_code=None`, `safe_fill_applied=False` |
| `scenario_cover_product_contain`, **no** scenario image | `reason_code="scenario_missing"`, `safe_fill_applied=False` | `reason_code="safe_preset_fill"`, `safe_fill_applied=True` |
| `single_product_focus`, no scenario image | `reason_code="scenario_missing"`, `safe_fill_applied=False` | `reason_code="scenario_missing"`, `safe_fill_applied=False` |

**Root cause:** In `renderer.py`, `LayoutRenderer.render()` (Pillow) hardcodes `scenario_safe_fill=False`. `PuppeteerStructuredRenderer.render()` derives it conditionally as `behavior.hero_policy.scenario_enabled and not bool(asset_urls.get("scenario_is_real"))`.

This means `scenario_contract_review.safe_fill_applied` will be `False` for all Pillow-path renders, even when the scenario image is absent and the mode supports safe fill. The evidence for this case is inaccurate in the Pillow path.

### Open Follow-Up

| Item | Owner | Notes |
|---|---|---|
| Align Pillow `scenario_safe_fill` to mirror Puppeteer conditional logic | Renderer | Low risk; no visual change, evidence correction only |
| Add a cross-renderer parity test for `scenario_contract_review` evidence shape | Test suite | Blocked on above fix |

### Merge Claim (This PR)

- scenario_region has explicit contract review, bounds, source, and policy evidence ✓
- Stage 2 reads scenario evidence from backend payload ✓
- Renderer-path evidence differences are formally documented (safe_fill divergence) ✓
- Product annotation remains intact and backend-driven ✓

---

## Tests Added

| Test | File | Covers |
|---|---|---|
| `test_scenario_contract_review_exposes_full_evidence_for_scenario_cover_mode` | `tests/poster2/test_pipeline.py` | hero_mode, scenario_enabled, render_policy, source chain, safe_fill=False, region bounds, slot rendered+reason_code+bounds, behavior_policy, evidence_source, renderer_path_parity keys |
| `test_scenario_contract_review_exposes_disabled_policy_for_single_product_focus` | `tests/poster2/test_pipeline.py` | scenario_disabled, requested_source=None, region not rendered, slot not rendered, behavior_policy peer_layout_policy |
| `test_frontend_stage2_surfaces_scenario_contract_review` | `tests/test_stage2_guard_diagnostics_surface.py` | HTML element, buildScenarioDetail function, scenario_region uses new builder, fallback present, app.js binding |
