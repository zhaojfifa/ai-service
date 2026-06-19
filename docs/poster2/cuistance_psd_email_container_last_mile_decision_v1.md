# CUISTANCE v1 · PSD 邮件容器 last-mile 工程决策 v1

Purpose: Record the last-mile engineering decision for turning the frozen `~/poster/ingredient/` design source
(产品海报.psd + ttt.html + ttt2.html) into a deterministic, Workbench-truth-driven email container — WITHOUT
becoming a generic PSD parser and WITHOUT letting old business facts enter CUISTANCE runtime.
Status: Phase 0 (freeze) — material frozen, baseline recorded, no runtime behavior changed.
Scope: design-shell extraction + deterministic email container; Workbench remains the only business truth source.
Owner gate: GO for direct heavy engineering (no Harness-X); real email send remains HOLD; no main merge / no tag push.

Task: `POSTER2-CUISTANCE-PSD-EMAIL-CONTAINER-LAST-MILE-HEAVY-V1`.

---

## 1. Rollback point (frozen baseline)

- Accepted asset-chain baseline commit: **`ae5e527`** (Step-1 asset persistence + backend-confirmed generate
  payload + current poster binding + selected-visual confirmation + header-only fix + email preview).
- Rollback tag (local, NOT pushed): **`poster2-cuistance-asset-chain-pass-ae5e527`** → `ae5e527`.
- Working branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1` (off `ae5e527`).
- Worktree note at start: only `.DS_Store` / `docs/.DS_Store` were tracked-dirty (macOS noise, present since
  session start); all other entries are pre-existing untracked artifacts. No real code was dirty; HEAD == `ae5e527`.

### Rollback commands (do NOT run unless Owner asks)

```bash
# return to accepted asset-chain baseline
git checkout trial/poster2-cuistance-v1-operator-trial
git reset --hard ae5e527

# or inspect rollback tag
git checkout poster2-cuistance-asset-chain-pass-ae5e527
```

## 2. Why PSD is accepted (as a design shell only)

`产品海报.psd` is a 600×1577 layered email/poster (a Technitalia/Codimatel-style **gas-réchaud** campaign). It gives
us a real, proportioned 600px email **container grammar**: dark header band → product/body visual stage → product
intro block → spec block → social/contact/footer band with red dividers. We accept it purely as a **design shell**
(geometry + region ordering + visual rhythm), exactly the "last mile" the operator UI still lacks (a full, coherent
600px send-ready email container instead of stacked cards).

## 3. Why the current asset-chain baseline is frozen

`ae5e527` is the Owner-accepted chain: asset persistence → backend-confirmed generate payload → current poster
binding → selected-visual confirmation → header-only fix → email preview. This run must NOT reopen that chain unless
a regression is proven. The PSD email container is additive (a new `email_container_template_id`), layered on top of
the frozen chain.

## 4. Why this is NOT a generic PSD parser

We parse exactly ONE PSD into ONE CUISTANCE-specific slice manifest (`cuistance_email_container_psd_v1`). There is no
general PSD-platform, no online editor, no arbitrary-PSD ingestion, no layer-editing UI. The parser scripts are
CUISTANCE-seed-specific and produce static manifests, not a runtime PSD engine.

## 5. Why Workbench truth remains the source of facts

Every business fact in the PSD belongs to the OLD gas product (LES RÉCHAUDS GAZ, XR 1444 / 4 BRULEURS, gas kW specs,
phone `01 41 53 12 12`, `kaly@tec…` email, old social/contact). These are **rejected truth** and are never allowed
into runtime. The email container exposes only **replaceable slots** bound to Workbench truth:
brand logo ← `workbench.email_banner.logo`; body visual ← `workbench.selected_email_body_visual` poster
`final_poster.url`; contact/footer ← `workbench` contact fields. `selected_email_body_visual = affiche | fiche`
stays backend-confirmed.

## 6. Why real send remains HOLD

No provider is configured; inline_only/preview_only must continue to read as "not real sent". This run does not
change email provider behavior and sends no email.

## 7. Phase plan

- **Phase 0 (this doc)** — freeze `~/poster/ingredient/` → project seed + sha256 manifest + source inventory +
  rollback record. No runtime change.
- **Phase 1** — parse PSD (psd_tools) + ttt/ttt2 (stdlib) → `psd_layer_inventory.json`, `psd_slice_manifest.json`,
  `rejected_truth_layers.json`, `html_reference_inventory.json` + flat/overlay screenshots. No integration.
- **Phase 2** — deterministic 600px email container (`cuistance_email_container_psd_v1`) for
  `campaign_poster_email` / `product_sheet_email`; HTML/CSS assembly; preview-only.
- **Phase 3** — integrate into `/cuistance_trial.html` Step 3; 3-step flow + refresh recovery; operator screenshots.
- **Phase 4** — remote/operator validation (deploy + OPS gated).

## 8. Tooling note

`psd_tools 1.17.2` was installed into the isolated `.venv` for analysis only (NOT added to runtime
`requirements.txt`); HTML reference parsing uses the Python stdlib (`html.parser`) — no new runtime dependency.
`psd_layer_auto_parse=true`.

## 9. Phase 0 acceptance

- source files copied to `docs/poster2/assets/cuistance_psd_email_container_last_mile_v1/source/` ✓
- sha256 manifest `inventory/source_sha256.txt` ✓
- source inventory `inventory/source_inventory.json` ✓
- decision doc (this file) ✓
- rollback point/tag/branch documented ✓
- no runtime behavior changed ✓
