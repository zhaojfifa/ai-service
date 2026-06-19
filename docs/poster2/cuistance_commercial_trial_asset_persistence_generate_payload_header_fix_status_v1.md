# CUISTANCE v1 · 素材持久化 / 生成载荷 / 页眉素材修复 v1

Purpose: Make Step 1 asset state reliably reach backend workbench truth and the Step 2 generation payload, fix the
selected-state confirmation, and correct the email header/banner asset boundary.
Status: submitted for Owner review — **local REAL-backend browser verification PASS** (`was_stubbed=false`).
Scope: Frontend + asset-generation. NO renderer/email-provider/send-behavior change; NO backend API change.
No real email sent.
Source dependencies: `frontend/cuistance_trial.html` (+ `docs/cuistance_trial.html` mirror); existing v1 endpoints;
`scripts/poster2_cuistance_header_band_assets.py` (new header band assets).
Owner gate: Owner review; remote browser validation with OPS auth (deploy + creds gated).

Task: `POSTER2-CUISTANCE-V1-ASSET-PERSISTENCE-GENERATE-PAYLOAD-AND-HEADER-ASSET-FIX`.

---

## 1. Root cause

`ensureWorkbench()` early-returned `if(S.wb)return true;` — so once a workbench existed, **Step 1 "save" never
re-PATCHed assets**. Any gallery/atmosphere/asset edit made after the first save (or after Command+R recovery) was
dropped, leaving `product_assets.gallery_images=[]` in backend truth even though the UI showed them — exactly the
Owner-observed `wb_9308b112feb0436e` state. Separately, `banner_option_02.jpg` was **1080×720** (a 3:2 image, not a
header strip), so cover-cropping it into the email header showed body/product content.

## 2. Fixes (frontend + assets — backend unchanged)

1. **Step 1 asset persistence.** `ensureWorkbench()` now creates the workbench if needed and then **ALWAYS PATCHes
   the latest product_truth + assets** (product_images[0..1], gallery_images[0..2], atmosphere{is_truth:false},
   email_banner.logo/background/selected_banner_ref). After saving it GETs the workbench and, if the UI has gallery
   slots but backend returns `gallery_images=[]`, shows `素材未保存成功，请重新保存产品与素材` and blocks. Diagnostics
   record the persisted counts.
2. **Generate payload from backend truth.** Before generating, `ensureWorkbench()` persists + verifies, then
   `genVisual` GETs the workbench and records `generation_assets` (product_images_count / gallery_images_count /
   atmosphere_present / logo_present / banner_background_present). Generation never runs from stale in-memory state.
3. **Step 2 preview = current generated poster.** After generation, GET candidate poster_key →
   `GET /api/v2/posters/{poster_key}` → render `final_poster.url`; diagnostics record `generated_poster_key`. The
   current poster is never conflated with old `send_attempts` evidence (send_attempts are historical only).
4. **Selected state after regeneration (deterministic).** Regenerating the currently-selected mode **clears the
   selection** (`clearSelection()` → require re-click). The UI shows selected only when backend GET confirms
   `selected_email_body_visual` == clicked mode. For the Owner's `ready + selected=null` state the card reads
   `产品海报已生成，请选择为邮件主体` (never `已选为邮件主体`).
5. **Header/Banner asset correction.** New header-only band assets `assets/header_band_01.png` (brand 品牌页眉) and
   `assets/header_band_02.png` (campaign 活动页眉), both 1200×200 (6:1 strip, charcoal + wordmark + red filet, no
   product/body/CTA/footer). Step 3 options, the format→header map (campaign→band_02, product_sheet→band_01), the
   header preview, the static email mock, and 使用示例素材 all use these. The header strip is also CSS-constrained
   (`max-height:108px`, `object-fit:cover`).
6. **Step 3 preview uses corrected header.** Before preview the header is persisted (`PATCH`), so the assembled
   header uses `email_banner.background` = header band; the assembled HTML is inspected and diagnostics record
   `selected_banner_ref`, `banner_background_url`, `header_boundary_valid`, `no_body_content_in_header_banner`,
   preview_contains_header/body_visual/cta/footer.
7. **Validation check.** `scripts/check_email_fill_format_alignment.py` extended (advisory) to verify
   `header_band_01/02.png` are header strips (aspect ≥ 3:1) and no third-party tracking is copied.

No raw ttt/ttt2 HTML or tracking copied; no forbidden engineering terms on the visible UI.

## 3. Files changed

- `frontend/cuistance_trial.html` — `ensureWorkbench` always-persist + verify; `genVisual` backend-confirmed asset
  counts + `clearSelection` on regen; ready-hint `请选择为邮件主体`; header band assets wired everywhere; per-format
  header map. `docs/cuistance_trial.html` mirror.
- `frontend/assets/header_band_01.png`, `frontend/assets/header_band_02.png` (+ `docs/assets/` mirror) — new
  header-only band assets.
- `scripts/poster2_cuistance_header_band_assets.py` — header band generator.
- `scripts/check_email_fill_format_alignment.py` — header-only + tracking advisory checks.
- `scripts/poster2_cuistance_asset_persistence_header_proof.py` — REAL-backend Playwright proof (no stubbing).
- **Backend: unchanged.**

## 4. REAL-backend browser verification (local, non-stubbed)

Real `app.main` backend; real page; Playwright NO route stubbing. Artifacts:
`docs/poster2/assets/cuistance_asset_persistence_generate_payload_header_fix_v1/` (01–09 + evidence.json).

| # | File | Proves |
|---|------|--------|
| 01 | step1_gallery_selected | gallery slots selected in Step 1. |
| 02 | workbench_after_save_gallery_persisted | gallery persisted; re-save persists a changed field. |
| 03 | step2_generation_with_asset_counts | generation from backend-confirmed assets (counts in diagnostics). |
| 04 | step2_current_generated_poster_not_old_send_attempt | current poster bound; selection still null (not falsely selected). |
| 05 | step2_selected_visual_confirmed | selection backend-confirmed (affiche), poster_key matches current candidate. |
| 06 | step3_header_options_corrected | header options are clean header bands (品牌页眉 / 活动页眉). |
| 07 | step3_final_preview_correct_header | preview = header band + selected poster body + copy + CTA + footer. |
| 08 | send_preview_only_if_run | inline_only/preview_only → not real sent. |
| 09 | diagnostics_asset_payload_header_evidence | counts / poster_key / boundary in diagnostics only. |

Evidence JSON (`evidence.json`): `was_stubbed=false`; product_images_count_after_save=2; **gallery_images_count_
after_save=2**; atmosphere_present_after_save=true; logo_present_after_save=true; banner_background_present_after_
save=true; selected_banner_ref=option_1; resave_field_persisted=true; resave_gallery_still_present=true;
generation_product_images_count=2; generation_gallery_images_count=2; generation_atmosphere_present=true;
generated_poster_key set; final_poster_url_present=true; selected_email_body_visual_before_select=null;
selected_email_body_visual_after_select=affiche; selected_poster_key_matches_current_candidate=true;
old_send_attempt_poster_key_ignored_for_current_selection=true; banner_option_01_header_only=true;
banner_option_02_header_only=true; no_body_content_in_header_banner=true; header_boundary_valid=true;
banner_background_url_is_header_band=true; preview_http_status=200; final_preview_rendered=true;
preview_contains_header/body_visual/cta/footer=true; send_provider=inline_only/send_status=skipped/
send_error_code=preview_only/provider_message_id_present=false/real_email_sent=false; ui_send_label_correct=true.

Validation: `check_docs_router.py --all` PASS; `check_email_fill_format_alignment.py` PASS (header bands 6:1 header-
only; no tracking); inline JS syntax OK; main-UI forbidden-term + fallback scan NONE. Backend untouched → no backend
tests run.

## 5. Remaining blockers / non-blockers

- Remote browser validation pending deploy + OPS creds (validation only; proven on a real backend locally with
  `was_stubbed=false`).
- Transitional: the affiche body visual still bakes its own banner into the poster image (documented in
  assembly.py); the email-level header band is separate and the boundary check confirms the header strip excludes
  the body visual. Fiche real generation needs Vertex Imagen3; real send needs a provider + provider_message_id.

## 6. Recommendation

**GO** — selected gallery images persist to backend truth (and survive re-save); generation runs from
backend-confirmed assets; the current generated poster is bound (not old send_attempt evidence); selection is only
shown when backend confirms it; header/banner assets are header-only and correctly mapped; the final preview uses
the corrected header + selected body visual. Remote confirmation remains, gated on deploy + OPS creds.

STATUS: ASSET PERSISTENCE GENERATE PAYLOAD HEADER FIX SUBMITTED FOR OWNER REVIEW.
