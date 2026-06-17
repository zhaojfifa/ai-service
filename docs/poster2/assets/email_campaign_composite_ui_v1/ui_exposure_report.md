# UI Exposure + Smoke — email_campaign_composite_v1 dropdown

## Diagnosis (why it was invisible)
The Stage1 template dropdown is built from `templates/registry.json`; `email_campaign_composite_v1` was
NOT in that registry → not listed. Additionally, even if listed, the Stage2 generate path remapped any
non-pilot id to `template_dual_v2` via `resolvePoster2PilotTemplateId` / `resolvePoster2CompositionTemplateId`
(fallback) — so the selection would not have reached the new backend route.

## Fix (additive, isolated)
1. `frontend/templates/registry.json` (+ `docs/` mirror): added the entry
   `{ id: email_campaign_composite_v1, name: "Email Campaign Composite · Campaign Explainer", preview: catalog_hero_v1_preview.svg, ... }`.
2. `frontend/app.js` (+ `docs/app.js` mirror): added `POSTER2_DIRECT_TEMPLATE_IDS = {catalog_hero_v1,
   email_campaign_composite_v1}` and made `resolvePoster2PilotTemplateId` + `resolvePoster2CompositionTemplateId`
   pass these ids through UNCHANGED (additive families dispatch by their own backend path). Family A/B pilot
   + composition routing is unaffected.
No backend renderer change. No UI redesign. No Stage1/2/3 semantics / Family A-B / Product Sheet / Catalog
Hero behavior change.

## Validation
| Check | Result |
|---|---|
| UI dropdown shows the new option | ✅ `ui_dropdown_option.png` — "Email Campaign Composite · Campaign Explainer" |
| Options preserved (no regression) | ✅ template_dual, template_dual_studio, template_product_sheet_v1, catalog_hero_v1 all still present |
| Selecting it yields template_id | ✅ `ui_proof.json` selected_value = `email_campaign_composite_v1` |
| Resolver passes it through (not remapped) | ✅ direct-passthrough added; verified in app.js |
| Local backend route accepts it | ✅ `api_response_review.json`: HTTP 200, template_id=email_campaign_composite_v1, structure_complete=true, callout_count=3, leakage_clean=true, thermostat_uses_unsupported_0_200C=false, ai_substrate_is_truth=false |
| Generated poster visual | ✅ `generated_poster.png` — matches accepted P2/runtime design, no regression |
| frontend↔docs sync + api + registry tests | ✅ 17 passed |

## Remote (deployed backend)
- `GET /health` = 200. `POST /api/v2/generate-poster (email_campaign_composite_v1)` = **401 — ops-auth-gated**.
- **Exact blocker (unchanged):** the remote generate endpoint requires ops auth; no credentials available
  and pulling Render secrets is forbidden. So remote generation + remote email business flow (R2 URL →
  preview → real send) could NOT be executed here. Local proof of the same deployed code passes all gates.

## Notes
- The new frontend changes are in the repo (frontend/ + docs/ mirror) but the live UI is GitHub Pages
  (zhaojfifa.github.io) — owner must publish the frontend (docs/) for the option to appear in production.
- Email business-flow smoke (preview + real send) was proven locally in the prior slice; remote real send
  remains blocked by ops auth + R2/Resend env verification (see remote_deploy_smoke_v1 / remote_ops_smoke_v2).
