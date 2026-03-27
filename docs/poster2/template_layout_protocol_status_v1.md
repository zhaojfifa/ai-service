# template layout protocol status v1

## 1. Task Objective

Use bottom as the proven SOP and lift its mixed-content behavior lessons into the first minimal template-level layout protocol on `PosterSop01`.

This status is scoped to:

- preserving the validated five-region structure
- preserving `bottom_region -> title_band_region / gallery_strip_region`
- preserving bottom closeout behavior
- introducing the first template-level policy layer without broad refactor or beautification expansion

## 2. Startup Context Used

- Root anchor: `AGENTS.md`
- Poster2 anchor: `docs/poster2/README.md`
- Task doc: `docs/poster2/template_behavior_layer_plan_v1.md`

No additional document was expanded in this run.

## 3. Problem Exposed By Bottom SOP

Bottom behavior closeout proved that local mixed-content behavior can be made declarative.

What it also exposed is that the system still lacked template-level answers for:

- when bottom remains a local behavior
- when bottom density should escalate into template-level response
- how feature and bottom should rebalance when both are dense
- how region priority should become reviewable rather than implicit

## 4. Minimal Template-Level Protocol Added

The first template-level layout protocol now includes:

- `content_priority_policy`
- `region_priority_policy`
- `peer_rebalance_policy`
- `layout_density_mode`
- `decision_scope`
- `drivers`

These are resolved at template level after bottom and feature local behavior are known.

## 5. First Runtime Consumption

This run does not redesign the template.

It applies the minimal first runtime effect only when:

- feature is dense
- and bottom is also dense

In that case:

- the system enters `multi_region_dense`
- `peer_rebalance_policy` becomes `feature_compacts_before_template_reflow`
- feature stack becomes slightly more compact through resolved feature policy

This is the first proof that bottom is no longer an isolated behavior island.

## 6. Metadata / Evidence Surface

Template-level behavior is now visible in:

- `template_behavior.template_layout_policy`
- `template_layout_review`

This lets operator review answer:

- whether the decision stayed local or escalated to template level
- which region took priority
- which density mode the template entered
- how feature-region response changed

## 7. Validation

Executed:

```bash
./.venv/bin/python -m pytest tests/poster2/test_api.py tests/poster2/test_contracts.py tests/poster2/test_renderer.py tests/poster2/test_pipeline.py tests/test_stage2_guard_diagnostics_surface.py tests/test_frontend_docs_sync.py
```

Observed result:

- `140 passed, 2 warnings`

## 8. Remaining Risks

- template-level protocol is still minimal and currently only drives feature response
- hero and header are not yet consuming template-level layout policy
- the policy is rule-based, not measurement-optimized

## 9. Next Recommended Step

Use the same template-level protocol to decide whether future dense hero / feature / bottom interactions remain local or should trigger shared template-level response.

## 10. Strategy Sentence

Strategy: do not keep repairing bottom in isolation; treat bottom as the validated SOP, then lift its mixed-content logic into a reusable template-level layout protocol before any beautification expansion.
