# poster2 Documentation Index

`docs/poster2/README.md` is the formal index only.
It defines the reading path and the formal doc path.
It does not carry branch history, pasted progress logs, or one-off process notes.

## Root-Level Exceptions

The following three files remain at `docs/poster2/` root by rule:

1. [poster_generation_product_design_baseline_v1.md](poster_generation_product_design_baseline_v1.md)
2. [README.md](README.md)
3. [current_branch_execution_log_v1.md](current_branch_execution_log_v1.md)

All other formal poster2 documents now belong under the layered directories:

- `01_product/`
- `02_architecture/`
- `03_engineering/`
- `04_skills/`
- `05_validation/`
- `99_archive/`

## Entry Order

Read in this order for poster2 work:

1. [poster_generation_product_design_baseline_v1.md](poster_generation_product_design_baseline_v1.md)
2. [template_dual_v2_architecture_business_definition.md](02_architecture/template_dual_v2_architecture_business_definition.md)
3. [template_family_region_matrix_v1.md](02_architecture/template_family_region_matrix_v1.md)
4. [template_family_slot_contract_baseline_v1.md](02_architecture/template_family_slot_contract_baseline_v1.md)
5. [renderer_routing_and_fallback_rules_v1.md](02_architecture/renderer_routing_and_fallback_rules_v1.md)
6. [quality_guard_and_structure_completeness_v1.md](02_architecture/quality_guard_and_structure_completeness_v1.md)
7. [family_isolation_rules_v1.md](02_architecture/family_isolation_rules_v1.md)
8. [skill_rules_and_storage_v1.md](04_skills/skill_rules_and_storage_v1.md)
9. [family_a_four_layer_verification_matrix_v1.md](05_validation/family_a_four_layer_verification_matrix_v1.md)

Then read only the task-relevant status / plan / validation documents.

## Formal Document Path

### 01 Product

- [external_reference_poster_design_review_and_migration_v1.md](01_product/external_reference_poster_design_review_and_migration_v1.md)
- [poster2_product_flow_reviewable_v1.md](01_product/poster2_product_flow_reviewable_v1.md)
- [cuistance_commercial_trial_product_design_v1.md](cuistance_commercial_trial_product_design_v1.md) — CUISTANCE Campaign Production Platform: v1 commercial-trial product design (Campaign Job → TruthLock → Poster/Email package → owner-gated send; A/B/C employee workflow; maps to the proven POSTER2 backend). Design only.
- [ui_mockups/cuistance_commercial_trial_v1/](ui_mockups/cuistance_commercial_trial_v1/) — **Static UI mockup / visual prototype** (task `POSTER2-CUISTANCE-COMMERCIAL-TRIAL-STATIC-UI-MOCKUP-V1`) of the commercial email workbench: self-contained `index.html` + `styles.css` + SVG placeholders + `README.md`. Renders the approved 3-step flow (① Produit & éléments ② Affiche produit ③ Email & envoi) in the preview-first two-column B2B-SaaS layout (top header + 3-step progress + left edit / right live preview + bottom single primary CTA + hidden ⓘ diagnostics drawer). Email Banner Module is visibly **first-class** (dark brand header + logo chip + subtle pattern + red filet + optional channel/campaign), **separate** from the poster body; the **final email preview shows banner + poster body**; the simplified product sheet is an **amber, useful option** (not a red error); recipients are manual chips with a confirm modal + per-recipient results. **No backend / no real upload·generate·send**; interactions are local view-switching only; **no engineering language** on operator screens (verified). Design artifact for Owner/PM/operator visual review — not PR-1, not production code. **REVISED (real assets + zh/fr test UI, 2026-06-18):** now uses **real assets** — `assets/logo_01.jpg` (real CUISTANCE logo from `~/poster/SOP/logo_01.jpg`), `assets/banner_option_01.jpg` (real CUISTANCE NOUVEAUTÉ email header, default-selected) + `assets/banner_option_02.jpg` (real Technitalia banner), both extracted from the remote-hosted images referenced by the target `.eml` files under `~/poster/SOP/` (provenance documented in the mockup README; `.jpg` filenames carry PNG content). The Email Banner Module shows **two real banner options with a default selection** and a live swap that updates both the editor preview and the final email preview (banner + poster body, kept separate). UI language: **Chinese-primary explanatory text + French UI labels/buttons** (system supports zh/fr). Product/gallery remain lightweight SVG placeholders (only logo/banner were required as real). **V2 REVISE (2026-06-18):** added a **language switch (中文 default / Français target)** that swaps the whole UI chrome (email preview content stays French); applied the **real logo** in header + Step 1 + banner module + final email preview; added **structured technical parameters** (import/recognition entry + rows for Référence/Capacité/Puissance/Tension/Dimensions/Matière/Thermostat/Autres + per-row confirm + format rules + a truth note: params from confirmed input, AI wording-only, **190°C = case001 sample, not a platform rule**); added a separate **Product Description / 产品介绍** field (email intro / sheet body / poster support copy / optimizer weak-input); upgraded the **simplified product sheet** to a real product-sheet visual (shared banner + **1–2 real product images** + description + confirmed params + CTA, an amber **useful option**, no fallback/degraded/Route-B wording); added **real product images** (`product_01/02.jpg` from `~/poster/SOP/Electric Fryer1/2.jpg`); and a **reference-alignment checklist** (Technitalia + the 3 CUISTANCE fallback emails + Email Campaign Composite). **STATUS: STATIC UI MOCKUP V2 SUBMITTED FOR OWNER REVIEW.**
- [cuistance_commercial_trial_claude_design_ui_v1.md](cuistance_commercial_trial_claude_design_ui_v1.md) — **Commercial visual UI design** for the CUISTANCE single-product promotional **email workbench** (task `POSTER2-CUISTANCE-COMMERCIAL-TRIAL-CLAUDE-DESIGN-UI-V1`; design → self-verify → submit). Design-forward layer over the approved 3-step flow (① Produit & éléments ② Affiche produit ③ Email & envoi): clean B2B SaaS / modern-European aesthetic, **preview-first** two-column workbench (left edit / right live email preview), single primary CTA per screen, neutral palette with CUISTANCE-red accent only on the active step/primary action, calm cards (no debug dashboards). Email Banner Module is **first-class** (logo + dark/brand background + pattern + optional channel/campaign text; never "removed"; final email shows **banner + poster body**); simplified product sheet is an **amber, useful option, not a failure**; product parameters come from **confirmed input** (190°C = case001/EF132V sample only, not a platform rule); AI/Gemini never shown as a truth source. Zero engineering leakage on operator screens (no branch/tag/API/R2/`template_id`/`request_id`/`poster_key`/renderer/chromium/Gemini/JSON/contract_review/Route A·B/degraded — internal terms isolated to the ⓘ diagnostics drawer / internal notes). Includes visual-style tokens, IA, 3 screen designs, banner-module design, simplified-sheet state, French UI copy table, text+Mermaid wireframes, business-language error states, usability review, design risks, and an explicit A–G self-verification report. Docs-only; no code/UI/renderer/merge/tag/push/send/PR-1; design **not self-approved**. **STATUS: SUBMITTED FOR OWNER REVIEW.**
- [cuistance_commercial_trial_ui_flow_design_v1.md](cuistance_commercial_trial_ui_flow_design_v1.md) — **UI-flow-first, commercial-facing** design (task `POSTER2-CUISTANCE-COMMERCIAL-TRIAL-BASELINE-AND-UI-FLOW-DESIGN-V1`; Owner ruling: UI before engineering; **REVISED to 3 steps + Chinese/internal-review doc**). Chinese-primary (English for technical identifiers; French only as UI copy examples — no separate French doc). Part A (engineering/internal only) = baseline-freeze plan: branch `feature/...remote-smoke-v1`, HEAD `11ece26`, feature = main + 9 commits, proposed tag `baseline/poster2-cuistance-commercial-trial-remote-pass-v1` — **propose only, do not create without Owner approval**; defer main merge. Part B = **3-step** operator workbench: ① 产品与素材 / Produit & éléments (merged old create+materials), ② 生成产品海报主体 / Affiche produit, ③ 拼接邮件、预览并发送 / Email & envoi. Engineering language (branch/tag/`template_id`/`renderer`/`chromium`/`R2`/Route A·B/API/`contract_review`/`request_id`/`poster_key`/Gemini) hidden from operator screens → only in the ⓘ diagnostics drawer / engineering appendix; operator UI uses business French (Affiche produit / Fiche produit simplifiée / Vérification / Information vérifiée / Version simplifiée disponible). Keeps poster route primary + simplified product-sheet fallback, Logo/Banner separated into Email Assembly, manual-recipient send, no contact-import/scheduling/analytics. Includes French UI copy table, visible-vs-internal split, business-language error states, wireframes, 3-step engineering implications (PR-1 = 3-step shell), and open questions. **REVISED (semantics, 2026-06-18):** (1) **Email Banner Module is first-class** — Logo/Banner is *separated* from the Product Poster Body into an independent email header module (logo + dark/brand background + pattern + optional channel/group/campaign text), reused across poster + simplified-sheet routes; the final email **keeps both banner and poster** (operator UI never says "removed"). Email Package = Banner Module → Poster Body → Copy/CTA → Footer Contact/Social → Attachments → Recipients/Send. (2) **Product parameters come from confirmed input** (manual / imported pack / future PDF extraction); AI organizes wording only, never invents/changes technical params — `jusqu'à 190°C` is a **case001/EF132V sample fact only, not a platform rule** (UI uses generic `Caractéristiques techniques` / `Information vérifiée`). Stop point: docs-only; PR-1 NOT started. No code, no merge, no push, no tag, no send.
- [cuistance_commercial_trial_operator_ui_exposure_status_v1.md](cuistance_commercial_trial_operator_ui_exposure_status_v1.md) — **Operator-trial UI exposure** (task `POSTER2-CUISTANCE-V1-EXPOSE-OPERATOR-TRIAL-UI`). Adds a minimal static operator page **`/cuistance_trial.html`** (`frontend/` + `docs/` mirror; served by the existing StaticFiles mount — no new route, no backend change) titled "CUISTANCE v1 · Operator Trial · 商业试用工作台", distinct from `/` and `/ops_campaign.html`. Drives the full v1 loop via existing endpoints (create workbench → EF132V product_truth → assets/banner → generate affiche [+fiche, allowed to fail without Vertex] → select → EmailBodyPlan preview → manual confirmed test send → send_attempts evidence). Default test mode + inline_only; real send requires explicit mode switch + confirm checkbox; manual single internal recipient only (no customer list/import/CRM/scheduling/analytics); URL/key assets only; OPS-login affordance for the gated `/api/v2/*`. Local validation: page served (200) + create→affiche(ready)→select→preview(layout=single_product_promo, width=600) green. STATUS: OPERATOR TRIAL UI EXPOSURE SUBMITTED FOR OWNER REVIEW.
- [cuistance_commercial_trial_remote_full_flow_smoke_result_v1.md](cuistance_commercial_trial_remote_full_flow_smoke_result_v1.md) — **Trial branch push + remote smoke result** (task `POSTER2-CUISTANCE-V1-TRIAL-BRANCH-PUSH-AND-REMOTE-SMOKE`). Branch `trial/poster2-cuistance-v1-operator-trial` committed (`972bdc3`, scoped 25 files, nothing forbidden staged) and **pushed to origin** (no merge/tag/main). **Remote deploy + remote full-flow smoke BLOCKED → Owner Decision Needed:** `render.yaml` has one service with no branch pin and no validation service (trial branch won't auto-deploy; deploying needs a Render dashboard action), and the live service returns **401 on all `/api/v2/*`** (OPS-auth gated; no credentials used/printed). Secret-safe config inference from `render.yaml`: Vertex/Firefly/Chromium likely present (fiche may work remotely), but **Resend and R2 are not declared** (real send + HTTPS posters likely unavailable). No remote smoke executed; no email sent. Verdict: **code/branch GO; remote operator validation HOLD** pending Owner's deploy-target choice (3 options listed) + Resend/R2 config + OPS credential delivery. **STATUS: TRIAL BRANCH REMOTE SMOKE SUBMITTED FOR OWNER REVIEW.**
- [cuistance_commercial_trial_operator_validation_branch_prep_v1.md](cuistance_commercial_trial_operator_validation_branch_prep_v1.md) — **Operator-trial branch prep + validation package** (task `POSTER2-CUISTANCE-V1-OPERATOR-TRIAL-BRANCH-PREP`). Prepares `trial/poster2-cuistance-v1-operator-trial` off base `11ece26`. Docs router PASS; **78 trial tests pass** (PR-1…PR-4) + existing API 35 (CORS caveat); scope confirmed clean (only workbench/email app files; no frontend/deploy changes). Includes feature-readiness matrix, secret-safe runtime-config readiness (all email/Vertex/R2 config **unset locally**), known limitations (fiche needs Vertex, real send needs Resend, inline data URL without R2), manual validation steps (affiche main route), and a GO/HOLD verdict (**logic GO; real-customer send HOLD until configured**). **Key finding: PR-1…PR-4 are uncommitted in the working tree** amid unrelated untracked churn, so the doc gives **exact scoped-commit + branch-create commands held for Owner approval** — branch **not created/committed/pushed**. **STATUS: OPERATOR VALIDATION BRANCH PREP SUBMITTED FOR OWNER REVIEW.**
- [cuistance_commercial_trial_full_flow_smoke_result_v1.md](cuistance_commercial_trial_full_flow_smoke_result_v1.md) — **Full-flow runtime smoke result** (task `POSTER2-CUISTANCE-COMMERCIAL-TRIAL-FULL-FLOW-SMOKE-V1`). End-to-end in-process run of the v1 loop: create workbench (`wb_33656232431e46a4`) → product_truth (EF132V) → assets/banner → generate candidates → select → EmailBodyPlan preview → manual confirmed test send → send_attempts evidence. **affiche generated (real Chromium, degraded=false, callout_count=3, poster_key `p2_4fb82bb4ba5e4120`); fiche FAILED** (`background_prepare_failed` — "Vertex Imagen3 client is not initialised", local Vertex unconfigured). Preview passed all 10 plan/shell/banner/CTA/footer checks. Send (test, inline_only): 3 unique recipients (1 deduped), 2 skipped `preview_only`, 1 `invalid_recipient`; resend probe → **"Resend is not configured."** **No real email sent** (no provider_message_id). Blockers = runtime config only (Resend/Vertex/R2 unconfigured), not workbench logic. Verdict: **HOLD for real send → GO after Resend+sender domain (and Vertex if fiche needed) configured.** Secret-safe; no tag/merge/push. **STATUS: FULL FLOW SMOKE SUBMITTED FOR OWNER REVIEW.**
- [cuistance_commercial_trial_pr4_manual_send_evidence_status_v1.md](cuistance_commercial_trial_pr4_manual_send_evidence_status_v1.md) — **PR-4 manual multi-recipient send + evidence** (task `POSTER2-CUISTANCE-COMMERCIAL-TRIAL-PR4-MANUAL-MULTI-RECIPIENT-SEND-EVIDENCE`). New endpoint `POST /api/v2/workbench/{key}/email/send` that **consumes the deterministic PR-3S package verbatim** (via a shared `_resolve_workbench_email_package` resolver also used by preview — no body reconstruction, no candidate re-selection, no Gemini fact change, no new poster). Requires explicit `confirm_send` (test + real); manual `recipients[]` only with format validation, deterministic case-insensitive dedup (`deduplicated_count`), and per-recipient isolation; persists `workbench.send_attempts` evidence (recipient, mode, status sent|error|skipped, provider, provider_message_id, error_code/message, attachment_types, at, selected_email_body_visual, body_visual_poster_key, `layout_type`, subject snapshot, deduplicated). Reuses the existing provider; **legacy single-recipient `/api/v2/email/send` untouched**. 14 new tests + 78 workbench (PR-1…PR-4) + existing API 35 pass; no real email sent in tests. No contact import/CRM/scheduling/analytics/dashboard/automation; no renderer/tag/merge/push. **Completes the v1 commercial backend loop.** **STATUS: PR-4 MANUAL MULTI-RECIPIENT SEND EVIDENCE SUBMITTED FOR OWNER REVIEW.**
- [cuistance_commercial_trial_pr3s_email_body_plan_status_v1.md](cuistance_commercial_trial_pr3s_email_body_plan_status_v1.md) — **PR-3S Email Body Plan** (task `POSTER2-CUISTANCE-COMMERCIAL-TRIAL-PR3S-EMAIL-BODY-PLAN-BEFORE-SEND`; PR-4 paused). Introduces a deterministic `EmailBodyPlanView` (`layout_type=single_product_promo`, `container_width=600`, fixed module order email_banner → title_intro → selected_body_visual → product_description → cta → contact_footer → legal_footer) + a `selected_body_visual_slot` (source=`workbench.selected_email_body_visual`, candidate_type, poster_key, `final_poster_url` from the loaded poster_record). `app/services/email/assembly.py` now **generates the HTML from the plan order**; the selected poster/product image enters the email **only** through the planned slot. `POST /api/v2/workbench/{key}/email/preview` now also returns `email_body_plan`. The prematurely-started PR-4 send endpoint/schema/helper were **backed out** (branch has no send path; existing `/api/v2/email/send` untouched). 11 new tests + PR-3/PR-3R 19 + PR-1/PR-2 34 + existing API 35 pass. No renderer/send change; no tag/merge/push. **STATUS: PR-3S EMAIL BODY PLAN SUBMITTED FOR OWNER REVIEW.**
- [cuistance_commercial_trial_reference_email_html_extraction_v1.md](cuistance_commercial_trial_reference_email_html_extraction_v1.md) — **PR-3R reference email grammar extraction** (task `POSTER2-CUISTANCE-COMMERCIAL-TRIAL-PR3R-REFERENCE-EMAIL-HTML-EXTRACTION-PATCH`). Extracts reusable email structure grammar from the real reference emails `~/poster/SOP/ttt.html` (CUISTANCE Mailchimp NOUVEAUTÉ) + `ttt2.html` (Technitalia Zoho): 600px table-safe container, top banner module, red/orange filet, title/intro, body-visual placement, CTA, contact/footer + 4-icon contact row + FB/LinkedIn/Instagram social row, legal/unsubscribe placeholder, and a banner/logo/product asset-URL inventory. **Adopts minimally** into `app/services/email/assembly.py` (640→600px table-safe shell + explicit red `#E1002A` filet + legal/unsubscribe placeholder); contact/social icon rows left as future. **Copies no** Zoho/Mailchimp scripts, tracking, share/comment widgets, view-in-browser, hidden campaign IDs, third-party unsubscribe, or raw HTML. 7 new tests + PR-3 12 + PR-1/2 34 + existing API 35 pass. `/api/v2/email/send` untouched; no renderer rewrite; no PR-4. **STATUS: PR-3R REFERENCE EMAIL HTML EXTRACTION PATCH SUBMITTED FOR OWNER REVIEW.**
- [cuistance_commercial_trial_pr3_email_banner_assembly_status_v1.md](cuistance_commercial_trial_pr3_email_banner_assembly_status_v1.md) — **PR-3 implementation status** (task `POSTER2-CUISTANCE-COMMERCIAL-TRIAL-PR3-EMAIL-BANNER-AND-ASSEMBLY-PREVIEW`). Email-level **Email Banner Module** + **Email Assembly preview**: new `app/services/email/assembly.py` + thin endpoint `POST /api/v2/workbench/{key}/email/preview` that **deterministically** consumes `workbench.selected_email_body_visual` → resolves `poster_candidates[selected].poster_key` → loads the poster_record → uses `final_poster.url` as the body visual, and assembles banner (from `workbench.email_banner`, shared by affiche/fiche) + selected visual + intro (`product_truth.description`) + CTA (`Nous contacter`) + footer + attachment readiness (reuses existing draft + `build_email_assets_for_record`). Gemini cannot touch technical parameters (canonical copy input excludes `product_truth.parameters` by construction); 190°C stays an ordinary parameter. **Banner decoupling done additively at the email layer with NO renderer change** — the candidate bodies still carry their own baked banner today (documented transitional state, surfaced via `body_visual_contains_own_banner`); **no Owner Decision Needed**. Existing `/api/v2/email/preview` + `/send` untouched. **12 new tests pass; PR-1+PR-2 34 + existing API 35 still pass** (CORS env caveat pre-existing). No PR-4/send change; no tag/merge/push. **STATUS: PR-3 EMAIL BANNER AND ASSEMBLY PREVIEW SUBMITTED FOR OWNER REVIEW.**
- [cuistance_commercial_trial_pr2_candidates_selected_visual_status_v1.md](cuistance_commercial_trial_pr2_candidates_selected_visual_status_v1.md) — **PR-2 implementation status** (task `POSTER2-CUISTANCE-COMMERCIAL-TRIAL-PR2-CANDIDATES-AND-SELECTED-VISUAL`). Step-2 backend: generate two email body visual candidates (affiche → `email_campaign_composite_v1`, fiche → `template_product_sheet_v1` with primary+secondary images) and persist exactly one `selected_email_body_visual`. New `app/services/workbench_candidate_generation.py` (pure truth→payload mapping) + candidate helpers in `workbench_records.py`; 2 thin endpoints `POST /api/v2/workbench/{key}/candidates/{type}/generate` and `PATCH /api/v2/workbench/{key}/selected-visual` that **reuse** `/api/v2/generate-poster` (no renderer fork, no poster_record truth copied — only `poster_key` refs stored). Selection rules: scalar single select, reject unready candidate, regenerating the selected candidate clears selection, regenerating the other keeps it, no version history. **15 new tests pass; PR-1 19 + existing API 35 still pass** (CORS env caveat pre-existing). No PR-3/email/send change; no tag/merge/push; 190°C stays an ordinary parameter. **STATUS: PR-2 CANDIDATES AND SELECTED VISUAL SUBMITTED FOR OWNER REVIEW.**
- [cuistance_commercial_trial_pr1_workbench_truth_status_v1.md](cuistance_commercial_trial_pr1_workbench_truth_status_v1.md) — **PR-1 implementation status** (task `POSTER2-CUISTANCE-COMMERCIAL-TRIAL-PR1-WORKBENCH-TRUTH-MODEL`). Implements the minimal backend-owned workbench truth model: new `app/services/workbench_records.py` (R2 JSON + `/tmp` fallback, mirrors poster_records), workbench/product_truth/product_assets/email_banner Pydantic models in `app/schemas/poster2.py`, and 3 endpoints `POST/GET/PATCH /api/v2/workbench[/{key}]`. URL/key-only (rejects base64), structured parameter rows (reference/capacity/power/voltage/dimensions/material/thermostat/other) with source + pending/confirmed + locked state (lock requires all-confirmed), product description separate from parameters, atmosphere `is_truth=false` only, and **190°C accepted as an ordinary thermostat value, not a platform rule**. PR-2…PR-4 fields are inert placeholders. **19 new tests pass; 54 pass with the existing API suite** (6 generate-poster CORS/error cases fail only without `CORS_ALLOW_ORIGINS` — a pre-existing env artifact, unrelated). No renderer/email/send change; no tag/merge/push. **STATUS: PR-1 WORKBENCH TRUTH MODEL SUBMITTED FOR OWNER REVIEW.**
- [cuistance_commercial_trial_backend_alignment_plan_v1.md](cuistance_commercial_trial_backend_alignment_plan_v1.md) — **Backend alignment + heavy-engineering plan** (task `POSTER2-CUISTANCE-COMMERCIAL-TRIAL-BACKEND-ALIGNMENT-PLAN-V1`) mapping the **Owner-approved UI Mockup V2** onto verified backend truth. Confirms ~70% is already there: R2 presign upload, `/api/v2/generate-poster` dispatch by `template_id` (**both email-body visuals reachable** — `email_campaign_composite_v1` = Affiche produit, `template_product_sheet_v1` = Fiche produit simplifiée, **already 2-image** via `product_image`+`product_secondary_image`), `poster_key`/`poster_record` persistence, `/api/v2/posters/{poster_key}`, `/api/v2/email/preview` (deterministic draft + optional Gemini non-truth + PNG/PDF), `/api/v2/email/send` (single-recipient). Identifies the **5 real gaps**: lightweight workbench/TrialCampaign + structured product-parameter/description truth, Step-2 two candidates + **`selected_email_body_visual` persistence**, **Email Banner Module decoupling** (logo currently baked into `banner_region`/`logo_banner_region`) + Email Assembly preview, **manual multi-recipient** confirmed send, small items. Proposes minimal records (`workbench_record`/`product_truth`/`product_assets`/`email_banner`/`poster_candidates`/`selected_email_body_visual`/`email_package`/`recipients·send_attempts`), **endpoint reuse** (only 2 thin new workbench endpoints), asset flow (url/key, no base64), parameter truth model (190°C = case001 sample only; AI wording-only), Email Assembly, a **PR-0…PR-4** sequence with per-PR acceptance + owner gates, and risks. Notes two Owner-listed source docs are missing in-tree (planned against real code instead). Docs-only; no code/renderer/send/tag/merge/push/PR-1. **STATUS: BACKEND ALIGNMENT PLAN SUBMITTED FOR OWNER REVIEW.**
- [cuistance_commercial_trial_branch_aware_heavy_engineering_design_v1.md](cuistance_commercial_trial_branch_aware_heavy_engineering_design_v1.md) — Branch-aware heavy engineering design (task `POSTER2-CUISTANCE-COMMERCIAL-TRIAL-BRANCH-AWARE-HEAVY-ENGINEERING-DESIGN-V1`). Grounded in live `git`: feature branch = `main` + 9 commits (**strict superset**, fast-forward merge), so the email-campaign chain is feature-only while the Product Sheet template already coexists in the feature tree (reuse needs no cherry-pick); what is missing is **integration** (Product Sheet not selected as Route B in the email chain). Covers branch reality map, feature/main capability ledgers, integration options A/B/C (recommends **A: build on feature first, merge after gates**), Route A/B architecture, Email Assembly, manual-recipient send boundary, support matrix, gap analysis (G1 logo-coupling both templates, G2 Email Assembly, G3 single-recipient, G4 Route B not wired, G5 persistence), merge-risk analysis, and a 3-PR sequence + controlled merge. Verdict: **APPROVE**. Design/review only; no code, no merge, no push, no send.
- [cuistance_commercial_trial_v1_multi_role_design_review.md](cuistance_commercial_trial_v1_multi_role_design_review.md) — Multi-role (Product / Engineering / Operator / Scope-Owner) design review (task `POSTER2-CUISTANCE-COMMERCIAL-TRIAL-V1-MULTI-ROLE-DESIGN-REVIEW`) that **scopes-down** the platform blueprint to a result-oriented v1 workbench: single-product promotion email, 4-step flow, Route A (poster body + Email Assembly) / Route B (HTML product-sheet fallback), **manual operator-confirmed multi-recipient send** (no address-book / Excel / CRM / scheduling / analytics). Grounds the engineering review in live code and flags 3 real gaps — G1 decouple Logo/Banner from the poster body, G2 build the Email Assembly HTML, G3 manual multi-recipient send — plus a 3-PR slice plan. Verdict: **APPROVE → enter engineering plan; start with PR-1 docs/UI-shell.** Design/review only; no code changed, no email sent.

### 02 Architecture

- [template_dual_v2_architecture_business_definition.md](02_architecture/template_dual_v2_architecture_business_definition.md)
- [template_dual_v2_structural_rebuild_baseline_v1.md](02_architecture/template_dual_v2_structural_rebuild_baseline_v1.md)
- [catalog_campaign_poster_set_orchestration_spec_v1.md](02_architecture/catalog_campaign_poster_set_orchestration_spec_v1.md)
  Docs-only orchestration architecture for the Owner-approved **Catalog Campaign Poster Set** direction
  (2026-06-15): shared product input bundle → multiple *simple* poster variants → per-variant contract +
  diagnostics, rolled up under a campaign manifest. Fan-out (not fusion) above Families A/B; no new renderer.
  First implementation candidate = **Product Announcement / Family B reactivation** (reactivate-not-redesign;
  reuses existing `template_product_sheet_v1` regions + SKU slot, adds only availability/tariff/CTA-text copy
  slots). Portrait Catalog Hero mega-poster, standalone Product Matrix, structured spec-table, and Stage3
  remain explicitly out of scope. Turns `real_email_to_poster_grammar_assessment_v1.md` into product architecture.
  **APPROVED (Owner, 2026-06-15).**
- [family_b_product_announcement_variant_contract_v1.md](02_architecture/family_b_product_announcement_variant_contract_v1.md)
  **Canonical** docs-only contract for the **Product Announcement** variant on reactivated Family B
  (`template_product_sheet_v1`) — task `POSTER2-FAMILY-B-ANNOUNCEMENT-VARIANT-CONTRACT-V1`. Reactivate-not-redesign:
  preserves the frozen Family B region order (`logo_banner` → `top_copy` → `materials_strip` → `product_hero` →
  `description`) and reuses the real existing fields (`sku_text`, `title`, `subtitle`, `product_image`,
  `product_secondary_image`, `description_title`, `description_body`); adds only three minimal optional **copy**
  slots — `availability_badge`, `tariff_line`, `on_poster_cta_text` (display only, **not** a Stage3 send). Maps the
  real Cuistance `NOUVEAUTÉ` email grammar, defines required shared + variant fields, diagnostics
  (`announcement_variant_contract_review`), explicit non-goals, and first-slice acceptance criteria. Spec-table
  excluded (deferred to Featured Spec). Stops for Owner approval of the implementation slice.
  - [family_b_announcement_variant_contract_v1.md](02_architecture/family_b_announcement_variant_contract_v1.md)
    — **SUPERSEDED** earlier short sibling; folded into the canonical doc above.
- [poster_visual_grammar_dimension_system_v1.md](02_architecture/poster_visual_grammar_dimension_system_v1.md)
  Visual Grammar Dimension System (task `POSTER2-VISUAL-GRAMMAR-REPLICATION-HEAVY-SLICE-V1`, docs-only):
  12 reusable visual-grammar dimensions (composition archetype, focal hierarchy, typography, color, asset
  relationship, region rhythm, surface, marketing signal, evidence/annotation, beauty tokens, content density,
  replication risk), each mapped to Template Family / Contract / Beauty Layer / AI Asset Layer / Reference→Seed /
  Operator Input / Diagnostics, with a per-dimension replication-risk class (E/V/O/F/U). A planner/selector layer
  **above** the families — it never renders, never edits geometry, never raises the frozen 3-slot annotation count,
  never touches Stage3 or Family A truth. Includes the `product_sheet_announcement_v1` and `catalog_hero_v1`
  grammar profiles. No production runtime code changed.
- [poster_visual_grammar_replication_pipeline_v1.md](02_architecture/poster_visual_grammar_replication_pipeline_v1.md)
  Eight-stage gated pipeline (reference → grammar extraction → operator approval → grammar contract → template
  family-fit check → static render/prototype → multimodal visual scorecard → productization decision) with four
  approval gates protecting frozen truth and a worked precedent (the catalog_hero_v1 reconstruction at 4.47/5).
  Docs-only.
- [catalog_hero_1to1_replication_plan_v1.md](02_architecture/catalog_hero_1to1_replication_plan_v1.md)
  PPT 1:1 replication plan for catalog_hero_v1 (task `POSTER2-CATALOG-HERO-1TO1-REPLICATION-P1`, docs-only):
  target reference (Technitalia), target grammar profile, slot mapping, owner-gated asset requirements, the
  real-asset **static prototype** plan, the gated runtime productization plan, and the ≥4.3 acceptance score gate.
  Finds the 1:1 gap is asset-bound, not grammar-bound. No runtime change.
- [poster2_composite_replication_route_v1.md](02_architecture/poster2_composite_replication_route_v1.md)
  Route-level architecture (task `POSTER2-REFERENCE-REPLICATION-COMPOSITE-ROUTE-REVIEW-V1`, docs-only): the
  composite route to 4.8 — Reference → PPT 1:1 extraction → visual grammar dimensions → replication kernel →
  operator approval → contract family → owner-gated asset layer → Puppeteer precision render → diagnostics/score
  gate. Catalog Hero is the visual spine, PPT 1:1 the offline extractor, Product Sheet the stability/operator
  anchor. Ownership split, 4.8 requirements, implementation path, acceptance gates. No runtime change.
- [poster_replication_kernel_v1.md](02_architecture/poster_replication_kernel_v1.md)
  The shared internal blueprint structure (canvas/object_graph/region_graph/typography/color/asset_semantic/
  layer_stack/annotation_graph/beauty_tokens/fillable_contract/owner_gates/diagnostics) with E/V/O/F/U risk
  classes; each family (B, Catalog Hero, Product Hero, Studio, Reference→Seed, Poster Set) is a kernel profile.
  Proposal-not-truth firewall preserved. No runtime change.
- [reference_inspired_hybrid_generation_route_v1.md](02_architecture/reference_inspired_hybrid_generation_route_v1.md)
  Reference-**inspired** controlled generation (task `POSTER2-REFERENCE-INSPIRED-HYBRID-GENERATION-ROUTE-V1`,
  docs-only): an additive third render mode (`hybrid_generated_bg`) that lets a visual model generate the
  reference-inspired **scene/background** while logo/title/SKU/CTA/feature-text/product identity stay
  **deterministic overlays** (the existing bg-gen + deterministic-foreground architecture). 6-step pipeline,
  element classification, distortion prevention, coexistence with Family B + deterministic Catalog Hero.
  AI output candidate-only until operator approval. No runtime change.
- [hybrid_generation_contract_v1.md](02_architecture/hybrid_generation_contract_v1.md)
  The `reference_inspired_generation_plan` output contract (style_profile, composition_intent,
  generated_layers vs locked_overlay_layers, prompt/negative_prompt, asset_constraints, validation_rules,
  diagnostics) — a replication-kernel profile split by provenance; locked-element policy + validation gate
  ordering (hard auto-reject → advisory score → authoritative operator gate). No runtime change.
- [campaign_manifest_and_variant_selection_contract_v1.md](02_architecture/campaign_manifest_and_variant_selection_contract_v1.md)
  Docs-only roll-up contract: shared bundle + closed-enum **variant selection** → fan-out (one existing
  single-poster resolve per variant; the layer never renders) → **campaign manifest** that references per-variant
  diagnostics (never merges them). Defines campaign identity, shared non-geometric `palette_token`, no-silent-drop /
  partial-set semantics, and read-only reuse of the existing `poster_record` closure (no Stage3 change).
- [template_family_region_matrix_v1.md](02_architecture/template_family_region_matrix_v1.md)
- [template_family_slot_contract_baseline_v1.md](02_architecture/template_family_slot_contract_baseline_v1.md)
- [renderer_routing_and_fallback_rules_v1.md](02_architecture/renderer_routing_and_fallback_rules_v1.md)
- [quality_guard_and_structure_completeness_v1.md](02_architecture/quality_guard_and_structure_completeness_v1.md)
- [family_isolation_rules_v1.md](02_architecture/family_isolation_rules_v1.md)

Review-only (no contract change):

- [real_email_to_poster_grammar_assessment_v1.md](real_email_to_poster_grammar_assessment_v1.md)
  Assessment-only review (HX-20260615-POSTER2-EMAIL-GRAMMAR-REVIEW) of four real customer
  `.eml` campaigns as evidence for poster-generation grammar. Separates email shell from
  poster body; finds the three `NOUVEAUTÉ` single-product emails are one Mailchimp template
  reused across products (stable Product Sheet grammar → Family B), and the `coup de chaud`
  email is the already-extracted `catalog_hero_v1` portrait mega-poster. Verdict: stable
  grammar YES, existing strategy PARTIAL, new flow PARTIAL ("Catalog Campaign Poster Set" =
  orchestration layer above Families A/B, not a new renderer). No code changed.
- [composition_priority_layer_review_v1.md](composition_priority_layer_review_v1.md)
  Review package for the Composition Priority Layer (HX-POSTER2-COMPOSITION-PRIORITY-V1): the operator "海报风格策略" (Balanced / Studio / Product Hero / Catalog Clean) — a request-level, non-geometric CSS-var bundle (scenario atmosphere recede + product lift + text breathing) plus the `template_dual_v2_product_hero` variant. Raises Product Hero to ~4.6/5 (product focus 4.6, scenario 2.5, bottom 2.5, title 4.5, premium 4.6). Proves all protected region bounds, ownership, bottom-SOP geometry, `visible_item_count`, and annotation truth unchanged; base/airy/studio unaffected.
- [geometry_variant_studio_review_v1.md](geometry_variant_studio_review_v1.md)
  Review package for the `template_dual_v2_studio` geometry style variant (HX-POSTER2-STYLE-VARIANT-V1): bounded product-image breathing + stronger title hierarchy + lighter gallery surface. Proves protected region bounds, ownership guards, bottom-SOP geometry, and the 3 product-annotation slots are byte-identical to the base; base + airy untouched. Includes stability + geometry-invariant results, operator review (~4.3/5), and the one Owner decision (geometric bottom-footprint reduction is a frozen-SOP amendment).
- [template_taxonomy_and_visual_relaxation_plan_v1.md](template_taxonomy_and_visual_relaxation_plan_v1.md)
  Planning only. Defines the template taxonomy (fixed base / seeded / style variant / campaign pack, all pinned to a base family) and a Composition / Visual Relaxation beauty-token layer that fixes "too tightly fitted / mechanically packed" output by tuning negative space, surface, blend, and text rhythm only — never region geometry. Governing rule: relaxation changes the space between/inside regions, never region boundaries; bottom SOP and product annotation truth are untouched. Includes runtime compatibility table, enum token model, relaxation rules per visual issue, renderer/Pillow policy, validator + aesthetic QA, and a Phase 1–4 plan.

### 03 Engineering

- [template_dual_v2_engineering_implementation_and_acceptance.md](03_engineering/template_dual_v2_engineering_implementation_and_acceptance.md)
- [template_behavior_layer_plan_v1.md](03_engineering/template_behavior_layer_plan_v1.md)
- [beautification_layer_plan_v1.md](03_engineering/beautification_layer_plan_v1.md)
- [poster_generation_project_restructure_checklist_v1.md](03_engineering/poster_generation_project_restructure_checklist_v1.md)
- [storage_copy_email_closure_status_v1.md](03_engineering/storage_copy_email_closure_status_v1.md)
- [email_copy_optimizer_and_optional_attachment_status_v1.md](03_engineering/email_copy_optimizer_and_optional_attachment_status_v1.md)
- [generation_quality_and_copy_optimization_status_v1.md](03_engineering/generation_quality_and_copy_optimization_status_v1.md)
- [copy_quality_phase1_status_v1.md](03_engineering/copy_quality_phase1_status_v1.md)
- [stage1_operator_input_surface_bugfix_status_v1.md](03_engineering/stage1_operator_input_surface_bugfix_status_v1.md)

Family A practical closure:

- [product_region_practical_beautification_observability_v1.md](03_engineering/family_a/product_region_practical_beautification_observability_v1.md)
- [bottom_region_practical_beautification_observability_v1.md](03_engineering/family_a/bottom_region_practical_beautification_observability_v1.md)
- [gemini_copy_optimizer_integration_v1.md](03_engineering/family_a/gemini_copy_optimizer_integration_v1.md)
- [copy_optimization_value_closure_v1.md](03_engineering/family_a/copy_optimization_value_closure_v1.md)
- [product_annotation_text_closure_v1.md](03_engineering/family_a/product_annotation_text_closure_v1.md)
- [copy_quality_closure_v1.md](03_engineering/family_a/copy_quality_closure_v1.md)
- [template_a_text_contract_repair_and_product_region_text_closure_v1.md](03_engineering/family_a/template_a_text_contract_repair_and_product_region_text_closure_v1.md)
- [family_a_commercial_fryer_min_delta_refinement_v1.md](03_engineering/family_a/family_a_commercial_fryer_min_delta_refinement_v1.md)
- [family_a_fryer_live_diagnosis_micro_refinement_v1.md](03_engineering/family_a/family_a_fryer_live_diagnosis_micro_refinement_v1.md)
- [family_a_product_annotation_shell_micro_structure_v1.md](03_engineering/family_a/family_a_product_annotation_shell_micro_structure_v1.md)
- [family_a_bottom_text_finalization_v1.md](03_engineering/family_a/family_a_bottom_text_finalization_v1.md)
- [family_a_fryer_hero_footer_blocker_removal_v1.md](03_engineering/family_a/family_a_fryer_hero_footer_blocker_removal_v1.md)
- [family_a_fryer_truth_parity_and_footer_caption_closeout_v1.md](03_engineering/family_a/family_a_fryer_truth_parity_and_footer_caption_closeout_v1.md)
- [family_a_fryer_anchor_rebind_and_left_rebalance_v1.md](03_engineering/family_a/family_a_fryer_anchor_rebind_and_left_rebalance_v1.md)
- [family_a_single_primary_support_surface_v1.md](03_engineering/family_a/family_a_single_primary_support_surface_v1.md)

### 04 Skills

- [skill_rules_and_storage_v1.md](04_skills/skill_rules_and_storage_v1.md)

### 05 Validation

Core verification anchors:

- [family_a_four_layer_verification_matrix_v1.md](05_validation/family_a_four_layer_verification_matrix_v1.md)
- [template_a_rebaseline_status_v1.md](05_validation/template_a_rebaseline_status_v1.md)
- [template_a_beautification_freeze_status_v1.md](05_validation/template_a_beautification_freeze_status_v1.md)
- [template_a_isolation_rebaseline_status_v1.md](05_validation/template_a_isolation_rebaseline_status_v1.md)
- [product_region_practical_closure_status_v1.md](05_validation/family_a/product_region_practical_closure_status_v1.md)
- [bottom_region_practical_closure_status_v1.md](05_validation/family_a/bottom_region_practical_closure_status_v1.md)
- [gemini_copy_optimizer_closure_status_v1.md](05_validation/family_a/gemini_copy_optimizer_closure_status_v1.md)
- [copy_optimization_value_closure_status_v1.md](05_validation/family_a/copy_optimization_value_closure_status_v1.md)
- [product_annotation_text_closure_status_v1.md](05_validation/family_a/product_annotation_text_closure_status_v1.md)
- [copy_quality_closure_status_v1.md](05_validation/family_a/copy_quality_closure_status_v1.md)
- [template_a_text_contract_repair_and_product_region_text_closure_status_v1.md](05_validation/family_a/template_a_text_contract_repair_and_product_region_text_closure_status_v1.md)
- [family_a_practical_closure_status_v1.md](05_validation/family_a/family_a_practical_closure_status_v1.md)
- [family_a_practical_closure_verification_matrix_v1.md](05_validation/family_a/family_a_practical_closure_verification_matrix_v1.md)
- [bottom_gallery_helper_card_rebalance_status_v1.md](05_validation/family_a/bottom_gallery_helper_card_rebalance_status_v1.md)
- [family_a_commercial_fryer_min_delta_refinement_status_v1.md](05_validation/family_a/family_a_commercial_fryer_min_delta_refinement_status_v1.md)
- [family_a_fryer_live_diagnosis_micro_refinement_status_v1.md](05_validation/family_a/family_a_fryer_live_diagnosis_micro_refinement_status_v1.md)
- [family_a_product_annotation_shell_micro_structure_status_v1.md](05_validation/family_a/family_a_product_annotation_shell_micro_structure_status_v1.md)
- [family_a_bottom_text_finalization_status_v1.md](05_validation/family_a/family_a_bottom_text_finalization_status_v1.md)
- [family_a_fryer_hero_footer_blocker_removal_status_v1.md](05_validation/family_a/family_a_fryer_hero_footer_blocker_removal_status_v1.md)
- [family_a_fryer_truth_parity_and_footer_caption_closeout_status_v1.md](05_validation/family_a/family_a_fryer_truth_parity_and_footer_caption_closeout_status_v1.md)
- [family_a_fryer_anchor_rebind_and_left_rebalance_status_v1.md](05_validation/family_a/family_a_fryer_anchor_rebind_and_left_rebalance_status_v1.md)
- [family_a_single_primary_support_surface_status_v1.md](05_validation/family_a/family_a_single_primary_support_surface_status_v1.md)
- [bottom_behavior_contract_status_v1.md](05_validation/bottom_behavior_contract_status_v1.md)
- [product_region_annotation_contract_status_v1.md](05_validation/product_region_annotation_contract_status_v1.md)
- [catalog_hero_1to1_replication_gap_review_v1.md](05_validation/catalog_hero_1to1_replication_gap_review_v1.md)
  PPT 1:1 gap review (task `POSTER2-CATALOG-HERO-1TO1-REPLICATION-P1`): scores current catalog_hero_v1 (synthetic
  assets) ~3.0/5 vs the Technitalia reference; implemented grammar ~4.4; real-asset ceiling ~4.3–4.7. Classifies
  every missing dimension (asset / template / typography-color / impossible-without-assets) and concludes the gap
  is asset-bound, not grammar-bound. Analysis only.
- [catalog_hero_p1_hardening_acceptance_v1.md](05_validation/catalog_hero_p1_hardening_acceptance_v1.md)
  Pre-deploy P1 gate for catalog_hero_v1: real-asset static trial ≥4.3, storage/poster_record parity, authenticated
  live render, visual scorecard, Family A/B-unchanged proof, no Stage3 mutation, no runtime AI asset, Owner approval.
  HOLD for deploy until all pass. Docs-only.
- [poster2_route_decision_matrix_v1.md](05_validation/poster2_route_decision_matrix_v1.md)
  Scores routes A (PPT 1:1), B (Product Sheet), C (Catalog Hero) across visual ceiling, controllability,
  operator usability, asset dependency, renderer complexity, risk, repeatability, and ability to reach 4.8;
  verdict = compose them (C spine + A extractor + B anchor). Docs-only.
- [catalog_hero_to_4_8_gap_plan_v1.md](05_validation/catalog_hero_to_4_8_gap_plan_v1.md)
  The 4.27 → 4.8 gap plan: levers (cooked on-theme red food asset + production parity dominate; callout
  radial-ring + logo minor), phased path (P1a port R1/R2/R3 → P1b asset gate → P1c runtime parity → P2 fidelity
  → P3 Reference→Seed), and the five acceptance gates. Docs-only.
- [hybrid_vs_replication_route_review_v1.md](05_validation/hybrid_vs_replication_route_review_v1.md)
  Compares the reference-inspired hybrid route vs strict 1:1, deterministic Catalog Hero, Family B, and fully
  free AI; finds hybrid combines B's control + D's visual quality (generated scene) while guaranteeing
  text/logo/product via deterministic overlay; recommends it as the main 4.8 path (additive mode). Docs-only.
- [hybrid_generation_mvp_plan_v1.md](05_validation/hybrid_generation_mvp_plan_v1.md)
  The minimum experiment: 1 product line (CUISTANCE fryers), 1 style target (Technitalia grammar), 3–5
  generated scene candidates + deterministic overlay, before/after vs deterministic Catalog Hero, ≥4.3 +
  beats-baseline + 100% text accuracy + operator approval; operator review form; needs Owner authorization of a
  generation model before running. Docs-only.
- [hybrid_real_asset_mvp_result_v1.md](05_validation/hybrid_real_asset_mvp_result_v1.md)
  Real-asset MVP execution + route verdict (task `POSTER2-HYBRID-REAL-ASSET-MVP-HEAVY-VALIDATION-V1`). Parsed the
  target `.eml` (Technitalia "LES RÉCHAUDS GAZ" via Cuistance). **Verdict: HYBRID_MVP_BLOCKED_BY_MODEL_ACCESS**
  (no generation credentials; no external call attempted) + a truth-vs-asset mismatch (email=gas stoves,
  kit=fryers). A fallback static composition (real scene-photo bg proxy + deterministic overlay) passes all hard
  gates, indicative ~4.1 (≈ tie with deterministic Catalog Hero), capped by the proxy. Deterministic-overlay
  firewall validated; generative half untested. Next: unblock generation + resolve mismatch, then re-trial. No
  production code touched; artifacts under `assets/hybrid_real_asset_mvp_v1/`.
- [family_b_announcement_visual_gap_review_v1.md](05_validation/family_b_announcement_visual_gap_review_v1.md)
  Multimodal gap review (task `POSTER2-VISUAL-GRAMMAR-REPLICATION-HEAVY-SLICE-V1`): scores the live Family B
  announcement output (~4/10) against the Technitalia reference and the proven catalog_hero_v1 reconstruction
  (4.47/5) across the 12 grammar dimensions; finds the 4/10 is a *grammar-mismatch* (wrong archetype), with the
  damage concentrated in archetype / focal hierarchy / asset relationship / evidence-annotation / color — not CSS
  surface. Verdict: **keep Family B as Product Sheet only** (do not upgrade its grammar); productize campaign-grade
  announcements through the additive portrait Catalog Hero family. Analysis only; no runtime code changed.
- [scenario_region_resolver_and_renderer_parity_status_v1.md](05_validation/scenario_region_resolver_and_renderer_parity_status_v1.md)
- [text_layer_contract_closure_status_v1.md](05_validation/text_layer_contract_closure_status_v1.md)

Family B historical validation remains under the same validation path and is not reopened by current Family A work:

- [template_b_backend_generation_fix_status_v1.md](05_validation/template_b_backend_generation_fix_status_v1.md)
- [template_b_contract_correction_status_v1.md](05_validation/template_b_contract_correction_status_v1.md)
- [template_b_design_baseline_v1.md](05_validation/template_b_design_baseline_v1.md)
- [template_b_parity_and_visual_contract_status_v1.md](05_validation/template_b_parity_and_visual_contract_status_v1.md)

### 99 Archive

- [session_state_2026-03-31.md](99_archive/session_state_2026-03-31.md)

## Active Working State

- [current_branch_execution_log_v1.md](current_branch_execution_log_v1.md)
  Branch execution/state log. This is the active state file for current branch progress, merge-path notes, migration notes, and short-lived working facts.

## Legacy Nonformal Paths

Older grouped directories such as `01_architecture/`, `02_engineering/`, `03_stage_assessment/`, `04_external_reference/`, and `05_next_phase_plan/` may still exist as historical material in this workspace.

They are no longer the formal doc path.
The formal doc path is defined only by:

- this root index
- the root product baseline
- the root execution log
- the layered directories listed above

## Current Alignment

- `AGENTS.md` is rules only
- `CLAUDE.md` is shared state only
- this file is index only
- branch-local progress belongs in `current_branch_execution_log_v1.md`

## Current Mainline

- current temporary priority override = none; Family A fryer truth-parity and footer-caption closeout is merged into the current baseline
- Template A remains the active oracle line for shared-skill and commercial acceptance verification
- Template B remains unchanged during the current Family A-only refinement pass
