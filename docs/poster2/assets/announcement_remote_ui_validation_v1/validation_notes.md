# Family B Announcement — Remote UI Fill Validation v1

> **Task:** `POSTER2-FAMILY-B-ANNOUNCEMENT-REMOTE-UI-FILL-VALIDATION-V1`.
> **Branch:** `poster2-family-b-announcement-ui-closure-v1`. **Date:** 2026-06-15.
> Goal: make the announcement UI operator-clear (operators were typing generic product text into it), then verify.
> **Code changed:** frontend label/placeholder/help/grouping copy + a small visual-distinction CSS only. No backend
> schema, no renderer geometry, no mapping change.

## Artifacts

- `stage1_filled_correct_values.png` — Stage1 with the improved 「公告展示条 · Announcement strip」 fieldset, filled.
- `stage2_summary_correct_values.png` — Stage2 read-only summary showing the four announcement values.
- `generate_request_payload.json` — the `/api/v2/generate-poster` body the UI builds (announcement fields included).
- `generate_response_diagnostics.json` — backend `announcement_variant_contract_review` evidence.
- `final_poster.png` + `final_poster_page_screenshot.png` — rendered poster + a result-view panel.
- `remote_build_info.json` — deployed build-info (see live note below).
- `ui_validation_result.json` — automated browser checks (label assertions, fill, Stage2 summary, snapshot).

## What changed (UI clarity)

- Stage1 fieldset relabeled to **「公告展示条 · Announcement strip」** with a prominent warning: *these are short
  poster display labels (库存 / 报价 / 联系) — **not** product description; do not enter product names/titles.*
- Bilingual field labels: **库存徽标 · Availability badge**, **报价行 · Tariff line** (checkbox = show
  `Tarif : nous contacter`), **联系按钮文案 · CTA label**, **联系邮箱 · CTA email**.
- Placeholders now the exact examples (`EN STOCK`, `Nous contacter`, `commercial@cuistance.eu`) — not product names.
- Removed prior `邮件 / Stage3 / 发送` wording; CTA email is described as *display-only poster text*.
- Visual distinction: red left-accent card + tinted warning box (so it doesn't read like the product copy fields).
- Stage2 summary labels clarified (库存徽标 · Availability badge / 报价行 · Tariff line / 联系文案 · CTA (海报文字)).
- No price input exists (tariff is a single on_request checkbox).

## A. Local/static UI validation (Playwright, mocked endpoints)

`ui_validation_result.json`:
- **Labels:** `Announcement strip`, `不是产品描述`, `Availability badge`, `Tariff line`, `CTA label`, `CTA email`
  all present; **no send/Stage3 wording**. (Self-check flagged the word "价格" — that is the clarifying note
  "不显示具体价格"; **there is no price input field**.)
- **Placeholders:** `EN STOCK` / `Nous contacter` / `commercial@cuistance.eu` (correct examples).
- **Stage1 fill:** all values entered.
- **Stage1 snapshot** (the object Stage2 consumes): `availability_badge=EN STOCK`, `tariff_mode=on_request`,
  `on_poster_cta_label=Nous contacter`, `on_poster_cta_email=commercial@cuistance.eu`.
- **Stage2 summary** (read-only): `Availability=EN STOCK`, `Tariff=按需报价 (Tarif : nous contacter)`,
  `CTA=Nous contacter · commercial@cuistance.eu`, `SKU=311011 (RC10L)` → **Stage2 preserves the values**.

## B. Live remote validation (deployed Render)

- The deployed backend is **current code** (the prior gap was redeployed): `/openapi.json` now contains
  `availability_badge`, `tariff_mode`, `announcement_variant_contract_review`, and the served `/index.html` has the
  announcement fieldset. (`remote_build_info.json` still reads `kit1.0/0cbaf65` — that static file is stale; the
  running code is current per OpenAPI.)
- **Live authenticated generate could not be executed from here:** `POST /api/v2/generate-poster` returns
  **`401 ops_auth_required`** (the deployed service enforces ops auth; no production credentials are available in
  this environment). The literal live POST capture + live final-poster screenshot are therefore the **Owner's
  authenticated step**. The exact verification to run while logged in:
  1. Confirm Network `POST /api/v2/generate-poster` body has `availability_badge=EN STOCK`, `tariff_mode=on_request`,
     `on_poster_cta_label=Nous contacter`, `on_poster_cta_email=commercial@cuistance.eu`.
  2. Confirm the response has `announcement_variant_contract_review` with the three slots `rendered=true`,
     `cta_action_bound=false`, `stage3_send_untouched=true`.
- **Backend render proof (local, real pipeline + contract code)** — `generate_response_diagnostics.json`:
  `structure_complete=true`; `new_copy_slots.availability_badge.rendered=true`,
  `new_copy_slots.tariff_line.rendered=true (mode on_request)`, `new_copy_slots.on_poster_cta_text.rendered=true`,
  `cta_action_bound=false`, `stage3_send_untouched=true`, `materials_strip_region.collapsed_by_design=true`.
  `final_poster.png` visibly shows **EN STOCK**, **Tarif : nous contacter**, **Nous contacter · commercial@cuistance.eu**.

## Answers to the required questions

1. **UI labels/placeholders clear enough?** **Yes** — bilingual labels, an explicit "not product description"
   warning, example placeholders, a visually distinct card.
2. **Could the operator fill the exact sample without ambiguity?** **Yes** — each field names its purpose and shows
   the exact example; the strip is clearly separated from the product copy fields.
3. **Did Stage2 preserve the values?** **Yes** — the Stage2 summary displays all four values (screenshot + assertion).
4. **Did live POST send the values?** **Local:** the values reach the Stage1 snapshot Stage2 POSTs from, and the
   mapping (`buildTemplateBPosterPayload`→`posterPayload`) is unchanged/verified; the remote backend accepts these
   fields (OpenAPI). **Live authenticated POST is the Owner step** (401 ops_auth_required here).
5. **Did backend diagnostics render the three slots?** **Yes** — all three `rendered=true` with the correct
   excerpts; CTA is display-only.
6. **Did the final poster show EN STOCK / Tarif / CTA?** **Yes** — visible in `final_poster.png`.
7. **Ready for Owner human validation?** **Yes** — the UI is now unambiguous; the Owner runs the authenticated live
   generate to capture the production Network body + final poster.
8. **Remaining UI copy nits?** Minor: could pre-validate that `on_poster_cta_email` looks like an email (display-only,
   so not enforced); the availability badge renders as accent text rather than a filled chip in Pillow (visual polish,
   out of scope). None block operator validation.

## Compliance

Frontend copy + minimal CSS only. No backend schema change (the deployed backend already accepts the fields — the
issue was UI clarity, not mapping). No renderer geometry, no Stage3/email/send, no price, no phone/contact footer,
no Poster Set runtime, no Family A / bottom SOP / product-annotation change, no merge, not pushed/deployed.
