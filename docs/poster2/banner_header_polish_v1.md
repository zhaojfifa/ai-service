# Banner / Header Polish v1

Task: **POSTER2-CUISTANCE-BANNER-HEADER-POLISH-V1**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.

Focused polish of the **banner/header layer only** for both accepted containers (`ttt_product_sheet_container` /
`ttt2_campaign_container`). The body/layout from the deep migration is unchanged. No body redesign, no send rebuild,
no `products[]`, P2A demo untouched.

---

## 1. Root cause

The deep migration's body was accepted, but the header defaulted to `css_dark_bar_wordmark` (a plain text block)
even when a valid `email_banner.logo` existed — remote diagnostics showed `header_variant=css_dark_bar_wordmark`,
`banner_source=default_wordmark`, `header_logo_used=false`. The real logo/banner asset was not used by default, so the
header looked engineering-like and dragged down the design.

## 2. What changed in default banner behavior

```
DEFAULT now PREFERS a logo banner:
  email_banner.logo present + operator did NOT explicitly pick the wordmark  ->  ttt_logo_banner (logo used)
  no logo (logo was preferred)                                              ->  css_dark_bar_wordmark + header_logo_missing_fallback=true
  operator explicitly picks 文字品牌条                                        ->  css_dark_bar_wordmark (deliberate, banner_source=default_wordmark)
```

The frontend default selection is now **TTT Logo Banner** (not 文字品牌条); the backend gracefully falls back to the
wordmark when no logo exists.

## 3. Header variants

```
ttt_logo_banner       : ttt-style dark header (taller, ~40px padding), centered CUISTANCE logo image, channel/campaign
                        meta (secondary), red filet  — the preferred default with a logo
logo_image_bar        : compact logo image bar (~20px padding) using email_banner.logo
css_dark_bar_wordmark : text-only wordmark fallback (no logo, or explicit operator choice)
```

Diagnostics exposed: `header_variant`, `banner_source` (uploaded_logo | default_wordmark | wordmark_fallback),
`banner_replaceable=true`, `header_logo_url`, `header_logo_used`, `header_logo_missing_fallback`,
`container_visual_variant`.

## 4. Asset safety rules (test-enforced)

```
header/logo may use ONLY: email_banner.logo.url  (or text wordmark fallback)
header/logo NEVER uses   : product image / gallery image / atmosphere image / generated poster / AI visual
```

Verified by `test_header_never_uses_product_gallery_atmosphere_as_logo` (fiche) and
`test_header_never_uses_poster_or_assets_as_logo_affiche` (affiche: the header region contains only the brand logo,
never the poster body visual or any product/gallery/atmosphere url).

## 5. Fiche result

`ttt_product_sheet_container` retained in full (serif reference/title, centered hero, supporting_media_strip, spec
block, CTA, dark footer). Header polished to the ttt logo banner (white CUISTANCE logo on the dark bar + red filet).
Banner verdict: **PASS**.

## 6. Affiche result

`ttt2_campaign_container` retained (no-inner-banner poster body, no spec duplication, no double header, CTA, dark
footer). Header polished to the ttt logo banner, integrating with the poster body. Banner verdict: **PASS**.

## 7. Screenshot review

```
docs/poster2/assets/banner_header_polish_v1/fiche_banner_polished.png   -> Fiche banner  : PASS
docs/poster2/assets/banner_header_polish_v1/affiche_banner_polished.png -> Affiche banner: PASS
```

Gate met: both >= PASS_WITH_NITS; no broken logo; no product/gallery/atmosphere/generated-poster used as logo; no
double header. The banner no longer drags down the design. Full review: `visual_review.md`.

## 8. Tests

```
+4 new: default prefers logo banner ; no-logo falls back to wordmark (missing_fallback=true) ;
        ttt_logo_banner renders the logo + red filet ; affiche header never uses poster/assets as logo
6 updated: tests that assumed the old wordmark default now assert the logo-banner default (logo present)
Focused suites green ; test_api -k email/workbench/selected/fiche/preview/send = 11 passed ;
node --check cuistance_trial.html = TRIAL_JS_OK ; check_docs_router --all = PASS
```

## 9. Remaining HOLD

```
customer send                HOLD
customer batch send          HOLD
products[] / multi-product   HOLD
P2A demo backend mapping     HOLD
remote browser re-verify of the logo banner : recommended after Render redeploys this commit
```
