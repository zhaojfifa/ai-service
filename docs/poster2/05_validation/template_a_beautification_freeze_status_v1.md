# Template A Beautification Freeze Status v1

## Scope

Template A only: `template_dual_v2`

This freeze completes a bounded Family A visual pack on top of the repaired and abstracted runtime.
It does not change geometry, ownership, or behavior.

## Allowed Layer Only

The freeze is limited to:

- `shell_surface`
- `shell_border`
- `shell_shadow`
- `accent_tone`
- `text_emphasis`

No region geometry, slot ownership, header/product/bottom behavior, or annotation logic was changed.

## Frozen Family A Beauty Pack

Template A now resolves to:

- `shell_surface = campaign_frozen_panel`
- `shell_border = clean_frame`
- `shell_shadow = medium`
- `accent_tone = warm_red`
- `text_emphasis = campaign_frozen`

## Visual Targets Closed

The freeze pack tightens Family A without reopening behavior:

- header shell reads as a finished campaign frame
- logo plaque and agent chip are visually unified with the header shell
- product shell and product canvas have a cleaner frozen highlight/inset treatment
- product-owned annotation cards, markers, and leader lines share a stable Family A visual language
- title band and gallery strip read as one frozen bottom family

## Renderer Consumption

The Family A beauty pack is consumed in both execution paths:

- Puppeteer HTML/CSS shell/text variables
- Pillow shell fill/shadow/border rendering

The deterministic Family A visual smoke fixture was rebaselined on top of this freeze.

## Acceptance

Family A beautification freeze is accepted when:

1. the same input preserves the same A-family contract/control truth
2. `deliverable` and `structure_complete` do not regress
3. Family A visual smoke hashes match the frozen fixture
4. diagnostics remain backend-truth-driven
5. Template B remains untouched

## Follow-up Maintenance Note

A narrow post-freeze follow-up repaired Stage2 preview consumption for Template A
`bottom_mode = text_only_expanded` when support copy is present.

This did not change Template A geometry, ownership, or bottom behavior truth.
It only aligned the preview bottom text stack with the already-correct backend/final render state.

Another narrow follow-up aligned Template A `title_gallery_split` support-copy mapping:

- UI label remains `Bottom Support Copy`
- canonical backend field remains `subtitle`
- Template A bottom support copy now preserves `requested_subtitle_text` and `sanitized_subtitle_text`

This also did not change geometry, ownership, or bottom behavior truth.

## Follow-up Acceptance Note

After the two narrow Template A bottom follow-ups, a fresh local acceptance run was attempted
against the canonical Family A sample `annotation_triplet_gallery_triplet_subtitle_present`.

The resulting runtime truth stayed aligned with the frozen Family A baseline:

- `hero_mode = scenario_cover_product_contain`
- `feature_mode = product_anchor_callouts`
- `product_annotation_mode = product_anchor_callouts`
- `header_mode = identity_left_agent_right`
- `bottom_mode = title_gallery_split`
- `gallery_mode = strip_local_visible_only`
- `secondary_product_mode = inset_hidden_no_reserve`
- `structure_complete = true`
- `deliverable = true`

However, local Chromium launch was unavailable in this workspace, so the attempted Puppeteer run
fell back with:

- `render_engine_used = pillow`
- `degraded = true`
- `degraded_reason = puppeteer_missing_chromium`

So the freeze remains contract/control-accepted, but a fresh live Chromium artifact must still be
re-run in a Chromium-ready environment to fully refresh the live acceptance bundle.

That Chromium-ready acceptance has now been refreshed on a non-degraded Puppeteer path, so the
Family A freeze is accepted as both code-complete and acceptance-complete.

For the refreshed canonical acceptance sample, fixture / summary / attached metadata are aligned on:

- canonical sample: `annotation_triplet_gallery_triplet_subtitle_present`
- `product_layout_mode = single_primary`
- `secondary_product_mode = inset_hidden_no_reserve`
- subtitle present and rendered, not collapsed
