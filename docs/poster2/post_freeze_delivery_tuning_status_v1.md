# Post-Freeze Delivery Tuning Status v1

**Date:** 2026-03-31  
**Scope:** Task-3 — Post-freeze delivery tuning only

## Read Before Implementation

- `CLAUDE.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `project_poster2_baseline_2026-03-30.md`
  - requested for this task, but not present in the repository
- `docs/poster2/README.md`

## Goal

Keep contract truth frozen and improve only delivery/capacity realization in already-established Family A surfaces:

- product annotation text
- header agent text
- subtitle / default split text capacity

This task does not change:

- bottom structure
- product geometry
- ownership truth
- mode names
- renderer responsibility boundaries

## What Is Already Live

The runtime code on `main` already contains the Task-3 delivery tuning.

### Header agent text

- `identity_left_agent_right.agent_char_budget = 28`
- `brand_block_two_line.agent_char_budget = 28`

### Product annotation text

- `product_anchor_callouts` char budgets:
  - `1 item -> 40`
  - `2 items -> 34`
  - `3 items -> 28`

### Bottom default split text capacity

Within the current `title_gallery_split` path:

- dense-quad: `title_char_budget >= 52`, `subtitle_char_budget >= 44`
- triplet: `title_char_budget >= 60`, `subtitle_char_budget >= 52`
- light-gallery: `title_char_budget >= 72`, `subtitle_char_budget >= 56`
- compact title-only split: `title_char_budget >= 52`

## Why This Is Delivery Tuning Only

- No region bounds changed.
- No slot bounds changed.
- No ownership fields changed.
- No new modes were introduced.
- No geometry was reopened.

This task only raises text-capacity floors inside already-frozen shells.

## Scoped Regression

Task-3 uses scoped regression only during development and PR completion:

```bash
/Users/tylerzhao/Code/ai-service/.venv/bin/python -m pytest tests/poster2/test_pipeline.py -q -k 'TestPostFreezeTextCapacity'
```

Coverage:

- default split title/subtitle capacity floors
- product annotation capacity floors
- header agent capacity floors

## Frozen Truth Preserved

The following remain frozen through Task-3:

- `annotation_owner_slot = product_primary_slot`
- `secondary_slot_annotation_ownership = false`
- bottom geometry
- product geometry
- diagnostics field names
- contract evidence field names

## Next Task

Future work must not reopen geometry or ownership under the name of delivery tuning.
