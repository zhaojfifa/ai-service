# Email Container Owner-Gated Real Send Smoke v1 — PASS (REAL_SEND_OK)

Task: **POSTER2-EMAIL-CONTAINER-OWNER-GATED-REAL-SEND-SMOKE-V1**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1` @ HEAD `4fe1aa3` (code at `396c7ea`).
Status: **PASS** — OPS-authenticated remote preview validated for both routes, and one owner-gated real test send to
the single authorized internal recipient succeeded with a real provider message id. No code change. No customer email.

---

## 1. Auth status

```
OPS creds: /tmp/cuistance_ops_auth/creds.env present (OPS_USER, OPS_PASS) — values not printed
POST /api/auth/ops-login -> authenticated=true (cookie session)
GET  /api/auth/me        -> {enabled:true, authenticated:true, username:"ops"}
```

## 2. Remote deployed commit status

```
remote reachable: /healthz=200, /cuistance_trial.html=200
deployed build serves the 396c7ea structure-first Fiche container (proven by live behavior below:
supporting_media_strip_present=true + supporting_media_count=3 + "Vues produit / Détails" in HTML — fields/markup
that only exist at >= 396c7ea). No /version endpoint, so exact hash is inferred from behavior, not read directly.
```

## 3. Fiche preview result (workbench wb_9308b112feb0436e)

```
selected_email_body_visual     = fiche
email_fill_format              = product_sheet_email
container_profile              = single_product_sheet_email
preview_ready                  = true
primary_product_visual_present = true
supporting_media_strip_present = true
supporting_media_count         = 3
supporting_media_sources       = [same_product_view, supporting_visual, supporting_visual]
product_image_count            = 2
gallery_image_count            = 3
atmosphere_present             = true
atmosphere_used_in_fiche       = false
send_hold                      = true
real_email_sent                = false
HTML contains "Vues produit / Détails" = true
```

All expected fields matched — the structure-first Fiche supporting-media fix is live and correct on remote.

## 4. Affiche regression result

Temporarily selected affiche, previewed, then restored fiche before sending.

```
email_fill_format              = campaign_poster_email
container_profile              = single_product_campaign_email
preview_ready                  = true
email_body_visual_contract_pass= true
body_visual_contains_own_banner= false
real_email_sent                = false
supporting_media_strip_present = false   (correct: affiche poster carries its own views)
```

Regression PASS. Selection restored to `fiche` (GET-confirmed) before the send.

## 5. Send payload summary (no secrets)

```
POST /api/v2/workbench/wb_9308b112feb0436e/email/send
{ "recipients": ["zhaojfifa@gmail.com"], "mode": "test", "delivery_mode": "resend", "confirm_send": true }
```

Single authorized internal recipient. No batch. No customer address. `delivery_mode=resend` + `confirm_send=true`
invoke the real Resend provider; `mode=test` labels it a test (not a customer campaign).

## 6. Send response summary

```
HTTP 200
mode=test  total=1  sent_count=1  failed_count=0  skipped_count=0
attempt: recipient=zhaojfifa@gmail.com  status=sent  provider=resend
         provider_message_id=bd9fce38-4678-46db-bed8-fff2ca6a48cc
VERDICT = REAL_SEND_OK
```

## 7. provider_message_id

`bd9fce38-4678-46db-bed8-fff2ca6a48cc` — present → real delivery, not an inline/preview skip.

## 8. real_email_sent

**true** (evidenced by `status=sent` + `provider=resend` + a non-null `provider_message_id`).

## 9. Customer email sent

**No.** Exactly one email to the authorized internal test address `zhaojfifa@gmail.com`. No customer, no batch.

## 10. Remaining HOLD

```
real send remains gated (NOT enabled by default; requires confirm_send + delivery_mode=resend + provider env)
customer / batch send             HOLD (forbidden)
products[] / multi-product backend HOLD
P2A demo backend mapping          HOLD
```

## Owner Decision Needed

Confirm receipt of the test email at `zhaojfifa@gmail.com` (provider id `bd9fce38-4678-46db-bed8-fff2ca6a48cc`).
The trial email chain (auth → Fiche preview with supporting media → Affiche regression → owner-gated real send) is
validated end-to-end. Decide whether to keep real send strictly owner/test-gated (recommended) before any broader
trial. `products[]`, multi-product, and customer sending remain HOLD.
