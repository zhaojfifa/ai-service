# Family A Gemini Copy Optimizer Closure Status v1

## Scope

Validation status for the third practical closure step on Family A:

- Gemini copy optimizer integration
- optimization lineage observability
- operator accept / reject loop

This step excludes:

- Template B
- geometry changes
- ownership changes
- bottom redesign
- renderer control ownership

## Bound Oracle

- template: `template_dual_v2`
- family: `Family A`
- Gemini is optimizer only
- renderer executes backend-resolved truth

## Validation Surface

Backend now emits `copy_optimization_review` with lineage for:

- `title`
- `subtitle`
- `annotation_items`

Stage2 now exposes:

- optimization mode
- decision
- optimizer used
- applied-to-rendered-output state
- changed fields
- title / subtitle / annotation lineage summary

## Focused Validation

- `./.venv/bin/python -m py_compile app/schemas/poster2.py app/services/poster2/contracts.py app/services/poster2/gemini_copy_optimizer.py app/services/poster2/copy_optimizer.py app/services/poster2/pipeline.py app/main.py tests/poster2/test_pipeline.py tests/poster2/test_api.py tests/test_stage2_guard_diagnostics_surface.py`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'copy_optimization or family_a or accepted_output_keys'`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py -k 'copy_optimization or generate_poster_v2_route_is_backward_compatible'`
- `./.venv/bin/python -m pytest -q tests/poster2/test_renderer.py`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py`

## Broad Legacy Note

- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'bottom or family_a or accepted_output_keys'`
  still includes the existing bottom-geometry/history failures that predate this PR-3 scope

## Acceptance

Accepted when:

1. `copy_optimization_review` is present for Family A optimization runs
2. pending optimization does not alter rendered Family A text
3. accepted optimization updates rendered Family A text without changing annotation count
4. Stage2 and backend show the same optimization trace
5. Template B remains unchanged
