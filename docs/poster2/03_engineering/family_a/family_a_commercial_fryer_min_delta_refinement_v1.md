# Family A Commercial Fryer Minimal-Delta Refinement v1

## Scope

- Template A / Family A only
- contract-first
- no geometry changes
- no ownership changes
- no Template B work
- keep current 3-column header
- keep current Stage1 / Stage2 overall layout and operator workflow

## Rollback anchor

- pre-change rollback tag:
  - `Poster2-FamilyA-MinDelta-PreCommercialRefine`
  - sha: `cdb3216cbb1b95630c9afbb27a9ada9c90af37a7`

## Objective

Improve the commercial electric fryer sample with the smallest possible delta:

- English copy defaults in the existing input flow
- cleaner product callout reading inside the fixed product-owned annotation path
- less repetitive bottom gallery semantics using existing assets only
- restrained Family A token adjustment toward a neutral commercial product language

## Default English copy

### Header

- `brand_name`: `ChefCraft`
- `agent_name`: `Commercial Electric Fryer Series`

### Product callouts

- `Fast Heat-Up`
- `Precise Thermostat Control`
- `Stainless Steel Body`

### Bottom copy

- title: `Power Up Your Fry Station`
- subtitle: `Fast heating, precise control, and durable stainless steel construction for everyday commercial use.`

### Bottom gallery semantic order

- `Single Tank`
- `Dual Tank`
- `Lid Detail`
- `Basket Detail`

## Minimal contract / control delta

No geometry or ownership change was introduced.

The only bounded Family A request/consumption delta is:

- Mode S / Template A default text now falls back to the commercial fryer English defaults when the operator leaves the existing fields blank
- bottom gallery semantic captions are seeded even when image assets are sparse
- Family A poster2 gallery fallback now prefers available product assets before brand-logo fallback:
  - slot 1: primary product
  - slot 2: secondary product if available, otherwise primary
  - slot 3: secondary detail if available, otherwise primary
  - slot 4: primary or secondary, then logo only as last resort

## Minimal beauty-token delta

The Family A frozen pack remains `campaign_frozen_panel`, but its values are tightened toward:

- cleaner light neutral shell surfaces
- restrained cool gray support tones
- fryer-panel-aligned red accent

No new layout system or restyle track was opened.
