# Email Container Remote Trial Smoke v1 — REMOTE_AUTH_BLOCKED

Task: **POSTER2-EMAIL-CONTAINER-REMOTE-TRIAL-SMOKE-V1**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1` @ HEAD `b6bcbbb`.
Status: **BLOCKED_OPS_AUTH_REQUIRED** — no remote blocker proven against the code; the authenticated preview
validation could not run because OPS credentials are unavailable in this environment.

No app/schema/email/assembly/P2A-demo code was changed. No real send. No fabricated authenticated evidence.

---

## 1. Remote URL

```
https://ai-service-leob.onrender.com/cuistance_trial.html
```

## 2. Deployed commit

Remote is deployed at **`b6bcbbb` or later** — proven WITHOUT auth: the served trial page carries the b6bcbbb
container-flexibility / fillability markers (NOT deploy lag):

```
container-fill-state        x3   (new fill-state UI element)
updateContainerFillState    x2   (new JS function)
container_profile           x2
fill-badge                  x2
spec_display_mode           x3
missing_required_fields     x4
```

There is no `/version` endpoint, so the exact deployed backend commit hash cannot be confirmed by hash; the
frontend markers confirm the deploy is at/after `b6bcbbb`.

Health: `healthz=200`, `health=200`. Page: `/cuistance_trial.html=200`, 110,895 bytes, is the trial page
(`商业试用工作台`), no fatal load error observed on fetch.

## 3. Affiche result

**BLOCKED.** The Affiche preview field assertions (`preview_ready`, `container_profile=single_product_campaign_email`,
`spec_display_mode=in_visual`, `body_visual_mode=email_embedded_no_header`, `email_body_visual_contract_pass`,
`body_visual_contains_own_banner`, `filled_*`, `missing_required_fields`, `send_hold`, `real_email_sent`) require an
authenticated workbench → candidate → select → preview round-trip. The v2 API is OPS-gated and OPS creds are absent.

## 4. Fiche result

**BLOCKED.** Same reason — the Fiche preview assertions (`preview_ready`, `container_profile=single_product_sheet_email`,
`spec_display_mode=spec_list`, `body_visual_mode=product_image`, `poster_key=null`, `uses_poster_generation=false`,
`generated_from=workbench_truth`, `product_sheet_email_contract_pass`, `filled_*`, `missing_required_fields`) could
not be executed.

## 5. Missing-field result

**BLOCKED.** The safe missing-field case (expected HTTP 200 + `preview_ready=false` + clear codes, no wrong-product
fallback) requires an authenticated preview call.

## 6. Send semantics

Not exercised live (requires auth). By code (verified locally at `b6bcbbb`): default `delivery_mode=inline_only` →
provider `preview_only` → attempt `skipped`; `real_email_sent=false`; `send_hold=true`. **No real send attempted.**
This task carries no test-recipient / confirm_send authorization.

## 7. Blockers

```
BLOCKED_OPS_AUTH_REQUIRED
  - Remote v2 API is OPS-gated: POST /api/v2/workbench -> 401 ops_auth_required
  - /api/auth/me -> {enabled:true, authenticated:false, username:null}
  - OPS credentials are not available in this environment (no /tmp/cuistance_ops_auth/creds.env, no OPS env)
```

To unblock: provide Owner-approved OPS credentials via the secure temporary method; the authenticated remote
Affiche/Fiche preview + missing-field + mismatch-guard validation then completes against this already-deployed build.

## 8. Ready for operator trial?

**Partially — deploy confirmed, authenticated behavior not yet remote-verified.** The remote service is up and is
serving the `b6bcbbb` container trial closure code. The two routes already PASS locally (42+10 focused tests at
`b6bcbbb`). Operator-trial readiness on remote is pending one OPS-authenticated smoke pass; nothing in this run
indicates a remote regression.

## Owner Decision Needed

Provide OPS credentials (secure temporary method) so the authenticated remote preview smoke can run against the
deployed `b6bcbbb` build. Multi-product, products[] backend, and real customer send remain HOLD.
