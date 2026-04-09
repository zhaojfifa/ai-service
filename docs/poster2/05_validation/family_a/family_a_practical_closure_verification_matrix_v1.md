# Family A Practical Closure Verification Matrix v1

## Scope

This matrix binds the accepted Family A live sample to the practical-closure surfaces that were added after the main freeze:

- product-region observability
- bottom-region observability
- Gemini copy optimization observability
- final validation binding

## Bound Canonical Sample

- template: `template_dual_v2`
- canonical sample: `annotation_triplet_gallery_triplet_subtitle_present`
- render engine used: `puppeteer`
- degraded: `false`
- structure_complete: `true`
- deliverable: `true`
- product_layout_mode: `single_primary`
- secondary_product_mode: `inset_hidden_no_reserve`
- subtitle present and rendered
- final hash: `194a61c2df4638038e0b61effd5c63b70a17fcb53bf404d4c68e0b03cd4f04b0`
- metadata sha256: `3698cb8da09c5ecda05eaacfc33e1669201e1a85598787b6942253357ea575ae`

## Verification Matrix

| Surface | Backend binding | UI binding | Acceptance state | Guard |
| --- | --- | --- | --- | --- |
| Product region | `product_contract_review` | product diagnostics chips | accepted | `product_layout_mode`, `secondary_product_mode`, `product_annotation_owner`, `visible_annotation_count` must stay backend-owned |
| Bottom region | `bottom_contract_review`, `title_text_layer`, `subtitle_text_layer` | bottom diagnostics chips | accepted | `bottom_mode`, `subtitle_slot.state`, rendered flags, gallery policy must match backend truth |
| Copy optimization | `copy_optimization_review` | copy optimization panel + accept/reject controls | accepted | Gemini may optimize copy only; no layout/control truth drift |
| Final validation | live acceptance metadata + runtime fixtures + golden matrix | Stage2 diagnostics + final artifact links | accepted | sample name, hashes, and frozen modes must remain aligned |

## Required Fixture Set

- `tests/poster2/fixtures/family_a_runtime_rebaseline_smoke.json`
- `tests/poster2/fixtures/family_a_golden_sample_matrix.json`
- `tests/poster2/fixtures/family_a_visual_smoke.json`
- `tests/poster2/fixtures/family_a_practical_closure_acceptance_v1.json`

## Required Diagnostic Set

- product-region diagnostics
- bottom-region diagnostics
- copy-optimization diagnostics
- final artifact / metadata links

## Follow-On Rule

This matrix closes the Family A practical-closure pass.
After this point, the next step may proceed to Family A anchored shared-skill extraction / adoption planning without reopening Template A contract, geometry, ownership, or Template B.
