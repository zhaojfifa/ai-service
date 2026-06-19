# CUISTANCE v1 · Step3 最终邮件预览绑定修复 v1

Purpose: Finish Step 3 — wire the right-side final email preview to the real backend `email/preview` endpoint,
render the assembled email, label it generated, gate send until a preview exists, and keep send semantics honest.
Status: submitted for Owner review — **local REAL-backend browser verification PASS** (`was_stubbed=false`).
Scope: Frontend/backend-contract wiring only. NO backend API / renderer / email-provider / send-behavior change.
No real email sent.
Source dependencies: `frontend/cuistance_trial.html` (+ `docs/cuistance_trial.html` mirror); existing v1 endpoints
`/api/v2/workbench/{key}/email/preview` + `/email/send`.
Owner gate: Owner review; remote browser validation with OPS auth (deploy + creds gated).

Task: `POSTER2-CUISTANCE-V1-FINAL-EMAIL-PREVIEW-BINDING-FIX`.

---

## 1. Fixes (frontend wiring — backend unchanged)

1. **Preview button bound to backend.** `预览邮件` now: (a) ensures `selected_email_body_visual` exists and the
   selected candidate is ready with a poster_key/url (refresh + load if needed); (b) calls
   `POST /api/v2/workbench/{key}/email/preview`; (c) on **HTTP 200** renders the returned assembled email HTML into
   the right-side 600px frame and sets the badge to `邮件预览已生成` + a business summary
   `邮件主体：目标海报|简单产品页 · 邮件格式：目标海报邮件格式|简单产品页邮件格式`; (d) on failure shows
   `邮件预览生成失败，请检查邮件主体和素材` (raw detail diagnostics only).
2. **Render backend content, not the local mock.** The preview consumes the backend response, accepting whichever
   assembled-email field it returns: `html` (current) → `assembled_html` → `email_html` → `preview_html`. The panel
   no longer says `预览示意，尚未生成邮件预览` after a 200.
3. **Preview binding diagnostics.** Diagnostics record workbench_key, selected_email_body_visual,
   body_visual_poster_key, preview_status, layout_type, selected/inferred email fill format, final_poster_url_present,
   `backend_preview_html_present`, `final_preview_rendered`. Main UI shows none of these engineering fields.
4. **Send gating.** Send is disabled until a backend preview has been generated in the current state; attempting it
   shows `请先生成邮件预览`. After a successful preview the send button is enabled. Send semantics remain strict: a real
   delivery REQUIRES a `provider_message_id`; `inline_only`/`preview_only`/`skipped` →
   `当前环境未配置真实发送服务，已记录预览发送证据，未真实投递`; never `发送成功/真实发送成功/已发送`.
5. **Recovery interaction.** After Command+R, entering Step 3 (selection restored) shows `需要重新生成邮件预览` (amber)
   with the illustrative panel and send disabled — a fake final email is never shown as confirmed unless the backend
   preview is actually (re)generated. Selecting a different body visual or switching fill format marks the preview
   stale (`需要重新生成邮件预览`) and re-gates send.

No forbidden engineering terms on the default visible UI; no user-facing fallback/degraded wording.

## 2. Files changed

- `frontend/cuistance_trial.html` — `previewGenerated` flag; `setEmailPreviewBadge`/`updateSendGate`/
  `updateStep3Preview`/`markPreviewStale`; rewritten `预览邮件` handler (pre-checks, multi-field backend HTML,
  rich diagnostics, failure message); send gating in `openSendModal`; Step-3 enter hook in `render()`.
  `docs/cuistance_trial.html` mirror.
- `scripts/poster2_cuistance_final_email_preview_binding_proof.py` — REAL-backend Playwright proof (no stubbing).
- **Backend: unchanged.**

## 3. REAL-backend browser verification (local, non-stubbed)

Real `app.main` backend; real page; Playwright NO route stubbing (real chromium affiche render; real
`/email/preview` assembly; inline provider → preview_only). Artifacts:
`docs/poster2/assets/cuistance_final_email_preview_binding_v1/` (01–05 + evidence.json).

| # | File | Proves |
|---|------|--------|
| 01 | step3_before_preview_not_generated | Before preview: `需要重新生成邮件预览`; send disabled. |
| 02 | step3_after_backend_preview_generated | After 200: `邮件预览已生成`; backend assembled email rendered. |
| 03 | step3_preview_contains_generated_poster | Preview contains banner + the selected generated poster body + CTA + footer. |
| 04 | send_preview_only_not_real_sent | mode=real/inline_only → preview-only, not real sent. |
| 05 | diagnostics_email_preview_binding_evidence | binding/engineering fields in diagnostics only. |

Evidence JSON (`evidence.json`): `was_stubbed=false`; before_preview_badge=`需要重新生成邮件预览`;
send_disabled_before_preview=true; preview_http_status=200; after_preview_badge=`邮件预览已生成`;
send_disabled_after_preview=false; backend_preview_html_present=true; final_preview_rendered=true;
preview_contains_generated_poster=true; selected_email_body_visual=affiche; body_visual_poster_key present;
selected_or_inferred_email_fill_format=campaign_poster_email; layout_type=single_product_promo; send_mode=real/
send_provider=inline_only/send_status=skipped/send_error_code=preview_only/provider_message_id_present=false/
real_email_sent=false; ui_send_label_correct=true.

Validation: `check_docs_router.py --all` PASS; `check_email_fill_format_alignment.py` PASS; inline JS syntax OK;
main-UI forbidden-term + fallback scan NONE. Backend untouched → no backend tests run.

## 4. Remaining blockers / non-blockers

- Remote browser validation pending deploy + OPS creds (validation only; binding proven on a real backend locally
  with `was_stubbed=false`). On remote, preview/send run after OPS login.
- Real send needs a configured provider + provider_message_id; until then preview-only is correctly reported. Fiche
  real generation needs Vertex Imagen3.

## 5. Recommendation

**GO** — Step 3 final preview is bound to the backend `email/preview` (200 → rendered assembled email labeled
`邮件预览已生成`, containing the selected generated poster), send is gated until a preview exists, and inline_only/
preview_only is honestly not labeled real sent. Remote confirmation remains, gated on deploy + OPS creds.

STATUS: FINAL EMAIL PREVIEW BINDING SUBMITTED FOR OWNER REVIEW.
