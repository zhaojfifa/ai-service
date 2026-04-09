# Session State — 2026-03-31

**Branch:** `fix/pr7-product-truth-only`
**Remote base:** `origin/main` at `34e1294`
**Last updated:** 2026-03-31

---

## Current branch health

| Metric | Value |
|---|---|
| `degraded` | `false` |
| `structure_complete` | `true` |
| `deliverable` | `true` |
| `product_geometry_mode` | `primary_secondary_dual_v2` |
| `scoped_validation` | `green` |

---

## PR-7 — Product image contract: bounds and fit authoritative from product_policy

**Source commit:** clean-room cherry-pick of `6a79e53`

**Three gaps closed:**

| Location | Old | New |
|---|---|---|
| `_build_product_annotation_contract_review()` | `hero_policy.layout_metrics["product_region_*"]` | `product_policy.layout_metrics["product_region_*"]` |
| `_product_image_slot()` single_primary | bounds from `hero_policy.layout_metrics` | bounds from `product_policy.product_primary_slot` |
| renderer fit | `hero_policy.product_fit` hardcoded | `product_policy.product_primary_image_fit` from resolver |

**New field:** `ResolvedProductBehavior.product_primary_image_fit`

**Focused validation run on clean merge path:**
- `.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'TestProductImageContract'`
- `.venv/bin/python -m pytest -q tests/poster2/test_renderer.py tests/poster2/test_pipeline.py -k 'product and not header and not scenario and not bottom'`

---

## Current PR status

| PR | Content | Status |
|---|---|---|
| PR-1 | Bottom mode semantic unification | ✅ Complete |
| PR-2 | Bottom mode boundary freeze | ✅ Complete |
| PR-3 | Product owner surfaces + dual-image geometry freeze | ✅ Complete |
| PR-4 | Text layer ownership freeze + feature delegation | ✅ Complete |
| PR-5 | Post-freeze text capacity optimization | ✅ Complete |
| Task-2 | Product region final geometry | ✅ Complete |
| PR-7 | Product image contract: product_policy authority | ✅ Complete |
| PR-8 | Annotation/text contract | Next |

---

## Remaining open items

- `product_secondary_slot`: Pillow renderer parity
- `scenario_region`: Pillow safe_fill parity fix
- Preview-path / generation-path parity (Puppeteer vs Pillow)
- Beautification layer planning (after all-region behavior stability)
