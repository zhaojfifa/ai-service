# Reconstruction Asset Plan v1 — AI Asset Designer

Task: **HX-POSTER2-REFERENCE-RECONSTRUCTION-V1**. Role: **AI Asset Designer**.
Scope: from the operator-supplied core assets, source/generate the missing supporting
imagery the catalog-hero needs (food hero, supporting food, gallery variants,
atmosphere, callout-support), and document prompts + outputs.

> **Honesty note (important):** no live text-to-image model is wired into this
> workspace (the project's Vertex Imagen path needs GCP credentials not present here).
> So this plan does **two** things: (1) records the exact generation **prompts** that
> *would* produce each missing asset, and (2) for the actual render, uses **real
> on-theme assets from the operator's own poster kit** (`/Users/tylerzhao/poster/…`),
> which is faithful to the brand and avoids fabricating imagery. Every asset used is
> listed below with its true source.

## Core supplied assets (operator-provided, used as-is)

| Asset | File | Used as |
|---|---|---|
| Brand logo | `logo_01.jpg` (400×80, CUISTANCE wordmark) | header + footer (reversed white) |
| Product (hero) | `产品图.jpg` (1280²) | right-lane isolated hero fryer + gallery slot 1 |
| Product (alt) | `产品图2.jpg` (1280²) | gallery slot 2 |

## Missing assets — generation prompts + actual source used

| Need | Generation prompt (if using a T2I model) | Actual source used (this render) |
|---|---|---|
| **Food hero** | "Commercial stainless double-tank electric fryer in a professional kitchen, golden French fries in one basket and crispy chicken nuggets in the other, steam rising, warm appetizing golden tones against cool steel, soft depth-of-field background, vertical/portrait, photoreal, no text" | **`SOP/Golden fries and crispy nuggets frying.png`** (1024×1536) — the operator's own on-theme photo of the CUISTANCE fryer in action |
| **Supporting food imagery** | "Close-up basket of golden crispy fries lifting out of hot oil, warm light, shallow focus, no text" | covered by the hero (frying scene already contains fries + nuggets); reserved slot for future variants |
| **Gallery variants** | "Studio product shots of a single-tank and a compact electric fryer, isolated on pure white, soft contact shadow, front-3/4 angle, consistent lighting with the hero product" | **`产品图.jpg`**, **`产品图2.jpg`**, **`demo图/Electric Fryer1.jpg`** (all 1280², isolated-on-white) |
| **Atmosphere imagery** | "Blurred professional kitchen background, stainless surfaces, warm service lighting, bokeh, no text" | available in kit (`demo图/the kitchen-1.jpeg`, `scenes-1/2.jpeg`); not needed — the hero already supplies kitchen atmosphere |
| **Callout-support imagery** | "Macro detail crops of fryer features: thermostat dial, removable inox tank, mesh basket handle — clean, isolated, neutral" | not required — callouts are text labels with dashed leaders to the product; no per-callout thumbnails in this layout |

## Asset processing (deterministic, in the renderer)

- Longest-edge cap 1400px before base64 inlining (memory-safe; reuses the
  HX-POSTER2-PUPPETEER-MEMORY-FIX approach).
- Food hero: LANCZOS **cover-crop** to the 474×772 left rail + a subtle bottom
  gradient for editorial depth.
- Products: `object-fit: contain` on white wells (isolated-on-white treatment).
- Logo: rendered reversed white (`brightness(0) invert(1)`) on charcoal bands.

## Provenance / safety

All imagery is operator-owned CUISTANCE brand material from the supplied poster kit;
nothing is scraped or cloned from third-party copyrighted artwork. The reference's
TECHNITALIA/CODIMATEL artwork and French copy are **not** reused — only the *design
grammar* is reconstructed, with CUISTANCE content. If/when a live T2I model is
available, the prompts above regenerate the food/atmosphere assets deterministically.
