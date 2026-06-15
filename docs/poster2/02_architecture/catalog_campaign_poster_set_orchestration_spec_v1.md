# Catalog Campaign Poster Set — Orchestration Architecture Spec v1

> **Status:** **APPROVED (Owner, 2026-06-15)** — docs-only architecture spec; the approved product direction
> for real-email-derived poster generation. **No runtime/template/registry/API/Stage3 code is written by this document.**
> Approved invariants (Owner): the orchestration layer sits above Family A / Family B; it does **not** render;
> it does **not** own geometry; it does **not** change bottom SOP; it does **not** change product annotation truth;
> it does **not** redesign Stage3 email; each poster variant must still run through the existing single-poster
> contract path. Next approved work is docs-gated only — (1) Family B Announcement Variant Contract,
> (2) Campaign Manifest + Variant Selection Contract — both authored as sibling specs in this directory.
> **Owner decision (2026-06-15):** APPROVE *Catalog Campaign Poster Set* as the next product direction.
> First implementation candidate = **Product Announcement / Family B reactivation**.
> Hard owner constraints: do **not** implement runtime code yet · do **not** build the portrait Catalog Hero
> mega-poster now · do **not** redesign Stage3 email · do **not** use `.eml` HTML as a runtime template.
>
> **Source of truth for the grammar evidence:** `real_email_to_poster_grammar_assessment_v1.md`.
> This spec turns that assessment into a formal Poster2 product architecture.

---

## 0. Reading path / anchors

- Product baseline: `poster_generation_product_design_baseline_v1.md` (two-family model, three-layer governance).
- Family A architecture: `02_architecture/template_dual_v2_architecture_business_definition.md`.
- Family B current state: `05_validation/template_b_design_baseline_v1.md`,
  `05_validation/template_b_parity_and_visual_contract_status_v1.md`.
- Grammar evidence: `real_email_to_poster_grammar_assessment_v1.md`.
- Catalog Hero (DEFERRED): `template_classification_v1.md`, `reference_analysis_v1.md`.
- Contract/diagnostics pattern to mirror: `05_validation/bottom_behavior_contract_status_v1.md`,
  `05_validation/product_region_annotation_contract_status_v1.md`,
  `composition_priority_layer_review_v1.md` (shared-token-bundle pattern).

---

## 1. Product definition

A **Catalog Campaign Poster Set** is:

> **one shared product input bundle → an operator-selected set of 1..N *simple* poster variants →
> each variant resolved through its own existing template/family, under one shared visual language,
> with a per-variant contract and per-variant diagnostics, rolled up under one campaign manifest.**

It is explicitly **not**:

- a new renderer or a new template engine,
- a single "does-everything" mega-poster (hero + spec + matrix + CTA fused into one image),
- a freeform editor or a Stage3/email redesign,
- a consumer of `.eml` HTML at runtime.

The core architectural move is **fan-out, not fusion**: the richness a real catalog email shows
(see the `coup de chaud` email folding Hero Explanation + Product Matrix into one image) is
re-expressed as **several simple posters from one shared bundle**, never as one over-complex template.

### 1.1 Why this is the right shape (from the evidence)

- The three `NOUVEAUTÉ` emails proved a **stable, repeatable** single-product Product-Sheet grammar:
  one ESP template reused across blender / coupe-frites / cuiseur à riz. Each is **one simple poster**.
- The `coup de chaud` email is a **folded set** (hero explanation + product matrix). Decomposing it into
  simple variants is exactly the Poster Set model.
- Poster2 already governs single-poster generation contract-first (request → normalize →
  resolver-as-truth → renderer → evidence → operator review) for both Family A and Family B. The Poster Set
  is a **coordinator above that proven single-poster path**, reused once per variant.

---

## 2. Layer position (where orchestration sits)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  CAMPAIGN ORCHESTRATION LAYER  (NEW — this spec)                           │
│  • shared product input bundle (canonical truth)                          │
│  • variant selection + resolution rules                                   │
│  • shared visual-language token bundle (non-geometric)                    │
│  • campaign manifest + per-variant roll-up diagnostics                    │
└───────────────┬───────────────────────────────┬──────────────────────────┘
                │ fan-out: one resolve per variant │
                ▼                               ▼
   ┌───────────────────────┐        ┌───────────────────────┐
   │ Family B Product Sheet │        │ Family A (gallery/strip│   … existing
   │ template_product_sheet │        │ for Product Matrix)    │   families,
   │ (Announcement / Spec)  │        │                        │   UNCHANGED
   └───────────┬───────────┘        └───────────┬───────────┘
               │ existing per-poster contract path (unchanged)
               ▼                               ▼
        renderer (Puppeteer → Pillow fallback)  ·  contract = single truth source
               │
               ▼
        per-poster evidence  +  poster_record  (existing closure, reused read-only)
```

**Invariants:**

1. The orchestration layer **never renders**. It composes inputs and reads results. Renderers and
   per-poster contracts are untouched.
2. Each variant is produced through the **existing single-poster generation path** (conceptually one
   `generate-poster` resolve per variant). No new render endpoint is required for v1.
3. Families A and B keep their frozen region order, ownership, `product_policy`, annotation truth,
   and bottom SOP. The orchestration layer has **no authority** to mutate them.

---

## 3. Shared product input bundle (canonical truth)

The bundle is the **single source of truth** for the whole campaign. Each variant *projects* a subset of
it into its template slots; variants never own input truth. (This mirrors the standing rule: resolver/
contract is truth, the surface is a projection.)

> **Schema below is a docs-only conceptual model.** Field names are proposals for a future contract doc,
> not committed API.

```yaml
campaign_bundle:                      # CANONICAL TRUTH
  campaign_key: string                # roll-up id (assigned at generate-time, like poster_key)
  brand:
    logo: asset_ref
    brand_name: string
    agent_name: string                # optional agent/distributor identity
    palette_token: enum               # shared visual-language bundle id (see §6)
  product:
    product_name: string
    product_type: string              # e.g. "CUISEUR À RIZ PROFESSIONNEL"
    reference_sku: string             # e.g. "311011 (RC10L)"  -> Family B SKU slot (EXISTS)
    product_image: asset_ref          # hero / packshot (operator-supplied; never hot-linked .eml)
    product_detail_image: asset_ref?  # optional in-use / detail (img2 role)
  spec:
    rows:                             # ordered labeled spec rows (NEW contract — see §5.3)
      - {label: "Dimensions", value: "L485 x P420 x H400 mm"}
      - {label: "Volume",     value: "10 L cuit / 6 L sec"}
      - {label: "Puissance",  value: "1,8 kW / 220-240 V"}
  commercial:
    tariff_mode: enum[price, on_request]   # "Tarif = Nous contacter" => on_request (NEW slot)
    availability: string?                  # e.g. "EN STOCK" / "DISPONIBLE" (NEW badge slot)
    cta_label: string                      # e.g. "Nous contacter" (on-poster text only)
    cta_email: string                      # mailto target shown on poster (NOT Stage3 send)
  copy:
    headline: string                  # e.g. "NOUVEAUTÉ ! …"
    subtitle: string?
    description: string?              # prose support copy (Family B description_region)
    feature_claims: [string]          # ✔ confirmation lines (sanitized, grounded)
  range:                              # for Product Matrix variant (deferred standalone)
    images: [asset_ref]
    captions: [string]
  variant_selection: [enum]           # which posters to emit (see §4)
```

**Rules:**

- All product imagery is **operator-supplied through Stage1 slots**, exactly as today. The bundle never
  references remote `.eml` image URLs (hot-linked, expirable, no alt) — see risk §9.
- Copy fields pass through the **existing sanitization + grounded-claim rejection + Gemini/deterministic
  optimizer** before any variant consumes them. No new copy engine.
- The bundle is **additive** over the current Stage1 Core Assets set; nothing in the existing single-poster
  input model is removed.

---

## 4. Variant catalog (simple posters)

Each variant is a **simple** poster that projects a subset of the bundle. Variants are closed-enum; there is
no freeform composition.

| Variant | Bundle subset projected | Target family | v1 status |
|---|---|---|---|
| **C. Product Announcement** | brand · product (name/type/sku/image) · headline · 1 claim · availability · cta_label/email | **Family B** (`template_product_sheet_v1`) | **FIRST — this spec's implementation candidate** |
| **B. Featured Spec** | C + `spec.rows` + description + product_detail_image | **Family B** (+ spec-table module) | next, after spec-table contract approved |
| **D. Product Matrix / Catalog Strip** | brand · range.images/captions | **Family A** bottom gallery (`title_gallery_split` / `gallery_only_expanded`, ≤4) | deferred; reuses existing gallery as a strip |
| **A. Hero Explanation** | brand · scenario · product · callouts · title | **Catalog Hero (portrait)** | **DEFERRED / GATED** — owner said do not build now |
| **E. CTA / Contact** | brand · commercial | — | **NOT a poster** — footer module only; do not extract as a standalone poster |

**Set composition (typical):** a real campaign emits **Announcement (C)** alone, or **Announcement (C) +
Featured Spec (B)**, or later **(C) + (B) + Matrix (D)**. Hero Explanation (A) stays out of v1 sets.

---

## 5. First implementation candidate — Product Announcement (Family B reactivation)

> Implementation is **not started**. This section defines the *first slice* for a future approved build.

### 5.1 Why Announcement first

- It is the **smallest** spec poster and rides almost entirely on the **already-existing** Family B
  template (`template_product_sheet_v1`), which is contract-valid, API-routable, has parity diagnostics,
  and already owns: `logo_banner_region`, `top_copy_region` (with an **existing SKU slot**),
  `materials_strip_region`, `product_hero_region`, `description_region`.
- It defers the only structurally-new contract (the labeled **spec-table**) to the Featured Spec variant.

### 5.2 Family B reactivation — current state vs. needed

Family B is **dormant ("historical validation, not reopened"), not greenfield**. Reactivation re-opens an
existing line under the same contract-first rules; it is **not** a redesign.

| Need for Announcement | Family B today | Action |
|---|---|---|
| Brand banner + logo + agent | `logo_banner_region` / `logo_banner_lockup` (EXISTS) | reuse unchanged |
| Reference / SKU | `sku_text` / SKU slot in `top_copy_region` (EXISTS) | reuse; map `product.reference_sku` |
| Headline / title + subtitle | `top_copy_region` title/subtitle (EXISTS) | reuse; map `copy.headline` / `copy.subtitle` |
| Product hero (+ optional detail inset) | `product_hero_region` single-hero + secondary inset (EXISTS) | reuse; map `product.product_image` / `product_detail_image`; bounds via `product_policy` |
| Claim / support copy | `description_region` title+body (EXISTS) | reuse; map `copy.feature_claims` / `copy.description` |
| **Availability badge ("EN STOCK")** | none | **new optional copy slot** (text only, no geometry redesign) |
| **Tariff line ("Tarif = Nous contacter")** | none | **new optional copy slot** (closed enum `price | on_request`) |
| **On-poster CTA text ("Nous contacter")** | none | **new optional copy slot** (poster text + mailto display only; NOT a Stage3 send action) |

All three new items are **text/copy slots inside frozen Family B regions** — no new region, no geometry
change, no ownership drift, no `materials_strip` repurpose.

### 5.3 Featured Spec (next) — the one genuinely-new contract

The `NOUVEAUTÉ` spec block (Dimensions / Volume / Puissance / Référence as labeled rows) has **no current
home**: `description_region` is prose, `materials_strip_region` is sample cards. The Featured Spec variant
needs a **structured spec-table module**:

- ordered `{label, value}` rows, fixed max count, per-row char budget, collapse rules for missing rows;
- lives inside (or adjacent to) `description_region` ownership — **no new top-level region** unless a later
  decision approves one;
- resolver-derived bounds; renderer executes; Pillow parity required.

This is deferred until its contract is separately specified and approved.

---

## 6. Shared visual-language token bundle

To keep a Poster Set visually coherent, all variants in one campaign share a **non-geometric token bundle**,
modeled exactly on the proven **Composition Priority Layer** pattern (`composition_priority_layer_review_v1`):
a closed-enum, request-level CSS-var bundle merged **last** through the beauty channel, touching only
whitelisted non-geometry vars (accent tone, surface, shadow/lift, text rhythm).

- `palette_token` on the bundle selects one shared look (e.g. the Cuistance "industrial red on warm stone"
  Family-B token set already defined as `industrial_sheet_*`).
- The bundle is **additive and reversible**: the empty/`balanced` token yields a byte-identical base render.
- It **may not** change region geometry, ownership, `visible_item_count`, annotation truth, or bottom SOP.

---

## 7. Per-variant contract model

Each variant declares a contract that maps bundle fields → its template slots. The contract — not the
renderer, not the surface — is the truth source (standing rule).

A variant contract declares:

- **slot map:** bundle field → template slot (e.g. `product.reference_sku → sku_text_slot`);
- **required vs optional slots**, and **collapse rules** for missing optional inputs;
- **char/line budgets** per text slot (reuse existing budget machinery);
- **product bounds/fit** via `product_policy` (reused, not redefined);
- **fallback behavior** (Puppeteer → Pillow parity required; degraded must be visible/explainable);
- **structure-completeness rule** (which missing slots make the poster a structure failure vs. an accepted
  collapse) — mirroring Family A/B presence rules.

---

## 8. Per-variant + campaign diagnostics

Diagnostics mirror the existing evidence pattern (`bottom_contract_review`,
`product_annotation_contract_review`, `template_b_parity_review`) — **no new diagnostics philosophy**.

**Per variant** (`<variant>_contract_review`), reuse the requested → sanitized → rendered chain:

- per slot: `requested_text` / `sanitized_text` / `rendered_excerpt` / `rendered` / `truncation_applied` /
  `reason_code` / source provenance;
- `structure_complete`, `missing_mandatory_slots`, `collapsed_by_design`;
- renderer path used, `degraded` flag, parity (visible-truth) result;
- the variant's own `poster_record` / `poster_key` (existing closure, reused read-only).

**Campaign roll-up** (`campaign_manifest`):

- `campaign_key`, requested `variant_selection`, per-variant `{variant, poster_key, structure_complete,
  degraded, deliverable}`;
- which variants rendered / collapsed / failed (no silent drop — a skipped or failed variant is reported);
- the shared `palette_token` applied;
- **separate diagnostics per poster** (owner requirement) — the roll-up references, never merges, per-variant
  evidence.

---

## 9. Risk assessment

| Risk | Mitigation in this architecture |
|---|---|
| **Mega-template temptation** (fold everything into one poster) | Fan-out, not fusion: each variant is simple; richness comes from the *set*, not one template. |
| **Overfitting to one customer** (all evidence is Cuistance/Technitalia) | Spec-table is generic `{label,value}` rows; validate variants against ≥1 unrelated catalog before freezing; no Cuistance-specific fields. |
| **Remote `.eml` images / `.eml` HTML as template** | Bundle forbids hot-linked URLs; operator re-supplies assets via Stage1 slots; `.eml` HTML is evidence only (hard-forbidden honored). |
| **Family B reactivation regression** | Reactivate, don't redesign: reuse frozen region order + existing SKU/hero/description slots; new items are text slots only; reuse Family B parity diagnostics; Family A untouched. |
| **Portrait Catalog Hero scope creep** | Hero Explanation (A) stays out of v1 sets; portrait-canvas RegionDefinition remains a separate owner-gated decision. |
| **Editor-first drift** | Closed-enum variant selection + structured key/value inputs + contract-first resolver truth; no drag-and-drop, no freeform HTML/CSS. |
| **Stage3 entanglement** | On-poster CTA text/mailto display is **copy only**; the orchestration layer reuses the existing closure (`poster_record`, email/preview/send) **read-only** and does not modify Stage3. |
| **Silent partial sets** | Campaign manifest reports every requested variant's outcome; failed/collapsed variants are explicit, never dropped silently. |

---

## 10. Non-goals (explicit, this version)

- No runtime/template/registry/API/Stage3 code (docs-only).
- No portrait Catalog Hero mega-poster; no portrait-canvas RegionDefinition build.
- No Family A geometry, ownership, annotation-truth, or bottom-SOP change.
- No new render endpoint required for v1 (fan-out over the existing per-poster path).
- No freeform editor; no `.eml` HTML as a runtime template; no new copy engine.
- No structured spec-table build yet (deferred to the Featured Spec contract).

---

## 11. Phased roadmap (docs-gated)

1. **This spec** — orchestration architecture (Catalog Campaign Poster Set). ✅ (docs-only)
2. **Docs-next (no code):**
   - `Family B Announcement variant contract` doc — bundle→slot map, the 3 new copy slots
     (availability / tariff / CTA-text), required/optional + collapse rules, diagnostics shape.
   - `Campaign manifest + variant-selection contract` doc — roll-up schema, per-variant diagnostics
     reference model, shared `palette_token` rules.
3. **First implementation slice (only after the above docs are approved):** Product Announcement on
   reactivated Family B, single product, additive copy slots only; reuse `product_policy`, Family B parity
   diagnostics, and the existing per-poster generate path.
4. **Then:** Featured Spec variant — gated on a separate **spec-table module contract**.
5. **Later / separate gates:** Product Matrix standalone (D); Hero Explanation portrait family (A).

---

## 12. Open owner decisions remaining

1. Approve the **two docs-next contracts** (§11.2) before any code? (Recommended: yes.)
2. Confirm **Announcement-first, Spec-second** ordering (Recommended) vs. Spec-first.
3. Confirm the shared visual language reuses the **existing Family B `industrial_sheet_*` token set** as the
   first `palette_token`, vs. defining a new campaign palette.
4. Confirm the campaign roll-up reuses the **existing `poster_record` per variant** (one record per poster)
   vs. introducing a campaign-level record (Recommended: per-variant records + a thin manifest that
   references them; no Stage3 change).
5. Keep **portrait Catalog Hero** and **standalone Product Matrix** on separate later gates? (Recommended: yes.)

---

## 13. Governance / compliance checklist

| Hard rule | Status in this spec |
|---|---|
| No runtime code implemented | ✅ docs-only |
| No portrait Catalog Hero mega-poster now | ✅ A deferred/gated |
| No Stage3 email redesign | ✅ closure reused read-only; on-poster CTA is copy only |
| No `.eml` HTML as runtime template | ✅ evidence only; assets operator-supplied |
| No Family A geometry / ownership / annotation / bottom-SOP change | ✅ A untouched; orchestration has no render authority |
| No freeform editor / arbitrary HTML-CSS | ✅ closed enums + structured inputs + contract-first truth |
| Family B reactivation is reactivate-not-redesign | ✅ frozen region order + existing slots reused; new = text slots only |
| Per-variant separate diagnostics | ✅ `<variant>_contract_review` per poster; manifest references, never merges |
