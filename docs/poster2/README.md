# poster2 Documentation Index

`docs/poster2/README.md` is the formal index only.
It defines the reading path and the formal doc path.
It does not carry branch history, pasted progress logs, or one-off process notes.

## Root-Level Exceptions

The following three files remain at `docs/poster2/` root by rule:

1. [poster_generation_product_design_baseline_v1.md](poster_generation_product_design_baseline_v1.md)
2. [README.md](README.md)
3. [current_branch_execution_log_v1.md](current_branch_execution_log_v1.md)

All other formal poster2 documents now belong under the layered directories:

- `01_product/`
- `02_architecture/`
- `03_engineering/`
- `04_skills/`
- `05_validation/`
- `99_archive/`

## Entry Order

Read in this order for poster2 work:

1. [poster_generation_product_design_baseline_v1.md](poster_generation_product_design_baseline_v1.md)
2. [template_dual_v2_architecture_business_definition.md](02_architecture/template_dual_v2_architecture_business_definition.md)
3. [template_family_region_matrix_v1.md](02_architecture/template_family_region_matrix_v1.md)
4. [template_family_slot_contract_baseline_v1.md](02_architecture/template_family_slot_contract_baseline_v1.md)
5. [renderer_routing_and_fallback_rules_v1.md](02_architecture/renderer_routing_and_fallback_rules_v1.md)
6. [quality_guard_and_structure_completeness_v1.md](02_architecture/quality_guard_and_structure_completeness_v1.md)
7. [family_isolation_rules_v1.md](02_architecture/family_isolation_rules_v1.md)
8. [skill_rules_and_storage_v1.md](04_skills/skill_rules_and_storage_v1.md)
9. [family_a_four_layer_verification_matrix_v1.md](05_validation/family_a_four_layer_verification_matrix_v1.md)

Then read only the task-relevant status / plan / validation documents.

## Formal Document Path

### 01 Product

- [external_reference_poster_design_review_and_migration_v1.md](01_product/external_reference_poster_design_review_and_migration_v1.md)
- [poster2_product_flow_reviewable_v1.md](01_product/poster2_product_flow_reviewable_v1.md)

### 02 Architecture

- [template_dual_v2_architecture_business_definition.md](02_architecture/template_dual_v2_architecture_business_definition.md)
- [template_dual_v2_structural_rebuild_baseline_v1.md](02_architecture/template_dual_v2_structural_rebuild_baseline_v1.md)
- [catalog_campaign_poster_set_orchestration_spec_v1.md](02_architecture/catalog_campaign_poster_set_orchestration_spec_v1.md)
  Docs-only orchestration architecture for the Owner-approved **Catalog Campaign Poster Set** direction
  (2026-06-15): shared product input bundle → multiple *simple* poster variants → per-variant contract +
  diagnostics, rolled up under a campaign manifest. Fan-out (not fusion) above Families A/B; no new renderer.
  First implementation candidate = **Product Announcement / Family B reactivation** (reactivate-not-redesign;
  reuses existing `template_product_sheet_v1` regions + SKU slot, adds only availability/tariff/CTA-text copy
  slots). Portrait Catalog Hero mega-poster, standalone Product Matrix, structured spec-table, and Stage3
  remain explicitly out of scope. Turns `real_email_to_poster_grammar_assessment_v1.md` into product architecture.
  **APPROVED (Owner, 2026-06-15).**
- [family_b_product_announcement_variant_contract_v1.md](02_architecture/family_b_product_announcement_variant_contract_v1.md)
  **Canonical** docs-only contract for the **Product Announcement** variant on reactivated Family B
  (`template_product_sheet_v1`) — task `POSTER2-FAMILY-B-ANNOUNCEMENT-VARIANT-CONTRACT-V1`. Reactivate-not-redesign:
  preserves the frozen Family B region order (`logo_banner` → `top_copy` → `materials_strip` → `product_hero` →
  `description`) and reuses the real existing fields (`sku_text`, `title`, `subtitle`, `product_image`,
  `product_secondary_image`, `description_title`, `description_body`); adds only three minimal optional **copy**
  slots — `availability_badge`, `tariff_line`, `on_poster_cta_text` (display only, **not** a Stage3 send). Maps the
  real Cuistance `NOUVEAUTÉ` email grammar, defines required shared + variant fields, diagnostics
  (`announcement_variant_contract_review`), explicit non-goals, and first-slice acceptance criteria. Spec-table
  excluded (deferred to Featured Spec). Stops for Owner approval of the implementation slice.
  - [family_b_announcement_variant_contract_v1.md](02_architecture/family_b_announcement_variant_contract_v1.md)
    — **SUPERSEDED** earlier short sibling; folded into the canonical doc above.
- [campaign_manifest_and_variant_selection_contract_v1.md](02_architecture/campaign_manifest_and_variant_selection_contract_v1.md)
  Docs-only roll-up contract: shared bundle + closed-enum **variant selection** → fan-out (one existing
  single-poster resolve per variant; the layer never renders) → **campaign manifest** that references per-variant
  diagnostics (never merges them). Defines campaign identity, shared non-geometric `palette_token`, no-silent-drop /
  partial-set semantics, and read-only reuse of the existing `poster_record` closure (no Stage3 change).
- [template_family_region_matrix_v1.md](02_architecture/template_family_region_matrix_v1.md)
- [template_family_slot_contract_baseline_v1.md](02_architecture/template_family_slot_contract_baseline_v1.md)
- [renderer_routing_and_fallback_rules_v1.md](02_architecture/renderer_routing_and_fallback_rules_v1.md)
- [quality_guard_and_structure_completeness_v1.md](02_architecture/quality_guard_and_structure_completeness_v1.md)
- [family_isolation_rules_v1.md](02_architecture/family_isolation_rules_v1.md)

Review-only (no contract change):

- [real_email_to_poster_grammar_assessment_v1.md](real_email_to_poster_grammar_assessment_v1.md)
  Assessment-only review (HX-20260615-POSTER2-EMAIL-GRAMMAR-REVIEW) of four real customer
  `.eml` campaigns as evidence for poster-generation grammar. Separates email shell from
  poster body; finds the three `NOUVEAUTÉ` single-product emails are one Mailchimp template
  reused across products (stable Product Sheet grammar → Family B), and the `coup de chaud`
  email is the already-extracted `catalog_hero_v1` portrait mega-poster. Verdict: stable
  grammar YES, existing strategy PARTIAL, new flow PARTIAL ("Catalog Campaign Poster Set" =
  orchestration layer above Families A/B, not a new renderer). No code changed.
- [composition_priority_layer_review_v1.md](composition_priority_layer_review_v1.md)
  Review package for the Composition Priority Layer (HX-POSTER2-COMPOSITION-PRIORITY-V1): the operator "海报风格策略" (Balanced / Studio / Product Hero / Catalog Clean) — a request-level, non-geometric CSS-var bundle (scenario atmosphere recede + product lift + text breathing) plus the `template_dual_v2_product_hero` variant. Raises Product Hero to ~4.6/5 (product focus 4.6, scenario 2.5, bottom 2.5, title 4.5, premium 4.6). Proves all protected region bounds, ownership, bottom-SOP geometry, `visible_item_count`, and annotation truth unchanged; base/airy/studio unaffected.
- [geometry_variant_studio_review_v1.md](geometry_variant_studio_review_v1.md)
  Review package for the `template_dual_v2_studio` geometry style variant (HX-POSTER2-STYLE-VARIANT-V1): bounded product-image breathing + stronger title hierarchy + lighter gallery surface. Proves protected region bounds, ownership guards, bottom-SOP geometry, and the 3 product-annotation slots are byte-identical to the base; base + airy untouched. Includes stability + geometry-invariant results, operator review (~4.3/5), and the one Owner decision (geometric bottom-footprint reduction is a frozen-SOP amendment).
- [template_taxonomy_and_visual_relaxation_plan_v1.md](template_taxonomy_and_visual_relaxation_plan_v1.md)
  Planning only. Defines the template taxonomy (fixed base / seeded / style variant / campaign pack, all pinned to a base family) and a Composition / Visual Relaxation beauty-token layer that fixes "too tightly fitted / mechanically packed" output by tuning negative space, surface, blend, and text rhythm only — never region geometry. Governing rule: relaxation changes the space between/inside regions, never region boundaries; bottom SOP and product annotation truth are untouched. Includes runtime compatibility table, enum token model, relaxation rules per visual issue, renderer/Pillow policy, validator + aesthetic QA, and a Phase 1–4 plan.

### 03 Engineering

- [template_dual_v2_engineering_implementation_and_acceptance.md](03_engineering/template_dual_v2_engineering_implementation_and_acceptance.md)
- [template_behavior_layer_plan_v1.md](03_engineering/template_behavior_layer_plan_v1.md)
- [beautification_layer_plan_v1.md](03_engineering/beautification_layer_plan_v1.md)
- [poster_generation_project_restructure_checklist_v1.md](03_engineering/poster_generation_project_restructure_checklist_v1.md)
- [storage_copy_email_closure_status_v1.md](03_engineering/storage_copy_email_closure_status_v1.md)
- [email_copy_optimizer_and_optional_attachment_status_v1.md](03_engineering/email_copy_optimizer_and_optional_attachment_status_v1.md)
- [generation_quality_and_copy_optimization_status_v1.md](03_engineering/generation_quality_and_copy_optimization_status_v1.md)
- [copy_quality_phase1_status_v1.md](03_engineering/copy_quality_phase1_status_v1.md)
- [stage1_operator_input_surface_bugfix_status_v1.md](03_engineering/stage1_operator_input_surface_bugfix_status_v1.md)

Family A practical closure:

- [product_region_practical_beautification_observability_v1.md](03_engineering/family_a/product_region_practical_beautification_observability_v1.md)
- [bottom_region_practical_beautification_observability_v1.md](03_engineering/family_a/bottom_region_practical_beautification_observability_v1.md)
- [gemini_copy_optimizer_integration_v1.md](03_engineering/family_a/gemini_copy_optimizer_integration_v1.md)
- [copy_optimization_value_closure_v1.md](03_engineering/family_a/copy_optimization_value_closure_v1.md)
- [product_annotation_text_closure_v1.md](03_engineering/family_a/product_annotation_text_closure_v1.md)
- [copy_quality_closure_v1.md](03_engineering/family_a/copy_quality_closure_v1.md)
- [template_a_text_contract_repair_and_product_region_text_closure_v1.md](03_engineering/family_a/template_a_text_contract_repair_and_product_region_text_closure_v1.md)
- [family_a_commercial_fryer_min_delta_refinement_v1.md](03_engineering/family_a/family_a_commercial_fryer_min_delta_refinement_v1.md)
- [family_a_fryer_live_diagnosis_micro_refinement_v1.md](03_engineering/family_a/family_a_fryer_live_diagnosis_micro_refinement_v1.md)
- [family_a_product_annotation_shell_micro_structure_v1.md](03_engineering/family_a/family_a_product_annotation_shell_micro_structure_v1.md)
- [family_a_bottom_text_finalization_v1.md](03_engineering/family_a/family_a_bottom_text_finalization_v1.md)
- [family_a_fryer_hero_footer_blocker_removal_v1.md](03_engineering/family_a/family_a_fryer_hero_footer_blocker_removal_v1.md)
- [family_a_fryer_truth_parity_and_footer_caption_closeout_v1.md](03_engineering/family_a/family_a_fryer_truth_parity_and_footer_caption_closeout_v1.md)
- [family_a_fryer_anchor_rebind_and_left_rebalance_v1.md](03_engineering/family_a/family_a_fryer_anchor_rebind_and_left_rebalance_v1.md)
- [family_a_single_primary_support_surface_v1.md](03_engineering/family_a/family_a_single_primary_support_surface_v1.md)

### 04 Skills

- [skill_rules_and_storage_v1.md](04_skills/skill_rules_and_storage_v1.md)

### 05 Validation

Core verification anchors:

- [family_a_four_layer_verification_matrix_v1.md](05_validation/family_a_four_layer_verification_matrix_v1.md)
- [template_a_rebaseline_status_v1.md](05_validation/template_a_rebaseline_status_v1.md)
- [template_a_beautification_freeze_status_v1.md](05_validation/template_a_beautification_freeze_status_v1.md)
- [template_a_isolation_rebaseline_status_v1.md](05_validation/template_a_isolation_rebaseline_status_v1.md)
- [product_region_practical_closure_status_v1.md](05_validation/family_a/product_region_practical_closure_status_v1.md)
- [bottom_region_practical_closure_status_v1.md](05_validation/family_a/bottom_region_practical_closure_status_v1.md)
- [gemini_copy_optimizer_closure_status_v1.md](05_validation/family_a/gemini_copy_optimizer_closure_status_v1.md)
- [copy_optimization_value_closure_status_v1.md](05_validation/family_a/copy_optimization_value_closure_status_v1.md)
- [product_annotation_text_closure_status_v1.md](05_validation/family_a/product_annotation_text_closure_status_v1.md)
- [copy_quality_closure_status_v1.md](05_validation/family_a/copy_quality_closure_status_v1.md)
- [template_a_text_contract_repair_and_product_region_text_closure_status_v1.md](05_validation/family_a/template_a_text_contract_repair_and_product_region_text_closure_status_v1.md)
- [family_a_practical_closure_status_v1.md](05_validation/family_a/family_a_practical_closure_status_v1.md)
- [family_a_practical_closure_verification_matrix_v1.md](05_validation/family_a/family_a_practical_closure_verification_matrix_v1.md)
- [bottom_gallery_helper_card_rebalance_status_v1.md](05_validation/family_a/bottom_gallery_helper_card_rebalance_status_v1.md)
- [family_a_commercial_fryer_min_delta_refinement_status_v1.md](05_validation/family_a/family_a_commercial_fryer_min_delta_refinement_status_v1.md)
- [family_a_fryer_live_diagnosis_micro_refinement_status_v1.md](05_validation/family_a/family_a_fryer_live_diagnosis_micro_refinement_status_v1.md)
- [family_a_product_annotation_shell_micro_structure_status_v1.md](05_validation/family_a/family_a_product_annotation_shell_micro_structure_status_v1.md)
- [family_a_bottom_text_finalization_status_v1.md](05_validation/family_a/family_a_bottom_text_finalization_status_v1.md)
- [family_a_fryer_hero_footer_blocker_removal_status_v1.md](05_validation/family_a/family_a_fryer_hero_footer_blocker_removal_status_v1.md)
- [family_a_fryer_truth_parity_and_footer_caption_closeout_status_v1.md](05_validation/family_a/family_a_fryer_truth_parity_and_footer_caption_closeout_status_v1.md)
- [family_a_fryer_anchor_rebind_and_left_rebalance_status_v1.md](05_validation/family_a/family_a_fryer_anchor_rebind_and_left_rebalance_status_v1.md)
- [family_a_single_primary_support_surface_status_v1.md](05_validation/family_a/family_a_single_primary_support_surface_status_v1.md)
- [bottom_behavior_contract_status_v1.md](05_validation/bottom_behavior_contract_status_v1.md)
- [product_region_annotation_contract_status_v1.md](05_validation/product_region_annotation_contract_status_v1.md)
- [scenario_region_resolver_and_renderer_parity_status_v1.md](05_validation/scenario_region_resolver_and_renderer_parity_status_v1.md)
- [text_layer_contract_closure_status_v1.md](05_validation/text_layer_contract_closure_status_v1.md)

Family B historical validation remains under the same validation path and is not reopened by current Family A work:

- [template_b_backend_generation_fix_status_v1.md](05_validation/template_b_backend_generation_fix_status_v1.md)
- [template_b_contract_correction_status_v1.md](05_validation/template_b_contract_correction_status_v1.md)
- [template_b_design_baseline_v1.md](05_validation/template_b_design_baseline_v1.md)
- [template_b_parity_and_visual_contract_status_v1.md](05_validation/template_b_parity_and_visual_contract_status_v1.md)

### 99 Archive

- [session_state_2026-03-31.md](99_archive/session_state_2026-03-31.md)

## Active Working State

- [current_branch_execution_log_v1.md](current_branch_execution_log_v1.md)
  Branch execution/state log. This is the active state file for current branch progress, merge-path notes, migration notes, and short-lived working facts.

## Legacy Nonformal Paths

Older grouped directories such as `01_architecture/`, `02_engineering/`, `03_stage_assessment/`, `04_external_reference/`, and `05_next_phase_plan/` may still exist as historical material in this workspace.

They are no longer the formal doc path.
The formal doc path is defined only by:

- this root index
- the root product baseline
- the root execution log
- the layered directories listed above

## Current Alignment

- `AGENTS.md` is rules only
- `CLAUDE.md` is shared state only
- this file is index only
- branch-local progress belongs in `current_branch_execution_log_v1.md`

## Current Mainline

- current temporary priority override = none; Family A fryer truth-parity and footer-caption closeout is merged into the current baseline
- Template A remains the active oracle line for shared-skill and commercial acceptance verification
- Template B remains unchanged during the current Family A-only refinement pass
