# CUISTANCE Trial — 850a0af Remote Browser Verify v1 — PASS

Task: **POSTER2-CUISTANCE-TRIAL-850A0AF-REMOTE-BROWSER-VERIFY**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1` @ HEAD `850a0af`.
Status: **PASS** — literal browser/UI validation of the deployed trial send alignment and the replaceable
banner/header. No code changed. One real test email to the authorized internal recipient only.

Validation method: **Playwright + system Chrome** (`channel="chrome"`) driving the deployed
`/cuistance_trial.html` and inspecting the real Network responses.

---

## 1. Remote deployed commit status

**Deployed at `850a0af` or later.** The served page carries the commit's markers
(`hdrvar`, `updateHeaderDiag`, `selectedHeaderVariant`, `header_logo_missing_fallback`, and the send mapping
`deliveryMode=(curMode()==='real')?'resend':'inline_only'`); the backend preview returns the new
`header_variant` / `header_logo_*` fields. Health `/healthz=200`, page `200`.

## 2. Browser UI send result

Flow driven in a real Chrome: OPS login (connection bar) → recover workbench `wb_9308b112feb0436e` → Fiche →
预览邮件 (preview_ready=true) → recipient `zhaojfifa@gmail.com` → 正式发送 → 确认发送 → send once.

```
UI send summary : 已发送真实测试邮件 1 封
UI results row  : 模式=real · provider=resend · status=sent · sent=1 · skipped=0 · failed=0 ·
                  message_id=e46866d5-fed5-4915-9a7e-ae4b11f4f13f · real_email_sent=true
Network /email/send response: sent_count=1, skipped_count=0, failed_count=0, status=sent, provider=resend,
                  provider_message_id=e46866d5-fed5-4915-9a7e-ae4b11f4f13f
VERDICT = REAL_SEND_OK  (NOT inline_only / preview_only / skipped)
```

## 3. Provider

`resend`.

## 4. Provider message id

`e46866d5-fed5-4915-9a7e-ae4b11f4f13f`.

## 5. Banner/header variant result

Both variants validated through the deployed UI preview (Network `/email/preview`):

```
css_dark_bar_wordmark (default): header_variant=css_dark_bar_wordmark, header_logo_used=false, fallback=false
logo_image_bar (UI radio)      : header_variant=logo_image_bar, header_logo_used=true, fallback=false
UI header diagnostics line      : 当前 Header：Logo 图片条 · Logo 已使用：是
logo source                     : email_banner.logo ONLY (header_logo_url present); product/gallery/atmosphere NOT used as logo
```

## 6. Fiche regression

```
supporting_media_strip_present = true
supporting_media_count         = 3
atmosphere_used_in_fiche       = false
preview_ready                  = true
```

Intact in both browser previews.

## 7. Affiche regression

Authenticated API check (selected affiche, previewed, restored fiche):

```
container_profile               = single_product_campaign_email
email_body_visual_contract_pass = true
body_visual_contains_own_banner = false  (no inner banner)
supporting_media_strip_present  = false
```

## 8. Any customer email sent

**No.** Exactly one real test email to the authorized internal recipient `zhaojfifa@gmail.com`. No batch, no
customer address. (The two header previews do not send.)

## 9. Evidence path

```
docs/poster2/assets/cuistance_trial_send_mainline_align_banner_flex_remote_verify_v1/evidence.json
```

## 10. Remaining HOLD

```
customer send / batch send   HOLD
products[] / multi-product   HOLD
P2A demo backend mapping     HOLD
```

The workbench was restored to defaults afterward (`selected=fiche`, `header_variant=css_dark_bar_wordmark`), and the
OPS session was logged out. Real send remains owner/test-gated.
