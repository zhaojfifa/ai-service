# poster2 Docs Index

## Directory Purpose

`docs/poster2/` is the poster2 documentation domain for architecture, engineering execution, stage assessment, external reference, and next-phase planning.

The directory is organized by responsibility, not by time:

- `01_architecture/`
  - stable business definition and architecture principles
- `02_engineering/`
  - implementation baselines, engineering execution, and acceptance-facing documents
- `03_stage_assessment/`
  - stage conclusions and transition/index notes
- `04_external_reference/`
  - external review inputs and migration judgments
- `05_next_phase_plan/`
  - forward plans for the next architecture layers

## Reading Order

Recommended reading order for the current repo state:

1. Architecture
   - [template_dual_v2_architecture_business_definition.md](01_architecture/template_dual_v2_architecture_business_definition.md)

2. Engineering baseline
   - [template_dual_v2_engineering_implementation_and_acceptance.md](02_engineering/template_dual_v2_engineering_implementation_and_acceptance.md)
   - [template_dual_v2_structural_rebuild_baseline_v1.md](02_engineering/template_dual_v2_structural_rebuild_baseline_v1.md)

3. Current stage assessment
   - [current_stage_assessment_and_engineering_path_update_v1.md](03_stage_assessment/current_stage_assessment_and_engineering_path_update_v1.md)
   - [index_update_stage_transition_v1.md](03_stage_assessment/index_update_stage_transition_v1.md)

4. External reference mapping
   - [external_reference_poster_design_review_and_migration_v1.md](04_external_reference/external_reference_poster_design_review_and_migration_v1.md)

5. Next-phase plans
   - [template_behavior_layer_plan_v1.md](05_next_phase_plan/template_behavior_layer_plan_v1.md)
   - [beautification_layer_plan_v1.md](05_next_phase_plan/beautification_layer_plan_v1.md)

## Current Stage Conclusion

Current conclusion from the docs and implemented repo state:

- poster2 has validated its contract-first baseline
- structure can be controlled
- content injection can be controlled
- outputs are reproducible and diagnosable
- the current architecture goal and basic route are correct
- the main remaining gap is not architecture direction, but engineering path and implementation maturity

The next phase focus is:

- Template Behavior Layer
- Beautification Pathfinding
- Geometry / Evidence Layer
- Render Service Layer

## Current Implementation Status

Current repo status for the engineering line on `PosterSop01`:

- `hero_mode` has been lifted into template metadata and resolved through a shared behavior resolver
- `feature_mode` has been lifted into template metadata and resolved through a shared feature policy layer
- the validated baseline remains `scenario_cover_product_contain`
- a second reusable hero mode now exists to prove renderer behavior is protocol-driven rather than hard-coded
- a second reusable feature mode now exists to prove feature count/connector/box policy is protocol-driven
- beauty token presets now cover multiple governed options for shell surface, border, shadow, accent, and text emphasis
- minimal beauty tokens exist, but broader preset expansion and Pillow visual parity still remain staged follow-up work
- geometry/evidence reinforcement remains intentionally limited until the dedicated evidence PR

Current non-goals remain:

- no free-collage/editor-first model
- no CSS-only tuning presented as architecture progress
- no five-region geometry redesign

## Current File Map

Present and organized in this repo now:

- `01_architecture/`
  - [template_dual_v2_architecture_business_definition.md](01_architecture/template_dual_v2_architecture_business_definition.md)
- `02_engineering/`
  - [template_dual_v2_engineering_implementation_and_acceptance.md](02_engineering/template_dual_v2_engineering_implementation_and_acceptance.md)
  - [template_dual_v2_structural_rebuild_baseline_v1.md](02_engineering/template_dual_v2_structural_rebuild_baseline_v1.md)
- `03_stage_assessment/`
  - [current_stage_assessment_and_engineering_path_update_v1.md](03_stage_assessment/current_stage_assessment_and_engineering_path_update_v1.md)
  - [index_update_stage_transition_v1.md](03_stage_assessment/index_update_stage_transition_v1.md)
- `04_external_reference/`
  - [external_reference_poster_design_review_and_migration_v1.md](04_external_reference/external_reference_poster_design_review_and_migration_v1.md)
- `05_next_phase_plan/`
  - [template_behavior_layer_plan_v1.md](05_next_phase_plan/template_behavior_layer_plan_v1.md)
  - [beautification_layer_plan_v1.md](05_next_phase_plan/beautification_layer_plan_v1.md)

Additional target files still not present in the current repo tree:

- `01_architecture/`
  - `poster_generation_product_design_baseline_v1.md`
- `02_engineering/`
  - `poster_sop01_engineering_kickoff_v1.md`
- `05_next_phase_plan/`
  - `render_service_layer_plan_v1.md`
  - `geometry_evidence_layer_plan_v1.md`

## Pointer To Next-Phase Plans

The next-phase planning directory is:

- [05_next_phase_plan](05_next_phase_plan)
