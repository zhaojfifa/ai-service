# Renderer Routing 与 Fallback 规则 v1

## 1. 文档定位

本文档用于把 poster2 的双引擎设计推进到工程可执行层，明确：

- 何时优先走 Puppeteer
- 何时允许 Pillow fallback
- fallback 后如何判断结果是否仍可交付
- degraded / incomplete_structure 的判定边界

本文档不讨论视觉效果差异，只讨论结构可交付性与引擎路由规则。

---

## 2. 双引擎正式角色

### 2.1 Puppeteer

角色：

- 复杂模板主执行路径
- 更强排版与多 region 协同
- 更强前景结构控制

默认适配：

- Family A：营销讲解型
- Family B：复杂产品图录型 / 长图型

### 2.2 Pillow

角色：

- 稳定 fallback
- 简化模板保底路径
- 在复杂模板执行失败时提供可解释回退

不应被视为：

- 复杂模板的等价替代实现
- 可以无条件吞掉 Puppeteer 失败的默认成功结果

---

## 3. 路由基本原则

### 3.1 路由以模板家族和模板版本为主语义

renderer routing 不应由单次样式或前端临时参数决定，而应由：

- `template_family`
- `template_id`
- `template_version`
- `family_mode`

联合决定。

### 3.2 路由不是“尝试哪个好”，而是“按契约执行哪个”

即：

- 先确定 preferred renderer
- 再判断 fallback 是否允许
- 再判断 fallback 后是否仍满足 family contract

### 3.3 fallback 之后必须再次做结构判定

不能只因为 Pillow 产出了一张图，就视为成功。

必须重新判断：

- mandatory regions 是否还成立
- required slots 是否还存在
- 结构阅读顺序是否仍成立

---

## 4. Family 级默认路由

## 4.1 Family A：营销讲解型

默认：

- `preferred_renderer = puppeteer`
- `fallback_renderer = pillow`

原因：

- Family A 强依赖 header / hero / feature / title band / gallery strip 的多 region 协同
- Puppeteer 更适合表达此类复杂结构

fallback 允许条件：

- Puppeteer timeout
- Puppeteer render exception
- Puppeteer asset composition failure

fallback 后仍可交付的最低要求：

- `header_region` 成立
- `product_region` 成立
- `title_band_region` 成立
- 不允许主产品图区消失
- 不允许 title 漂移到无归属空白区

若上述条件不满足：

- `degraded = true`
- `incomplete_structure = true`
- 不应视为可交付成品

## 4.2 Family B：产品图录型

默认：

- `preferred_renderer = puppeteer`
- `fallback_renderer = pillow`

说明：

- 对于简单短页型 product_sheet，可允许 Pillow 成为 family mode 的 primary renderer
- 但这应由 family mode 显式声明，而不是隐式切换

family mode 示例：

- `product_sheet_simple` → Pillow 可作为 primary
- `product_story_longform` → Puppeteer 必须作为 primary

fallback 后仍可交付的最低要求：

- `brand_banner_region` 成立
- `hero_product_region` 成立
- `spec_region` 或 `copy_region` 至少成立一个核心信息区
- CTA / footer 可折叠，但主产品与核心信息区不可消失

---

## 5. degraded 与 incomplete_structure 语义

## 5.1 `degraded`

定义：

- 原定 preferred path 未成功
- 系统进入替代执行路径
- 但结果可能仍可交付

触发示例：

- Puppeteer timeout，转 Pillow
- Puppeteer region-level render exception，转 Pillow

### `degraded=true` 不自动等于失败

只有在 fallback 后仍满足模板最低交付条件时，才可视为：

- `degraded = true`
- `deliverable = true`

否则：

- `degraded = true`
- `incomplete_structure = true`
- `deliverable = false`

## 5.2 `incomplete_structure`

定义：

- mandatory region 缺失
- required slot 缺失
- 结构阅读顺序被破坏
- fallback 后无法满足家族最低交付结构

触发示例：

- Family A 没有 `product_region`
- Family A title 脱离 `title_band_region`
- Family B 没有 `hero_product_region`
- Family B 的 `spec_region` 与 `copy_region` 同时缺失

---

## 6. 渲染决策流程

建议工程上固定以下决策顺序：

### Step 1. Resolve template family

输入：

- template_family
- template_id
- template_version
- family_mode

输出：

- preferred renderer
- allowed fallback
- minimum deliverable structure

### Step 2. Run preferred renderer

输出：

- render success / failure
- artifact urls
- timing metrics
- raw render status

### Step 3. If preferred renderer fails, evaluate fallback eligibility

检查：

- 当前模板是否允许 fallback
- 当前错误类型是否允许 fallback

若不允许：

- 直接标记失败

### Step 4. Run fallback renderer

输出：

- fallback artifacts
- fallback metrics
- fallback render status

### Step 5. Re-check structure completeness

基于：

- region matrix
- slot contract
- family minimum deliverable rules

输出：

- `structure_complete`
- `missing_mandatory_regions`
- `missing_required_slots`
- `deliverable`

---

## 7. 错误类型与 fallback 建议

### 7.1 允许 fallback 的错误

- Puppeteer timeout
- page navigation timeout
- page content render failure
- browser crash / transient browser exception
- asset load partial failure but template still recoverable

### 7.2 不应自动 fallback 的错误

- 模板协议解析失败
- region contract 不合法
- required slot binding 缺失
- input qualification 未通过
- 主产品图缺失

这些属于“输入或协议级错误”，不是 renderer 级错误。

若此类错误发生，应直接标记：

- `deliverable = false`
- `incomplete_structure = true`

---

## 8. Metadata 最低输出要求

每次渲染至少应输出：

- `template_family`
- `template_id`
- `template_version`
- `family_mode`
- `requested_renderer_mode`
- `render_engine_used`
- `effective_renderer_mode`
- `degraded`
- `fallback_reason_code`
- `incomplete_structure`
- `deliverable`
- `missing_mandatory_regions`
- `missing_required_slots`
- `region_render_status`
- `slot_binding_status`

---

## 9. 当前阶段的工程要求

在真正开动工程前，至少要满足：

- Family A / B 有明确的 preferred renderer 规则
- fallback 后有结构再判定
- degraded 与 incomplete_structure 语义分离
- “出图成功”不再等于“可交付成功”

---

## 10. 一句话结论

> **双引擎路由的核心不是“哪个能出图”，而是“哪个路径能在模板家族契约下产出仍可交付的结果”；fallback 必须重新接受结构完整性审查。**
