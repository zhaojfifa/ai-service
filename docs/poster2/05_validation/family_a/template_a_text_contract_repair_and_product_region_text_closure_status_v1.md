# Template A Text Contract Repair And Product-Region Text Closure Status v1

## Status

Complete.

## Acceptance

Validated on Template A only with no geometry or ownership drift.

### Closed

- annotation slot 3 no longer loses meaning during sanitize
- explicit fit rewrite now exists for fixed annotation slots
- accepted optimization can drive rendered subtitle / annotation output
- subtitle cleanup and fit rewrite are visible in metadata
- Stage2 now surfaces the actual final text source chain

### Preserved

- `product_annotation_owner = product_region`
- 3 fixed annotation slots remain unchanged
- Template A geometry remains unchanged
- Template B remains unchanged

## Focused Validation

- `tests/poster2/test_pipeline.py -k 'copy_optimization or annotation_sanitization or subtitle_cleanup_and_fit_rewrite'`
- `tests/poster2/test_renderer.py`
- `tests/poster2/test_api.py -k 'copy_optimization or generate_poster_v2_route_is_backward_compatible'`
- `tests/test_stage2_guard_diagnostics_surface.py`
- `tests/test_frontend_docs_sync.py`

## Key Evidence

Expected Family A text lifecycle now includes:

- `requested_text`
- `sanitized_text`
- `cleanup_text`
- `fit_rewrite_text`
- `optimized_text`
- `accepted_text`
- `rendered_text`
- `rendered_text_source`

## Known Boundaries

- this pass does not reopen Family A geometry or bottom structure
- this pass does not expand into Template B
- this pass does not retune Gemini quality beyond Template A text contract closure
