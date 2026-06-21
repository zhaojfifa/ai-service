# Banner Product Module — Finalize v1

Task: **POSTER2-BANNER-PRODUCT-SPEC-AND-DESIGN-REVIEW-V1**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`. Spec: `banner_product_module_spec_v1.md`.
Designer-style review: `docs/poster2/assets/banner_product_module_finalize_v1/visual_review.md`.

Finalizes the banner as a **route-specific product module** and answers the core product question with an honest
designer-perspective recommendation. Banner-layer only — body/layout, send path, P2A demo all unchanged; no AI images;
no `products[]`.

---

## 1. Product root cause

The banner was technically correct (composite fields exist) but read as a generic dark-bar-plus-logo template header
— it had no route intent and no premium treatment. The question was a **product/design** one, not a field-existence
one: can engineering reach a native CUISTANCE banner with existing assets, or is a designer base required?

## 2. Files changed

```
app/schemas/poster2.py          : (banner_variant remains a free str field; no literal change needed)
app/services/email/assembly.py  : route-specific product variants (brand_standard_header / campaign_poster_header /
                                  text_fallback_header) + route geometry + refined meta hierarchy (hairline + small caps)
app/main.py                     : (already wires banner_variant; unchanged this task)
frontend/cuistance_trial.html   : operator labels (品牌标准/营销海报/文字回退页眉) + route-default note + diag mapping (+mirror)
tests/poster2/...               : +3 route-default tests; 2 banner_variant assertions updated to product names
docs + evidence                 : spec, finalize doc, screenshots, designer visual_review, evidence.json, log
```

## 3. Banner product module spec (summary)

Full spec in `banner_product_module_spec_v1.md`. Route defaults: Fiche → `brand_standard_header` (medium, larger logo,
hairline + small-caps meta), Affiche → `campaign_poster_header` (tighter, smaller logo, compact meta; poster stays the
hero), fallback → `text_fallback_header`. Contrast: `on_dark` / `light_plate`. Logo = `email_banner.logo` only.

## 4. Fiche default banner result

`brand_standard_header` — `fiche_brand_standard_header.png`. Designer verdict **PASS_WITH_NITS** (clean, premium-ish,
does not overpower the serif title; but flat-plate → not bespoke).

## 5. Affiche default banner result

`campaign_poster_header` — `affiche_campaign_poster_header.png`. Designer verdict **PASS_WITH_NITS** (lighter/tighter so
the generated poster stays the hero; no double header).

## 6. Designer-style review verdict + recommendation

Reviewed across 10 designer criteria (brand presence, logo clarity, hierarchy, spacing, contrast, premium feel, body
fit ×2, email-native, template-feel). Both routes **PASS_WITH_NITS**.

**Recommendation: C — request a designer banner / base-lockup draft.** `designer_base_recommended = true`.

Honest rationale (not forced PASS): the route-specific headers are accepted as the **interim first-trial default** (they
meet the PASS_WITH_NITS bar and are route-correct), but they still read structurally as "dark plate + logo + text". The
remaining premium gap is a **design-asset gap**, not an engineering gap — the ttt reference's quality came from a subtle
background photo behind the header, which we deliberately avoid (it caused the earlier PSD header distortion bug). A
further engineering polish (option B) would not close the premium gap, so **C** over **B**.

## 7. Tests

```
+3 route-default tests (fiche->brand_standard, affiche->campaign_poster, no-logo->text_fallback) ;
2 banner_variant assertions updated to the product names.
Focused suites = 102 passed ; test_api -k email/workbench/selected/fiche/preview/send = 11 passed ;
node --check cuistance_trial.html = TRIAL_JS_OK ; check_docs_router --all = PASS.
```

## 8. Remaining HOLD

```
designer banner / base-lockup master : RECOMMENDED (the path to "premium native") — owner to commission
customer send / batch send           : HOLD
products[] / multi-product            : HOLD
P2A demo backend mapping              : HOLD
remote browser re-verify              : recommended after Render redeploys this commit
```
