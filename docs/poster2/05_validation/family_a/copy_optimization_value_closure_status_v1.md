# Family A Copy Optimization Value Closure Status v1

## Scope

Validation status for Template A copy optimization value closure.

## Bound Oracle

- template: `template_dual_v2`
- family: `Family A`
- optimizer scope: `title / subtitle / annotation`
- renderer executes backend truth

## Validated Outcomes

- mode-off review is emitted with `disabled_reason`
- dead accept/reject controls are hidden in Stage2
- mode-on review surfaces `changed_fields`
- metadata and UI both show:
  - `requested_text`
  - `sanitized_text`
  - `optimized_text`
  - `rendered_text`

## Focused Validation

- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'copy_optimization or annotation_slots_surface_fixed_budget_and_truncation_fields'`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py -k 'copy_optimization or generate_poster_v2_route_is_backward_compatible'`
- `./.venv/bin/python -m pytest -q tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py`

## Acceptance

Accepted when:

1. mode-off review is non-empty and explains why controls are unavailable
2. mode-on review carries suggestion lineage and diffs
3. operator accept / reject remains advisory copy-only state
4. Template B remains untouched
