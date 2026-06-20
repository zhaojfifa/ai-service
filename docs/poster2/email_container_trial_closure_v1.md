# Email Container Trial Closure v1

Task: **POSTER2-EMAIL-CONTAINER-TRIAL-CLOSURE-V1**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.
Goal: 打通邮件试用链路 · 补强邮件容器灵活性 · 补强邮件容器可填充性 · 保护现有 Affiche / Fiche 基线.

This slice strengthens the **existing** email-container trial flow. It does NOT start a new UI, does NOT touch
the P2A demo page, does NOT implement `products[]`, and does NOT enable real send. All backend additions are
**additive and backward compatible** (the two live routes keep their existing PASS contracts).

---

## 1. What was wrong before

```
邮件容器灵活性不足  — the container had no explicit, inspectable profile/mode vocabulary; the only knob was
                     email_fill_format. Header / spec / body-visual modes were implicit and unnamed.
邮件容器可填充性不足 — there was no explicit signal of WHICH fields filled from truth and WHICH were missing.
                     A fiche with no product image rendered an empty body silently (no blocked/missing status).
```

## 2. What was changed

Backend (additive, no behavior/truth change):

```
app/services/email/assembly.py
  + container_profile_for() + CONTAINER_PROFILE_FOR_FILL_FORMAT
  + per-assembly: container_profile, header_variant, spec_display_mode, body_visual_mode
  + fillability: filled_subject/intro/cta/footer, missing_required_fields[], preview_ready
  (also mirrored inside the email_container dict)

app/schemas/poster2.py
  + ContainerProfile = single_product_campaign_email | single_product_sheet_email
  + CONTAINER_PROFILE_FOR_FILL_FORMAT
  + WorkbenchEmailPreviewRequest.container_profile (optional, validated)
  + EmailAssemblyPreviewResponse: container_profile, header_variant, spec_display_mode, body_visual_mode,
    filled_subject, filled_intro, filled_cta, filled_footer, missing_required_fields, preview_ready,
    send_hold (=true), real_email_sent (=false)  — all optional/defaulted (backward compatible)

app/main.py (preview endpoint only; send path UNCHANGED)
  + container_profile_mismatch guard (same model as email_fill_format_mismatch)
  + wires the new fields into the preview response
```

Frontend (minimal, no layout drift — only the existing trial page):

```
frontend/cuistance_trial.html  (+ byte-identical docs/cuistance_trial.html mirror)
  + business-readable container fill state: 邮件容器已填充 / 邮件容器待补充
    (待补充：缺少产品图 · 缺少产品名称/型号 · 缺少产品参数 · 真实发送仍 HOLD)
  + extended internal diagnostics (container_profile / spec_display_mode / body_visual_mode /
    preview_ready / missing_required_fields / send_hold / real_email_sent)
```

The container is a **named profile with deterministic per-route modes**, NOT a general template engine. The
`container_profile` request field is a *bounded assertion* (it must match the selected visual's canonical profile,
exactly like `email_fill_format`) — there is no free-form profile selection and no free-form spec-value editing.

## 3. How Affiche fills the container

```
container_profile  = single_product_campaign_email
header_variant     = ttt_html_header (CSS dark bar + CUISTANCE wordmark + red filet; no header-band cover)
body_visual_mode   = email_embedded_no_header (cropped, no inner banner) from the generated poster_record
spec_display_mode  = in_visual (specs are baked into the poster body visual)
title/intro        = operator copy from the deterministic draft (parameters never sent to Gemini)
cta                = Nous contacter
footer/contact     = channel · campaign meta
required: email_body_visual present, subject, cta_label
```

## 4. How Fiche fills the container

```
container_profile  = single_product_sheet_email
header_variant     = ttt_html_header
body_visual_mode   = product_image (the product image; NO poster generation, NO poster_key)
spec_display_mode  = spec_list (from CONFIRMED product_truth.parameters) | spec_list_empty (advisory)
title              = product_name | reference
description        = product_truth.description
specs              = confirmed parameters only (values are truth, read-only)
cta                = Nous contacter
footer/contact     = channel · campaign meta
required: product_image present, product_identity (name|reference)
```

No business truth is ever taken from atmosphere / gallery / reference HTML / PSD; no AI-generated fact is inserted;
no unknown-product fallback.

## 5. Missing-field behavior

```
preview_ready = (missing_required_fields == [])
missing codes: product_image | email_body_visual | product_identity | subject | cta_label
spec advisory: spec_display_mode = spec_list_empty (fiche with no confirmed parameters)
```

Missing required fields are **surfaced, not silently filled** — the preview still returns 200 (it is a preview,
not a send) but `preview_ready=false` and the operator sees a business-readable “待补充” status. There is no wrong
fallback and no generic-product substitution.

## 6. Send semantics

```
preview-only default : delivery_mode=inline_only -> provider returns preview_only -> attempt status=skipped
real send HOLD       : real delivery requires explicit confirm_send AND delivery_mode=resend AND a configured
                       provider (env/ops gated); mark_sent only when mode=real AND a provider_message_id exists
real_email_sent      : surfaced false in the preview response; a real send is proven ONLY by provider_message_id
```

The send path was **not changed** in this task. No real customer email was sent. No real send was enabled by default.

## 7. What remains HOLD

```
new demo UI review (P2A)              — HOLD (demo files untouched)
backend mapping from the demo UI       — HOLD
products[]                             — HOLD (not implemented)
multi-product runtime                  — HOLD
real customer send                     — HOLD
```

## 8. Next recommended step after this trial closure

```
POSTER2-EMAIL-CONTAINER-TRIAL-REMOTE-VALIDATION
  — OPS-authenticated remote validation of the two routes' preview_ready + container_profile + missing-field
    surfacing on Render (requires OPS creds + deploy). Multi-product and real send stay HOLD.
```
