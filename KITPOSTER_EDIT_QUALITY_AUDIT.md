# KitPoster Edit Quality Audit

## Scope

Narrow review for KitPoster Stage2 edit rendering quality only:

1. mask coverage and editable boundaries
2. post-edit recomposition order
3. negative prompt hardening for fake text/UI artifacts
4. title/subtitle protection
5. scenario fallback behavior impact

Reviewed files:

- [glibatree.py](/Users/tylerzhao/Code/ai-service/app/services/glibatree.py)
- [template_dual_spec.json](/Users/tylerzhao/Code/ai-service/frontend/templates/template_dual_spec.json)
- [presets.json](/Users/tylerzhao/Code/ai-service/frontend/prompts/presets.json)
- [poster.py](/Users/tylerzhao/Code/ai-service/app/services/poster.py)

## Executive Findings

1. The current edit mask was too permissive: both `scenario` and `gallery_strip` were editable in `_build_edit_mask_for_template`.
2. Recomposition order is structurally correct: edited image is always passed through `_apply_locked_frame(...)`, which overlays locked regions back on top.
3. Negative prompts were not hardened enough in the kitposter edit path; fake text/signage/UI artifacts can still appear inside editable background zones.
4. Title/subtitle slots are not in editable slots directly, but protection was only indirect via keep-mask inversion; no explicit margin guard around typography slots.
5. `scenario_fallback_used` warning is currently not a proven quality signal for failed scenario rendering in this path; it is added from draft handling.

## Answers To Specific Questions

### Which exact regions are currently editable that should never be editable?

Before this patch:

- `scenario` slot
- `gallery_strip` slot

Source:

- `_build_edit_mask_for_template` used `editable_slots = {"scenario", "gallery_strip"}` in [glibatree.py](/Users/tylerzhao/Code/ai-service/app/services/glibatree.py)

`gallery_strip` should not be model-editable for stable typography/clean footer presentation.

### Is the mask too permissive around center title and lower subtitle?

It was indirectly protected (because those slots were not editable), but protection had no explicit safety margin around typography boundaries.

Risk:

- visual contamination near slot borders can still happen from nearby editable areas.

### After Vertex edit returns, are locked elements fully re-applied on top, or only partially?

The code reapplies locked content via `_apply_locked_frame(...)` using keep-mask alpha (`_build_keep_mask_alpha`), then alpha-composites locked overlay on edited output.

So this is a full re-overlay of keep regions, not a partial random reapply. The issue is primarily editable-region choice and artifact suppression inside editable zones.

### Which prompt strings should be strengthened?

For kitposter edit path, negative prompts should explicitly include:

- `no text`
- `no letters`
- `no typography`
- `no signage`
- `no labels`
- `no numbers`
- `no UI`
- `no screen content`
- `no captions`
- `no packaging text`
- `no watermark`

This is now added as a forced hardening suffix for `force_edit` calls.

### Is the current scenario preset too open-ended?

Yes, moderately. `scenario-closeup` negative prompt in [presets.json](/Users/tylerzhao/Code/ai-service/frontend/prompts/presets.json) includes `text` and `watermark`, but it does not aggressively block typography-like artifacts, labels, numbers, UI/screen content, and packaging text.

That is a quality risk under inpainting even when layout lock is technically correct.

## Minimal Low-Risk Patch Applied

Implemented in [glibatree.py](/Users/tylerzhao/Code/ai-service/app/services/glibatree.py):

1. Tightened editable area to scenario only
   - removed `gallery_strip` from editable slots
2. Added protected-slot carving with margin
   - carved keep zones for `logo`, `brand_name`, `agent_name`, `product`, `title`, `subtitle`
   - margin: `12px`
3. Added kitposter edit negative hardening
   - merged hardening phrase into negative prompt when `force_edit=True`
   - deduplicates merged tokens

No deployment/env changes were made.
No template business logic was refactored.
