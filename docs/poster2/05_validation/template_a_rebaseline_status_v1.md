# Template A Rebaseline Status v1

## Scope

Template A only: `template_dual_v2`

This document freezes the repaired Template A runtime as the accepted baseline before structure/control/evidence abstraction and bounded beautification freeze work.

## Frozen Runtime Truth

The accepted Template A runtime remains:

- `template_id = template_dual_v2`
- `render_engine_used = puppeteer`
- `degraded = false`
- `structure_complete = true`
- `deliverable = true`
- `hero_mode = scenario_cover_product_contain`
- `feature_mode = product_anchor_callouts`
- `product_annotation_mode = product_anchor_callouts`
- `header_mode = identity_left_agent_right`
- `bottom_mode = title_gallery_split`
- `gallery_mode = strip_local_visible_only`
- `product_annotation_owner = product_region`

## Canonical Smoke And Golden Matrix

The deterministic baseline is anchored by:

- `tests/poster2/fixtures/family_a_runtime_rebaseline_smoke.json`
- `tests/poster2/fixtures/family_a_visual_smoke.json`
- `tests/poster2/fixtures/family_a_golden_sample_matrix.json`

The current golden matrix covers:

- 3 annotation items
- 3 gallery items
- 4 gallery items
- subtitle present
- subtitle empty

## Accepted Output Surface

The accepted Family A output whitelist is stored in:

- `tests/poster2/fixtures/family_a_accepted_output_keys.json`

Family A payloads must remain family-clean:

- only A-family region/evidence keys are allowed
- no Template B parity surface is allowed
- no Template B region/evidence keys are allowed

## Abstraction Surfaces Added

Family A now exposes explicit family-scoped abstraction helpers for:

- structure surface
- control surface
- visible-truth filtering

These helpers are family-scoped and do not merge A/B semantics.

## Validation Gate

Template A rebaseline is accepted only when:

1. canonical runtime smoke matches fixture
2. accepted output keys match fixture
3. family control surface remains frozen
4. geometry evidence exposes the explicit Family A structure entry
5. no Template B residue appears in Template A payloads
