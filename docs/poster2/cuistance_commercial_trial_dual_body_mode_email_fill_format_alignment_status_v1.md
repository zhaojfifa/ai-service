# CUISTANCE v1 · 双正式展示模式 + 邮件填充格式对齐 v1

Purpose: Correct the product model — CUISTANCE v1 has TWO equal first-class body visual modes (Affiche / Fiche),
each connected to one of the two reference-HTML-derived email fill formats, with Step 3 owning the fill-format
choice and honest preview/send semantics.
Status: submitted for Owner review — **local REAL-backend browser verification PASS** (`was_stubbed=false`).
Scope: Frontend/product-flow alignment + thin contract usage. NO renderer / email-provider / send-behavior change.
No real email sent.
Source dependencies: `frontend/cuistance_trial.html` (+ `docs/cuistance_trial.html` mirror); existing v1 endpoints;
`docs/poster2/cuistance_commercial_trial_reference_email_html_extraction_v1.md` (PR-3R grammar).
Owner gate: Owner review; remote browser validation with OPS auth (deploy + creds gated).

Task: `POSTER2-CUISTANCE-V1-DUAL-BODY-MODE-AND-EMAIL-FILL-FORMAT-ALIGNMENT`.

---

## 1. Product model (corrected)

Two EQUAL official body visual modes — neither is a fallback/degraded/backup/failure path:
- **affiche = 目标海报模式 / Affiche promotionnelle** — visual campaign poster (`email_campaign_composite_v1`,
  chromium). Higher visual ceiling; for campaigns / new launches.
- **fiche = 简单产品页模式 / Fiche produit simple** — stable HTML-composed product page
  (`template_product_sheet_v1`). Default for product-introduction emails; more deterministic/controllable.

Two email fill formats (Step 3), default-mapped from the selected body visual:
- **campaign_poster_email = 目标海报邮件格式** (ttt2.html / Technitalia-Zoho grammar) — default for affiche.
- **product_sheet_email = 简单产品页邮件格式** (ttt.html / Cuistance-Mailchimp grammar) — default for fiche.

Default mapping: affiche → campaign_poster_email; fiche → product_sheet_email. Operator may switch the format and
re-preview. The selected/inferred format + body visual are shown in Step 3 (`邮件主体：… / 邮件格式：…`) and recorded
in diagnostics; the backend assembly remains the single deterministic email package wrapping the selected body
visual's `final_poster.url` (backend unchanged).

## 2. Fixes (frontend wiring — backend unchanged)

1. **Step 1 simplified.** Product info / description / structured params / product images / gallery / atmosphere /
   logo remain. The Step-1 banner-format chooser was removed; logo+banner are relabeled `品牌素材（用于后续邮件页眉）`
   (the banner format decision now lives in Step 3). Right side keeps the asset-readiness checklist (no fake poster).
2. **Step 2 = dual equal modes.** Reframed to `生成邮件主体 · 选择展示模式` with two equal first-class cards
   (目标海报模式 / 简单产品页模式), each with its own 生成 / 重新生成 / 查看大图 / 复制图片链接 / 选为邮件主体. Both badged
   `正式模式`. Fiche failure shows a mode-specific amber `简单产品页模式暂不可用，可先使用目标海报模式继续。` (and the symmetric
   message for affiche) — never a global failure, never a fallback. Affiche keeps working independently.
3. **Real generated-image binding for both modes.** Each ready candidate → `GET /api/v2/posters/{poster_key}` →
   bind `final_poster.url` into its card; missing url → `已生成记录不完整，请查看内部诊断`. Main UI shows business
   labels only (已生成 / 使用后端生成结果 / 查看大图 / 复制图片链接); poster_key/url/template_id stay in diagnostics.
4. **Selected state from backend GET.** `选为邮件主体` → PATCH `selected-visual` → immediate GET → only when
   `selected_email_body_visual` equals the clicked mode show `已选为邮件主体` + unlock Step 3; else
   `选择邮件主体失败，请重试` and no unlock.
5. **Step 3 owns email fill format.** Adds a `邮件填充格式` selector (目标海报邮件格式 / 简单产品页邮件格式) default-mapped
   from the selected body visual; Step 3 shows `邮件主体：…` and `邮件格式：…`. Banner/header config stays in Step 3 and
   is email-layer (never product truth; never blocks generation; never dominates Step 2).
6. **Preview backend-rendered or labeled.** Pre-preview: `预览示意，尚未生成邮件预览`. On `POST /email/preview` 200:
   render assembled backend HTML, label `邮件预览已生成`; diagnostics record selected_email_body_visual,
   selected_email_fill_format, body_visual_poster_key, layout_type, final_poster_url_present, preview_status,
   assembled_html_from_backend.
7. **Email assembly relationship.** Email Package = fill format + banner/header + selected body visual
   `final_poster.url` + intro/body + CTA + footer/contact/legal (deterministic; backend unchanged).
8. **Send semantics.** A real delivery REQUIRES `provider_message_id`. `inline_only`/`preview_only`/`skipped` →
   `当前环境未配置真实发送服务，已记录预览发送证据，未真实投递`; never `发送成功/真实发送成功/已发送`.

No forbidden engineering terms on the default visible UI (diagnostics-only).

## 3. HTML Reference Fill Format Alignment

1. **ttt.html → product_sheet_email / 简单产品页邮件格式** (Cuistance-Mailchimp product-style).
2. **ttt2.html → campaign_poster_email / 目标海报邮件格式** (Technitalia-Zoho campaign-style).
3. These are **email fill formats** used AFTER poster/body-visual generation and BEFORE send.
4. They are **not** raw HTML copied wholesale.
5. Third-party tracking / scripts / `list-manage` / Zoho / Mailchimp pixels must **not** be copied.
6. Only **structure/grammar** is used: 600px container; header/banner; red divider; product/body visual;
   description/spec/CTA; footer/contact/social/legal.
7. The EmailBodyPlan (`layout_type`) records the assembly; the UI records the selected fill format in diagnostics.
8. Operator UI exposes **business names** (目标海报邮件格式 / 简单产品页邮件格式), not internal keys.

Advisory check: `scripts/check_email_fill_format_alignment.py` warns (non-blocking) if the reference doc / this
status doc is missing, if Step-3 UI omits either format name, or if the ttt/ttt2 mapping is not documented. It does
NOT block unrelated legacy docs.

## 4. Files changed

- `frontend/cuistance_trial.html` — Step 1 relabel + banner-chooser removed; Step 2 dual equal mode cards
  (mode-generic `setModeCard`/`loadModePoster`/`genVisual`); fiche fixed to backend `fiche` candidate type (was the
  invalid `sheet`); Step 3 fill-format selector + binding labels; preview diagnostics. `docs/cuistance_trial.html`
  mirror.
- `scripts/check_email_fill_format_alignment.py` — advisory HTML-reference alignment check.
- `scripts/poster2_cuistance_dual_body_mode_proof.py` — REAL-backend Playwright proof (no stubbing).
- **Backend: unchanged.**

## 5. REAL-backend browser verification (local, non-stubbed)

Real `app.main` backend; real page; Playwright NO route stubbing (real chromium affiche render; fiche image-gen
unavailable → mode-specific amber; inline provider → preview_only). Artifacts:
`docs/poster2/assets/cuistance_dual_body_mode_email_fill_format_alignment_v1/` (01–09 + evidence.json).

| # | File | Proves |
|---|------|--------|
| 01 | step1_simplified_product_assets_no_banner_confusion | Step 1 product/material only; no banner-format chooser. |
| 02 | step2_dual_body_modes | Two equal cards 目标海报模式 / 简单产品页模式 (both `正式模式`). |
| 03 | step2_affiche_generated_with_open_copy_actions | Real affiche bound + 查看大图/复制图片链接. |
| 04 | step2_fiche_generated_or_mode_specific_unavailable | Fiche mode-specific amber (not fallback), affiche unaffected. |
| 05 | step2_selected_body_visual_confirmed | Affiche selected (confirmed from backend GET). |
| 06 | step3_email_fill_format_selection | 邮件填充格式 selector; default-mapped. |
| 07 | step3_final_email_preview | Backend preview (200) `邮件预览已生成`, uses selected visual + format. |
| 08 | send_preview_only_semantics | mode=real/inline_only → preview-only, not real sent. |
| 09 | diagnostics_dual_mode_email_format_evidence | engineering fields in diagnostics only. |

Evidence JSON (`evidence.json`): `was_stubbed=false`; step1_has_banner_format_chooser=false; affiche+fiche cards
present (`正式模式`); affiche_status=ready / affiche_final_poster_url_present=true / open-action visible+poster href;
fiche_status=failed → `fiche_unavailable_shown=true` (`简单产品页模式暂不可用，可先使用目标海报模式继续。`);
selected_email_body_visual=affiche; selected_email_fill_format=campaign_poster_email; default_mapping_applied=true;
body/format labels `邮件主体：目标海报` / `邮件格式：目标海报邮件格式`; preview_status=200;
preview_uses_body_visual_poster_key=true; send_mode=real/send_provider=inline_only/send_status=skipped/
send_error_code=preview_only/provider_message_id_present=false/real_email_sent=false;
send_summary=`当前环境未配置真实发送服务，已记录预览发送证据，未真实投递`; ui_send_label_correct=true;
html_reference_alignment_checked=true; ttt_maps_to_product_sheet_email=true; ttt2_maps_to_campaign_poster_email=true.

Validation: `check_docs_router.py --all` PASS; `check_email_fill_format_alignment.py` PASS; inline JS `node --check`
OK; main-UI forbidden-term scan NONE; no user-facing "fallback/degraded" wording (only code comments). Backend
untouched → no backend tests run.

## 6. Remaining blockers / non-blockers

- Remote browser validation pending deploy + OPS creds (validation only; alignment proven on a real backend
  locally with `was_stubbed=false`).
- Fiche (`template_product_sheet_v1`) needs Vertex Imagen3; where image-gen is unconfigured it shows the
  mode-specific amber (equal-mode framing) and does not block affiche. Real send needs a provider + provider
  message id; until then the UI correctly reports preview-only.

## 7. Recommendation

**GO (affiche main route; fiche equal-mode with image-gen-gated availability)** on the real, non-stubbed local
verification; remote confirmation remains, gated on deploy + OPS creds.

STATUS: DUAL BODY MODE AND EMAIL FILL FORMAT ALIGNMENT SUBMITTED FOR OWNER REVIEW.
