# 当前阶段判断与工程路径修订 v1

## 0. 文档锚点说明

本文档的阶段判断服从已恢复的顶层产品基线 [poster_generation_product_design_baseline_v1.md](poster_generation_product_design_baseline_v1.md)。

也就是说：

- 产品治理口径仍是 `Structure -> Control -> Beautification`
- 模板执行口径仍是 `Background -> Shell -> Content`

本文档只负责给出当前阶段判断，不重写这些基线。

## 1. 结论

当前 `poster2` 的**架构目标与基本路线是正确的**，这一点已经通过本轮工程验证成立。

已经被验证成立的部分包括：

- 结构 contract 可以守住
- 内容注入可以受控
- 结果可以复现
- diagnostics / deliverable / structure 语义已经成立
- `template_dual_v2` 的五大 region（header / scenario / product / feature / bottom）已经具备可用的稳定性基线

但与此同时，也已经明确：

> 当前问题不在于架构方向错误，而在于 **工程路径与实施技术仍需优化**。

换句话说：

- **架构目标正确**
- **基本路线正确**
- **工程实现方式还不够成熟**

---

## 2. 已经证明了什么

当前阶段已经证明：

### 2.1 结构可以控制

海报已经不再是“自由拼贴”，而是由 region / slot / shell / content 共同约束的结构化模板。

### 2.2 内容可以控制

logo、brand、agent、title、scenario、product、gallery 等关键输入，已经不再是自由排版，而是在模板 contract 范围内注入。

### 2.3 结果可以复现与审查

当前系统已经具有：

- template / version / renderer 信息
- degraded / fallback 语义
- structure / deliverable 语义
- region / slot 级状态输出

这意味着 poster2 已经从“能跑通”进入“可审查、可复盘”的阶段。

---

## 3. 还没有证明什么

当前仍未充分证明以下两件更难的事：

### 3.1 模板真正可驱动

当前很多行为仍然分散在：

- template JSON
- slot spec
- CSS
- Python renderer 条件逻辑

这意味着：

- 结构是可控的
- 但模板行为还没有真正上浮成统一的行为层

当前更像“半声明式模板”，而不是“模板协议真正驱动结果”。

### 3.2 结果可稳定美化

当前已证明结构可控，但尚未证明：

- 在不破坏 structure contract 的前提下
- 能通过独立的 Beautification Layer
- 稳定地产出更成熟、更优雅的结果

---

## 4. 当前阶段的真实判断

可以正式定义为：

> 我们已经证明了“可控生成架构”成立，但还没有证明“模板驱动能力”和“结果美化能力”已经成熟。

因此，下一阶段不应继续被定义为“基础稳定化”，而应转入：

- Template Behavior Layer
- Beautification Pathfinding
- Geometry / Evidence Layer
- Render Service Layer

的逐步补强。

---

## 5. 为什么说工程路径和实施技术还要优化

### 5.1 当前工程仍偏 template-specific tuning

虽然结构已经守住，但很多行为仍靠：

- 单模板 CSS 调整
- 单模板 renderer 条件分支
- 局部 token / layout 修补

这说明工程还停留在：

> “把一个模板做稳”

而没有完全进入：

> “让模板协议自己驱动行为”

### 5.2 渲染服务层还不够独立

当前 Puppeteer 已经发挥作用，但它仍更像嵌入式 renderer，而不是成熟的 Render Service Layer。

后续仍需补足：

- browser lifecycle policy
- page reuse / page pool
- request filtering
- wait strategy
- artifact policy

### 5.3 几何证据层还不够强

当前已有：

- structure_evidence_source
- structure_evidence_complete
- region_render_status
- slot_binding_status

但后续仍建议补足：

- region_bounds
- slot_bounds
- visible_bounds
- overflow_state
- clipping_state
- visible_item_count

让“结构守住了”从肉眼判断，升级为几何可证明。

---

## 6. 下一阶段应如何定义

### 6.1 阶段名称建议

建议将下一阶段明确命名为：

## `Template Behavior Layer + Beautification Pathfinding`

### 6.2 阶段目标

下一阶段的目标不是继续“修这个模板”，而是：

1. 证明模板行为能由协议驱动
2. 证明结果可以在不破坏 contract 的前提下开始变美
3. 补足 Geometry / Evidence Layer
4. 补足 Render Service Layer

---

## 7. 下一阶段最小实施顺序

### 第一步：证明模板行为可驱动

仅在 `template_dual_v2` 上选择 1~2 个行为维度上浮为 template behavior modes。

优先建议：

- `hero_mode`
- `feature_mode`

要求：

- 可见结果尽量不变
- diagnostics 不变
- 只证明行为可由模板协议驱动

当前工程线已完成的最小落地点：

- `hero_mode` 已进入 template metadata
- `feature_mode` 已进入 template metadata
- renderer 通过统一 resolver 消费已解析 hero policy
- renderer 通过统一 resolver 消费已解析 feature policy
- 当前基线 `scenario_cover_product_contain` 被保留
- 第二个 hero mode 已存在，用于证明 hero 行为不是 renderer 内部硬编码
- 第二个 feature mode 已存在，用于证明 feature 布局策略不是 CSS/Python 分散硬编码

当前仍未完成的部分：

- header / product / gallery strip 的 geometry evidence 强化

当前已完成但应明确边界的部分：

- Pillow 已开始消费与 Puppeteer 相同的 beauty token families
- 该对齐目标是 semantic parity，不是 exact pixel parity
- metadata 已开始输出最小 geometry evidence：
  - `region_bounds`
  - `slot_bounds`
  - `visible_item_count`

### 第二步：引入最小 Beautification Layer

新增最小 beauty tokens，例如：

- `shell_surface`
- `shell_border`
- `shell_shadow`
- `accent_tone`
- `text_emphasis`

只作用于现有 shell，不改变 geometry，不取代 behavior layer。

### 第三步：补最小 Geometry / Evidence Layer

先从最关键区域开始：

- header
- product
- gallery strip

新增：

- `region_bounds`
- `slot_bounds`
- `visible_item_count`

### 第四步：补 Render Service Layer

逐步把 Puppeteer 路径硬化为可治理的 runtime service。

---

## 8. 当前应更新的工程文档

基于本阶段判断，建议同步维护以下工程文档：

### 必须更新

1. `docs/poster2/README.md`
   - 更新当前推荐阅读顺序
   - 加入“当前阶段判断与工程路径修订”文档
   - 把下一阶段从“结构收口”切到“行为层 + 美化层”

2. `docs/poster2/current_stage_assessment_and_engineering_path_update_v1.md`
   - 作为本次阶段结论文档
   - 明确“架构正确，工程路径和实施技术需优化”

3. `docs/poster2/external_reference_poster_design_review_and_migration_v1.md`
   - 作为外部参考的迁移依据
   - 为下一阶段的技术选择提供约束

### 建议继续补齐

4. `docs/poster2/template_behavior_layer_plan_v1.md`
   - 定义 behavior modes 如何上浮进模板协议

5. `docs/poster2/beautification_layer_plan_v1.md`
   - 定义 beauty tokens / style presets 的最小落地模型

6. `docs/poster2/render_service_layer_plan_v1.md`
   - 定义 Puppeteer runtime 的后续硬化路线

---

## 9. 一句话结论

> 当前 `poster2` 已证明”架构目标与基本路线正确”，但尚未证明”模板行为可驱动”和”结果可美化”已经成熟。下一阶段应从”结构稳定化”转向”Template Behavior Layer + Beautification Pathfinding”，并同步优化工程路径与实施技术。

---

## Addendum — PosterSop03 P1 修复说明

本次 PosterSop03 针对 main 合并后诊断图暴露的三个 P1 问题完成了修复，均已合并回 main。

### 修复 1：subtitle 文本泄漏（contract enforcement 失效）

**问题**：resolver 输出 `subtitle_char_budget`（如 48 chars），但 Pillow 和 Puppeteer 渲染器均直接使用原始文本，未强制执行截断约束。CSS `-webkit-line-clamp` 因为 `height: auto !important` 无法作为硬约束。

**修复**：在 Pillow renderer 的 `_draw_text` 调用前，以及 Puppeteer renderer 的 `_build_html` 替换阶段，对 title 和 subtitle 均调用 `_apply_char_budget(text, budget)` 进行硬截断。Budget 由 `bottom_policy.subtitle_char_budget` / `title_char_budget` 提供，来源为 resolver 已解析的合约值。

**意义**：Contract enforcement 在渲染前完成，不再依赖 CSS clamp 作为唯一的溢出防线。

### 修复 2：product 区白框（fit/contain anchor 问题）

**问题**：`template_dual_v2.json` 中 `product_slot.align_y = “end”`，CSS `.slot-product { align-items: flex-end }`，且 `.product-fit-contain img { object-position: center bottom }`。对于横向/宽幅产品图片，`contain` 缩放后高度远小于容器，图片落在底部，上半部分呈现 shell 背景白框。

**修复**：三层同步修改：
- `template_dual_v2.json`: `align_y: “end”` → `”center”`
- `template_dual_v2.css`: `.slot-product` `align-items: flex-end` → `center`；`.product-fit-contain img` `object-position: center bottom` → `center center`
- `template_behavior.py`: `resolve_hero_behavior` 中 `scenario_cover_product_contain` 的 `product_anchor` 由 `”bottom”` 改为 `”center”`

**意义**：产品图片现在在 product region 容器内居中合成，消除了白框，且 Pillow / Puppeteer / behavior 三层保持一致。

### 修复 3：header_mode 空声明（behavior layer 未覆盖 identity_zone_mode）

**问题**：`resolve_header_behavior()` 已实现并输出 `identity_zone_mode`（`logo_and_brand` / `brand_only`），但渲染器未消费该字段。`brand_only` 模式下 logo 仍会在资产存在时被渲染，behavior layer 的声明未真正约束渲染行为。

**修复**：
- `ResolvedHeaderBehavior.css_classes` 新增 `header-identity-*` CSS class
- Pillow renderer：当 `identity_zone_mode == “brand_only”` 时跳过 logo 渲染
- Puppeteer renderer：当 `identity_zone_mode == “brand_only”` 时将 logo URL 视为空，触发 `state-logo-empty`
- `layer_render_status[“brand_logo_layer”]`：新增 `logo_suppressed_by_header_mode` reason_code

**意义**：header behavior layer 现在真正驱动 logo 可见性，`brand_only` 模式声明不再是空声明。

### 当前状态

三个 P1 问题均已关闭。合约驱动基线成立条件进一步加固：
- subtitle/title 文本边界由 resolver budget 强制守住
- product region 合成正确、无白框
- header identity_zone_mode 行为层声明连接到渲染执行

下一步工作继续沿 behavior layer 覆盖（其他 region resolver）和 beautification 层推进。
