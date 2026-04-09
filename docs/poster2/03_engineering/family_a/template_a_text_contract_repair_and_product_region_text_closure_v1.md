# Template A Text Contract Repair And Product-Region Text Closure v1

## Scope

Template A only.

This pass closes the text lifecycle gap without changing:

- geometry
- ownership
- annotation anchors
- Template B behavior or UI

## Problem

Template A product-region and bottom text quality was limited by text lifecycle drift:

1. annotation sanitization was destructive
2. accepted optimization did not always drive final rendered text
3. subtitle cleanup / fit handling happened too late or not at all
4. UI lineage was shorter than the actual backend text path

## Contract Decisions

### 1. Sanitization is hygiene-only

For Template A annotation inputs, `sanitized_text` is now restricted to hygiene:

- trim
- whitespace normalization
- punctuation normalization
- invalid-character cleanup

It must not remove semantic content.

### 2. Fit rewrite is explicit

Template A fixed annotation slots and subtitle now expose:

- `fit_rewrite_text`
- `fit_rewrite_applied`
- `fit_rewrite_reason`

Fit rewrite is only used when the slot budget requires it.

### 3. Render source is explicit

Each Family A text surface can now expose:

- `requested_text`
- `sanitized_text`
- `cleanup_text`
- `fit_rewrite_text`
- `optimized_text`
- `accepted_text`
- `rendered_text`
- `rendered_text_source`

### 4. Renderer still executes truth

Renderer behavior does not define text truth.
The selected final candidate is decided before render and then consumed by the renderer.

## Family A Notes

### Annotation

- product annotation owner remains `product_region`
- 3 fixed slots remain frozen
- fit rewrite improves budget fit without changing slot count or slot identity

### Subtitle

- cleanup removes noisy tails and punctuation artifacts before fit handling
- fit rewrite reduces fragment-style truncation in the current Family A practical sample

### Optimization

- optimization remains limited to `title / subtitle / annotation`
- accepted optimization can now become the actual rendered candidate
- optimization may not change mode, ownership, geometry, or control truth

## UI Consumption

Stage2 continues to keep copy optimization secondary to the main workflow, but the lineage view now reflects the actual backend chain instead of a shortened `sanitized -> rendered` path.
