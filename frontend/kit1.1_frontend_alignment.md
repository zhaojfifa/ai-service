# Kit1.1 Frontend Alignment

## Scope
- Frontend-only adjustments (static pages + JS utilities).
- Keep existing backend routes and payloads.
- Mode S focuses on asset utilization, not layout editing.

## Stage 1 - Assets & Copy (Mode S)
- Header: "Stage 1 - Assets & Copy (Mode S)" with Mode S subtext.
- Sections in order:
  1) Top Banner Assets (logo optional, brand name, agent/channel name).
  2) Image Assets (scenario optional + selection; product image 1 required, product image 2 optional).
  3) Copy & Bottom Products (title required, bullets optional 0-4, tagline optional, bottom thumbnails optional 0-4).
  4) Material Preview (wireframe safe areas + asset thumbnails + bottom slots).
  5) Actions (Save Draft / Save and Continue).
- Bottom thumbnails: always show 4 slots; upload/replace/clear; empty is allowed.
- Asset visualization: any uploaded image shows immediate preview.

## Stage 2 - Categorized Controls
- Visible panels: Scene Background, Core Product, Bottom Series Thumbnails.
- Operator adjustments: show bullets, title size S/M/L, fallback to stable.
- Advanced prompt editing must be under a collapsed Advanced block.
- Preview: wireframe + bottom slots; empty slots remain clean (no blocking errors).
- Results area shows poster key + copy/open URL controls.

## Instrumentation (console-only)
On Generate click, log:
- bottom_count, has_scenario, has_product2, title_len, bullets_count
- adjustments: showBullets, titleSize, fallbackStableClicked
- t0, t1, duration_ms

## Storage
- Preserve draft storage under kitposter:draft.
- Bottom thumbnails stored as an array length 0-4.

## Notes
- No new dependencies.
- Do not introduce new backend endpoints.
