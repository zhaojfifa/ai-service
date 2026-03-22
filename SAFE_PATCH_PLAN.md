# Safe Patch Plan

## Goal

Improve KitPoster Stage2 edit quality with minimal, low-risk, testable changes.

## Applied now (low risk)

1. **Mask tightening**
   - File: [glibatree.py](/Users/tylerzhao/Code/ai-service/app/services/glibatree.py)
   - Change:
     - `editable_slots` reduced from `{"scenario", "gallery_strip"}` to `{"scenario"}`
   - Why:
     - prevents model from writing artifacts into bottom strip area
   - Risk:
     - low; only narrows model edit area

2. **Protected slot margin carve-out**
   - File: [glibatree.py](/Users/tylerzhao/Code/ai-service/app/services/glibatree.py)
   - Change:
     - Added protected-slot carving in `_build_edit_mask_from_slots`
     - Protected slots: `logo`, `brand_name`, `agent_name`, `product`, `title`, `subtitle`
     - Margin: `12px`
   - Why:
     - reduces edge pollution around typography/product protected regions
   - Risk:
     - low; only reduces editable pixels

3. **Negative prompt hardening for edit mode**
   - File: [glibatree.py](/Users/tylerzhao/Code/ai-service/app/services/glibatree.py)
   - Change:
     - Added `KITPOSTER_NEGATIVE_HARDENING`
     - In `_generate_poster_with_vertex`, when `force_edit=True`, merge hardening terms into negative prompt
   - Why:
     - suppresses fake text/signage/UI/watermark artifacts inside editable background
   - Risk:
     - low to medium; may slightly reduce creative variance but improves cleanliness

## Not applied (intentionally deferred)

1. Reworking template coordinates or layout semantics
2. Changing gallery fallback fill rules
3. Overhauling scenario preset system in frontend
4. Any deployment/env restructuring

## Verification focus

1. `POST /api/generate-poster` with `render_mode=kitposter1_a/b`
2. Confirm:
   - `degraded=false` remains
   - left scenario area has fewer fake letters/signage
   - title/subtitle visual region remains clean
   - bottom strip no longer receives model-generated noise
3. Optional debug:
   - set `DEBUG_KITPOSTER_MASK=1` and inspect `/tmp/kitposter_debug/<trace>/edit_mask.png`

## If quality is still unacceptable

Next safe step (not yet applied):

- switch mask generation to consume a dedicated scenario mask asset (`mask_scene`) if its alpha semantics are validated in production samples.

This is deferred because asset alpha semantics are template-dependent and can be risky without sample-by-sample validation.
