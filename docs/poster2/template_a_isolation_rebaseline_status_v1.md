# Template A Isolation Rebaseline Status v1

## Scope

Family A only: `template_dual_v2`

This document records the post-isolation current-good baseline after:

- family-aware evidence isolation
- family-aware renderer/material isolation
- anti-crossline rules and regression gates

It does not redefine Family A architecture.
It freezes the repaired baseline as the next acceptable starting point for future Family A validation or beautification gate work.

## Root Rules Followed

- contract-first
- renderer executes family truth
- family routing must be explicit
- beautification cannot substitute for isolation or contract repair
- Family B contract remained untouched during this rebaseline pass

## Current-good Runtime Summary

Canonical Family A runtime smoke now expects:

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

The canonical accepted runtime subset is stored in:

- `tests/poster2/fixtures/family_a_runtime_rebaseline_smoke.json`

## Accepted Output Keys

Family A accepted region keys:

- `header_region`
- `scenario_region`
- `product_region`
- `feature_region`
- `bottom_region`
- `title_band_region`
- `gallery_strip_region`

Canonical Family A visible-truth smoke keys:

- `header_region`
- `product_region`
- `title_text_layer`
- `gallery_strip_region`

Family B-only keys must not appear in Family A runtime payloads:

- `logo_banner_region`
- `top_copy_region`
- `materials_strip_region`
- `product_hero_region`
- `description_region`

`template_b_parity_review` may remain on the HTTP/schema surface for compatibility, but Family A must keep it empty.

## Golden Smoke Anchors

To stabilize future regression checks, the following deterministic smoke anchors are recorded in:

- `tests/poster2/fixtures/family_a_visual_smoke.json`

Anchors:

- canonical Family A Pillow render SHA-256
- canonical Family A structured HTML payload SHA-256

These are engineering smoke anchors, not product-facing golden approvals.

## Validation Gates

Family A rebaseline now depends on these gates:

1. runtime smoke fixture match
2. visible-truth whitelist / cross-family absence
3. family-aware renderer asset routing
4. family-aware HTML routing
5. existing Family A regression path

## Remaining Limits

- no fresh live Chromium artifact bundle was stored in-repo during this step
- the canonical runtime smoke uses deterministic local test fixtures rather than deployed-environment assets
- a future Family A beautification freeze gate should regenerate live artifacts on top of this rebaseline, not bypass it
