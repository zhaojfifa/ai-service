# Family B — Product Announcement Variant Contract v1

> **STATUS: SUPERSEDED.** The canonical Product Announcement variant contract is now
> [`family_b_product_announcement_variant_contract_v1.md`](family_b_product_announcement_variant_contract_v1.md)
> (task `POSTER2-FAMILY-B-ANNOUNCEMENT-VARIANT-CONTRACT-V1`). That doc is grounded in the full Family B
> contract-correction / line-2 evidence and uses the real Family B payload field names. This file is kept only
> as the earlier short sibling; do not treat it as the formal contract.

> **Status:** docs-only contract spec. **No runtime/template/registry/API/Stage3 code is written by this document.**
> **Owner gate (2026-06-15):** approved as docs-gated next work under the
> `catalog_campaign_poster_set_orchestration_spec_v1.md` direction.
> **Parent:** `catalog_campaign_poster_set_orchestration_spec_v1.md`.
> **Grounding:** `05_validation/template_b_design_baseline_v1.md`,
> `05_validation/template_b_parity_and_visual_contract_status_v1.md`,
> `real_email_to_poster_grammar_assessment_v1.md`.
>
> **Field/id names below are PROPOSED for a future contract, not committed API or schema.**

---

## 1. Purpose & scope

Define the contract for the **Product Announcement** poster variant (variant **C** in the orchestration
spec) on the **reactivated Family B** template `template_product_sheet_v1`.

This is the **first implementation candidate** of the Catalog Campaign Poster Set, chosen because it is the
*smallest* spec poster and rides almost entirely on the **already-existing** Family B template.

**In scope:** the bundle→slot map for Announcement; the three new copy slots; required/optional + collapse
rules; diagnostics; fallback/parity; the Announcement vs. Featured-Spec boundary.

**Out of scope (explicit):** the structured spec-table (deferred to Featured Spec); any geometry/region/
ownership change; portrait Catalog Hero; Stage3 email; `.eml` HTML as a template; freeform editing.

---

## 2. Reactivate, do not redesign

Family B is **dormant ("historical validation, not reopened"), not greenfield.** This contract **reopens** it
under the standing contract-first rules; it does **not** redesign it.

**Frozen Family B region order is preserved exactly** (from `template_b_parity_and_visual_contract_status_v1`):

1. `logo_banner_region`
2. `top_copy_region`
3. `materials_strip_region`
4. `product_hero_region`
5. `description_region`

Hard preservation rules (inherited, not re-litigated):

- contract-first; renderer executes, renderer does not define truth;
- no Family A geometry/behavior change; no Family B **region-order** change;
- no scenario / feature-callout reintroduction into Family B;
- product bounds/fit resolved via the existing `product_policy` authority (not redefined here);
- `header_mode = logo_banner_lockup` unchanged.

---

## 3. Variant identity & routing

```yaml
announcement_variant:
  variant_id: family_b_product_announcement     # proposed closed-enum id
  template_binding: template_product_sheet_v1   # existing Family B template (reused)
  family: B
  run_path: existing_single_poster_contract_path # one resolve per variant; orchestration never renders
  renderer: puppeteer_primary_pillow_fallback    # unchanged dual-renderer model
```

The variant is produced through the **existing per-poster generation path** (the same path already covered by
`generate_poster_v2_accepts_template_b`). The orchestration layer only supplies a projected single-poster input
and reads back the result; it does not introduce a new render endpoint.

---

## 4. Bundle → slot map

The shared campaign bundle (orchestration spec §3) is the truth source. The Announcement variant **projects a
subset** into existing Family B slots. It never owns input truth.

| Bundle field | Family B slot / region | Status | Notes |
|---|---|---|---|
| `brand.logo` | `brand_logo_slot` / `logo_banner_region` | EXISTS | reuse unchanged |
| `brand.brand_name` | banner brand lockup / `logo_banner_region` | EXISTS | reuse |
| `brand.agent_name` | subordinate agent chip / `logo_banner_region` | EXISTS | optional; suppressed-agent path already handled |
| `product.reference_sku` | `sku_text_slot` / `top_copy_region` | **EXISTS** | the SKU slot already exists (`sku_text`); map directly |
| `copy.headline` | title line / `top_copy_region` | EXISTS | dominant line |
| `copy.subtitle` | subtitle line / `top_copy_region` | EXISTS | optional, quieter |
| `product.product_image` | primary hero / `product_hero_region` | EXISTS | single dominant hero; bounds via `product_policy` |
| `product.product_detail_image` | secondary inset / `product_hero_region` | EXISTS | optional inset detail card (not a 2nd hero) |
| `copy.description` | `description_body_layer` / `description_region` | EXISTS | calm support copy |
| `copy.feature_claims[0]` | `description_title_layer` or claim line / `description_region` | EXISTS | one grounded ✔ claim for Announcement |
| `commercial.availability` | **`availability_badge_slot`** | **NEW** | see §5.1 |
| `commercial.tariff_mode` | **`tariff_line_slot`** | **NEW** | see §5.2 |
| `commercial.cta_label` + `commercial.cta_email` | **`cta_text_slot`** | **NEW** | see §5.3 |
| `spec.rows` | — | **EXCLUDED** | spec-table is Featured-Spec only (§7) |
| `range.images` | — | **EXCLUDED** | Product Matrix variant only |

---

## 5. The three new copy slots

All three are **text/copy slots inside frozen Family B regions** — **no new top-level region, no geometry
change, no ownership drift, no `materials_strip_region` repurpose.** Each follows the existing
requested → sanitized → rendered evidence chain and the existing char/line budget machinery.

### 5.1 `availability_badge_slot`

- **Owner region:** `top_copy_region` (adjacent to SKU/title hierarchy).
- **Input:** `commercial.availability` (free text, e.g. "EN STOCK", "DISPONIBLE").
- **Type:** short label; single line; tight char budget (proposed ≤ 16 chars), ellipsis on overflow.
- **Required:** optional. **Collapse:** absent input → slot collapses by design (not a structure failure).
- **Style:** small emphasis chip via the shared `palette_token` accent; no new geometry.

### 5.2 `tariff_line_slot`

- **Owner region:** `top_copy_region` or `description_region` (decision §9.2; default `top_copy_region`).
- **Input:** `commercial.tariff_mode` ∈ `{price, on_request}`.
  - `on_request` → renders the standing phrase ("Tarif = Nous contacter" equivalent; copy via sanitizer).
  - `price` → renders the operator-supplied price string (future bundle field; not required for v1 if only
    `on_request` is supported first — see §9.3).
- **Type:** single line; bounded budget; ellipsis on overflow.
- **Required:** optional. **Collapse:** absent/empty → collapses by design.

### 5.3 `cta_text_slot`

- **Owner region:** `description_region` footer edge (poster body), **not** a Stage3 action.
- **Input:** `commercial.cta_label` (e.g. "Nous contacter") + `commercial.cta_email` (mailto display).
- **Semantics:** **copy/display only.** It renders CTA *text* and the contact email **on the poster**. It does
  **not** trigger, configure, or alter any Stage3 send. The actual email send remains the existing closure path,
  untouched.
- **Type:** single line label + email; bounded budget.
- **Required:** optional. **Collapse:** absent → collapses by design.

---

## 6. Required vs optional & structure-completeness

Mirrors the Family A/B presence model (`required` / `optional` / `collapsed_by_design`).

| Slot | Requirement |
|---|---|
| `brand_logo_slot` | required |
| title (`copy.headline`) | required |
| primary hero (`product.product_image`) | required |
| `sku_text_slot` | required for Announcement (a "NOUVEAUTÉ" announcement always carries a reference) |
| subtitle, description, claim | optional |
| `availability_badge_slot`, `tariff_line_slot`, `cta_text_slot` | optional, `collapsed_by_design` when absent |
| secondary inset (`product_detail_image`) | optional |

**Structure-completeness rule:** the Announcement poster is a **structure failure** only if a *required* slot
is missing (logo, title, primary hero, SKU). Missing optional slots are `collapsed_by_design` and must **not**
appear in `missing_mandatory_slots`. No silent excuse for missing required slots (conservative, like Family A).

---

## 7. Announcement vs. Featured Spec boundary

The **structured spec-table** (Dimensions / Volume / Puissance / Référence as labeled `{label,value}` rows) is
**excluded from Announcement.** Announcement carries at most one grounded claim line + optional prose
description. The spec-table is the one genuinely-new contract and belongs to the **Featured Spec** variant,
gated on its own contract doc. Announcement must not back-door a spec-table into `description_region` or
`materials_strip_region`.

---

## 8. Text budgets, sanitization, product geometry (all reused)

- **Sanitization:** all copy passes through the existing poster-facing sanitization + grounded-claim rejection
  + Gemini/deterministic optimizer **before** the variant consumes it. No new copy engine.
- **Budgets:** reuse existing per-slot char/line budget + truncation machinery; the three new slots declare
  their own bounded budgets (above).
- **Product geometry:** primary hero + secondary inset bounds/fit come from the existing `product_policy`
  authority. This contract introduces **no product geometry**.

---

## 9. Fallback / degraded / parity

- **Renderer:** Puppeteer primary → Pillow fallback (unchanged). Contract is the single truth source; both
  engines consume the same resolved truth.
- **Parity:** reuse the existing `template_b_parity_review` + `visible_truth_evidence` (header_in_banner,
  top_copy_in_region, hero_in_region, description_in_region, parity_failure_reasons, per-target containment). The
  three new slots must be added to the Family B target map so DOM visible-truth parity covers them; otherwise
  their evidence goes stale (known Family B risk).
- **Degraded:** visible and explainable; a degraded render must say so in evidence (standing rule).

---

## 10. Diagnostics — `announcement_variant_contract_review`

Mirror the existing evidence shape (`bottom_contract_review`, `product_annotation_contract_review`,
`template_b_parity_review`) — **no new diagnostics philosophy.** Per the orchestration spec, each variant emits
its **own** review (separate diagnostics per poster).

Proposed fields:

```yaml
announcement_variant_contract_review:
  variant_id: family_b_product_announcement
  template_binding: template_product_sheet_v1
  structure_complete: bool
  missing_mandatory_slots: [string]
  slots:                       # one entry per mapped slot
    - slot_id: string
      requested_text: string
      sanitized_text: string
      rendered_excerpt: string
      rendered: bool
      truncation_applied: bool
      collapsed_by_design: bool
      reason_code: string
      source: string           # bundle-field provenance
  new_copy_slots:              # explicit visibility for the 3 additions
    availability_badge: {requested, sanitized, rendered_excerpt, rendered, collapsed_by_design}
    tariff_line:        {mode, requested, sanitized, rendered_excerpt, rendered, collapsed_by_design}
    cta_text:           {label, email, rendered_excerpt, rendered, collapsed_by_design,
                         note: "display only; not a Stage3 send"}
  renderer_path: string
  degraded: bool
  parity_review_ref: template_b_parity_review   # reference, not a merge
  poster_key: string                            # existing closure, reused read-only
```

---

## 11. Compliance checklist

| Hard rule | Status |
|---|---|
| No runtime code implemented | ✅ docs-only |
| Reactivate-not-redesign Family B | ✅ frozen region order + existing slots reused; new = 3 text slots |
| No Family B region-order / geometry / ownership change | ✅ |
| No Family A change | ✅ |
| No bottom SOP / product annotation truth change | ✅ (Family B has neither bottom-gallery nor anchor-callout truth in this path) |
| No Stage3 email redesign | ✅ `cta_text_slot` is display-only copy |
| No `.eml` HTML as template | ✅ evidence only; assets operator-supplied |
| No spec-table here | ✅ deferred to Featured Spec |
| Each variant runs the existing single-poster path | ✅ |
| Separate diagnostics per poster | ✅ `announcement_variant_contract_review` |

---

## 12. Open decisions

1. Confirm `availability_badge_slot` owner = `top_copy_region` (recommended) vs. banner.
2. Confirm `tariff_line_slot` owner region (default `top_copy_region`).
3. v1 supports `tariff_mode = on_request` only, or both `on_request` + `price` from the start?
   (Recommended: `on_request` first — it is the only mode in the evidence.)
4. Confirm `cta_text_slot` placement at `description_region` footer edge.
5. Confirm the three new slots are added to the Family B parity target map (recommended — avoids stale
   visible-truth evidence).
