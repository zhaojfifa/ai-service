# Product Region Annotation Contract — Status v1

**Branch:** `PosterSop06-beautification-phase1`
**Date:** 2026-03-29
**Phase:** Post-beautification-phase1 — product annotation layer activation

---

## What This Document Records

This document records the end-to-end activation of the `product_anchor_callouts` feature mode as the live production mode for `template_dual_v2`. It covers:

- Template JSON mode switch
- Renderer path fix (`_resolve_feature_callout_layout` branch for fixed-anchor mode)
- New pipeline layers (`product_annotation_shell_layer`, `product_annotation_items_layer`)
- New `_build_product_annotation_contract_review()` pipeline function
- `product_annotation_mode` exposure in `behavior_modes`
- `product_annotation_contract_review` field in `RenderManifest`
- Frontend Stage 2 display: annotation chip + per-slot evidence panel
- Test suite: 179/179 pass

---

## What Was Already Done (Prior to This PR)

The `product_anchor_callouts` mode was established in `feature_anchor_callouts_contract_status_v1.md`:

- Resolver: `resolve_feature_behavior("product_anchor_callouts", ...)` already existed
- Contract review: `feature_contract_review` already emitted `connector_policy: "product_anchor_leader_line"` and `text_budget_policy: "anchor_fixed_budget"` for this mode
- Beautification: anchor dot, leader line, and shell visual already rendered in `beautification_phase1_status_v1.md`
- Template JSON: `feature_mode` was still set to `count_driven_callout_stack` — **activation not yet done**
- Renderer layout algorithm: `_resolve_feature_callout_layout()` was still using the old centering/stacking path for all modes — **fixed in this PR**

---

## Changes Made

### 1. `app/templates/specs/template_dual_v2.json`

Switched `feature_mode` from `count_driven_callout_stack` to `product_anchor_callouts`:

```json
"behavior_modes": {
  "hero_mode": "scenario_cover_product_contain",
  "feature_mode": "product_anchor_callouts",
  "bottom_mode": "title_gallery_split",
  "gallery_mode": "strip_local_visible_only"
}
```

This is the single activation gate. All downstream resolver, renderer, and contract review logic already branched on this value.

### 2. `app/services/poster2/renderer.py`

Fixed `_resolve_feature_callout_layout()` to branch on `product_anchor_callouts`:

**Old behavior (all modes):** centering/stacking algorithm distributes callouts vertically using spaced slot positions derived from the item count (1→center, 2→split, 3→compact, 4→dense).

**New behavior (product_anchor_callouts mode):** uses template-spec fixed anchor positions directly. No centering computation. Applies accent color overrides from resolved behavior, preserves anchor_x/anchor_y from `template.feature_callouts[i]`, caps at `feature_policy.visible_item_count` (max 3 for this mode).

**De-duplication rule:** when `product_anchor_callouts` is active, the old stacking path is never reached. Feature text is consumed through the product annotation path. There is no separate "feature right-stack" render — the same `_draw_feature_callout()` primitive is used, but called from fixed positions rather than the computed layout.

### 3. `app/services/poster2/template_behavior.py`

Extended `ResolvedTemplateBehavior.as_dict()` to expose `product_annotation_mode` as a distinct key in `behavior_modes`:

```python
product_annotation_mode = (
    self.feature_mode
    if self.feature_mode == "product_anchor_callouts"
    else "none"
)
```

This key is emitted in the renderer metadata payload under `template_behavior.behavior_modes.product_annotation_mode`.

### 4. `app/services/poster2/pipeline.py`

**New layers in `_build_layer_render_status()`:**

| Layer | Active when | Collapsed when |
|---|---|---|
| `product_annotation_shell_layer` | `feature_mode == "product_anchor_callouts"` | any other mode |
| `product_annotation_items_layer` | active + at least 1 item rendered | inactive or no items |

`reason_code` for inactive shell: `"product_annotation_mode_none"`
`reason_code` for inactive items: `"product_annotation_mode_none"` or `"no_annotation_items"`

**New `_build_product_annotation_contract_review()` function:**

Returns a dict with:

```
product_annotation_mode         "product_anchor_callouts" | "none"
annotation_active               bool
fixed_slot_count                3 (when active)
requested_annotation_items      list[str]  — from poster_spec.features
sanitized_annotation_items      list[str]  — empty strings dropped, whitespace stripped
rendered_annotation_items       list[str]  — capped at visible_item_count
slots                           list[SlotEvidence] — see below
product_region                  {rendered, bounds}
behavior_policy                 {connector_policy, marker_policy, text_budget_policy, max_items, positions_source}
feature_suppression             {feature_right_stack_suppressed, suppression_reason}
```

**Per-slot evidence (`slots[i]`):**

```
slot_index          0-based
slot_id             "product_annotation_slot_{i+1}"
rendered            bool
requested_text      str
sanitized_text      str
rendered_excerpt    str
truncation_applied  bool
anchor_x            int  — from template_spec.feature_callouts[i].anchor_x
anchor_y            int  — from template_spec.feature_callouts[i].anchor_y
label_bounds        {x, y, w, h}  — from template_spec.feature_callouts[i].label_box
connector_policy    "product_anchor_leader_line"
marker_policy       "dot_marker_accent_color"
positions_source    "template_spec_fixed"
anchor_color        str  — hex color
```

**`RenderManifest` field:**

```python
product_annotation_contract_review: dict = field(default_factory=dict)
```

Populated from `renderer_metadata_payload["product_annotation_contract_review"]` in `pipeline.py`.

### 5. `frontend/stage2.html` and `frontend/app.js`

**app.js** stores the backend payload into the diagnostic element:
```javascript
setJson('poster2-product-annotation-contract-review', data?.product_annotation_contract_review, '{}');
```

**stage2.html** changes:
- Hidden diagnostic `<pre id="poster2-product-annotation-contract-review">{}` element
- `product_annotation_mode` chip added to the modes strip (shown only when mode ≠ `"none"`)
- `product_region` row in the Resolver Layout now dispatches to `buildProductAnnotationDetail(annotationReview)` when `annotation_active` is true, otherwise falls back to `buildHeroDetail`
- `buildProductAnnotationDetail(annotationReview)` renders:
  - Mode badge
  - Per-slot text chain: requested → sanitized → rendered_excerpt, anchor coordinates, label bounds
  - Feature suppression badge
- `renderResolverLayout` signature accepts `annotationReview` as 8th arg
- `tryRebuild` parses `poster2-product-annotation-contract-review` and passes it through

**`docs/` sync:** `bash scripts/sync_frontend_to_docs.sh` confirmed in sync after this change.

---

## Test Suite

### Test changes

**`tests/poster2/test_contracts.py`**
- `test_real_template_dual_v2_loads`: updated `feature_mode` assertion from `"count_driven_callout_stack"` to `"product_anchor_callouts"`

**`tests/poster2/test_renderer.py`**
- `test_template_behavior_resolver_uses_template_metadata`: updated both `feature_mode` and `feature_policy.mode` assertions to `"product_anchor_callouts"`
- `test_template_behavior_resolver_promotes_dense_feature_and_bottom_into_template_policy`: added `feature_mode` override to `count_driven_callout_stack` (preserves box_h=56, gap=10 assertions which are specific to that mode's dense-quad rebalance path)
- `test_template_behavior_resolver_keeps_bottom_dense_case_local_when_feature_is_light`: same override (preserves `start_strategy == "centered_in_region"` assertion)

**`tests/poster2/test_pipeline.py`**
- Added `_load_template_with_feature_mode(feature_mode: str) -> TemplateSpec` helper
- `test_renderer_metadata_includes_layer_render_status`: updated `feature_mode` → `"product_anchor_callouts"`, added `product_annotation_mode` assertion, changed `connector_policy` → `"product_anchor_leader_line"`, `text_budget_policy` → `"anchor_fixed_budget"`
- `test_renderer_metadata_exposes_template_level_layout_policy_when_feature_and_bottom_are_both_dense`: switched to `_load_template_with_feature_mode("count_driven_callout_stack")` (preserves box_h=56, gap=10)
- `test_feature_contract_review_exposes_requested_sanitized_rendered_chain_with_empty_and_capped_items`: switched to `_load_template_with_feature_mode("count_driven_callout_stack")` (preserves visible_item_count == 4)

### Result

```
179 passed, 2 warnings in 15.66s
```

---

## De-Duplication Rule

When `feature_mode == "product_anchor_callouts"`:

1. `_resolve_feature_callout_layout()` uses fixed anchor positions from the template spec — the stacking/centering algorithm is bypassed entirely.
2. Feature text is consumed through the product annotation slot sequence (slots 0–2, capped at `visible_item_count`).
3. `product_annotation_shell_layer` and `product_annotation_items_layer` are marked rendered.
4. `feature_suppression.feature_right_stack_suppressed == true` in `product_annotation_contract_review`.
5. There is no double-render: the same `_draw_feature_callout()` primitive is used, but only from the fixed-position path.

---

## What Remains Outside This PR

- `product_annotation_contract_review` assertions are not yet in a dedicated test (covered indirectly by `test_renderer_metadata_includes_layer_render_status` via `product_annotation_mode` check). A targeted test for the full `_build_product_annotation_contract_review()` output can be added in a follow-on.
- The Puppeteer renderer does not yet produce the equivalent of `product_annotation_contract_review` — it returns a `ForegroundResult` without contract review fields. Parity is a future task.
- No new `RendererRoutingError` case is introduced for annotation failures; annotation evidence is always emitted even when items are absent (empty slots are marked `rendered: false`).

---

## Governance Position

This PR activates `product_anchor_callouts` as the production default for Family A. It does not introduce new geometry or beautification — the anchor positions, label box coordinates, connector style, and marker style were all established in `feature_anchor_callouts_contract_status_v1.md` and `beautification_phase1_status_v1.md`. The change here is:

1. Template JSON switch (activation gate)
2. Renderer algorithm fix (use fixed positions when in this mode)
3. Pipeline contract evidence (product annotation layers + review)
4. Frontend read-through (display backend evidence)

The `Structure → Control → Beautification` governance order is maintained: structure and control were proven in prior phases; this PR completes the activation without introducing new beautification work.
