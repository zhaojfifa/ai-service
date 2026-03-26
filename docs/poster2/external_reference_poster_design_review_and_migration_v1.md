# poster-design 外部参考复盘与迁移建议 v1

## 1. 文档定位

本文档用于沉淀对外部参考项目 `poster-design` 的第二轮复盘，并将其结论映射到当前 `poster2` 工程。

目标不是讨论“是否迁移为编辑器架构”，而是回答以下问题：

1. `poster-design` 哪些能力值得借鉴。
2. 这些能力应放入 `poster2` 的哪一层。
3. 哪些能力不能借鉴，避免破坏当前已验证的 contract-first 架构。
4. 基于这些结论，下一阶段的工程应如何推进。

---

## 2. 当前项目基线（带入原有工程约束）

在看外部参考前，必须先锁定当前 `poster2` 已经验证的事实。

### 2.1 已验证成立的部分

当前 `poster2` 已经证明：

- 结构 contract 已经可以守住。
- 内容注入已经可以受控。
- 结果可以复现。
- diagnostics / deliverable / structure 语义已经成立。
- `template_dual_v2` 的五大 region（header / scenario / product / feature / bottom）已具备可用的稳定性基线。

### 2.2 尚未证明的部分

当前尚未完全证明：

- 模板行为真正可驱动。
- 两类模板家族可由统一的行为层驱动，而不是继续依赖大量模板级编码。
- 结果可在不破坏 structure contract 的前提下形成独立的 Beautification Layer。

### 2.3 不可破坏的三条约束

后续所有借鉴和迁移，都必须保留以下约束：

1. **两类模板家族目标不变**
   - 当前系统不是只服务一个模板，而是要支撑至少两类模板家族。

2. **业务闭环不变**
   - 输入素材 → 生成海报 → 发送邮件 的业务闭环不能被破坏。
   - `deliverable`、`structure_complete`、`region_render_status`、`slot_binding_status` 等运营审查语义必须保留。

3. **双引擎职责边界不变**
   - Pillow 仍是稳定主路径 / fallback 基线。
   - Puppeteer 仍是复杂模板与复杂排版增强路径。
   - 行为层不应塌缩成 Puppeteer-only 逻辑。

---

## 3. 对 poster-design 的第二轮判断

## 3.1 总体结论

`poster-design` 是一个 **editor-first** 的在线图片编辑/海报设计系统，不是一个 **contract-first** 的模板协议驱动系统。

因此，它不适合作为 `poster2` 的直接主架构来源。

但它在以下四方面具有很强的参考价值：

1. Beautification vocabulary
2. PSD / design asset extraction
3. page/layer/container envelope 作为中间物料模型
4. browser-based render service pattern

### 3.2 核心判断

- 它强在“视觉能力”和“编辑器运行时”，不强在“模板行为协议”。
- 它可以帮助我们补足 Beautification Layer 与 Render Service Layer。
- 它不能替代我们已经验证过的 region / slot / diagnostics / deliverable 体系。

---

## 4. 值得借鉴的内容

## 4.1 Beautification vocabulary（最高优先级）

这是 `poster-design` 最值得借鉴的部分。

可借鉴内容包括：

- 文本效果 vocabulary
  - fill
  - stroke
  - shadow
  - offset
  - emphasis
- 图片表现 vocabulary
  - radius
  - mask
  - flip
  - border-image-like slicing
- 背景与表面 vocabulary
  - gradient
  - shell surface
  - tone
  - depth
  - accent

这些内容不应直接搬成 widget 配置，而应转译成 `poster2` 的 **beauty tokens / effect presets**。

## 4.2 PSD / design extraction ideas（第二优先级）

`poster-design` 的 PSD parser 思路值得参考。

它能从设计稿中抽出：

- text/image clouds
- writing mode
- stroke / shadow
- transform matrix

对 `poster2` 的价值不是“导入 PSD 直接生成最终模板”，而是：

- 用于生成 template seed data
- 用于 Geometry / Evidence ingestion
- 用于辅助构建 designer-authored intermediate

输出必须映射回我们自己的：

- region
- slot
- behavior mode
- evidence payload

而不是映射回 editor widget instances。

## 4.3 Page / Layer / Container envelope（可适配借鉴）

`poster-design` 的 page + flat layers + parent/container envelope 结构，适合作为：

- contract 解析后的内部物料模型
- 多模板家族下的下游 render material representation

但它只能位于：

- region / slot contract 之后
- renderer runtime 之前

不能成为用户侧模板协议本身。

## 4.4 Browser render service pattern（参考借鉴）

`poster-design` 的浏览器截图路径只能作为：

- Puppeteer Render Service Layer 的参考

可借鉴：

- browser lifecycle
- page lifecycle
- asset/font wait strategy
- screenshot artifact flow

不能直接借鉴：

- html2canvas 主路径
- DOM export 作为最终证据层
- 依赖前端 route 的 render core

---

## 5. 不值得借鉴的内容

以下内容不应成为 `poster2` 的主方向。

## 5.1 Editor state stores

例如：

- selection state
- crop state
- drag/drop state
- moveable handles
- group resize replay

这些是交互式编辑器复杂度，不属于生成产线的稳定语义。

## 5.2 Widget-first runtime

`poster-design` 的模板本质是页面快照 / layer snapshot，而不是语义 contract。

因此不应让 `poster2` 变成：

- widget-first JSON
- page snapshot 驱动
- editor component 驱动

## 5.3 DOM existence as render evidence

`poster-design` 的浏览器 render path 更偏 faithful screenshot，而不是 backend-safe deterministic evidence。

`poster2` 必须继续坚持：

- diagnostics / evidence 由后端控制
- visible / clipped / collapsed / deliverable 不能仅靠 DOM 节点存在判断

---

## 6. 映射到 poster2 的架构层

基于当前架构，建议把外部参考吸收进以下四层。

## 6.1 Template Behavior Layer（当前最缺）

这是下一阶段最关键的新增层。

当前许多行为仍分散在：

- `template_dual_v2.json`
- `slot_spec.template_dual_v2.json`
- `template_dual_v2.css`
- `renderer.py`

应逐步上浮成声明式 behavior modes。

建议最先抽出的 mode：

- `header_mode`
- `hero_mode`
- `feature_mode`
- `bottom_mode`
- `gallery_mode`

当前 `template_dual_v2` 的隐含 mode，可先视为：

- `header_mode = identity_left_agent_right`
- `hero_mode = scenario_cover_product_contain_bottom_anchor`
- `feature_mode = count_driven_callout_stack`
- `bottom_mode = independent_title_gallery_split`
- `gallery_mode = strip_local_visible_only`

这些 mode 应进入 template metadata / behavior resolver，而不是继续只散落在 CSS 和 Python 常量里。

## 6.2 Beautification Layer（第二优先级）

建议新增独立的 beauty token object。

最小可行 token families：

- `shell_surface`
- `shell_border`
- `shell_shadow`
- `accent_tone`
- `text_emphasis`

原则：

- 先装饰现有 shell
- 不替代结构
- 不修改 region geometry
- 不用 beauty 覆盖 behavior 问题

## 6.3 Geometry / Evidence Layer（第三优先级）

当前已有：

- `structure_evidence_source`
- `structure_evidence_complete`
- `region_render_status`
- `slot_binding_status`

后续建议新增通用 evidence payload：

- `region_bounds`
- `slot_bounds`
- `visible_bounds`
- `overflow_state`
- `clipping_state`
- `visible_item_count`

这会让“结构守住了”变成几何可证明，而不是主要靠肉眼判断。

## 6.4 Render Service Layer（第四优先级）

当前 Puppeteer 仍更多是 renderer embedded in app logic。

后续应逐步硬化成：

- browser lifecycle policy
- page reuse / page pool
- request filtering policy
- wait policy
- artifact policy

原则：

- renderer 负责模板输出
- runtime service 负责浏览器治理
- 不需要一开始就拆独立微服务

---

## 7. 迁移矩阵

## 7.1 Directly adopt

- Declarative behavior modes as template metadata
  - `feature_mode`
  - `bottom_mode`
  - `hero_mode`
- Beauty tokens as a separate layer
- Geometry evidence as explicit diagnostics payload
- Puppeteer runtime hardening concepts

## 7.2 Adapt and adopt

- `header_mode`
  - 必须适配到 shell/content split，不走自由编辑器组合
- `gallery_mode`
  - 必须保留当前独立 `gallery_strip_region` 语义
- beautification vocabulary
  - 适配成小型 token families，而不是 editor widget config
- PSD extraction ideas
  - 输出 region/slot/evidence intermediate，而不是 widget snapshot
- page/layer/container envelope
  - 仅作为 contract 解析后的内部 material model

## 7.3 Reference only

- browser automation render pattern
- multi-artboard organization ideas
- family taxonomy naming ideas

## 7.4 Reject

- editor-first runtime as poster2 core
- widget-first JSON as main template protocol
- interactive state stores/actions as backend primitives
- html2canvas / route screenshot 作为长期 render core
- 用美化层替代结构行为层

---

## 8. 对当前工程的落地建议

## 8.1 先不要重写

当前 `poster2` 已经验证了 contract-first 基线。

因此不建议：

- 改成 editor-first
- 改成 widget-first
- 改成完全 DOM 快照驱动
- 为了做美化而破坏 region / slot / diagnostics / deliverable 体系

## 8.2 下一阶段的第一步

最小可行第一步：

### A. 证明模板行为可驱动

仅在 `template_dual_v2` 上新增：

- `feature_mode`
- `bottom_mode`

先把当前 hard-coded mode constants 从 renderer 中抽到 template metadata / behavior resolver。

要求：

- 可见结果不变
- diagnostics 不变
- 只证明行为可由模板驱动

### B. 证明结果可美化

新增最小 beauty tokens：

- `surface_fill`
- `border_strength`
- `shadow_depth`
- `corner_scale`

只作用于已有 shell：

- header banner
- scenario shell
- product shell
- title band shell
- gallery strip shell

要求：

- 不动 geometry
- 不动 slot contract
- 不改变 behavior mode

### C. 补最小几何证据

新增：

- `region_bounds`
- `slot_bounds`
- `visible_item_count`

先从最关键的：

- header
- product
- gallery strip

开始。

---

## 9. 建议的下一阶段名称

当前阶段不再适合继续叫“基础稳定化”。

建议后续阶段命名为：

### `Template Behavior Layer + Beautification Pathfinding`

其目标不是“继续调这个模板”，而是：

- 证明模板行为能由协议驱动
- 证明在不破坏 contract 的前提下，结果可以开始变美

---

## 10. 一句话结论

`poster-design` 的价值，不在于替换 `poster2` 的架构，而在于帮助我们补足：

- Template Behavior Layer
- Beautification Layer
- Geometry / Evidence Layer
- Render Service Layer

下一阶段的重点，不是继续做 editor 化，而是在已经验证的 contract-first 基线上，逐步把行为、样式、证据和运行时治理上浮成明确层次。