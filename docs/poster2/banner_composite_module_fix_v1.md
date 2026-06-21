# Banner Composite Module Fix v1

Task: **POSTER2-CUISTANCE-BANNER-COMPOSITE-MODULE-FIX-V1**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`. Design: `banner_composite_module_design_v1.md`.

Makes the banner a first-class **composite header module** (`email_banner_composite`) instead of a single logo-image
flag. Banner-layer only — no body redesign, no AI images, no send rebuild, no `products[]`, P2A demo untouched.

---

## 1. Root cause

The banner was a logo flag (`header_logo_used=true`) rendered as a plain dark slab + raw logo image + one meta line.
The operator's dark logo (`logo_01.jpg`) was invisible dark-on-dark, and there was no lockup (channel/campaign
composition), so it read as an engineering bar rather than a designed ttt/ttt2 banner.

## 2. Files changed

```
app/schemas/poster2.py          : EmailBanner.banner_logo_contrast_mode; 6 additive response fields
app/services/email/assembly.py  : email_banner_composite rendering (plate + lockup + channel + campaign pill + filet),
                                  banner_variant mapping, contrast modes, diagnostics
app/main.py                     : wire the 6 new response fields
frontend/cuistance_trial.html   : banner variant rename + contrast mode UI + diagnostics  (+ docs mirror)
tests/poster2/...               : +4 composite tests
docs + evidence                 : design, fix doc, screenshots, visual_review, evidence.json, log
```

## 3. Banner composite design

```
email_banner_composite = background_plate (#1f2329) + brand_lockup (logo OR white wordmark)
                         + channel_line (channel_name) + campaign_tag (campaign_label, red-bordered pill)
                         + red_filet (#E1002A, full 600px)
variants: ttt_banner_composite (default w/ logo) | compact_logo_banner | text_wordmark_fallback
mapped 1:1 from header_variant (ttt_logo_banner | logo_image_bar | css_dark_bar_wordmark) — backward compatible
contrast: banner_logo_contrast_mode = on_dark (default; light logo) | light_plate (dark logo -> white plate)
asset safety: banner/logo uses email_banner.logo ONLY — never product/gallery/atmosphere/generated-poster/AI
```

`banner_source` includes a reserved `default_banner_lockup_asset` value — NOTE: `~/poster/ingredient/logo banner.png`
is a Photoshop layers-panel screenshot, not a clean hosted banner image, so it is not adopted; the field is reserved.

## 4. Fiche result

`ttt_product_sheet_container` retained; banner is now the composite lockup (logo + "CUISTANCE Europe" channel +
"NOUVEAUTÉ" pill + red filet). Verdict: **PASS** (`fiche_banner_composite.png`).

## 5. Affiche result

`ttt2_campaign_container` retained (no double header, no spec duplication); same composite banner framing the poster
body. Verdict: **PASS** (`affiche_banner_composite.png`).

## 6. Diagnostics exposed

```
banner_variant, banner_source, banner_composite_used, banner_logo_url, banner_logo_contrast_mode,
banner_background_mode, banner_filet_used, header_logo_used, header_logo_missing_fallback
(backward compatible: header_variant, container_visual_variant, banner_replaceable)
```

UI shows: 当前 Banner（TTT Banner 组件 / 紧凑 Logo Banner / 文字品牌回退）· Logo 来源（上传 Logo / 默认 Banner 素材 /
文字回退）· 对比模式（深色底 / 浅色 Logo 板）.

## 7. Screenshot review

```
fiche_banner_composite.png   -> PASS
affiche_banner_composite.png -> PASS
```

Gate met: both >= PASS_WITH_NITS; no invisible logo (on_dark for light logos, light_plate for dark logos); no broken
logo; no product/gallery/atmosphere/generated-poster used as banner/logo; no double header. Full: `visual_review.md`.

## 8. Tests

```
+4 composite: composite module with lockup ; light_plate contrast for a dark logo ; no-logo wordmark fallback ;
              banner never uses product/gallery/atmosphere/poster as logo (affiche)
Focused suites = 99 passed ; test_api -k email/workbench/selected/fiche/preview/send = 11 passed ;
node --check cuistance_trial.html = TRIAL_JS_OK ; check_docs_router --all = PASS
```

Send path unchanged (no provider change).

## 9. Remaining HOLD

```
customer send / batch send   HOLD
products[] / multi-product   HOLD
P2A demo backend mapping     HOLD
remote browser re-verify of the composite banner : recommended after Render redeploys this commit
```
