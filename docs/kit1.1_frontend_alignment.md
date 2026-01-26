# KitPoster 1.1 Frontend Alignment (Mode S)

## Scope
- Frontend-only (static HTML/CSS/JS).
- No backend route or business-layer changes.
- Mode S affects asset utilization only (allow_auto_fill), not layout editing.

## Stage 1 Layout (Partitioned Upload)
1) Template selection
   - Template select + variant (A/B) visible.
   - Template preview canvas + description.

2) Image assets
   - Scenario image upload (optional) + preview.
   - Product image 1 (required) + preview.
   - Product image 2 (optional) + preview.
   - Scenario description + product description inputs stay visible.
   - Brand logo + brand name + agent/channel name remain visible.

3) Copy fields
   - Title required.
   - Bullets optional (0–4).
   - Tagline optional.

4) Bottom thumbnails
   - 4 slots always visible.
   - Upload/replace/clear per slot.
   - 0–4 allowed, no blocking validation.

5) Layout preview
   - Wireframe preview with safe areas (fitTextToBox).
   - Poster preview DOM (#preview-*) for operators.
   - Empty thumbnails render clean placeholders.
   - Fallback warning shown on image load fallbacks.

## Validation Rules
- Required: product image 1 + title.
- Optional: scenario, product image 2, bullets (0–4), tagline, bottom thumbnails (0–4).
- No minimum bullets requirement.

## Stage 2 Controls
- Categorized panels: Scene Background / Core Product / Bottom Series Thumbnails.
- Operator adjustments: show bullets, title size (S/M/L), fallback to stable.
- Advanced prompt editing is under a collapsed <details> block.
- Wireframe + material preview stays visible; empty slots show placeholders.

## Preview Safety
- fitTextToBox reduces font size until it fits; min size then ellipsis.
- Truncation warning shown below preview.

## Image Fallbacks
- onError fallback chain for critical images:
  1) default scenario asset (if applicable)
  2) local placeholder asset
  3) inline placeholder
- Fallback warning is non-blocking.

## Draft Storage
- Persist: template_id, template_variant, scenario/product assets, copy fields,
  bottom thumbnails array (0–4), allow_auto_fill.
