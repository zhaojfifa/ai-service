# poster2 Documentation Index

`docs/poster2/README.md` is the single official entry point for poster2 documentation on this branch.

Its job is not to replace the underlying documents. Its job is to keep the document system anchored, ordered, and readable so engineering work stays on one contract-first path.

## What This Document System Is For

poster2 documentation is organized as a governed document system, not a loose collection of implementation notes.

This system exists to prevent four recurring failures:

- readers skipping the product baseline and jumping straight into implementation detail
- stage or rollout documents being read without architecture context
- renderer behavior being mistaken for template truth
- local engineering progress drifting away from the agreed contract-first path

When there is ambiguity, start from the product baseline, then move downward into architecture, engineering baselines, and next-phase plans.

## The Two Complementary Views

poster2 uses two complementary views of the same system:

- Product governance view: `Structure -> Control -> Beautification`
- Template execution view: `Background -> Shell -> Content`

These are not competing models.

- `Structure / Control / Beautification` is the product-governance and rollout order.
- `Background / Shell / Content` is the template execution-layer view.

The governance view explains what must be proven in sequence.
The execution view explains how the template is actually organized at runtime.

## Non-Negotiable Architectural Position

All poster2 documents in this directory should remain aligned to the following position:

- poster2 is not free collage
- poster2 is contract-first
- renderer is the execution layer, not the template truth-source
- behavior should be lifted from CSS/Python branching into declarative template modes
- beautification must not hide structure or control failures

If a stage or implementation document appears to weaken any of the above, read it as subordinate to the baseline documents below.

## Document Groups

Use the documentation in the following groups. The groups matter because they define how readers should descend from product intent into engineering execution.

### 1. Product Baseline

Start here first. Do not skip this section.

- [poster_generation_product_design_baseline_v1.md](poster_generation_product_design_baseline_v1.md)
  The top-level poster2 anchor. Defines the product essence, the two template families, and the governance order `Structure -> Control -> Beautification`.

This baseline is the primary reference whenever later documents appear to diverge.

### 2. Architecture Guidance

Read this section after the product baseline. It defines the stable architecture shape that engineering must preserve.

- [template_dual_v2_architecture_business_definition.md](template_dual_v2_architecture_business_definition.md)
  Family A engineering definition under the product baseline.
- [template_family_region_matrix_v1.md](template_family_region_matrix_v1.md)
  Region-level framing for template-family structure.
- [template_family_slot_contract_baseline_v1.md](template_family_slot_contract_baseline_v1.md)
  Slot contract baseline and SSOT expectations.
- [renderer_routing_and_fallback_rules_v1.md](renderer_routing_and_fallback_rules_v1.md)
  Execution routing and fallback rules. This explains renderer responsibility; it does not redefine template truth.
- [quality_guard_and_structure_completeness_v1.md](quality_guard_and_structure_completeness_v1.md)
  Quality and structure-completeness guardrails for contract-first generation.

### 3. Engineering Baseline & Progress

Read this section only after the product baseline and architecture guidance. These documents describe implementation closure and stage progression, not a replacement architecture.

- [template_dual_v2_structural_rebuild_baseline_v1.md](template_dual_v2_structural_rebuild_baseline_v1.md)
  Structural rebuild baseline for the validated Family A template path.
- [template_dual_v2_engineering_implementation_and_acceptance.md](template_dual_v2_engineering_implementation_and_acceptance.md)
  Engineering implementation and acceptance framing for template_dual_v2.
- [current_stage_assessment_and_engineering_path_update_v1.md](current_stage_assessment_and_engineering_path_update_v1.md)
  Current stage judgment and engineering path update. Read this as stage assessment under the restored baseline, not as a new top-level definition.
- [index_update_stage_transition_v1.md](index_update_stage_transition_v1.md)
  Transition/index helper for stage movement and reading continuity.
- [poster_generation_project_restructure_checklist_v1.md](poster_generation_project_restructure_checklist_v1.md)
  Supporting project-level restructuring checklist for keeping implementation aligned.
- [poster2_product_flow_reviewable_v1.md](poster2_product_flow_reviewable_v1.md)
  Phase 3 PR-4 closure record: minimum operator loop (Stage 1 → Stage 2 → Stage 3) reviewable under contract-first baseline. Records Stage 2 live contract panel integration and all-region Resolver Layout evidence.
- [bottom_behavior_contract_status_v1.md](bottom_behavior_contract_status_v1.md)
  Bottom region resolver SOP baseline: behavior policies, metadata, gallery distribution, text evidence chain, and `gallery_input_count_raw -> gallery_input_count_normalized -> gallery_requested_count -> gallery_visible_count` closure. Frozen as Phase 2 baseline.
- [feature_anchor_callouts_contract_status_v1.md](feature_anchor_callouts_contract_status_v1.md)
  Phase 0 contract drift repair + Phase 1 `product_anchor_callouts` feature mode contract. Records header_mode drift fix, Stage 2 modeLabel path fixes, and new mode resolver/evidence contract.
- [beautification_phase1_status_v1.md](beautification_phase1_status_v1.md)
  Beautification Phase 1 closure: minimal beauty-token-driven improvements to `glass_light` shell surface, `soft_line` border, `soft` shadow, and feature connector/marker visual. No geometry or behavior change. 153/153 tests pass.
- [product_region_annotation_contract_status_v1.md](product_region_annotation_contract_status_v1.md)
  Product annotation layer activation: `product_anchor_callouts` switched to live production mode for `template_dual_v2`. Records renderer algorithm fix (fixed-anchor path), new pipeline layers (`product_annotation_shell_layer`, `product_annotation_items_layer`), `_build_product_annotation_contract_review()` per-slot evidence, `product_annotation_mode` in behavior_modes, frontend Stage 2 evidence display. 179/179 tests pass.
- [product_region_contract_closure_status_v1.md](product_region_contract_closure_status_v1.md)
  PR-3 product region contract closure: 7 owner surfaces frozen, annotation ownership enforced (primary slot only, secondary never owner), `primary_secondary_dual_v2` geometry declared final, `geometry_frozen` / `annotation_owner_slot` / `secondary_slot_annotation_ownership` / `owner_surfaces` emitted in contract evidence. 242/242 tests pass.
- [post_freeze_delivery_tuning_status_v1.md](post_freeze_delivery_tuning_status_v1.md)
  Task-3 delivery-only closeout: header agent text, product annotation text, and default split subtitle/title capacity tuned without any contract, geometry, or ownership change.
- [text_layer_contract_closure_status_v1.md](text_layer_contract_closure_status_v1.md)
  PR-4 text ownership freeze and feature delegation: `_TEXT_LAYER_OWNER_MAP` / `_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS` / `_PRODUCT_ANNOTATION_TEXT_OWNER_REGION` declared as constants; all three text layers emit `ownership_frozen = True`; `feature_view_mode = delegated_diagnostic` enforces no dual ownership when annotation active. 252/252 tests pass.

### 4. Next-Phase Plans

Read this section only after the validated baseline and current stage judgment are understood.

- [template_behavior_layer_plan_v1.md](template_behavior_layer_plan_v1.md)
  Control-layer rollout plan: behavior lifted into declarative template modes.
- [beautification_layer_plan_v1.md](beautification_layer_plan_v1.md)
  Beautification-layer rollout plan, downstream of contract and behavior stability.

## Recommended Reading Order

If you are new to poster2, use this order:

1. [poster_generation_product_design_baseline_v1.md](poster_generation_product_design_baseline_v1.md)
2. [template_dual_v2_architecture_business_definition.md](template_dual_v2_architecture_business_definition.md)
3. [template_family_region_matrix_v1.md](template_family_region_matrix_v1.md)
4. [template_family_slot_contract_baseline_v1.md](template_family_slot_contract_baseline_v1.md)
5. [renderer_routing_and_fallback_rules_v1.md](renderer_routing_and_fallback_rules_v1.md)
6. [quality_guard_and_structure_completeness_v1.md](quality_guard_and_structure_completeness_v1.md)
7. [template_dual_v2_structural_rebuild_baseline_v1.md](template_dual_v2_structural_rebuild_baseline_v1.md)
8. [template_dual_v2_engineering_implementation_and_acceptance.md](template_dual_v2_engineering_implementation_and_acceptance.md)
9. [current_stage_assessment_and_engineering_path_update_v1.md](current_stage_assessment_and_engineering_path_update_v1.md)
10. [index_update_stage_transition_v1.md](index_update_stage_transition_v1.md)
11. [template_behavior_layer_plan_v1.md](template_behavior_layer_plan_v1.md)
12. [beautification_layer_plan_v1.md](beautification_layer_plan_v1.md)
13. [poster2_product_flow_reviewable_v1.md](poster2_product_flow_reviewable_v1.md)

If you are working on implementation and want to jump ahead, do not start from a phase-plan document. Re-anchor on the product baseline first, then re-enter through the architecture guidance set.

## Family Framing

The top-level baseline keeps two template families in scope:

- `Family A: Campaign Explainer Poster`
- `Family B: Product Sheet / Product Story Poster`

`template_dual_v2` belongs to Family A. Current structure, behavior, and beautification work should continue to be interpreted inside that family framing rather than as a general free-form poster model.

## Usage Rules For Future Updates

When adding or updating poster2 docs:

- keep this README as the official entry point
- anchor new stage documents back to the product baseline
- do not present rollout plans as architecture replacements
- do not present renderer behavior as template truth
- do not describe local CSS tuning as architecture progress

If a new document cannot be placed cleanly into one of the groups above, that is a signal to check for architecture drift before adding it.

## Current Engineering Phase (as of 2026-03-30)

### PR-4 — Text ownership freeze and feature delegation — COMPLETE

Text layer owner surfaces are now frozen as constants. Feature delegation is explicit and no-dual-ownership is enforced in contract evidence.

**What is established:**
- `_TEXT_LAYER_OWNER_MAP` declares `header_text_layer → header_region`, `title_text_layer → title_band_region`, `subtitle_text_layer → title_band_region`
- `_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS` names exactly `product_annotation_slot_1/2/3` as `product_region` surfaces
- All three text layers emit `ownership_frozen = True` in pipeline evidence
- `feature_contract_review.feature_view_mode = "delegated_diagnostic"` when annotation active; `"owner"` otherwise
- No dual ownership: when annotation active, `feature_region.visible_item_count = 0` and `rendered_feature_items = []`
- `product_annotation_contract_review` emits `annotation_text_owner_region`, `annotation_slot_ids`, `ownership_frozen`
- Dead code (no-`template` builder copies) removed from `pipeline.py`
- 252/252 tests pass

**Prior phases still established:**
- PR-3: product owner surfaces frozen, dual-image geometry frozen
- PR-2: bottom mode boundary freeze and completeness rules
- PR-1: canonical bottom mode runtime truth unification
- Bottom SOP resolver baseline (Phase 2)
- Beautification Phase 1: shell/shadow/connector visual refinement

**What is NOT yet done:**
- `header_region` `identity_zone_mode` resolver wiring
- Pillow secondary slot rendering parity (contract-only)
- Puppeteer text layer evidence parity (Pillow-only)
- Beautification layer remains downstream of all-region behavior stability

### Next steps

1. `header_region` — complete `identity_zone_mode` resolver wiring
2. `scenario_region` Pillow safe_fill parity fix
3. Preview-path / generation-path parity (Puppeteer vs Pillow)
4. Beautification layer planning (after all-region behavior stability)

---

## Notes On Branch-Local Materials

This branch may still contain historical or grouped copies under subdirectories such as `01_architecture/`, `02_engineering/`, `03_stage_assessment/`, `04_external_reference/`, and `05_next_phase_plan/`.

Those materials may remain useful as branch-local history or organization aids, but the root-level documents listed in this README are the formal poster2 document system for this branch.
