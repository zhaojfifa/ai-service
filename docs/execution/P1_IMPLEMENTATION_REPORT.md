# P1 Implementation Report

## Summary

The pilot landed on the existing `poster2` architecture and `POST /api/v2/generate-poster`.

Additions:

- renderer abstraction with `pillow` and `puppeteer` modes
- Chromium-backed structured foreground renderer for `template_dual_v2`
- explicit render metadata in manifest and response
- structured template HTML/CSS/SVG/JSON assets
- focused tests

## Runtime Changes

Required Python dependency:

- `playwright==1.53.0`

Render build command update:

- `pip install -r requirements.txt && python -m playwright install chromium`

Optional runtime env:

- `POSTER2_DEFAULT_RENDERER_MODE`
- `PLAYWRIGHT_CHROMIUM_EXECUTABLE`

## Render Platform Notes

If Render Chromium startup fails due to missing system libraries, install or enable packages that satisfy headless Chromium dependencies. Typical missing classes are:

- `libnss3`
- `libatk-bridge2.0-0`
- `libxkbcommon0`
- `libdrm2`
- `libgbm1`
- `libasound2`

This repo change does not force those packages directly; it documents them because availability depends on the Render base image.

## Risk Notes

- The Playwright path currently launches a fresh browser per render.
- The default route behavior remains safe because Pillow is still the fallback.
- Structured renderer coverage is limited to `template_dual_v2` for this pilot.
