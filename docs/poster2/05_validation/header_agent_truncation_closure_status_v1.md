# header agent truncation closure status v1

## 1. Task Objective

Close the user-visible truncation of the header agent text in `identity_left_agent_right` mode.

Example: "STARLIGHT CHANNEL SERVICE CENTER" (33 chars) was visibly cut off under the old
single-line `agent_char_budget = 28` policy. After this PR it renders in full without truncation.

## 2. Scope

- PR-7A2 only
- header agent truncation closure for `identity_left_agent_right`

## 3. Frozen Unchanged

- bottom geometry and bottom mode behavior
- product region geometry and annotation path
- feature delegation
- beautification
- email/save workflow
- brand text priority (brand slot contract unchanged)
- `brand_block_two_line` and `brand_only` agent behavior (both keep `agent_line_clamp = 1`)
- header mode names and slot geometry for modes other than `identity_left_agent_right`

## 4. Problem Reproduced

Before PR-7A2:

- `identity_left_agent_right` had `agent_line_clamp = 1` and `agent_char_budget = 28`
- "STARLIGHT CHANNEL SERVICE CENTER" (33 chars) was budget-truncated at 28 chars
- CSS `white-space: nowrap; text-overflow: ellipsis` additionally clipped overflow visually
- `agent_truncation_applied = True` for this example
- No wrap path existed for the agent text slot

## 5. Root Cause

Single-line lockup on agent text: `agent_char_budget = 28` set below the minimum needed
for common longer agent names, with `agent_line_clamp = 1` providing no wrap fallback.
The 228px agent side zone at 15px font can hold ≈ 26–28 chars per line; allowing 2 lines
with a matched budget eliminates truncation for typical agent names.

## 6. Approach

Solved by controlled text policy only (preferred path). No broad header geometry redesign.

1. `agent_line_clamp = 2` for `identity_left_agent_right` — allows two-line wrap
2. `agent_char_budget = 52` for `identity_left_agent_right` — two-line capacity (2 × 26)
3. `agent_slot_h = 36` for `identity_left_agent_right` — slot height for 2 lines (2 × 18px)
4. `header-agent-wrap` CSS class emitted by resolver when `agent_line_clamp > 1`
5. CSS `.header-agent-wrap .text-agent-secondary` — switches from `nowrap+ellipsis` to `webkit-box` clamp
6. Pillow renderer `_agent_text_slot`: `max_lines` now uses `header_policy.agent_line_clamp` (was hardcoded `1`)

## 7. Files Changed

- `app/services/poster2/template_behavior.py`
- `app/services/poster2/renderer.py`
- `app/templates_html/template_dual_v2.css`
- `tests/poster2/test_pipeline.py`
- `docs/poster2/header_agent_truncation_closure_status_v1.md` (this file)
- `docs/poster2/current_branch_execution_log_v1.md`

## 8. Contract Field Changes — `identity_left_agent_right`

| field | before | after |
|-------|--------|-------|
| `agent_line_clamp` | 1 | **2** |
| `agent_char_budget` | 28 | **52** |
| `agent_slot_h` (layout_metrics) | 18 | **36** |
| `header-agent-wrap` in css_classes | absent | **present** |
| `--header-agent-line-clamp` CSS var | `"1"` | `"2"` |
| Pillow `max_lines` | hardcoded `1` | `header_policy.agent_line_clamp` |

`brand_block_two_line` and `brand_only`: all agent fields unchanged.

## 9. CSS Change

Before:
```css
.text-agent-secondary {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
/* no wrap path */
```

After:
```css
.text-agent-secondary {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-agent-wrap .text-agent-secondary {
  white-space: normal;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: var(--header-agent-line-clamp);
  line-clamp: var(--header-agent-line-clamp);
}
```

`header-agent-wrap` is present on the `layer-header-banner` element only when
`agent_line_clamp > 1` (i.e., `identity_left_agent_right` only). The descendent selector
`.header-agent-wrap .text-agent-secondary` activates the wrap behavior.

## 10. Before / After Truncation Evidence

### "STARLIGHT CHANNEL SERVICE CENTER" (33 chars)

| | before | after |
|--|--------|-------|
| `agent_char_budget` | 28 | 52 |
| `agent_line_clamp` | 1 | 2 |
| `rendered_excerpt` | `"STARLIGHT CHANNEL SERVICE CE"` (truncated at 28) | `"STARLIGHT CHANNEL SERVICE CENTER"` (full) |
| `truncation_applied` | `True` | **`False`** |
| CSS | `white-space: nowrap; text-overflow: ellipsis` | wraps to 2 lines via `header-agent-wrap` |
| Pillow max_lines | 1 (hardcoded) | 2 (resolver-driven) |

### Stale assertions updated in test_pipeline.py

| assertion | before | after |
|-----------|--------|-------|
| `policy.agent_line_clamp` (identity_left_agent_right) | `== 1` | `== 2` |
| `d["agent_line_clamp"]` (identity_left_agent_right) | `== 1` | `== 2` |
| `css["--header-agent-line-clamp"]` (identity_left_agent_right) | `== "1"` | `== "2"` |
| `review["behavior_policy"]["agent_line_clamp"]` (default mode) | `== 1` | `== 2` |
| `agent_slot["line_clamp"]` (default mode) | `== 1` | `== 2` |
| `geometry["slot_bounds"]["agent_name_slot"]["h"]` | `18` | `36` |
| `test_header_agent_budget_truncates_longer_name_at_new_floor` input | `"A" * 40` | `"A" * 60` |

## 11. Test Commands and Results

```bash
python3 -m pytest -q tests/poster2/test_pipeline.py
# 226 passed (214 prior + 12 new TestHeaderAgentTruncationClosurePR7A2)

python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py
# 109 passed
```

## 12. Acceptance Evidence

- `agent_truncation_applied = False` for "STARLIGHT CHANNEL SERVICE CENTER" ✓
- `rendered_excerpt == "STARLIGHT CHANNEL SERVICE CENTER"` (full text) ✓
- `agent_line_clamp = 2` propagates: resolver → behavior_policy → agent_text_slot → CSS var ✓
- `header-agent-wrap` CSS class emitted for `identity_left_agent_right` ✓
- `--header-agent-line-clamp: 2` CSS var emitted ✓
- `agent_slot_h = 36` in geometry evidence ✓
- Pillow `max_lines` now resolver-driven (not hardcoded) ✓
- `brand_block_two_line` agent_line_clamp = 1, agent_char_budget = 28 — no regression ✓
- `brand_only` agent_line_clamp = 1 — no regression ✓
- No changes to bottom, product region, or feature delegation ✓

## 13. Next PR Only

- PR-7B — bottom subtitle text contract / propagation / wrapping closure
