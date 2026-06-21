# Container Deep Migration — Design Review v1

Task: **POSTER2-CUISTANCE-DEEP-CONTAINER-MIGRATION-V1** (Part 1, design analysis BEFORE implementation).
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.

Goal: rebuild the two email containers so the first operator-usable CUISTANCE email looks **native**, shaped around
the real reference HTML containers, not an engineering preview.

References inspected (all present in `~/poster/ingredient/`): `ttt.html` (22 KB, Fiche), `ttt2.html` (114 KB,
Affiche), `产品海报.psd` (3.3 MB), `图层示意.png`, `图层细节.png`, `logo banner.png`, `logo_01.jpg`.

---

## 1. Why the previous container was insufficient

The previous container was a single flat 600px table: a thin dark wordmark bar, an image, a paragraph, a small flat
CTA, and a light-grey one-line footer. It read as an engineering preview:

```
- header was a thin bar, not the tall centered brand banner of the reference
- no editorial (serif) headline hierarchy — everything was one sans size
- product image was left in a plain padded box, not a centered hero
- CTA was a small flat link, not the reference rounded red-orange button
- footer was a single light-grey meta line, not the reference dark contact+legal footer
- large empty whitespace; weak contrast; not "CUISTANCE-native"
```

## 2. ttt.html → Fiche grammar (single_product_sheet_email / ttt_product_sheet_container)

Extracted from `ttt.html` (Mailchimp export):

```
templateHeader : background #222222, vertical padding ~68px, CENTERED CUISTANCE logo (width ~288)
templateBody   : #ffffff, max-width 600px centered, padding-top 36 / bottom 45
  headline    : Playfair Display serif. italic reference line ("RÉFÉRENCE PRODUIT : ...") + big 36px bold title
  hero image  : centered primary product image (width ~434)
  sub/desc    : 24px bold serif sub-title + italic 17px serif description
  divider     : 2px solid #eaeaea
  2nd image   : centered supporting product image (width ~383)
  spec block  : "✔" red check + bold product name + Dimensions + Référence + "Tarif = Nous contacter" (serif)
  divider     : 2px solid #eaeaea
  CTA         : rounded button border-radius 14px, background #df3004, white bold "Nous contacter", padding 18px
templateFooter : background #333333, padding 45/63, CENTERED logo, CONTACT (phone/email, white 12px), legal block
```

Brand palette: dark `#222222`/`#333333`, CTA `#df3004`, divider `#eaeaea`, serif Playfair Display/Georgia, body
Helvetica `#757575`/`#000000`, 600px centered white body.

## 3. ttt2.html → Affiche grammar (single_product_campaign_email / ttt2_campaign_container)

Extracted from `ttt2.html` (Zoho/campaign-image export) + `图层示意.png`/`图层细节.png` (the poster PSD layers):

```
shell      : 600px white campaign shell
header     : brand banner (red accent) + logo
body       : the GENERATED POSTER VISUAL is the main body (it already carries the product hero/title/specs:
             "LES RÉCHAUDS GAZ" / "EN PLUSIEURS DÉCLINAISONS" / "NOTRE COUP DE COEUR" / PUISSANCE / DISPOSITION /
             3.5 kW / 6 kW — these live INSIDE the poster, NOT duplicated by the email container)
intro/CTA  : short campaign intro + CTA (accent orange #eb7a00 / red #db4b38 in the reference)
footer     : dark footer #3F3F3F with contact + legal
no double header : the poster visual is the email-embedded NO-inner-banner variant; the email header is separate
```

Because the Affiche poster already contains the product copy/specs, the ttt2 container must NOT re-render a
spec_list (that would duplicate). It frames the poster with header + intro + CTA + dark footer only.

## 4. Truth boundaries (must hold — reference is design shell only)

```
ttt.html / ttt2.html are DESIGN/CONTAINER references, never business truth.
DO NOT copy as live truth:
  - Mailchimp tracking / unsubscribe URLs (list-manage.com/track, /unsubscribe, canspamBar "This email was sent to…")
  - the stale sample product facts (COUPE-FRITES, ref 1210025 (FC001), LES RÉCHAUDS GAZ, kW values)
  - the hardcoded mcusercontent / stratus.campaign-image image URLs as product truth
Business truth comes ONLY from product_truth (name/reference/description/confirmed parameters) + product_images.
The banner/header NEVER uses product / gallery / atmosphere / AI-generated images as the logo — only email_banner.logo.
The footer contact (commercial@cuistance.eu, +33 (0)1 71 84 11 20, cuistance-europe.com) is CUISTANCE's OWN brand
contact, rendered deterministically; the unsubscribe is a non-tracking placeholder ("#"), never the Mailchimp link.
```

## 5. Migration plan (implemented in Part 2+)

```
container_visual_variant (NEW default per route):
  fiche   -> ttt_product_sheet_container   (ttt.html grammar)
  affiche -> ttt2_campaign_container        (ttt2.html grammar)

header_variant (UNCHANGED fallback contract): css_dark_bar_wordmark (default) | logo_image_bar
  -> governs the brand element INSIDE the ttt header: wordmark (default) or uploaded email_banner.logo
  -> logo missing + logo_image_bar requested -> fallback to wordmark (header_logo_missing_fallback=true)

Preserve: 600px email-safe table/inline styles, dark #1f2329 header + red #E1002A filet (brand-consistent with the
reference dark header), supporting_media_strip ("Vues produit / Détails"), Affiche no-inner-banner contract
(email_body_visual_contract_pass / body_visual_contains_own_banner), the deterministic email_body_plan + diagnostics.

Upgrade: serif editorial headline hierarchy, centered hero product image, #eaeaea dividers, rounded #df3004 CTA
button, dark contact+legal footer, reduced whitespace, stronger contrast.

New diagnostics: container_visual_variant, banner_source, banner_replaceable=true (+ existing header_variant /
header_logo_url / header_logo_used / header_logo_missing_fallback).
```

## 6. Acceptance for this migration

```
Fiche + Affiche screenshots >= PASS_WITH_NITS
no double header · no broken image · no truth leakage (no Mailchimp tracking/unsubscribe, no stale facts)
Affiche no-inner-banner contract still PASS · supporting media strip still correct · send path unchanged
```
