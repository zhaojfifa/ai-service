# Container Deep Migration v1 — ttt.html (Fiche) + ttt2.html (Affiche)

Task: **POSTER2-CUISTANCE-DEEP-CONTAINER-MIGRATION-V1**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.
Design analysis: `container_deep_migration_design_review_v1.md`. Visual review:
`docs/poster2/assets/container_deep_migration_v1/visual_review.md`.

Rebuilds both email containers around the real reference HTML containers so the first operator-usable CUISTANCE
email reads as native, not an engineering preview. No `products[]`, no multi-product, no send rebuild, P2A demo
untouched.

---

## 1. Why the previous container was insufficient

A single flat 600px table: thin dark wordmark bar, plain image, one-size sans text, small flat CTA, light-grey
one-line footer, large empty whitespace. It read as an engineering preview, below the original HTML reference.

## 2. How ttt.html was used for Fiche (ttt_product_sheet_container)

Adopted the `ttt.html` Mailchimp grammar (design shell only):

```
dark #1f2329 header, centered serif CUISTANCE brand element, uppercase channel·campaign meta, red #E1002A filet
white 600px body: italic serif reference line + big 30px serif title
centered hero product image
supporting media strip ("VUES PRODUIT / DÉTAILS")
italic serif description + ✔ red-check spec block (confirmed parameters) + reference line
#eaeaea divider + rounded (14px) red #df3004 CTA
dark #333333 footer: brand + CONTACT (phone/email) + legal (rights/url/copyright/address) + non-tracking unsubscribe
```

## 3. How ttt2.html was used for Affiche (ttt2_campaign_container)

Adopted the `ttt2.html` campaign grammar + the poster PSD layers (`图层示意/细节`):

```
same dark header + red filet
modest serif campaign title + intro
the GENERATED POSTER VISUAL (email-embedded, no inner banner) as the centered main body
rounded red CTA
dark #3F3F3F footer (brand + contact + legal)
NO spec_list duplication — the poster already carries the product hero/title/specs
NO double header — the email header is separate from the no-inner-banner body visual
```

## 4. Banner replacement behavior

```
container_visual_variant : auto per route (ttt_product_sheet_container / ttt2_campaign_container)
header_variant           : css_dark_bar_wordmark (default) | logo_image_bar  (operator-selectable, persisted)
banner_source            : default_wordmark | uploaded_logo | wordmark_fallback
banner_replaceable       : true
logo source              : email_banner.logo ONLY — NEVER product / gallery / atmosphere / AI visuals
fallback                 : logo_image_bar requested + no logo -> wordmark, header_logo_missing_fallback=true
```

The brand logo sits directly on the dark header (ttt grammar; the CUISTANCE brand logo is light-on-transparent).

## 5. Product replacement behavior

```
Fiche  : product_truth.product_name -> serif title ; reference -> reference line ; description -> serif description ;
         confirmed parameters -> ✔ spec block ; product_images[0] -> hero ; product_images[1..] -> strip
         (same_product_view) ; gallery_images[] -> strip (supporting_visual) ; atmosphere -> NOT used
Affiche: selected body visual -> campaign visual ; deterministic subject/intro/CTA ; deterministic footer
```

Verified by test `test_fiche_product_replacement_fills_ttt_container`: replacing the product truth+image swaps the
rendered name/reference/description/spec/image and the previous product does NOT leak.

## 6. Layout / typography improvements

```
600px centered body ; reduced empty whitespace ; centered hero product image
serif (Georgia/Playfair) editorial headline hierarchy ; stronger contrast
rounded red #df3004 CTA matching the reference ; dark contact+legal footer matching the reference
supporting media strip aligned as a clean centered row
```

## 7. Screenshot review

Rendered locally (deterministic) + screenshotted via Playwright + Chrome at 600px:

```
docs/poster2/assets/container_deep_migration_v1/fiche_screenshot.png   -> Fiche  : PASS
docs/poster2/assets/container_deep_migration_v1/affiche_screenshot.png -> Affiche: PASS_WITH_NITS
```

Gate met: both >= PASS_WITH_NITS; no catastrophic layout; no double header; no broken image; no truth leakage
(no Mailchimp tracking/unsubscribe/list-manage, no stale sample facts; specs from confirmed parameters only).

## 8. Send path preservation

No send code changed. Real send still routes through the shared mainline Resend provider when
`delivery_mode=resend`; real success still requires a `provider_message_id`; preview-only (`inline_only`) still
records `skipped`/`preview_only`. Verified by the existing `test_workbench_email_send` suite (incl. the alignment
tests). `real_email_sent` is surfaced false in preview.

## 9. Remote validation

**PENDING_REDEPLOY.** The new container backend is not yet deployed (this commit must reach Render first). The
send path itself was already validated end-to-end in a real browser in the prior task (same endpoint). After
Render deploys this commit, one internal test send to `zhaojfifa@gmail.com` can confirm the received email uses the
new ttt/ttt2 container.

## 10. Remaining HOLD

```
customer send                HOLD
customer batch send          HOLD
products[] / multi-product   HOLD
P2A demo backend mapping     HOLD
remote ttt/ttt2 container validation : PENDING redeploy
```
