# Marketing Poster Workflow Demo

This repository provides a demonstration workflow for preparing a marketing
poster campaign aimed at kitchen appliances. The process follows three
stages:

1. **Poster input preview** – structure and verify the required assets following
the provided layout guidelines.
2. **Poster generation prompt** – craft a detailed instruction set for the
   "Glibatree Art Designer" image generation tool.
3. **Marketing email draft** – prepare a matching outreach email that references
the generated poster.

## Usage

```bash
python poster_workflow.py
```

The command will create an `output/` directory containing:

- `poster_input_preview.txt` – textual layout preview of the poster inputs.
- `glibatree_prompt.txt` – ready-to-use prompt for the Glibatree Art Designer.
- `marketing_email.txt` – localized marketing email copy.

### Custom configuration

Provide a JSON configuration file to customize the poster materials:

```json
{
  "brand_name": "厨匠ChefCraft",
  "agent_name": "味觉星球营销中心",
  "scenario_image": "现代开放式厨房中智能蒸烤一体机的使用场景",
  "product_name": "ChefCraft 智能蒸烤大师",
  "features": [
    "一键蒸烤联动，精准锁鲜",
    "360° 智能热风循环，均匀受热",
    "高温自清洁腔体，省心维护",
    "Wi-Fi 远程操控，云端菜谱推送"
  ],
  "title": "焕新厨房效率，打造大厨级美味",
  "series_description": "标准款 / 高配款 / 嵌入式款 产品三视图",
  "subtitle": "智能蒸烤 · 家宴轻松掌控",
  "email": "client@example.com"
}
```

Run the workflow with the configuration file:

```bash
python poster_workflow.py --config my_config.json --output custom_output
```

> **Note:** The workflow generates textual prompts and email drafts. Actual image
> rendering with Glibatree Art Designer and real email delivery must be executed
> with external services.
