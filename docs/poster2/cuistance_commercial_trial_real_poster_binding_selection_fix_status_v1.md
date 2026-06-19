# CUISTANCE v1 · 真实海报绑定 & 选择修复 v1

Purpose: Make Step 2 display the REAL backend-generated poster (poster_record.final_poster.url via
`GET /api/v2/posters/{poster_key}`) instead of a static mock, persist `selected_email_body_visual=affiche`, and
unlock Step 3 — proven against a REAL (non-stubbed) backend with screenshots + evidence.json.
Status: submitted for Owner review — **local REAL-backend browser verification PASS** (`was_stubbed=false`).
Scope: Frontend/backend-contract wiring fix. NO backend API / renderer / send-behavior change. No real email sent.
Source dependencies: `frontend/cuistance_trial.html` (+ `docs/cuistance_trial.html` mirror); existing v1 endpoints
`GET /api/v2/posters/{poster_key}`, `/api/v2/workbench*`, `/candidates/{affiche|fiche}/generate`,
`/selected-visual`, `/email/preview`.
Owner gate: Owner review; remote browser validation with OPS auth (deploy + creds gated).
Next action: deploy the trial branch to remote, then repeat the flow with operator OPS login.

Task: `POSTER2-CUISTANCE-V1-REAL-POSTER-BINDING-AND-SELECTION-FIX`.

---

## 1. Root cause (confirmed)

Owner-observed state (`wb_fafd04a9d0264ad1`: affiche `status=ready`, `poster_key=p2_feb400a9f22f4d36`,
`template_id=email_campaign_composite_v1`, `render_engine_used=chromium`, `degraded=false`,
`structure_complete=true`, `selected_email_body_visual=null`): the backend generated a **real** product poster, but
the Step-2 card still rendered a **static/mock** `.poster`. The UI never called `GET /api/v2/posters/{poster_key}`
and never displayed `poster_record.final_poster.url`. Because the real poster was never loaded/verified, the
selection step did not persist `selected_email_body_visual` and Step 3 stayed locked.

## 2. Fix (frontend wiring — backend unchanged)

- **Real poster binding.** When Step 2 receives/refreshes workbench state and finds `affiche.status==ready` +
  `poster_key`, the UI now calls `GET /api/v2/posters/{poster_key}`, reads `final_poster.url` (falls back to
  `render_result.final_url`), and renders it as an `<img id="affiche-real">` in the 产品海报 card — labeled
  `产品海报已生成` / `使用后端生成结果`. The static `.poster` mock is hidden when the real poster is bound.
- **Static mock is never "generated".** Before generation the mock is labeled `预览示意，尚未生成` (badge `尚未生成`);
  it is only a placeholder and is never labeled `产品海报已生成`.
- **Incomplete record guard.** If `final_poster.url` is missing, the card shows `已生成记录不完整，请查看内部诊断`
  (raw detail only in diagnostics) and selection is blocked.
- **Generate button.** `生成产品海报` → POST generate → on success bind the real poster via `GET /posters/...`. On
  **504/502** it refreshes workbench state, fetches+binds a ready candidate if present, and shows
  `生成超时，但已找到可用生成结果，可继续选择` (or `生成超时，可继续使用已生成版本或稍后重试` if none) — a usable ready
  candidate is never erased.
- **Selection gate.** `选为邮件主体` is allowed only once the real poster (`final_poster.url`) is loaded/verified;
  it PATCHes `selected-visual` → GET confirm `selected_email_body_visual==affiche` → card `已选为邮件主体` →
  continue enabled → Step 3. On failure: `选择邮件主体失败，请重试` (raw detail in diagnostics only).
- **Step 3 unlock.** Unlocked when a visual is selected, its candidate is ready, and it has a poster_key; NOT gated
  on fiche success / R2 upload / real send provider / gallery / atmosphere.
- **Backend connection placement.** The connection/auth state (`未连接 / 已连接 / 连接失败`, 401 → `请先连接后端`) stays
  near the top of the workbench content as a slim bar within the page (not a separate root admin console); raw auth
  detail stays in diagnostics.

No forbidden engineering terms on the default visible UI (poster_key / workbench_key / final_poster_url /
template_id / payload / renderer / inline_only / send_attempts / EmailBodyPlan / provider_message_id / Vertex /
R2 / API appear only inside the collapsed 内部诊断 / 工程证据 drawer).

## 3. Files changed

- `frontend/cuistance_trial.html` — real poster binding (`setAfficheCard` / `loadAffichePoster`), generate/504
  recovery binding, selection gated on `final_poster.url`, placeholder labeling, Step-3 image coherence; small CSS.
- `docs/cuistance_trial.html` — identical mirror.
- `scripts/poster2_cuistance_real_poster_binding_proof.py` — REAL-backend Playwright proof (no route stubbing).
- **Backend: unchanged** (no API contract / renderer / send change; no backend bug found).

## 4. REAL-backend browser verification (local, non-stubbed)

A real `app.main` backend (OPS auth inactive locally; R2 not configured → `final_poster.url` is a real
`data:image/png;base64` of the actual chromium composite render) served the real page; Playwright drove it with NO
stubbed endpoints. Artifacts: `docs/poster2/assets/cuistance_real_poster_binding_selection_fix_v1/`.

| # | File | Proves |
|---|------|--------|
| 1 | `01_step2_before_generation_placeholder_labeled.png` | Static card labeled `预览示意，尚未生成` (badge `尚未生成`) — not "generated". |
| 2 | `02_step2_real_backend_poster_loaded.png` | **Real backend poster** (`email_campaign_composite_v1`, chromium) bound into the card; mock hidden; badge `产品海报已生成`. |
| 3 | `03_step2_selected_backend_poster.png` | Selected: button `已选为邮件主体`, card highlighted, continue enabled. |
| 4 | `04_step3_email_preview_with_backend_poster.png` | Step 3 preview (HTTP 200) renders the assembled email with the selected generated poster. |
| 5 | `05_diagnostics_real_poster_binding_evidence.png` | poster_key / workbench_key / final_poster binding evidence in the collapsed diagnostics drawer only. |

Evidence JSON: `docs/poster2/assets/cuistance_real_poster_binding_selection_fix_v1/evidence.json`
- `was_stubbed`: **false**
- `generate_http_status`: 200 · `affiche_status`: ready · `poster_key`: present · `template_id`:
  email_campaign_composite_v1
- `poster_record_loaded`: true · `final_poster_url_present`: true · `final_poster_url_origin`:
  poster_record.final_poster.url (data:image/png;base64, len≈720k) · 1240×1754
- `render_engine_used`: chromium · `degraded`: false · `structure_complete`: true
- **`ui_image_bound_to_final_poster`: true** (the Step-2 card `<img>` src equals poster_record.final_poster.url)
- `selected_email_body_visual`: **affiche** · `step3_unlocked`: true · `preview_status`: 200
- main-UI forbidden-term scan: NONE; inline JS `node --check`: OK; `check_docs_router.py --all`: PASS.

## 5. Remote validation

- Requires the trial branch to be deployed to `https://ai-service-leob.onrender.com/cuistance_trial.html` and
  operator OPS login (no creds held this pass). Per prior logs the remote deploy lags pushes; not claiming remote
  GO here. After deploy, repeat: 使用示例素材 → save → 生成产品海报 → confirm the card shows the backend
  final_poster.url → 选为邮件主体 → `selected_email_body_visual=affiche` → Step 3 → preview.

## 6. Remaining blockers / non-blockers

- Remote browser validation pending deploy + OPS creds (validation only; the code fix is proven against a real
  backend locally with `was_stubbed=false`).
- fiche needs image-gen; real send needs a provider; remote upload needs R2 — allowed non-blockers for the affiche
  route (use 使用示例素材).

## 7. Recommendation

**GO (affiche main route)** for the real-poster-binding + selection fix on the basis of the real, non-stubbed local
verification; remote confirmation against the deployed page remains, gated on deploy + OPS creds.

STATUS: REAL POSTER BINDING AND SELECTION FIX SUBMITTED FOR OWNER REVIEW.
