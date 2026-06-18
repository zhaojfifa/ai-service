# CUISTANCE v1 · 操作台候选选择 & 预览状态修复 v1

Purpose: Fix the operator-UI state machine so Step 1 shows asset readiness (not a fake poster), Step 2 clearly
surfaces the backend-generated ready product-poster candidate, selection persists `selected_email_body_visual`,
and Step 3 unlocks — proven by browser screenshots.
Status: submitted for Owner review — **local browser verification PASS (affiche main route)**.
Scope: Frontend-only state/contract fix. NO backend API / renderer / send-behavior change. No real email sent.
Source dependencies: `frontend/cuistance_trial.html` (+ `docs/cuistance_trial.html` mirror); existing v1 workbench
endpoints (`/api/v2/workbench*`, `/candidates/{affiche|fiche}/generate`, `/selected-visual`, `/email/preview`).
Owner gate: Owner review; remote browser validation with OPS auth (deploy + creds gated).
Next action: deploy the trial branch to the remote, then repeat the browser flow with operator OPS login.

Task: `POSTER2-CUISTANCE-V1-UI-CANDIDATE-SELECTION-AND-PREVIEW-STATE-FIX-WITH-SCREENSHOT-VERIFY`.

---

## 1. Root cause (confirmed)

Owner-observed backend state: `workbench_key=wb_af43f59a05944611`, `poster_candidates.affiche.status=ready`,
`poster_key=p2_2b0c5b002c59455d`, `render_engine_used=chromium`, `degraded=false`, `structure_complete=true`,
yet `selected_email_body_visual=null` and Step 3 locked.

- **Primary cause — timeout leaves UI blind to a ready candidate.** Candidate generation can return a gateway
  **504** even though the backend completes the candidate (`status=ready`). The old 504 branch returned without
  re-reading backend state, so the in-memory candidate key stayed `null`. The «选为邮件主体» handler refused to
  PATCH when the in-memory key was null → selection never persisted → `selected_email_body_visual` stayed null →
  Step 3 never unlocked. This is exactly the Owner-observed pattern.
- **Secondary cause — Step 1 preview was a fake assembled poster.** The right panel rendered a static poster
  mockup, implying the final poster already existed, instead of showing business-level asset readiness.
- **Tertiary — Step 2 did not clearly mark the backend-generated ready candidate** on the card itself (only a
  side hint changed), so the operator could not tell the ready affiche apart from the static mockup.

Backend generation was NOT the blocker (it had already produced a ready affiche). The frontend failed to (1) show
readiness, (2) recover/display the ready candidate after a timeout, (3) persist the selection, (4) unlock Step 3.

## 2. Fix (frontend-only)

- **Step 1 = asset readiness panel (not a poster).** Replaced the static right-side mockup with a dynamic
  `素材就绪检查` checklist driven by the in-card slot state: 产品主图（已就绪/缺失，必需）、第二产品图（已就绪/可选）、
  画廊图（N/3 计数）、氛围/场景图（视觉素材，可选）、邮件 Logo（已就绪/缺失）、邮件横幅（已就绪/可选）。A hint states
  it is a readiness check, not the final poster. Upload/change controls stay **inside each visual card** (8 slots).
- **Step 2 candidate clarity.** The 产品海报 card now shows an in-card backend-ready badge: `尚未生成` → after a
  ready candidate is found, `产品海报已生成` + `使用后端生成结果，可直接「选为邮件主体」`. On selection the button
  relabels to `已选为邮件主体` and the card shows the `✓ 已选用` badge + selected highlight.
- **Selection recovers backend truth.** «选为邮件主体» now calls `refreshState()` first when no in-memory key
  exists, so a backend-ready candidate (e.g. produced during a timeout) becomes selectable; then PATCH
  `selected-visual` → GET confirm `selected_email_body_visual` → `applySelectVisual` → unlock Step 3.
- **Timeout no longer confuses the UI.** On 504/502 the UI shows `生成超时，可继续使用已生成版本或稍后重试` AND calls
  `refreshState()` to pick up the backend-completed ready candidate (it is never erased).
- **Step 3 unlock rule.** Unlocked when a visual is selected and its candidate is ready with a poster_key; not
  gated on fiche success, R2 upload, real provider, or optional gallery/atmosphere assets.

No forbidden engineering terms on the default visible UI (poster_key / workbench_key / template_id / payload /
renderer / inline_only / send_attempts / EmailBodyPlan / provider_message_id / Vertex appear only inside the
collapsed 内部诊断 / 工程证据 drawer).

## 3. Files changed

- `frontend/cuistance_trial.html` — Step 1 readiness panel, Step 2 affiche-card ready/selected status, readiness
  renderer, selection refresh-first, 504 recovery; small CSS for readiness badges. **Backend unchanged.**
- `docs/cuistance_trial.html` — identical mirror (kept in sync).
- `scripts/poster2_cuistance_ui_candidate_selection_proof.py` — Playwright proof: serves the real page, stubs the
  existing v1 endpoints to reproduce the Owner-observed state (ready affiche, selection null, generation 504),
  drives the flow, asserts state, and captures screenshots.

## 4. Browser screenshot verification (local)

Artifacts: `docs/poster2/assets/cuistance_ui_candidate_selection_state_fix_v1/`

| # | File | Proves |
|---|------|--------|
| 1 | `01_step1_asset_readiness.png` | **Step 1 preview correctness** — right panel is an asset-readiness checklist (prod1 已就绪 / prod2 已就绪 / 画廊 1/3 张 / 氛围 视觉素材,可选 / Logo 已就绪 / 横幅 已就绪), not a fake assembled poster; upload controls inside the cards. |
| 2 | `02_step2_before_select.png` | **Candidate ready state** — 产品海报 card shows `产品海报已生成` with «选为邮件主体»; no forced regeneration. |
| 2b | `02b_step2_timeout_retained.png` | Regeneration 504 shows `生成超时，可继续使用已生成版本或稍后重试` while the ready candidate is retained (`产品海报已生成`). |
| 3 | `03_step2_after_select.png` | **Selected state** — card shows `产品海报已生成` + `✓ 已选用`, button reads `已选为邮件主体`, bottom continue enabled, business language only. |
| 4 | `04_step3_email_preview.png` | **Step 3 unlock** — 邮件预览与测试发送 active, email preview rendered (banner + selected poster body + CTA + footer/legal). |
| 5 | `05_diagnostics_evidence.png` | Engineering evidence (workbench_key / poster_key / selected=affiche) appears only in the collapsed diagnostics drawer. |

Asserted evidence (`evidence.json`):
- readiness rows: prod1 `已就绪`, prod2 `已就绪`, gallery `1 / 3 张`, atmo `视觉素材，可选`, logo `已就绪`, banner `已就绪`.
- affiche card badge: `产品海报已生成`.
- after regen 504: flash `生成超时，可继续使用已生成版本或稍后重试`, badge still `产品海报已生成`.
- **`selected_email_body_visual` after PATCH = `affiche`**.
- next button disabled after select = `false` (**Step 3 unlocked**); select button label = `已选为邮件主体`.
- Step 3 active = `true`; preview format `single_product_promo`, width 600; `邮件预览已生成`.
- diagnostics dump carries workbench_key `wb_af43f59a05944611`, poster_key `p2_2b0c5b002c59455d`, selected `affiche`.

Validation tooling: `python3 scripts/check_docs_router.py --all` → **PASS** (warnings legacy/advisory). Inline JS
`node --check` → OK. Visible-UI forbidden-term scan → NONE.

## 5. Remote validation

- Requires the trial branch to be deployed to `https://ai-service-leob.onrender.com/cuistance_trial.html` (remote
  deploy lags pushes per prior logs) and operator OPS login (no creds held in this pass — not claiming remote GO).
- After deploy, repeat the browser flow with OPS login using the Owner-observed pattern: a ready affiche exists
  with `selected_email_body_visual=null` → selection alone unlocks Step 3 without regenerating.

## 6. Remaining blockers / non-blockers

- Remote browser validation pending deploy + OPS creds (validation only).
- Resume-by-`workbench_key` after a full page reload is out of scope (the recovery here covers in-session timeout).
- fiche needs image-gen; real send needs a provider; remote upload needs R2 — all allowed non-blockers for the
  affiche main route (use 使用示例素材).

STATUS: UI CANDIDATE SELECTION AND PREVIEW STATE FIX SUBMITTED FOR OWNER REVIEW.
