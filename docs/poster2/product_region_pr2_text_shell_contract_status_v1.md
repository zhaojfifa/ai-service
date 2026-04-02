# PR-2 — Product Text-Shell Contract Closure Status v1

**Branch:** `claude/festive-heisenberg`
**Status:** Complete
**Date:** 2026-04-02

---

## 1. Scope

PR-2 formalizes `product_text_shell` as an explicit, named sibling shell inside `product_region`.

In scope:
- Add `_PRODUCT_TEXT_SHELL_*` frozen constants to `template_behavior.py`
- Add `"product_text_shell_layer"` to `_FROZEN_PRODUCT_OWNER_SURFACES`
- Add `product_text_shell_bounds` field to `ResolvedProductBehavior` dataclass
- Add `product_text_shell_*` keys to `layout_metrics`
- Add `product_text_shell_layer` to Pillow `layer_render_status` (pipeline.py)
- Add `product_text_shell_layer` to HTML renderer layer status (renderer.py)
- Add `product_text_shell_layer` section to `_build_product_contract_review()` with bounds, owner truth, and no-compete evidence
- Add focused tests for all of the above

Not in scope for PR-2:
- CSS / HTML changes
- UI wiring
- Bottom / header / scenario behavior
- Beautification
- Annotation geometry tuning
- char_budget or line_clamp tuning

---

## 2. Precondition: PR-1 Truth Loaded

From `product_region_pr1_boundary_closure_status_v1.md`:

| Surface | x | y | w | h | bottom edge |
|---|---|---|---|---|---|
| `product_region` / `product_card_shell_layer` | 456 | 188 | 472 | 540 | 728 |
| `product_canvas_shell_layer` | 456 | 188 | 300 | 540 | 728 |
| `product_primary_slot` (dual) | 456 | 188 | 300 | 310 | 498 |
| `product_secondary_slot` (dual) | 456 | 518 | 300 | 210 | 728 |

Frozen: `height: 540px` added to `.region-shell-product` CSS override. Outer shell bottom at y=728 matches canvas shell and secondary slot.

---

## 3. Product Text Shell Contract

### Geometry derivation

From `template_dual_v2.json` feature_callouts (product_anchor_callouts mode):

| Callout | anchor_x | anchor_y | label_box x | label_box y | label_box w | label_box h | bottom |
|---|---|---|---|---|---|---|---|
| 1 | 764 | 250 | 784 | 216 | 144 | 60 | 276 |
| 2 | 764 | 350 | 784 | 316 | 144 | 60 | 376 |
| 3 | 764 | 416 | 784 | 416 | 144 | 60 | 476 |

Product text shell = bounding rect of all 3 label slots:
- `x = 784` = product_region_x (456) + canvas_shell_w (300) + 28px offset
- `y = 216` = product_region_y (188) + 28px top pad
- `w = 144` = label slot width (all slots share the same width)
- `h = 260` = bottom_of_slot_3 (476) − top_of_slot_1 (216)

```
product_text_shell = {x: 784, y: 216, w: 144, h: 260}
```

### Sibling relationship

```
product_region {x:456, y:188, w:472, h:540}
├── product_canvas_shell_layer {x:456, y:188, w:300, h:540}   ← image surface
│   ├── product_primary_slot {x:456, y:188, w:300, h:310}
│   └── product_secondary_slot {x:456, y:518, w:300, h:210}
└── product_text_shell_layer {x:784, y:216, w:144, h:260}     ← text surface (this PR)
    ├── product_annotation_slot_1 {x:784, y:216, w:144, h:60}
    ├── product_annotation_slot_2 {x:784, y:316, w:144, h:60}
    └── product_annotation_slot_3 {x:784, y:416, w:144, h:60}
```

### No-compete verification

- `product_text_shell_layer` left edge: x = 784
- `product_canvas_shell_layer` right edge: x + w = 456 + 300 = 756
- 784 ≥ 756 → text shell starts 28px to the right of canvas shell right edge ✓
- Text shell does NOT overlap image canvas width

### Owner surface truth

- `product_text_shell_layer` is added to `_FROZEN_PRODUCT_OWNER_SURFACES`
- Owner region: `"product_region"` (matches `_PRODUCT_ANNOTATION_TEXT_OWNER_REGION`)
- `feature_region` is not a parallel text owner when `product_anchor_callouts` is active

---

## 4. Files Changed

1. `app/services/poster2/template_behavior.py`
   - Add `_PRODUCT_TEXT_SHELL_X/Y/W/H` constants
   - Add `"product_text_shell_layer"` to `_FROZEN_PRODUCT_OWNER_SURFACES`
   - Add `product_text_shell_bounds` field to `ResolvedProductBehavior`
   - Add `product_text_shell_*` keys to `layout_metrics`
   - Populate `product_text_shell_bounds` in resolver

2. `app/services/poster2/pipeline.py`
   - Add `product_text_shell_layer` to Pillow `layer_render_status` (after `product_canvas_shell_layer`)
   - Add `product_text_shell_layer` section to `_build_product_contract_review()`

3. `app/services/poster2/renderer.py`
   - Add `product_text_shell_layer` to HTML renderer layer status (after `product_canvas_shell_layer`)

4. `tests/poster2/test_pipeline.py`
   - New class `TestProductTextShellContract`

---

## 5. Frozen Unchanged

- `_PRODUCT_CANVAS_SHELL_W`, `_PRODUCT_REGION_OUTER_W` — unchanged
- `product_primary_slot`, `product_secondary_slot`, `product_single_primary_slot` — unchanged
- `_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS` — unchanged
- `_PRODUCT_ANNOTATION_TEXT_OWNER_REGION` — unchanged (still `"product_region"`)
- CSS, HTML — unchanged
- `annotation_shell` dynamic bounding box — unchanged
- `char_budget`, `line_clamp` values — unchanged
- Bottom, header, scenario — unchanged
- Beautification — unchanged

---

## 6. Inspectable Evidence After PR-2

`product_contract_review.product_text_shell_layer` will contain:

```json
{
  "rendered": true,
  "reason_code": null,
  "bounds": {"x": 784, "y": 216, "w": 144, "h": 260},
  "owner_region": "product_region",
  "owner_surface": "product_text_shell_layer",
  "text_does_not_compete_with_canvas": true
}
```

`product_annotation_contract_review` will include the existing per-slot chain:
- `requested_text` → `sanitized_text` → `rendered_excerpt`
- `truncation_applied`
- `char_budget`, `line_clamp` via `behavior_policy`

`renderer_metadata.layer_render_status.product_text_shell_layer` will appear as a sibling of `product_canvas_shell_layer`.

---

## 7. Acceptance Criteria

- `product_text_shell_layer` is in `_FROZEN_PRODUCT_OWNER_SURFACES` ✓
- `product_text_shell_bounds` appears in `layout_metrics` ✓
- `product_text_shell_layer` appears in `product_contract_review` with correct bounds ✓
- `text_does_not_compete_with_canvas` is `True` ✓
- `product_text_shell_layer` appears in renderer `layer_render_status` ✓
- `feature_region` is not a parallel text owner when annotation is active ✓
- Focused tests pass ✓

---

## 8. Risks / Follow-up for PR-C Only

- PR-C: capacity / label bounds / clamp / connector tuning — NOT started here
- `annotation_shell` dynamic bounding box remains alongside `product_text_shell` fixed bounds; both coexist without conflict
- No CSS change in this PR; the HTML rendering of text shell appearance is PR-C territory
