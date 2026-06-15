# Family B — Product Announcement Variant Contract v1 (canonical)

> **Task:** `POSTER2-FAMILY-B-ANNOUNCEMENT-VARIANT-CONTRACT-V1`.
> **Status:** docs/design-only contract. **No runtime code, no template-spec edits, no renderer change, no
> template-registry change, no API change, no Stage3 change.**
> **Owner gate (2026-06-15):** Catalog Campaign Poster Set orchestration is approved as docs-only architecture;
> **runtime implementation is NOT approved yet.** This document defines the first implementable poster variant
> contract and then **stops for Owner approval of an implementation slice.**
>
> **Owner verdict (2026-06-15): APPROVE WITH REQUIRED CHANGES — doc-fix slice (no runtime).** This revision
> applies the four required review changes; the doc then returns for Owner approval before any runtime:
> 1. `structure_complete` must require a **Family B core information area** (see §6.1, §9, §10).
> 2. `materials_strip_region` collapse must be **explicit `collapsed_by_design` evidence** (see §7, §9).
> 3. **tariff v1 is `on_request` only** (`price` deferred) (see §5.2, §11).
> 4. `on_poster_cta_text` must **prove display-only / no Stage3 binding** (see §5.3, §9, §10).
> **Parent:** `catalog_campaign_poster_set_orchestration_spec_v1.md`.
> **Supersedes:** `family_b_announcement_variant_contract_v1.md` (earlier short sibling; folded into this canonical doc).
> **Grounding read:** `template_b_design_baseline_v1.md`, `template_b_contract_correction_status_v1.md`,
> `template_b_line2_independent_flow_status_v1.md`, `template_b_parity_and_visual_contract_status_v1.md`,
> `real_email_to_poster_grammar_assessment_v1.md`, `poster_generation_product_design_baseline_v1.md`.
> **Review source of the four required changes:** `../family_b_product_announcement_variant_contract_review_v1.md`.
>
> **All field / id names below are PROPOSED for a future contract — not committed API, schema, or template-spec.**

---

## 0. Reactivate, do not redesign (load-bearing principle)

Family B is **dormant ("historical validation, not reopened"), not greenfield.** The grounding docs prove
`template_product_sheet_v1` is already a clean, independent, contract-driven line:

- **Frozen region order** (`template_b_contract_correction_status_v1`, `_parity_…`):
  1. `logo_banner_region` 2. `top_copy_region` 3. `materials_strip_region` 4. `product_hero_region`
  5. `description_region`
- **header_mode = `logo_banner_lockup`**; `brand_logo_slot` renderable.
- Family B already emits its **own** contract reviews: `top_copy_contract_review` (layers `sku_text_layer`,
  `top_copy_title_layer`, `top_copy_subtitle_layer`), `description_contract_review` (`description_title_layer`,
  `description_body_layer`), and a `bottom_contract_review` scoped to `description_region_only`.
- It has an **independent Stage1 → Stage2 → `/api/v2/generate-poster` flow** with a dedicated serializer
  (`buildTemplateBPosterPayload`) carrying only B-relevant fields, with **Puppeteer disabled in the Template B
  renderer selector** (Pillow path in the operator line today).

This variant therefore **reactivates and projects onto** that existing line. It does **not** redesign the
template engine, the region order, ownership, geometry, or the renderer.

---

## 1. Product Announcement Variant — purpose

The **Product Announcement** variant is the **smallest** Catalog Campaign poster: a single-product "new arrival /
in stock" announcement. It is variant **C** in the orchestration spec and the **first implementation candidate**
because it rides almost entirely on the existing Family B template with only minor additive **copy** slots.

Its job: take one product from the shared campaign bundle and render a clean Family B product-sheet announcement —
brand banner, reference/SKU, headline, product hero, one grounded claim, and (new) availability / tariff /
on-poster contact text. It deliberately carries **no structured spec-table** (that is the *Featured Spec* variant)
and **no scenario / callout / gallery** (those are Family A).

---

## 2. Mapping to the real Cuistance `NOUVEAUTÉ` email grammar

Evidence (`real_email_to_poster_grammar_assessment_v1.md`): the three `NOUVEAUTÉ … CUISTANCE` emails are **one
Mailchimp template filled with three products** (blender / coupe-frites / cuiseur à riz). Their stable, repeated
body grammar maps cleanly onto Family B regions:

| `NOUVEAUTÉ` email module (poster body) | Example (cuiseur à riz) | Family B region |
|---|---|---|
| top brand banner | shared Cuistance banner | `logo_banner_region` |
| `Référence produit : <code>` | `311011 (RC10L)` | `top_copy_region` → `sku_text_layer` |
| `NOUVEAUTÉ ! <PRODUCT TYPE>` headline | `NOUVEAUTÉ ! CUISEUR À RIZ PROFESSIONNEL` | `top_copy_region` → `top_copy_title_layer` |
| product name (restated) / strapline | `CUISEUR À RIZ PROFESSIONNEL` | `top_copy_region` → `top_copy_subtitle_layer` |
| product hero image | rice-cooker packshot | `product_hero_region` (primary) |
| in-use / detail image | secondary image | `product_hero_region` (secondary inset) |
| description (materials, prose) | "Structure extérieure en acier inoxydable…" | `description_region` → `description_body_layer` |
| `✔` confirmation claim | "Cuiseur à riz professionnel 10 litres" | `description_region` → `description_title_layer` (one claim) |
| **availability ("EN STOCK / DISPONIBLE")** | "… DISPONIBLES EN STOCK …" | **NEW** `availability_badge` (§5.1) |
| **`Tarif = Nous contacter`** | tariff-on-request | **NEW** `tariff_line` (§5.2) |
| **`Nous contacter` + commercial@…** | mailto contact | **NEW** `on_poster_cta_text` (§5.3) |
| spec block (Dimensions / Volume / Puissance) | `L485×P420×H400 · 10 L` | **EXCLUDED** — Featured Spec only (§8) |
| email shell (forwarding, social, unsubscribe, tracking pixel) | — | **DISCARDED** — not poster content (§8) |

The **image-role skeleton** is also stable across the three emails (shared banner img0, unique product hero img1,
unique detail img2, shared footer logo img3, 1×1 tracking pixel). The variant consumes only the **two product
images** (hero + detail) from operator-supplied Stage1 slots — never the remote `.eml` URLs.

---

## 3. Required shared input fields (from the campaign bundle)

Projected from the canonical campaign bundle (orchestration spec §3). The bundle is the truth source; the variant
**projects**, it does not own input truth.

| Bundle field | Required for Announcement? | Notes |
|---|---|---|
| `brand.logo` | required | banner logo |
| `brand.brand_name` | required | banner brand lockup |
| `brand.agent_name` | optional | subordinate agent chip; suppressed-agent path already handled |
| `brand.palette_token` | optional | shared visual-language token (default = existing `industrial_sheet_*`) |
| `product.product_name` | required | drives title/strapline |
| `product.product_type` | required | headline subject |
| `product.reference_sku` | required | maps to existing `sku_text` |
| `product.product_image` | required | primary hero |
| `product.product_detail_image` | optional | secondary inset |
| `copy.headline` | required | dominant title line |
| `copy.subtitle` | optional | quieter strapline |
| `copy.description` | optional | prose support copy |
| `copy.feature_claims[0]` | optional | one grounded ✔ claim |
| `commercial.availability` | optional | → `availability_badge` |
| `commercial.tariff_mode` | optional | → `tariff_line` |
| `commercial.cta_label` + `commercial.cta_email` | optional | → `on_poster_cta_text` |

Excluded from this variant: `spec.rows` (Featured Spec), `range.images` (Product Matrix), any scenario / gallery /
feature-callout field.

> **Description copy core (review §4.1):** `copy.feature_claims[0]` and `copy.description` are individually
> optional fields, but **at least one must be present and render** — it supplies the mandatory `description_region`
> copy core required for `structure_complete` (§6.1). A submission with neither is a structure failure.

---

## 4. Required variant-specific fields

These are the fields the Announcement variant **declares as its own resolution inputs** (beyond raw bundle data),
all closed-enum / structured — **no freeform geometry, no editor input**:

| Variant field | Type | Purpose |
|---|---|---|
| `variant_id` | const `family_b_product_announcement` | closed-enum identity |
| `template_binding` | const `template_product_sheet_v1` | existing Family B template (reused) |
| `tariff_mode` | **v1: `on_request` only** (enum name reserves `price`, deferred) | selects the tariff line content; the only evidenced mode (§5.2) |
| `availability_present` | derived bool | whether `availability_badge` renders |
| `cta_present` | derived bool | whether `on_poster_cta_text` renders |
| `secondary_present` | derived bool | drives `single_hero_centered_without_secondary_asset` vs `…_with_secondary_inset` (existing reason codes) |
| `palette_token` | enum (shared) | non-geometric visual-language token (default existing `industrial_sheet_*`) |

---

## 5. Three minimal new copy slots

All three are **text/copy slots inside frozen Family B regions** — **no new region, no geometry change, no
ownership drift, no `materials_strip_region` repurpose.** Each follows the existing requested → sanitized →
rendered evidence chain and the existing char/line budget + truncation machinery, and each is **optional /
`collapsed_by_design`** when absent. All copy passes the existing sanitization + grounded-claim rejection +
Gemini/deterministic optimizer first.

### 5.1 `availability_badge`

- **Owner region:** `top_copy_region` (adjacent to the SKU/title hierarchy).
- **Input:** `commercial.availability` (e.g. "EN STOCK", "DISPONIBLE").
- **Type:** short single-line label, tight char budget (proposed ≤ 16), ellipsis on overflow.
- **Style:** small accent chip via the shared `palette_token`; no new geometry.
- **Collapse:** absent input → slot collapses by design (not a structure failure).

### 5.2 `tariff_line`

- **Owner region:** `top_copy_region` (default) or `description_region` (open decision §11.2).
- **Input:** `tariff_mode`. **v1 is `on_request` ONLY** (Required change 3 — Owner-decided 2026-06-15).
  - `on_request` → renders the standing on-request phrase (sanitized; e.g. the "Tarif = Nous contacter" sense).
    This is the **only** evidenced mode (all three `NOUVEAUTÉ` emails are `Tarif = Nous contacter`).
  - `price` → **DEFERRED, out of scope for v1.** Not a valid `tariff_mode` value in the v1 contract; a `price`
    request is rejected (no silent fallback) until a future revision adds a price bundle field + contract. The
    enum is documented as `{on_request, price}` only to reserve the name; **v1 accepts `on_request` exclusively.**
- **Type:** single line, bounded budget, ellipsis on overflow.
- **Collapse:** absent/empty `tariff_mode` → collapses by design.

### 5.3 `on_poster_cta_text`

- **Owner region:** `description_region` footer edge (poster body).
- **Input:** `commercial.cta_label` (e.g. "Nous contacter") + `commercial.cta_email` (mailto display).
- **Semantics — copy / display ONLY.** It renders CTA *text* and the contact email **on the poster image**. It
  does **not** trigger, configure, or alter any Stage3 send. The actual email send remains the existing closure
  path, fully untouched. (This is the explicit boundary that keeps the variant out of Stage3.)
- **Type:** single line label + email, bounded budget.
- **Collapse:** absent → collapses by design.
- **Provable display-only / no-Stage3-binding (Required change 4).** "Display-only" must be *demonstrated*, not
  merely asserted:
  - **Data boundary:** `on_poster_cta_text` derives from `commercial.cta_label` / `commercial.cta_email` purely as
    **render text**. It does **not** read from, write to, or reference any Stage3 field
    (`email/preview`, `email/send`, `attachment_types`, recipient, draft source, `email_assets`).
  - **No live link / no action:** the rendered output is **flat poster pixels** (text + the email *string*). The
    mailto is **displayed as text**, not wired as an actionable link, send trigger, or callback.
  - **Diagnostics proof:** the slot evidence must carry `render_kind: "display_text_only"`,
    `cta_action_bound: false`, and `stage3_send_untouched: true` (see §9; field names per review §4.4). The
    campaign closure (`poster_record`, `email/preview`, `email/send`) is reused **read-only** and is unchanged by
    the presence/absence of this slot.
  - **Acceptance proof:** the first-slice acceptance (§10) requires a no-change check demonstrating that rendering
    a poster **with** vs. **without** `on_poster_cta_text` produces **identical Stage3/closure behavior** (no send
    invoked, no closure field changed) — i.e. the slot is provably inert outside the poster image.

---

## 6. Existing Family B regions / slots reused (no change)

Reused **unchanged** from the validated Family B contract surface:

| Family B region | Reused slots / layers | Source of truth |
|---|---|---|
| `logo_banner_region` | `brand_logo_slot`, brand lockup, agent chip; `header_mode = logo_banner_lockup` | `header_contract_review` |
| `top_copy_region` | `sku_text_layer`, `top_copy_title_layer`, `top_copy_subtitle_layer` | `top_copy_contract_review` |
| `materials_strip_region` | framed sample cards (count-aware) | existing materials evidence |
| `product_hero_region` | `product_canvas_shell_layer` (full-width hero, w=800, bounds `{x:112,y:348,w:800,h:384}`), primary + secondary inset; `product_text_shell_layer` stays zero/`not_used_in_template_b`; reason codes `single_hero_centered_without_secondary_asset` / `…_with_secondary_inset` | product hero evidence; bounds via `product_policy` |
| `description_region` | `description_title_layer`, `description_body_layer`; `bottom_contract_review` scoped `description_region_only` | `description_contract_review` |

The three new copy slots (§5) attach **inside** `top_copy_region` and `description_region` — no new top-level
region is introduced.

### 6.1 Family B core information area (structure-completeness anchor) — Required change 1

`structure_complete` is **not** the conjunction of loose individual slots. It is anchored on a named **Family B
core information area** that must be present and rendered for the poster to count as structurally complete:

Per the Owner review (§4.1), the earlier `missing_mandatory_slots = {logo, title, primary hero, sku_text}` is
**too narrow** for Family B governance: a poster with only brand + SKU + headline + product image must **not**
pass while failing Family B's product-sheet/story completeness. Because Announcement excludes the spec-table,
the core must require a **copy-region core information slot** in `description_region`.

```yaml
family_b_core_information_area:
  required_members:                  # ALL must render for structure_complete == TRUE
    - logo_banner_region.brand_logo_slot     # brand / banner anchor
    - top_copy_region.sku_text_layer         # reference/SKU (mandatory for a "NOUVEAUTÉ" announcement)
    - top_copy_region.top_copy_title_layer   # headline / title
    - product_hero_region.primary            # the single dominant product hero
    - description_region.copy_core           # >=1 of {description_title_layer, description_body_layer} rendered
  description_copy_core:             # the "copy-region core" required by review §4.1
    satisfied_by_any_of:
      - description_title_layer      # from copy.feature_claims[0]
      - description_body_layer       # from copy.description
  rule: >
    structure_complete == TRUE only if brand_logo_slot, top_copy sku_text_layer, top_copy_title_layer,
    the primary product hero, AND at least one description_region copy-core layer all render.
    Any missing core member is a structure failure listed in missing_core_information_members.
  not_part_of_core:                  # optional; absence never fails structure
    - top_copy_subtitle_layer
    - availability_badge / tariff_line / on_poster_cta_text
    - materials_strip_region
    - product_hero_region.secondary
```

This makes `structure_complete` express "the Family B information core is intact" — brand anchor + top-copy
(SKU + title) + product hero + **at least one description copy core** — not merely "some slots rendered." It
supersedes the earlier loose phrasing wherever §6/§7 differ, and directly satisfies review §4.1.

---

## 7. Field → existing slot mapping (SKU / title / subtitle / materials / product / description)

Using the **real** Family B payload field names from `template_b_line2_independent_flow_status_v1` (the dedicated
Template B serializer carries exactly these):

| Bundle field (Announcement) | Real Family B field / slot | Region |
|---|---|---|
| `product.reference_sku` | **`sku_text`** → `sku_text_layer` | `top_copy_region` |
| `copy.headline` | **`title`** → `top_copy_title_layer` | `top_copy_region` |
| `copy.subtitle` (or `product.product_name` restated) | **`subtitle`** → `top_copy_subtitle_layer` | `top_copy_region` |
| `range`/materials evidence (announcement = none or sparse) | **`materials_images`** → `materials_strip_region` | `materials_strip_region` (optional; announcement typically omits) |
| `product.product_image` | **`product_image`** (a.k.a. `product_image_1`) → primary hero | `product_hero_region` |
| `product.product_detail_image` | **`product_secondary_image`** (a.k.a. `product_image_2`) → secondary inset | `product_hero_region` |
| `copy.feature_claims[0]` | **`description_title`** → `description_title_layer` | `description_region` |
| `copy.description` | **`description_body`** → `description_body_layer` | `description_region` |
| `commercial.availability` | **`availability_badge`** (NEW copy slot) | `top_copy_region` |
| `tariff_mode` | **`tariff_line`** (NEW copy slot) | `top_copy_region` |
| `commercial.cta_label` + `cta_email` | **`on_poster_cta_text`** (NEW copy slot) | `description_region` |

Note on **materials**: the `NOUVEAUTÉ` Announcement does not use a materials strip; `materials_images` stays
optional and **collapses with explicit `collapsed_by_design` evidence** for this variant (Required change 2; see
§9) — never a silent gap, never a structure failure, no repurpose into a spec-table or gallery.

---

## 8. Explicit non-goals

- **No new renderer.** Runs through the existing Family B render path (Pillow today; Puppeteer parity inherits
  existing Family B rules if/when enabled). Renderer executes contract truth; it does not define it.
- **No new template family.** Reuses `template_product_sheet_v1`. No portrait Catalog Hero; no mega-poster.
- **No new top-level region; no Family B region-order / geometry / ownership change.**
- **No structured spec-table here.** Dimensions / Volume / Puissance / Référence rows are the *Featured Spec*
  variant, gated on a separate spec-table contract. Announcement must not back-door a spec-table into
  `description_region` or `materials_strip_region`.
- **No Stage3 sending behavior.** `on_poster_cta_text` is display-only copy; the closure (`poster_record`,
  `email/preview`, `email/send`, attachments) is reused **read-only** and unmodified.
- **No email shell.** Forwarding chrome, social icons, unsubscribe, tracking pixels, ESP footers are discarded;
  they are never poster content.
- **No phone/contact footer module; no fourth copy slot.** The real `.eml` shows phone + email; Announcement v1
  displays only CTA label + email via `on_poster_cta_text`. A phone/contact footer is **deferred** and must not
  be added as a fourth slot without a new contract (review §5 / Owner decision §11.7).
- **No mega-poster.** Richness comes from the *Poster Set* (fan-out), not from one over-complex template.
- **No `.eml` HTML as runtime template; no editor-first / freeform geometry.** Closed enums + structured inputs
  only; assets operator-supplied via Stage1 slots.
- **No API / template-spec / registry edit by this document.**

---

## 9. Diagnostics requirements

Mirror the existing Family B evidence philosophy (`top_copy_contract_review`, `description_contract_review`,
`template_b_parity_review`) — **no new diagnostics model.** The variant emits its **own** review (separate
diagnostics per poster, per the orchestration spec).

Proposed `announcement_variant_contract_review`:

```yaml
announcement_variant_contract_review:
  variant_id: family_b_product_announcement
  template_binding: template_product_sheet_v1

  # Required change 1 — structure_complete is anchored on the Family B core information area (§6.1)
  structure_complete: bool
  core_information_area:
    members:                                 # each core member's render verdict (review §4.1)
      brand_logo_slot:        {rendered: bool}   # logo_banner_region
      sku_text_layer:         {rendered: bool}   # top_copy_region
      top_copy_title_layer:   {rendered: bool}   # top_copy_region
      product_hero_primary:   {rendered: bool}   # product_hero_region
      description_copy_core:   {rendered: bool, satisfied_by: enum[description_title_layer, description_body_layer]}
    intact: bool                             # ALL members above rendered (incl. >=1 description copy core)
  missing_core_information_members: [string] # populated when intact == false -> structure failure

  reused_slots:                              # requested -> sanitized -> rendered chain (existing shape)
    - {slot_id, requested_text, sanitized_text, rendered_excerpt, rendered, truncation_applied, source}

  # Required change 2 — materials collapse is explicit, never silent
  materials_strip_region:
    rendered: bool
    collapsed_by_design: bool                # true for Announcement when materials absent
    reason_code: string                      # e.g. "materials_not_used_in_announcement_variant"
    count: int                               # 0 when collapsed

  new_copy_slots:
    availability_badge: {requested, sanitized, rendered_excerpt, rendered, collapsed_by_design, reason_code}
    tariff_line:        {mode: "on_request", requested, sanitized, rendered_excerpt, rendered,
                         collapsed_by_design, reason_code}   # v1: on_request only (Required change 3)
    # Required change 4 — on_poster_cta_text proves display-only / no Stage3 binding
    on_poster_cta_text: {label, email, rendered_excerpt, rendered, collapsed_by_design, reason_code,
                         render_kind: "display_text_only", cta_action_bound: false, stage3_send_untouched: true}

  product_hero:
    layout_mode_reason: enum[single_hero_centered_without_secondary_asset, single_hero_centered_with_secondary_inset]
  renderer_path: string
  degraded: bool
  parity_review_ref: template_b_parity_review     # reference, not a merge
  poster_key: string                              # existing closure, reused read-only
```

Requirements:

- **Required change 1:** `structure_complete` is `true` only when `core_information_area.intact == true` —
  brand logo + `sku_text_layer` + `top_copy_title_layer` + primary hero **+ at least one `description_region`
  copy core** (`description_title_layer` or `description_body_layer`) all rendered (review §4.1). Any gap is
  listed in `missing_core_information_members` and fails structure (conservative; no silent excuse).
- **Required change 2:** when Announcement omits the materials strip, `materials_strip_region` MUST emit explicit
  `collapsed_by_design: true` + a `reason_code` + `count: 0`. A materials strip absence is never a silent gap and
  never a structure failure.
- **Required change 4:** `on_poster_cta_text` MUST carry `render_kind: "display_text_only"`,
  `cta_action_bound: false`, and `stage3_send_untouched: true`; evidence must show the closure is unaffected by
  the slot.
- the three new copy slots must be added to the **Family B parity target map** so visible-truth parity covers
  them (otherwise their DOM evidence goes stale — a known Family B risk);
- no silent collapse: an absent optional slot is reported as `collapsed_by_design` with a `reason_code`;
- degraded renders must be visible and explainable in evidence.

---

## 10. Acceptance criteria for the first runtime slice

> The slice itself is **not** approved yet. These are the criteria a future approved slice must meet.

A first Product Announcement runtime slice is accepted only if:

1. It runs through the **existing single-poster contract path** on `template_product_sheet_v1`; no new renderer,
   template family, registry entry, or API endpoint is introduced.
2. The **frozen Family B region order and ownership are byte-unchanged**; the existing reused slots (logo / SKU /
   title / subtitle / hero / description) behave identically to the current Family B baseline.
2a. **(Required change 1)** `structure_complete` is driven by the **Family B core information area** (§6.1): it is
   `true` only when brand logo + `sku_text_layer` + `top_copy_title_layer` + primary hero **+ at least one
   `description_region` copy core** (`description_title_layer` or `description_body_layer`) all render; any missing
   core member yields `structure_complete = false` with `missing_core_information_members` populated. A poster with
   only brand + SKU + headline + product image **must fail** structure (review §4.1).
3. The **three new copy slots** (`availability_badge`, `tariff_line`, `on_poster_cta_text`) render when supplied,
   `collapsed_by_design` (with a `reason_code`) when absent, respect their char/line budgets, and appear in evidence.
3a. **(Required change 2)** `materials_strip_region = collapsed_by_design` is a **named acceptance item** for
   `family_b_product_announcement`: when materials are omitted it emits explicit `collapsed_by_design: true` +
   `reason_code` + `count: 0`; **the frozen five-region order is unchanged** even when it collapses; **no
   spec-table, contact module, or gallery content is routed into `materials_strip_region`**; and parity/visible-
   truth reports the collapsed state rather than silently dropping it.
3b. **(Required change 3)** `tariff_line` accepts **`on_request` only** in v1; a `price` request is rejected
   (no silent fallback). `price` is a future extension with its own field, sanitization, currency/locale policy,
   and parity evidence.
4. **(Required change 4)** `on_poster_cta_text` is provably display-only: evidence carries
   `render_kind: "display_text_only"`, `cta_action_bound: false`, and `stage3_send_untouched: true`, and a
   no-change check shows rendering **with** vs. **without** the slot yields **identical Stage3/closure behavior**
   (no send invoked, no closure field changed).
5. **No structured spec-table** appears (deferred to Featured Spec).
6. `announcement_variant_contract_review` emits the full requested → sanitized → rendered chain per slot, the
   `core_information_area` verdict, the explicit `materials_strip_region` collapse evidence, the layout-mode
   reason, and the read-only `poster_key`.
7. **Parity:** the new slots are in the Family B parity target map; degraded path is explainable; Puppeteer↔Pillow
   parity (where Puppeteer is enabled) holds.
8. **Stability:** announcement renders are deterministic across repeated runs (reuse the existing stability
   harness pattern).
9. **No regression** to Family A or to the existing Family B baseline tests.
10. All copy passes the existing sanitization + grounded-claim rejection; no ungrounded marketing claim reaches
    the poster.

---

## 11. Open decisions (for the implementation-slice approval)

1. Confirm `availability_badge` owner = `top_copy_region` (recommended) vs. banner.
2. Confirm `tariff_line` owner region (default `top_copy_region`).
3. ~~v1 tariff modes~~ — **RESOLVED (Required change 3):** v1 is `on_request` only; `price` deferred.
4. Confirm `on_poster_cta_text` placement at the `description_region` footer edge.
5. Confirm the three new slots are added to the Family B parity target map (recommended — avoids stale
   visible-truth evidence).
6. ~~Materials use~~ — **RESOLVED (Required change 2):** `materials_strip_region` stays collapsed for Announcement
   and must emit explicit `collapsed_by_design` evidence.
7. **Confirm phone/contact footer is deferred** and is **not** a fourth copy slot in Announcement v1 (review §5
   nit / Owner decisions). The real `.eml` shows phone + email; v1 displays only CTA label + email. Recommended:
   defer phone/contact footer.
8. Confirm the shared `palette_token` default = the existing Family B `industrial_sheet_*` token bundle; do **not**
   create a new campaign palette in the first slice (review §5 nit). Recommended: reuse existing.

---

## 12. Compliance checklist

| Hard rule | Status |
|---|---|
| Do not change code | ✅ docs-only |
| Do not modify template specs | ✅ no spec edit |
| Do not edit renderer | ✅ |
| Do not modify APIs | ✅ |
| Do not redesign Family B | ✅ reactivate-not-redesign; frozen region order + existing slots reused |
| No editor-first behavior | ✅ closed enums + structured inputs |
| Do not treat `.eml` HTML as runtime template | ✅ evidence only; assets operator-supplied |
| Do not touch Stage3 email flow | ✅ `on_poster_cta_text` display-only; closure read-only |
| New = three minimal copy slots inside frozen regions | ✅ |
| Spec-table excluded | ✅ deferred to Featured Spec |
| Each variant runs the existing single-poster path | ✅ |
| Separate diagnostics per poster | ✅ `announcement_variant_contract_review` |
| Required change 1 — `structure_complete` requires the Family B core information area | ✅ §6.1, §9, §10.2a |
| Required change 2 — materials collapse is explicit `collapsed_by_design` evidence | ✅ §7, §9, §10.3a |
| Required change 3 — tariff v1 is `on_request` only | ✅ §4, §5.2, §10.3b, §11.3 |
| Required change 4 — `on_poster_cta_text` proves display-only / no Stage3 binding | ✅ §5.3, §9, §10.4 |

---

## 12a. Implementation status — first runtime slice (2026-06-15)

**Owner-approved first runtime slice is IMPLEMENTED (strict scope).** Code landed exactly within the approved
allowed list; nothing outside it.

- **Schema / threading:** `availability_badge`, `tariff_mode` (`Optional[Literal["on_request"]]` — `price`
  rejected at the schema boundary), `on_poster_cta_label`, `on_poster_cta_email` added to
  `GeneratePosterV2Request` + `PosterSpec` + `main.py` thread-through; response gains
  `announcement_variant_contract_review`.
- **Resolution:** pure helper `resolve_announcement_copy_slots(spec)` in `contracts.py` (deterministic; collapse =
  `present` flag) — mirrors how `sku_text` is handled inline (no new behavior-resolver dataclass fields).
- **Render:** three Pillow draw blocks (availability badge in `top_copy_region`; tariff line + CTA in
  `description_region` lower band) within frozen region bounds; matching HTML elements +
  `data-parity-key` + CSS for Puppeteer parity; `slot_spec` layer contracts added.
- **Diagnostics:** `_build_announcement_variant_contract_review` emits the Family B core information area
  (incl. description copy core), explicit `materials_strip_region` collapse evidence, the three slots'
  requested→sanitized→rendered chain, and CTA `render_kind=display_text_only` / `cta_action_bound=false` /
  `stage3_send_untouched=true`. Three parity targets added to `_build_template_b_parity_review` + visible-truth maps.
- **Tests:** 6 new (5 pipeline + 1 schema): all three slots render-when-supplied; collapse-by-design when absent;
  materials collapse evidence; structure_complete requires the description copy core (fail + pass cases); tariff
  `on_request` accepted / `price` rejected.
- **Validation:** full `tests/poster2/` suite — **53 pre-existing failures unchanged, +6 new passing, zero
  regressions** (verified by baseline-vs-change failure-set diff). Family B operator path is Pillow (Puppeteer
  disabled in its selector); the slice runs through the existing `/api/v2/generate-poster` single-poster path.
- **Out of scope (not done, by design):** no Stage1/Stage2 operator UI for the new fields (fields are optional;
  existing flow unchanged) — a follow-up slice if the Owner wants operator entry; no new renderer / family /
  registry / Stage3 / price support.
- **Localization note:** the `on_request` tariff phrase is a fixed constant `TEMPLATE_B_TARIFF_ON_REQUEST_TEXT`
  ("Tarif : nous contacter", matching the Cuistance evidence) — flagged as a future localization item.

## 13. Stop point

This document is the **docs-only contract** for the Product Announcement variant. **No implementation is started.**

This revision applied the **four Owner-required review changes** (core information area for `structure_complete`;
explicit `materials_strip_region` collapse evidence; tariff v1 `on_request` only; provable display-only
`on_poster_cta_text`). Per the Owner verdict, the doc now **returns for Owner approval before any runtime.**

**Owner approval is requested** for a first runtime implementation slice scoped exactly to:
reactivated Family B `template_product_sheet_v1` + the three additive copy slots + the
`announcement_variant_contract_review` diagnostics, under the acceptance criteria in §10 (now including the four
required changes) — and nothing else.
