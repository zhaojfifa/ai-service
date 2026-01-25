# KitPoster1.1 Operator Review

## Goal
Stabilize operator workflow for KitPoster1.1 with predictable backend control flow and a clearer Stage1/Stage2 UX.

## Boundary
- No new generation routes or GPU worker changes.
- No backend composition refactor or drag-and-drop editing.
- Minimal, patch-like changes only.

## Stage1
- Keep a wireframe preview with safe areas for title/bullets/tagline.
- Real-time text fitting inside the boxes.

## Stage2
- Only lightweight controls: bullets toggle, title size presets, one-click fallback to stable.
- Advanced fields remain hidden/collapsible.

## Warnings/Degraded
- Response includes warnings and degraded flag for fallbacks.
- Scenario default fallback triggers a warning.
