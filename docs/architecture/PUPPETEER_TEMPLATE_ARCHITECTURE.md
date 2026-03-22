# Puppeteer Template Architecture

## Scope

This pilot adds a deterministic structured foreground renderer to the existing `poster2` path used by `POST /api/v2/generate-poster`.

The renderer mode is named `puppeteer` at the product layer. The Python implementation uses Playwright-driven Chromium to render fixed HTML/CSS/SVG template assets.

## Guardrails

- AI is restricted to background and material generation only.
- Title, subtitle, agent label, brand label, feature callouts, and gallery placement are never delegated to a generative model.
- Anchors are template-bounded and loaded from versioned JSON assets.
- Layout is deterministic for a given template asset set and input payload.

## Asset Set

Pilot template: `template_dual_v2`

- `app/templates_html/template_dual_v2.html`
- `app/templates_html/template_dual_v2.css`
- `app/templates_html/template_dual_v2.svg`
- `app/templates_html/slot_spec.template_dual_v2.json`
- `app/templates_html/anchor_map.template_dual_v2.json`

## Render Flow

1. `slot_spec.*.json` defines fixed structural slots, safe margin, and protected zones.
2. `anchor_map.*.json` defines bounded callout anchor coordinates and label boxes.
3. The renderer converts resolved PIL assets into data URLs.
4. HTML is assembled with fixed-position slots and the SVG overlay.
5. Chromium screenshots `#poster-root` with transparent background.
6. The composed foreground is alpha-composited over the generated background.

## Fallback

If Chromium or Playwright is unavailable, the pipeline degrades to the existing Pillow renderer and returns:

- `degraded=true`
- `degraded_reason=puppeteer_fallback:<ExceptionType>`

The route remains available and backward compatible.
