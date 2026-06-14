# Reconstruction Design Spec v1 — Design Analyst

Task: **HX-POSTER2-REFERENCE-RECONSTRUCTION-V1**. Role: **Design Analyst**.
Target: the reference poster (`poster_refer.pdf` p1 — *LES RÉCHAUDS GAZ*) reconstructed
with the operator's **CUISTANCE** brand + supplied **electric fryer** products.
Goal: same design system, new content (not a pixel clone).
Deliverable poster: `scripts/out/reference_grammar_v1/reconstruction/reconstruction_render_v1.png`
(tracked copy `docs/poster2/assets/reconstruction_v1/reconstruction_render_v1.png`).

Cross-reference: the operator's own CUISTANCE newsletters `SOP/目标海报1.jpg` /
`目标海报2.jpg` confirm the brand system this reconstruction must speak (charcoal
CUISTANCE bar, red accent, FR/中 bilingual copy, reference numbers, 联系我们 CTA).

---

## 1. Visual hierarchy (reconstruction targets)

| Level | Element | How it earns the rank |
|---|---|---|
| Primary | **Warm food hero** (golden fries + nuggets frying, left full-bleed rail) | largest saturated mass, top-left entry, appetite trigger |
| Secondary | **Isolated fryer product** + dashed radial callouts (right lane) | the commercial subject; callouts make the eye orbit it |
| Tertiary | **Red ALL-CAPS italic title** "LES FRITEUSES ÉLECTRIQUES" | highest-contrast verbal hook, top of the product lane |
| Quaternary | **3-item fryer range gallery** (isolated-on-white) | "choose your model" closer |
| Supporting | charcoal CUISTANCE header + footer/CTA, restated title, subtitle | brand frame + verbal close |

## 2. Typography hierarchy

- **Display title** — heavy (900), italic, UPPERCASE, condensed feel via tight
  letter-spacing + `skewX(-6deg)`, accent red; stacked 3 lines (`LES / FRITEUSES /
  ÉLECTRIQUES`). Mirrors the reference's condensed red display type.
- **Bilingual subline** — NotoSansSC SemiBold `专业商用电炸炉` (operator's 中/FR system).
- **Restated title** — same red italic caps, ~⅔ display size, centered.
- **Subtitle/strapline** — light gray, uppercase, tracked: *"Quand le croustillant
  fait toute la différence !"* (reference cadence: *"Quand les plats ont besoin…"*).
- **Callout labels** — small (18px) semibold, borderless (editorial, not pill chips).
- **Gallery captions** — semibold name + gray reference number.

## 3. Color system (measured + brand)

| Token | Value | Role |
|---|---|---|
| Accent red | `#E1002A` | the single decisive accent (title, dots, leaders nodes) |
| Charcoal | `#232428` | header + footer brand bands |
| Ink | `#2b2b2b` | callout/caption text |
| Steel gray | `#8a9099` | subtitles, reference numbers |
| Orange | `#E8531F` | CTA button (from CUISTANCE `目标海报2`) |
| Surface | `#FFFFFF` | flat editorial ground |

Discipline: red is the only accent; steel/charcoal/white carry everything else —
matching the reference's restrained palette.

## 4. Composition weights (target, from grammar `catalog_hero_v1`)

`hero 0.34–0.42 · product 0.24–0.30 · title 0.10–0.14 · gallery 0.10–0.14 ·
header 0.08–0.12`, whitespace high. Hero ∥ product **dual co-anchor**; hero
**full-saturation, not receded** (warm-vs-cool tension with the steel fryer).

## 5. Reading flow

`food hero → red title → product → callouts → restated title → gallery → CTA` —
emotional entry, verbal hook, subject, proof, close. The dashed leaders script the
micro-flow around the product.

## 6. Image proportions

- Canvas **portrait A4 0.707** (1240×1754) — the format the reference uses and the
  grammar requires.
- Food hero: tall left rail, **full-bleed** to the left/top edge, cover crop.
- Product: isolated-on-white, contained in the right lane, ~0.28 weight.
- Gallery: 3 isolated-on-white product cards, equal width.

## 7. Product prominence

The fryer (产品图.jpg, dual-tank) is the secondary anchor — large, centered in the
right lane, ringed by 6 dashed radial callouts with red dot nodes (the reference's
6-callout density; this is a NEW family, not bound by Family A's frozen 3-slot
annotation contract, which remains untouched).

## 8. Brand prominence

CUISTANCE wordmark reversed white on the charcoal header bar (logo-left), with a
"CUISINE PROFESSIONNELLE" partner-slot on the right, a 6px red underline, and a
repeated CUISTANCE mark + contact + orange CTA in the charcoal footer — matching the
reference's brand-bar weighting and the operator's own newsletter system.
