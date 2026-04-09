# Family A Structural Closeout — Diagnosis v1

**Branch:** `PosterSop06-beautification-phase1`
**Date:** 2026-03-29
**Scope:** Family A — `template_dual_v2` structural capacity failure diagnosis

---

## 1. Why This Document Exists

The previous engineering cycle treated bottom text truncation as a budget tuning problem. The runtime evidence shows it is not. This document records the structural diagnosis that ends the budget-tuning loop and starts a contract-upgrade path.

---

## 2. Observed Runtime Failure

Reference poster samples confirm:

### `title_only` mode
- Title: "Upgrade your kitchen with ChefCraft" → renders fully ✓
- Subtitle: "April 24 we'll start using GitHub Copilot interactio..." → minor trailing clip

### `title_gallery_split` mode + 4 gallery items
- Title: "Upgrade your kitchen with ChefCraft" (35 chars) → rendered as **"Upgrade your kitchen with Ch"** (~28 chars) ✗
- Subtitle: "April 24 we'll start using GitHub Copilot interaction" (52 chars) → rendered as **"April 24 we'll start using G"** (~27 chars) ✗

Both texts are severely truncated. The truncation is not a rendering artifact — it is a direct consequence of the resolver's budget assignments.

---

## 3. Root Cause: Structural Ceiling, Not Budget Tuning

The bottom resolver in `_resolve_bottom_layout_policies()` assigns the following under `title_gallery_split` + dense subtitle + 4 visible gallery items:

```
title_band_sizing_mode = "standard"
title_line_clamp = 1        (when subtitle_length > 48)
title_char_budget = 20      (when title_line_clamp == 1)
subtitle_line_clamp = 1
subtitle_char_budget = 24
title_band_height = 144
bottom_shell_top = 728      (hardcoded)
```

These constraints exist because the title_band and gallery_strip must both fit between `y=728` and `y=1024` (296px total).

With `title_band_height=144` and `gallery_shell_height=68` (for quad), plus peer_gap=10, the math is:
```
144 + 10 + 68 = 222px used
296px available
74px margin
```

There is margin in the geometry — but the **text slot** inside the title band is only:
- `title_slot_height ≈ 54px` (1-line clamp)
- `subtitle_slot_height ≈ 28px`
- This is driven by `title_line_clamp=1` imposed by the dense-quad branch

The dense-quad branch was designed to protect gallery strip space. It works by compressing title to 1 line and assigning a very small char_budget. But the result is **title cuts to 20 chars** — a budget that cannot hold "Upgrade your kitchen with ChefCraft" (35 chars).

**The ceiling is structural, not tunable:**
- You cannot raise `title_char_budget` further without also raising `title_slot_height`
- You cannot raise `title_slot_height` without raising `title_band_height`
- You cannot raise `title_band_height` further without shrinking `gallery_shell_height` to unacceptable levels
- All of this is bounded by `bottom_shell_top = 728`, which is frozen into the baseline

The frozen baseline (`bottom_shell_top = 728`) is a contract surface. It cannot be changed without a new architecture decision.

**Conclusion:** The current bottom region cannot hold typical Family A text content alongside 4 gallery items. The geometry is exhausted. Budget tuning within this structure is not a solution.

---

## 4. What Budget Tuning Would NOT Solve

Raising `title_char_budget` to 40 or `subtitle_char_budget` to 40 without raising `title_band_height` does not prevent visual truncation — the renderer still clips at the slot boundary. The char budget is a pre-render gate; the slot height is the rendering ceiling. Both are constrained by the same structural limit.

Prior iterations raised budgets incrementally. Each raise produced marginal improvement but could not reach the full text because the slot heights were not raised to match.

---

## 5. Structural Requirements For Fix

To hold typical Family A text in split mode:

| Requirement | Target |
|---|---|
| title: 2-line, 40-char budget | `title_slot_height ≥ 72px`, `title_char_budget ≥ 40` |
| subtitle: 2-line, 48-char budget | `subtitle_slot_height ≥ 44px`, `subtitle_char_budget ≥ 48` |
| gallery strip: at least pair/triplet height | `gallery_shell_height ≥ 80px` |
| total capacity needed | `72+44+8(gap)+80+12(peer_gap) = 216px for text+gallery content only` |
| total bottom shell needed | `≥ 280px (content + padding)` |

The current frozen baseline provides `296px` (y=728 to y=1024). This is borderline — title+subtitle at current sizing fights quad gallery for the same space.

**For materially larger capacity**, the bottom shell must start higher:
- `text_only_expanded`: shell starts at `y=656` → `368px` capacity, no gallery
- `text_gallery_expanded`: shell starts at `y=640` → `384px` capacity, text + gallery

These are new structural modes, not adjustments to the frozen baseline.

---

## 6. Product Region Structural Gap

The product region is currently defined as a single slot:
- `product_slot: x=456, y=188, w=300, h=520`

This provides no contract-level hierarchy:
- No distinction between a primary display image and a secondary contextual image
- Annotation callouts are anchored to the product slot but have no slot hierarchy
- No `product_primary_slot` or `product_secondary_slot` in the contract

For Family A to support dual-product presentation (main product + supporting/variant product), the product region needs:
- An explicit `product_layout_mode` at the contract level
- `product_primary_slot` and `product_secondary_slot` as named contract surfaces
- The annotation shell must remain independent and attach only to the primary slot

---

## 7. Text Layer Evidence Gap

Text evidence currently lives inside `bottom_contract_review.behavior_policy`:
- `requested_title_text`, `sanitized_title_text`, `rendered_title_excerpt`
- `title_truncation_applied`, `subtitle_truncation_applied`

This is bottom-region-scoped evidence, not a first-class **text layer** in the rendering pipeline.

**Missing layer-level evidence:**
- `title_text_layer` — is the title slot rendered? What are its resolved bounds? What was truncated?
- `subtitle_text_layer` — same for subtitle
- `header_text_layer` — brand + agent text layer status (these exist in `layer_render_status` but not as named text layers with full evidence)

These are needed to validate text as a structural outcome rather than relying only on truncation flags post-hoc.

---

## 8. Conclusion

The Family A structural closeout requires three contract-level changes:

1. **New bottom layout modes** (`text_only_expanded`, `text_gallery_expanded`) that place the bottom shell higher on the canvas, providing materially larger text and gallery capacity than the frozen baseline permits.

2. **New product layout modes** (`single_primary`, `primary_secondary_dual`) that give the product region a named slot hierarchy and make dual-image product presentation a first-class contract feature.

3. **Text layer evidence** (`header_text_layer`, `title_text_layer`, `subtitle_text_layer`) that validates text as a rendered layer, not just a budget check.

These three changes end the micro-tuning loop and place Family A on a structurally sound path for beautification.
