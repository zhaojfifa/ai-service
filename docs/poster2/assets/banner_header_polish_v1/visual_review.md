# Banner / Header Polish — Visual Self-Review v1

Rendered from `build_email_assembly` (deterministic) with the polish applied; screenshots via Playwright + Chrome at
600px. The previous container body/layout (accepted) is unchanged — only the banner/header layer changed.

Screenshots: `fiche_banner_polished.png`, `affiche_banner_polished.png`.

Scale: **PASS** / **PASS_WITH_NITS** / **FAIL**.

## Before → After (banner)

```
Before: header_variant=css_dark_bar_wordmark, banner_source=default_wordmark, header_logo_used=false
        -> plain text block, engineering-like
After : header_variant=ttt_logo_banner, banner_source=uploaded_logo, header_logo_used=true (when a logo exists)
        -> ttt-style dark header with the centered CUISTANCE LOGO + uppercase channel·campaign meta + red filet
```

## Fiche banner

| Dimension                  | Verdict | Note |
| -------------------------- | ------- | ---- |
| Fiche banner               | PASS | taller native ttt header; white CUISTANCE logo centered; uppercase secondary meta; red filet preserved |
| logo used / fallback       | logo used (`uploaded_logo`); falls back to wordmark only when no logo |
| header/body consistency    | PASS | dark header + red filet matches the dark footer; body is the accepted ttt_product_sheet_container |
| banner drags down design?  | NO  | the logo banner reads native, no longer a crude black text block |

## Affiche banner

| Dimension                  | Verdict | Note |
| -------------------------- | ------- | ---- |
| Affiche banner             | PASS | same ttt logo banner; integrates with the poster body; no double header |
| logo used / fallback       | logo used (`uploaded_logo`) |
| header/body consistency    | PASS | header frames the generated poster cleanly; dark footer matches |
| banner drags down design?  | NO  | banner now complements the target poster body |

## Acceptance gate

```
Fiche banner   : PASS   (>= PASS_WITH_NITS) ✓
Affiche banner : PASS   (>= PASS_WITH_NITS) ✓
no broken logo ✓ (white CUISTANCE logo renders on the dark header)
no product/gallery/atmosphere/generated-poster used as logo ✓ (email_banner.logo only — test-enforced)
no double header ✓
```

## Asset safety (enforced by tests)

```
header logo source = email_banner.logo ONLY
never: product image / gallery image / atmosphere image / generated poster / AI visual
verified: test_header_never_uses_product_gallery_atmosphere_as_logo + test_header_never_uses_poster_or_assets_as_logo_affiche
```
