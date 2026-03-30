# Bottom Mode Stabilization Status v1

**Task:** Task-1 — Stabilize `text_gallery_expanded` and `gallery_only` runtime modes
**Status:** Complete
**Date:** 2026-03-30

## Scope

This task is intentionally narrow:

- stabilize `text_gallery_expanded`
- stabilize `gallery_only`
- no geometry rewrite
- no beautification
- no frontend layout inference
- no product-region finalization
- no delivery/capacity tuning

## Goal

Both modes must satisfy the same health standard already expected from `text_only_expanded`:

- `degraded = false`
- `structure_complete = true`
- `deliverable = true`
- no silent fallback

## What Was Added

Runtime/API guards now require both modes to expose:

- `requested_bottom_mode`
- `effective_bottom_mode`
- `bottom_layout_mode`
- `bottom_mode_override_reason`

Stage 2 diagnostics guards now require the backend-driven panel to keep showing:

- requested/effective runtime line
- layout mode line
- mode availability for `text_gallery_expanded`
- mode availability for `gallery_only`

## Fresh Runtime Verification

Temporary local HTTP runtime wrapper used only to provide fake assets and storage while hitting real `/api/v2/generate-poster`.

### `text_gallery_expanded`

- request id: `p2-task1-text-gallery`
- trace id: `bb2c29ea-c595-4866-8c2a-89040aa4edcb`
- result:
  - `degraded = false`
  - `structure_complete = true`
  - `deliverable = true`
  - `requested_bottom_mode = text_gallery_expanded`
  - `effective_bottom_mode = text_gallery_expanded`
  - `bottom_layout_mode = text_gallery_expanded`
  - `bottom_mode_override_reason = request_override_applied`
  - `title_band_region.rendered = true`
  - `gallery_strip_region.rendered = true`

### `gallery_only`

- request id: `p2-task1-gallery-only`
- trace id: `dd3ef904-af95-4eb1-acd3-ecc2dfa34c71`
- result:
  - `degraded = false`
  - `structure_complete = true`
  - `deliverable = true`
  - `requested_bottom_mode = gallery_only`
  - `effective_bottom_mode = gallery_only`
  - `bottom_layout_mode = gallery_only`
  - `bottom_mode_override_reason = request_override_applied`
  - `title_band_region.rendered = false`
  - `gallery_strip_region.rendered = true`

## Validation

Command:

```bash
python -m pytest tests/poster2/test_api.py tests/poster2/test_pipeline.py tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py
```

Result:

- `103 passed, 2 warnings`

## Conclusion

`text_gallery_expanded` and `gallery_only` are now explicitly stabilized as live runtime modes with API-path and Stage 2 diagnostics coverage. This task does not alter geometry, capacity policy, or visual styling.
