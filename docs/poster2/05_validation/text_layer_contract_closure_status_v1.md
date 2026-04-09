# Text Layer Contract Closure Status v1

**PR:** PR-4
**Date:** 2026-03-30
**Status:** Complete

---

## Goal

Freeze text ownership and feature delegation so that:

- Each text layer has a declared, immutable `owner_region` coming from a constant, not inlined as a string literal.
- Product annotation text is owned exclusively by `product_region`; slot IDs are frozen.
- When `product_annotation_mode = product_anchor_callouts`, `feature_region` becomes a delegated diagnostic view only — not a rendered owner.
- No dual ownership: a text slot cannot be claimed by two regions simultaneously.
- No duplicate rendered evidence chains across `feature_contract_review` and `product_annotation_contract_review`.

---

## What Changed

### `app/services/poster2/template_behavior.py`

New constants:

```python
_TEXT_LAYER_OWNER_MAP: dict[str, str] = {
    "header_text_layer": "header_region",
    "title_text_layer": "title_band_region",
    "subtitle_text_layer": "title_band_region",
}

_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS: tuple[str, ...] = (
    "product_annotation_slot_1",
    "product_annotation_slot_2",
    "product_annotation_slot_3",
)

_PRODUCT_ANNOTATION_TEXT_OWNER_REGION = "product_region"
```

### `app/services/poster2/pipeline.py`

- Imports expanded: `_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS`, `_PRODUCT_ANNOTATION_TEXT_OWNER_REGION`, `_TEXT_LAYER_OWNER_MAP`.
- Dead code removed: the older no-`template` copies of `_build_title_text_layer_evidence`, `_build_subtitle_text_layer_evidence`, `_build_header_text_layer_evidence` (superseded by the full versions that take `template` as a positional arg).
- `_build_title_text_layer_evidence()`: `owner_region` now reads from `_TEXT_LAYER_OWNER_MAP["title_text_layer"]`; new field `ownership_frozen = True`.
- `_build_subtitle_text_layer_evidence()`: same pattern for `"subtitle_text_layer"`.
- `_build_header_text_layer_evidence()`: same pattern for `"header_text_layer"`.
- `_build_feature_contract_review()`: new field `feature_view_mode`:
  - `"delegated_diagnostic"` when `product_annotation_mode = product_anchor_callouts`
  - `"owner"` otherwise
- `_build_product_annotation_contract_review()`: three new fields on the active branch:
  - `annotation_text_owner_region = _PRODUCT_ANNOTATION_TEXT_OWNER_REGION` (`"product_region"`)
  - `annotation_slot_ids = list(_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS)` (the 3 slot IDs)
  - `ownership_frozen = True`

---

## Frozen Owner Surfaces

### Text layers

| layer_id | owner_region |
|---|---|
| `header_text_layer` | `header_region` |
| `title_text_layer` | `title_band_region` |
| `subtitle_text_layer` | `title_band_region` |

### Product annotation slots

| slot_id | owner_region |
|---|---|
| `product_annotation_slot_1` | `product_region` |
| `product_annotation_slot_2` | `product_region` |
| `product_annotation_slot_3` | `product_region` |

---

## Feature Delegation Rules

When `product_annotation_mode = product_anchor_callouts`:

- `feature_contract_review.feature_view_mode = "delegated_diagnostic"`
- `feature_contract_review.feature_region.visible_item_count = 0`
- `feature_contract_review.rendered_feature_items = []`
- `feature_contract_review.responsibility_owner = "product_region"`
- `product_annotation_contract_review` is the sole rendered evidence chain
- `product_annotation_contract_review.annotation_text_owner_region = "product_region"`
- No dual ownership: `feature_region` carries diagnostic metadata only; it does not claim rendered text.

When `product_annotation_mode = none` (or any non-callout mode):

- `feature_contract_review.feature_view_mode = "owner"`
- `feature_region` is the rendered owner of feature callout text.

---

## Tests (`tests/poster2/test_pipeline.py`)

New class: `TestTextOwnershipFreeze` (10 tests):

| Test | What it validates |
|---|---|
| `test_text_layer_owner_map_constant_shape` | `_TEXT_LAYER_OWNER_MAP` has correct 3-entry shape |
| `test_frozen_annotation_slot_ids_constant` | `_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS` is tuple of exactly 3 IDs |
| `test_product_annotation_text_owner_region_constant` | `_PRODUCT_ANNOTATION_TEXT_OWNER_REGION == "product_region"` |
| `test_title_text_layer_ownership_frozen` | `owner_region == "title_band_region"` and `ownership_frozen = True` in evidence |
| `test_subtitle_text_layer_ownership_frozen` | `owner_region == "title_band_region"` and `ownership_frozen = True` in evidence |
| `test_header_text_layer_ownership_frozen` | `owner_region == "header_region"` and `ownership_frozen = True` in evidence |
| `test_feature_view_mode_is_delegated_diagnostic_when_annotation_active` | `feature_view_mode = "delegated_diagnostic"` + `visible_item_count = 0` |
| `test_feature_view_mode_is_owner_when_annotation_not_active` | `feature_view_mode = "owner"` when non-callout mode |
| `test_no_dual_ownership_when_annotation_active` | No dual evidence chain; `feature_region` carries zero rendered items |
| `test_annotation_contract_review_emits_frozen_slot_ids` | `annotation_slot_ids`, `annotation_text_owner_region`, `ownership_frozen` in review |

---

## Acceptance

- `_TEXT_LAYER_OWNER_MAP` declared in `template_behavior.py` with 3 entries ✓
- `_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS` is a tuple of exactly `("product_annotation_slot_1", "product_annotation_slot_2", "product_annotation_slot_3")` ✓
- `_PRODUCT_ANNOTATION_TEXT_OWNER_REGION = "product_region"` ✓
- All three text layers emit `ownership_frozen = True` in pipeline evidence ✓
- `owner_region` values come from `_TEXT_LAYER_OWNER_MAP` constants, not string literals ✓
- `feature_view_mode = "delegated_diagnostic"` when annotation active ✓
- `feature_region.visible_item_count = 0` when annotation active ✓
- No duplicate rendered evidence chains ✓
- `product_annotation_contract_review` emits `annotation_text_owner_region`, `annotation_slot_ids`, `ownership_frozen` ✓
- Dead code (no-`template` builder copies) removed ✓
- 252/252 tests pass (242 prior + 10 new) ✓

---

## Open Follow-ups

- `header_region` `identity_zone_mode` resolver wiring still pending
- Pillow secondary slot rendering parity (contract-only for now)
- Puppeteer text layer evidence parity (Pillow-only for now)
- Stage 2 frontend: `ownership_frozen` / `feature_view_mode` not yet surfaced in diagnostics panel (low priority)
