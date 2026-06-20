# CUISTANCE Dual-Mode Single-Product Baseline v1

Status: **ACCEPTED BASELINE** (frozen for single-product scope)
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`
Owner decision: dual-mode single-product baseline accepted; multi-product NOT in current scope.

## 1. Currently supported modes

The CUISTANCE operator trial supports exactly two email body visual modes, each bound to one email fill format:

| Mode (UI) | Email body visual | Email fill format | Route |
| --- | --- | --- | --- |
| **Affiche** (目标海报模式) | `affiche` | `campaign_poster_email` | Target poster route — generated campaign poster (composite), embedded with no inner banner. |
| **Fiche** (简单产品页模式) | `fiche` | `product_sheet_email` | **Single-product product sheet email** — deterministic, built from Workbench truth (no poster generation, no `poster_key`). |

Both modes are accepted as PASS. The email fill format always follows the selected email body visual
(`affiche → campaign_poster_email`, `fiche → product_sheet_email`); a mismatch is rejected.

## 2. `product_sheet_email` means single-product only

`product_sheet_email` currently renders **one product**: header (ttt_html_header CUISTANCE wordmark) + that product's
image + title/reference + specs (`product_truth.parameters`) + description + CTA + footer. It does not render, group,
or compare multiple distinct products.

## 3. `product_assets.product_images[]` = multiple images of ONE product

`product_assets.product_images[]` is a gallery of **images of a single product** (primary + secondary views), not a
list of different products. The fiche body visual uses the first product image; additional images are alternate views
of the same product. There is no per-product identity, pricing, or per-product copy in the current contract.

## 4. Multi-product support requires a future `products[]` contract

Rendering multiple distinct products in one email is **out of scope** and is intentionally NOT implemented. It would
require a new explicit contract, e.g. a top-level `products[]` array where each entry carries its own
name/reference/image(s)/specs/copy — distinct from today's single `product_truth` + `product_images[]`. Until that
contract exists, the platform must not infer "multiple products" from multiple images.

## 5. Future layout families (not implemented — naming reserved)

When multi-product is opened in a future scope, the intended layout families are:

- `single_product_sheet_email` — today's Fiche (one product). The current `product_sheet_email` maps here.
- `multi_product_grid_email` — several products in a grid/card layout (requires `products[]`).
- `catalog_digest_email` — a longer catalog/digest of many products (requires `products[]`).

These names are reserved for design alignment only; no behavior is wired today.

## 6. Real send remains HOLD

Real email send is **HOLD**. Preview and inline send paths only; no provider send is performed by default
(`real_email_sent=false`). This baseline does not change real send.

## 7. Cleanup audit may start after this baseline

With this baseline recorded, an evidence/asset **cleanup audit** may begin. The audit is documentation-only — it
classifies existing evidence without deleting or moving any file. See:

- `docs/poster2/cleanup_audit_v1.md`
- `docs/poster2/assets_cleanup_inventory_v1.json`
- `docs/poster2/large_files_report_v1.txt`
- `docs/poster2/keep_candidates_v1.md`
- `docs/poster2/archive_candidates_v1.md`
- `docs/poster2/delete_candidates_v1.md`

## Related lineage (accepted PASS evidence)

- `docs/poster2/assets/cuistance_psd_email_container_last_mile_v1/remote_last_mile_fix/fiche_product_sheet_email_closure_v1/` — Fiche closure (no poster runtime).
- `docs/poster2/assets/cuistance_psd_email_container_last_mile_v1/remote_last_mile_fix/fiche_selection_preview_truth_fix_v1/` — Fiche selection/preview truth fix.
