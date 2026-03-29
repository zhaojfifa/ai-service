# product region annotation contract status v1

## 1. Task Objective

Introduce `product_region` as an independent contract layer with a separate product annotation review path, without redesigning Family A or letting frontend invent product layout semantics.

This status file records the first backend contract pass only.

## 2. Scope Preserved

The following remain unchanged:

- `product_region` stays inside the existing five-region baseline
- renderer remains the execution layer
- Stage 2 remains a backend-payload viewer
- no drag-and-drop
- no arbitrary annotation count
- no free-form editor behavior

## 3. Independent Product Contract Added

The backend now exposes a separate `product_contract_review` alongside:

- `hero_contract_review`
- `header_contract_review`
- `feature_contract_review`
- `bottom_contract_review`

The product contract is modeled as:

- `product_region`
- `product_canvas_shell_layer`
- `product_image_layer`
- `product_annotation_shell_layer`
- `product_annotation_items_layer`

## 4. product_annotation_mode

Supported modes:

- `none`
- `right_stack_mirror`
- `product_anchor_callouts`

Current template baseline:

- `template_dual_v2.behavior_modes.product_annotation_mode = "none"`

This preserves the validated baseline while allowing contract-level product annotation support to exist now.

## 5. First Executable Policies

The resolver now emits independent product annotation policy:

- `annotation_count_policy`
- `annotation_connector_policy`
- `annotation_marker_policy`
- `annotation_shell_policy`
- `annotation_bounds_policy`
- `text_budget_policy`
- `line_clamp`
- `char_budget`
- `layout_metrics`

First-version constraints:

- fixed 3 annotation anchors max
- no arbitrary annotation count
- no request-level override
- template mode remains the source of truth

## 6. Evidence Added

`product_contract_review` now exposes:

- `product_annotation_mode`
- `requested_product_source`
- `effective_product_source`
- `rendered_product_source`
- `product_source`
- `requested_annotation_items`
- `sanitized_annotation_items`
- `rendered_annotation_items`
- `product_region`
- `product_canvas_shell_layer`
- `product_image_layer`
- `product_annotation_shell_layer`
- `product_annotation_items_layer`
- `behavior_policy`
- `annotation_slots`

Each `annotation_slots[]` item can expose:

- `slot_id`
- `requested_text`
- `sanitized_text`
- `rendered_excerpt`
- `rendered`
- `truncation_applied`
- `reason_code`
- `anchor_index`
- `anchor_x`
- `anchor_y`
- `anchor_color`
- `label_bounds`
- `connector_policy`
- `marker_policy`
- `positions_source`

## 7. Renderer / Status Honesty

This round preserves contract honesty:

- product annotation evidence exists even when the current template mode is `none`
- if a non-`none` mode is resolved but the current renderer path is not the active execution path, layer status uses `annotation_renderer_pending`
- the system does not claim product annotation rendering when only contract metadata exists

## 8. Stage 2 Alignment

Stage 2 now reads `product_contract_review` from the live backend payload and renders it in the existing Resolver Layout panel.

Stage 2 still does **not**:

- compute annotation bounds
- compute connector geometry
- invent mode names

## 9. Current Status

Status:

- contract exists
- evidence exists
- Stage 2 live payload path exists
- baseline template remains on `product_annotation_mode = none`
- renderer-specific independent product annotation expression remains deferred

## 10. Remaining Risks

- `right_stack_mirror` is contract-declared but not yet a dedicated renderer expression path
- `product_anchor_callouts` is contract-ready, but truthful layer status depends on the current renderer path actually using the anchored callout mode
- this is a backend-first contract layer, not a finished art-direction system

## 11. Next Recommendation

After bottom count closure is accepted:

1. keep `product_contract_review` stable
2. verify Stage 2 operator review on live payload
3. if the product annotation mode is promoted in template metadata later, wire the dedicated renderer branch without changing the review schema

---

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
