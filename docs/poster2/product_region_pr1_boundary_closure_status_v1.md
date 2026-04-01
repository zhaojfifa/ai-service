# PR-1 — Product Region Boundary Closure Status v1

**Branch:** `claude/festive-heisenberg`
**Status:** In progress
**Date:** 2026-04-02

---

## 1. Scope

PR-1 closes the boundary model for:

- `product_region` outer container
- `product_card_shell_layer` (visible outer shell)
- `product_canvas_shell_layer` (image surface)
- `product_primary_slot` (dual mode upper image)
- `product_secondary_slot` (dual mode lower image)
- `feature_region` delegation / suppression confirmation

Not in scope for PR-1:
- product text shell work
- bottom / header / scenario behavior
- beautification
- annotation text lane geometry

---

## 2. Current Runtime Truth Before Fix

### Contract (from `template_behavior.py` constants)

| Surface | x | y | w | h | bottom edge |
|---|---|---|---|---|---|
| `product_region` / `product_card_shell_layer` | 456 | 188 | 472 | 540 | **728** |
| `product_canvas_shell_layer` | 456 | 188 | 300 | 540 | **728** |
| `product_primary_slot` (dual) | 456 | 188 | 300 | 310 | **498** |
| gap | — | 498 | — | 20 | **518** |
| `product_secondary_slot` (dual) | 456 | 518 | 300 | 210 | **728** |
| `product_single_primary_slot` | 456 | 188 | 300 | 540 | **728** |

Internal consistency: `310 + 20 + 210 = 540` ✓

### Mismatch Found — Puppeteer CSS

`app/templates_html/template_dual_v2.css`:

```css
/* Shared rule — sets height: 520px for both */
.region-shell-scenario,
.region-shell-product {
  top: 188px;
  height: 520px;   /* ← 520, not 540 */
  ...
}

/* Product override — missing height */
.region-shell-product {
  left: 456px;
  width: 472px;
  /* no height: 540px → inherits 520px from shared rule */
  ...
}

/* Canvas shell — correct */
.region-shell-product-canvas {
  top: 188px;
  height: 540px;   /* ✓ */
  ...
}
```

**Effect in Puppeteer:**
- `product_card_shell_layer` outer shell renders at h=520 → bottom at y=708
- `product_canvas_shell_layer` renders at h=540 → bottom at y=728
- `product_secondary_slot` image extends to y=728

The outer shell ends 20px above the canvas shell and secondary slot bottom. The secondary product image overflows the outer shell boundary visually.

**Pillow path:**
- Uses `_product_shell_bounds()` which reads `product_region_h=540` from metrics → correct, no fix needed.

---

## 3. Feature Region Confirmation

`feature_region` is delegated / suppressed correctly:
- When `feature_mode = product_anchor_callouts`: `feature_region` is `delegated_diagnostic`; annotation items go through product annotation path
- When `feature_mode = count_driven_callout_stack`: `feature_region` owns callouts directly
- `feature_region` is never a parallel owner with `product_region` for annotation text

No change needed for `feature_region`.

---

## 4. Fix

**File:** `app/templates_html/template_dual_v2.css`

Add `height: 540px` to the `.region-shell-product` override block so it no longer inherits the shared `height: 520px` from the `.region-shell-scenario, .region-shell-product` rule.

**Before:**
```css
.region-shell-product {
  left: 456px;
  width: 472px;
  border: var(--shell-border-product);
  background: var(--shell-surface-product);
}
```

**After:**
```css
.region-shell-product {
  left: 456px;
  width: 472px;
  height: 540px;
  border: var(--shell-border-product);
  background: var(--shell-surface-product);
}
```

---

## 5. Test Added

New test class `TestProductShellBoundaryClosure` in `tests/poster2/test_renderer.py`:

- Reads `template_dual_v2.css` directly
- Asserts the `.region-shell-product` override block contains `height: 540px`
- Asserts the `region-shell-product-canvas` block contains `height: 540px`
- Asserts `product_canvas_shell_layer` appears in rendered HTML

---

## 6. Frozen Unchanged

- `product_primary_slot`, `product_secondary_slot`, `product_single_primary_slot` constants — unchanged
- `_PRODUCT_REGION_OUTER_W`, `_PRODUCT_CANVAS_SHELL_W` — unchanged
- Pillow renderer `_product_shell_bounds` — unchanged (already correct)
- Annotation lane geometry — unchanged
- `feature_region` delegation logic — unchanged
- Bottom, header, scenario — unchanged
- No text-shell work

---

## 7. Files Changed

1. `app/templates_html/template_dual_v2.css` — add `height: 540px` to `.region-shell-product` override
2. `tests/poster2/test_renderer.py` — new `TestProductShellBoundaryClosure` class

---

## 8. Acceptance Evidence

After fix, runtime boundary model is coherent:

| Surface | Puppeteer CSS h | Contract h | Match |
|---|---|---|---|
| `product_card_shell_layer` outer shell | 540 | 540 | ✓ |
| `product_canvas_shell_layer` | 540 | 540 | ✓ |
| `product_primary_slot` (dual) | 310 (inline style) | 310 | ✓ |
| `product_secondary_slot` (dual) | 210 (inline style) | 210 | ✓ |

- Outer shell bottom at y=728 matches canvas shell bottom and secondary slot bottom
- Two product images are fully contained within the outer shell visual boundary
- `feature_region` remains delegated/suppressed — not a parallel owner
- Focused tests pass

---

## 9. Risks / Follow-up for Next PR

- PR-B (product text shell) remains the next priority — not started here
- The `region-shell-scenario` still has h=520 from the shared rule — this is the scenario region's correct size and was not changed
- No additional style gaps between slots and canvas shell were introduced; the 20px inter-slot gap remains correct by contract
