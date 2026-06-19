# CUISTANCE v1 · Step3 邮件填充格式 / 预览纠正 v1

Purpose: Fix Step 3 so the final email preview shows the COMPLETE send-ready email shape (not a cropped top band),
the email header/banner boundary is correct (header never includes product body), and the two HTML-derived email
fill formats are reliable as the content-organization layer before send.
Status: submitted for Owner review — **local REAL-backend browser verification PASS** (`was_stubbed=false`).
Scope: Step 3 frontend only. NO Step1/Step2 redesign, NO poster-generation change, NO renderer / email-provider /
send-behavior change. No real email sent.
Source dependencies: `frontend/cuistance_trial.html` (+ `docs/cuistance_trial.html` mirror); existing v1 endpoints;
`...reference_email_html_extraction_v1.md` (PR-3R grammar); `app/services/email/assembly.py` (read-only).
Owner gate: Owner review; remote browser validation with OPS auth (deploy + creds gated).

Task: `POSTER2-CUISTANCE-V1-STEP3-EMAIL-FILL-FORMAT-PREVIEW-CORRECTION`.

---

## 1. Root cause

The final preview iframe (`.mail-frame`) had a **fixed `height:560px` and `max-width:420px`**. The backend
assembles a 600px-wide, ~1200px-tall email (header strip → poster body → copy → CTA → footer), so only the top
~560px showed — the header band + a sliver of the poster. That read as "banner dominates / body cropped /
incomplete," i.e. the email header appearing to swallow the body. The backend assembly itself is correct: the
header is a dark strip using `email_banner.background` (CSS background) + logo, and the body visual is a separate
`<img>` of `final_poster.url` — they were never merged.

## 2. Fixes (Step 3 frontend — backend unchanged)

1. **Format ≠ banner option.** Step 3 keeps a distinct `邮件填充格式` selector (目标海报邮件格式 / 简单产品页邮件格式) and a
   separate `邮件页眉 / Header` module. Internal keys (`campaign_poster_email`/`product_sheet_email`) and `ttt/ttt2`
   stay in diagnostics only.
2. **Correct header/banner boundary.** The `邮件页眉 / Header` module is relabeled and constrained to a header band
   (`max-height:108px`, `object-fit:cover`) with the caption `仅邮件页眉（不含产品主体）` — it can no longer crop a
   body/product image and masquerade as the full email. The email-layer header asset is mapped per fill format
   (campaign_poster_email → Technitalia campaign banner / `option_2`; product_sheet_email → brand header /
   `option_1`), unless the operator manually overrides it. Before preview the header is persisted
   (`PATCH /workbench`) so the assembled header matches the chosen format.
3. **Complete, scrollable final preview.** `.mail-frame` is now `max-width:600px` with the height **auto-fitted to
   the assembled email's content** (`scrollHeight`, capped 1800px) inside a scrollable `#emailPreviewFrame`
   (`max-height:78vh; overflow:auto`). The whole send-ready email (header → body visual → copy → CTA → footer) is
   visible; tall emails scroll. The banner no longer visually dominates.
4. **Two-format validation check.** `scripts/check_email_fill_format_alignment.py` extended (advisory) to assert
   both formats are present, the ttt/ttt2 mapping is documented, Step 3 separates `邮件页眉` + `邮件最终预览`, and no
   third-party tracking/scripts/list-manage/Zoho/Mailchimp markers are copied into the UI. Runtime header-boundary
   assertions live in the proof evidence.
5. **Preview evidence.** On a successful preview the iframe document is inspected (same-origin) and diagnostics record
   selected_email_body_visual, selected/inferred fill format, preview_status, backend_preview_html_present,
   final_preview_rendered, preview_contains_header/body_visual/cta/footer, header_boundary_valid,
   no_body_content_in_header_banner.
6. **Step 3 UI clarity.** Left = 邮件填充格式 · 邮件页眉/Header · 邮件内容 · 测试发送/发送证据; right = 邮件最终预览 (full
   600px frame, scrollable). Labels show `邮件主体：目标海报|简单产品页` and `邮件格式：目标海报邮件格式|简单产品页邮件格式`.
7. **Send gating unchanged.** Send stays disabled until a backend preview exists; inline_only/preview_only →
   `当前环境未配置真实发送服务，已记录预览发送证据，未真实投递`; never `发送成功/真实发送成功/已发送`.

No raw ttt/ttt2 HTML copied; no third-party tracking. No forbidden engineering terms on the visible UI.

## 3. Files changed

- `frontend/cuistance_trial.html` — `.mail-frame` auto-fit + scrollable preview frame; header module relabel +
  header-band constraint + caption; per-format header mapping (`FORMAT_HEADER`, `bannerManual`); preview PATCHes the
  header then auto-fits the iframe and inspects header/body/cta/footer boundary. `docs/cuistance_trial.html` mirror.
- `scripts/check_email_fill_format_alignment.py` — extended advisory checks.
- `scripts/poster2_cuistance_step3_fill_format_preview_proof.py` — REAL-backend Playwright proof (no stubbing).
- **Backend: unchanged.**

## 4. REAL-backend browser verification (local, non-stubbed)

Real `app.main` backend; real page; Playwright NO route stubbing (real chromium affiche render; real `/email/preview`
assembly; inline provider → preview_only). Artifacts:
`docs/poster2/assets/cuistance_step3_email_fill_format_preview_correction_v1/` (01–07 + evidence.json).

| # | File | Proves |
|---|------|--------|
| 01 | step3_campaign_format_before_preview | campaign format selected; preview not yet generated. |
| 02 | step3_campaign_format_full_preview | full send-ready email (header → poster body → copy → CTA → footer). |
| 03 | step3_campaign_header_boundary_correct | header module = header band only (no body/product). |
| 04 | step3_product_sheet_format_preview_or_valid_unavailable | product_sheet format preview valid (header boundary ok). |
| 05 | step3_final_preview_scrollable_complete | iframe auto-fit (1218px) — complete, scrollable, not cropped. |
| 06 | send_preview_only_semantics_if_run | mode=real/inline_only → preview-only, not real sent. |
| 07 | diagnostics_email_fill_format_boundary_evidence | boundary/fill-format evidence in diagnostics only. |

Evidence JSON (`evidence.json`): `was_stubbed=false`; campaign_format_present=true; product_sheet_format_present=true;
ttt2_maps_to_campaign_poster_email=true; ttt_maps_to_product_sheet_email=true;
selected_or_inferred_email_fill_format=campaign_poster_email; preview_http_status=200;
backend_preview_html_present=true; final_preview_rendered=true; preview_contains_header=true;
preview_contains_body_visual=true; preview_contains_cta=true; preview_contains_footer=true;
campaign_header_boundary_valid=true; no_body_content_in_header_banner=true; preview_uses_body_visual_poster_key=true;
preview_iframe_height_px=1218; final_preview_scrollable_or_complete=true; product_sheet_preview_status=200;
product_sheet_header_boundary_valid=true; send_mode=real/send_provider=inline_only/send_status=skipped/
send_error_code=preview_only/provider_message_id_present=false/real_email_sent=false; ui_send_label_correct=true.

Validation: `check_docs_router.py --all` PASS; `check_email_fill_format_alignment.py` PASS (incl. new boundary/
tracking advisories); inline JS syntax OK; main-UI forbidden-term + fallback scan NONE. Backend untouched → no
backend tests run.

## 5. Remaining blockers / non-blockers

- Remote browser validation pending deploy + OPS creds (validation only; correction proven on a real backend locally
  with `was_stubbed=false`).
- Transitional: the affiche body visual (email_campaign_composite_v1) still bakes its own banner into the poster
  image (documented in assembly.py); the email-level header is separate and the boundary check confirms the header
  strip does not contain the body visual. Full body-only rendering would be a renderer contract change (out of
  scope). Fiche real generation needs Vertex Imagen3; real send needs a provider + provider_message_id.

## 6. Recommendation

**GO** — Step 3 final preview shows the complete send-ready email and is scrollable (no crop); header/banner
boundary is correct for both fill formats (no body-as-header); preview uses the selected generated body visual; CTA
and footer/contact/legal are visible; send remains gated and honest. Remote confirmation remains, gated on deploy +
OPS creds.

STATUS: STEP3 EMAIL FILL FORMAT PREVIEW CORRECTION SUBMITTED FOR OWNER REVIEW.
