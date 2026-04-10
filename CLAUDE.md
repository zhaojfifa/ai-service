# CLAUDE.md

## Shared State

This file is shared state only.
Repository rules live in `AGENTS.md`.
poster2 document entry and grouping live in `docs/poster2/README.md`.

## Current poster2 baseline

- Product baseline: `docs/poster2/poster_generation_product_design_baseline_v1.md`
- Family A architecture anchor: `docs/poster2/02_architecture/template_dual_v2_architecture_business_definition.md`
- Branch execution log: `docs/poster2/current_branch_execution_log_v1.md`

## Current established state

- Read first for this restart pass:
  - `AGENTS.md`
  - `CLAUDE.md`
  - `docs/poster2/README.md`
  - `docs/poster2/current_branch_execution_log_v1.md`
  - `docs/poster2/poster_generation_product_design_baseline_v1.md`
  - `docs/poster2/template_dual_v2_architecture_business_definition.md`
  - `docs/poster2/template_dual_v2_structural_rebuild_baseline_v1.md`
- PR-7 complete: product image bounds / fit authority unified under `product_policy`
- PR-8A accepted intermediate baseline: safe product-geometry widening baseline
- PR-8B complete and merged: product annotation/text runtime contract under `product_policy`
- poster2/template_dual_v2 skeleton is treated as stable for closure engineering
- `product_anchor_callouts` is the live production mode
- product ownership and bottom SOP baseline are treated as frozen
- bottom remains in maintenance mode only; no redesign work is active
- current closure engineering scope:
  - poster_record persistence
  - backend email draft generation
  - Resend-backed send path plus Stage3 closure
  - Gemini-backed copy optimization with deterministic fallback
  - optional backend-owned email attachment assets
- Stage3 must consume live backend payload only
- frontend may cache in `sessionStorage` but must not treat it as truth source

## Current branch-log facts

- `project_poster2_baseline_2026-03-30.md` is missing in this workspace
- `docs/poster2/current_branch_execution_log_v1.md` is the working execution/state log for branch-local progress
- closure engineering adds:
  - `poster_key` on `/api/v2/generate-poster`
  - persisted `poster_record`
  - `GET /api/v2/posters/{poster_key}`
  - `POST /api/v2/email/preview`
  - `POST /api/v2/email/send`
- current closure extension adds:
  - optimizer-aware email draft generation from canonical poster_record truth
  - `generated_from` / `summary_points` / `tone`
  - backend-owned `email_assets.poster_png` and `email_assets.poster_pdf`
  - optional resend attachment wiring through `attachment_types`
- copy quality tightening adds:
  - poster-facing text sanitization for title / subtitle / features / annotation-derived text
  - deterministic preview policy that prefers product sell points over subtitle
  - Gemini post-sanitization and grounded-claim rejection
  - fallback to deterministic when Gemini is unsafe or not materially better
- Stage2 now carries `poster_key` in the success URL and forwards Stage3 via query param
- Stage3 now restores poster, draft source, and attachment readiness from backend truth, then supports light edit plus send
- PR-S2 complete:
  - Stage2 bottom mode state now canonicalizes before runtime
  - `title_only -> text_only_expanded`
  - stale `title_only_expand -> text_only_expanded`
  - preview and final generate now use the same canonical `bottom_mode` truth
- no poster structure contract changes were made in this closure pass
- Family A fryer blocker closeout complete:
  - product-region text shell now uses a bounded fryer-only fixed-slot capacity variant
  - fryer default bottom subtitle now renders the required commercial sentence without forced fit rewrite
  - fryer accepted optimization still switches rendered output and metadata truth together
  - fryer bottom strip now uses the bounded detail-row distribution inside `title_gallery_split`
- Family A fryer hero/footer blocker removal complete:
  - fryer secondary asset no longer auto-promotes the hero into the generic dual split
  - fryer hero now resolves through a bounded single-primary + supporting-inset geometry variant
  - fryer product region now uses `w=520`, `primary=324x540`, `secondary=120x120`, `text lane x=792 w=184`
  - fryer footer remains `title_gallery_split` but now uses `title=172`, `strip=90`, `items=66`, `peer_gap=14`
- Family A fryer truth/parity closeout complete:
  - fryer annotation contract review now reads resolved slot truth from `product_policy`
  - fryer-only stale `template_spec_fixed` evidence is removed from annotation review paths
  - fryer bottom behavior now exposes `gallery_caption_mode`, `gallery_caption_owner`, and `gallery_caption_slots`
  - Pillow final footer now renders bounded thumbnail + caption cards for fryer detail rows
  - non-fryer Family A footer caption mode remains `none`

## Current document alignment target

- `AGENTS.md` should remain rules only
- `CLAUDE.md` should remain shared state only
- `docs/poster2/README.md` should remain index only
- process-heavy / one-off / duplicated branch-local materials should not define the formal document path

## Next code priority

- current temporary priority override = none
- Template A remains the active oracle line for shared-skill and commercial acceptance verification
- pre-change rollback tag for this pass:
  - `Poster2-FamilyA-MinDelta-PreCommercialRefine`
  - `cdb3216cbb1b95630c9afbb27a9ada9c90af37a7`
- hard boundaries remain:
  - no freeform geometry editing
  - no ownership drift
  - no Template B work
  - UI layout and 3-column header stay unchanged
- last closed refinement focus:
  - fixed product annotation slots stayed fixed while fryer card capacity was widened in a bounded variant
  - fryer bottom subtitle now reaches render as finalized product-grade copy
  - fryer bottom strip now reads as a semantic detail row with breathing room
  - fryer hero stage now reads as a single dominant product stage with a supporting inset
- latest bounded closeout:
  - fryer annotation evidence now matches resolved runtime slot truth
  - fryer final footer now matches preview semantics as a thumbnail + caption row
- not yet: Family A redesign
- not yet: Template B reopen
- not yet: editor-first drift
