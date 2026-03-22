# P1.8 UI Pilot Plan

## Scope

Enable internal-only browser validation of poster2 structured rendering on the existing product UI.

Constraints:

- poster2 remains the main path for this pilot flow
- `template_dual_v2` is the only Puppeteer pilot template
- Pillow remains default and fallback
- Puppeteer remains opt-in only
- no new templates
- no broad frontend redesign

## UI Goals

1. Allow the existing Stage 2 UI to call `POST /api/v2/generate-poster` for the pilot flow.
2. Let internal users choose:
   - `auto/default`
   - `pillow`
   - `puppeteer`
3. Surface renderer diagnostics and debug artifact links after each generation.
4. Support sequential A/B comparison by keeping a small recent-run history in the UI.

## Pilot Flow

1. Stage 1 uses the existing `template_dual` selection.
2. Stage 2 maps that pilot-eligible template to `template_dual_v2` on the poster2 API path.
3. Renderer mode stays safe by default with `auto`.
4. Internal users can rerun with `pillow` and `puppeteer` and compare final outputs plus diagnostics.

## Non-Pilot Templates

Templates other than `template_dual` stay on the existing safe/default path. The UI labels Puppeteer as pilot-only and disables the selector effect for non-pilot templates.
