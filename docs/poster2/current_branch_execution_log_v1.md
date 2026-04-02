# Current Branch Execution Log v1

## Mainline Replacement Note
- old `origin/main` archived before replacement:
  - branch: `archive/main-before-pra-product-outer-shell-20260401`
  - tag: `backup/main-before-pra-product-outer-shell-20260401`
- new `origin/main` points to `fix/pra-product-outer-shell` baseline commit `1b4d001`
- no merge commit was used
- future poster2 work starts from the new `main` only

## Current Active Workstream
- workstream: `product region contract upgrade`
- execution mode: `one function = one PR`
- current active PR: `PR-2 — product text-layer contract closure`
- current PR status doc: `docs/poster2/product_region_pr2_text_shell_contract_status_v1.md`

## Frozen Unchanged
- bottom frozen as SOP baseline
- `feature_region` must stay delegated diagnostic when product annotation is active
- header/scenario behavior out of scope for current product-region PRs
- beautification out of scope
- old-main compatibility must not be reopened

## Carry-Forward Truth From PR-A
- `product_region` / `product_card_shell_layer` outer shell: `{x:456,y:188,w:472,h:540}`
- `product_canvas_shell_layer`: `{x:456,y:188,w:300,h:540}`
- `product_image_layer` anchors to `product_canvas_shell_layer`, not the widened outer shell
- fixed annotation lane remains on the right side and was intentionally not reopened in PR-A
- declared next priority after PR-A: add `product_text_shell` as a sibling shell and keep `feature_region` suppressed

## Last Accepted PR
- `PR-1 — Product Region Boundary Closure`
- status: accepted
- status doc: `docs/poster2/product_region_pr1_boundary_closure_status_v1.md`
- carry-forward result:
  - Puppeteer `product_card_shell_layer` boundary now matches contract height `h:540`
  - `product_card_shell_layer`, `product_canvas_shell_layer`, and dual product image bounds now close at the same bottom edge
  - frozen unchanged from PR-1:
    - `product_primary_slot = {x:456, y:188, w:300, h:310}`
    - `product_secondary_slot = {x:456, y:518, w:300, h:210}`
    - `product_canvas_shell_layer h = 540`
    - annotation lane unchanged
    - text-shell not started in PR-1

## Current PR Goal
`PR-2 — product text-layer contract closure`

Required result:
- add `product_text_shell` as a real sibling shell under `product_region`
- make `product_text_shell` explicit in backend contract/evidence
- bind annotation text truth to product-owned text-shell surfaces
- keep `product_canvas_shell_layer` separate from text ownership
- keep `feature_region` suppressed/delegated
- no UI wiring in this PR

## Next PR To Start After PR-2 Acceptance
- `PR-3 — product text-layer UI and Stage2 driver wiring`
- status doc: `docs/poster2/product_region_pr3_text_ui_and_driver_status_v1.md`
- blocked until PR-2 is accepted

## Reading Rule For New Sessions
Do not read this whole file as a long archive.
Read only these sections:
1. `Mainline Replacement Note`
2. `Current Active Workstream`
3. `Last Accepted PR`
4. `Current PR Goal`
5. `Next PR To Start After PR-2 Acceptance`

If deeper detail is needed, open the linked PR status doc instead of expanding this file.

## Archive Note
Detailed historical entries were moved out of the active working set.
Use an archive file or the per-PR status docs for full historical detail.
