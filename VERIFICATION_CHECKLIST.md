# Verification Checklist

## 1) Expected startup log when edit is enabled

Look for a line from [vertex_imagen3.py](/Users/tylerzhao/Code/ai-service/app/services/vertex_imagen3.py) similar to:

- `[vertex3.model] project=<...> location=<...> generate_model=<...> edit_model=<...> enabled=True reason=None ...`

And a line from [main.py](/Users/tylerzhao/Code/ai-service/app/main.py) with runtime summary:

- `Runtime configuration resolved` containing:
  - `vertex.project`
  - `vertex.location`
  - `vertex.generate_model`
  - `vertex.edit_model`
  - `vertex.edit_enabled=true`
  - `storage.backend`

## 2) Expected startup log when edit is disabled

Typical disabled-by-flag:

- `[vertex3.model] ... enabled=False reason=flag_not_enabled ...`

Typical disabled-by-model-load-failure:

- warning line:
  - `[vertex3.model] edit disabled: failed to load edit model '<name>': <error>`
- model summary line:
  - `enabled=False reason=edit_model_load_failed:<ExceptionType>`

## 3) API response differences: edit path vs fallback path

Edit path healthy (target):

- `POST /api/generate-poster` response:
  - `status=success`
  - `degraded` expected `false` (or absent/false depending payload path)
  - warnings should not include:
    - `vertex_edit_failed_fallback`
    - `kitposter1_locked_frame_fallback`

Fallback path (current degraded signature):

- `status=success`
- `degraded=true`
- warnings include one or more:
  - `vertex_edit_failed_fallback`
  - `kitposter1_locked_frame_fallback`
  - possibly `scenario_fallback_used` depending draft path

## 4) Exact manual/curl test steps

Set base URL:

```bash
BASE="https://<your-render-service>.onrender.com"
```

Health checks:

```bash
curl -i "$BASE/health"
curl -i "$BASE/healthz"
```

Minimal kitposter generation check (replace object refs with real uploaded assets):

```bash
curl -s "$BASE/api/generate-poster" \
  -H "Content-Type: application/json" \
  -d '{
    "poster": {
      "brand_name": "ChefCraft",
      "agent_name": "Channel A",
      "scenario_image": "default",
      "product_name": "Smart Oven",
      "template_id": "template_dual",
      "features": ["f1","f2","f3"],
      "title": "Title",
      "series_description": "Series",
      "subtitle": "Subtitle",
      "scenario_asset": "https://<cdn>/scenario.png",
      "scenario_key": "uploads/scenario.png",
      "product_asset": "https://<cdn>/product.png",
      "product_key": "uploads/product.png",
      "gallery_items": [
        {"asset":"https://<cdn>/g1.png","key":"uploads/g1.png","mode":"upload"}
      ]
    },
    "render_mode": "kitposter1_a",
    "variants": 1,
    "seed": 0,
    "lock_seed": true
  }' | jq
```

Inspect response fields:

- `warnings`
- `degraded`
- `degraded_reason`
- `fallback_used`
- `poster_url` / `poster_key`

Operational check in Render logs for same request:

- confirm `[vertex] generate_poster start`
- confirm `[vertex3.model] ... enabled=True ...` at startup
- confirm absence of fallback warnings in request log path when edit works
