# Banner Composite Module — Visual Self-Review v1

Rendered from `build_email_assembly` (deterministic); screenshots via Playwright + Chrome at 600px. Only the
banner/header module changed — body/layout unchanged. Screenshots: `fiche_banner_composite.png`,
`affiche_banner_composite.png`.

Scale: **PASS** / **PASS_WITH_NITS** / **FAIL**.

## Before → After

```
Before: banner == logo flag -> dark slab + raw logo (dark logo invisible dark-on-dark), single meta line
After : email_banner_composite -> dark plate + logo lockup + channel line + campaign PILL tag + red filet,
        with banner_logo_contrast_mode (on_dark | light_plate) so dark logos are never invisible
```

| Dimension                  | Fiche | Affiche | Note |
| -------------------------- | ----- | ------- | ---- |
| banner component integrity | PASS | PASS | a real lockup: logo + channel line + campaign pill + red filet (not a single image flag) |
| logo contrast              | PASS | PASS | white CUISTANCE logo crisp on the dark plate (on_dark); `light_plate` wraps a dark logo in a white plate (test-verified) |
| channel/campaign readability | PASS | PASS | "CUISTANCE Europe" channel line + "NOUVEAUTÉ" red-bordered pill, secondary but readable |
| red filet alignment        | PASS | PASS | 3px #E1002A spanning the full 600px container, directly under the plate |
| body/header consistency    | PASS | PASS | dark plate + red filet matches the dark footer; header does not compete with the body |
| overall                    | **PASS** | **PASS** | reads as a native CUISTANCE email banner |

## Acceptance gate

```
Fiche banner   : PASS   (>= PASS_WITH_NITS) ✓
Affiche banner : PASS   (>= PASS_WITH_NITS) ✓
no invisible logo ✓ (on_dark for light logos; light_plate for dark logos)
no broken logo ✓
no product/gallery/atmosphere/generated-poster used as banner/logo ✓ (test-enforced; email_banner.logo only)
no double header ✓
```

## Contrast modes

```
on_dark (default)  : light/white logo directly on the dark plate (shown in both screenshots)
light_plate        : dark/colored logo inside a subtle white rounded plate within the dark banner
                     (test_banner_light_plate_contrast_for_dark_logo verifies the white plate is rendered)
```

The operator picks the contrast mode in the trial UI (深色底 / 浅色 Logo 板) per their logo asset, so a dark
operator logo (e.g. logo_01.jpg) is never left invisible dark-on-dark.
