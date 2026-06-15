# Family B Product Announcement — Runtime Result Validation v1

> **Task:** `POSTER2-FAMILY-B-ANNOUNCEMENT-RESULT-VALIDATION-V1` (result-oriented validation; no new slots,
> no contract expansion, no Poster Set runtime, no Stage3 change).
> **Date:** 2026-06-15.
> **Verdict:** **OPERATOR-TRIAL READY** (with documented, non-blocking polish opportunities).

## Artifacts

- `sample_payload.json` — Cuistance-style `/api/v2/generate-poster` request body (rice-cooker announcement).
- `final_poster.png` — 1024×1024 poster from the **real pipeline** (`template_product_sheet_v1`, Pillow operator
  path — Template B disables Puppeteer).
- `diagnostics.json` — full backend evidence (structure, region status, `announcement_variant_contract_review`,
  top-copy / description / product contract reviews).
- `visual_review.md` — this review.
- Repro: `PYTHONPATH=. ./.venv/bin/python scripts/poster2_announcement_runtime_validation.py`.

## Render setup (honest notes)

- The poster is produced through the existing `PosterPipeline` on `template_product_sheet_v1`, Pillow operator
  path, with the implemented variant fields only (`availability_badge`, `tariff_mode=on_request`,
  `on_poster_cta_label/email`, `sku_text`, `title`, `subtitle`, `description_title/body`, `product_image`, `logo`).
- The product image is a synthesized but recognizable commercial rice-cooker silhouette (portrait), used to
  judge contain-fit / distortion. No real customer artwork is used.
- **Font environment:** the first render fell back to a bitmap font (NotoSansSC missing in `app/assets/fonts/`),
  and a stale 4 KB→4 MB "Regular" file rendered Latin advance-widths with **no outlines** (invisible small text).
  Aligning `NotoSansSC-Regular.ttf` to the working variable font (exactly what `scripts/fetch_fonts.sh` intends —
  both names point at the same VF) fixed it. This is an **environment/asset precondition**, not a template
  limitation. Operator deployments must have the font pack present.

## Backend evidence (from diagnostics.json)

- `structure_complete = true`, `deliverable = true`.
- `announcement_variant_contract_review.structure_complete = true`; core information area **intact** (brand logo +
  SKU + title + primary hero + description copy core all rendered).
- `new_copy_slots`: `availability_badge` → "EN STOCK" rendered; `tariff_line` mode `on_request` →
  "Tarif : nous contacter" rendered; `on_poster_cta_text` rendered with
  `render_kind=display_text_only`, `cta_action_bound=false`, `stage3_send_untouched=true`.
- `materials_strip_region`: `collapsed_by_design=true`, `reason_code=materials_not_used_in_announcement_variant`,
  `count=0`, `region_order_unchanged=true`, `foreign_content_routed_in=false`.

## Visual review — the nine questions

| # | Question | Answer | Notes |
|---|---|---|---|
| 1 | Reads as a product announcement? | **Yes** | Dark brand banner → SKU + "NOUVEAUTÉ" headline + "EN STOCK" → hero product → claim/spec → tariff/contact. Unmistakably a new-product announcement / product sheet. |
| 2 | Product prominent and undistorted? | **Undistorted yes; prominence moderate** | Aspect preserved (contain-fit), centered, clean contact shadow. The product occupies the centre of a large hero card with generous surrounding whitespace, so it reads as a calm "studio float" rather than a dominant hero. Prominence is template-geometry-bound (see polish notes). |
| 3 | Availability badge visible? | **Yes** | "EN STOCK" in accent red, top-right of the top-copy row. Legible; reads as an availability flag (in Pillow it is accent text, not a filled chip). |
| 4 | SKU visible? | **Yes** | "311011 (RC10L)" in accent red, top-left. Small but legible. |
| 5 | Title hierarchy strong? | **Yes** | "NOUVEAUTÉ ! CUISEUR À RIZ PROFESSIONNEL" is clearly the dominant element; strong size/weight contrast vs SKU/subtitle/body. |
| 6 | Description / core claim readable? | **Yes** | "Inox – maintien au chaud 24h" (claim title) + the materials paragraph are readable. |
| 7 | Tariff / contact line visible? | **Yes** | "Tarif : nous contacter" (accent) + the contact line render at the description footer. |
| 8 | CTA visible but display-only? | **Yes** | "Nous contacter · commercial@cuistance.eu" renders as flat poster text; backend proves `cta_action_bound=false` / `stage3_send_untouched=true`. No action wired. |
| 9 | Real marketing poster or scaffold? | **Real product sheet** (clean, complete) — not a scaffold | It reads as a legitimate, on-brand commercial product announcement. It is calmer / more whitespace-led than a high-punch campaign poster — which is consistent with Family B's purpose (the punchy campaign anatomy is Family A / Catalog Hero, deliberately out of scope here). |

## Polish opportunities (non-blocking; most are out of this slice's scope)

1. **Product prominence** — the product is small relative to the wide `product_hero_region` (800×384), leaving
   large whitespace. Enlarging it / tightening the composition is a **template-geometry** change → **out of scope**
   for this slice (would be a separate, owner-gated polish/geometry slice). Not a defect; it is undistorted and
   correctly placed.
2. **Vertical whitespace** between the top-copy band and the hero card, and inside the description card, makes the
   page feel airy. Also geometry-bound.
3. **Availability badge as a filled chip** — in the Pillow operator path the badge is accent text, not the filled
   "chip" defined in the HTML/CSS. Could be a small future in-slot enhancement, but the plain accent text is clean
   and legible; not pursued here to avoid a wide accent bar across the right-aligned slot.

None of these block an operator trial; all required elements are present, legible, undistorted, correctly owned,
and on-brand.

## Stage2 browser flow (item 5)

**Not run — justified.** The three new fields (`availability_badge`, `tariff_mode`, `on_poster_cta_*`) have **no
Stage2 operator-input surface in this slice** (operator UI was intentionally deferred from the approved runtime
slice). A Stage2 screenshot would therefore not exercise or display the announcement variant, and would
additionally require a live backend + generation. A representative Stage2 capture is deferred to a future
operator-UI slice (if the Owner approves adding the fields to Stage1/Stage2).

## Adjustment decision (item 7)

The result is **not visibly poor** — it is clean, complete, and operator-usable. No runtime/visual code change was
made: the only "fix" required for a fair render was the **font-asset environment precondition** (above), and the
remaining polish items are template-geometry-bound and out of this slice's approved scope. Making a geometry or
contract change to chase "campaign punch" would violate the strict scope, so none was made.

## Verdict

**OPERATOR-TRIAL READY.** The implemented Family B Product Announcement variant produces a complete, correct,
legible, undistorted, on-brand product announcement through the existing single-poster path, with all three new
copy slots rendering (and collapsing) as specified and the CTA provably display-only. It is suitable for an
operator trial today (given the font pack), reading as a clean professional product sheet. Higher campaign-style
visual punch (product prominence, denser composition) is **template-geometry-bound and intentionally out of this
slice's scope** — a candidate for a future owner-gated polish slice, not a blocker.
