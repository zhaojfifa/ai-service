# Container Deep Migration — Visual Self-Review v1

Rendered locally from `build_email_assembly` output (deterministic), screenshotted via Playwright + system Chrome at
600px. Screenshots: `fiche_screenshot.png`, `affiche_screenshot.png` (HTML: `fiche_preview.html`,
`affiche_preview.html`).

Scale: **PASS** / **PASS_WITH_NITS** / **FAIL**.

## Fiche — ttt_product_sheet_container (default header = css_dark_bar_wordmark)

| Dimension          | Verdict | Note |
| ------------------ | ------- | ---- |
| banner quality     | PASS | dark #1f2329 bar, centered serif CUISTANCE wordmark, uppercase channel·campaign meta, red #E1002A filet |
| logo/header quality| PASS | brand element centered; no product/gallery/atmosphere in header |
| body layout        | PASS | 600px centered white body, balanced whitespace (the large empty-space problem is gone) |
| product containment| PASS | centered hero product image, bordered, properly sized |
| text hierarchy     | PASS | italic serif reference line → big 30px serif title → italic description → ✔ spec block |
| CTA quality        | PASS | rounded (14px) red #df3004 "Nous contacter" button, reference-style |
| footer quality     | PASS | dark #333333 footer, white wordmark, CONTACT (phone/email), legal block |
| email-native feel  | PASS | reads as a native CUISTANCE editorial email, not an engineering preview |

**Overall Fiche: PASS.**

## Affiche — ttt2_campaign_container (header = logo_image_bar, white CUISTANCE logo)

| Dimension          | Verdict | Note |
| ------------------ | ------- | ---- |
| banner quality     | PASS | white CUISTANCE logo directly on the dark bar (ttt grammar) + meta + red filet |
| logo/header quality| PASS | logo = email_banner.logo ONLY; no double header |
| body layout        | PASS | the generated poster visual is the centered main body; no spec_list duplication (poster carries specs) |
| product containment| PASS | poster visual centered and sized to 540px max |
| text hierarchy     | PASS_WITH_NITS | modest serif campaign title + intro above the poster; the local preview uses a product image as the body-visual stand-in (in production this is the generated no-inner-banner poster) |
| CTA quality        | PASS | rounded red #df3004 button |
| footer quality     | PASS | dark #3F3F3F footer, logo, CONTACT, legal |
| email-native feel  | PASS | campaign shell framing the poster cleanly |

**Overall Affiche: PASS_WITH_NITS** (single nit: the body visual in the *local* preview is a product image stand-in,
because there is no live generated poster in the offline render; the container grammar/contract is correct).

## Acceptance gate

```
Fiche screenshot   : PASS              (>= PASS_WITH_NITS) ✓
Affiche screenshot : PASS_WITH_NITS    (>= PASS_WITH_NITS) ✓
no catastrophic layout issue ✓
no double header ✓   (header separate from the no-inner-banner body visual; affiche contract_pass=true)
no broken image ✓    (white logo renders on the dark bar; product images load)
no truth leakage ✓   (no Mailchimp tracking/unsubscribe/list-manage; no stale sample facts; specs from confirmed params only)
```

Banner/header never uses product / gallery / atmosphere / AI visuals as the logo — only `email_banner.logo`
(verified by test `test_header_never_uses_product_gallery_atmosphere_as_logo`).
