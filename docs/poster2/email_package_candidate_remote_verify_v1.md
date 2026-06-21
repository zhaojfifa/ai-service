# Email Package Candidate — Remote Verify v1 (commit ce28295) — PASS

Task: **POSTER2-EMAIL-PACKAGE-CANDIDATE-REMOTE-VERIFY-V1**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1` @ HEAD `ce28295`.
Status: **PASS** — the email package candidate layer is live and verified on remote. No code changed. No real/customer
email sent.

Method: OPS-authenticated API calls (the exact calls the trial UI makes) on the existing workbench
`wb_9308b112feb0436e`. The deployed page also carries the package-card markers.

---

## 1. Remote deployed commit status

**Deployed at `ce28295` or later.** `GET /api/v2/workbench/{key}/email/packages` returns `401` (deployed + ops-gated,
not `404`); the served `/cuistance_trial.html` carries `pkgCards`, `loadPackages`, `email/packages`,
`selected_email_package`, `发送这个版本`. Health 200.

## 2. Package endpoint result

`GET /email/packages` → `200`, returns `email_package_candidates: { fiche, affiche }`, each exposing `status`,
`preview_ready`, `send_ready`, `subject`, `body_visual_url`, `container_profile`, `container_visual_variant`,
`banner_variant`, `missing_required_fields`, `package_updated_at`, `staleness_status` (+ route-specific fields).

## 3. Fiche package result — PASS

```
package_type=fiche, status=ready, preview_ready=true, send_ready=true
uses_poster_generation=false, generated_from=workbench_truth
supporting_media_count=3, product_image_count=2, gallery_image_count=3
container_visual_variant=ttt_product_sheet_container, banner_variant=brand_standard_header
staleness_status=maybe_stale  (generated before a later content edit — real staleness signal)
```

## 4. Affiche package result — PASS

```
package_type=affiche, status=ready, preview_ready=true, send_ready=true
poster_key=p2_9f215cca560e4e2d, standalone_poster_url present, email_body_visual_url present
available_attachment_types=[]  (field present)
container_visual_variant=ttt2_campaign_container, banner_variant=campaign_poster_header
staleness_status=fresh
```

## 5. Switching behavior — PASS

```
select fiche   -> packages: fiche=ready, affiche=ready (affiche package retained)
select affiche -> packages: fiche=ready, affiche=ready (fiche package retained)
```

Neither route's package is lost on switch; both cards remain populated.

## 6. Send selection behavior — PASS (non-real)

A non-delivering `inline_only` send (to the authorized internal address) confirms the new send-response reporting:

```
delivery_mode=inline_only -> attempt status=skipped, real_email_sent=false  (NOT a real send)
sent_package_type=affiche, selected_email_body_visual=affiche,
body_visual_poster_key=p2_9f215cca560e4e2d, container_visual_variant=ttt2_campaign_container
```

No real send was run: the send path is unchanged code and was already proven real at `850a0af`
(`provider_message_id` present). The shape was validated without sending another real email.

## 7. Mismatch guard result — PASS

With `selected_email_body_visual=affiche`, a send asserting `selected_email_package=fiche` returns
`422 selected_package_mismatch` — the sent package is unambiguous.

## 8. Staleness result — PASS

Observed live: the fiche package = `maybe_stale` (its candidate predates a later content edit), the affiche package =
`fresh`. The signal differentiates correctly on real data, and the send UI surfaces it (it does not hide stale
packages). The mechanism (monotonic `content_version`) is also covered by a local test
(`test_staleness_maybe_stale_after_content_change`). The live workbench truth was NOT mutated for this check.

## 9. Remaining HOLD

```
customer send / batch send   HOLD
products[] / multi-product   HOLD
final designer banner assets HOLD (designer brief delivered)
P2A demo backend mapping     HOLD
```

The workbench was restored to its original selection (`fiche`) and the OPS session was logged out.

## Owner Decision Needed

Accept the package-candidate layer as remote-verified. Commission the designer banner assets for final quality (the
banner remains the accepted interim default). `customer/batch send` and `products[]` remain HOLD.
