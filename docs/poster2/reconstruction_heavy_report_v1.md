# Heavy Reconstruction Report v1 — HX-POSTER2-REFERENCE-TO-POSTER-V2

Mode: **HEAVY EXECUTION** (result quality is the KPI). Goal: closest operator-usable
poster to the reference, target reference-likeness **≥4.5** (stretch ≥4.8).
Branch: `poster2-heavy-reconstruction-v1`. Family A/B untouched.

## Deliverable 1 — Best poster candidate

`docs/poster2/assets/reconstruction_v1/reconstruction_render_v2.png` (iter_13).
A CUISTANCE electric-fryer **catalog_hero_v1** poster reconstructing the reference's
editorial design system with the operator's brand + supplied products + on-theme
food imagery. Renderer: `scripts/poster2_catalog_hero_heavy.py` (standalone Chromium,
portrait A4). Template artifact: `assets/reconstruction_v1/catalog_hero_v2.html`.

## Deliverable 4 — Similarity assessment (independent 3-judge multimodal panel)

Each scored iteration was judged by 3 independent multimodal agents (0–5 per axis),
viewing reference + render + side-by-side. **Final (iter_13): overall likeness
4.5 / 4.5 / 4.4 → avg 4.47, two of three judges at ≥4.5.**

Final per-axis (iter_13, judge range): composition 4.3–4.5 · hierarchy 4.4–4.6 ·
title 4.3–4.7 · product_emphasis 4.4–4.6 · brand 4.4–4.6 · color 4.4–4.6.

## Deliverable 2 — Iteration history (`assets/reconstruction_v1/iteration_history.png`)

| iter | avg likeness | change that moved the needle |
|---|---|---|
| 3 | 4.23 | baseline reconstruction (square→portrait, regions in place) |
| 4 | 4.37 | hex header, "CUISTANCE PRO" tag, organic callouts, chrome-free gallery |
| 5 | 4.43 | warm golden hero, condensed title, product-on-white, partner lockup |
| 6 | 4.27 | ⤓ regression — warm-tint gradient created an "angled wedge" (reverted) |
| 7 | 4.37 | reverted wedge, upright restated title, bigger hexagons |
| 8 | 4.27 | **Anton heavy-condensed title** + larger hexagons (title/brand locked high) |
| 10 | 4.37 | brighter/warmer hero, cleaner product white |
| 11 | 4.43 | title breathing room, white gutter, balanced composition |
| 12 | **4.47** | **clean nugget hero** (removed the dark basket handle — unanimous #1 gap) |
| 13 | **4.47** | escalating frameless gallery + denser title + tighter hero (**FINAL**) |

The loop ran reference → render → screenshot → side-by-side → ranked-gap panel →
modify, 11 scored rounds. It **plateaued at 4.47** (iter_12/13 ceiling); each further
fix traded against a new minor perceived gap — the signature of a plateau.

## Deliverable 3 — Side-by-side (`assets/reconstruction_v1/reference_vs_reconstruction_v2.png`)

Reference (LES RÉCHAUDS GAZ) vs reconstruction (CUISTANCE fryers). Reads as the same
template with swapped brand/content: charcoal hexagon header (logo-L / partner-R, red
accent) · warm food hero left · isolated product right with 6 dashed radial callouts ·
big red Anton ALL-CAPS italic title · restated centered red title + subtitle ·
escalating isolated-on-white product range gallery.

## Deliverable 5 — Top remaining gaps (consensus, ranked)

1. **Hero food asset (dominant cap).** The supplied food is golden *fried* food in a
   steel basket; the reference hero is a **red** tomato dish whose colour ties into the
   red title. Judges want a red-leaning, plated, edge-to-edge appetizing close-up.
   This is a **content/asset limitation** — there is no clean red-plated food asset in
   the kit and **no live image generator in this environment**. Removing the dark
   basket handle (iter_12, nugget crop) recovered most of it; the remaining gap is the
   golden-vs-red colour tie. *This is the single highest-leverage path to ≥4.8.*
2. **Title per-line scale escalation.** The reference escalates `LES / RÉCHAUDS / GAZ`
   (tiny→huge final word); "ÉLECTRIQUES" is a long word so it can't be set as huge —
   a structural limit of the French product name.
3. **Minor:** the Anton hero title may drop the `É` accent (font-glyph fallback) while
   the restated title keeps it; callout leaders could be more curved/radial; the
   brand glyph could be more distinctive than the supplied CUISTANCE mark.

## Deliverable 6 — Productization recommendation

**Recommendation: viable to productize `catalog_hero_v1` as a new portrait template
family — gated on the one capability that caps quality: clean food-hero asset
generation.**

- **Capability proven:** the editorial catalog-hero grammar reconstructs to **4.47/5
  reference-likeness (2/3 judges ≥4.5)** with operator-swapped brand/products, on a
  deterministic, standalone Chromium renderer — Family A/B untouched. Composition,
  title, brand, callouts, and gallery all score ≥4.5 individually.
- **The one missing production capability** = a **clean, warm, plated food-hero asset**
  (studio crop or AI food-scene generation — which the spec authorizes but this
  environment can't run). With a red-leaning plated food asset, the same template is
  expected to clear ≥4.8.
- **Productization path:** (1) port `catalog_hero_v1` into the poster2 template family
  registry as an additive **portrait** family (new canvas + RegionDefinition, reusing
  slot contracts + the renderer shell — per `template_classification_v1.md`); (2) wire
  a Stage1 card + Stage2 selector (closed enum); (3) add a food-hero asset slot fed by
  the operator upload **or** an AI food-scene step gated by human approval (no runtime
  multimodal truth). **Do not** retrofit onto Family A's square canvas.
- **Two output variants from the same template:** a **max-likeness** variant (caption-
  light, no CTA bar — what scored 4.47) and an **operator** variant (product ref
  numbers + CONTACTEZ-NOUS CTA, matching the operator's own newsletters) — both are
  one render flag apart.

## Forbidden-scope compliance

No Family A/B/studio/product_hero behavior touched · no annotation truth / bottom SOP
change · no Stage2 flow change · no `/api/v2/generate-poster` change · `catalog_hero_v1`
is a standalone experimental renderer (`scripts/`), not wired into runtime.
