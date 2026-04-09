# Family A Fryer Live Diagnosis Micro-Refinement v1

## Scope

- Template A / Family A only
- contract-first
- current 3-column header preserved
- Stage1 / Stage2 UI structure unchanged
- no geometry changes
- no ownership changes
- no Template B work

## Live diagnosis honored

The latest fryer live result showed four bounded gaps:

- right-column header text still carried old service-center semantics
- subtitle could remain empty/collapsed through the bottom request path
- product-owned annotation cards still felt cramped for short commercial benefit phrases
- dense-quad bottom strip still read as a crowded repeated row

## Minimal repair strategy

### 1. Header semantic carry-through

Keep `header_mode = identity_left_agent_right` and the 3-column structure unchanged.

Only normalize the Family A fryer path so generic service-center placeholders do not survive into the live render.  
The right column now carries:

- `Commercial Electric Fryer Series`

### 2. Subtitle default carry-through

Keep `bottom_mode = title_gallery_split` and bottom ownership unchanged.

The Family A fryer path now treats blank bottom-contract subtitle state as incomplete, not intentional canonical empty state, and rehydrates it from the fryer default:

- `Fast heating, precise control, and durable stainless steel construction for everyday commercial use.`

### 3. Product annotation shell micro-expansion

Keep:

- 3 fixed product-owned annotation slots
- fixed anchors
- product ownership in `product_region`

The bounded repair is not a free relayout.  
It aligns structured HTML consumption with the current fixed-slot contract:

- annotation anchor map slots 1-3 now use `176x76`
- structured HTML now preserves the fixed product-anchor positions for `product_anchor_callouts`

### 4. Bottom strip semantic breathing

Keep:

- 4-item strip
- `title_gallery_split`
- gallery ownership

Only the dense-quad item distribution was relaxed:

- item width `196 -> 188`
- gap `16 -> 20`
- frame padding for dense quad now allows visible outer breathing

This keeps the same region and shell, but makes the row read less like a compressed repeated strip.

## Runtime evidence target

For the current fryer sample, the expected Family A truth after this repair is:

- `header_mode = identity_left_agent_right`
- `requested_agent_text = Commercial Electric Fryer Series`
- `subtitle_slot.state = rendered`
- `product_annotation_owner = product_region`
- annotation slot bounds remain fixed and traceable
- `gallery_distribution_policy = dense_quad`
- dense-quad item layouts use the relaxed Family A spacing
