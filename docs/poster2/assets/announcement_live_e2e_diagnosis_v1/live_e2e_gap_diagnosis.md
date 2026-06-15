# Family B Announcement — Live E2E Gap Diagnosis v1

> **Task:** `POSTER2-FAMILY-B-ANNOUNCEMENT-LIVE-E2E-GAP-DIAGNOSIS`. **Date:** 2026-06-15.
> **Verdict:** **DEPLOYMENT MISMATCH — remote is not running the announcement commit. Stop at Step 1 (per task).**
> No code change is warranted: the announcement code is correct and committed; it is simply not deployed.

## Step 1 — remote service version (decisive)

Probed the deployed backend `https://ai-service-leob.onrender.com` directly (network reachable).

| Signal | Deployed value | Expected (this work) |
|---|---|---|
| `build-info.json` | **branch `kit1.0`, sha `0cbaf65`, built `2026-01-24`** | branch `poster2-family-b-announcement-ui-closure-v1`, sha `1fdeb84` |
| OpenAPI `GeneratePosterV2Request.availability_badge` | **ABSENT** | present |
| OpenAPI `…tariff_mode` / `on_poster_cta_label` / `on_poster_cta_email` | **ABSENT** | present |
| OpenAPI `GeneratePosterV2Response.announcement_variant_contract_review` | **ABSENT** | present |
| OpenAPI Template-B fields `sku_text` / `description_title` / `description_body` | present | present |
| Served `/index.html` `#s1-template-b-announcement` + announcement input ids | **ABSENT** | present |

Git ground truth (`git ls-remote origin`):

- `origin/main` = `21ebba2` (composition priority layer) — predates announcement work.
- `origin/poster2-family-b-announcement-ui-closure-v1` = `1fdeb84` — **the announcement commit is pushed**, but
  the Render service is **not** serving it.
- The deployed build (`kit1.0` / `0cbaf65`, 2026-01-24) predates **even `main`**.

**Conclusion: `ai-service-leob` is NOT running `1fdeb84` (nor `main`). It is pinned to an old `kit1.0` build.**
Evidence: `live_e2e_probe_evidence.json`, `remote_build_info.json`.

## Root cause (why the symptom occurs)

1. **Deployed backend has no announcement schema.** Its `GeneratePosterV2Request` does not define
   `availability_badge` / `tariff_mode` / `on_poster_cta_*`. FastAPI/Pydantic models default to `extra=ignore`, so
   even if a newer operator UI sends those fields, the **old backend silently drops them** → the poster renders
   without EN STOCK / Tarif / CTA.
2. **Deployed backend has no announcement diagnostics.** Its `GeneratePosterV2Response` has no
   `announcement_variant_contract_review` field → diagnostics cannot show it (matches the owner's observation).
3. **Deployed frontend (served by Render) also predates the UI.** The Render-served `/index.html` lacks the
   announcement fieldset. So "the UI appears present" was observed on a **different frontend build** (local
   validation, or the feature branch's GitHub Pages), not on the Render-served one. The two surfaces are out of
   sync with the deployed backend.

This fully explains: UI seen elsewhere → fields sent → **old deployed backend ignores them** → no announcement
content in the poster and no `announcement_variant_contract_review` in the response.

## Steps 2–5 — not applicable yet

Per the task ("If not [current], report deployment mismatch and stop"), Steps 2–5 are **gated**: capturing the
live Network POST body or chasing a frontend-mapping/backend-resolver bug is moot while the deployed backend
predates the feature entirely. The local E2E was already proven in the prior slice (backend render + diagnostics +
UI fill + Stage1-snapshot capture; `announcement_ui_closure_v1/`). The gap is purely **deploy**, not code.

## Remediation (Owner action — no code change required)

1. **Deploy the announcement commit to the backend.** Point the Render `ai-service-leob` service at
   `1fdeb84` — either merge `poster2-family-b-announcement-ui-closure-v1` into the branch Render builds (it is
   currently pinned to `kit1.0` / `0cbaf65`, so confirm/repoint the Render branch + trigger a rebuild), or
   configure it to deploy this branch. After deploy, `/build-info.json` should report the new sha and
   `/openapi.json` should contain `availability_badge` + `announcement_variant_contract_review`.
2. **Publish the matching frontend.** Ensure the GitHub Pages / served `docs/` build that operators use is the
   one containing `#s1-template-b-announcement` (this branch's `docs/`), pointed at the updated backend.
3. **Re-run live E2E** (the prior slice's acceptance): select Family B, fill EN STOCK / on_request / CTA,
   generate, and confirm the final poster shows EN STOCK / "Tarif : nous contacter" / "Nous contacter · email"
   and the response includes `announcement_variant_contract_review`.

## Quick verification command (post-deploy)

```
curl -s https://ai-service-leob.onrender.com/build-info.json
curl -s https://ai-service-leob.onrender.com/openapi.json | grep -o '"availability_badge"' | head -1
```

Expect the new sha and a non-empty `availability_badge` match.

## Compliance

No code changed; no Stage3 / Poster Set runtime / Catalog Hero / Family A / bottom SOP / geometry change; nothing
pushed or deployed by this diagnosis. Evidence-only.
