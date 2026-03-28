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
  Bottom region resolver SOP baseline: behavior policies, metadata, gallery distribution, text evidence chain. Frozen as Phase 2 baseline.
- [feature_anchor_callouts_contract_status_v1.md](feature_anchor_callouts_contract_status_v1.md)
  Phase 0 contract drift repair + Phase 1 `product_anchor_callouts` feature mode contract. Records header_mode drift fix, Stage 2 modeLabel path fixes, and new mode resolver/evidence contract.

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

## Current Engineering Phase (as of 2026-03-28)

### Phase 2: bottom SOP baseline — ESTABLISHED

The `bottom_region` resolver path is the agreed SOP baseline for the behavior layer rollout.

**What is established:**
- `bottom_mode`, `gallery_mode`, `gallery_count`, `title`, `subtitle` are the declared behavior contract for `bottom_region`
- These controls are always wired in Stage 2 regardless of template eligibility (bottom mode selection bug fixed)
- Stage 2 page refactored to Resolver Layout design: two-column layout, left panel holds copy + renderer + bottom controls, right panel shows Poster Preview and Resolver Layout with all region rows
- `frontend/` and `docs/` are in sync

**What this proves under the product baseline:**
- The `Structure → Control → Beautification` governance order holds: bottom structure was proven in Phase 1, bottom control behavior is now the SOP baseline in Phase 2
- The resolver path is repeatable: declare mode → resolve bounds → renderer consumes → evidence emitted

**What is NOT yet done:**
- Other regions (header, scenario, product, feature) do not yet have full resolver coverage
- Beautification layer has not started; it remains downstream of behavior stability across all regions

### Phase 3: next steps

Apply the bottom resolver pattern to remaining regions:
1. `header_region` — complete `identity_zone_mode` resolver wiring
2. `scenario_region`, `product_region`, `feature_region` — resolver coverage
3. Preview-path / generation-path parity收口 (Puppeteer vs Pillow)
4. Beautification layer planning (after all-region behavior stability)

---

## Notes On Branch-Local Materials

This branch may still contain historical or grouped copies under subdirectories such as `01_architecture/`, `02_engineering/`, `03_stage_assessment/`, `04_external_reference/`, and `05_next_phase_plan/`.

Those materials may remain useful as branch-local history or organization aids, but the root-level documents listed in this README are the formal poster2 document system for this branch.
