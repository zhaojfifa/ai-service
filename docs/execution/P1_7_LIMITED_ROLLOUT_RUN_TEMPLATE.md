# P1.7 Limited-Rollout Run Template

Use this table to record 5 to 10 staging validation runs for `template_dual_v2`.

## Run Matrix

| Run | Scenario | renderer_mode | render_engine_used | degraded | fallback_reason_code | Title/Subtitle OK | Callouts OK | Gallery OK | Artifacts OK | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Baseline repeat | puppeteer |  |  |  |  |  |  |  |  |
| 2 | Baseline repeat | puppeteer |  |  |  |  |  |  |  |  |
| 3 | Baseline repeat | puppeteer |  |  |  |  |  |  |  |  |
| 4 | Long title | puppeteer |  |  |  |  |  |  |  |  |
| 5 | Long subtitle/features | puppeteer |  |  |  |  |  |  |  |  |
| 6 | Tall product asset | puppeteer |  |  |  |  |  |  |  |  |
| 7 | Wide product asset | puppeteer |  |  |  |  |  |  |  |  |
| 8 | Optional assets missing | puppeteer |  |  |  |  |  |  |  |  |
| 9 | Full asset variation | puppeteer |  |  |  |  |  |  |  |  |
| 10 | Forced fallback safety | puppeteer |  |  |  |  |  |  |  |  |

## Required Per-Run Attachments

- final poster URL
- renderer metadata URL
- background layer URL
- product/material layer URL
- foreground layer URL
- final composited URL

## Recording Guidance

- `render_engine_used` should stay `puppeteer` for runs 1 through 9 unless a real fallback occurs.
- run 10 should intentionally validate fallback safety.
- mark a run as failed if any protected-zone overlap or missing structured text is observed.
