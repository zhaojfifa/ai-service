# Header Wrap Render Parity Status v1

## Scope

- PR-7A3 only
- header wrap render parity closure
- no bottom work
- no product/header redesign beyond the active header agent wrap path

## State Read First

Read in order:

1. `AGENTS.md`
2. `CLAUDE.md`
3. `docs/poster2/README.md`
4. `docs/poster2/current_branch_execution_log_v1.md`
5. `docs/poster2/header_text_contract_and_wrap_status_v1.md`
6. `docs/poster2/header_agent_truncation_closure_status_v1.md` — missing in this workspace, recorded and not treated as a blocker

## Frozen Unchanged

- brand priority policy
- header mode names
- bottom
- product region
- scenario/header broad layout redesign
- beautification

## DOM / CSS Root Cause

The real final rendered node is:

- `.layer-header-banner`
- `.layer-header-agent-zone`
- `.layer-agent-name-text`
- `.slot-agent-name-text`
- `.text-agent-secondary`

The visible single-line ellipsis persisted because three live-path issues stacked together:

1. `#poster-root` received the resolved header CSS vars, but `.layer-header-banner` defined its own local defaults (`--header-side-width: 228px`, `--header-agent-line-clamp: 1`), which masked the resolver values inside the actual rendered banner.
2. The real rendered text node is `.text-agent-secondary`, and its default rule remained `white-space: nowrap; overflow: hidden; text-overflow: ellipsis;` unless a wrap class reached the active banner path.
3. The layout normalization rule later in the CSS forced `.slot-agent-name-text` to `width: 100% !important; height: 100% !important;`, so the final browser path kept consuming the masked one-line banner lane until the live banner vars were injected at the banner itself.

## What Changed

- `identity_left_agent_right` now resolves `agent_line_clamp = 2`
- `header-agent-wrap` is emitted when `agent_line_clamp > 1`
- final HTML injects resolved header behavior vars directly onto `.layer-header-banner`
- active agent slot bounds are aligned to the wrapped contract lane already established on main:
  - `x: 684`
  - `y: 96`
  - `w: 228`
  - `h: 36`
- `agent_name_slot` / slot-spec layer contract / pipeline evidence / renderer consumption all use the same wrapped bounds
- the real rendered `.text-agent-secondary` node now computes to wrapped multi-line behavior in the browser:
  - `white-space: normal`
  - `text-overflow: clip`
  - `-webkit-line-clamp: 2`

## Files Changed

- `app/services/poster2/template_behavior.py`
- `app/services/poster2/renderer.py`
- `app/services/poster2/template_registry.py`
- `app/templates/specs/template_dual_v2.json`
- `app/templates_html/slot_spec.template_dual_v2.json`
- `app/templates_html/template_dual_v2.html`
- `app/templates_html/template_dual_v2.css`
- `tests/poster2/test_pipeline.py`
- `tests/poster2/test_renderer.py`
- `tests/poster2/test_contracts.py`
- `docs/poster2/header_wrap_render_parity_status_v1.md`
- `docs/poster2/current_branch_execution_log_v1.md`

## Exact Test Commands And Results

```bash
.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'HeaderTextContractPR7A or header_contract_review or header_text_layer or renderer_metadata_includes_layer_render_status'
# 19 passed, 195 deselected

.venv/bin/python -m pytest -q tests/poster2/test_renderer.py -k 'HeaderAndTitleBandLayoutControl or header_two_line_mode_emits_two_line_brand_class_and_vars_in_html'
# 5 passed, 98 deselected

.venv/bin/python -m pytest -q tests/poster2/test_contracts.py -k 'TemplateSpecLoading or structured_template_assets_exist'
# 12 passed, 5 deselected

.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py tests/poster2/test_renderer.py tests/poster2/test_contracts.py -k 'header and not bottom and not product and not scenario and not feature'
# 26 passed, 308 deselected
```

## Before / After Final Hash Evidence

Probe case:

- `brand_name = "ChefCraft"`
- `agent_name = "Smart Kitchen Upgrade Team Service Center"`
- `title = "Test"`
- `subtitle = "Sub"`

Pre-fix live Puppeteer render from detached worktree at `HEAD` before PR-7A3 patch:

- `agent_line_clamp = 1`
- `header-agent-wrap = false`
- `final sha256 = ae48f545cb650c5cc2bad1f5f81c527516bf10eccfd90128949ffc3c5dcaaa62`

Post-fix live Puppeteer render from current workspace:

- `agent_line_clamp = 2`
- `header-agent-wrap = true`
- `final sha256 = 2b14ddda8a29dbfe3006170f05daa8346803d2d80a4af058a3370dcca08e6ec7`

Result:

- final hash changed
- no merge-gate or unrelated runtime work was introduced

## Final Acceptance Evidence

Live browser inspection on the patched DOM path:

- `.layer-header-banner` computed `--header-side-width = 228px`
- `.layer-header-banner` computed `--header-agent-line-clamp = 2`
- `.slot-agent-name-text` inline style is `left:0px;top:0px;width:228px;height:36px;`
- computed slot box is `228px x 36px`
- `.text-agent-secondary` computed:
  - `white-space = normal`
  - `text-overflow = clip`
  - `-webkit-line-clamp = 2`

Pipeline evidence on the same header path:

- `header_contract_review.behavior_policy.agent_line_clamp = 2`
- `header_contract_review.agent_truncation_applied = false`
- `header_text_layer.agent_text_slot.truncation_applied = false`
- `header_text_layer.agent_text_slot.slot_bounds = {x: 684, y: 96, w: 228, h: 36}`

Acceptance summary:

- final image path no longer stays on the masked single-line header lane
- the real rendered node receives wrapped-mode behavior
- current primary case no longer reports agent truncation
- resolver, geometry evidence, text-layer metadata, and final render path now tell the same story
