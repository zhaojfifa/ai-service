# Beautification Phase 1 — Status v1

**Date:** 2026-03-28
**Phase:** 1 — minimal beauty-token-driven improvements on top of established region contract baseline
**Status:** COMPLETE — 153/153 tests pass; no geometry or behavior regression

---

## 1. Startup Context Used

- `CLAUDE.md`
- `AGENTS.md`
- `docs/poster2/README.md`
- `docs/poster2/poster2_product_flow_reviewable_v1.md`
- `docs/poster2/bottom_behavior_contract_status_v1.md`
- `docs/poster2/beautification_layer_plan_v1.md`
- `docs/poster2/feature_anchor_callouts_contract_status_v1.md`
- `app/templates/specs/template_dual_v2.json` (runtime metadata)
- `app/templates_html/template_dual_v2.css` (Puppeteer rendering path)
- `app/services/poster2/template_behavior.py` (token presets + CSS var generation)
- `app/services/poster2/renderer.py` (Pillow rendering path)

---

## 2. Phase 0 — Contract Stability Verification

Confirmed stable before starting beautification:

| Check | Status |
|-------|--------|
| `header_mode` drift repaired | ✅ Fixed in `feature_anchor_callouts_contract_status_v1.md` |
| `template_behavior.behavior_modes.header_mode` matches `header_contract_review.header_mode` | ✅ Aligned |
| Stage 2 modeLabel paths read `behavior_modes.*` | ✅ Fixed |
| `feature_mode = count_driven_callout_stack` in template spec | ✅ Confirmed |
| `product_anchor_callouts` NOT present in this task | ✅ Excluded per scope |
| beauty_tokens schema present in `template_dual_v2.json` | ✅ `glass_light / soft_line / soft / warm_red / campaign_primary` |
| Both renderer paths (Pillow + Puppeteer) consume token families | ✅ Confirmed |

No unresolved contract drift found. Proceeding to Phase 1.

---

## 3. Files Changed

| File | Type of Change |
|------|---------------|
| `app/services/poster2/template_behavior.py` | Token preset values updated (beauty layer only) |
| `app/services/poster2/renderer.py` | Pillow fill/border/shadow + anchor marker ring |
| `app/templates_html/template_dual_v2.css` | CSS fallback vars + connector/marker visual refinement |

---

## 4. Visual Refinements Made

### 4.1 Shell Surface — `glass_light` preset

| Shell target | Before | After | Rationale |
|---|---|---|---|
| `bottom` start opacity | 0.70 | 0.74 | More finished panel feel |
| `bottom` end opacity | 0.56 | 0.60 | Consistent with start bump |
| `title_band` start opacity | 0.94 | 0.96 | Slightly crisper legibility zone |
| `title_band` end opacity | 0.88 | 0.90 | Consistent with start bump |
| `gallery_strip` opacity | 0.68 | 0.72 | Cleaner gallery frame |
| `feature_card` opacity | 0.95 | 0.96 | Minor consistency bump |
| `header`, `scenario`, `product` | unchanged | unchanged | Already at target quality |

Pillow path (`_pillow_shell_fill["glass_light"]`):
- `bottom` alpha: 156 → 178
- `title_band` alpha: 224 → 238
- `gallery_strip` alpha: 168 → 182

### 4.2 Shell Border — `soft_line` preset

| Token | Before | After | Rationale |
|---|---|---|---|
| `--shell-border-accent-alpha` | `"14"` (7.8%) | `"1a"` (10.2%) | Slightly more defined panel edge |
| `--feature-card-border-alpha` | `"1f"` (12.2%) | `"26"` (14.9%) | Better card edge definition |
| `--shell-border-gallery` | `rgba(255,255,255,0.44)` | `rgba(255,255,255,0.50)` | Cleaner gallery strip frame |
| `--shell-border-hero` | unchanged | unchanged | Hero shell border stays subtle |

Pillow path (`_pillow_border`):
- `soft_line` accent alpha: 20 → 26

### 4.3 Shell Shadow — `soft` preset

| Target | Before | After | Rationale |
|---|---|---|---|
| `--shell-shadow-main` | `0 18px 36px rgba(34,22,22,0.11)` | `0 20px 40px rgba(30,18,18,0.13)` | Slightly more natural depth |
| `--shell-shadow-secondary` | `0 12px 26px rgba(31,22,22,0.08)` | `0 14px 28px rgba(28,18,18,0.10)` | Consistent improvement |
| `--feature-card-shadow` | `0 12px 24px rgba(24,16,16,0.10)` | `0 12px 26px rgba(22,14,14,0.11)` | Slightly more refined card shadow |
| `--gallery-item-shadow` | `0 10px 22px rgba(31,22,22,0.10)` | `0 10px 24px rgba(29,18,18,0.11)` | Minor gallery item lift |

Pillow path (`_pillow_shadow`):
- `soft` params: `(0, 10, 10, 0, 26)` → `(0, 12, 12, 0, 32)` (offset, blur, alpha)
- `medium` params: `(0, 12, 14, 0, 38)` → `(0, 14, 16, 0, 44)` (consistent bump)

### 4.4 Feature Connector Visual Refinement (Puppeteer path)

**`.feature-callout-connector`** (HTML/CSS):
- Added `border-radius: 1px` — softens the connector line endpoints
- Added `opacity: 0.9` — connector at 90% intensity rather than full; slightly more refined

**`.feature-callout-marker`** (HTML/CSS):
- Added `box-shadow: 0 0 0 2.5px rgba(255, 255, 255, 0.78)` — subtle white halo ring around the anchor dot; makes it read as a more finished callout indicator

**Pillow anchor marker** (`_draw_feature_callout_structure`):
- Added white ring ellipse before colored dot: `draw.ellipse([ax-r-2, ay-r-2, ax+r+2, ay+r+2], fill=(255,255,255,200))`
- White ring is 2px expansion around the anchor dot, alpha 200/255
- Consistent intent with the CSS `box-shadow` ring; Pillow and Puppeteer remain separately implemented (no exact parity required per doc baseline)

### 4.5 CSS Fallback Vars

Updated `#poster-root` vars in `template_dual_v2.css` to match the new preset values. These are fallback values only — the behavior-generated CSS vars always take precedence at runtime via `style="__BEAUTY_CSS_VARS__"` injection. Updated for consistency and documentation accuracy.

---

## 5. What Was Intentionally NOT Changed

| Area | Why excluded |
|---|---|
| Region geometry (positions, sizes) | Out of scope — contract baseline is fixed |
| Slot ownership | Out of scope — contract baseline is fixed |
| Behavior mode semantics | Out of scope — behavior layer is upstream |
| `product_anchor_callouts` renderer path | Out of scope — explicitly excluded in task |
| `campaign_primary` text_emphasis colors | Already correct; title/subtitle at accent tone is the intended hierarchy |
| `panel_clean`, `panel_dark_soft`, `solid_soft` presets | Not the active token for `template_dual_v2`; no need to change |
| `clean_frame`, `none` border presets | Not active |
| `medium`, `none` shadow presets | Not active |
| `editorial_soft`, `high_contrast` text_emphasis | Not active |
| Stage 2 HTML layout / controls | No change — Stage 2 remains backend-driven read-only review surface |
| Pillow/Puppeteer exact parity for feature callout boxes | Not a goal per `beautification_layer_plan_v1.md` §8 |

---

## 6. Proof No Geometry or Behavior Change

All changes are within:
- Opacity/alpha values in CSS gradient strings
- Box-shadow values in CSS
- RGBA alpha components in Pillow tuples
- CSS `border-radius` and `opacity` on connector element
- CSS `box-shadow` on marker element
- A 2px white ellipse drawn before the colored anchor dot (Pillow)

No changes to:
- `canvas_w`, `canvas_h`, or any slot position/size in `template_dual_v2.json`
- Any geometry-driving CSS variable (`--bottom-shell-top`, `--title-band-height`, etc.)
- Any resolver function in `template_behavior.py`
- Any behavior policy enum or resolution path
- Any contract schema field
- `_draw_shells` geometry bounds (`_header_shell_bounds`, `_bottom_shell_bounds`, etc.)
- Any region collapse logic, count policy, or mode resolution

---

## 7. Validation Results

```
pytest tests/poster2/test_renderer.py tests/poster2/test_pipeline.py \
       tests/poster2/test_api.py tests/poster2/test_contracts.py \
       tests/test_stage2_guard_diagnostics_surface.py \
       tests/test_frontend_docs_sync.py -q

153 passed, 2 warnings in 14.63s
```

- No test failures
- 2 warnings are pre-existing (Pydantic V1 deprecation)
- Gallery distribution, text chains, evidence fields, diagnostics surface all pass
- `test_frontend_docs_sync.py` — `frontend/` and `docs/` sync state checked

> Note: `test_frontend_docs_sync.py` validates that `frontend/app.js` and `docs/app.js` are in sync. The CSS file at `app/templates_html/template_dual_v2.css` is backend-served, not a frontend sync target. `frontend/stage2.html` was not changed in this round, so no sync needed.

---

## 8. Deferred Items

### 8.1 `product_anchor_callouts` renderer branch
- **Status:** Contract stable, resolver complete; renderer still uses generic stacking algorithm
- **Why deferred:** Out of scope for this beautification round per task constraint
- **Next step:** Add `product_anchor_callouts` branch in `_resolve_feature_callout_layout` that reads `anchor_x / anchor_y` directly from template spec
- **Reference:** `feature_anchor_callouts_contract_status_v1.md` §Known Bugs item 1

### 8.2 Preview-path / generation-path parity (Puppeteer vs Pillow)
- **Status:** Known divergence on feature callout box backgrounds (Pillow: no card background; Puppeteer: full card with surface/border/shadow)
- **Why deferred:** Renderer parity is a separate work item, not beautification
- **Next step:** Align Pillow feature callout box rendering with Puppeteer card style

### 8.3 Stage 2 presentation polish
- **Status:** Stage 2 mode chips and region rows are functional and readable; no polish applied in this round
- **Why deferred:** Core renderer beautification was higher priority; Stage 2 CSS is already adequate
- **Next step:** Minor typography/spacing improvements to `.s2-mode-chip` and `.s2-region-head` if requested

### 8.4 Other region resolver coverage
- **Status:** `header_region`, `scenario_region`, `product_region` do not yet have full resolver coverage
- **Why deferred:** Phase 3 work, upstream of any further beautification
- **Reference:** `docs/poster2/README.md` Phase 3 section

---

## 9. Next Recommendation

1. **Run a live generation** against the backend and inspect the poster visually — confirm shells look more defined, shadows have more natural depth, and feature callout markers have the white halo ring.

2. **Stage 2 contract panel review** — verify all 5 region detail cards populate, requested/rendered text chains are correct, and no evidence regression.

3. **`product_anchor_callouts` renderer branch** (next behavior-adjacent task) — add the fixed-position renderer branch so anchor callouts render at the template-specified positions rather than the centering algorithm.

4. **Phase 3 region resolver coverage** — replicate bottom SOP pattern to `header_region`, `scenario_region`, `product_region`, `feature_region`.

---

## 10. Architecture Stance Preserved

- Backend remains truth-source; Stage 2 was not changed
- Contract-first order maintained: Structure → Control → **Beautification** (this round)
- Shell/content separation intact — only visual surface layer changed
- Renderer is execution layer, not template truth-source — no behavior logic added to renderer
- beauty token families remain separate from behavior policy resolution
- `frontend/` and `docs/` are in sync (no Stage 2 HTML changes made)
