# CLAUDE.md

## Shared State

This file is shared state only.
Repository rules live in `AGENTS.md`.
poster2 document entry and grouping live in `docs/poster2/README.md`.

## Current poster2 baseline

- Product baseline: `docs/poster2/poster_generation_product_design_baseline_v1.md`
- Family A architecture anchor: `docs/poster2/template_dual_v2_architecture_business_definition.md`
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
- no bottom / product annotation truth changes were made in this closure pass

## Current document alignment target

- `AGENTS.md` should remain rules only
- `CLAUDE.md` should remain shared state only
- `docs/poster2/README.md` should remain index only
- process-heavy / one-off / duplicated branch-local materials should not define the formal document path

## Next code priority

- current temporary priority override = Template A re-baseline -> structure/control abstraction -> beautification freeze
- Family A isolation repair + anti-crossline hardening remains the repaired baseline under this freeze pass
- current narrow insertion before further A-freeze work: Template A bottom support-copy mapping alignment (`Bottom Support Copy` UI label -> canonical backend `subtitle`) is complete
- fresh Family A live Chromium acceptance has now been captured on a non-degraded Puppeteer path
- next poster2 priority after A freeze acceptance: Family A anchored shared-skill extraction
- current priority after the Template A freeze pass: resume deployed-environment validation for Gemini quality and Resend live closure behavior
- next after backend closure: review live-output quality and closure metrics, not poster contract redesign
- bottom text/layout follow-up should remain a known maintenance issue while storage / email work proceeds
- not yet: bottom beautification reopen
- not yet: poster contract redesign
- not yet: editor-first drift
