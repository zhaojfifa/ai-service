# Family A Fryer Live Diagnosis Micro-Refinement Status v1

## Scope accepted

- Template A only
- current 3-column header preserved
- Stage1 / Stage2 UI structure unchanged
- no geometry drift
- no ownership drift
- no Template B work

## Verified

- header remains `identity_left_agent_right`
- fryer right-column header text carries through as `Commercial Electric Fryer Series`
- subtitle remains rendered instead of collapsing under the fryer Family A path
- product annotation remains fixed-slot and product-owned
- structured HTML now consumes the current fixed annotation slot contract
- dense-quad strip keeps 4 items but gains more horizontal breathing
- Family A visual smoke fixture updated to the new structured HTML baseline

## Focused runtime evidence

Current fryer sample summary:

- `structure_complete = true`
- `deliverable = true`
- `header_requested_agent_text = Commercial Electric Fryer Series`
- `header_rendered_agent_excerpt = Commercial Electric Fryer Series`
- `subtitle_slot.state = rendered`
- `rendered_subtitle_excerpt = Fast heating · precise control`
- `product_annotation_owner = product_region`
- annotation slot bounds:
  - slot 1: `x=784 y=216 w=176 h=76`
  - slot 2: `x=784 y=316 w=176 h=76`
  - slot 3: `x=784 y=416 w=176 h=76`
- `gallery_distribution_policy = dense_quad`
- dense-quad item layouts:
  - `x=106/314/522/730`
  - `w=188`
  - `h=60`

## Focused validation run

- `bash scripts/sync_frontend_to_docs.sh`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py` -> `117 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'test_metadata_dense_quad_split_uses_expanded_quad_policies or test_template_a_payload_filters_out_template_b_visible_truth_and_parity_keys or family_a_runtime_rebaseline_matches_fixture or test_template_a_product_annotation_slots_surface_fixed_budget_and_truncation_fields'` -> `3 passed`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py` -> `18 passed`

## Updated baseline evidence

- `family_a_visual_smoke.json`
  - `pillow_sha256 = 0eef4d7511552e31d8f820e68b63c574d8198239791b56289b3e9d5303328c29`
  - `structured_html_sha256 = a0262d44c5637a4f361b14c813768acfe5e8df2bb009ce3bf127a0f0be273b5b`

## Remaining risks

- this is a bounded micro-refinement, not a reopened Family A redesign track
- a fresh external live artifact bundle is still separate from this local runtime verification
- existing historical bottom backlog outside the fryer micro-refinement scope remains unchanged
