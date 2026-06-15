# Campaign Manifest + Variant Selection Contract v1

> **Status:** docs-only contract spec. **No runtime/template/registry/API/Stage3 code is written by this document.**
> **Owner gate (2026-06-15):** approved as docs-gated next work under the
> `catalog_campaign_poster_set_orchestration_spec_v1.md` direction.
> **Parent:** `catalog_campaign_poster_set_orchestration_spec_v1.md`.
> **Sibling:** `family_b_announcement_variant_contract_v1.md`.
>
> **Field/id names below are PROPOSED for a future contract, not committed API or schema.**

---

## 1. Purpose & scope

Define the **roll-up contract** for a Catalog Campaign Poster Set: how one shared product input bundle plus a
**variant selection** fans out into multiple single posters, and how those posters are reported back under one
**campaign manifest** with **separate per-variant diagnostics**.

**In scope:** campaign identity; variant-selection model; fan-out execution semantics; shared `palette_token`
rules; manifest schema; per-variant diagnostics reference model; partial-set / no-silent-drop semantics;
relationship to existing closure.

**Out of scope (explicit):** rendering (the layer never renders); any geometry/ownership/bottom-SOP/annotation
change; a new render endpoint; Stage3 email redesign; portrait Catalog Hero; the per-variant slot contracts
(those live in each variant's own doc, e.g. the Announcement contract).

---

## 2. Position & invariants (from the approved orchestration spec)

The campaign layer sits **above Family A / Family B**. Owner-approved invariants it must honor:

- it does **not** render;
- it does **not** own geometry;
- it does **not** change bottom SOP;
- it does **not** change product annotation truth;
- it does **not** redesign Stage3 email;
- **each poster variant must still run through the existing single-poster contract path.**

The manifest is therefore a **coordinator + reporter**, never a renderer and never a truth source for poster
geometry. The truth source for each poster remains that poster's own resolved contract.

---

## 3. Campaign identity

```yaml
campaign:
  campaign_key: string         # assigned at generate-time, like poster_key (roll-up id)
  bundle_ref: campaign_bundle  # the shared product input bundle (orchestration spec §3)
  palette_token: enum          # one shared visual-language token (§5)
  variant_selection: [enum]    # ordered, deduped (§4)
```

`campaign_key` is the roll-up handle. It **references** per-variant `poster_key`s; it does not replace them
(decision §10.4 — default is per-variant `poster_record` + a thin manifest that references them).

---

## 4. Variant selection model

```yaml
variant_selection:
  type: closed_enum_list
  allowed_variants:                      # v1 closed set
    - family_b_product_announcement      # variant C — implemented first
    - family_b_featured_spec             # variant B — gated on spec-table contract
    - family_a_product_matrix_strip      # variant D — deferred (uses existing Family A gallery)
  excluded_in_v1:
    - catalog_hero_portrait              # variant A — Owner: do not build now
    - cta_contact_poster                 # variant E — footer module, never a standalone poster
  rules:
    - ordered: render/report order follows selection order
    - deduped: a variant may appear at most once per campaign
    - min_items: 1
    - max_items: bounded (proposed 3 for v1)
    - empty_selection: rejected (a campaign must emit >= 1 poster)
    - unknown_variant: rejected (no silent drop; closed enum only)
```

Typical sets: `[announcement]`, `[announcement, featured_spec]`, later `[announcement, featured_spec,
product_matrix_strip]`. Hero Explanation (A) and CTA/Contact (E) are not selectable in v1.

---

## 5. Shared visual-language token (`palette_token`)

To keep a set visually coherent, all variants in one campaign share **one** non-geometric token bundle, modeled
exactly on the proven **Composition Priority Layer** pattern (`composition_priority_layer_review_v1`):

- closed-enum → closed CSS-var tokens, merged **last** through the beauty channel;
- touches only whitelisted **non-geometry** vars (accent tone, surface, shadow/lift, text rhythm);
- the empty/`balanced` token yields a byte-identical base render per variant;
- it **may not** change region geometry, ownership, `visible_item_count`, annotation truth, or bottom SOP.

v1 default candidate: reuse the existing Family B `industrial_sheet_*` token set as the first `palette_token`
(decision §10.3). Family A variants in a mixed set apply the same token through their own beauty channel.

---

## 6. Fan-out execution model

```
campaign(bundle, palette_token, selection)
  for each variant in selection (ordered):
     project bundle -> single-poster input for that variant   # per-variant contract
     resolve + render via EXISTING single-poster path         # orchestration does NOT render
     capture: poster_key, <variant>_contract_review, degraded, structure_complete, deliverable
  assemble campaign_manifest (references, never merges, per-variant evidence)
```

- One **existing single-poster resolve** per selected variant. No new render endpoint.
- The layer **captures references** to each poster's result; it never re-derives geometry or merges evidence.
- Fan-out may be sequential or parallel; ordering in the manifest follows selection order regardless.

---

## 7. Campaign manifest schema (roll-up)

```yaml
campaign_manifest:
  campaign_key: string
  palette_token: enum
  requested_variants: [enum]          # echo of selection (ordered)
  variants:                           # one entry per requested variant — no silent drop
    - variant_id: enum
      poster_key: string | null       # null if the variant failed before producing a record
      structure_complete: bool
      degraded: bool
      deliverable: bool
      outcome: enum[rendered, collapsed, failed]
      contract_review_ref: string      # points to <variant>_contract_review (reference, not merge)
      reason_code: string | null       # populated for collapsed/failed
  campaign_outcome:
    delivered_count: int
    requested_count: int
    status: enum[complete, partial, failed]   # see §8
  notes: string?
```

**Separate diagnostics per poster (Owner requirement):** `contract_review_ref` *references* each variant's own
review (e.g. `announcement_variant_contract_review`). The manifest **never merges** per-variant evidence into a
single blob.

---

## 8. Partial-set & no-silent-drop semantics

- **Every requested variant appears** in `variants[]` with an explicit `outcome` — `rendered`, `collapsed`
  (structure-incomplete but explainable), or `failed`. A skipped/failed variant is **never** silently dropped
  (standing "no silent caps" rule).
- **Campaign status:**
  - `complete` — all requested variants `rendered` + `deliverable`;
  - `partial` — ≥1 but not all variants deliverable; the manifest names which failed and why;
  - `failed` — 0 variants deliverable.
- A failing variant **does not abort** the others; the orchestration continues and reports per-variant outcome.

---

## 9. Relationship to existing closure (read-only)

- Each variant reuses the **existing per-poster `poster_record` / `poster_key`** path. Default model:
  **one `poster_record` per poster** + a **thin campaign manifest that references them** (decision §10.4).
- The manifest **reuses the closure read-only.** It does **not** modify `poster_record`, `email/preview`,
  `email/send`, attachment wiring, or any Stage3 behavior. On-poster CTA remains display-only copy (see the
  Announcement contract §5.3).
- No campaign-level email/send concept is introduced here. Delivery stays exactly as today, per poster.

---

## 10. Open decisions

1. `max_items` per campaign for v1 (proposed 3).
2. Fan-out execution: sequential (simpler, ordered) vs. parallel (faster) — manifest ordering is selection-order
   either way. (Recommended: start sequential.)
3. Shared `palette_token` v1 default = reuse existing Family B `industrial_sheet_*` (recommended) vs. a new
   campaign palette.
4. Record model: **per-variant `poster_record` + thin referencing manifest** (recommended) vs. a new
   campaign-level record. (Recommended avoids any Stage3/closure change.)
5. Whether a `partial` campaign is operator-acceptable for review, or must be `complete` to advance
   (Recommended: `partial` is acceptable and explicitly flagged).

---

## 11. Compliance checklist

| Hard rule | Status |
|---|---|
| No runtime code implemented | ✅ docs-only |
| Layer does not render | ✅ fan-out over existing single-poster path |
| Layer does not own geometry | ✅ references per-poster truth, never re-derives |
| No bottom SOP / product annotation truth change | ✅ |
| No Family A / Family B region/ownership change | ✅ |
| No Stage3 email redesign | ✅ closure reused read-only; no campaign send concept |
| Each variant runs the existing single-poster path | ✅ |
| Separate diagnostics per poster | ✅ manifest references, never merges |
| No silent drop of a requested variant | ✅ every variant reported with an outcome |
| Closed-enum variant selection (no freeform) | ✅ |
