# Family A Bottom Region Practical Closure Status v1

## Scope

Validation status for the second practical closure step on Family A:

- bottom-region beautification
- bottom-region observability

This step excludes:

- product-region work
- Gemini copy optimizer integration
- Template B

## Bound Oracle

- template: `template_dual_v2`
- family: `Family A`
- bottom contract remains frozen:
  - `bottom_mode = title_gallery_split`
  - `gallery_mode = strip_local_visible_only`
  - subtitle ownership remains in `title_band_region`

## Observability Surface

Bottom diagnostics now surface:

- `bottom_mode`
- `subtitle_slot.state`
- `title_rendered`
- `subtitle_rendered`
- `gallery_distribution_policy`

The same truth is derived from backend-controlled bottom review data.

## Validation

Focused closure checks:

- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'family_a or accepted_output_keys or test_template_a_bottom_contract_review_surfaces_practical_observability_fields'`

Broad legacy note:

- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'bottom or family_a or accepted_output_keys'`
  still includes existing bottom-geometry/history failures outside this practical-closure scope

## Acceptance

Accepted when:

1. bottom diagnostics chips reflect backend truth
2. title/subtitle hierarchy polish lands without geometry drift
3. dense-quad gallery shell/items are visually tightened without behavior drift
4. focused Family A closure tests pass
