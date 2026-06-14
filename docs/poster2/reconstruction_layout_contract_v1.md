# Reconstruction Layout Contract v1 — Layout Engineer

Task: **HX-POSTER2-REFERENCE-RECONSTRUCTION-V1**. Role: **Layout Engineer**.
Template family: **`catalog_hero_v1`** (new, experimental; Family A untouched).
Canvas: **1240 × 1754 px**, portrait, ratio **0.707** (A4). Coordinates are the
literal values rendered by `scripts/poster2_catalog_hero_reconstruction.py`
(`device_scale_factor=2`). Relative geometry = fraction of canvas.

## Region map (measurable)

| Region | px box (x, y, w, h) | rel x | rel y | rel w | rel h |
|---|---|---|---|---|---|
| **header** | 0, 0, 1240, 116 | 0.00 | 0.00 | 1.00 | 0.066 |
| header accent (red rule) | 0, 110, 1240, 6 | 0.00 | 0.063 | 1.00 | 0.003 |
| **hero food** (full-bleed left rail) | 0, 122, 474, 772 | 0.00 | 0.070 | 0.382 | 0.440 |
| **title** (product-lane top) | 498, 144, 706, ~320 | 0.402 | 0.082 | 0.569 | 0.182 |
| **product** (isolated, right lane) | 660, 498, 400, 384 | 0.532 | 0.284 | 0.323 | 0.219 |
| **callouts** (radial, over right lane) | 484, 540, 712, 300 | 0.390 | 0.308 | 0.574 | 0.171 |
| restated title band | 0, 946, 1240, ~150 | 0.00 | 0.539 | 1.00 | 0.086 |
| **gallery** (3 items) | 44, 1150, 1152, 380 | 0.035 | 0.656 | 0.929 | 0.217 |
| footer (CTA strip) | 0, 1626, 1240, 128 | 0.00 | 0.927 | 1.00 | 0.073 |

### Right-lane budget (resolves the food | labels | product | labels packing)
`food rail [0–474] · left callout labels [484–640] · product [660–1060] · right
callout labels [1080–1236]`. Leaders run from each label's inner edge to a red dot
node on the product.

## Callout slots (6, radial — `catalog_hero_v1` annotation grammar)

| # | side | label | anchor (px) | label_y |
|---|---|---|---|---|
| 1 | left | Cuve inox amovible | 706, 580 | 556 |
| 2 | left | Sécurité anti-surchauffe | 694, 706 | 690 |
| 3 | left | Structure acier inox AISI 304 | 724, 824 | 812 |
| 4 | right | Thermostat réglable 0–200°C | 1012, 580 | 556 |
| 5 | right | Double cuve indépendante | 1024, 706 | 690 |
| 6 | right | Panier grillagé à poignée | 980, 824 | 812 |

Leader style: 1.4px dashed (`3 4`) ink line @0.7 opacity + 5.5px **red** dot node on
the product + 3px ink node at the label. Borderless labels (editorial), 3 left / 3
right (balanced fan).

> **Annotation-contract note:** `catalog_hero_v1` is a separate family; it uses 6
> callouts to match the reference. Family A's frozen 3-slot product-annotation truth
> is **not modified** (no Family A file touched).

## Gallery contract (3 isolated-on-white range cards)

| slot | image | caption | ref |
|---|---|---|---|
| 1 | 产品图.jpg (dual-tank) | Double cuve · 2×8 L | EF-82D |
| 2 | 产品图2.jpg (single-tank) | Simple cuve · 8 L | EF-81S |
| 3 | Electric Fryer1.jpg | Compacte · 6 L | EF-60C |

Card: 362px wide, 300px image well (`#fafafa`, 1px border, 10px radius, contain
fit), name caption + gray reference line. Equal gaps, full content width.

## Protected geometry (if `catalog_hero_v1` were productized)

Frame ratio 0.707; the hero∥product split (food rail right edge @ x=474); title
anchored in the product-lane top; gallery as an equal-width 3-card row; header/footer
charcoal bands. Fallbacks: missing food → atmosphere scene; missing gallery item →
collapse to available (≥2); >6 callouts → clamp to 6.

## Slot ownership

`header`: brand_logo (L), partner_text (R). `hero`: scenario/food image. `title`:
title_text + bilingual subline. `product`: product_primary + the 6 callout slots
(owned by the product region). `gallery`: gallery_item_1..3 (+caption owned by
gallery). `footer`: contact_text + cta_text. All deterministic; no freeform.
