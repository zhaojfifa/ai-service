# Banner Product Module — Spec v1

Task: **POSTER2-BANNER-PRODUCT-SPEC-AND-DESIGN-REVIEW-V1**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.

Defines the email banner as a **product module with route-specific defaults**, not a logo flag. Implemented
deterministically with existing assets (logo + ttt/ttt2 grammar + color system + red filet). The honest design-risk
note is in §8.

---

## 1. Banner as a product module (not a logo flag)

The banner is `email_banner_composite` — a header component with: background plate, brand lockup (logo or wordmark),
channel line, campaign label, and the red filet, with route-specific proportions and a contrast mode. It is resolved
and rendered as one unit; "logo present" is only one input, not the whole banner.

## 2. Route-specific defaults

```
Fiche   (simple product sheet) -> brand_standard_header     (default)
Affiche (target poster email)  -> campaign_poster_header     (default)
no usable logo                 -> text_fallback_header       (safe fallback, NOT preferred)
```

These are automatic per route (the operator does not pick brand-vs-campaign; the route decides). The operator
controls only: logo vs compact vs text-fallback brand element, and the logo contrast mode.

## 3. Visual ratio rules

```
                       brand_standard_header     campaign_poster_header     text_fallback_header
plate background       solid #1f2329             solid #1f2329              solid #1f2329
top/bottom padding     36 / 28 px (medium)       22 / 15 px (tighter)       30 / 24 px
logo height            ~46 px                    ~34 px                     n/a (wordmark ~30px)
brand element          centered logo             centered logo (smaller)    centered white wordmark
channel hierarchy      hairline rule + UPPERCASE  compact UPPERCASE line     UPPERCASE line
                       small-caps line
campaign label         folded into the meta line  folded into the meta line  in the meta line
                       (subtle; no loud pill)     (compact)
red filet              3px #E1002A, full 600px    3px #E1002A, full 600px    3px #E1002A, full 600px
relationship to body   medium presence; must not  light/tight; the generated medium
                       overpower the serif title  poster stays the hero
```

## 4. Logo contrast rules

```
banner_logo_contrast_mode = on_dark (default)   : light/white logo directly on the dark plate (the CUISTANCE brand
                                                  logo is white-on-transparent -> crisp)
                          = light_plate          : dark/colored logo inside a subtle white rounded plate inside the
                                                  dark banner, so it is never invisible dark-on-dark
```

A dark operator logo (e.g. `logo_01.jpg`) must use `light_plate`. The banner/logo NEVER uses product / gallery /
atmosphere / generated-poster / AI visuals.

## 5. Fallback rules

```
no valid logo  OR  explicit operator wordmark choice  ->  text_fallback_header
header_logo_missing_fallback = true when a logo was preferred but none/unusable is present
```

## 6. Operator-facing labels

```
品牌标准页眉 (brand_standard_header)
营销海报页眉 (campaign_poster_header)
文字回退页眉 (text_fallback_header)
route defaults shown: 简单产品页默认 = 品牌标准页眉 ; 目标海报默认 = 营销海报页眉
contrast: 深色底（浅色 Logo） / 浅色 Logo 板（深色 Logo）
```

## 7. Backend field mapping

```
banner_variant            : brand_standard_header | campaign_poster_header | text_fallback_header   (route-derived)
banner_composite_used     : true for brand_standard / campaign_poster
banner_source             : uploaded_logo | wordmark_fallback | default_wordmark | (reserved) default_banner_lockup_asset
banner_logo_url           : email_banner.logo.url
banner_logo_contrast_mode : on_dark | light_plate
banner_background_mode    : dark_plate
banner_filet_used         : true
header_logo_used / header_logo_missing_fallback : logo usage + fallback flags
(backward compatible: header_variant, container_visual_variant, banner_replaceable)
```

## 8. Design-risk note (explicit)

```
Can engineering solve this with existing assets?
  -> PARTIALLY. With the existing logo + solid dark plate + ttt/ttt2 grammar, engineering reaches a CLEAN, CORRECT,
     route-appropriate header (PASS_WITH_NITS). It does NOT reach a premium / distinctive / bespoke banner.

Why the ceiling:
  -> The ttt.html reference header derived its warmth/premium feel from a SUBTLE BACKGROUND PHOTO behind the dark
     header. We deliberately do NOT use a header-band background cover (it caused the earlier PSD header distortion /
     "强覆盖 / 配色不对" bug). With a solid plate only, the banner remains structurally "dark plate + logo + text".

Recommendation:
  -> A designer-provided banner/base-lockup MASTER (a crafted header artwork or a safe brand background treatment +
     lockup spec) IS RECOMMENDED to cross from "clean template" to "premium native CUISTANCE banner".
  -> The implemented brand_standard / campaign_poster headers are accepted as the INTERIM first-trial default
     (they meet the PASS_WITH_NITS bar and are route-correct), pending the designer master.
```
