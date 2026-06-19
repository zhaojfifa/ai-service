# CUISTANCE v1 · Step2/Step3 布局与预览一致性修复 v1

Purpose: Make the operator UI usable for ordinary trial — rework Step 2 into a balanced dual-mode workspace
(segmented tabs + active-mode controls + prominent preview), keep Step 3 owning banner/header + fill format with a
coherent final email preview, and keep send semantics honest. Frontend UX/layout + preview-consistency only.
Status: submitted for Owner review — **local REAL-backend browser verification PASS** (`was_stubbed=false`).
Scope: Frontend only. NO backend business logic / renderer / email-provider / send-behavior change. No real email.
Source dependencies: `frontend/cuistance_trial.html` (+ `docs/cuistance_trial.html` mirror); existing v1 endpoints.
Owner gate: Owner review; remote browser validation with OPS auth (deploy + creds gated).

Task: `POSTER2-CUISTANCE-V1-STEP2-STEP3-LAYOUT-AND-PREVIEW-CONSISTENCY-FIX`.

---

## 1. Fixes (frontend UX/layout — backend unchanged)

1. **Step 1 unchanged/simplified.** Product info / description / structured params / images / gallery / atmosphere /
   logo + asset-readiness checklist retained. No banner-format decision in Step 1 (`step1_has_banner_format_chooser
   =false`). Only vestigial unused Step-2 title/accroche inputs were dropped (not Step 1).
2. **Step 2 = balanced dual-mode tab workspace.** Replaced the awkward "empty-left + stacked-right previews" with a
   **segmented control** (`目标海报模式 / 简单产品页模式`) on top; the active mode's **controls** (description, status
   badge, generate/regen, 查看大图 / 复制图片链接, 选为邮件主体) fill the left column and its **preview** shows
   prominently on the right. Tabs carry a status dot (✓ generated / • unavailable). Generating or selecting a mode
   switches to its tab.
3. **Step 2 mode semantics.** Affiche: `目标海报模式` · `视觉营销 · 活动推广`; on ready → `产品海报已生成` +
   `使用后端生成结果` + 查看大图/复制图片链接/选为邮件主体. Fiche: `简单产品页模式` · `稳定产品展示 · 默认产品介绍`; on ready →
   `简单产品页已生成` + same actions; if unavailable →
   `简单产品页模式暂不可用，当前环境缺少图像生成配置；可先使用目标海报模式继续。` Fiche is an EQUAL official mode — never
   fallback/degraded/backup/failure path, and its unavailability never blocks affiche.
4. **Step 2 selection (backend-confirmed).** `选为邮件主体` → PATCH `selected-visual` → GET workbench → only when
   `selected_email_body_visual` equals the clicked mode show `已选为邮件主体` + unlock Step 3. Bottom continue button
   reads `进入邮件预览与测试发送 ▶`; when nothing selected → `请先选择邮件主体`.
5. **Step 3 layout.** Left column = 邮件填充格式 · 邮件页眉/Banner 模块 · 邮件内容 · 测试发送 · 发送证据; right column =
   邮件最终预览 (one coherent 600px email frame: header/banner + selected body visual + body copy + CTA + footer). The
   body visual is the main content; the banner/header supports it.
6. **Banner/header consistency.** Banner/header lives in Step 3 only as an email-layer module (options + selected
   state, applied in the final preview; default `使用默认品牌页眉`). Not in Step 1; not product truth; not a product
   image.
7. **Preview credibility.** Pre-preview: `预览示意，尚未生成邮件预览`; on `POST /email/preview` 200 → render the
   backend assembled HTML and label `邮件预览已生成`. Diagnostics record selected_email_body_visual,
   selected/inferred fill format, body_visual_poster_key, preview_status, preview_uses_body_visual_poster_key,
   real_email_sent.
8. **Send semantics (strict).** A real delivery REQUIRES a `provider_message_id`. `inline_only`/`preview_only`/
   `skipped` → `当前环境未配置真实发送服务，已记录预览发送证据，未真实投递`; never `发送成功/真实发送成功/已发送`.

No forbidden engineering terms on the default visible UI; no user-facing fallback/degraded wording.

## 2. Files changed

- `frontend/cuistance_trial.html` — Step 2 segmented-tab layout (controls/preview split, `switchMode`, tab status
  dots, mode-specific ready badges, fiche unavailable wording with `当前环境缺少图像生成配置`); Step-2 continue label;
  CSS for `.mode-tabs/.mode-tab/.mode-pv`. `docs/cuistance_trial.html` mirror.
- `scripts/poster2_cuistance_step2_step3_layout_proof.py` — REAL-backend Playwright proof (no stubbing).
- **Backend: unchanged.**

## 3. REAL-backend browser verification (local, non-stubbed)

Real `app.main` backend; real page; Playwright NO route stubbing (real chromium affiche render; fiche image-gen
unavailable → official-mode amber; inline provider → preview_only). Artifacts:
`docs/poster2/assets/cuistance_step2_step3_layout_preview_consistency_v1/` (01–09 + evidence.json).

| # | File | Proves |
|---|------|--------|
| 01 | step1_still_simplified | Step 1 simplified; no banner-format chooser. |
| 02 | step2_dual_mode_balanced_layout | Segmented tabs + active controls (left) + prominent preview (right). |
| 03 | step2_affiche_generated_openable | Real affiche `产品海报已生成`, 查看大图/复制图片链接. |
| 04 | step2_fiche_mode_status | Fiche official-mode amber (`…当前环境缺少图像生成配置…`), not fallback, affiche unaffected. |
| 05 | step2_selected_body_visual | Affiche selected (backend GET confirmed); continue = `进入邮件预览与测试发送`. |
| 06 | step3_email_format_and_banner_controls | Step 3 owns 邮件填充格式 + banner/header controls. |
| 07 | step3_final_email_preview_coherent | Coherent backend preview: banner + body visual + copy + CTA + footer. |
| 08 | send_preview_only_label | mode=real/inline_only → preview-only, not real sent. |
| 09 | diagnostics_layout_preview_evidence | engineering fields in diagnostics only. |

Evidence JSON (`evidence.json`): `was_stubbed=false`; step2_has_mode_tabs=true; affiche_controls_visible=true;
affiche_preview_visible=true; affiche_status=ready / affiche_final_poster_url_present=true /
affiche_open_action_visible=true; fiche_status=failed → `fiche_unavailable_shown=true`
(`简单产品页模式暂不可用，当前环境缺少图像生成配置；可先使用目标海报模式继续。`); fiche_official_mode_present=true;
fiche_not_labeled_fallback=true; selected_email_body_visual=affiche; continue_btn_label=`进入邮件预览与测试发送 ▶`;
step3_banner_controls_present=true; step3_fill_format_present=true;
selected_or_inferred_email_fill_format=campaign_poster_email; preview_status=200;
preview_uses_body_visual_poster_key=true; final_preview_rendered=true; preview_badge=`邮件预览已生成`;
send_mode=real/send_provider=inline_only/send_status=skipped/send_error_code=preview_only/
provider_message_id_present=false/real_email_sent=false;
send_summary=`当前环境未配置真实发送服务，已记录预览发送证据，未真实投递`; ui_send_label_correct=true.

Validation: `check_docs_router.py --all` PASS; `check_email_fill_format_alignment.py` PASS; inline JS `node --check`
OK; main-UI forbidden-term scan NONE; no user-facing fallback/degraded wording. Backend untouched → no backend
tests run.

## 4. Remaining blockers / non-blockers

- Remote browser validation pending deploy + OPS creds (validation only; the layout/preview fix is proven on a real
  backend locally with `was_stubbed=false`).
- Fiche real generation needs Vertex Imagen3 — where unconfigured it shows the official-mode amber and does not
  block affiche. Real send needs a provider + provider_message_id; until then preview-only is correctly reported.

## 5. Recommendation

**GO** — Step 1 simplified; Step 2 balanced dual-mode tab workspace; Affiche/Fiche equal official modes (fiche not
demoted to fallback); Step 3 owns banner/header with a coherent final email preview; send semantics honest. Remote
confirmation remains, gated on deploy + OPS creds.

STATUS: STEP2 STEP3 LAYOUT PREVIEW CONSISTENCY SUBMITTED FOR OWNER REVIEW.
