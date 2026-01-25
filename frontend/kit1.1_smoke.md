# KitPoster1.1 Smoke Checks

## Valid request (minimal)
```bash
curl -s -X POST "$BASE/api/generate-poster" \
  -H "Content-Type: application/json" \
  -d '{
    "render_mode": "kitposter1_a",
    "poster": {
      "brand_name": "Acme",
      "agent_name": "Channel",
      "scenario_image": "default",
      "product_name": "Widget",
      "features": ["Fast", "Quiet", "Compact"],
      "title": "Acme Widget",
      "subtitle": "Spring Drop",
      "series_description": "Series A",
      "product_image_1": "r2://bucket/path/product.png"
    }
  }'
```

## Invalid request (no product images -> 422)
```bash
curl -s -X POST "$BASE/api/generate-poster" \
  -H "Content-Type: application/json" \
  -d '{
    "render_mode": "kitposter1_a",
    "poster": {
      "brand_name": "Acme",
      "agent_name": "Channel",
      "scenario_image": "default",
      "product_name": "Widget",
      "features": ["Fast", "Quiet", "Compact"],
      "title": "Acme Widget",
      "subtitle": "Spring Drop",
      "series_description": "Series A"
    }
  }'
```

## Draft validation example (KitPoster1.1)
```bash
curl -s -X POST "$BASE/api/generate-poster" \
  -H "Content-Type: application/json" \
  -d '{
    "render_mode": "kitposter1_a",
    "draft": {
      "template_id": "template_dual",
      "variant": "a",
      "product_images": ["r2://bucket/path/product.png"],
      "copy": {
        "title": "Acme Widget",
        "bullets": ["Fast", "Quiet", "Compact"],
        "tagline": "Spring Drop"
      },
      "options": {
        "quality_mode": "stable",
        "allow_auto_fill": true
      }
    },
    "poster": {
      "brand_name": "Acme",
      "agent_name": "Channel",
      "scenario_image": "default",
      "product_name": "Widget",
      "features": ["Fast", "Quiet", "Compact"],
      "title": "Acme Widget",
      "subtitle": "Spring Drop",
      "series_description": "Series A",
      "product_image_1": "r2://bucket/path/product.png"
    }
  }'
```
