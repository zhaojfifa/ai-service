# Template Taxonomy & Visual Relaxation Plan (v1)

Status: planning only. No code. No Stage2 flow change. No `/api/v2/generate-poster`
contract change. No Template A/B breaking change. No freeform editor. No
AI-generated arbitrary layout.
Author role: architecture & product reviewer.

Related: [template_seed_generation_support_plan_v1.md](template_seed_generation_support_plan_v1.md),
[ppt_1to1_template_analyzer_adaptation_review_v1.md](ppt_1to1_template_analyzer_adaptation_review_v1.md),
[beautification_layer_plan_v1.md](03_engineering/beautification_layer_plan_v1.md).

---

## 0. The Governing Distinction (read this first)

The "too tightly fitted / mechanically packed" problem has **two different causes**
that must be solved by **two different layers**, and conflating them is the main
risk:

- **Surface & negative-space causes** — crowded text, weak image blending, gallery
  that *feels* heavy, uniform mechanical spacing, "correct but not designed."
  These are solved by the **Visual Relaxation Layer**, which tunes *padding, gaps,
  insets, blending, surface weight, and text rhythm* — **never region geometry.**
  This is a beauty-token extension and is contract-safe.

- **Geometry causes** — product slot genuinely too large/small, gallery slot
  genuinely occupying too much canvas. Changing these means changing region
  geometry, which the relaxation layer **must not** do. Those are solved by
  **authoring a new template** (a style-variant or new fixed template) with
  different geometry — a taxonomy move, operator-authored, version-bumped.

> Relaxation changes the **space between and inside** regions. It never moves the
> **boundaries of** regions. Bottom SOP truth and product-annotation truth are
> region/ownership truth — they are **untouched** by relaxation by construction.

Everything below follows from this split.

---

## 1. Template Taxonomy

Four classes, all pinned to an existing **base family** (`family_a_campaign_explainer`
or `family_b_product_sheet_story`). None introduces a new visual family or new
render shell.

| Class | What it is | Authoring source | Geometry | Beauty/Relaxation |
|---|---|---|---|---|
| **Fixed base templates** | The canonical hand-authored templates (Template A `template_dual_v2`, Template B `template_product_sheet_v1`) | Hand-authored spec + render assets | Frozen, owns the base shell | Base preset |
| **Seeded templates** | Templates derived from a reference poster via the Seed pipeline | Reference image → seed draft → blueprint → compiler (see seed plan) | Parameterization of a base shell only | Inherited + bounded overrides |
| **Style variant templates** | A base (or seeded) template re-issued with a different **relaxation/beauty preset** and optionally bounded permitted geometry deltas | Operator picks a preset over an existing base | Same base shell; only permitted geometry deltas | **Primary consumer of the relaxation layer** |
| **Campaign pack templates** | A *named set* of coordinated templates (e.g. main campaign poster + product sheet + an airy variant) sharing palette/tokens for one campaign | Library grouping of the above classes | Per-member (inherited) | Shared token theme across members |

Notes:

- **Campaign pack is an authoring/library construct, not a runtime construct.** At
  runtime each pack member is just a normal `template_id`. The "pack" is metadata
  that groups members and shares a token theme; Stage2 never sees a "pack."
- **Style variant is the cheapest, highest-leverage class** for the immediate
  visual problem: it lets us ship an "airy / relaxed" issue of Template A without
  touching Template A itself.

---

## 2. Supported Now vs Later

| Class | Status | Gating dependency |
|---|---|---|
| Fixed base templates | **Now** (exist today) | none |
| Style variant templates (beauty-preset only, no new geometry) | **Now-adjacent** | requires the relaxation token family to be consumed by the renderer (small, additive, §6); until then a variant can only re-use existing tokens |
| Style variant templates (with bounded geometry deltas) | **Later** | needs variant-authoring + validation (Phase 2–3) |
| Seeded templates | **Later** | full seed pipeline (seed plan Phase 3) |
| Campaign pack templates | **Later** | template library layer (seed plan Phase 4) |

The immediate visual relief ("posters feel too tight") is delivered by the
**relaxation layer applied to the existing fixed base templates** (no new template
needed) plus the first **style variant** — both available early, both contract-safe.

---

## 3. Runtime Compatibility Table

"Runs through existing Stage2 unchanged" = loads via `load_template(template_id)`,
renders through the existing Puppeteer/Pillow path, passes the existing
`quality_guard`, with **no** change to `/api/v2/generate-poster`.

| Class | Loads via existing loader? | Existing Stage2 path? | `/api/v2/generate-poster` change? | Quality guard reused? | Notes |
|---|---|---|---|---|---|
| Fixed base | ✅ | ✅ | ❌ none | ✅ | as today |
| Relaxation preset applied to a fixed base (no new id) | ✅ | ✅ | ❌ none | ✅ | new beauty tokens are forward-compatible: `TemplateSpec.from_json` already filters unknown keys, so adding token keys to a spec is non-breaking; rendering them needs the additive CSS-var mapping in §6 |
| Style variant (new id) | ✅ | ✅ | ❌ none | ✅ | separate spec + registry entry; pins `base_family` |
| Seeded | ✅ (once compiled+registered) | ✅ | ❌ none | ✅ | per seed plan |
| Campaign pack member | ✅ | ✅ | ❌ none | ✅ | pack grouping is ops-only metadata |

**Conclusion:** every class runs through Stage2 unchanged once it exists as a
registered template. The only net-new runtime capability is the **additive**
relaxation-token → CSS-var mapping (§6), which extends beauty tokens without
altering any contract, signature, or geometry.

---

## 4. Beauty Token Model

Extend the existing `TemplateBeautyTokensSpec` (today: `shell_surface`,
`shell_border`, `shell_shadow`, `accent_tone`, `text_emphasis`) with a new,
bounded **Composition / Relaxation token family**. Every token is a **closed enum**,
never a free numeric/pixel value. Each enum maps deterministically to a bounded set
of the CSS variables that already exist in `template_dual_v2.css`.

Proposed relaxation token family (illustrative names + enums):

| Token | Enum values | Maps to (existing CSS vars / mechanism) | Solves |
|---|---|---|---|
| `density` | `airy` \| `balanced` \| `compact` | global multiplier over `--peer-region-gap`, shell insets | overall "mechanically packed" feel |
| `region_gap` | `relaxed` \| `standard` \| `tight` | `--peer-region-gap` (currently 24px) | regions touching / no rhythm |
| `text_breathing` | `loose` \| `standard` \| `dense` | `--title-stack-gap`, line-height, letter-tracking, max-lines headroom | crowded text |
| `product_breathing` | `generous` \| `standard` \| `snug` | `--product-content-pad-*` (inset **inside** the product slot) | product area lacks breathing room — **without resizing the product slot** |
| `image_blend` | `feathered` \| `soft` \| `hard` | scenario↔product seam gradient/mask (the near-transparent `--shell-surface-scenario-real` seam) | weak scenario/product blending |
| `gallery_weight` | `recede` \| `balanced` \| `present` | `--shell-surface-gallery-strip`, gallery border/opacity, `--peer-region-gap` above gallery | bottom gallery dominates / feels mechanically inserted |
| `elevation` | `flat` \| `soft` \| `lifted` | `--shell-shadow-main` / `--shell-shadow-secondary` | flat, undesigned look |
| `accent_restraint` | `quiet` \| `standard` \| `bold` | `--accent-tone` saturation/usage | over-uniform / shouty accent |

Hard rules for the token model:

1. **Enums only.** No template or operator ever sets a raw pixel/number through
   tokens. The enum→CSS-var mapping table is the single source of bounded values.
2. **Tokens never emit geometry.** They write only spacing/inset/surface/blend/text
   CSS variables. They cannot write slot `x/y/w/h`, region boundaries, anchor
   positions, or annotation slot coordinates.
3. **Backward-compatible defaults.** Every new token has a default that reproduces
   today's exact rendering (`density: balanced`, etc.), so existing templates are
   visually unchanged until a preset opts in.
4. **Forward-compatible loading.** Unknown token keys are already ignored by
   `from_json`; the renderer maps only known tokens. Adding the family is additive.

---

## 5. Composition Relaxation Rules

Concrete, bounded responses to each named visual issue. All operate via §4 tokens;
none changes geometry.

1. **Text feels crowded** → `text_breathing: loose`: increase `--title-stack-gap`,
   add line-height and a small tracking increase, and reserve max-lines headroom so
   auto-shrink engages later. Bounded: tracking and line-height move within a
   defined min/max; text never overflows its slot (auto-shrink still governs).

2. **Product area lacks breathing room** → `product_breathing: generous`: increase
   the **inset padding inside** the product slot (`--product-content-pad-*`) so the
   product image floats with margin **within its existing slot box**. The product
   slot geometry (`x:456 y:188 w:300 h:540`) is unchanged; only the negative space
   inside it grows. (Genuinely shrinking the product *region* is a geometry change →
   a style-variant template, not a relaxation token — §0.)

3. **Bottom gallery dominates / feels mechanically inserted** → `gallery_weight:
   recede`: de-emphasize the gallery shell surface and border, lower its contrast,
   and increase the gap separating it from the title band so it reads as a
   supporting strip, not a second hero. For cases where the gallery should not lead
   at all, the **existing** `bottom_mode` enum already offers `text_only_expanded`
   (gallery collapsed) and `gallery_mode: supporting_packshots` — relaxation tunes
   weight; behavior modes choose presence. **Bottom SOP truth (geometry/ownership)
   is untouched.**

4. **Weak scenario/product blending** → `image_blend: feathered`: strengthen the
   gradient/feather mask at the scenario↔product seam (the CSS already models this
   seam as a near-transparent surface). Produces a soft transition instead of a hard
   edge. Bounded: a mask/gradient overlay only; no compositing logic change in
   Stage1/Stage2, no geometry move.

5. **"Correct but not designed"** → combine `density: airy` + `elevation: soft` +
   `accent_restraint: quiet` to introduce a deliberate **2-level spatial rhythm**
   (the predecessor design rule: max ~2 visual hierarchy levels). The fix is
   *intentional asymmetric breathing and restrained accent*, not more decoration.

Relaxation invariants:
- Never moves a region boundary, anchor, or annotation slot.
- Never collapses/adds a region (that is `behavior_modes`' job, already governed).
- Never masks a structure/behavior failure — `quality_guard` still runs first and
  binds (consistent with the beautification-layer doctrine: beauty is downstream).

---

## 6. Renderer Integration

**Puppeteer-first, fully additive, no parity break.**

- **Token → CSS-var mapping** lives in the same channel that already injects beauty
  tokens: the renderer expands the relaxation enums into CSS custom properties and
  injects them through the existing `__BEAUTY_CSS_VARS__` placeholder on the root
  element. The CSS variables they set (`--peer-region-gap`, `--title-stack-gap`,
  `--product-content-pad-*`, gallery surface vars, shadow vars, seam gradient)
  **already exist** in `template_dual_v2.css`; relaxation only changes their values
  within bounds.
- **No new HTML structure, no markup authoring.** The shell, data-region/data-slot
  markup, and layer order are unchanged. This keeps region semantics, ownership,
  bottom SOP, and annotation truth frozen.
- **Pillow path:** relaxation tokens that map cleanly to Pillow spacing/padding
  (e.g. `region_gap`, `product_breathing`, `text_breathing`) may be honored by the
  Pillow renderer; tokens that have no faithful Pillow equivalent (e.g.
  `image_blend: feathered`, fine gradient seams) are **ignored by Pillow and must
  be declared Puppeteer-only**. A style-variant/seeded template that *depends* on a
  Puppeteer-only relaxation effect must be marked `pillow_compatible: false`
  (Puppeteer-only, no silent fallback) — same policy as the seed plan. Degradation
  stays explicit.
- **Determinism preserved:** same spec + same tokens → same CSS vars → same render.
  No model call at render time; the enum→var table is static.

---

## 7. Validator Updates

Additive checks; the existing `quality_guard` remains the binding runtime gate and
is **not** forked.

1. **Token legality (compile/author time):** every relaxation token value must be in
   its closed enum; reject unknown values. No raw numbers accepted.
2. **Bounds enforcement (compile/author time):** the enum→CSS-var mapping is the
   only place numbers exist, and each is range-checked against a min/max so even a
   future mapping edit cannot produce out-of-bounds spacing.
3. **Geometry-immutability assertion (compile/author time):** assert that applying a
   relaxation preset changes **only** spacing/surface/blend/text CSS vars and leaves
   all slot/region/anchor/annotation geometry byte-identical to the base. This is the
   structural guarantee that relaxation cannot drift into geometry or touch bottom
   SOP / annotation truth.
4. **Runtime (unchanged):** `quality_guard` still checks structure completeness,
   mandatory regions, required slots, ownership — first and binding. Relaxation can
   never satisfy or mask a structural failure.

---

## 8. Aesthetic Review Criteria

Human, advisory, ops-only (mirrors the seed plan's QA loop; never gates runtime):

- **Breathing:** is there a deliberate, non-uniform rhythm between regions (not all
  gaps equal)? ~2 hierarchy levels, not more.
- **Text comfort:** no crowding; title/subtitle have headroom; auto-shrink not
  fighting the slot.
- **Product presence:** product reads as the protagonist with margin inside its
  slot; not jammed to edges.
- **Gallery role:** gallery reads as supporting, not a competing hero; not
  "mechanically inserted."
- **Blend quality:** scenario↔product transition feels intentional, not a hard
  paste.
- **Designed vs assembled:** does it look composed, or merely contract-correct?
- **Foreign-content robustness:** still looks designed under the 3 foreign asset
  packs (different copy lengths, product shapes) — not overfit to one reference.

Output: an advisory quality report surfaced in ops; the binding gate stays
`quality_guard`. Optional advisory SSIM/structural similarity may be shown, never
used to gate or auto-tune (consistent with prior plans).

---

## 9. Phase Plan

**Phase 1 — Relaxation token family, applied to fixed base templates (no new ids).**
- Define the closed-enum relaxation token family (§4) + the static enum→CSS-var
  mapping with bounds.
- Apply as an opt-in preset to Template A only; default values reproduce today's
  render exactly.
- Puppeteer-first; mark any Puppeteer-only effects; Pillow honors the safe subset.
- Validators §7.1–7.3 added at author time. Runtime unchanged.
- **No new template ids, no registry change, no Stage2 change.**

**Phase 2 — First style-variant template (new id) over a base.**
- Issue e.g. `template_dual_v2_airy_v1` (base_family A): same geometry, a relaxed
  beauty/relaxation preset baked in.
- Goes through the existing loader/registry as a normal template; Stage2-selectable.
- This is the first template that *ships* the relaxed look as a selectable option
  without touching Template A.

**Phase 3 — Bounded geometry-delta variants + seeded-template relaxation reuse.**
- Allow style variants that carry **bounded, permitted** geometry deltas (e.g. a
  smaller product region for genuine breathing) — authored + validated, version
  bumped, base contract untouched.
- Seeded templates (from the seed plan) consume the same relaxation token family.

**Phase 4 — Campaign packs + template library.**
- Group templates into named packs sharing a token theme; ops library for
  listing/versioning/deprecation. Pack remains ops-only metadata; runtime sees
  only individual templates.

Each phase is independently shippable and reversible. Phase 1 cannot affect any
existing output unless a preset is explicitly opted into.

---

## 10. Owner Decisions

1. **Relaxation = non-geometric, confirmed?** Accept §0: relaxation tokens tune only
   negative space / surface / blend / text and never region geometry; geometry
   breathing is a separate style-variant template. (Recommended: yes — it is the
   safety backbone.)
2. **Token family scope:** approve the §4 enum set (or add/remove tokens). Confirm
   enums-only (no raw pixel authoring) as a hard rule.
3. **Default = visually identical?** Confirm Phase 1 defaults must reproduce today's
   render byte-for-byte on geometry and only opt-in presets change appearance.
4. **Pillow policy for relaxation:** confirm Puppeteer-only effects (e.g. feathered
   blend) force `pillow_compatible: false` rather than silently degrading.
5. **First deliverable:** relax Template A in place (Phase 1 preset) vs ship a new
   `*_airy` variant first (Phase 2)? (Recommendation: Phase 1 preset for fast,
   reversible relief; Phase 2 variant for a permanent selectable option.)
6. **Style-variant geometry deltas:** in Phase 3, what geometry is a variant
   *permitted* to change, and what stays frozen (bottom SOP, annotation slots stay
   frozen regardless)?
7. **Campaign pack ownership:** who authors/owns packs; is the shared token theme
   enforced or advisory?
8. **Aesthetic review gate:** advisory-only confirmed (never blocks generation)?

---

## 11. Hard Boundary Compliance

| Boundary | How this plan complies |
|---|---|
| No code changes (this task) | Planning doc only |
| No Stage2 flow change | All classes load/render through the existing path |
| No `/api/v2/generate-poster` contract change | Relaxation is additive beauty tokens; no signature change |
| No Template A/B breaking change | New tokens default to today's render; variants are new ids; A/B specs untouched |
| No freeform canvas/editor | Tokens are closed enums; no pixel/drag authoring; geometry immutable under relaxation |
| No AI-generated arbitrary layout | No model output reaches runtime; relaxation is a static enum→CSS-var map; geometry is operator-authored, validated, version-bumped |
| Bottom SOP truth untouched | Relaxation never moves region geometry/ownership; gallery presence governed by existing `bottom_mode` |
| Product annotation truth untouched | Annotation slots are geometry/ownership truth; relaxation cannot write geometry; §7.3 asserts byte-identical geometry |

---

## 12. Implementation status (v1 — 2026-06-14)

The first relaxation layer is implemented. See the execution-log entry
"Visual Relaxation Layer + template_dual_v2_airy" in
[current_branch_execution_log_v1.md](current_branch_execution_log_v1.md) and
`app/services/poster2/relaxation.py`.

What shipped, and where the build deviated from the §4 token model after the live
CSS + freeze pack were inspected:

- **Presets** `none` / `airy` / `premium_soft` / `dense_safe`, sourced from the
  template spec (`behavior_modes.relaxation_preset`), injected via the existing
  `__BEAUTY_CSS_VARS__` channel (the real emitter is
  `ResolvedTemplateBehavior.css_var_style()` — §6 abstracted this as the channel).
- **`none` injects zero vars** → the `template_dual_v2` render is proven
  byte-identical before/after (Pillow + CSS-var-style hashes unchanged).
- **Only two of the eight proposed token effects are wired**, because the others
  are inert or out-of-bounds against the live code:
  - `text_breathing` → `--title-stack-gap` (effective).
  - `product_breathing` is delivered as a **product-image drop-shadow lift**
    (`--product-primary-shadow`), **not** as inset padding: `--product-content-pad-*`
    is consumed but the product slot inside it is absolutely positioned, so padding
    does not move the product. Genuine product *resize* breathing is a **geometry**
    change → a future geometry style-variant (this is exactly the §0 split in action).
  - `region_gap` / `density` (`--peer-region-gap`): the var exists but is consumed
    nowhere — inert; not wired.
  - `image_blend` (scenario↔product seam): no seam var exists; a seam mask would be
    new geometry → out of bounds; not wired.
  - `gallery_weight` / `elevation` / `accent_restraint`
    (`--shell-surface-*`, `--shell-shadow-*`, `--accent-tone`): authored
    (warm-tinted) by the Family A freeze pack; overriding them would re-tint / mask
    frozen surface truth, so they are left to the freeze pack and not wired.
- **`template_dual_v2_airy`** ships as the first style-variant (Phase 2): same
  Family A shell + byte-identical asset copies, differing only by `relaxation_preset`.
- **Validation**: non-geometric whitelist guard (runtime) + a differential
  geometry-immutability check (`quality_guard.assert_relaxation_non_geometric`,
  proven none-vs-airy region/slot bounds identical) + a 10×-per-template stability
  harness (`scripts/poster2_relaxation_stability_harness.py`).

Net: the implementation confirms the plan's load-bearing thesis (§0) — surface /
negative-space relaxation is safe and additive; anything that needs a region to
actually grow or shrink is a geometry style-variant, not relaxation.
