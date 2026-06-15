# Real Email → Poster Grammar Assessment v1

> **HX task:** `HX-20260615-POSTER2-EMAIL-GRAMMAR-REVIEW`
> **Mode:** `assessment_only` — **no runtime/template/registry/API/Stage3 code changed.**
> **Owner:** Jackie. **Date:** 2026-06-15.
>
> This task is **not** about email sending, Stage3, SMTP, Resend, or Mailchimp transport.
> The real customer `.eml` files are treated as **evidence for poster-generation logic**:
> can stable, repeatable poster expressions be extracted from real customer emails and
> mapped into Poster2 as reusable poster grammar / poster variants?

Input inspected directly:
`/Users/tylerzhao/harness-x/input/poster2_email_samples/20260615/`

- `Fw_ Fwd_ Quand les plats ont besoin d'un petit coup de chaud !.eml`
- `NOUVEAUTÉ ! LES BLENDERS AVEC CAISSON INSONORISANT SONT DISPONIBLES EN STOCK CHEZ CUISTANCE.eml`
- `NOUVEAUTÉ ! LES COUPES FRITES SONT DISPONIBLES EN STOCK CHEZ CUISTANCE.eml`
- `NOUVEAUTÉ ! LES CUISEURS À RIZ SONT DISPONIBLES EN STOCK CHEZ CUISTANCE.eml`

---

## 1. Executive verdict

| Question | Verdict | One-line basis |
|---|---|---|
| **Stable poster grammar extractable?** | **YES** | The three `NOUVEAUTÉ` emails are the **same fixed template filled with three different products** — that *is* a repeatable poster grammar. The fourth email is a richer catalog-hero campaign already extracted as `catalog_hero_v1`. |
| **Existing Poster2 strategy compatible?** | **PARTIAL** | The `NOUVEAUTÉ` single-product spec/announcement pattern maps cleanly onto the **Family B (Product Sheet)** anatomy already defined in the product baseline. The fourth email's catalog-hero pattern is **not** reachable on the frozen square canvas (confirmed by prior `reference_analysis_v1` → `template_classification_v1`: it needs a new portrait Catalog Hero family). |
| **New flow needed?** | **PARTIAL** | No new *renderer* is needed for the single-product posters. What is genuinely new is the **"Poster Set" orchestration concept** (one shared product input bundle → 2–3 variant posters, each through an existing/known family, each with its own diagnostics). That is an **orchestration layer above existing families**, not a new template engine. The portrait Catalog Hero template remains a separately-gated build. |

**Headline finding.** The strongest evidence in this batch is *not* the visually richest
email — it is the **three near-identical `NOUVEAUTÉ` emails**. Three different products
(blender / coupe-frites / cuiseur à riz) flow through a **byte-stable section order, a
stable image-role skeleton, and a stable text-module set**. That repetition across
products is the literal definition of "stable, repeatable poster expression," and it lands
on **Family B / Product Sheet**, not Family A.

---

## 2. Email shell vs poster body (required separation)

Every `.eml` is a **forwarded** marketing email and carries heavy non-poster chrome.
The shell must be discarded before any poster grammar is read:

**Email shell (NOT poster content — discard):**

- Forwarding chain noise: `---------- 转发的邮件 ---------`, `发自我的 iPhone`,
  `Début du message transféré`, repeated `From/Date/To/Subject` quote headers.
  (The Technitalia email was forwarded Technitalia → Gabriel/Cuistance → Jacky →
  `xxakka2013` → `zhaojfifa`; four hops of quoting.)
- Sender e-signature: NewOldStamp signature logo (`img w=130`) + four 24px social
  icons (Facebook / Twitter / Pinterest / Instagram).
- ESP chrome: "Can't read or see images? View this email in a browser",
  unsubscribe / "Manage Preference" / "Update profile" links, company legal
  registration footer (Codimatel SIRET, Cuistance "ZI Garonor", Mailchimp/Zoho
  list-manage URLs).
- A **1×1 tracking pixel** (`open.gif` / `track/open.php`) in every email.

**Poster body (the reusable design — keep):** the central single-column product
campaign block: banner → reference/SKU → headline → product name → description →
feature tick → spec block → tariff line → CTA → brand/contact footer, plus the
product hero image and the spec/detail image.

> This separation matches the standing project position: **".eml HTML is evidence, not
> a runtime template source"** (hard-forbidden rule honored — no `.eml` HTML was treated
> as a template).

---

## 3. Evidence from each `.eml`

### 3.1 The three `NOUVEAUTÉ … CUISTANCE` emails (Mailchimp, single product)

These three share one Mailchimp skeleton (`mcusercontent.com` assets). Decoded facts:

| Axis | BLENDER | COUPE-FRITES | CUISEUR À RIZ |
|---|---|---|---|
| Subject | `NOUVEAUTÉ ! LES BLENDERS AVEC CAISSON INSONORISANT …` | `NOUVEAUTÉ ! LES COUPES FRITES …` | `NOUVEAUTÉ ! LES CUISEURS À RIZ …` |
| Product type | sound-insulated blender | professional fry-cutter | professional rice cooker |
| Reference / SKU | `8010002 (CBG2000)` | `1210025 (FC001)` | `311001 / 311011 (RC10L)` |
| Spec line | `L240×P220×H500 mm · 2 L · 1,8 kW / 220-240V` | `L380×P260×H250 mm` | `L485×P420×H400 mm · 10 L cuit / 6 L sec` |
| Tariff | `Tarif = Nous contacter` | `Tarif = Nous contacter` | `Tarif = Nous contacter` |
| CTA | `mailto:commercial@cuistance.eu?subject=Question…` | identical | identical |
| Contact | `+33 (0)1 71 84 11 20 · commercial@cuistance.eu` | identical | identical |
| `<img>` count | 5 | 5 | 5 |

**Image roles (identical role-map across all three):**

| slot | width | role | shared? |
|---|---|---|---|
| img0 | 288 | top **brand banner** | **shared src across all 3** (`0a50184e-be…`) |
| img1 | 434 | **product hero** (the SKU) | unique per product |
| img2 | 360–383 | **product detail / spec / in-use image** | unique per product |
| img3 | 242 | footer **brand logo** | **shared src across all 3** (same `0a50184e-be…`) |
| img4 | 1 | tracking pixel | shell (discard) |

**Repeated section order (stable, all three):**

```
banner(brand)
→ reference/SKU line          ("Référence produit : <code>")
→ NOUVEAUTÉ headline          ("NOUVEAUTÉ ! <PRODUCT TYPE PROFESSIONNEL>")
→ product name (restated)
→ description paragraph        (materials + integrated specs, prose)
→ ✔ feature tick line         (one bold confirmation bullet)
→ product hero image          (img1)
→ spec block                  (Dimensions / Volume / Puissance / Référence)
→ tariff line                 ("Tarif = Nous contacter")
→ CTA                         ("Nous contacter" → mailto)
→ CONTACT block               (phone + email)
→ brand footer                (logo, address, ©, unsubscribe[shell])
```

**Text modules:** reference/SKU · headline · product-name · description · feature-tick ·
spec table · tariff · CTA label · contact. **CTA / contact modules:** a single
`mailto:` "Nous contacter" (no button-style web CTA), plus a static phone/email contact
block. **Verdict for this group: one product = one poster (a single Product Sheet),
and the template is provably stable because three products reuse it unchanged.**

### 3.2 `Quand les plats ont besoin d'un petit coup de chaud` (Zoho/Technitalia, catalog hero)

- **Subject:** `Quand les plats ont besoin d'un petit coup de chaud !` (gas burners /
  `LES RÉCHAUDS GAZ`).
- **Product type:** gas réchaud range (multiple declensions).
- **This is the SAME campaign already analyzed** under `HX-POSTER2-REFERENCE-GRAMMAR-V1`
  (`poster_refer.pdf` = this Technitalia/Codimatel email). Prior measured evidence is in
  `reference_analysis_v1.md`, `reference_contract_v1.md`, `template_classification_v1.md`,
  `reference_catalog_hero_contract_report_v1.md`.
- **Image roles:** charcoal brand bar + warm food hero (`w=600`) + isolated product with
  dashed radial callouts + restated centered title/subtitle + **product range matrix**
  (four `w=60` thumbnails = "choose your model" strip), then the social/contact shell.
- **Repeated structure:** `header → hero(scenario) → red ALL-CAPS title → product +
  callout ring → restated section title → subtitle → range-matrix gallery`. Measured
  weights: hero 0.38, product 0.28, title 0.12, gallery 0.12, header 0.10; whitespace
  >45%; **dual co-anchor (hero ∥ product, hero NOT receded), portrait 0.71 frame**.
- **CTA module:** the poster body has **no button CTA**; the verbal close (restated
  title + subtitle) is the close, and all CTA machinery (social, contact, unsubscribe)
  lives in the email shell.
- **Verdict for this email: it is internally a *Poster Set folded into one mega-poster*** —
  a Hero Explanation block **plus** an embedded Product Matrix strip. It is the
  decomposition target for the task's "Poster Set" hypothesis.

---

## 4. Extracted poster variants

From the four emails, the recurring poster expressions decompose into these variants:

| Variant | Source evidence | Anatomy | Status |
|---|---|---|---|
| **A. Hero Explanation Poster** | coup-de-chaud top block | brand bar · food/scene hero · red ALL-CAPS hook · product + dashed callout ring · strapline | **Catalog Hero grammar** (`catalog_hero_v1`); portrait, dual co-anchor |
| **B. Featured Spec Poster** | each `NOUVEAUTÉ` email | banner · product name · hero image · **spec table** (dims/volume/power) · reference · tariff | Maps to **Family B Product Sheet** |
| **C. Product Announcement Poster** | each `NOUVEAUTÉ` subject + headline + ✔ line | banner · "NOUVEAUTÉ !" headline · product hero · one-line claim · "en stock" · CTA | Lightweight subset of B (announcement, fewer specs) |
| **D. Product Matrix / Catalog Strip Poster** | coup-de-chaud `w=60` ×4 thumbnails + 3-cluster range | isolated-on-white product range, "choose your model" | Supported as a strip today (`title_gallery_split` gallery, ≤4 items); as a standalone poster it is a new compose |
| **E. CTA / Contact Poster** | `NOUVEAUTÉ` contact block + mailto | phone · email · "Nous contacter" · brand footer | **Not a standalone poster** — it is a footer module, not a full poster; do not over-extract |

**Note on the hypothesis "campaign = Poster Set of 2–3 simpler variants":** the evidence
**partially supports** it. The coup-de-chaud email *is* a single mega-poster that already
fuses A + D, so it *could* be decomposed into a Set. But the three `NOUVEAUTÉ` emails are
each **already a single, simple, self-contained poster** (variant B/C) — they are not
sets. So "Poster Set" is a **useful optional composition**, not a universal requirement.

---

## 5. Mapping to current Poster2

### 5.1 Per-variant family mapping

| Variant | Current family that can support it | Reusable contract pieces | Gaps |
|---|---|---|---|
| **B / C — Spec / Announcement** | **Family B — Product Sheet** (defined in `poster_generation_product_design_baseline_v1` §3.2: brand banner → reference/型号 → product main → spec/说明 → CTA → footer). Anatomy is a **near 1:1 match**. | header/brand banner; product main slot; `product_anchor_callouts` (optional); bottom title/subtitle; `bottom_contract_review`/`geometry_evidence` evidence chain; copy sanitization + Gemini/deterministic optimizer (already closed). | **Family B is not the active build line** (Family A square is the live oracle; Family B is "historical validation, not reopened"). Needs: a dedicated **spec-table module** (dims/volume/power/reference rows) — Poster2 has no structured spec-table slot today; a **reference/SKU slot**; a **tariff/"nous contacter" line**. None exist as contracts yet. |
| **A — Hero Explanation** | **NEW — Catalog Hero (portrait)** | header L/R; scenario slot; product slot; `product_anchor_callouts` (clamped to 3); gallery strip; brand-red palette token bundle. | Already documented as **unreachable on the frozen square canvas**: portrait ratio, dual co-anchor (hero not receded), title-in-product-lane have **no expression** in Family A region grammar. Requires the **missing portrait-canvas RegionDefinition layer** (`template_classification_v1` §4). |
| **D — Product Matrix** | Family A **bottom gallery** (`title_gallery_split`, `gallery_only_expanded`, ≤4 items, isolated-on-white) supports it **as a strip inside a poster**. | `gallery_mode`, `visible_item_count`, gallery distribution policies, caption rows. | As a **standalone** matrix poster it needs a compose that is mostly-gallery; the bottom SOP gallery already does the hard part but is frozen as a *bottom strip*, not a full-canvas matrix. |
| **E — CTA / Contact** | Footer / header identity lanes | brand footer, agent pill, contact. | None — it should stay a **module**, not a poster. |

### 5.2 What already exists and is reusable (do not rebuild)

- Five-region shell (header / scenario / product / feature / bottom) + slot contracts.
- `product_policy` unified product bounds/fit authority (PR-7/8) and the 3-slot frozen
  `product_anchor_callouts` annotation truth.
- Bottom SOP gallery (1/2/3/4 distribution, caption rows) — directly serves variant D.
- Copy pipeline: sanitization, deterministic preview policy, Gemini optimizer with
  deterministic fallback, grounded-claim rejection — directly serves the prose
  description / claim lines in B/C.
- Closure layer (`poster_record`, `email/preview`, `email/send`, optional PNG/PDF
  attachment) — relevant to *delivery*, explicitly **out of scope** here.
- Catalog Hero grammar already normalized as `catalog_hero_v1`.

### 5.3 Net gaps

1. **No structured spec-table contract** (Dimensions / Volume / Puissance / Référence
   as labeled rows) — the single biggest missing piece for variant B.
2. **No reference/SKU slot** and **no tariff/price-on-request slot**.
3. **No portrait canvas / RegionDefinition** (blocks variant A Catalog Hero).
4. **No campaign-level orchestration** (shared input bundle → N posters).
5. **Family B is dormant** — adopting B/C means re-activating a frozen line.

---

## 6. Architecture recommendation

**Recommended: a two-track, docs-gated plan — do NOT build a new mega-template.**

- **Track 1 (nearer, lower-risk): Featured Spec / Product Announcement on Family B.**
  The `NOUVEAUTÉ` pattern is the most stable, most repeatable, and most directly
  mappable evidence in the batch, and it lands on the **already-defined** Family B
  Product Sheet anatomy. The only true new contracts are a **spec-table module** +
  **reference/tariff slots**. This is an *extension of an existing family*, not a new
  family.

- **Track 2 (separate, already-gated): Catalog Hero portrait family.** Unchanged from
  the prior `template_classification_v1` recommendation: variant A needs the
  portrait-canvas RegionDefinition layer and is an Owner-gated, P1-scale build. **Keep
  it gated; do not fold it into Track 1.**

- **"Catalog Campaign Poster Set" = an orchestration layer, NOT a new renderer.**
  Model it as: *shared product input bundle → emit 2–3 variant posters, each rendered
  through its own existing/known template, each with its own per-poster diagnostics,
  under one shared visual-language token bundle.* This sits **above** Families A/B and
  reuses their renderers untouched. It is the correct home for the task's "Poster Set"
  hypothesis and avoids the mega-template risk (one over-complex poster trying to be
  hero + spec + matrix + CTA at once).

**Reject:** a single new "does-everything" catalog email template; treating any `.eml`
HTML as a runtime template; reopening Family A geometry to absorb spec tables.

---

## 7. Implementation path proposal (docs-only next step first)

> Per the task stop point, **nothing below is started in this task.** This is the proposed
> sequence for a *future* approved track.

1. **Docs-only next step (no code):**
   - Formalize a **Product Sheet (Family B) spec-table + reference/tariff contract spec**
     doc (slots, row model, collapse rules, char budgets) under `02_architecture/`.
   - Formalize a **Catalog Campaign Poster Set orchestration spec** (shared input bundle
     schema, variant selection rules, per-poster diagnostics, shared token bundle) — as a
     *concept/contract* doc, not code.

2. **First implementation slice (when approved):** **variant C — Product Announcement on
   Family B**, single product, the smallest of the spec posters: banner + headline +
   product hero + one claim line + reference + "en stock" + mailto CTA. It needs the
   fewest new contracts (reference slot + CTA line; spec-table deferred to variant B).

3. **Required contracts:** spec-table module (labeled rows), reference/SKU slot,
   tariff/price-on-request slot, optional product-detail (img2) slot; all under the
   Family B contract-first pattern (request → normalize → resolver-as-truth → renderer →
   evidence → operator review), reusing `product_policy` for product bounds.

4. **Required Stage1 inputs:** product reference/SKU, spec key-value pairs
   (dims/volume/power), tariff mode (`price | on_request`), CTA email, product detail
   image (optional). No freeform geometry input.

5. **Required Stage2 operator-UI changes:** a closed-enum variant selector
   (Announcement / Spec) and a structured spec-row entry surface — additive only,
   3-column header and layout unchanged, no drag-and-drop, no editor.

6. **Required diagnostics:** a `product_sheet_contract_review` mirroring the existing
   `bottom_contract_review`/`product_annotation_contract_review` evidence shape (requested
   → sanitized → rendered per spec row, reference/tariff provenance, renderer parity).

---

## 8. Risk assessment

| Risk | Reading from this evidence | Mitigation |
|---|---|---|
| **Overfitting to one customer** | All four emails are **one customer** (Cuistance, reselling Technitalia/Codimatel). The "stability" is partly *one ESP template reused*, not an industry-wide law. | Treat the extracted grammar as a **commercial-kitchen Product Sheet** pattern; validate against ≥1 unrelated catalog before freezing; keep the spec-table generic (key/value rows), not Cuistance-specific fields. |
| **Remote image extraction limits** | Every product image is a **remote `mcusercontent.com` / `campaign-image.eu` URL** (hot-linked, expirable, no alt text). They are not embedded. | Never depend on `.eml` remote images at runtime; operator re-supplies product assets in Stage1 (slot-driven), exactly as today. |
| **Email HTML not a runtime template** | `.eml` bodies are ESP table-soup with tracking pixels and shell chrome. | Already honored: HTML is evidence only; grammar is re-expressed as Poster2 contracts. |
| **Mega-template risk** | The coup-de-chaud email shows the temptation: hero + product + callouts + restated title + matrix in one image. | Use the **Poster Set orchestration** model (split into simple variants) instead of one all-in-one template. |
| **Editor-first drift** | Spec tables + CTA invite "let the operator drag/edit." | Hard-forbidden; keep closed enums + structured key/value inputs + contract-first resolver truth. |
| **Family B reactivation cost** | Family B is dormant; reopening carries parity/regression risk. | Scope Track 1 narrowly (announcement first), reuse the Family A SOP/evidence patterns, keep Family A untouched. |
| **Portrait-canvas scope creep** | Variant A pulls toward a large new family. | Keep it on a **separate gate**; do not bundle with Track 1. |

---

## 9. Owner decision needed

1. **Approve the Poster Set route as an *orchestration layer* (above Families A/B)** —
   yes / no? (Recommended: yes, as a docs-only spec first.)
2. **Which variant first** — **Product Announcement (C)** or **Featured Spec (B)**?
   (Recommended: **Announcement first** — fewest new contracts; Spec second once the
   spec-table contract is approved.)
3. **Re-activate Family B (Product Sheet)** as the home for B/C — yes / no? (Required for
   either; Family B is currently dormant.)
4. **Catalog Hero portrait family** — keep gated/deferred (recommended) or open the
   portrait-canvas RegionDefinition decision now?
5. **Treat "Catalog Campaign Poster Set" as orchestration** (recommended) vs. a new
   template family vs. a new Stage2 flow?

---

## 10. Acceptance self-check

- `.eml` files inspected directly — **yes** (parsed MIME parts, decoded text + HTML,
  enumerated image roles, links, tracking pixels).
- Report distinguishes **email shell from poster body** — **yes** (§2).
- Report evaluates **one poster vs multiple variants** — **yes** (§3.2, §4: NOUVEAUTÉ =
  one poster each; coup-de-chaud = a folded Set).
- Each extracted pattern mapped to **existing families/contracts** — **yes** (§5).
- States whether **current strategy is enough or a new Poster Set flow is needed** —
  **yes** (§1, §6: existing PARTIAL; Poster Set = orchestration layer; portrait Catalog
  Hero = separate gated family).
- **No implementation code changed** — **confirmed.**
