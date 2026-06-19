# CUISTANCE v1 · 远程候选选择状态验证（b9f3df5）

Purpose: Remote browser validation that on the deployed `/cuistance_trial.html` a ready product-poster candidate can
be selected as the email body and Step 3 unlocks (verifying commit `b9f3df5` of the candidate-selection/state fix).
Status: **HOLD** — remote prerequisites not met at validation time (deploy not landed + no OPS credentials held).
Scope: Remote validation only. No backend/renderer/send/code change. No customer send. No secret stored.
Source dependencies: https://ai-service-leob.onrender.com/cuistance_trial.html ; v1 workbench endpoints (OPS-gated).
Owner gate: Owner to (1) confirm/complete the trial-branch deploy of b9f3df5+ and (2) provide OPS credentials.
Next action: re-run this verification once both prerequisites are met.

Task: `POSTER2-CUISTANCE-V1-REMOTE-CANDIDATE-SELECTION-STATE-VERIFY-B9F3DF5`.

---

## 1. Deploy state (checked 2026-06-19)

- Git: local trial HEAD = `b9f3df5`; **origin `trial/poster2-cuistance-v1-operator-trial` HEAD = `b9f3df5…768068`** (push
  confirmed).
- Remote page: `https://ai-service-leob.onrender.com/cuistance_trial.html` → **HTTP 200**, but still serves the
  **OLD version**. New-version markers absent across 5 polls over ~4 min (09:14–09:17):
  - `素材就绪检查` (Step-1 asset-readiness panel) → **0 hits**
  - `id="rb-prod1"` (readiness row) → **0 hits**
  - `affiche-card-badge` (Step-2 backend-ready badge) → **0 hits**
  - (`btn-sample` / 使用示例素材 present → it is the prior page, not b9f3df5.)
- Conclusion: the Render deploy of `b9f3df5` has **not landed yet** (documented remote deploy lag — the remote
  routinely runs a prior commit for a window after push).

## 2. Auth gate (documented, no creds used)

- `GET /api/auth/me` (no creds) → HTTP 200 `{"enabled":true,"authenticated":false,"username":null}` — OPS login is
  **required** for the API-backed flow (workbench create / candidate generate / selected-visual / email preview).
- **No OPS credentials were available** in this pass (no `/tmp/cuistance_ops.json`, no env vars). Per policy no
  password is printed or committed. The remote API-backed flow cannot be exercised without OPS auth.

## 3. Why HOLD (per task acceptance rules)

Two independent prerequisites are unmet, each a task-defined HOLD condition:
1. **Remote still serves the old page** → required screenshots 01/02/03 depend on the new readiness markup +
   backend-ready badge that are not deployed yet.
2. **OPS login cannot be attempted** (no credentials) → the API-backed selection/preview flow cannot run remotely.

No code change was made: the blockers are deploy + credentials, not a code defect. The local implementation and
screenshot verification of `b9f3df5` were already **accepted** by the Owner (see
`cuistance_commercial_trial_ui_candidate_selection_state_fix_status_v1.md`).

## 4. Screenshots

Target dir: `docs/poster2/assets/cuistance_remote_candidate_selection_verify_b9f3df5/` (see README placeholder).
Remote screenshots are **PENDING** — not captured/fabricated, because the deployed page is stale and OPS auth is
unavailable. The five required shots (`01_remote_step1_asset_readiness.png`, `02_remote_step2_ready_before_select.png`,
`03_remote_step2_after_select.png`, `04_remote_step3_preview.png`, `05_remote_diagnostics_evidence.png`) will be
captured when validation is re-run.

## 5. Evidence summary

- selected_email_body_visual after selection: **not verified remotely** (flow not run).
- Step 3 unlocked: **not verified remotely**.
- preview status: **not verified remotely**.
- test send: **not run**.
- real email sent: **No** (nothing sent).

## 6. Prerequisites to clear the HOLD

1. Confirm/complete the Render deploy of `b9f3df5` or later on the trial branch (verify the page shows
   `素材就绪检查` / `id="rb-prod1"` / `affiche-card-badge`).
2. Provide OPS credentials securely (e.g. a temp file the verifier reads, never printed/committed/deleted-after).

When both are met, re-run: 使用示例素材 → save Step 1 → enter Step 2 (reuse ready affiche; if generate 504s, confirm
`生成超时，可继续使用已生成版本或稍后重试` + retained ready candidate) → 选为邮件主体 → confirm
`selected_email_body_visual=affiche` + `已选为邮件主体` + continue enabled → Step 3 → preview (brand header + selected
poster + CTA + footer/legal) → optional test-send (internal recipient, test mode, no customer).

## 7. Recommendation

**HOLD** for operator trial remote GO until the deploy lands and OPS creds are provided. The accepted local
verification stands; only the remote confirmation against the deployed page remains.

STATUS: REMOTE CANDIDATE SELECTION STATE VERIFY SUBMITTED FOR OWNER REVIEW.
