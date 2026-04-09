# bottom subtitle wrap and expansion status v1

## Scope

PR-7B only: close the remaining bottom text issue.

- `title_gallery_split`: move subtitle from single-line ellipsis fallback to controlled two-line clamp
- `text_only_expanded`: ensure title/subtitle text-layer slot bounds fully follow expanded bottom truth

## Frozen Unchanged

- header
- product geometry
- feature delegation
- beautification
- email/save workflow
- bottom structure
- gallery distribution structure

## Root Cause

Two separate closures were still incomplete:

1. `title_gallery_split`
   - active subtitle policy still had single-line ellipsis branches in the gallery-present expanded split path
   - this left the bottom contract and final HTML vars on a one-line subtitle path in the remaining primary cases

2. `text_only_expanded`
   - bottom layout metrics and geometry evidence already exposed full-width truth
   - but `title_text_layer` / `subtitle_text_layer` evidence still read frozen template slot `x/w`, so text-layer metadata could lag behind the expanded band width

## What Changed

- `title_gallery_split` gallery-present subtitle cases now use controlled two-line clamp in the active expanded split path
- subtitle evidence and final HTML vars now agree on `subtitle_line_clamp = 2` for the remaining subtitle-present split cases
- `text_only_expanded` text-layer evidence now reads `title_band_x/w` and `subtitle_slot_x/w` from resolved layout metrics
- PR-7B5 refines the remaining closure:
  - dense-quad `title_gallery_split` keeps two-line subtitle clamp but extends excerpt capacity
  - subtitle-present `text_only_expanded` moves the text stack upward through pad rebalance without reopening budgets

## title_gallery_split Policy Table

| Case | Before | After |
| --- | --- | --- |
| gallery + subtitle (balanced/default) | `single_line_ellipsis_inside_expanded_split_title_band`, clamp `1`, subtitle slot `h=28` | `two_line_clamp_inside_expanded_split_title_band`, clamp `2`, subtitle slot `h=44` |
| dense quad + subtitle | `single_line_ellipsis_inside_expanded_split_title_band`, clamp `1`, subtitle slot `h=28` | `two_line_clamp_inside_expanded_split_title_band`, clamp `2`, subtitle slot `h=44`, excerpt budget `72` |

## text_only_expanded Propagation Parity

Expanded bottom truth remains:

- `title_band_x = 96`
- `title_band_w = 832`
- `subtitle_slot_x = 136`
- `subtitle_slot_w = 752`

PR-7B closes the remaining text-layer parity gap:

- `title_text_layer.slot_bounds` now follows expanded `title_band_x/w`
- `subtitle_text_layer.slot_bounds` now follows expanded `subtitle_slot_x/w`
- final HTML still uses `--title-band-left` / `--title-band-width` from resolver vars
- PR-7B5 then rebalances subtitle-present vertical allocation:
  - `title_content_pad_top = 24`
  - `title_content_pad_bottom = 24`
  - dense proof: `title_slot_y = 784`, `subtitle_slot_y = 880`

## Files Changed

- `app/services/poster2/template_behavior.py`
- `app/services/poster2/pipeline.py`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_renderer.py`
- `docs/poster2/bottom_subtitle_wrap_and_expansion_status_v1.md`

## Acceptance Evidence

- `title_gallery_split` subtitle policy now resolves to `two_line_clamp_inside_expanded_split_title_band`
- `title_gallery_split` subtitle clamp now resolves to `2`
- dense-quad `title_gallery_split` excerpt budget now resolves to `72` while keeping stable two-line clamp
- `text_only_expanded` text-layer evidence no longer falls back to stale standard-band width
- final HTML still emits `--title-band-left: 96px` and `--title-band-width: 832px` for `text_only_expanded`
- `text_only_expanded` subtitle-present vertical stack is less bottom-heavy while keeping non-truncation in the primary proof

## Next PR Only

copy / email workflow only
