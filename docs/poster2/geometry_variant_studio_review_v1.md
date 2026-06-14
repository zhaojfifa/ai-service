# Geometry Style Variant — `template_dual_v2_studio` Review Package (v1)

Task: HX-POSTER2-STYLE-VARIANT-V1. Branch: `poster2-vrelax-heavy-v1`.
Status: implemented, validated, **awaiting Owner approval** (do not merge yet).

The Visual Relaxation Layer proved the remaining visual problem is **geometry, not
spacing/shadow**. This variant makes a *bounded* geometry change (the product image
floats inside its unchanged card) plus typography/surface changes, while keeping
every protected region boundary, ownership guard, the 3 product-annotation slots,
and the bottom-SOP geometry byte-identical to the base.

---

## 1. What changed (and what did not)

| Goal | How (bounded, in-contract) | Proven unchanged |
|---|---|---|
| **Product breathing** | `behavior_modes.geometry_profile = "studio_breathing_v1"` → `resolve_product_behavior` floats the product IMAGE slot to `{x:474, y:224, w:264, h:468}` (was `456/188/300/540`) inside the **unchanged** product card | `product_region` bounds (`456/188/504/540`), the product card (canvas/shell), ownership, and annotation anchors |
| **Title hierarchy** | Variant CSS `.text-title` 40→**52px** (puppeteer) + spec `title_slot.font_size 52` (Pillow); subtitle recedes (17→16px, lower opacity) | `title_band_region` bounds (`112/728/800/144`) — only text reflows inside |
| **Bottom weight reduced** | (a) the stronger title **leads** the bottom; (b) variant CSS lightens the gallery **strip surface** (background/border/shadow) so it recedes | `gallery_strip_region` bounds, `bottom_region` bounds, `visible_item_count` (gallery still renders 4) — geometry/evidence untouched, **surface only** |

Mechanism mirrors the relaxation/airy precedent: a registered Family-A campaign-
explainer variant with its own spec + assets. Only the **CSS** differs from the
base assets; `html`/`svg`/`slot_spec`/`anchor_map` are byte-identical copies. The
product geometry flows from a `geometry_profile`-keyed branch in
`resolve_product_behavior` (defaulting to `"default"`, so base + airy are untouched).

---

## 2. Required outputs

- **Before/after screenshots** — `scripts/out/studio/`:
  `template_dual_v2_final.png`, `template_dual_v2_studio_final.png`,
  `studio_side_by_side.png`, `studio_zoom.png`, `studio_diff_heatmap.png`.
- **Quality report** — `scripts/out/studio/geometry_variant_quality_report.json`
  (regenerate: `PYTHONPATH=. ./.venv/bin/python scripts/poster2_geometry_variant_review.py`).
- **Operator review** — §4 below.
- **Implementation report** — §1, §3, §6 + the execution-log entry.

The diff heatmap shows the change is **surgically confined** to three areas —
product image (breathing), title text (hierarchy), gallery strip surface (bottom
weight). Header, scenario, and the feature callouts/annotations show **zero change**.

Per-band change (studio vs baseline): header 0.00% · product 9.94% ·
title band 10.47% · gallery 10.47% · **total 10.21% of canvas** (vs airy's 3.53%).

---

## 3. Validation

- **Stability (10× each, real Puppeteer, mocked Firefly/R2)** — baseline + studio
  both **100% success**, validator pass, deterministic single hash each
  (base `16147a03…`, studio `eeeb22e2…`). ≥95% bar met.
- **Geometry / ownership invariants** (all PASS): every protected region bound
  (`header / scenario / product / feature / bottom / title_band / gallery_strip`)
  identical; `visible_item_count` identical; `ownership_guards` identical; the
  **only** slot delta is the product image slot.
- **Tests** — `tests/poster2/test_geometry_variant.py` (10 cases) pass; full
  poster2 suite shows **zero new failures** vs the post-relaxation baseline; base +
  airy geometry unaffected (`geometry_profile == "default"`).
- `node --check` (both), `check_frontend_docs_sync.sh`, `py_compile` — pass.

---

## 4. Operator visual review

| Dimension | Score | Notes |
|---|---|---|
| Product breathing | **4 / 5** | Product floats with clear margin inside its card — reads as a premium "product on a clean card." Not cramped. |
| Title hierarchy | **4.5 / 5** | Title clearly dominant (52 vs 40), subtitle recedes. Strong, balanced. |
| Bottom weight | **4 / 5** | Gallery strip recedes (lighter), title leads the bottom. Footprint unchanged (SOP), perceived weight clearly reduced. |
| No region break | **5 / 5** | Gallery renders 4 items; all regions intact (proven). |
| Contract safety | **5 / 5** | Ownership / bottom-SOP geometry / annotation truth all byte-identical (proven). |
| **Overall** | **≈ 4.3 / 5** | Meets the ≥4/5 bar. Cohesive, tasteful, safe. |

Harness caveat: the product is a solid placeholder block and gallery thumbnails
are flat colour swatches, so on real product/packshot assets the breathing and the
receding gallery will read more naturally than in the synthetic evidence.

---

## 5. Success criteria

| Criterion | Status |
|---|---|
| Product breathing improved | ✅ image floats with margin |
| Title hierarchy improved | ✅ 40→52, subtitle recedes |
| Bottom weight reduced | ✅ perceived (gallery surface recedes + title-led). ⚠️ geometric *footprint* not reduced — see §6 |
| No ownership violations | ✅ `ownership_guards` identical (proven) |
| No bottom SOP violations | ✅ bottom/title/gallery region bounds + `visible_item_count` identical; surface-only |
| No annotation truth violations | ✅ 3 slots, owner=`product_region`, anchors unchanged |
| Stability ≥95% | ✅ 100% / 100% |
| Operator review ≥4/5 | ✅ ≈4.3/5 |

---

## 6. Owner decision needed (one item)

**Geometric bottom-footprint reduction is blocked by frozen bottom SOP.** The
bottom shell top is frozen at its minimum (`y=728`, 296 px footprint) across all
governed modes; making the bottom physically *smaller* requires a new
`bottom_mode` / a change to `_EXPANDED_BOTTOM_SHELL_TOPS`, i.e. a **bottom
SOP / geometry-contract amendment** — an Owner decision per the SOP. This variant
therefore reduces **perceived** bottom weight (surface + title-led), not the 296 px
footprint. If the Owner wants the bottom physically smaller, that is a separate
SOP-amendment task.

No other owner decision is required: no new template family, geometry contract
(beyond the above), and the ≥4/5 quality target is reached.

---

## 7. Stop point

Implementation complete and validated; **not merged**. Awaiting Owner approval and
the §6 decision on whether geometric bottom-footprint reduction should be pursued
as a follow-up SOP amendment.
