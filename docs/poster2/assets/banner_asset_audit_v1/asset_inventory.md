# Banner Asset Inventory — `~/poster/ingredient`

All 7 source files present. Inspected via `sips` (dimensions), `psd_tools` (PSD layer tree), and direct visual
inspection. Business truth is NOT extracted from any of these — design/container reference only.

| Asset | Dimensions | Contains | Banner plate | Logo lockup | Channel/campaign | Red filet | Safe to use | Disposition | Classification |
|-------|-----------|----------|--------------|-------------|------------------|-----------|-------------|-------------|----------------|
| `logo_01.jpg` | 400×80 | CUISTANCE logo lockup (house/pot icon + "CUISTANCE" wordmark, **dark/black**, red dot on the A) | no | YES (logo only) | no | no | YES (as the logo) | use as the logo inside a reconstructed banner; dark-on-transparent → needs light bg / `light_plate` on dark | **USABLE_LOGO_ONLY** |
| `产品海报.psd` → layer `logo banner` | 600×54 | **TECHNITALIA / CODIMATEL** banner (hexagon plate + TECHNITALIA logo left, CODIMATEL right) | YES | yes (Technitalia) | no | no | **NO — wrong brand** | reject for CUISTANCE; reference only | **NOT_USABLE_FOR_BANNER** |
| `产品海报.psd` (whole) | 600×1577 RGB | Technitalia gas-stove product poster: `背景`, `logo banner` (Technitalia), `产品功能海报` (hero), `产品介绍` (LES RÉCHAUDS GAZ), `产品参数说明` (specs), `分享方式` (footer w/ `kaly@tec…`, `01 41 53 12 12`) | n/a | n/a | n/a | n/a | layout only | structure/grammar reference; NOT a CUISTANCE asset | **DESIGN_REFERENCE_ONLY** |
| `ttt.html` | 22.6 KB | Mailchimp export — CUISTANCE product-sheet email (COUPE-FRITES). Dark header w/ background image + centered hosted CUISTANCE logo PNG; red CTA; dark footer. Carries Mailchimp tracking/unsubscribe + stale sample facts | n/a (CSS/table) | yes (hosted logo, external URL) | yes | yes | header grammar only | CSS/table reconstruction reference; do NOT copy tracking/facts | **DESIGN_REFERENCE_ONLY** |
| `ttt2.html` | 114 KB | Zoho/campaign export (Technitalia, `stratus.campaign-image.eu`) — campaign layout | n/a | n/a | n/a | n/a | layout only | reconstruction reference (other brand) | **DESIGN_REFERENCE_ONLY** |
| `图层示意.png` | 1868×960 | Photoshop SCREENSHOT of the PSD design + layers panel | no | no | no | no | no | reference screenshot, not artwork | **DESIGN_REFERENCE_ONLY** |
| `图层细节.png` | 258×843 | Photoshop layers-panel detail SCREENSHOT | no | no | no | no | no | reference screenshot, not artwork | **DESIGN_REFERENCE_ONLY** |
| `logo banner.png` | 271×240 | Photoshop **layers-panel SCREENSHOT** (layer names: logo banner / 产品功能海报 / …) — mislabeled; contains NO banner artwork | no | no | no | no | no | reject (UI screenshot) | **NOT_USABLE_FOR_BANNER** |

## Decisive evidence (saved crops)

- `psd_logo_banner_is_technitalia.png` — the PSD's only 600px banner layer is **TECHNITALIA / CODIMATEL**, not CUISTANCE.
- `cuistance_logo_only.png` — the only CUISTANCE-branded asset is a **logo-only** lockup (dark wordmark, no plate / channel / campaign / filet).

## PSD layer tree (z-order)

```
背景            (0,0,600,1577)      background
logo banner     (0,0,600,54)        TECHNITALIA/CODIMATEL banner   <-- only 600px header, WRONG brand
产品功能海报      (0,54,598,454)      product hero poster (Technitalia)
产品介绍         (15,490,585,876)    LES RÉCHAUDS GAZ + product image
产品参数说明      (-2,912,605,1314)   specs (XR144, DIMENSIONS 800*700*270, PUISSANCE, kW)
分享方式         (-2,1310,604,1578)  footer: social + COMMANDES/CATALOGUES/SITE INTERNET + kaly@tec… + 01 41 53 12 12
```
