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
