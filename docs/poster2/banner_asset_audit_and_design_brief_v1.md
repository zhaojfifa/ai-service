# Banner Asset Audit & Designer Brief v1

Task: **POSTER2-BANNER-ASSET-AUDIT-AND-DESIGN-BRIEF-V1** (audit only — no code/frontend/schema/send change).
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.

Question answered with evidence: **Does `~/poster/ingredient` contain a usable CUISTANCE email banner/header
master?** → **NO.** Full inventory: `assets/banner_asset_audit_v1/asset_inventory.md`. Evidence crops:
`psd_logo_banner_is_technitalia.png`, `cuistance_logo_only.png`.

---

## 1. Asset inventory (summary)

All 7 files present.

```
logo_01.jpg          400x80    CUISTANCE logo lockup (dark wordmark + icon)        -> USABLE_LOGO_ONLY
产品海报.psd          600x1577  Technitalia gas-stove product poster (RGB)          -> DESIGN_REFERENCE_ONLY
  └ layer 'logo banner' (0,0,600,54)  = TECHNITALIA / CODIMATEL banner             -> NOT_USABLE_FOR_BANNER (wrong brand)
ttt.html             22.6KB    Mailchimp CUISTANCE product-sheet (tracking+facts)  -> DESIGN_REFERENCE_ONLY
ttt2.html            114KB     Zoho/Technitalia campaign export                    -> DESIGN_REFERENCE_ONLY
图层示意.png          1868x960  Photoshop screenshot of the design + layers          -> DESIGN_REFERENCE_ONLY
图层细节.png          258x843   Photoshop layers-panel detail screenshot            -> DESIGN_REFERENCE_ONLY
logo banner.png      271x240   Photoshop layers-panel SCREENSHOT (no artwork)       -> NOT_USABLE_FOR_BANNER
```

## 2. Is there a usable banner master? — NO

The PSD **does** contain a structured top header layer (`logo banner`, 600×54, full width) — exactly where a banner
master would live. **But that layer is a TECHNITALIA / CODIMATEL banner, not CUISTANCE** (verified visually:
`psd_logo_banner_is_technitalia.png`). The whole PSD is the original Technitalia template (product "LES RÉCHAUDS GAZ /
XR 144", footer `kaly@tec…` / `01 41 53 12 12`), not a CUISTANCE design.

The only CUISTANCE-branded asset is `logo_01.jpg` — a **logo only** (no background plate, no channel/campaign
placement, no red filet, no dark/light background rule, no fallback, no mobile crop). It is also **dark-on-transparent**,
so on a dark header it must use a light background / the `light_plate` contrast mode.

Therefore: **no usable CUISTANCE banner/header master asset exists** in `~/poster/ingredient`. The PSD/HTML are layout
references only; `logo banner.png` is a UI screenshot; the PSD banner layer is another brand.

## 3. Why existing assets are insufficient

```
- the only 600px banner master (PSD logo banner layer) is the WRONG BRAND (Technitalia/Codimatel)
- logo_01.jpg is a logo, not a banner: no plate, no channel/campaign zone, no filet, no bg rule, no fallback
- logo_01.jpg is dark-on-transparent -> invisible on a dark plate without light_plate / a light background
- ttt/ttt2 HTML give CSS/table grammar only, and carry Mailchimp tracking / other-brand / stale facts (never copy)
- 图层示意/细节/logo banner.png are Photoshop SCREENSHOTS, not exportable artwork
```

## 4. Designer brief (required deliverables)

A CUISTANCE banner/header master must be produced. Two deliverables:

### Deliverable A — Brand Standard Header (Fiche / simple product sheet email)

```
600px email-safe header (table/inline-CSS reconstructable, OR exported PNG/SVG @1x + @2x)
CUISTANCE logo lockup (a LIGHT/white logo variant for dark plate, OR a defined light background)
channel line placement (channel_name)
campaign label placement (campaign_label) — subtle, secondary
red filet rule (#E1002A, 3px, full 600px) position spec
dark background rule + light background rule (which logo variant for each)
no-logo fallback rule (text wordmark)
mobile-safe crop (≤ 600px, no fixed heights that clip on narrow clients)
deliverable form: exportable PNG/SVG (lightweight) OR a CSS/table reconstruction spec with exact paddings/sizes/colors
```

### Deliverable B — Campaign Poster Header (Affiche / target poster email)

```
lighter/shorter campaign header (must NOT compete with the generated poster body — poster is the hero)
CUISTANCE logo lockup (compact)
channel/campaign compact placement (single line)
red filet rule (#E1002A, 3px)
no double-header (the body visual is already the no-inner-banner poster)
mobile-safe crop
deliverable form: exportable PNG/SVG (lightweight) OR a CSS/table reconstruction spec
```

Shared constraints: email-safe (no unsupported CSS), brand logo = CUISTANCE only (never product/gallery/atmosphere/
generated-poster/AI), no Mailchimp tracking / unsubscribe / stale facts, lightweight assets only.

## 5. Recommended final path

```
INTERIM (already shipped): keep the deterministic CSS/table reconstruction —
  Fiche  = brand_standard_header, Affiche = campaign_poster_header (committed at 7e16d66),
  with logo_01.jpg as the logo + light_plate contrast for the dark CUISTANCE logo.
  This is PASS_WITH_NITS / usable for internal testing.

FINAL: REQUEST A DESIGNER BANNER MASTER (Deliverables A + B above).
  The premium gap is a design-asset gap, not an engineering gap. No usable CUISTANCE banner master exists in the
  source assets, so engineering cannot extract one — a designer must provide it.
```

## 6. Proposed follow-up implementation task (NOT executed here)

Only if a real usable banner master is later provided/approved:

```
POSTER2-BANNER-MASTER-WIRE-IN-V1 (proposed; requires Owner authorization + the designer asset):
  - extract a deterministic, lightweight banner asset (PNG/SVG @1x/@2x) OR encode the CSS/table reconstruction spec
  - store the lightweight asset under docs/poster2/assets/ (or the app's static assets) — no heavy files
  - wire as the default banner_source = default_banner_lockup_asset for Brand Standard / Campaign Poster headers
  - preserve the existing fallbacks (uploaded_logo / wordmark_fallback) and contrast modes
  - test Fiche + Affiche previews (banner_variant, no double header, supporting media intact, send path unchanged)
```

This audit does NOT implement it (no usable asset exists yet; and no implementation is authorized in this task).

## 7. Boundaries honored

No app/frontend/schema/send change. No AI images. No email sent. P2A demo untouched. No product facts / Mailchimp
tracking / stale facts extracted. PSD/HTML used as design reference only.
