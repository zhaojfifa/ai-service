# Email Package Send-Binding — Remote Verify v1 (commit 8aa7ba8) — PASS

Task: **POSTER2-EMAIL-PACKAGE-SEND-BINDING-REMOTE-VERIFY-V1**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.
Status: **PASS** — the P0 send-binding fix is live and verified on remote: **sending Affiche delivers Affiche**. No
code changed. One real email to the authorized internal recipient only; no customer email.

Method: OPS-authenticated API mirroring the new UI `sendThisVersion` flow (PATCH select route → send with
`selected_email_package=route`) on workbench `wb_9308b112feb0436e`.

---

## 1. Remote deployed commit status

**Deployed at `8aa7ba8` or later.** The served `/cuistance_trial.html` carries the new send-binding markers
(`sendThisVersion`, `pendingSendPackage`, `sent_package_type!==route`, `selected_email_package:route`), and the
backend send response now returns the new `email_fill_format` field. Health 200.

## 2. New send-binding markers present

Yes — `sendThisVersion` (the complete explicit per-route send), `pendingSendPackage` (the bound package), and the
`sent_package_type!==route` mismatch→error guard are all in the deployed JS.

## 3. Affiche send binding result — PASS (AFFICHE_BIND_REAL_OK)

Selected Affiche, then sent `selected_email_package=affiche` (one real `resend` send to the internal recipient):

```
sent_package_type            = affiche
selected_email_body_visual   = affiche
email_fill_format            = campaign_poster_email
container_visual_variant     = ttt2_campaign_container
body_visual_poster_key       = p2_9f215cca560e4e2d   (non-null -> the Affiche poster body, NOT Fiche)
provider                     = resend
provider_message_id          = b2c8b594-a271-4659-9198-ab1ac824dff6
real_email_sent              = true
attempt status               = sent
```

**Sending Affiche sent Affiche.** The previously-observed P0 (Affiche selected → Fiche delivered) is resolved.

## 4. Provider / provider_message_id

`resend` / `b2c8b594-a271-4659-9198-ab1ac824dff6`.

## 5. Fiche dry binding result — PASS (no real email)

Selected Fiche, sent `inline_only` (preview-only, NOT a real send):

```
sent_package_type        = fiche
email_fill_format        = product_sheet_email
container_visual_variant = ttt_product_sheet_container
body_visual_poster_key   = null            (no Affiche poster used)
real_email_sent          = false           (inline_only -> attempt skipped)
```

## 6. Mismatch guard result — PASS

Persisted selection = fiche, send `selected_email_package=affiche` → `422 selected_package_mismatch`. The send is
unambiguous; a divergence is rejected rather than silently sending the wrong version.

## 7. UI result display

The deployed UI shows `已发送版本：目标海报邮件 · 容器 · 海报Key · provider_message_id` on success, and — via the
deployed `sent_package_type!==route` logic — shows an **error (not success)** if the backend's `sent_package_type`
does not match the clicked package. The send response provides all the fields the UI displays
(`sent_package_type`, `provider`, `provider_message_id`).

## 8. Remaining HOLD

```
customer send / batch send   HOLD
products[] / multi-product   HOLD
final designer banner assets HOLD
P2A demo backend mapping     HOLD
```

The workbench selection was restored to its original value and the OPS session was logged out.

## Owner Decision Needed

Accept the send-binding hotfix as remote-verified (Affiche sends Affiche; Fiche binds to Fiche; mismatch rejected).
Commission the designer banner assets for final quality. `customer/batch send` and `products[]` remain HOLD.
