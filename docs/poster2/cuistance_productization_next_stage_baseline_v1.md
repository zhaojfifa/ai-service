# CUISTANCE Productization — Next-Stage Baseline v1

Status: **roadmap / contract baseline only** — no product features implemented in this document or task.
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1` @ `032b946`.
Builds on `cuistance_dual_mode_single_product_baseline_v1.md` and `cuistance_clean_baseline_packet_v1.md`.

## 1. Current accepted routes (verified)

- **Affiche / `campaign_poster_email`** — target poster route: a standalone composite poster embedded into the email
  body as a no-inner-banner visual; the email container header is the deterministic `ttt_html_header` wordmark.
- **Fiche / `product_sheet_email`** — single-product product sheet email: built from Workbench truth (product image +
  specs + description + CTA + footer); **no poster generation, no `poster_key`**.

Both PASS; the email fill format always follows `selected_email_body_visual`; mismatches are rejected.

## 2. Current NON-scope (not implemented; do not start without a new owner task)

- Real send (HOLD).
- Multi-product email (requires a future `products[]` contract).
- Git history rewrite.
- `ai-service-clean` export.
- Public customer deployment.

## 3. Productization Direction A — material input flexibility

Make business material inputs explicit, validated, and separable from rendered/visual assets.

- **logo input** — brand mark for the email header/banner module.
- **product image input** — primary product image(s) (`product_images[]` = images of ONE product).
- **gallery input** — supporting/secondary product images.
- **atmosphere input** — lifestyle/scene image (Affiche route only).
- **reference email/html input** — design shell reference (e.g. `ttt.html` / `ttt2.html` / PSD) — design only, not truth.
- **product truth input** — `product_name`, `reference`, `description`, `parameters[]` (specs).
- **contact input** — footer/contact block fields.
- **asset validation** — each input validated for presence/type/size before it can drive generate/preview.
- **truth vs visual asset separation** — business truth (Workbench `product_truth`) is authoritative and must never be
  mutated by a visual/reference asset or by copy optimization.

## 4. Productization Direction B — email container flexibility

A module/slot-based 600px email container, with the body visual chosen by route.

- **`single_product_campaign_email`** — today's Affiche (`campaign_poster_email`).
- **`single_product_sheet_email`** — today's Fiche (`product_sheet_email`).
- **`multi_product_grid_email`** — FUTURE; requires `products[]`.
- **`catalog_digest_email`** — FUTURE; requires `products[]`.
- **container width 600px** — email-safe table shell.
- **module system** — banner / title+intro / selected_body_visual / product_description / cta / contact_footer / legal_footer.
- **slot system** — the selected body visual enters ONLY through the planned `selected_body_visual` slot.
- **header/body/footer separation** — header is `ttt_html_header` (no body/product/CTA/footer content); body carries the
  route visual; footer carries contact/legal. No double header.

## 5. Productization Direction C — operator editability

Operator-facing editability, always gated by business truth.

- **editable title**, **editable intro**, **editable CTA** label.
- **editable spec visibility/order** — choose which `parameters[]` rows show and in what order (values are truth, not editable copy).
- **main product image selection** — pick which `product_images[]` entry is the primary body image.
- **email container selection** — pick the route/container (Affiche vs Fiche today).
- **preview before send** — a backend preview must be generated before any send is allowed.
- **truth gate before preview/send** — required truth (product name/reference + ≥1 product image) must be present;
  edits to presentation never override `product_truth`.

## 6. Contract boundaries (must hold)

- `product_images[]` means **multiple images of ONE product**, not multiple products.
- `products[]` is **required** for any future multi-product layout; absence of it must never be inferred as multi-product.
- reference **HTML/PSD is design shell only** — never a source of business truth.
- **Workbench truth is business truth** (authoritative; optimizer/visual assets cannot change it).
- `send_attempt` is **historical only** (evidence of past sends; never the current body source).
- `selected_email_body_visual` is the **current body truth** (drives fill format and preview/send).

## 7. Next recommended phase (do NOT start in this task)

```
POSTER2-PRODUCTIZATION-P1-MATERIAL-INPUT-AND-CONTAINER-CONTRACT
```

Scope intent (for a future task): formalize the material-input contract (Direction A) and the email-container
module/slot contract (Direction B section names) WITHOUT implementing multi-product, real send, or operator editing —
i.e. contract + validation first, behavior later.
