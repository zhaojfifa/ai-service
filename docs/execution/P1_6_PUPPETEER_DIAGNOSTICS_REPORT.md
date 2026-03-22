# P1.6 Puppeteer Diagnostics Report

## What Changed

Poster2 Puppeteer fallback reasons are now classified into stable, diagnosable codes instead of surfacing only as `puppeteer_fallback:Error`.

## Operational Effect

Staging can now distinguish:

- missing Chromium
- missing system libraries
- browser launch failure
- template/render preparation failure
- navigation failure
- screenshot failure
- timeout
- generic unknown failure

## Metadata Surfaces

The classification is now visible in:

- poster2 HTTP response fields
- render manifest fields
- renderer metadata debug artifact
- structured logs from the Puppeteer path

## Remaining Dependency Notes

Better classification still depends on the runtime surfacing meaningful Chromium/Playwright error messages. To distinguish `missing_chromium` from `missing_system_libs`, the environment still needs:

- Playwright installed
- Chromium installed
- enough stderr/error text from Chromium startup

If the runtime suppresses those details, the code will still fall back safely but may classify the failure as `puppeteer_browser_launch_failed` or `puppeteer_unknown_error` instead of a more specific bucket.
