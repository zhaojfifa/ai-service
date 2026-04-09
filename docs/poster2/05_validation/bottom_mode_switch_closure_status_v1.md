# bottom mode switch closure status v1

## Scope

PR-S2 only: investigate and close the Stage2 post-generate bottom mode switch failure for the bottom mode family.

This is a request-state / normalization / parity closure, not a beautification pass and not a bottom redesign.

## Positioning

- bottom remains in maintenance mode only
- bottom contract architecture stays frozen
- header, product geometry, feature ownership, email flow, and renderer routing are out of scope
- Stage2 preview path and final generate path must consume the same canonical bottom request truth

## What Was Read First

1. `AGENTS.md`
2. `CLAUDE.md`
3. `docs/poster2/README.md`
4. `docs/poster2/current_branch_execution_log_v1.md`
5. `docs/poster2/bottom_behavior_contract_status_v1.md`

Additional note:

- latest stage2 screenshots / console / network payload evidence was not present as a tracked workspace artifact in this run
- latest `text_only_expanded` runtime evidence was therefore taken from the current pipeline/runtime test path instead of an external pasted payload

## Problem Reproduced

The Stage2 control surface still exposed:

- `title_gallery_split`
- `text_gallery_expanded`
- `title_only`
- `text_only_expanded`
- `gallery_only`

But the frontend request-state chain did not canonicalize bottom mode before:

- storing `stage2State.poster2.bottomContract`
- hydrating controls
- building the bottom request preview
- building the final generate payload

This meant a stale legacy token could survive after a successful generate and leak into the next regenerate request.

The concrete bad token was:

- `title_only_expand`

That token is not a valid backend runtime mode. The backend canonicalizes:

- `title_only -> text_only_expanded`

but does not accept:

- `title_only_expand`

## Root Cause

The leaking code path was entirely frontend request-state logic:

- `ensurePoster2BottomContractState(...)`
- `syncPoster2BottomContractFromControls(...)`
- `buildPoster2BottomRequestState(...)`
- `initPoster2BottomContractControls(...)`

Each of those paths trusted the raw bottom mode value and forwarded it unchanged.

So the bug was not:

- bottom contract design
- renderer geometry
- CSS behavior
- backend effective-mode diagnostics

It was a Stage2 state canonicalization gap.

## What Changed

Added a frontend/runtime canonicalization helper:

- `canonicalizePoster2BottomMode(rawMode)`

Rules:

- `title_only -> text_only_expanded`
- `title_only_expand -> text_only_expanded`
- invalid / unknown token -> `title_gallery_split`

Applied that canonicalization to:

- bottom contract state initialization
- control-to-state sync
- request preview construction
- final generate payload construction
- control hydration so the active UI state matches the canonical runtime state

## Before / After Request Payload Examples

Before:

```json
{
  "bottom_mode": "title_only_expand",
  "gallery_mode": "strip_local_visible_only"
}
```

After:

```json
{
  "bottom_mode": "text_only_expanded",
  "gallery_mode": "strip_local_visible_only"
}
```

Legacy alias before runtime:

```json
{
  "bottom_mode": "title_only"
}
```

Canonical request truth used by preview and final generate:

```json
{
  "bottom_mode": "text_only_expanded"
}
```

## Contract / Parity Verification

Verified bottom mode family expectations remain intact:

- `title_gallery_split`
  - `title_band_region` present
  - `gallery_strip_region` present
- `text_gallery_expanded`
  - `title_band_region` present
  - `gallery_strip_region` present
- `text_only_expanded`
  - `title_band_region` present
  - `gallery_strip_region` collapsed by design
- `gallery_only`
  - `title_band_region` collapsed by design
  - `gallery_strip_region` present

Diagnostics still expose and agree on:

- `requested_bottom_mode`
- `effective_bottom_mode`
- `bottom_layout_mode`
- `bottom_mode_override_reason`

## Files Changed

- `frontend/app.js`
- `docs/app.js`
- `tests/poster2/test_api.py`
- `tests/test_stage2_guard_diagnostics_surface.py`
- `docs/poster2/bottom_mode_switch_closure_status_v1.md`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/README.md`
- `CLAUDE.md`

## Validation

- focused Stage2 surface / mirror checks
- focused API bottom-mode diagnostics checks
- focused pipeline bottom-mode invariants

## Remaining Risks

- this closes the request-state/parity failure, not the broader bottom text/layout family
- any remaining subtitle-capacity or visual-allocation issue should stay as a known bottom maintenance issue while Storage / Copy / Email work continues

## One-Line State

Stage2 bottom mode switching is now canonicalized before runtime, preview and final generate share the same bottom-mode truth, and legacy stale tokens no longer leak into backend requests.
