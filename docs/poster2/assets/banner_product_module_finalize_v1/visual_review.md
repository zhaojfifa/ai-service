# Banner Product Module — Designer-Style Visual Review v1

Reviewed as a **designer/brand person**, not as engineering diagnostics. Screenshots (Playwright + Chrome, 600px):
`fiche_brand_standard_header.png` (brand_standard_header), `affiche_campaign_poster_header.png` (campaign_poster_header).
Body/layout unchanged — only the banner module is under review.

Scale: **PASS** / **PASS_WITH_NITS** / **FAIL**. Each item has a short critique.

---

## Fiche — brand_standard_header

| # | Criterion | Rating | Critique |
|---|-----------|--------|----------|
| 1 | Brand presence | PASS_WITH_NITS | The CUISTANCE mark anchors the top and the dark plate gives weight, but the plate is a flat rectangle — there is no brand texture, depth, or crafted lockup, so presence is "corporate-clean" rather than "premium". |
| 2 | Logo clarity | PASS | White logo is crisp and centered on the dark plate; good size. |
| 3 | Visual hierarchy | PASS_WITH_NITS | Logo → hairline → uppercase channel/campaign reads cleanly; but the meta is generic small-caps, not a distinctive type treatment. |
| 4 | Spacing / proportion | PASS | Medium height with balanced padding; the header sits well above the serif title without crowding it. |
| 5 | Contrast | PASS | Light logo on dark is strong. (A dark operator logo requires `light_plate`; the mechanism exists.) |
| 6 | Premium / commercial feel | PASS_WITH_NITS (borderline) | Clean and professional, but it does not feel bespoke or premium — it is a well-made template header, not a designed brand banner. |
| 7 | Fit with Fiche body | PASS | Tone matches the editorial serif sheet; does not overpower the product title. |
| 8 | Fit with Affiche poster body | n/a (fiche) | — |
| 9 | Email-native quality | PASS | Email-safe, renders as a real CUISTANCE email. |
| 10 | Still looks like an engineering template? | PARTIALLY YES | It is a polished template header; structurally still "dark plate + logo + uppercase line + red filet". |

**Fiche overall: PASS_WITH_NITS.**

## Affiche — campaign_poster_header

| # | Criterion | Rating | Critique |
|---|-----------|--------|----------|
| 1 | Brand presence | PASS_WITH_NITS | Intentionally lighter so the poster is the hero — correct call — but for the same flat-plate reason it is not distinctive. |
| 2 | Logo clarity | PASS | Smaller logo, still crisp and legible. |
| 3 | Visual hierarchy | PASS | Tighter header → poster body is clearly the focus; good route differentiation from Fiche. |
| 4 | Spacing / proportion | PASS | Shorter/tighter than Fiche; does not steal attention from the generated poster. |
| 5 | Contrast | PASS | Same as Fiche. |
| 6 | Premium / commercial feel | PASS_WITH_NITS | Acceptable framing; not premium for the same flat-plate reason. |
| 7 | Fit with Fiche body | n/a (affiche) | — |
| 8 | Fit with Affiche poster body | PASS | Frames the poster without a second heavy brand block; no double header. |
| 9 | Email-native quality | PASS | Renders as a real campaign email. |
| 10 | Still looks like an engineering template? | PARTIALLY YES | Same structural ceiling. |

**Affiche overall: PASS_WITH_NITS.**

## Gate

```
Fiche banner   : PASS_WITH_NITS  (>= PASS_WITH_NITS) ✓
Affiche banner : PASS_WITH_NITS  (>= PASS_WITH_NITS) ✓
no invisible logo ✓ · no broken logo ✓ · no product/gallery/atmosphere/poster as logo ✓ · no double header ✓ · send path preserved ✓
```

## Final recommendation

**C — Stop engineering polish and request a designer banner / base-lockup draft.**

Honest rationale (not forcing PASS): the route-specific headers are now clean, correct, and route-appropriate
(PASS_WITH_NITS) and are accepted as the **interim first-trial default**. But they still read structurally as
"dark plate + logo + text". The premium gap is a **design-asset gap**, not an engineering gap: the ttt reference's
quality came from a subtle background photo behind the header, which we deliberately avoid (it caused the earlier
PSD header distortion bug). Further deterministic engineering polish on a solid plate will yield diminishing returns.

```
designer_base_recommended = true
interim default            = brand_standard_header (Fiche) / campaign_poster_header (Affiche) — usable now
to reach "premium native"  = a designer-provided banner master / safe brand background treatment + lockup spec
```

A one-more-engineering-polish (option B) is possible but will not close the premium gap; hence **C** over **B**.
