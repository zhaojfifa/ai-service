# CUISTANCE v1 · 状态恢复 + Step2/Step3 一致性修复 v1

Purpose: Make the operator flow trial-ready — survive Command+R / hard refresh (P0), give Step 2 product context +
backend-driven preview state (P1), and finish Step 3 as the email assembly stage (P2). Frontend state recovery +
UX consistency only.
Status: submitted for Owner review — **local REAL-backend browser verification PASS** (`was_stubbed=false`).
Scope: Frontend only. NO backend API / renderer / email-provider / send-behavior change. No real email sent.
Source dependencies: `frontend/cuistance_trial.html` (+ `docs/cuistance_trial.html` mirror); existing v1 endpoints.
Owner gate: Owner review; remote browser validation with OPS auth (deploy + creds gated).

Task: `POSTER2-CUISTANCE-V1-STATE-RECOVERY-STEP2-SUMMARY-STEP3-CONSISTENCY-FIX`.

---

## 1. Fixes (frontend — backend unchanged)

**P0 — refresh/state recovery.** The workbench key is persisted to
`localStorage["cuistance_trial_last_workbench_key"]` on create/restore, and the current step to
`cuistance_trial_last_step`. On load, the boot step is captured before the first render, a recovery bar appears when
a last key exists, and once a connection is authenticated the page auto-calls `GET /api/v2/workbench/{key}` and
restores from backend truth: product_truth (name/reference/description), product_assets
(product_images/gallery/atmosphere), email_banner (logo/background/channel/campaign/selected_banner_ref),
poster_candidates (affiche/fiche), `selected_email_body_visual`, and the generated poster image via
`GET /api/v2/posters/{poster_key}`. It restores to a safe step (3 only if a visual is selected, else 2). Manual
affordances: `恢复上次工作台` button + `输入工作台编号继续` input. On failure:
`未能恢复上次工作台，请重新连接后端或重新开始` (raw detail in diagnostics only). State is never relied on from in-memory
JS alone.

**P1 — Step 2 product summary.** A compact `当前产品摘要` sits at the top of Step 2: `当前产品：{name} · {ref}`,
a key-parameter line, and `素材：产品图 N 张 · 画廊 N 张 · 氛围图…`, plus the selected mode and a `返回修改产品素材`
action — so the operator knows exactly what is being generated/regenerated.

**P1 — Step 2 preview state consistency.** Each mode's preview is driven by backend state: not generated →
`预览示意，尚未生成` (illustrative only); generating → `正在生成，请稍候` (generate buttons disabled); generated →
`已生成 / 使用后端生成结果` rendering `poster_record.final_poster.url` + 查看大图/复制图片链接; timeout → refresh +
bind a ready candidate if present, else keep the placeholder labeled not-generated. Placeholder and generated status
are never mixed.

**P1 — Step 2 selection consistency.** `选为邮件主体` → PATCH `selected-visual` → GET workbench → confirm
`selected_email_body_visual` → update card → unlock Step 3 → persist step+key. Failure → `选择邮件主体失败，请重试`
(no unlock).

**P2 — Step 3 email assembly stage.** Left: 邮件主体 (目标海报/简单产品页 · `已使用生成结果`) → 邮件填充格式 (目标海报邮件格式 /
简单产品页邮件格式, default-mapped from the selected body visual) → 邮件页眉/Banner (default `使用默认品牌页眉`; selected
option; email-layer only) → 邮件内容 (subject/intro/CTA) → 测试发送 → 发送证据. Right: one coherent 600px final
preview (header/banner + selected body visual + body copy + CTA + footer/contact/legal). Backend preview renders as
`邮件预览已生成`; pre-preview is `预览示意，尚未生成邮件预览`.

**P2 — preview & send semantics (unchanged, kept honest).** Backend-rendered preview is labeled distinctly from the
local illustrative preview. A real delivery REQUIRES a `provider_message_id`; `inline_only`/`preview_only`/`skipped`
→ `当前环境未配置真实发送服务，已记录预览发送证据，未真实投递`; never `发送成功/真实发送成功/已发送`.

No forbidden engineering terms on the default visible UI; no user-facing fallback/degraded wording.

## 2. Files changed

- `frontend/cuistance_trial.html` — recovery bar; localStorage key+step persistence; `restoreWorkbench()` /
  `maybeRestore()` / boot-step capture; Step-2 `当前产品摘要` (`updateS2Summary`); `generating` preview state +
  generate-button disable; `返回修改产品素材`. `docs/cuistance_trial.html` mirror.
- `scripts/poster2_cuistance_state_recovery_proof.py` — REAL-backend Playwright proof incl. two hard refreshes.
- **Backend: unchanged.**

## 3. REAL-backend browser verification (local, non-stubbed)

Real `app.main` backend; real page; Playwright NO route stubbing; two hard `page.reload()`s. Artifacts:
`docs/poster2/assets/cuistance_state_recovery_step2_step3_consistency_v1/` (01–09 + evidence.json).

| # | File | Proves |
|---|------|--------|
| 01 | step2_product_summary | `当前产品摘要` (name/ref/params/asset counts). |
| 02 | step2_generated_poster_before_refresh | Real affiche bound before refresh. |
| 03 | after_refresh_recovered_workbench | `已恢复上次工作台`; same workbench restored after Command+R. |
| 04 | step2_generated_poster_after_refresh | Generated affiche image rebound after refresh. |
| 05 | step2_selected_body_visual | Affiche selected (backend GET confirmed). |
| 06 | step3_email_assembly_stage | Step 3 = 邮件主体 + 填充格式 + 页眉/Banner + 内容 + 发送. |
| 07 | step3_final_email_preview | Coherent backend preview (header + body visual + copy + CTA + footer). |
| 08 | send_preview_only_semantics_if_run | mode=real/inline_only → preview-only, not real sent. |
| 09 | diagnostics_recovery_evidence | recovery + engineering fields in diagnostics only. |

Evidence JSON (`evidence.json`): `was_stubbed=false`; localStorage_key_present=true; initial_workbench_key ==
recovered_workbench_key → recovered_after_refresh=true; product_truth_restored=true; assets_restored=true;
affiche_status=ready; affiche_final_poster_url_present_before_refresh=true & _after_refresh=true;
on_step2_after_refresh=true; selected_email_body_visual=affiche; step3_unlocked=true; step3_has_fill_format=true;
step3_has_banner=true; preview_status=200; preview_uses_body_visual_poster_key=true; final_preview_rendered=true;
selected_state_restored_after_refresh=true; step3_active_after_2nd_refresh=true; send_mode=real/
send_provider=inline_only/send_status=skipped/send_error_code=preview_only/provider_message_id_present=false/
real_email_sent=false; ui_send_label_correct=true.
s2 summary text: `当前产品：Friteuse électrique double · EF132V | 素材：产品图 2 张 · 画廊 1 张 · 无氛围图`.

Validation: `check_docs_router.py --all` PASS; `check_email_fill_format_alignment.py` PASS; inline JS `node --check`
OK; main-UI forbidden-term + fallback scan NONE. Backend untouched → no backend tests run.

## 4. Remaining blockers / non-blockers

- Remote browser validation pending deploy + OPS creds (validation only; recovery proven on a real backend locally
  with `was_stubbed=false`). Note: on remote, auto-restore runs after OPS login (the recovery bar + `恢复上次工作台`
  let the operator trigger it post-login); locally OPS auth is inactive so restore is automatic.
- Fiche real generation needs Vertex Imagen3 (official-mode amber otherwise); real send needs a provider +
  provider_message_id.

## 5. Recommendation

**GO** — Command+R restores the workbench, product summary, generated poster, selection, and step; Step 2 preview
states are backend-driven; Step 3 is a coherent email assembly stage; send semantics honest. Remote confirmation
remains, gated on deploy + OPS creds.

STATUS: STATE RECOVERY STEP2 STEP3 CONSISTENCY SUBMITTED FOR OWNER REVIEW.
