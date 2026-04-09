# Family A Four-Layer Verification Matrix v1

## Scope

This document binds the current canonical Family A live acceptance sample to the four-layer poster2 governance model:

1. structure
2. control
3. beautification
4. evidence

It is a verification matrix skeleton, not a branch log.
Execution details remain in [../current_branch_execution_log_v1.md](../current_branch_execution_log_v1.md).

## Bound Canonical Live Sample

- template: `template_dual_v2`
- family: `Family A`
- canonical sample name: `annotation_triplet_gallery_triplet_subtitle_present`
- render engine used: `puppeteer`
- degraded: `false`
- structure_complete: `true`
- deliverable: `true`
- product_layout_mode: `single_primary`
- secondary_product_mode: `inset_hidden_no_reserve`
- subtitle state: `present / rendered`
- final hash: `194a61c2df4638038e0b61effd5c63b70a17fcb53bf404d4c68e0b03cd4f04b0`
- metadata sha256: `3698cb8da09c5ecda05eaacfc33e1669201e1a85598787b6942253357ea575ae`

## Verification Matrix

| Layer | Family A anchor | Runtime / fixture anchor | Live acceptance binding | Current status | Next closure check |
| --- | --- | --- | --- | --- | --- |
| Structure | [template_dual_v2_structural_rebuild_baseline_v1.md](../02_architecture/template_dual_v2_structural_rebuild_baseline_v1.md) | `family_a_structure_surface_v1` + `family_a_accepted_output_keys.json` | canonical sample region order / bounds / slot bounds match Family A-only surfaces | accepted | keep Family A structure family-clean while shared-skill adoption continues |
| Control | [template_dual_v2_architecture_business_definition.md](../02_architecture/template_dual_v2_architecture_business_definition.md) | `family_a_control_surface_v1` + `family_a_runtime_rebaseline_smoke.json` | `hero_mode`, `feature_mode`, `bottom_mode`, `gallery_mode`, `product_layout_mode`, `secondary_product_mode` unchanged | accepted | prevent control drift during future Family B planning |
| Beautification | [template_a_beautification_freeze_status_v1.md](template_a_beautification_freeze_status_v1.md) | `family_a_beautification_freeze_pack_v1` | current live sample uses frozen A shell/text/annotation/bottom visual pack with no geometry change | accepted | keep freeze pack consumption skill-scoped; no style exploration without explicit reopen |
| Evidence | [family_isolation_rules_v1.md](../02_architecture/family_isolation_rules_v1.md) | `family_a_evidence_surface_v1` + `family_a_runtime_rebaseline_smoke.json` | Family A payload remains free of Template B evidence/parity residue | accepted | maintain family whitelist and backend-truth diagnostics |

## Required Companion Fixtures

- `tests/poster2/fixtures/family_a_runtime_rebaseline_smoke.json`
- `tests/poster2/fixtures/family_a_accepted_output_keys.json`
- `tests/poster2/fixtures/family_a_golden_sample_matrix.json`
- `tests/poster2/fixtures/family_a_visual_smoke.json`

## Required Runtime Skill Anchors

- `family_a_structure_surface_v1`
- `family_a_control_surface_v1`
- `family_a_beautification_freeze_pack_v1`
- `family_a_evidence_surface_v1`

## Follow-On Use

Before any Family A practical closure pass or any Family B skill adoption planning begins, this matrix should be used as the checklist anchor to confirm:

- the canonical sample name still matches the accepted live sample
- the fixture and acceptance metadata still describe the same Family A sample
- the four Family A skill surfaces remain aligned with the accepted runtime
