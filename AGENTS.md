# AGENTS.md

## Purpose

This file is the engineering anchor for work in this repository.
It exists to keep implementation aligned with the agreed product baseline, documentation baseline, and publishing workflow.

This repository does **not** use a broad generic coding-style manual as its primary control point.
Instead, work must follow the repository entry documents and the poster2 document system.

---

## 1. Required reading order before editing

Before starting any implementation task, read in this order:

1. Root `README.md`
2. `docs/poster2/README.md` if the task touches poster2
3. The top-level poster2 product baseline:
   - `docs/poster2/poster_generation_product_design_baseline_v1.md`
4. Then the architecture / stage / family documents relevant to the task

Do **not** jump directly into code, CSS, or renderer logic without re-anchoring on the docs first.

---

## 2. Repository publishing and file-source rules

### 2.1 Source vs published mirror
- `frontend/` is the source area for Stage2 page files.
- `docs/` is the GitHub Pages mirror / published copy.

### 2.2 Sync rule
If a task changes Stage2 page behavior or presentation, the corresponding published files in `docs/` must be kept in sync.
Typical examples include:
- `frontend/stage2.html`
- `frontend/app.js`
- related published copies under `docs/`

Do not leave `frontend/` and `docs/` diverged without explicitly documenting why.

---

## 3. poster2 core architecture stance

All poster2 work must preserve the following:

- contract-first
- no free collage model
- renderer is execution layer, not template truth-source
- shell and content remain strictly separated
- behavior should be lifted into declarative modes / resolver output
- beautification must not hide structure or control failures

### 3.1 Two complementary views, not competing models

#### Product governance view
- Structure
- Control
- Beautification

#### Template execution view
- Background
- Shell
- Content

These are complementary views of the same system.
Do not present them as conflicting architectures.

---

## 4. poster2 implementation order

Default engineering order for poster2:

1. Contract
2. Validation
3. Resolver / behavior wiring
4. Renderer consumption
5. Evidence / metadata
6. Beautification

This order matters.
Do **not** reverse it.

In particular:
- do not start from CSS tuning when the contract is unclear
- do not use Puppeteer or Pillow behavior as the source of template truth
- do not use beautification to compensate for missing control behavior

---

## 5. How to approach a task

For each poster2 task, identify which layer it belongs to:

### A. Contract task
Examples:
- region split
- slot ownership
- required vs optional slot policy
- bottom/title/gallery contract

Rule:
Solve at the contract/model layer first.

### B. Control / behavior task
Examples:
- mode resolution
- text budget policy
- collapse behavior
- overflow behavior
- gallery visible-count behavior
- peer-region balance behavior

Rule:
Solve in declarative behavior / resolver logic, not scattered CSS or renderer branches.

### C. Renderer task
Examples:
- execution of already-resolved contract
- engine-specific rendering mechanics
- parity between Puppeteer and Pillow

Rule:
Renderer must consume the resolved contract/behavior. It must not invent template semantics.

### D. Beautification task
Examples:
- shell surface
- border
- shadow
- text emphasis
- accent tone

Rule:
Only start after contract and control behavior are stable enough.

---

## 6. Scope control rules

When a task is clearly bounded, respect the boundary.

Examples:
- If the task is docs alignment, do not rewrite product architecture.
- If the task is bottom contract validation, do not expand into broad visual redesign.
- If the task is behavior-layer work, do not silently refactor unrelated renderer runtime concerns.
- If the task is README cleanup, do not edit large numbers of unrelated docs unless necessary.

Prefer the smallest coherent fix that preserves the architecture path.

---

## 7. Validation rules

A task is not complete only because a sample image renders.
Validation should match the task type.

### 7.1 For contract/control tasks
Require evidence such as:
- metadata
- rendered region state
- slot ownership
- visible counts
- collapse state
- overflow/clipping state when relevant

### 7.2 For Stage2 tasks
Validate both:
- page-side input / preview path
- final generation path

Do not assume the preview path proves the generation path.

### 7.3 For editing flows
A default happy-path success is not enough.
If a field is intended to be editable, edited valid inputs must also work.

---

## 8. Reporting requirements for each engineering task

After completing work, provide at minimum:

1. Root rules followed
2. Problem reproduced
3. Root cause found
4. Files changed
5. What layer was changed
   - contract
   - behavior
   - renderer
   - docs
   - validation
6. Validation / test steps run
7. Remaining risks

Keep reports concrete and task-scoped.

---

## 9. Red lines

Do not do the following unless the task explicitly requires it and the docs support it:

- invent a new architecture path from implementation convenience
- treat a sample image as the primary specification
- bypass the product baseline and drive behavior from CSS-only fixes
- let renderer-specific logic become the long-term template truth-source
- merge unrelated improvements into one task just because they are nearby
- silently change published behavior without updating the relevant docs or validation path

---

## 10. Practical default

If there is tension between:
- a visually convenient patch
- and a contract-first implementation

choose the contract-first implementation.

If there is tension between:
- fast local tuning
- and keeping `frontend/` / `docs/` aligned

keep the repository aligned.

If there is tension between:
- making one sample look better
- and making the behavior explainable under input variation

choose explainable behavior.

---

## 11. Working principle summary

Use this short version when in doubt:

- Read the docs first.
- Stay on the baseline.
- Contract before engineering.
- Behavior before beautification.
- Renderer executes, not defines.
- Validate edited inputs, not just default samples.
- Keep source and published copies aligned.

---

## 12. Current phase state (as of 2026-03-28)

### Phase 2: bottom SOP baseline — ESTABLISHED + gallery pair tuned

The `bottom_region` resolver path is now the SOP baseline for the behavior layer.

What is established:
- `bottom_mode` / `gallery_mode` / `gallery_count` / title / subtitle controls are always wired in Stage 2, regardless of template eligibility
- **bottom mode selection bug — FIXED** (`initPoster2BottomContractControls` no longer has an early return for non-eligible templates)
- Stage 2 page refactored: two-column Resolver Layout; bottom controls in left panel; debug areas (Result Diagnostics, old Layout Preview) removed; Resolver Layout shows all region rows post-generation via `region_render_status`
- **Bottom contract gallery pair UI upgraded** (`strip_local_visible_only` count=2): `gallery_shell_height` 88→100, `gallery_items_height` 68→80, `item_width` 260→280, `gap` 20→16; pair renders as a proper pair showcase frame, not a compressed residual strip
- **Title char budget relaxed** for 1-line clamp + light gallery + dense subtitle scenario: `title_char_budget` 22→36; Python-level pre-truncation no longer cuts titles at 22 chars — CSS `line-clamp: 1` + `text-overflow: ellipsis` handles visual overflow cleanly
- 116 poster2 tests passing

What this proves:
- bottom behavior can be declared, resolved, and validated end-to-end through the contract → resolver → renderer → evidence path
- the SOP baseline pattern is repeatable
- gallery pair sizing is now a declared resolver output, not an implicit strip default

### Phase 3: replicate to other regions

Apply the same resolver coverage pattern to:
- `header_region` — complete `identity_zone_mode` resolver wiring
- `scenario_region`, `product_region`, `feature_region` — resolver coverage
- Preview-path / generation-path parity收口
- Beautification layer (after behavior stability is confirmed across all regions)
