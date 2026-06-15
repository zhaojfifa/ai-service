# Family B Product Announcement Variant Contract Review v1

> **Task:** `POSTER2-FAMILY-B-ANNOUNCEMENT-CONTRACT-REVIEW`
> **Mode:** review only. No runtime code, template spec, renderer, API, Stage3, registry, or email-send change.
> **Date:** 2026-06-15
> **Verdict:** **APPROVE WITH REQUIRED CHANGES**

## 1. Review scope

Reviewed targets:

- `docs/poster2/02_architecture/catalog_campaign_poster_set_orchestration_spec_v1.md`
- `docs/poster2/02_architecture/family_b_product_announcement_variant_contract_v1.md`
- `docs/poster2/real_email_to_poster_grammar_assessment_v1.md`
- `docs/poster2/05_validation/template_b_contract_correction_status_v1.md`
- `docs/poster2/05_validation/template_b_line2_independent_flow_status_v1.md`
- `docs/poster2/05_validation/template_b_design_baseline_v1.md`
- `docs/poster2/05_validation/template_b_parity_and_visual_contract_status_v1.md`
- `docs/poster2/05_validation/template_b_backend_generation_fix_status_v1.md`
- `docs/poster2/02_architecture/template_family_region_matrix_v1.md`
- `docs/poster2/02_architecture/template_family_slot_contract_baseline_v1.md`

Required anchors read:

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/poster2/README.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/poster_generation_product_design_baseline_v1.md`
- `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
- `docs/poster2/05_validation/product_region_annotation_contract_status_v1.md`
- `docs/poster2/05_validation/bottom_behavior_contract_status_v1.md`

Note: the task named some Template B status files at `docs/poster2/`; the formal index places them under
`docs/poster2/05_validation/`, and this review used those canonical paths.

## 2. Final verdict

**APPROVE WITH REQUIRED CHANGES.**

The Product Announcement Variant is architecturally correct: it reuses Family B, keeps the Catalog Campaign
Poster Set as orchestration above single-poster contracts, avoids Stage3/email-shell confusion, avoids a
mega-poster, and restricts new work to three optional copy slots. It should not proceed to runtime until the
required contract changes below are made in the docs and accepted by the Owner.

## 3. Blocking issues

None.

No issue requires blocking the direction outright. The current contract is a sound first slice candidate once
the structure-completeness and slice-boundary clarifications below are made before implementation.

## 4. Required changes before runtime approval

### 4.1 Structure completeness is too narrow

`family_b_product_announcement_variant_contract_v1.md` currently proposes `missing_mandatory_slots` as only
`logo`, `title`, `primary hero`, and `sku_text`. That is too narrow for existing Family B governance.

Family B success criteria require:

- brand/banner anchor present,
- hero product region present,
- **spec region or copy region has at least one core information area**.

Because Announcement intentionally excludes the spec-table, the first slice must require a copy-region core:
at minimum `description_title` from `copy.feature_claims[0]` or `description_body` from `copy.description`.
Otherwise a poster with only brand + SKU + headline + product image could pass the new review while failing
Family B's own product-sheet/story completeness model.

Required change: update the Announcement diagnostics and acceptance criteria so `structure_complete = true`
requires:

- `logo_banner_region` / brand anchor,
- `top_copy_region` with `sku_text` and title,
- `product_hero_region` with primary image,
- `description_region` core information via at least one rendered claim/title or description body.

### 4.2 Clarify `materials_strip_region` collapse as an Announcement variant rule

The contract says Announcement typically omits `materials_images` and lets `materials_strip_region` collapse.
That fits the lightweight variant, and backend history says empty materials paths are supported. However,
because Family B has a frozen five-region order and historical product-sheet language can treat supporting
visual/materials as visible structure, the runtime slice must explicitly prove:

- the region order remains unchanged even when materials collapse,
- no spec-table, contact module, or gallery content is routed into `materials_strip_region`,
- parity/visible-truth diagnostics report the collapsed materials state rather than silently dropping it.

Required change: make `materials_strip_region = collapsed_by_design` a named acceptance item for
`family_b_product_announcement`.

### 4.3 Pin tariff v1 to `on_request`

The real `.eml` evidence only contains `Tarif = Nous contacter`. The contract allows future `price`, but no
price field is required for v1.

Required change: first runtime slice should support `tariff_mode = on_request` only. `price` should remain a
future explicit extension with its own input field, sanitization, currency/locale policy, and parity evidence.

### 4.4 Make display-only CTA evidence stronger

The contract correctly states `on_poster_cta_text` is display-only and must not touch Stage3. The acceptance
criteria should require structural proof, not only wording.

Required change: first slice diagnostics should include a boolean or evidence note such as
`stage3_send_untouched: true` / `cta_action_bound: false`, and validation should include a no-change check for
Stage3/closure behavior.

## 5. Non-blocking nits

- The real email includes phone + email contact text, while the proposed slot only displays CTA label + email.
  This is acceptable for a minimal first slice, but the Owner should explicitly confirm phone/contact footer is
  deferred and not a fourth slot.
- The grammar assessment says "no reference/SKU slot" as a gap, but later Template B correction work establishes
  real `sku_text` ownership. The new contract handles this correctly; future docs should treat the assessment
  statement as resolved history.
- The canonical contract and the superseded sibling use slightly different slot names (`on_poster_cta_text` vs.
  `cta_text_slot`). The canonical names should remain the only names used in any implementation ticket.
- The shared `palette_token` default should remain the existing Family B `industrial_sheet_*` token bundle; do
  not create a new campaign palette in the first slice.

## 6. Answers to review questions

1. **Does the Product Announcement Variant correctly reuse Family B instead of redesigning it?**
   Yes. It binds to `template_product_sheet_v1`, preserves the established five-region Family B stack, and
   reuses `sku_text`, `title`, `subtitle`, primary/secondary product images, and description slots.

2. **Are the three optional copy slots sufficient and minimal?**
   Yes for the Announcement slice: `availability_badge`, `tariff_line`, and `on_poster_cta_text` cover the
   stable non-spec commercial copy in the `NOUVEAUTÉ` evidence. Do not add spec rows, phone footer, or product
   matrix content to this slice without a new contract.

3. **Does the contract preserve existing Family B region order and payload truth?**
   Mostly yes. The slot map uses the real Template B payload fields. Required change: tighten
   `structure_complete` so the contract honors Family B's existing copy-or-spec core information requirement.

4. **Does the contract avoid Stage3/email-shell/send-action confusion?**
   Yes. `.eml` HTML is evidence only, email shell is discarded, and CTA is display-only. Required change: make
   the no-send/no-Stage3 evidence explicit in diagnostics.

5. **Does the contract avoid building a mega-poster?**
   Yes. It excludes Catalog Hero, Product Matrix, spec table, email footer, and Stage3; richness remains in the
   Poster Set fan-out model.

6. **Does the contract fit the Catalog Campaign Poster Set orchestration layer?**
   Yes. It is a single variant under the set coordinator, references per-poster diagnostics, and does not ask the
   orchestration layer to render or own geometry.

7. **Are diagnostics and acceptance criteria concrete enough for a first runtime slice?**
   Close, but not yet. They need the required changes above: Family B core-info completeness, explicit materials
   collapse evidence, tariff v1 narrowing, and display-only CTA proof.

8. **What should be the first implementation slice if approved?**
   Reactivated Family B `template_product_sheet_v1` only, using the existing `/api/v2/generate-poster` single
   poster path, with additive resolver/schema support for the three copy slots, `announcement_variant_contract_review`,
   Family B parity target-map additions, and no new template family, endpoint, registry family, renderer, or Stage3
   behavior.

9. **What must remain explicitly forbidden?**
   New renderer; new top-level region; Family B region-order change; spec-table in Announcement; `materials_strip`
   repurpose; `.eml` HTML as runtime template; remote `.eml` image hot-linking; Stage3 send/action wiring;
   portrait Catalog Hero; Product Matrix; CTA/contact standalone poster; freeform geometry/editor behavior;
   Family A bottom SOP or product-annotation truth changes.

10. **Are there any mismatches with the real `.eml` evidence?**
    No fatal mismatch. The contract intentionally excludes the spec block and phone/footer contact modules. That is
    acceptable for Announcement, but the phone/contact exclusion should be an explicit Owner decision. The evidence
    supports `tariff_mode = on_request`; it does not support v1 price rendering.

## 7. Recommended first implementation slice

If the Owner approves runtime after the required doc changes:

1. Add only the three copy fields to the Family B request/normalization/resolver path:
   `availability_badge`, `tariff_line` for `on_request`, and `on_poster_cta_text`.
2. Preserve the existing `template_product_sheet_v1` region order and all existing Family B slot behavior.
3. Add `announcement_variant_contract_review` with requested/sanitized/rendered evidence, collapse reasons,
   structure completeness, product hero layout reason, read-only `poster_key`, parity reference, and explicit
   `cta_action_bound: false`.
4. Add the three new slots to the Family B visible-truth parity target map.
5. Validate page-side and final-generation paths with supplied slots and with each optional slot absent.

## 8. Owner decisions still required

- Confirm the required structure-completeness rule: Announcement must render at least one copy-region core
  information slot when spec rows are absent.
- Confirm `availability_badge` owner = `top_copy_region`.
- Confirm `tariff_line` owner = `top_copy_region`.
- Confirm v1 `tariff_mode = on_request` only.
- Confirm `on_poster_cta_text` placement at the `description_region` footer edge.
- Confirm phone/contact footer is deferred and not a fourth copy slot in Announcement v1.
- Confirm `materials_strip_region` collapses by design for Announcement unless real materials are supplied.
- Confirm the three new slots must be added to Family B parity targets before runtime approval.

## 9. Reporting minimum

- **Root rules followed:** read governance anchors first; stayed contract-first; no runtime/template/renderer/API/Stage3/registry/email change.
- **Problem reproduced:** docs review reproduced the proposed Product Announcement contract against Family B baseline, orchestration spec, and real `.eml` evidence.
- **Root cause found:** the proposed first-slice diagnostics under-specify Family B core information completeness and need stronger collapse/no-Stage3 proof before runtime.
- **Files changed:** this review report and `docs/poster2/current_branch_execution_log_v1.md`.
- **Layer changed:** docs/review only.
- **Validation run:** document inspection only; no tests run because no runtime code changed.
- **Remaining risks:** Family B is dormant and parity-sensitive; first runtime slice can regress visible truth if new slots are not included in the parity target map.
