# Email Container Structure & Fill Contract v1

Status: **STRUCTURE-FIRST CONTRACT.** Defines the two supported trial email containers, their module structure, and
the exact fill rules from Workbench truth. The assembly/UI/tests are updated to satisfy THIS contract (not the other
way round). No general template engine. No `products[]`. No multi-product. No real send.

Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.

---

## 0. Vocabulary (must hold)

```
product_images[]  = multiple VIEWS/IMAGES of ONE product   (NOT multiple products)
gallery_images[]  = supporting visuals of the same product
atmosphere        = visual-only mood/scene asset; NEVER business truth
products[]        = multiple distinct products — NOT IMPLEMENTED (HOLD)
```

The email container width is **600px**, email-client-safe table/inline-style HTML only.

---

## 1. Supported trial containers

```
single_product_campaign_email   (Affiche route / campaign_poster_email)
single_product_sheet_email      (Fiche route   / product_sheet_email)
```

### single_product_campaign_email — Affiche

Purpose: marketing poster visual is the main body; the email container wraps the poster body visual with
header/footer/CTA context.

```
Required modules:
  email_header
  title_intro
  selected_body_visual        (the email-embedded, no-inner-banner poster visual)
  cta
  contact_footer
  legal_footer

Allowed optional modules:
  product_description
  spec_summary                 (conceptual; today rendered inside product_description when present)
```

The Affiche poster already carries the product views/specs inside the rendered poster, so the campaign container does
NOT add a supporting media strip.

### single_product_sheet_email — Fiche

Purpose: a product sheet email where product truth, the product image, parameters, and supporting visuals are
assembled into a 600px container (NO poster generation, NO poster_key).

```
Required modules:
  email_header
  title_intro
  primary_product_visual       (= the implementation module key "selected_body_visual" for fiche)
  product_description
  spec_list                    (conceptual; today rendered inside product_description from confirmed parameters)
  cta
  contact_footer
  legal_footer

Optional but STRUCTURAL module:
  supporting_media_strip        (part of the container even when absent for a given product)
```

Implementation-key mapping (kept backward compatible with the existing deterministic module order):

```
contract module            implementation fragment/diagnostic
-------------------------  ------------------------------------
email_header               email_banner
primary_product_visual     selected_body_visual (body_visual_mode = product_image for fiche)
supporting_media_strip     supporting_media_strip          (NEW)
product_description         product_description (intro text)
spec_list                  rendered within product_description (RÉF. + confirmed parameters); diagnostic spec_display_mode
contact_footer             contact_footer
legal_footer               legal_footer
```

---

## 2. Fiche fill rules (single_product_sheet_email)

```
product_assets.product_images[0]      -> primary_product_visual
product_assets.product_images[1..]    -> supporting_media_strip   (role = same_product_view)
product_assets.gallery_images[]       -> supporting_media_strip   (role = supporting_visual)
product_assets.atmosphere             -> NOT used by default in Fiche (role = visual_only_not_truth)
product_truth.description             -> product_description
product_truth.parameters[state=confirmed] -> spec_list
operator copy / deterministic fallback    -> title_intro / CTA
```

### supporting_media_strip rules

```
max items   = 3
priority     = 1) product_images[1..]  (same_product_view)
               2) gallery_images[]      (supporting_visual)
label        = "Vues produit / Détails"
layout       = single horizontal strip of up to 3 thumbnails (600px-safe table row)
styling      = inline, email-safe; object-fit:cover for stable thumbnail framing
truth        = NONE of these are business truth; they are supporting VISUALS only
atmosphere   = excluded by default (atmosphere_used_in_fiche = false)
```

The strip is inserted **after** `primary_product_visual` and **before** `product_description` / `spec_list`.

---

## 3. Truth boundaries (unchanged, reaffirmed)

```
product_truth (name/reference/description/confirmed parameters) = the ONLY business truth
product_images = truth assets (the product); product_images[1..] are MORE VIEWS of the same product
gallery_images = supporting visual evidence, NOT identity truth
atmosphere = visual only, is_truth=False, never enters the Fiche fact area
AI-generated visual is never business truth
no free-form editing of technical spec VALUES (operator edits visibility/order only)
```

---

## 4. Diagnostics exposed by the preview response

```
container_profile               single_product_campaign_email | single_product_sheet_email
container_modules               [{order,key,present}] for the assembled container
body_visual_mode                product_image (fiche) | email_embedded_no_header (affiche)
primary_product_visual_present  bool
supporting_media_strip_present  bool
supporting_media_count          int (0..3)
supporting_media_sources        [ "same_product_view" | "supporting_visual" ... ]
product_image_count             int
gallery_image_count             int
atmosphere_present              bool
atmosphere_used_in_fiche        false (always, by contract)
```

---

## 5. selected_email_body_visual persistence

The selected route is Workbench truth. The operator's selection is persisted via
`PATCH /api/v2/workbench/{key}/selected-visual` and the preview/send assemble strictly from
`workbench.selected_email_body_visual`. A preview-time `email_fill_format` / `container_profile` assertion may only
VALIDATE against the selected route (mismatch → 422); it never overrides the persisted selection.

```
select Fiche   -> GET workbench.selected_email_body_visual == "fiche"
select Affiche -> GET workbench.selected_email_body_visual == "affiche"
```

---

## 6. Out of scope / HOLD

```
products[] backend                  HOLD
multi-product runtime               HOLD
P2A demo backend mapping            HOLD
OPS-authenticated remote smoke      HOLD (BLOCKED_OPS_AUTH_REQUIRED)
real customer send                  HOLD
```
