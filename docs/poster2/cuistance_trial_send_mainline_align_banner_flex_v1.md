# CUISTANCE Trial Send — Mainline Alignment + Banner/Header Flexibility v1

Task: **POSTER2-CUISTANCE-TRIAL-SEND-MAINLINE-ALIGN-AND-BANNER-FLEX-V1**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.

Two changes only: (A) align the CUISTANCE trial UI send with the existing mainline send capability; (B) add minimal
replaceable banner/header support. No email-sending rebuild, no duplicate provider logic, no customer/batch send, no
`products[]`, P2A demo untouched.

---

## 1. Root cause — trial UI was not aligned with the mainline send path

The trial UI send button **hardcoded `delivery_mode:'inline_only'`** in `cuistance_trial.html`, so even when the
operator chose 正式发送 (real), the request routed to the inline provider → `provider:'inline_only'`,
`status:'skipped'`, `error_code:'preview_only'`, `provider_message_id:null` (the exact symptom reported).

The backend was never the problem: `POST /api/v2/workbench/{key}/email/send` already reaches the **same shared
provider path** as mainline (`app/services/email/providers.py` → `ResendEmailProvider(settings.resend)`) when
`delivery_mode='resend'`.

## 2. Mainline send path found and reused

```
endpoint     : POST /api/v2/workbench/{workbench_key}/email/send  (consumes the deterministic assembled package)
provider sel : app/services/email/providers.py get_email_provider(delivery_mode)
real provider: app/services/email/resend_provider.py ResendEmailProvider(settings.resend)  (same config as mainline /api/send-email)
semantics    : confirm_send required; delivery_mode=resend -> real provider; delivery_mode=inline_only -> preview_only/skipped
real success : status=sent AND provider_message_id present (provider=resend)
```

No parallel provider path was created; the trial reuses this exact mainline provider/config.

## 3. Trial send payload before / after

```
BEFORE: { recipients:[r], mode:curMode(), confirm_send:true, delivery_mode:'inline_only' }   // always preview-only
AFTER : { recipients:[r], mode:curMode(), confirm_send:true, delivery_mode:(curMode()==='real' ? 'resend' : 'inline_only') }
```

`selected_email_body_visual` is NOT sent in the body — the backend reads it from persisted Workbench truth (the
correct design). Single recipient only; no customer batch.

## 4. Preview-only vs real-send display rules

```
real (resend, provider_message_id present)        -> 已发送真实测试邮件 N 封
inline_only / preview_only / skipped              -> 未真实发送：当前为预览模式 / inline_only
error                                             -> 发送失败 N 封
mixed                                             -> 部分发送失败：真实 N / 失败 M
```

The UI now also shows a diagnostics row: `mode · provider · status · sent · skipped · failed · error_code ·
message_id · real_email_sent`. Skipped/preview_only is never labelled as sent.

## 5. Real-send success criteria

A UI send is marked successful ONLY if the backend returns `status=sent` AND `provider=resend` (configured real
provider) AND `provider_message_id != null`. Otherwise it is shown as not sent.

## 6. Banner/header replacement rules

Two variants (additive `EmailBanner.header_variant`, default keeps current behavior):

```
css_dark_bar_wordmark (default): dark bar + CSS CUISTANCE wordmark + channel/campaign meta + red filet
logo_image_bar                 : dark bar + email_banner.logo IMAGE + meta + red filet
```

Rules enforced in `assembly.py`:

```
logo_image_bar uses email_banner.logo ONLY (never product / gallery / atmosphere)
channel_name + campaign_label remain editable/fillable in both variants
red filet preserved; header has no body/product/CTA/footer
logo missing + logo_image_bar requested -> fall back to wordmark, header_logo_missing_fallback=true
```

Preview diagnostics: `header_variant, header_logo_url, header_logo_used, header_logo_missing_fallback,
header_channel_name, header_campaign_label`. The UI exposes a 文字品牌条 / Logo 图片条 selector and shows the current
header type + whether the logo was used + the fallback note.

Note: the response field `header_variant` now reports the brand-element variant
(`css_dark_bar_wordmark`/`logo_image_bar`); the header GRAMMAR/source stays `ttt_html_header`
(`email_header_source`/`header_source`).

## 7. Remote browser validation result

OPS-authenticated remote validation against `https://ai-service-leob.onrender.com` (workbench
`wb_9308b112feb0436e`). No Playwright in this environment, so the exact corrected-UI request was replayed at the API
level:

```
preflight: selected=fiche, preview_ready=true, supporting_media_count=3
REAL (mode=real, delivery_mode=resend): sent_count=1, status=sent, provider=resend,
       provider_message_id=2c895198-9e81-4ea0-9a4a-c380cca68cdd  -> REAL_SEND_OK
PREVIEW (mode=test, delivery_mode=inline_only): status=skipped, provider=inline_only, error_code=preview_only,
       provider_message_id=null -> correctly NOT a real send
```

One real test email to the authorized internal recipient `zhaojfifa@gmail.com` only. The inline_only call records a
skip (no delivery). The **deployed-frontend literal browser run** and the **header-variant remote diagnostics**
require a Render redeploy of this commit (header_variant backend is new and not yet deployed).

## 8. Remaining HOLD

```
customer send                    HOLD
batch / customer send            HOLD
products[] / multi-product       HOLD
P2A demo backend mapping         HOLD
header-variant remote validation HOLD (pending Render redeploy of this commit)
deployed-frontend literal browser HOLD (pending redeploy; validated at API level here)
```

## Owner Decision Needed

Confirm receipt of the test email at `zhaojfifa@gmail.com` (Resend id `2c895198-9e81-4ea0-9a4a-c380cca68cdd`). After
Render redeploys this commit, the deployed trial UI will issue `delivery_mode=resend` on 正式发送 and the
logo_image_bar header becomes available; a literal browser pass can then confirm both. Real send remains
owner/test-gated; customer/batch send and `products[]` stay HOLD.
