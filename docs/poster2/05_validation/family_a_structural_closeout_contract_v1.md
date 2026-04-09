# Family A Structural Closeout — Contract v1

**Branch:** `PosterSop06-beautification-phase1`
**Date:** 2026-03-29
**Anchored to:** `poster_generation_product_design_baseline_v1.md`, `template_dual_v2_architecture_business_definition.md`

This document records the new contract modes and evidence fields introduced in the structural closeout phase. It does not replace the frozen bottom SOP baseline — it extends the mode surface with new first-class structural modes.

---

## 1. Governing Position

Per the product baseline and architecture definition:

- `Structure / Control / Beautification` order is non-negotiable
- Contract-first: structure is defined in the resolver, consumed by the renderer
- Frozen baseline (`bottom_shell_top = 728`, existing `title_gallery_split` / `title_only` / `gallery_only` modes) stays unchanged
- New modes introduce new geometry at the bottom-shell level, not patches to the frozen baseline
- Beautification starts only after this structural slice is stable

---

## 2. Scope A — Bottom Structural Expansion

### 2.1 New `bottom_layout_mode` values

Two new first-class bottom layout modes are added:

#### `text_only_expanded`

Purpose: maximum text capacity for Family A copy-heavy content. No gallery.

| Parameter | Value |
|---|---|
| `bottom_shell_top` | 656 |
| `bottom_shell_capacity` | 368px (y=656 to y=1024) |
| `title_band_height` | 180–220px (content-driven) |
| `title_line_clamp` | 2 or 3 |
| `title_char_budget` | 56–72 |
| `subtitle_line_clamp` | 2 or 3 |
| `subtitle_char_budget` | 60–80 |
| `gallery_strip_rendered` | always false |
| `bottom_mode` equivalence | superset of `title_only` |

Structural distinction from `title_only`:
- Shell starts 72px higher (y=656 vs y=728)
- title_band_height can reach 220px (vs 144px max in current frozen baseline)
- Supports 3-line title clamp where content warrants it
- subtitle budget can hold a full 2-line callout (~64 chars)

#### `text_gallery_expanded`

Purpose: materially larger title+subtitle alongside a gallery strip. Replaces dense-quad split compression.

| Parameter | Value |
|---|---|
| `bottom_shell_top` | 640 |
| `bottom_shell_capacity` | 384px (y=640 to y=1024) |
| `title_band_height` | 156–192px (content-driven) |
| `title_line_clamp` | 2 |
| `title_char_budget` | 44–60 |
| `subtitle_line_clamp` | 1 or 2 |
| `subtitle_char_budget` | 44–56 |
| `gallery_strip_rendered` | true (1–4 items) |
| `gallery_shell_height` | 88–120px (distribution-driven) |
| `bottom_mode` equivalence | superset of `title_gallery_split` |

Structural distinction from `title_gallery_split`:
- Shell starts 88px higher (y=640 vs y=728)
- total capacity = 384px vs 296px (+30%)
- Dense-quad no longer forces `title_char_budget=20`; expanded mode allows `title_char_budget=44` minimum
- Gallery strip gets taller items (88px shell height vs 68px for quad in frozen baseline)

### 2.2 Backward compatibility

Existing `title_gallery_split`, `title_only`, and `gallery_only` modes remain unchanged. They are not modified. The new modes are additive.

### 2.3 Resolver contract

New modes are gated in `_SUPPORTED_BOTTOM_MODES`. The resolver branch for each new mode:

- Sets its own `bottom_shell_top` constant (different from 728)
- Resolves `title_band_height` dynamically from content pressure (not hardcoded)
- Emits all the same evidence fields as the frozen baseline (`title_band_sizing_mode`, `title_band_growth_policy`, etc.)
- Exposes `bottom_layout_mode` as a new field in `behavior_policy`

### 2.4 Evidence additions

Each new mode emits:
- `bottom_layout_mode` (new field) — the name of the structural expansion mode
- `bottom_shell_top` — the actual starting y coordinate of the bottom shell
- `text_capacity_mode` — `expanded_text_only` or `expanded_text_gallery`

---

## 3. Scope B — Product Region Structural Upgrade

### 3.1 New `product_layout_mode` values

Two modes for the product region:

#### `single_primary` (default, backward-compatible)

- product region uses existing `product_slot` geometry unchanged
- `product_primary_slot` = current product_slot bounds
- `product_secondary_slot` = null (collapsed)
- All existing annotation behavior unchanged

#### `primary_secondary_dual`

- product region is expanded to accommodate two named product image slots
- `product_primary_slot`: upper portion of product region, larger, receives annotations
- `product_secondary_slot`: lower portion of product region, smaller, no annotations
- Annotation shell attaches to `product_primary_slot` only

Slot geometry (within `scenario_cover_product_contain` hero mode):

**product_primary_slot:**
```
x: 456, y: 188, w: 300, h: 310
fit: contain, align_x: center, align_y: center
pad_top: 16, pad_right: 12, pad_bottom: 8, pad_left: 12
```

**product_secondary_slot:**
```
x: 456, y: 506, w: 300, h: 202
fit: contain, align_x: center, align_y: center
pad_top: 8, pad_right: 12, pad_bottom: 10, pad_left: 12
```

Gap between primary and secondary: 8px (primary bottom = 498, secondary top = 506)

### 3.2 Minimum slot contract surfaces

The resolver must expose:
- `product_layout_mode` — `single_primary` | `primary_secondary_dual`
- `product_primary_slot` — bounds dict: `{x, y, w, h}`
- `product_secondary_slot` — bounds dict or `null`
- `product_secondary_slot_rendered` — bool
- `product_secondary_asset_policy` — `secondary_present` | `secondary_absent_collapsed`

### 3.3 Annotation shell independence

In `primary_secondary_dual` mode:
- Feature callout anchors remain on `product_primary_slot` (no geometry change to callout anchors)
- `product_annotation_shell` bounds are derived from primary slot only
- Secondary slot has no callout relationship

### 3.4 Backward compatibility

`single_primary` is the default when `product_layout_mode` is absent or unset. All existing behavior is preserved. No change to annotation mode or hero mode geometry.

---

## 4. Scope C — Text Layer Evidence

### 4.1 New layer-level evidence fields

Three new layers are promoted from incidental evidence to first-class layer evidence:

#### `title_text_layer`

```json
{
  "layer_id": "title_text_layer",
  "rendered": true,
  "slot_bounds": {"x": 112, "y": <resolved_y>, "w": 800, "h": <resolved_h>},
  "requested_text": "<raw title from PosterSpec>",
  "sanitized_text": "<after normalization>",
  "rendered_excerpt": "<what the renderer actually drew>",
  "truncation_applied": false,
  "line_clamp": 2,
  "char_budget": 44,
  "owner_region": "title_band_region"
}
```

#### `subtitle_text_layer`

```json
{
  "layer_id": "subtitle_text_layer",
  "rendered": true,
  "slot_bounds": {"x": 152, "y": <resolved_y>, "w": 720, "h": <resolved_h>},
  "requested_text": "<raw subtitle from PosterSpec>",
  "sanitized_text": "<after normalization>",
  "rendered_excerpt": "<what the renderer actually drew>",
  "truncation_applied": false,
  "line_clamp": 1,
  "char_budget": 28,
  "owner_region": "title_band_region"
}
```

#### `header_text_layer`

```json
{
  "layer_id": "header_text_layer",
  "rendered": true,
  "brand_text_slot": {
    "rendered": true,
    "requested_text": "<brand_name>",
    "rendered_excerpt": "<what drew>",
    "truncation_applied": false,
    "line_clamp": 1,
    "char_budget": 40,
    "slot_bounds": {"x": 244, "y": 88, "w": 416, "h": 36}
  },
  "agent_text_slot": {
    "rendered": true,
    "requested_text": "<agent_name>",
    "rendered_excerpt": "<what drew>",
    "truncation_applied": false,
    "line_clamp": 1,
    "char_budget": 24,
    "slot_bounds": {"x": 684, "y": 96, "w": 228, "h": 18}
  },
  "owner_region": "header_region"
}
```

### 4.2 Evidence placement

These three layers are emitted by new builders in `pipeline.py`:
- `_build_title_text_layer_evidence()`
- `_build_subtitle_text_layer_evidence()`
- `_build_header_text_layer_evidence()`

They are added to `renderer_metadata_payload` and exposed as `RenderManifest` fields:
- `title_text_layer`
- `subtitle_text_layer`
- `header_text_layer`

### 4.3 Truncation definition

`truncation_applied = True` when:
- `len(sanitized_text) > char_budget` AND the text was actually clipped (not just budget-gated)
- OR `len(rendered_excerpt) < len(sanitized_text)` by more than trailing whitespace

---

## 5. Scope D — Behavior Stability Preservation

The following must remain unchanged throughout this structural closeout:

- `product_annotation_mode = product_anchor_callouts` (live)
- `product_annotation_contract_review` schema unchanged
- `bottom_contract_review` schema for existing modes unchanged
- Stage 2 remains backend-evidence-driven; no editor-first drift
- `feature_mode`, `hero_mode`, `gallery_mode` semantics unchanged
- 187+ tests must pass after implementation

---

## 6. Success Conditions

This structural closeout is complete when:

1. `text_only_expanded` mode resolves correctly with materially larger text budgets than frozen baseline max
2. `text_gallery_expanded` mode resolves correctly and holds full title ("Upgrade your kitchen with ChefCraft") + subtitle ("April 24 we'll start using GitHub Copilot interaction") without truncation alongside 4 gallery items
3. `primary_secondary_dual` product mode exposes `product_primary_slot` and `product_secondary_slot` as named contract surfaces
4. `title_text_layer`, `subtitle_text_layer`, `header_text_layer` are emitted per generation with `truncation_applied` field
5. All existing mode behavior unchanged
6. Beautification may start only after tests pass against these success conditions

---

## 7. What This Document Is Not

- This is not a beautification plan
- This is not a renderer-specific patch
- This is not a CSS tuning document
- New modes must not be described as "visual improvements"
- New modes do not change the existing frozen bottom SOP baseline in any way

The structural closeout is a contract-first expansion of available mode space, followed by evidence promotion. It ends the micro-tuning loop without touching the frozen baseline.
