# Family B Product Announcement — Operator UI Closure Validation v1

> **Task:** `POSTER2-FAMILY-B-ANNOUNCEMENT-OPERATOR-UI-CLOSURE-V1`.
> **Branch:** `poster2-family-b-announcement-ui-closure-v1`. **Date:** 2026-06-15.
> Makes the already-implemented announcement variant operable from the existing Stage1/Stage2 frontend flow.
> No Stage3 / send change; no new template family; no Poster Set runtime.

## Artifacts

- `stage1_or_stage2_input_screenshot.png` — Stage1 Family B form filled (Cuistance sample), incl. the new
  「新品公告信息」 fieldset.
- `stage2_request_preview_screenshot.png` — Stage2 page (review surface).
- `final_poster.png` — 1024×1024 backend render of the same announcement payload (Pillow operator path).
- `diagnostics.json` — backend evidence (`announcement_variant_contract_review`, etc.).
- `sample_payload.json` — the `/api/v2/generate-poster` body shape the UI produces.
- `ui_validation_result.json` — automated browser-validation results (visibility, fill, snapshot capture).
- Repro: `PYTHONPATH=. ./.venv/bin/python scripts/poster2_announcement_ui_validation.py` (browser) and
  `POSTER2_VALIDATION_OUT=docs/poster2/assets/announcement_ui_closure_v1 PYTHONPATH=. ./.venv/bin/python scripts/poster2_announcement_runtime_validation.py` (backend render).

## What was implemented (frontend, mirrored to docs/)

- **Stage1** (`index.html`): a Family-B-only fieldset `#s1-template-b-announcement` (`data-variant-visible="b"`)
  with `availability_badge`, a single `tariff_on_request` checkbox (→ `tariff_mode=on_request`; **no price entry**),
  `on_poster_cta_label`, `on_poster_cta_email`.
- **app.js**: state defaults/reads/rehydrate; `collectStage1Data` + `serialiseStage1Data` carry the 4 fields;
  `buildTemplateBPosterPayload` + the `/api/v2/generate-poster` Template B `posterPayload` map them to the request.
- **Stage2** (`stage2.html` + app.js): read-only summary fields `#s2-b-availability` / `#s2-b-tariff` / `#s2-b-cta`;
  request summary (`stage2_request_helpers.js`) surfaces the fields.
- Mirrored to `docs/` via `scripts/sync_frontend_to_docs.sh`; sync check passes.

## Automated browser validation (Playwright, static frontend, mocked endpoints)

`ui_validation_result.json` (key results):

- **Visibility:** `announcement=true, topcopy=true, description=true`; `familyA_bottom=false, familyA_callouts=false`.
  → The announcement fields appear **only** for Family B; Family A controls do not leak in.
- **Fill:** all four announcement fields hold the entered Cuistance values (`EN STOCK`, tariff checked,
  `Nous contacter`, `commercial@cuistance.eu`) plus SKU.
- **Stage1 → snapshot:** the persisted Stage1 `sessionStorage` snapshot (the exact object Stage2's
  `buildTemplateBPosterPayload` consumes) contains `availability_badge="EN STOCK"`, `tariff_mode="on_request"`,
  `on_poster_cta_label="Nous contacter"`, `on_poster_cta_email="commercial@cuistance.eu"`.
- **Console:** no JS errors — only resource 404 / DNS for unrelated remote assets/health-probe in the offline
  static context (not script errors).

## Answers to the required questions

- **Can an operator fill the announcement fields from UI?** **Yes** — proven by the Stage1 screenshot and the
  automated fill/read-back.
- **Do existing Template B fields still work?** **Yes** — SKU / title / subtitle / description / materials /
  product image are unchanged and populate normally (visible in the screenshot; existing Family B tests still pass).
- **Does Family A remain unaffected?** **Yes** — the new fields are gated by `data-variant-visible="b"`; Family A
  bottom + callouts stay visible only for A and hidden for B; no Family A code path was changed.
- **Did the final poster include the new fields?** **Yes** — `diagnostics.json` →
  `announcement_variant_contract_review.new_copy_slots`: availability_badge, tariff_line (on_request),
  on_poster_cta_text all `rendered=true`; visible in `final_poster.png` (EN STOCK, Tarif : nous contacter,
  Nous contacter · commercial@cuistance.eu).
- **Did diagnostics prove display-only CTA and materials collapse?** **Yes** —
  `on_poster_cta_text`: `render_kind=display_text_only`, `cta_action_bound=false`, `stage3_send_untouched=true`;
  `materials_strip_region`: `collapsed_by_design=true`, `reason_code=materials_not_used_in_announcement_variant`.
- **Is the result ready for human operator validation?** **Yes** (UI flow ready for human validation) — the
  operator can select Family B, fill the announcement fields, and they flow to the backend and render.
- **What remains as visual polish only?** Product prominence / whitespace in the wide hero card (template-geometry
  bound, out of scope); the Pillow availability badge renders as accent text rather than a filled chip; optional
  Stage1 live-preview chips for the new fields.

## Honest limitation (item 5 — literal request capture)

The automated test proves the field path **through the persisted Stage1 snapshot** (the exact data Stage2 reads)
and the backend render of that payload. It did **not** capture the literal `/api/v2/generate-poster` request body,
because the Stage2 generate flow performs multi-base backend health-probing + asset upload that is impractical to
fully mock offline (the abort happens before the POST). The snapshot→request mapping is pure, reviewed code
(`buildTemplateBPosterPayload` + `posterPayload`) that mirrors `sku_text` exactly — and `sku_text` is the proven
working Template B field that already reaches this backend. Backend acceptance + render of all four fields is
independently proven by `tests/poster2/test_pipeline.py`, `test_api.py`, and `final_poster.png`/`diagnostics.json`.
A live end-to-end UI→backend generate is the natural step for the Owner's human validation with a running backend.

## Verdict

**UI flow ready for human validation.** Operator can fill the announcement fields from the existing Stage1/Stage2
Family B flow; the fields persist into the Stage1 snapshot Stage2 consumes; the backend renders them and emits the
expected diagnostics; Family A and normal Template B (empty announcement fields → collapse-by-design) are unaffected.
