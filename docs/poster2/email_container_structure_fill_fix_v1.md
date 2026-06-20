# Email Container Structure-First Fillability Fix v1

Task: **POSTER2-EMAIL-CONTAINER-STRUCTURE-FIRST-FILLABILITY-FIX-V1**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.
Approach: define the container **structure first** (see
`email_container_structure_and_fill_contract_v1.md`), then map assets into it, then update assembly / UI / tests.

No `products[]`. No multi-product backend. No real send. P2A demo untouched.

---

## 1. Root cause

In Fiche (`single_product_sheet_email`) the assembly rendered **only `product_images[0]`** as the body visual.
There was **no container module** to receive the other assets, so `product_images[1..]` (more views of the same
product) and `gallery_images[]` (supporting visuals) were never placed into the email — they appeared to
"disappear" in the preview. This is a **container-structure / fillability gap**, not an upload loss (the assets are
persisted on the Workbench the whole time).

## 2. Container structure definition

Two trial containers (no template engine):

```
single_product_campaign_email (Affiche): email_header, title_intro, selected_body_visual, cta, contact_footer,
                                          legal_footer  (+ optional product_description / spec_summary)
single_product_sheet_email    (Fiche)  : email_header, title_intro, primary_product_visual, supporting_media_strip,
                                          product_description, spec_list, cta, contact_footer, legal_footer
```

`supporting_media_strip` is now a **structural module** in the deterministic module order (between the primary
visual and the description). It is present-rendered only for Fiche when it has supporting media; for Affiche it is
part of the structure but `present=false` (the poster already carries the product views).

## 3. Fiche module fill rules

```
product_assets.product_images[0]      -> primary_product_visual  (body_visual_mode = product_image)
product_assets.product_images[1..]    -> supporting_media_strip   role = same_product_view
product_assets.gallery_images[]       -> supporting_media_strip   role = supporting_visual
product_assets.atmosphere             -> NOT used in Fiche        role = visual_only_not_truth
product_truth.description             -> product_description
product_truth.parameters[confirmed]   -> spec_list
operator copy / deterministic fallback -> title_intro / CTA
```

## 4. Supporting media strip behavior

```
max items = 3
priority  = product_images[1..] first, then gallery_images[]
label     = "Vues produit / Détails"
layout    = single 600px-safe table row of up to 3 thumbnails, inline email-safe styles, object-fit:cover
atmosphere = excluded (atmosphere_used_in_fiche = false, always)
truth     = none of these are business truth — supporting visuals only
```

Observed case (2 product images + 3 gallery + atmosphere) now yields `supporting_media_count=3`
(`["same_product_view","supporting_visual","supporting_visual"]` — `product_images[1]` then `gallery[0..1]`; the 4th
asset is dropped by the cap), with the primary visual still `product_images[0]` and atmosphere unused.

## 5. selected_email_body_visual persistence

The selected route is Workbench truth: persisted via `PATCH /selected-visual`, and preview/send assemble strictly
from `workbench.selected_email_body_visual`. A preview-time `email_fill_format` / `container_profile` assertion only
validates against the selected route (mismatch → 422) and never overrides it. Verified by test for both routes
(select Fiche → GET fiche; select Affiche → GET affiche). No flow change was required.

## 6. Truth boundaries (reaffirmed)

```
product_truth = the only business truth
product_images[1..] = MORE VIEWS of the same product (NOT separate products)
gallery_images = supporting visual evidence, not identity truth
atmosphere = visual only, never enters the Fiche fact/body area
AI visual is never business truth
no free-form editing of technical spec VALUES
```

## 7. Tests

```
+7 new (tests/poster2/test_workbench_email_assembly.py):
   strip module present + ordered; 2 images + 3 gallery -> 3 supporting; primary stays product_images[0];
   roles views-then-gallery; atmosphere present-but-unused; no-supporting -> primary only;
   affiche has no strip (structural but present=false) + real_email_sent false; selection persistence both routes
~1 updated (tests/poster2/test_workbench_email_body_plan.py): module order now includes supporting_media_strip (8 modules)

Focused suites: assembly+candidates+psd_container+body_plan+reference+send = 81 passed;
test_api -k email/workbench/selected/fiche/preview = 10 passed; trial JS node --check = TRIAL_JS_OK;
check_docs_router --all = PASS (legacy advisory only).
```

## 8. Remaining HOLD

```
OPS-authenticated remote smoke   HOLD (BLOCKED_OPS_AUTH_REQUIRED)
products[]                       HOLD
multi-product backend            HOLD
P2A demo backend mapping         HOLD
real customer send               HOLD
```
