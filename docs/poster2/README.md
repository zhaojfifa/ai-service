# poster2 Documentation Index

`docs/poster2/README.md` is the formal index only.
It defines the reading path and the formal doc path.
It does not carry branch history, pasted progress logs, or one-off process notes.

## Entry Order

Read in this order for poster2 work:

1. [poster_generation_product_design_baseline_v1.md](poster_generation_product_design_baseline_v1.md)
2. [template_dual_v2_architecture_business_definition.md](template_dual_v2_architecture_business_definition.md)
3. [template_family_region_matrix_v1.md](template_family_region_matrix_v1.md)
4. [template_family_slot_contract_baseline_v1.md](template_family_slot_contract_baseline_v1.md)
5. [renderer_routing_and_fallback_rules_v1.md](renderer_routing_and_fallback_rules_v1.md)
6. [quality_guard_and_structure_completeness_v1.md](quality_guard_and_structure_completeness_v1.md)

Then read only the task-relevant status / plan / progress documents.

## Formal Document Path

### Product Baseline

- [poster_generation_product_design_baseline_v1.md](poster_generation_product_design_baseline_v1.md)

### Architecture Guidance

- [template_dual_v2_architecture_business_definition.md](template_dual_v2_architecture_business_definition.md)
- [template_family_region_matrix_v1.md](template_family_region_matrix_v1.md)
- [template_family_slot_contract_baseline_v1.md](template_family_slot_contract_baseline_v1.md)
- [renderer_routing_and_fallback_rules_v1.md](renderer_routing_and_fallback_rules_v1.md)
- [quality_guard_and_structure_completeness_v1.md](quality_guard_and_structure_completeness_v1.md)

### Engineering Baseline And Progress

- [template_dual_v2_structural_rebuild_baseline_v1.md](template_dual_v2_structural_rebuild_baseline_v1.md)
- [template_dual_v2_engineering_implementation_and_acceptance.md](template_dual_v2_engineering_implementation_and_acceptance.md)
- [current_stage_assessment_and_engineering_path_update_v1.md](current_stage_assessment_and_engineering_path_update_v1.md)
- [index_update_stage_transition_v1.md](index_update_stage_transition_v1.md)
- [poster2_product_flow_reviewable_v1.md](poster2_product_flow_reviewable_v1.md)
- [bottom_behavior_contract_status_v1.md](bottom_behavior_contract_status_v1.md)
- [bottom_vertical_anchoring_closure_status_v1.md](bottom_vertical_anchoring_closure_status_v1.md)
- [bottom_mode_family_contract_closure_status_v1.md](bottom_mode_family_contract_closure_status_v1.md)
- [feature_anchor_callouts_contract_status_v1.md](feature_anchor_callouts_contract_status_v1.md)
- [product_region_annotation_contract_status_v1.md](product_region_annotation_contract_status_v1.md)
- [product_region_contract_closure_status_v1.md](product_region_contract_closure_status_v1.md)
- [product_region_container_and_annotation_text_contract_status_v1.md](product_region_container_and_annotation_text_contract_status_v1.md)
- [text_layer_contract_closure_status_v1.md](text_layer_contract_closure_status_v1.md)
- [scenario_region_resolver_and_renderer_parity_status_v1.md](scenario_region_resolver_and_renderer_parity_status_v1.md)
- [beautification_phase1_status_v1.md](beautification_phase1_status_v1.md)
- [bottom_mode_switch_closure_status_v1.md](bottom_mode_switch_closure_status_v1.md)
- [email_copy_optimizer_and_optional_attachment_status_v1.md](email_copy_optimizer_and_optional_attachment_status_v1.md)
- [generation_quality_and_copy_optimization_status_v1.md](generation_quality_and_copy_optimization_status_v1.md)
- [visual_polish_phase1_status_v1.md](visual_polish_phase1_status_v1.md)

### Plans

- [template_behavior_layer_plan_v1.md](template_behavior_layer_plan_v1.md)
- [beautification_layer_plan_v1.md](beautification_layer_plan_v1.md)

### Working State

- [current_branch_execution_log_v1.md](current_branch_execution_log_v1.md)
  Branch execution/state log. This is the active state file for current branch progress, merge-path notes, and short-lived working facts.
- [document_alignment_status_note_v1.md](document_alignment_status_note_v1.md)
  Current document-path alignment note.
- [bottom_region_contract_skill_v1.md](bottom_region_contract_skill_v1.md)
  Proposed reusable bottom-region contract-to-implementation skill distilled from the successful bottom SOP path.

## What Is Not Formal Doc Path

The following should not be treated as the formal doc path:

- grouped copy folders such as `01_architecture/`, `02_engineering/`, `03_stage_assessment/`, `04_external_reference/`, `05_next_phase_plan/`
- one-off session notes
- pasted branch-local materials
- external reference dumps

These may remain as branch-local history or reference material, but the formal path is defined only by the root-level documents listed above.

## Current Alignment

- `AGENTS.md` is rules only
- `CLAUDE.md` is shared state only
- this file is index only
- branch-local progress belongs in `current_branch_execution_log_v1.md`

## Current Engineering Phase

- poster2 has entered Storage / Copy / Email Closure engineering
- Stage3 is backend-driven through `poster_key` and `poster_record`
- bottom remains maintenance-only; PR-S2 closed the Stage2 bottom mode switch canonicalization/parity bug
- copy quality tightening is now complete on top of the frozen poster contract baseline
- current priority is deployed-environment validation for Gemini quality and Resend live closure behavior

## Next Steps

- deployed-environment validation for Gemini optimizer output quality
- deployed-environment validation for Resend attachments and live closure behavior
- keep bottom in maintenance mode only unless a request-state / parity regression appears
- keep poster contract, bottom truth, product annotation truth, renderer routing, and beautification frozen during closure work
