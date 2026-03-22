# P1.6 Puppeteer Fallback Reason Codes

## Scope

These reason codes apply only to the poster2 `puppeteer` foreground renderer fallback path on `POST /api/v2/generate-poster`.

## Codes

- `puppeteer_browser_launch_failed`
  Chromium/Playwright failed during browser launch.

- `puppeteer_missing_chromium`
  Playwright is installed but the Chromium executable is missing.

- `puppeteer_missing_system_libs`
  Chromium could not start because required system libraries are absent.

- `puppeteer_template_render_failed`
  Template asset loading or HTML assembly failed before navigation.

- `puppeteer_navigation_failed`
  Browser page navigation or `set_content()` failed.

- `puppeteer_screenshot_failed`
  Screenshot capture of `#poster-root` failed.

- `puppeteer_timeout`
  A Puppeteer-rendering operation timed out.

- `puppeteer_asset_load_failed`
  Asset-to-data-url preparation failed before browser render.

- `puppeteer_unknown_error`
  The failure did not match a more specific classified path.

## Response Fields

When fallback occurs, poster2 responses expose:

- `degraded=true`
- `degraded_reason=<reason_code>`
- `fallback_reason_code=<reason_code>`
- `fallback_reason_detail=<safe truncated detail>`
- `render_engine_used=pillow`

## Diagnostics Artifact

The renderer metadata artifact also records:

- requested renderer
- effective renderer
- fallback triggered
- fallback reason code
- fallback reason detail
- fallback exception class
- fallback stage
- timings
