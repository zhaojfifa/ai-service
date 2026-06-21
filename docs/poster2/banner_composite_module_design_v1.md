# Banner Composite Module — Design v1

Task: **POSTER2-CUISTANCE-BANNER-COMPOSITE-MODULE-FIX-V1** (design section, before code).
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.

The banner/header is currently treated as a single logo-image flag (`header_logo_used=true`), so it still renders as a
plain dark slab + image. This defines the banner as a **first-class composite module** (`email_banner_composite`) with
structure, contrast handling, and fallback.

---

## 1. Root cause

```
Banner == logo flag, not a designed module:
  - dark plate + raw logo image + one channel line; no lockup, no contrast handling
  - the operator's uploaded logo_01.jpg is dark-on-transparent -> invisible on the dark #1f2329 plate
  - channel/campaign not composed as a secondary lockup line
  - reads as an engineering dark bar, not a ttt/ttt2 native banner
```

## 2. email_banner_composite — module structure

```
background_plate   : solid dark plate (#1f2329), full 600px width, balanced height
brand_lockup       : centered logo image OR text wordmark (the brand element)
channel_line       : channel_name (primary secondary text)
campaign_tag       : campaign_label (small uppercase tag under the channel line)
red_filet          : 3px #E1002A, full 600px, directly under the plate
contrast_mode      : on_dark | light_plate  (how the logo sits on the dark plate)
padding/height      : ttt-inspired (taller for the composite, compact for the fallback bar)
alignment          : centered
fallback           : no logo -> text wordmark (header_logo_missing_fallback=true)
```

Asset safety (unchanged, enforced): the banner/logo uses ONLY `email_banner.logo` (or a text wordmark). It NEVER uses
product / gallery / atmosphere / generated-poster / AI visuals.

## 3. Three banner variants

### 1. ttt_banner_composite (DEFAULT when a logo exists)

```
dark plate, taller (≈ 36/30 px padding)
centered logo lockup (logo image) + channel line + campaign tag under it
red filet aligned to the full 600px container
email-safe inline styles
maps from header_variant = ttt_logo_banner  (backward compatible)
```

### 2. compact_logo_banner (compact mode)

```
dark plate, less vertical height (≈ 18/14 px padding)
centered logo, channel/campaign secondary (single line)
red filet
maps from header_variant = logo_image_bar
```

### 3. text_wordmark_fallback (only when no valid logo)

```
dark plate, white CUISTANCE wordmark + channel/campaign + red filet
header_logo_missing_fallback = true
maps from header_variant = css_dark_bar_wordmark
```

## 4. Contrast mode (the dark-on-dark fix)

```
on_dark (default)   : logo sits directly on the dark plate — correct for a LIGHT / white brand logo
                      (the real CUISTANCE brand logo is white-on-transparent -> crisp on dark)
light_plate         : logo sits inside a subtle WHITE rounded plate within the dark banner — correct for a
                      DARK / colored logo (e.g. logo_01.jpg) so it is never invisible dark-on-dark
```

We cannot reliably detect logo luminance server-side, so `banner_logo_contrast_mode` is an operator setting
(`email_banner.banner_logo_contrast_mode`), default `on_dark`. The trial UI exposes it so an operator with a dark logo
selects `light_plate`. If the uploaded logo fails on dark and no light variant is provided, the safe options are:
light_plate (logo on a light plate), or the text wordmark fallback. We never blindly leave a dark logo invisible.

## 5. banner_source

```
uploaded_logo               : email_banner.logo is used (ttt_banner_composite / compact_logo_banner)
wordmark_fallback           : no logo (or no logo + a logo was preferred) -> text wordmark
default_banner_lockup_asset : RESERVED — for an approved hosted banner-lockup image. NOTE: ~/poster/ingredient/
                              "logo banner.png" is a Photoshop LAYERS-PANEL screenshot (layer names: logo banner /
                              产品功能海报 / 产品介绍 / ...), NOT a clean hosted banner image, so it is NOT adopted as a
                              default lockup asset here. The field is reserved for a future approved asset.
```

## 6. Required behavior (matches the owner contract)

```
logo exists  -> banner_variant=ttt_banner_composite, banner_source=uploaded_logo, header_logo_used=true,
                header_logo_missing_fallback=false, banner_composite_used=true
no logo      -> banner_variant=text_wordmark_fallback, banner_source=wordmark_fallback, header_logo_used=false,
                header_logo_missing_fallback=true
dark logo    -> operator sets banner_logo_contrast_mode=light_plate -> logo on a light plate (visible)
```

## 7. Diagnostics exposed

```
banner_variant, banner_source, banner_composite_used, banner_logo_url, banner_logo_contrast_mode,
banner_background_mode, banner_filet_used, header_logo_used, header_logo_missing_fallback
(kept backward compatible: header_variant, container_visual_variant, banner_replaceable)
```

## 8. Out of scope / HOLD

```
no AI image generation ; no body redesign ; no send rebuild ; no products[] ; P2A demo untouched
customer / batch send : HOLD
```
