# 模板家族 Slot Contract 基线 v1

## 1. 文档定位

本文档在 `template_family_region_matrix_v1.md` 的基础上，继续把两类模板家族推进到工程可执行层。

本文档的目标不是描述视觉样式，而是锁定：

- 每个 region 内有哪些 slot
- 哪些 slot 为 required
- 哪些 slot 为 optional
- 哪些 slot 可 collapse
- slot 的输入来源、数量规则与失效语义

本文档的作用是把模板从“区域级结构”推进到“槽位级协议”。

---

## 2. 共同原则

### 2.1 Slot 不是自由元素，而是受约束的协议对象

每个 slot 必须明确：

- `slot_id`
- `source_binding`
- `required / optional`
- `count`
- `collapse_rule`
- `fallback_rule`
- `failure_semantics`

### 2.2 required slot 缺失不能静默吞掉

如果 required slot 没有可用内容，系统必须：

- 标记 slot 缺失
- 触发 region 级失败或家族级降级
- 在 metadata 中可解释输出

### 2.3 optional slot 只能按规则折叠

optional slot 可折叠，但必须满足：

- 没有可绑定内容
- 或当前 family mode 明确关闭
- 且折叠后不破坏 reading order

### 2.4 一个 slot 只绑定一种主语义

例如：

- `title_slot` 只绑定标题
- `reference_slot` 只绑定型号 / 参考号
- `feature_item_slot` 只绑定 feature items

不允许多个业务语义混绑到同一个 slot 中做临时补位。

### 2.5 先锁 slot，再谈布局行为

slot contract 解决“放什么、能不能缺、缺了怎么办”；
布局控制解决“怎么放得更稳”。

---

## 3. 共同 Slot 类型

poster2 统一使用以下 slot 类型语法：

- `brand_logo_slot`
- `brand_text_slot`
- `agent_pill_slot`
- `scenario_image_slot`
- `product_image_slot`
- `supporting_image_slot`
- `title_slot`
- `subtitle_slot`
- `feature_item_slot[]`
- `gallery_item_slot[]`
- `reference_slot`
- `spec_item_slot[]`
- `copy_slot`
- `cta_slot`
- `footer_brand_slot`

---

## 4. 模板家族 A：营销讲解型（Campaign Explainer）

## 4.1 `header_region` slot contract

### A.header.brand_logo_slot

- 类型：image
- 来源：`brand_logo`
- 状态：required-or-fallback
- 规则：
  - 与 `brand_text_slot` 至少有一个成立
  - 若 logo 缺失，允许退化为 `brand_text_slot` 单独成立
- 失效语义：
  - 若 logo 与品牌文字同时缺失，则 `header_region` 失败

### A.header.brand_text_slot

- 类型：text
- 来源：`brand_name`
- 状态：required-or-fallback
- 规则：
  - 与 `brand_logo_slot` 至少有一个成立
  - 文本允许截断，但不允许为空时静默丢失
- 失效语义：
  - 若与 `brand_logo_slot` 同时缺失，则 `header_region` 失败

### A.header.agent_pill_slot

- 类型：text / badge
- 来源：`agent_name` / `channel_name`
- 状态：optional
- 规则：
  - 可折叠
  - 不允许反向挤压 `brand_logo_slot` 与 `brand_text_slot`
- 折叠语义：
  - 记录 `agent_pill_slot.collapsed = true`

---

## 4.2 `product_region` slot contract

### A.product.product_image_slot

- 类型：image
- 来源：`product_image`
- 状态：required
- 规则：
  - count = 1
  - 不允许变形
  - 不允许被 supporting image 替代
- 失效语义：
  - 缺失即 `product_region` 失败

---

## 4.3 `scenario_region` slot contract

### A.scenario.scenario_image_slot

- 类型：image
- 来源：`scenario_image`
- 状态：optional / preferred
- 规则：
  - count = 1
  - 缺失时允许 region 折叠
- 折叠语义：
  - `scenario_region.collapsed = true`
  - hero wrapper 保持成立

---

## 4.4 `feature_region` slot contract

### A.feature.feature_item_slot[]

- 类型：text + connector
- 来源：`features[]`
- 状态：optional array
- 规则：
  - count_valid ∈ [0, 3] 作为 v1 基线
  - 实际渲染数量 = 有效 feature 数量
  - 未使用 slot 必须完全 collapse
  - connector 只为已渲染 slot 存在
- 失效语义：
  - `features=[]` 时 region 折叠，不判模板失败
  - 出现 ghost connector / ghost box 记为 structure violation

---

## 4.5 `title_band_region` slot contract

### A.title.title_slot

- 类型：text
- 来源：`title`
- 状态：required
- 规则：
  - count = 1
  - 不允许折叠
  - 允许后续通过 layout control 处理换行 / 截断 / 缩放
- 失效语义：
  - 缺失即 `title_band_region` 失败

### A.title.subtitle_slot

- 类型：text
- 来源：`subtitle`
- 状态：optional
- 规则：
  - count = 0..1
  - 可折叠
- 折叠语义：
  - title 仍然必须成立

---

## 4.6 `gallery_strip_region` slot contract

### A.gallery.gallery_item_slot[]

- 类型：image
- 来源：`gallery_images[]`
- 状态：optional array
- 规则：
  - count_valid ∈ [0, 4] 作为 v1 基线
  - 若数量为 0，则整个 region 可折叠
  - 若数量 > 0，则只渲染有效数量，不允许用空壳补足
- 失效语义：
  - 无图可折叠，不判失败
  - 图条存在但图片为空，记为 slot violation

---

## 4.7 Family A slot 成功标准

Family A 结构成立，至少要求以下 required slot 成立：

- `brand_logo_slot` 或 `brand_text_slot`
- `product_image_slot`
- `title_slot`

以下 slot 允许折叠：

- `agent_pill_slot`
- `scenario_image_slot`
- `feature_item_slot[]`
- `subtitle_slot`
- `gallery_item_slot[]`

---

## 5. 模板家族 B：产品图录型（Product Sheet / Product Story）

## 5.1 `brand_banner_region` slot contract

### B.brand.brand_logo_slot

- 类型：image
- 来源：`brand_logo` / `brand_banner_asset`
- 状态：required-or-fallback
- 规则：
  - 与 `footer_brand_slot` 不互为替代
  - 顶部品牌锚点必须存在
- 失效语义：
  - 缺失时 `brand_banner_region` 失败

---

## 5.2 `reference_region` slot contract

### B.reference.reference_slot

- 类型：text
- 来源：`reference_code` / `model_code`
- 状态：optional / preferred
- 规则：
  - count = 0..1
  - 缺失时允许 region 折叠
- 折叠语义：
  - 不影响主产品区与正文区的 reading order

---

## 5.3 `hero_product_region` slot contract

### B.hero.product_image_slot

- 类型：image
- 来源：`product_image`
- 状态：required
- 规则：
  - count = 1
  - 不允许变形
  - 不允许被配件图 / supporting image 替代
- 失效语义：
  - 缺失即 family B 失败

### B.hero.supporting_image_slot[]

- 类型：image
- 来源：`supporting_images[]`
- 状态：optional array
- 规则：
  - count_valid ∈ [0, 8] 作为 v1 基线
  - 仅作为辅图，不可上升为主图
- 折叠语义：
  - supporting images 缺失时不影响主图区成立

---

## 5.4 `spec_region` slot contract

### B.spec.spec_item_slot[]

- 类型：structured text
- 来源：`spec_items[]`
- 状态：conditional required
- 规则：
  - 若 family mode = `product_sheet`，则至少需要 1 个有效 spec item
  - 若 family mode = `product_story`，允许由 `copy_slot` 承担主信息表达
- 失效语义：
  - product_sheet 模式下 spec 全缺失，则核心信息区失败

---

## 5.5 `copy_region` slot contract

### B.copy.title_slot

- 类型：text
- 来源：`title`
- 状态：conditional required
- 规则：
  - 在 product_story 模式下为 required
  - 在 product_sheet 模式下可弱化，但若存在需保持固定语义

### B.copy.copy_slot

- 类型：text block
- 来源：`body_copy` / `description`
- 状态：conditional required
- 规则：
  - 在 product_story 模式下为 required
  - 在纯参数型 product_sheet 模式下可折叠
- 失效语义：
  - 若 product_story 模式下 title 与 copy 同时缺失，则信息区失败

---

## 5.6 `cta_region` slot contract

### B.cta.cta_slot

- 类型：button / text block
- 来源：`cta_text` / `contact_info`
- 状态：optional
- 规则：
  - 若存在，则 count = 1
  - 若缺失，可折叠
- 折叠语义：
  - 不允许导致 footer 无解释上移抢位

---

## 5.7 `footer_brand_region` slot contract

### B.footer.footer_brand_slot

- 类型：image / text block
- 来源：`brand_footer_asset` / `brand_name`
- 状态：optional / preferred
- 规则：
  - 用于纵向长图的品牌收束
  - 在短页模式下可折叠
- 折叠语义：
  - 页面末端仍需保持正常收束感

---

## 5.8 Family B slot 成功标准

Family B 结构成立，至少要求以下 required slot 成立：

- `brand_logo_slot`
- `product_image_slot`
- `spec_item_slot[]` 或 `copy_slot` 至少形成一个核心信息区

以下 slot 允许折叠：

- `reference_slot`
- `supporting_image_slot[]`
- `cta_slot`
- `footer_brand_slot`

---

## 6. 工程侧直接转化对象

本文档应直接转化为以下工程对象：

### 6.1 Slot Presence Check

输出：

- `required_slots_present`
- `missing_required_slots`
- `collapsed_optional_slots`
- `slot_violation_reasons`

### 6.2 Slot Binding Report

输出：

- 每个 slot 绑定到了什么 source
- 是否 rendered
- 是否 collapsed
- count_valid / count_requested

### 6.3 Slot-aware Fallback Gate

fallback 时必须额外判断：

- fallback renderer 是否还能满足 required slots
- 若不能满足，则标记 `incomplete_structure`

---

## 7. 一句话结论

> **Region Matrix 锁定的是“哪些区域必须存在”，Slot Contract 锁定的是“每个区域里到底放什么、缺了怎么办”，两者结合后，模板家族才真正进入工程可执行状态。**
