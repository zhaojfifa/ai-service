# CUISTANCE v1 · PSD 邮件容器 last-mile 状态 v1

Purpose: Result/status of the controlled last-mile engineering baseline — frozen source → PSD/ttt/ttt2 manifests →
deterministic PSD email container (`cuistance_email_container_psd_v1`) → Workbench-truth-driven Step-3 preview →
operator screenshots. Companion to the decision doc `cuistance_psd_email_container_last_mile_decision_v1.md`.
Status: Phases 0–3 PASS (local REAL-backend, `was_stubbed=false`). Real email send remains HOLD.
Scope: design-shell extraction + additive email-layer container; Workbench remains the only business truth source.
NO renderer contract change; NO backend send-behavior change; NO main merge; NO tag push.

Task: `POSTER2-CUISTANCE-PSD-EMAIL-CONTAINER-LAST-MILE-HEAVY-V1`.

---

## 1. Branch / rollback

- Working branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1` (off `ae5e527`).
- Rollback commit: `ae5e527`; rollback tag (local, NOT pushed): `poster2-cuistance-asset-chain-pass-ae5e527`.
- Commits this run: `d34e315` (Phase 0 freeze) · `13b8c47` (Phase 1 parse) · `ebdfea7` (Phase 2 container) · Phase 3
  (this commit).
- Rollback commands documented in the decision doc.

## 2. Phase 0 — freeze (PASS)

`~/poster/ingredient/` (7 files) frozen into
`docs/poster2/assets/cuistance_psd_email_container_last_mile_v1/source/` with `inventory/source_sha256.txt` +
`inventory/source_inventory.json`. No runtime change.

## 3. Phase 1 — parse (PASS)

- `scripts/poster2_cuistance_psd_inventory.py` (psd_tools 1.17.2, dev-only venv) → canvas **600×1577**, **49 layers**,
  **21 rejected_truth layers**, **6 regions**, **5 replaceable slots**; `psd_flat_reference.png` +
  `psd_slice_overlay_debug.png`.
- `scripts/poster2_cuistance_email_html_inventory.py` (stdlib only) → **ttt.html → product_sheet_email**,
  **ttt2.html → campaign_poster_email**; third-party tracking detected in source (list-manage / campaign-image /
  zcsclwgt) and explicitly NOT copied.
- Rejected truth: LES RÉCHAUDS GAZ, XR 1444 / 4 BRULEURS, gas kW/dimensions/PUISSANCE specs, NOTRE COUP DE COEUR,
  old phone `01 41 53 12 12`, old email line, CATALOGUES / SITE IN TERNET, old product/scene rasters — all
  `runtime_allowed=false`.
- Replaceable slots → Workbench truth: brand_logo_slot ← `workbench.email_banner.logo`; body_visual_slot ←
  `workbench.selected_email_body_visual…final_poster.url`; contact_email/phone/website ← `workbench.contact.*`.

## 4. Phase 2 — deterministic email container (PASS)

`cuistance_email_container_psd_v1` is the existing deterministic 600px email assembly tagged + format-mapped
(additive, email-layer only — NO renderer change). The assembly region order matches the PSD slice manifest
(header band + red filet → body visual → intro → CTA → contact → legal footer). `POST /email/preview` now returns
`email_container_template_id`, `email_fill_format` (affiche→campaign_poster_email, fiche→product_sheet_email), and
an `email_container` evidence block (`header_source=psd_slice_manifest`, `legacy_truth_rejected=true`,
`workbench_truth_used=true`, `uses_current_selected_visual=true`, `body_visual_poster_key`). Backwards-compatible
(new optional response fields). Tests: `tests/poster2/test_workbench_psd_email_container.py` (container fields +
no-legacy-gas-leakage) — PASS; 25 email/assembly tests PASS.

## 5. Phase 3 — CUISTANCE trial integration (PASS, REAL backend, non-stubbed)

Operator flow (real `app.main`, Playwright, no stubbing): Step 1 sample+save → backend gallery/assets persisted →
Step 2 affiche generate → select (backend-confirmed `affiche`) → Step 3 `campaign_poster_email` preview using
`cuistance_email_container_psd_v1` (HTTP 200) → hard refresh → recover from Workbench truth → re-preview → inline
send (preview_only, not real). Evidence (`evidence.json`): all `flow_validation` true;
`email_container.legacy_truth_rejected=true` / `workbench_truth_used=true` /
`no_body_content_in_header_banner=true` / header+body+cta+footer present; `refresh_recovery_ok=true`;
`real_email_sent=false`, `inline_only_not_claimed_as_real_send=true`.

Operator screenshots (`operator_screenshots/`): 01 source inventory · 02 psd layer/composite · 03 html reference
inventory · 04 slice manifest overlay · 05 step1 assets saved · 06 step2 affiche generated · 07 selected visual
confirmed · 08 step3 PSD email container preview · 09 refresh recovery preview · 10 send semantics (no real send).

## 6. Architecture rules upheld

Workbench is the only business truth source; PSD/ttt/ttt2 are design-shell/reference only; old Technitalia/
Codimatel/Gaz facts never enter runtime (21 rejected layers; assembly has no legacy fact); `selected_email_body_
visual` stays backend-confirmed; Stage 3 consumes live backend payload; `sessionStorage`/`localStorage` cache only;
real send HOLD; no generic PSD parser/editor; no renderer contract change; existing `/cuistance_trial.html`
asset-chain behavior preserved (no regression — pre-existing generate-poster/stage3.html test failures verified
identical on baseline with changes stashed).

## 7. Evidence

- Master: `docs/poster2/assets/cuistance_psd_email_container_last_mile_v1/evidence.json` (`was_stubbed=false`).
- Manifests: `manifest/psd_layer_inventory.json`, `psd_slice_manifest.json`, `rejected_truth_layers.json`,
  `html_reference_inventory.json`.
- Operator flow: `operator_flow_evidence.json` + `operator_screenshots/01–10`.

## 8. Remaining blockers / Owner decision needed

- Remote operator validation pending deploy + OPS creds (local REAL-backend validation only this run).
- Real email send remains HOLD (no provider; inline_only/preview_only correctly not real-sent).
- `psd_tools` was installed into the isolated `.venv` for analysis only (NOT in runtime `requirements.txt`) — Owner
  decision if PSD re-parsing should ever run in CI.
- Tag push / main merge withheld pending Owner authorization.

STATUS: PSD EMAIL CONTAINER LAST-MILE — PHASES 0–3 PASS (local), SUBMITTED FOR OWNER REVIEW.
