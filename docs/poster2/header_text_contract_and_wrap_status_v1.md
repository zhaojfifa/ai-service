# header text contract and wrap status v1

## 1. Task Objective

Close header as the first region in the unified text-governance line.

Bring header agent and brand text fields to the same contract standard already established for bottom (requested_text / sanitized_text / rendered_excerpt / truncation_applied / line_clamp / char_budget / slot_bounds / owner_region).

Add controlled wrapping so the renderer and CSS consume the contract's declared clamp value rather than having wrap behavior hardcoded in CSS.

## 2. Scope

- PR-7A only
- header text contract / propagation / wrapping

## 3. Frozen Unchanged

- bottom geometry and bottom mode behavior
- product region geometry
- product annotation/text path
- feature delegation
- beautification
- email/save workflow
- header mode names and slot geometry (no geometry rebalance in this PR)
- identity_left_agent_right: agent pill stays single-line by design (agent_line_clamp = 1)

## 4. Problem Reproduced

Before PR-7A:

- `ResolvedHeaderBehavior` had `brand_line_clamp` but no `agent_line_clamp` field
- `header_text_layer.agent_text_slot.line_clamp` was hardcoded `1` in `pipeline.py` — not derived from the resolver
- `header_contract_review.behavior_policy` exposed `brand_line_clamp` but not `agent_line_clamp`
- CSS `.header-mode-brand_block_two_line .text-brand` hardcoded `-webkit-line-clamp: 2` — the value was not driven by a CSS var from the resolver
- No `--header-brand-line-clamp` or `--header-agent-line-clamp` CSS vars were emitted from the resolver
- Brand wrap behavior was triggered by a mode class (`header-mode-brand_block_two_line`) rather than a behavior class (`header-brand-wrap`) derived from the contract field value

## 5. Root Cause

Split governance: the contract declared `brand_line_clamp` for Pillow but CSS had its own hardcoded clamp value independent of the resolver. The agent side had no `line_clamp` field at all — the `1` in evidence was a source-level constant, not a resolver output.

## 6. Files Changed

- `app/services/poster2/template_behavior.py`
- `app/services/poster2/pipeline.py`
- `app/templates_html/template_dual_v2.css`
- `tests/poster2/test_pipeline.py`
- `docs/poster2/header_text_contract_and_wrap_status_v1.md` (this file)
- `docs/poster2/current_branch_execution_log_v1.md`

## 7. Contract Fields Now Exposed / Aligned

### `ResolvedHeaderBehavior` (template_behavior.py)

| Field | Before | After |
|-------|--------|-------|
| `brand_line_clamp` | present | unchanged |
| `agent_line_clamp` | **missing** | **added** |
| `brand_char_budget` | present | unchanged |
| `agent_char_budget` | present | unchanged |

`agent_line_clamp` per mode:

| mode | agent_line_clamp |
|------|-----------------|
| `identity_left_agent_right` | 1 |
| `brand_block_two_line` | 1 |
| `brand_only` | 1 |

### `as_dict()` (template_behavior.py)

`agent_line_clamp` added to `ResolvedHeaderBehavior.as_dict()`.

### `_build_header_contract_review` (pipeline.py)

`behavior_policy` now includes `agent_line_clamp`.

Before:
```python
"brand_line_clamp": ...,
"brand_char_budget": ...,
"agent_char_budget": ...,
```

After:
```python
"brand_line_clamp": ...,
"brand_char_budget": ...,
"agent_line_clamp": resolved_behavior.header_policy.agent_line_clamp,
"agent_char_budget": ...,
```

### `_build_header_text_layer_evidence` (pipeline.py)

`agent_text_slot.line_clamp` now reads from the resolver field.

Before:
```python
"line_clamp": 1,   # hardcoded
```

After:
```python
"line_clamp": header.agent_line_clamp,   # resolver-derived
```

Both `brand_text_slot` and `agent_text_slot` now have `line_clamp` driven from resolver fields.

Full text contract fields per slot (both slots now complete):

| field | brand_text_slot | agent_text_slot |
|-------|----------------|----------------|
| `requested_text` | ✓ | ✓ |
| `sanitized_text` | ✓ | ✓ |
| `rendered_excerpt` | ✓ | ✓ |
| `truncation_applied` | ✓ | ✓ |
| `line_clamp` | ✓ resolver | ✓ resolver (was hardcoded) |
| `char_budget` | ✓ | ✓ |
| `slot_bounds` | ✓ | ✓ |
| `owner_region` | outer level | outer level (unchanged) |

## 8. Propagation Alignment Evidence

### Resolver → CSS vars

`_resolve_header_behavior_vars` now emits:

```
--header-brand-line-clamp: 1   (identity_left_agent_right)
--header-brand-line-clamp: 2   (brand_block_two_line)
--header-brand-line-clamp: 1   (brand_only)
--header-agent-line-clamp: 1   (all modes)
```

These are injected into the poster inline style, overriding the defaults in `.layer-header-banner`.

### Resolver → CSS class

`resolve_header_behavior` now adds `header-brand-wrap` to `css_classes` when `brand_line_clamp > 1`.

| mode | header-brand-wrap |
|------|-----------------|
| `identity_left_agent_right` | absent |
| `brand_block_two_line` | **present** |
| `brand_only` | absent |

### CSS consumption

Before:
```css
/* mode-specific, hardcoded clamp value */
.header-mode-brand_block_two_line .text-brand {
  white-space: normal;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;   /* hardcoded */
  line-clamp: 2;            /* hardcoded */
}
```

After:
```css
/* behavior-class-driven, CSS-var-driven clamp value */
.header-brand-wrap .text-brand {
  white-space: normal;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: var(--header-brand-line-clamp);   /* resolver-driven */
  line-clamp: var(--header-brand-line-clamp);            /* resolver-driven */
}
```

The resolver controls both when the wrap class appears and what clamp value the CSS uses.

### `.layer-header-banner` CSS defaults

Added:
```css
--header-brand-line-clamp: 1;
--header-agent-line-clamp: 1;
```

These are the fallback values. The resolver's inline style overrides them for the actual poster root.

## 9. Wrap / Truncation Before / After Evidence

### Brand text — `identity_left_agent_right`

| | Before | After |
|--|--------|-------|
| CSS rule | `white-space: nowrap; text-overflow: ellipsis` | unchanged |
| CSS var | not emitted | `--header-brand-line-clamp: 1` |
| CSS class trigger | none | none (`brand_line_clamp == 1`) |
| Pillow max_lines | `brand_line_clamp` (1) | unchanged |

No visual change for this mode. Contract field now explicit.

### Brand text — `brand_block_two_line`

| | Before | After |
|--|--------|-------|
| CSS rule trigger | `.header-mode-brand_block_two_line` (mode class) | `.header-brand-wrap` (behavior class) |
| CSS clamp value | hardcoded `2` | `var(--header-brand-line-clamp)` = `"2"` |
| CSS var | not emitted | `--header-brand-line-clamp: 2` |
| Pillow max_lines | `brand_line_clamp` (2) | unchanged |

Wrap behavior preserved. Governance moves from hardcoded CSS to resolver-driven class + CSS var.

### Agent text — all modes

| | Before | After |
|--|--------|-------|
| `agent_line_clamp` field | missing | `1` (explicit resolver field) |
| evidence `line_clamp` value | `1` (hardcoded in pipeline.py) | `header.agent_line_clamp` (resolver) |
| CSS var | not emitted | `--header-agent-line-clamp: 1` |
| CSS behavior | `white-space: nowrap; text-overflow: ellipsis` | unchanged (clamp = 1, no wrap class) |

Truncation behavior unchanged. Governance is now explicit.

## 10. Test Commands and Results

```bash
python3 -m pytest -q tests/poster2/test_pipeline.py
# 214 passed (199 prior + 15 new TestHeaderTextContractPR7A)

python3 -m pytest -q tests/poster2/test_renderer.py tests/test_stage2_guard_diagnostics_surface.py
# 109 passed
# Note: test_renderer.py test_header_two_line_mode_emits_two_line_brand_class_and_vars_in_html
# updated — stale assertion for CSS selector string "header-mode-brand_block_two_line"
# (underscores) replaced by correct class "header-mode-brand-block-two-line" (hyphens)
# + new assertions: "header-brand-wrap", "--header-brand-line-clamp: 2"
```

## 11. Next PR Only

- PR-7B — bottom subtitle text contract / propagation / wrapping closure
