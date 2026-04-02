# PR-3 — Product Text-Layer UI and Stage2 Driver Wiring Status v1

**Branch:** `claude/festive-heisenberg`
**Status:** In progress
**Date:** 2026-04-02

---

## 1. Scope

PR-3 wires Stage2 diagnostics UI to the product text-shell truth already established by PR-2.

In scope:
- Add `text_shell` status chip to `buildProductDetail` (alongside image / secondary / annotation chips)
- Add `product_text_shell_layer` bounds row: `(x, y, w, h)` · `owner_region / owner_surface`
- Add `text_does_not_compete_with_canvas` badge
- Show full annotation slot text chain: `requested` → `sanitized` (if sanitization occurred) → `rendered_excerpt` (if truncated)
- Show `char_budget` and `line_clamp` from `productReview.behavior_policy`
- Add focused frontend guard test `test_frontend_stage2_surfaces_product_text_shell_evidence`
- Keep `frontend/app.js` and `docs/app.js` aligned (no changes needed — app.js already forwards `product_contract_review`)
- Mirror `frontend/stage2.html` → `docs/stage2.html`

Not in scope for PR-3:
- Backend contract changes
- CSS / HTML structural changes for the poster render
- Annotation geometry tuning
- char_budget / line_clamp value tuning
- Bottom / header / scenario behavior
- Beautification
- `feature_region` ownership model changes
- PR-C capacity / label bounds / clamp / connector tuning

---

## 2. Precondition: PR-2 Truth Loaded

From `product_region_pr2_text_shell_contract_status_v1.md`:

- `product_text_shell_layer` is an explicit sibling shell in `_FROZEN_PRODUCT_OWNER_SURFACES`
- `product_contract_review.product_text_shell_layer` carries: `rendered`, `reason_code`, `bounds`, `owner_region`, `owner_surface`, `text_does_not_compete_with_canvas`
- `product_contract_review.behavior_policy` carries: `char_budget`, `line_clamp`, `layout_metrics`
- `product_contract_review.annotation_slots[i]` carries: `requested_text`, `sanitized_text`, `rendered_excerpt`, `truncation_applied`
- `feature_region` is delegated diagnostic when annotation is active; not a parallel text owner

```
product_text_shell = {x: 784, y: 216, w: 144, h: 260}
```

No-compete: `text_shell_x (784) >= canvas_right (456 + 300 = 756)` ✓

---

## 3. UI Changes

### 3.1 Status chip: `text_shell`

Added as a fourth chip in `buildProductDetail` chips row (after `annotation`):

```javascript
html += `<span ...>text_shell ${slotStatusHtml(productReview.product_text_shell_layer?.rendered, productReview.product_text_shell_layer?.reason_code)}</span>`;
```

### 3.2 Text shell bounds / owner / no-compete row

Added after slot geometry chips (reads from `productReview.product_text_shell_layer`):

```
text_shell (784,216,144,260) · owner: product_region / product_text_shell_layer  [no-compete-with-canvas ✓]
```

### 3.3 Annotation slot text chain

`buildProductDetail` annotation slots loop enhanced:
- Show `char_budget` and `line_clamp` from `productReview.behavior_policy` before the per-slot rows
- For each slot: show `requested_text` → `sanitized_text` arrow (if sanitization occurred)
- If truncation also applies: show a second `↳ rendered` row

### 3.4 `feature_region` remains delegated diagnostic

No change to `buildFeatureDetail`. When `delegated_to_product_annotation` is true, UI continues to show the `delegated to product_annotation` badge. Feature region is not a parallel owner in UI semantics.

---

## 4. Files Changed

1. `frontend/stage2.html`
   - `buildProductDetail`: text_shell chip, text shell bounds/owner/no-compete row, full annotation slot text chain, char_budget/line_clamp

2. `docs/stage2.html`
   - Mirror of `frontend/stage2.html`

3. `tests/test_stage2_guard_diagnostics_surface.py`
   - New test: `test_frontend_stage2_surfaces_product_text_shell_evidence`

No backend changes. `frontend/app.js` and `docs/app.js` are unchanged — both already forward `product_contract_review` from the backend payload.

---

## 5. Frozen Unchanged

- `product_primary_slot` / `product_secondary_slot` geometry — unchanged
- `product_canvas_shell_layer` — unchanged
- `product_text_shell` contract semantics — unchanged
- Annotation lane / connector / marker / label bounds — unchanged
- `char_budget` / `line_clamp` values — unchanged
- Bottom / header / scenario — unchanged
- Beautification — frozen
- Backend `pipeline.py`, `template_behavior.py`, `renderer.py`, `contracts.py` — no changes
- `frontend/app.js` / `docs/app.js` — no changes

---

## 6. Acceptance Evidence

- `buildProductDetail` reads `product_text_shell_layer` from backend `product_contract_review` payload ✓
- `text_does_not_compete_with_canvas` badge visible in UI when true ✓
- `owner_region` / `owner_surface` displayed ✓
- Annotation slot text chain shows `requested` / `sanitized` / `rendered` stages ✓
- `char_budget` and `line_clamp` displayed from `behavior_policy` ✓
- `feature_region` remains delegated diagnostic — no parallel ownership in UI ✓
- `docs/stage2.html` == `frontend/stage2.html` ✓
- Focused guard test passes ✓

---

## 7. Test Commands and Results

```
.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py -k 'product_text_shell'
.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py
.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TestProductTextShellContract'
```

Results: see execution log entry.

---

## 8. Risks / Follow-up for PR-C Only

- PR-C: capacity / label bounds / clamp / connector tuning — NOT started here
- No CSS change in this PR; visual rendering of text shell appearance is PR-C territory
