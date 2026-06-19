# CUISTANCE v1 · 邮件预览/发送语义校准 v1

Purpose: Make email preview + send semantics trustworthy — explicit email-banner selection, generated-poster
view/copy actions, Step-3 preview rendered from the backend `email/preview` and clearly bound to the selected
generated poster, and HONEST send semantics (inline_only/preview_only must never read as a real send).
Status: submitted for Owner review — **local REAL-backend browser verification PASS** (`was_stubbed=false`).
Scope: Frontend/backend-contract alignment. NO renderer / email-provider / send-behavior change. No real email sent.
Source dependencies: `frontend/cuistance_trial.html` (+ `docs/cuistance_trial.html` mirror); existing v1 endpoints
`/api/v2/workbench*`, `/posters/{poster_key}`, `/email/preview`, `/email/send`.
Owner gate: Owner review; remote browser validation with OPS auth (deploy + creds gated).
Next action: deploy the trial branch to remote, then repeat with operator OPS login.

Task: `POSTER2-CUISTANCE-V1-EMAIL-PREVIEW-SEND-SEMANTICS-CALIBRATION`.

---

## 1. Fixes (frontend wiring — backend unchanged)

1. **Explicit email-banner selection (Step 1).** Added Option 1 / Option 2 banner choices in Step 1 under
   「邮件横幅选择（页眉，非产品真值）」. Selecting an option sets `email_banner.background.url` (absolute) +
   `email_banner.selected_banner_ref` (persisted via the Step-1 save PATCH); the Step-3 Email Banner Module uses the
   selected banner. No selection → `未选择则使用默认品牌页眉`. Banner is email-layer material — never product truth,
   never baked into the poster body. Step-3 banner options re-persist via PATCH when changed.
2. **Generated-poster URL actions (Step 2).** Once the real poster is bound, the card shows `查看生成大图` (opens
   `final_poster.url` in a new tab) and `复制图片链接` (copies `final_poster.url`). No poster_key on the main UI;
   poster_key + url live only in diagnostics.
3. **Email preview binding clarity (Step 3).** Before preview the panel is labeled `预览示意，尚未生成邮件预览`. When
   `POST /email/preview` returns 200 the assembled backend HTML is rendered and labeled `邮件预览已生成` +
   `邮件主体：产品海报 · 已使用生成海报`. Diagnostics record `selected_email_body_visual`, `body_visual_poster_key`,
   `layout_type`, `final_poster_url_present`.
4. **Selected-state consistency (Step 2).** `选为邮件主体` → PATCH `selected-visual` → immediate GET workbench →
   only when `selected_email_body_visual==affiche` show `已选为邮件主体` + unlock Step 3; otherwise
   `选择邮件主体失败，请重试` and Step 3 stays locked. Diagnostics reflect the confirmed backend state.
5. **Honest send semantics (Step 3).** A real delivery now REQUIRES a `provider_message_id`. When `mode=real` but the
   provider returns `inline_only` / `status=skipped` / `error_code=preview_only` / `provider_message_id=null`, the UI
   shows `当前环境未配置真实发送服务，已记录预览发送证据，未真实投递` and the state reads `预览已记录` — never
   `发送成功 / 真实发送成功 / 已发送`. Per-attempt labels distinguish `真实发送成功` (only with a provider_message_id) /
   `已跳过真实投递（预览已记录）` / `发送失败`. `真实发送成功` is shown only when a `provider_message_id` exists.

No forbidden engineering terms on the default visible UI (poster_key / workbench_key / final_poster_url /
template_id / payload / renderer / inline_only / send_attempts / EmailBodyPlan / provider_message_id / Vertex / R2 /
API appear only inside the collapsed 内部诊断 / 工程证据 drawer).

## 2. Files changed

- `frontend/cuistance_trial.html` — banner options + `selectBanner()`/`selected_banner_ref`; poster view/copy
  actions; preview binding labels + diagnostics; honest send semantics (`isRealSent`/`attemptLabel`/`renderResults`);
  small CSS. `docs/cuistance_trial.html` — identical mirror.
- `scripts/poster2_cuistance_email_preview_send_semantics_proof.py` — REAL-backend Playwright proof (no stubbing).
- **Backend: unchanged** (no API contract / renderer / provider / send change; no backend bug found).

## 3. REAL-backend browser verification (local, non-stubbed)

A real `app.main` backend served the real page; Playwright drove it with NO stubbed endpoints (real chromium
`email_campaign_composite_v1` render; R2 absent → `final_poster.url` is a real data-URL; inline provider →
`preview_only`). Artifacts: `docs/poster2/assets/cuistance_email_preview_send_semantics_v1/`.

| # | File | Proves |
|---|------|--------|
| 1 | `01_step1_banner_option_selected.png` | Explicit banner choice (Option 2) selected; `已选择邮件横幅（页眉）`. |
| 2 | `02_step2_generated_poster_with_open_link.png` | Real generated poster + `查看生成大图` / `复制图片链接` actions. |
| 3 | `03_step3_preview_uses_generated_poster.png` | Backend preview (200) labeled `邮件预览已生成` + `邮件主体：产品海报 · 已使用生成海报`. |
| 4 | `04_send_preview_only_not_real_sent.png` | Send (mode=real, inline_only) reads `当前环境未配置真实发送服务，已记录预览发送证据，未真实投递` — not a real send. |
| 5 | `05_diagnostics_email_preview_send_evidence.png` | selected_email_body_visual / body_visual_poster_key / layout_type / send evidence in diagnostics only. |

Evidence JSON: `docs/poster2/assets/cuistance_email_preview_send_semantics_v1/evidence.json`
- `was_stubbed`: **false**
- `selected_banner_ref`: option_2 · `banner_background_url_present`: true
- `poster_key`: present · `final_poster_url_present`: true · `ui_has_open_generated_image_action`: true
- `selected_email_body_visual_after_get`: **affiche**
- `email_preview_status`: 200 · `preview_uses_body_visual_poster_key`: **true** ·
  preview labels `邮件预览已生成` / `邮件主体：产品海报 · 已使用生成海报`
- `send_mode`: real · `send_provider`: inline_only · `provider_message_id_present`: false · `send_status`: skipped ·
  `send_error_code`: preview_only · **`real_email_sent`: false**
- `send_summary_text`: 当前环境未配置真实发送服务，已记录预览发送证据，未真实投递 · **`ui_send_label_correct`: true**
- main-UI forbidden-term scan: NONE; inline JS `node --check`: OK; `check_docs_router.py --all`: PASS.

## 4. Remote validation

- Requires the trial branch deployed to `https://ai-service-leob.onrender.com/cuistance_trial.html` + operator OPS
  login (no creds held this pass; not claiming remote GO). Per prior logs the remote deploy lags pushes. After
  deploy, repeat: OPS login → assets + select banner → save → generate poster → open large image → select →
  confirm `selected_email_body_visual=affiche` → Step 3 preview (uses generated poster) → internal-only send →
  confirm UI says preview evidence recorded / not real sent.

## 5. Remaining blockers / non-blockers

- Remote browser validation pending deploy + OPS creds (validation only; the calibration is proven against a real
  backend locally with `was_stubbed=false`).
- Real delivery needs a configured provider (Resend) + a `provider_message_id`; until then the UI correctly reports
  preview-only / not real sent. Remote upload needs R2; fiche needs image-gen — allowed non-blockers.

## 6. Recommendation

**GO (affiche main route)** for the email preview/send semantics calibration on the basis of the real, non-stubbed
local verification; remote confirmation remains, gated on deploy + OPS creds.

STATUS: EMAIL PREVIEW SEND SEMANTICS CALIBRATION SUBMITTED FOR OWNER REVIEW.
