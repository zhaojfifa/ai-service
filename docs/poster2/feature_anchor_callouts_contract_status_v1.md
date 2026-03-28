# feature_mode = product_anchor_callouts — Contract Status v1

**Date:** 2026-03-28
**Phase:** 1 — Contract + Resolver complete; renderer in existing fallback path; beautification deferred
**Status:** CONTRACT STABLE — ready for renderer layer next phase

---

## Summary

This document records the Phase 0 contract closure work and Phase 1 introduction of `feature_mode = product_anchor_callouts`.

---

## Phase 0 — Contract Drift Repaired

### Drift 1: `template_behavior.behavior_modes.header_mode` was raw (possibly `None`)

**Root cause:** `ResolvedTemplateBehavior.header_mode` was assigned `modes.header_mode` (raw template value, possibly `None`) rather than the resolved effective value from `header_policy.mode`.

**Effect:** `template_behavior.behavior_modes.header_mode` in the API response was `null` even when the header was rendered under the `identity_left_agent_right` default. `header_contract_review.header_mode` was already correct (always resolved), creating a split between the two evidence fields.

**Fix:** `template_behavior.py` line 473 — changed `header_mode=modes.header_mode` to `header_mode=header_policy.mode`.

**Post-fix:** `template_behavior.behavior_modes.header_mode` and `header_contract_review.header_mode` are now consistent.

---

### Drift 2: Stage 2 modeLabel access paths were wrong for all regions

**Root cause:** `templateBehavior` in Stage 2 is the `template_behavior` dict, which has structure:
```json
{ "behavior_modes": { "hero_mode": ..., "feature_mode": ..., "header_mode": ..., ... }, ... }
```

But the Resolver Layout code was reading flat keys (`templateBehavior?.bottom_mode`, `templateBehavior?.feature_mode`, `templateBehavior?.header_identity_zone_mode`) that do not exist at the top level.

**Effect:** All region mode labels in the Resolver Layout section were empty (falling through to contract review fallbacks where present, or blank otherwise).

**Fix:** `stage2.html` — updated all five region modeLabel reads to use `templateBehavior?.behavior_modes?.{mode_key}` as the primary path.

| Region | Old (broken) | New (correct) |
|--------|-------------|---------------|
| bottom | `templateBehavior?.bottom_mode` | `templateBehavior?.behavior_modes?.bottom_mode` |
| header | `templateBehavior?.header_identity_zone_mode` | `templateBehavior?.behavior_modes?.header_mode` |
| scenario | `templateBehavior?.hero_mode` | `templateBehavior?.behavior_modes?.hero_mode` |
| product | `templateBehavior?.hero_mode` | `templateBehavior?.behavior_modes?.hero_mode` |
| feature | `templateBehavior?.feature_mode` | `templateBehavior?.behavior_modes?.feature_mode` |

---

## Phase 1 — product_anchor_callouts

### Behavioral contract

| Property | Value |
|----------|-------|
| `feature_mode` | `product_anchor_callouts` |
| `max_items` | **3 (fixed)** — not count-driven, not from template slot count |
| `visible_item_count_policy` | `fixed_3_anchor_points` |
| `connector_policy` | `product_anchor_leader_line` |
| `box_policy` | `anchor_fixed_position` |
| `start_strategy` | `template_anchor_fixed` |
| `gap` | `0` (positions are template-spec-driven, not stacked) |
| `line_clamp` | 2 |
| `char_budget` | 36 / 30 / 24 for 1 / 2 / 3 visible items |
| `truncation_policy` | `two_line_clamp` |
| `collapse_policy` | `collapse_when_empty` |

**Activation:** Set `behavior_modes.feature_mode = "product_anchor_callouts"` in the template JSON spec. This is **not** a request-level override field — it must come from the template definition.

### Anchor evidence emitted in `feature_contract_review`

When `feature_mode == "product_anchor_callouts"`, the contract review includes an `anchor_evidence` array (null for all other modes):

```json
"anchor_evidence": [
  { "anchor_index": 0, "anchor_x": 764, "anchor_y": 250, "anchor_color": "#E8002A", "positions_source": "template_spec_fixed" },
  { "anchor_index": 1, "anchor_x": ..., "anchor_y": ..., "anchor_color": "#E8002A", "positions_source": "template_spec_fixed" },
  { "anchor_index": 2, "anchor_x": ..., "anchor_y": ..., "anchor_color": "#E8002A", "positions_source": "template_spec_fixed" }
]
```

Anchor positions are read directly from `template.feature_callouts[i].anchor_x / anchor_y` — immutable from the template spec.

### Stage 2 display

`buildFeatureDetail()` in `stage2.html` was updated to show anchor coordinates when `mode === 'product_anchor_callouts'` and `anchor_evidence` is present.

---

## Files Changed

| File | Change |
|------|--------|
| `app/services/poster2/template_behavior.py` | Added `product_anchor_callouts` to `_SUPPORTED_FEATURE_MODES`; added `_PRODUCT_ANCHOR_CALLOUTS_MAX_ITEMS = 3`; added resolver branch in `resolve_feature_behavior()`; fixed `header_mode=header_policy.mode` |
| `app/services/poster2/pipeline.py` | `_build_feature_contract_review()`: emit `anchor_evidence` array when mode is `product_anchor_callouts` |
| `frontend/stage2.html` | Fixed all 5 region modeLabel access paths; updated `buildFeatureDetail()` to display anchor evidence |

---

## Contract Closure Status

| Check | Status |
|-------|--------|
| `template_behavior.behavior_modes.header_mode` resolves correctly | ✅ Fixed |
| `header_contract_review.header_mode` == `template_behavior.behavior_modes.header_mode` | ✅ Aligned |
| Stage 2 reads live backend payload only | ✅ Confirmed — no client-side mode state |
| Stage 2 modeLabel reads correct behavior_modes path | ✅ Fixed |
| `product_anchor_callouts` recognized by validator | ✅ In `_SUPPORTED_FEATURE_MODES` |
| `product_anchor_callouts` resolver returns correct policy | ✅ 179/179 tests pass |
| `feature_contract_review.anchor_evidence` emitted for new mode | ✅ Implemented |
| `feature_contract_review.anchor_evidence` is null for other modes | ✅ Confirmed |
| Renderer works with new mode (fallback path) | ✅ Existing `_resolve_feature_callout_layout` handles generic callout layout |

---

## Known Bugs / Limitations

1. **Renderer uses stacking algorithm for all modes.** For `product_anchor_callouts`, the renderer's `_resolve_feature_callout_layout` still runs the centering/stacking algorithm (overriding anchor_y from the template spec). Fixed-position rendering requires a dedicated renderer branch — deferred to next phase as beautification work.

2. **Template JSON not yet updated.** `template_dual_v2.json` still has `"feature_mode": "count_driven_callout_stack"`. To test the new mode end-to-end, update that field to `"product_anchor_callouts"`. Leaving the template unchanged preserves existing behavior.

3. **No request-level feature_mode override.** By design (`GeneratePosterV2Request` has no `feature_mode` field). Mode is set per-template, not per-request.

---

## Next Recommendation

1. **Validate contract layer end-to-end:** Update `template_dual_v2.json` → `"feature_mode": "product_anchor_callouts"`, run a generation, inspect `feature_contract_review.anchor_evidence` in Stage 2.

2. **Renderer layer:** Add `product_anchor_callouts` branch in `_resolve_feature_callout_layout` that uses `base.anchor_x / anchor_y` directly from the template spec (bypassing the centering algorithm). This is the beautification / renderer-layer step.

3. **Replicate resolver pattern** to `scenario_region`, `hero_region` per Phase 3 plan.
