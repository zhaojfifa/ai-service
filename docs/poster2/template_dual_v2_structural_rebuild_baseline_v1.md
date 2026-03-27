# poster2 / template_dual_v2 结构重建阶段基线定义（Baseline v1）

## 1. 阶段判断

poster2 已从最近一版结构被扰乱的状态，回到一个可继续工程推进的稳定基线。

当前阶段的核心判断不是“视觉已经完成”，而是系统重新具备了继续演进所需的几个关键条件：

- 主链路可用
- 核心资产可绑定
- 渲染引擎路径明确
- 结果未降级
- 调试与诊断信息可见
- 结构问题已可被明确观察和拆解

因此，当前 poster2 不再定义为“恢复阶段”或“继续修 bug 阶段”，而应正式定义为：

> poster2 / template_dual_v2 进入结构重建阶段。
>
> 以当前 binding-complete、diagnostics-complete、engine-stable 的可工作基线为起点，重建 region shell / content layer / slot contract 的结构体系，先收口版式稳定，再进入视觉优化。

---

## 2. 当前基线的工程结论

### 2.1 链路已恢复为可工作状态

Stage2 已能稳定调用生成接口，并返回完整结果对象。当前状态不是“只能出一张图”，而是已经具备“能生成、能解释、能复查”的工程基础。

### 2.2 当前基线属于 Puppeteer structured path

当前生成结果的工程特征为：

- `renderer_mode = puppeteer`
- `render_engine_used = puppeteer`
- `degraded = false`

这意味着当前基线应被视为：

> Puppeteer structured rendering path 的可工作基线。

而不是临时 fallback 或预览态结果。

### 2.3 Diagnostics 基线已成立

当前 Stage2 已可观察以下调试资产：

- background layer
- product / material layer
- foreground layer
- final composed poster
- renderer metadata

这使后续工程可以按 layer、contract、region 去定位问题，而不是继续依赖肉眼猜测。

### 2.4 核心资产绑定已回到可用状态

当前结果中，以下核心资产已重新进入渲染：

- logo
- scenario image
- product image
- gallery images
- title / subtitle
- feature callout

因此，当前主要问题已经不再是“资产进不来”，而是：

> 资产已经进入，但尚未在固定结构中被稳定、清晰、对等地安放。

---

## 3. 新架构定义

poster2 不再按“自由拼接海报”理解，而是按“结构优先、层次可控、可审计”的方式组织。

### 3.1 第一层：Background Layer

只负责背景氛围与底图承载。

约束：

- 不承担 slot 占位职责
- 不承担内容结构职责
- 不替代场景区、产品区、底部图区的真实布局功能

### 3.2 第二层：Region / Slot Shell Layer

负责将版面拆成固定区域，并建立稳定壳层。

最低应包含以下 region：

- `header_region`
- `scenario_region`
- `product_region`
- `feature_region`
- `bottom_region`

在 region 内继续定义稳定 slot / layer contract，例如：

- `brand_logo_layer`
- `brand_text_layer`
- `agent_pill_layer`
- `scenario_image_layer`
- `product_image_layer`
- `feature_callout_layer`
- `title_layer`
- `subtitle_layer`
- `bottom_gallery_shell_layer`
- `bottom_gallery_items_layer`

约束：

- shell 只负责边界、留白、圆角、布局关系
- shell 不承载真正内容
- shell 不允许通过浅色遮罩、视觉补片等方式替代结构修正

### 3.3 第三层：Content / Text Layer

真正负责内容注入与表达，包括：

- logo
- 场景图
- 产品图
- 底部系列图
- 标题
- 副标题
- 卖点文案
- 品牌 / 代理文案

约束：

- content 只负责内容本身
- 不反向侵入壳层定义
- 不再让图片、文字、遮罩混合承担布局职责

### 3.4 架构本质

poster2 的核心逻辑已经从：

> 让渲染器尽量排出一张看起来不错的图

转为：

> 先用固定结构锁住版面，再把内容填进去，最后才做视觉优化。

---

## 4. 业务目标定义

这套架构的目标，不是创意海报生成，而是：

> 面向运营可用的、结构稳定的营销海报生成能力。

核心目标包括：

### 4.1 结构稳定

无论 logo、scenario、product、gallery 是否齐全，结果都必须在固定结构内渲染，不漂移、不串层、不破版。

### 4.2 品牌可控

Header、标题区、场景区、产品区、卖点区、底部系列图区必须遵循统一逻辑，不能因输入差异破坏版式。

### 4.3 资产可审查

运营必须能明确知道：

- logo 是否真正进入
- scenario 是否真正进入
- gallery 是否真正进入
- 哪个 layer 被渲染
- 哪个 layer 被 collapse
- 当前是否发生 fallback 或 degraded

### 4.4 调试可视化

系统不只输出 final poster，还应持续支持：

- background layer
- foreground / material layer
- renderer metadata
- region / slot debug artifacts
- structure overlay

### 4.5 后续可扩展

结构稳定之后，才进入字体、阴影、配色、风格统一等视觉增强，不再把“看起来更好看”放在结构之前。

---

## 5. 当前业务流程定义

### Stage 1：Core Assets

采集核心输入资产：

- `logo`
- `scenario_image`
- `product_image`
- `gallery_images`
- `brand_name`
- `agent_name`
- `title`
- `subtitle`
- `features`

### Stage 2：Generate Poster

Stage2 不再只是一个生成按钮页，而是运营控制台。

当前可控项包括：

- `renderer_mode = puppeteer`
- preset 选择
- title size / bullet count / region preset
- scene / product / gallery preset
- 触发 `/api/v2/generate-poster`

### Stage 3：Operator Review

运营在结果侧检查：

- final output
- diagnostics
- debug artifacts
- 后续的 slot metadata / structure overlay

这条链路的本质不是“生成一张图”，而是：

> 让运营知道这张图是如何被结构化拼出来的。

---

## 6. 当前暴露出的核心结构问题

当前问题已经不再是链路可用性，而是结构治理不足。

### 6.1 `header_region` 尚未闭环

当前 header 已基本恢复，但仍存在：

- 右侧 `agent_pill_layer` 裁断
- brand / agent text lane 宽度治理不稳定

这说明 header 的 lane contract 还没有真正锁死。

### 6.2 `scenario_region` 被壳层压弱

左侧场景图虽然已经进入，但仍偏“被罩住”“被雾化”，不像真正承载情境的主视觉区。

这说明：

- scenario content 已存在
- 但 scenario shell 与背景 / 前景层关系仍不合理

### 6.3 `product_region` 与 `scenario_region` 不在同一结构层级

中间产品卡偏重，左侧场景区偏虚，说明两个 region 仍不属于同一套清晰、对等的层级体系。

这不是素材问题，而是 region shell 不一致。

### 6.4 `feature_region` 仍存在 slot 治理问题

右侧 feature callout 已出来，但仍有以下问题：

- 文本截断
- 高度不一致
- connector 与文本容器关系不够稳定

也就是说，feature 数量虽然进入了，但 `count / box / connector / collapse` 还没有真正闭环。

### 6.5 `bottom_region` 仍然职责混合

底部 title band 与 gallery strip 虽然都已出现，但仍处于“叠在一起”的状态，更像一个视觉带里塞了两个职责。

这意味着 bottom 区应继续拆成两个独立 region，而不是继续在一个混合层上修修补补。

---

## 7. 当前工程版本定义

建议将当前新一轮工程正式命名为：

> `poster2 / template_dual_v2 / Structural Rebuild Baseline v1`

也可简写为：

> `template_dual_v2-sr1`

含义如下：

- `template_dual_v2`：当前核心模板
- `Structural Rebuild`：当前任务不是美化，而是结构重建
- `Baseline v1`：这是回归后的稳定起点，不是最终视觉版

---

## 8. 本轮工程目标

本轮目标不是“做一张更好看的图”，而是：

> 将当前可工作的 Puppeteer baseline，升级为 region-shell 清晰、slot 行为稳定、layer 分层明确的结构版本。

要达成的业务结果是：

### G1. Header 稳定

logo、brand、agent pill 三条 lane 在不同文本长度下不裁断、不漂移。

### G2. Scenario / Product 对齐

场景区和产品区进入同一套 region 逻辑，避免一个实、一个虚。

### G3. Feature 数量闭环

只渲染真实 feature 数量；未使用 slot 完全 collapse；不留 ghost connector。

### G4. Bottom 区职责拆开

将标题区和底部系列图区彻底拆分，避免底部继续混层。

### G5. Diagnostics 持续成立

在推进结构时，不破坏当前已成立的 diagnostics 与 artifacts 输出能力。

---

## 9. 本轮明确不做的事情

为了避免再次把变量搅乱，本轮冻结以下范围：

- 不改 Stage1 资产输入逻辑
- 不改 API contract
- 不改 background prompt / Firefly 路线
- 不改配色体系
- 不改阴影 polish
- 不改字体美化细节
- 不扩新模板
- 不同时动前端交互与后端生成协议

本轮只做：

- region shell
- slot bound
- lane width
- count / collapse
- safe bounds
- content / shell 分离

---

## 10. 本轮实施顺序

### Iteration 1：Header 闭环

固定三条 lane：

- logo lane
- brand text lane
- agent pill lane

处理内容：

- pill 裁断
- brand lane 溢出
- header 内边距与最大宽度规则

### Iteration 2：Scenario / Product 双区对齐

目标：

- 两个 region 成为同一层级体系
- shell 只负责容器
- content 只负责图像
- 禁止再用浅遮罩修视觉

### Iteration 3：Feature 区闭环

目标：

- `feature_count` 决定渲染数量
- 未使用 slot 完全 collapse
- connector 只服务真实 slot
- 文本高度按固定 contract 处理

### Iteration 4：Bottom 区拆分

将当前 bottom 拆成：

- `title_band_region`
- `gallery_strip_region`

并分别赋予独立的 shell、padding 与 safe bounds 规则。

### Iteration 5：轻量视觉校正

仅在以上四步稳定以后，再处理：

- scene / product balance
- border radius 微调
- shadow
- 对齐与留白 polish

---

## 11. 本轮验收标准

本轮不再用“看起来更顺眼”作为验收标准，而改用结构硬标准。

### A. 引擎与状态

- `render_engine_used = puppeteer`
- `degraded = false`
- diagnostics 持续可见

### B. Header

- agent pill 不裁断
- brand text 不压 logo
- 三条 lane 在较长文本下仍稳定

### C. Scenario / Product

- 场景区不再被洗白成占位态
- 产品区与场景区视觉权重接近
- 两区边界明确但不互抢

### D. Feature

- 真实数量 = 渲染数量
- 未使用 slot 全部 collapse
- connector 不残留
- 文本不出现半截裁断

### E. Bottom

- `title_band_region` 与 `gallery_strip_region` 完全分离
- gallery 图片条不侵入标题带
- subtitle 不再夹在底部混合结构中间

---

## 12. 一句话项目定义

> poster2 已从异常结构版本回到一个可工作的 Puppeteer baseline；当前核心任务不是继续修链路，而是以 `template_dual_v2` 为中心，重建 region shell / content layer / slot contract 的结构体系，形成可稳定演进的海报模板架构。

---

## 13. 可直接用于新对话或新分支的开场描述

当前 poster2 已回到一个可工作的结构基线：Stage2 能稳定生成，`render_engine_used=puppeteer`，`degraded=false`，且 background / product-material / foreground / final / renderer metadata 等 debug artifacts 均可见。当前问题不再是链路不可用，也不是资产无法绑定，而是结构治理仍未收口：header 的 pill lane 裁断，scenario shell 压弱内容，product 与 scenario 不在同一 region 层级，feature slot 仍存在 count / connector / box 不一致，bottom 区仍混合了 title band 与 gallery strip。新工程定义为 `template_dual_v2 Structural Rebuild Baseline v1`，目标是从当前基线出发，优先重建 region shell / content layer / slot contract，先完成结构闭环，再进入视觉优化。
