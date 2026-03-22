# Poster2 Renderer Abstraction

## Objective

Keep `poster2` as the main architecture while allowing two deterministic foreground engines:

- `pillow`
- `puppeteer`

## Selection Model

Request field:

- `renderer_mode`: `auto | pillow | puppeteer`

Current behavior:

- default request value is `auto`
- `auto` resolves to `POSTER2_DEFAULT_RENDERER_MODE` when set
- fallback default is `pillow`
- explicit `puppeteer` degrades to `pillow` if unavailable

## Manifest Fields

The render manifest and HTTP response now expose:

- `renderer_mode`
- `render_engine_used`
- `template_contract_version`
- `foreground_renderer`
- `background_renderer`

## Layering

The pipeline records explicit layer buckets:

- `background_layer_ms`
- `product_material_layer_ms`
- `foreground_structure_layer_ms`
- `text_layer_ms`

The existing `load_and_bg_ms`, `renderer_ms`, `compose_ms`, and `total_ms` remain for compatibility and coarse timing.
