# Productization P1 — Material Input & Email Container Contract v1

Status: **CONTRACT / DESIGN — documentation only. No UI, runtime, schema, or behavior change.**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1` @ `638f4a1`.

This contract is grounded in the **current code** (`app/schemas/poster2.py`, `app/services/email/`, `app/main.py`).
Where a field already exists it is marked **[exists]**; proposed-future naming is marked **[future]**. Nothing here
changes code — it freezes the vocabulary and gates that P2+ will implement.

---

## 1. Current accepted baseline

```
Affiche = campaign_poster_email
Fiche   = product_sheet_email
product_sheet_email = single-product only
real send    = HOLD
multi-product = HOLD
```

`selected_email_body_visual ∈ {affiche, fiche}` drives the fill format via
`FILL_FORMAT_FOR_VISUAL = {affiche: campaign_poster_email, fiche: product_sheet_email}` **[exists]**. A client-asserted
`email_fill_format` that contradicts the selected visual is rejected (`email_fill_format_mismatch`) **[exists]**.

---

## 2. Material input contract

Input groups, mapped to the live schema. "Truth-bearing" = part of business truth that AI/visual assets must never
mutate. All asset refs are **url/key only — inline base64/data URLs are rejected by design** (`WorkbenchAssetRef`) **[exists]**.

| Group | Maps to (code) | Required | Owner/source | Truth-bearing | AI may touch | Validation | Fallback |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `brand_assets` | `EmailBanner.logo/background/pattern/channel_name/campaign_label` **[exists]** | optional | operator | no (presentation) | no | url/key only; ≤80 char meta | header renders ttt_html_header wordmark without logo image |
| `product_truth` | `ProductTruth.product_name/reference/description/parameters[]` **[exists]** | **required** | operator | **YES** | no (copy optimizer is post-sanitized, never alters specs) | name or reference present; `description ≤2000` | none — truth gate blocks |
| `product_assets` | `ProductAssets.product_images[]` (max 2) **[exists]** | **required (≥1)** | operator | **YES (truth asset)** | no | ≥1 url/key image | none — truth gate blocks |
| `gallery_assets` | `ProductAssets.gallery_images[]` (max 3) **[exists]** | optional | operator | supporting visual evidence (not identity truth) | no | url/key only | omitted |
| `atmosphere_assets` | `ProductAssets.atmosphere` (`WorkbenchAtmosphereAsset.is_truth=False`) **[exists]** | optional | operator | **no (visual only)** | yes (Affiche styling only) | url/key only | omitted (Fiche ignores it) |
| `reference_assets` | `source/ttt.html`, `ttt2.html`, `产品海报.psd` **[exists, design shell]** | optional | designer | **no (design shell only)** | no | n/a (not a runtime input) | deterministic ttt_html_header |
| `contact_assets` | footer/contact fields (in `EmailBanner` meta + assembly footer) **[exists]** | optional | operator | yes (contact facts) | no | plain text | static contact line |
| `operator_copy` | subject/preview_text/intro/cta_label (assembly draft) **[exists, derived]** | optional | operator | **no (presentation copy)** | yes (optimizer, deterministic fallback) | sanitized; grounded-claim rejection | deterministic copy from truth |

Mandatory invariants:

```
product_truth is business truth
product images are truth assets
gallery may be supporting visual evidence
atmosphere is visual only, not truth   (enforced: WorkbenchAtmosphereAsset.is_truth = Literal[False])
reference HTML/PSD is design shell only
AI-generated visual is never business truth
```

---

## 3. Email container module contract

Container families:

```
single_product_campaign_email   = Affiche / campaign_poster_email   [exists]
single_product_sheet_email      = Fiche   / product_sheet_email      [exists]
future_multi_product_grid_email                                      [future — requires products[]]
future_catalog_digest_email                                          [future — requires products[]]
```

Modules (the live `EmailBodyPlanModuleKey` set is `email_banner, title_intro, selected_body_visual,
product_description, cta, contact_footer, legal_footer` **[exists]**; `spec_list` is a **[future]** explicit split of
product_description for Fiche):

| Module | Purpose | Req/Opt | Input source | Editable fields | Validation gate | Route |
| --- | --- | --- | --- | --- | --- | --- |
| `email_header` | brand bar (ttt_html_header wordmark + filet + channel meta) | required | `brand_assets` | channel_name, campaign_label | header has no body/product/CTA/footer content | both |
| `title_intro` | headline + intro line | required | `operator_copy` ← truth | subject, intro | non-empty after sanitization | both |
| `selected_body_visual` | the route visual | required | `selected_email_body_visual` slot only | (selection, not content) | route pass conditions §6 | both |
| `product_description` | marketing description | required | `product_truth.description` | intro/description copy | sanitized; no fabricated claims | both |
| `spec_list` **[future]** | structured specs table | optional | `product_truth.parameters[]` | visibility, order | values are truth (read-only) | Fiche (primary) |
| `cta` | call to action | required | `operator_copy` | cta_label, cta_href | label non-empty | both |
| `contact_footer` | contact block | required | `contact_assets` | (facts truth-gated) | plain text | both |
| `legal_footer` | unsubscribe/legal | required | static | none | present | both |

Container is a **600px** email-safe table shell; the selected body visual enters ONLY through the
`selected_body_visual` slot; **no double header** (Affiche body is the no-inner-banner variant) **[exists]**.

---

## 4. Slot naming contract

Stable slot names → current code source:

```
brand.logo                        = EmailBanner.logo                         [exists]
brand.channel_name                = EmailBanner.channel_name                 [exists]
brand.campaign_label              = EmailBanner.campaign_label               [exists]

product.name                      = ProductTruth.product_name                [exists]
product.reference                 = ProductTruth.reference                   [exists]
product.description               = ProductTruth.description                 [exists]
product.parameters[]              = ProductTruth.parameters[] (key/label/value/source/state/locked) [exists]
product.primary_image             = ProductAssets.product_images[0]          [exists]
product.secondary_images[]        = ProductAssets.product_images[1..]        [exists]

visual.affiche.standalone_poster_url   = preview.standalone_poster_url       [exists]
visual.affiche.email_body_visual_url   = preview.email_body_visual_url       [exists]
visual.fiche.product_image_url         = body_visual.url (= product image)   [exists]

email.subject                     = assembly.subject                         [exists]
email.preview_text                = assembly.preview_text                    [exists]
email.intro                       = assembly.intro                           [exists]
email.cta_label                   = assembly.cta_label                       [exists]
email.cta_href                    = assembly.cta_href                         [future field; today static]
email.contact_footer              = assembly contact footer                  [exists]
email.legal_footer                = assembly legal footer                    [exists]
```

Clarifications (must hold):

```
product_images[] means multiple images of ONE product
products[] is required for future multi-product (absence != multi-product)
selected_email_body_visual is the current email body truth
send_attempt is historical only (never the current body source)
```

---

## 5. Operator editability contract

Operator MAY edit (presentation only):

```
subject
preview_text
intro
CTA label
CTA href
product parameter visibility          (which parameters[] rows show)
product parameter order
primary product image selection        (which product_images[] entry is primary)
email fill format — ONLY through selected_email_body_visual (never a free fill-format pick)
```

Operator may NOT edit without truth review (these are `product_truth` / facts):

```
reference
technical specs (values)
thermostat / voltage / power / dimensions
product identity
claims
contact facts
```

Mechanism note: `product.parameters[]` already carries `state ∈ {pending, confirmed}` and `locked`; a `locked` row
must be `confirmed` first, and `parameters_locked` requires all rows confirmed **[exists]**. Spec **values** are truth;
operator editing is limited to **visibility/order**, not values.

Required gates:

```
truth_gate   : product name|reference present AND ≥1 product image  (else generate/preview blocked)
format_gate  : email_fill_format must equal FILL_FORMAT_FOR_VISUAL[selected]  (mismatch rejected)
preview_gate : a backend preview must be generated before send is enabled
send_gate    : explicit confirm + recipients; real send remains HOLD
```

---

## 6. Validation contract

Validation states (lifecycle):

```
draft            → workbench created, truth incomplete
assets_ready     → ≥1 product image + product name|reference present
candidate_ready  → route candidate generated (affiche: poster_key; fiche: status=ready, no poster_key)
selected_for_email → selected_email_body_visual set and GET-confirmed
preview_ready    → backend /email/preview returned a valid package
send_hold        → preview exists; send intentionally held (real send HOLD)
```

Route-specific PASS conditions (all **[exists]** as preview/candidate fields):

**Affiche:**
```
standalone_poster_url exists
email_body_visual_url exists
email_body_visual_url != standalone_poster_url
body_visual_contains_own_banner = false
email_body_visual_contract_pass = true
```

**Fiche:**
```
poster_key = null
uses_poster_generation = false
generated_from = workbench_truth
selected_email_body_visual = fiche
email_fill_format = product_sheet_email
product_sheet_email_contract_pass = true
```

---

## 7. UI implications (future only — NOT implemented here)

```
asset intake panel        — per material group (§2), with url/key validation + truth/visual labelling
truth editor panel        — product_truth + parameters[] (confirm/lock; values truth, not free copy)
candidate mode switch      — affiche / fiche (drives fill format)
email container selector   — container family (single_product_campaign / single_product_sheet today)
module preview             — per-module render of the 600px container
operator edit panel        — presentation-only edits (§5), truth-gated
contract diagnostics panel — surface the §6 pass conditions per route
```

These are descriptions of intent for P2+. No UI is added in P1.

---

## 8. Next implementation recommendation

The contract is sufficient to begin a thin, behavior-light implementation slice next:

```
POSTER2-PRODUCTIZATION-P2-MATERIAL-INPUT-FLEXIBILITY-UI
```

Scope intent for P2 (future task): implement the **asset intake + truth/visual labelling** panel and the §6 contract
diagnostics surface, WITHOUT multi-product, real send, or free-form spec-value editing. If review finds the container
module split (esp. `spec_list` vs `product_description`) still ambiguous, run `POSTER2-PRODUCTIZATION-P1R-CONTRACT-REVIEW`
first.

Recommendation: proceed to **P2** (contract is sufficient); keep `spec_list` as the single open refinement to confirm
during P2 design.

---

## Appendix — Draft contract JSON shapes (documentation only)

```json
{
  "material_input_contract": {
    "brand_assets":     {"required": false, "truth": false, "ai_may_touch": false, "fields": ["logo","background","pattern","channel_name","campaign_label"], "asset_ref": "url_or_key_no_base64"},
    "product_truth":    {"required": true,  "truth": true,  "ai_may_touch": false, "fields": ["product_name","reference","description","parameters[]"]},
    "product_assets":   {"required": true,  "min": 1, "max": 2, "truth": true,  "ai_may_touch": false, "fields": ["product_images[]"]},
    "gallery_assets":   {"required": false, "max": 3, "truth": "supporting_visual", "ai_may_touch": false, "fields": ["gallery_images[]"]},
    "atmosphere_assets":{"required": false, "truth": false, "ai_may_touch": true,  "fields": ["atmosphere"], "is_truth": false},
    "reference_assets": {"required": false, "truth": false, "role": "design_shell_only", "fields": ["ttt.html","ttt2.html","产品海报.psd"]},
    "contact_assets":   {"required": false, "truth": true,  "ai_may_touch": false},
    "operator_copy":    {"required": false, "truth": false, "ai_may_touch": true,  "fields": ["subject","preview_text","intro","cta_label"]}
  },
  "email_container_contract": {
    "families": ["single_product_campaign_email","single_product_sheet_email","future_multi_product_grid_email","future_catalog_digest_email"],
    "width_px": 600,
    "modules": ["email_header","title_intro","selected_body_visual","product_description","spec_list","cta","contact_footer","legal_footer"],
    "body_visual_source": "selected_email_body_visual",
    "no_double_header": true
  },
  "operator_edit_contract": {
    "editable": ["subject","preview_text","intro","cta_label","cta_href","parameter_visibility","parameter_order","primary_product_image_selection","fill_format_via_selected_visual_only"],
    "truth_review_required": ["reference","spec_values","thermostat","voltage","power","dimensions","product_identity","claims","contact_facts"]
  },
  "validation_contract": {
    "states": ["draft","assets_ready","candidate_ready","selected_for_email","preview_ready","send_hold"],
    "gates": ["truth_gate","format_gate","preview_gate","send_gate"],
    "affiche_pass": {"standalone_poster_url": "exists", "email_body_visual_url": "exists != standalone", "body_visual_contains_own_banner": false, "email_body_visual_contract_pass": true},
    "fiche_pass": {"poster_key": null, "uses_poster_generation": false, "generated_from": "workbench_truth", "selected_email_body_visual": "fiche", "email_fill_format": "product_sheet_email", "product_sheet_email_contract_pass": true}
  }
}
```
