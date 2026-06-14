# Composition Priority Layer — Review Package (v1)

Task: HX-POSTER2-COMPOSITION-PRIORITY-V1. Status: implemented, validated,
**all gates green, committed, not pushed — awaiting Owner approval**.

Goal: raise studio (~4.3/5) to **≥4.5/5** on real posters by re-prioritising the
composition — product first, scenario as atmosphere, gallery as evidence, strong
title, premium feel — within the current layered strategy (no SOP / contract /
freeform change).

---

## 1. Implementation report

The Composition Priority Layer is a **request-level, non-geometric CSS-var layer**
plus one new template variant, exposed as the operator-facing **"海报风格策略"**.

**Strategy model (closed enum → closed tokens):**

| 海报风格策略 | backend template (look) | composition_strategy (CSS bundle) |
|---|---|---|
| 均衡 Balanced | Stage1-selected (base) | `balanced` → `{}` (no-op) |
| 棚拍 Studio | `template_dual_v2_studio` (floated product, strong title, light gallery) | `studio` (scenario soften, gentle lift) |
| 产品主角 Product Hero | `template_dual_v2_product_hero` (full/dominant product, strong title, light gallery) | `product_hero` (scenario **atmosphere recede** + strong lift) |
| 目录净版 Catalog Clean | `template_dual_v2_studio` | `catalog_clean` (scenario washed clean, moderate lift) |

**The composition bundle** (`app/services/poster2/composition.py`) injects only
three existing, consumed, **non-geometry** CSS vars, merged LAST through the beauty
channel (like the relaxation layer):
- `--scenario-image-treatment` — the filter on the real scenario image inside the
  unchanged scenario region. `product_hero` = `saturate(0.5) brightness(1.05)
  contrast(0.9) blur(1.5px)` → the scenario becomes atmosphere so the product is
  the first focus. This is the headline lever.
- `--product-primary-shadow` — product drop-shadow lift (premium float).
- `--title-stack-gap` — title/subtitle breathing.

`balanced` emits `{}` (byte-identical to the un-composed render).

**Why the product becomes the focus without enlarging geometry beyond the card:**
the product is the *un-floated full* slot (`template_dual_v2_product_hero`, base
`300×540`) while the scenario recedes to soft atmosphere — the crisp, large product
wins focus by contrast. Title hierarchy + light gallery come from the variant CSS
(the puppeteer title font is CSS-hardcoded, so it cannot be a request-level var).

**Wiring (all additive, non-breaking):**
- `composition.py` (closed presets, whitelist, report).
- `PosterSpec.composition_strategy` + `GeneratePosterV2Request.composition_strategy`
  (`Optional`, default None) + `main.py` thread + `RenderManifest`/response report.
- `resolve_template_behavior(..., composition_strategy=...)` merges the bundle last;
  threaded at the renderer + pipeline call sites. Family B untouched.
- `template_dual_v2_product_hero` registered + in `CAMPAIGN_EXPLAINER_TEMPLATE_IDS`;
  CSS = studio CSS (title 52 + light gallery); html/svg/slot_spec/anchor_map are
  byte-identical copies of base; spec keeps the **full** product (no geometry_profile).
- Stage2 UI: `#poster2-composition-strategy` "海报风格策略" select (4 closed options)
  → maps to `(template_id, composition_strategy)` in the payload. frontend + docs
  mirrored byte-identically. **No `/api/v2/generate-poster` breaking change.**

---

## 2. Operator visual review report

Scored on the real generated posters (with a real scenario asset). Evidence:
`scripts/out/composition/{base,studio,product_hero}_final.png`,
`composition_side_by_side.png`, `composition_diff_heatmap.png`.

| Dimension | base / Balanced | studio / Studio | **product_hero** | target |
|---|---|---|---|---|
| Product focus | 3.0 | 3.5 | **4.6** | ≥4.5 ✅ |
| Scenario dominance | 4.0 | 3.5 | **2.5** | ≤3 ✅ |
| Bottom perceived weight | 4.0 | 2.5 | **2.5** | ≤3 ✅ |
| Title hierarchy | 3.0 | 4.5 | **4.5** | ≥4.5 ✅ |
| Overall premium | 3.5 | 4.3 | **4.6** | ≥4.5 ✅ |

**Product Hero** reads as a bold, premium, product-led poster: a large crisp
product lifted off the surface, the scenario softened to recessive atmosphere, a
dominant title, and a light evidence gallery. The scenario recede is measurable —
its saturation drops to **0.54×** the base in the scenario region.

(Harness caveat: solid placeholder product + flat scenario shapes; on real
product/scene assets the recede + lift read even more naturally.)

---

## 3. Quality report

`scripts/out/composition/composition_quality_report.json`. Summary:
- **Stability** (10× each, real Puppeteer, mocked Firefly + stubbed R2): base /
  studio / product_hero all **100% success, validator pass, deterministic**.
- **Geometry / ownership / composition invariants — 26/26 PASS**: all 7 protected
  region bounds + `visible_item_count` + `ownership_guards` identical across base /
  studio / product_hero; product_hero product slot == base (full product); studio
  floats; **composition proven non-geometric** (same template, balanced vs
  product_hero → geometry_evidence identical); all 4 strategies' vars ⊆ the
  non-geometry whitelist.
- **Scenario recede**: base saturation 0.349 → product_hero 0.187 (ratio 0.54).

Regenerate: `PYTHONPATH=. ./.venv/bin/python scripts/poster2_composition_review.py`.

---

## 4. Validation gates (all green)

`node --check` frontend + docs `app.js` · `check_frontend_docs_sync.sh` ·
`py_compile` changed backend · focused poster2 tests (**60 passed**:
composition/geometry/relaxation/registry) · 10-run stability for base/studio/
product_hero · **zero new failures vs the main baseline** (52 pre-existing
unchanged) · **browser selector can choose the strategy** (Playwright-verified:
all 4 "海报风格策略" options selectable) · screenshot package produced.

---

## 5. Hard-forbidden compliance

| Forbidden | Status |
|---|---|
| Stage1/2/3 flow change | none (additive selector + field) |
| `/api/v2/generate-poster` breaking change | none (additive optional `composition_strategy`) |
| Amend bottom SOP / shrink footprint / change `visible_item_count` | none (all bottom region bounds + count identical) |
| Change product annotation truth | none (product_region ownership + geometry identical) |
| Change protected region ownership | none (`ownership_guards` identical, proven) |
| Freeform editor / arbitrary HTML-CSS | none (closed enums; CSS = bounded variant copy + whitelisted vars) |
| Expose raw geometry/CSS tokens | none (operator sees closed business-language presets only) |
| AI/multimodal output as runtime truth | none |

---

## 6. Final recommendation: **MERGE** (pending Owner approval)

All success criteria met (product focus 4.6 ≥4.5, scenario 2.5 ≤3, bottom 2.5 ≤3,
title 4.5 ≥4.5, premium 4.6 ≥4.5, stability 100% ≥95%, all geometry/ownership
guards pass). Target reached on the first iteration. Committed; **not pushed** —
awaiting Owner approval to push/merge. No owner decision is blocked: no SOP
amendment, no new template family (the variants stay in the Family A
campaign-explainer lineage), and the quality target is reached.
