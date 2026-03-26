# poster2 / template_dual_v2 工程实施与验收清单

## 1. 文档目的

本文档用于承接 `poster2 / template_dual_v2` 在“结构重建阶段”的工程实施工作。

与《架构与业务定义》不同，本文档聚焦：

- 当前工程基线判断
- 现阶段主要结构问题
- 实施范围与冻结范围
- 迭代顺序
- 验收标准
- 新分支 / 新对话的工程开场口径

本文档允许保留必要的业务细节、诊断信息和实施约束，用于指导具体工程推进。

---

## 2. 当前工程基线判断

当前 poster2 已回到一个可工作的基线版本，可作为结构重建阶段的起点。

当前基线具备以下工程特征：

- Stage2 可稳定生成结果
- `/api/v2/generate-poster` 主链路可用
- `renderer_mode = puppeteer`
- `render_engine_used = puppeteer`
- `degraded = false`
- debug artifacts 可见
- renderer metadata 可见
- 核心资产已可进入渲染

当前基线应被定义为：

> binding-complete、diagnostics-complete、engine-stable 的 Puppeteer structured baseline。

这意味着当前不是“恢复失败的版本”，而是一个可以继续推进结构化工程的稳定起点。

建议工程版本命名为：

- 正式名：`poster2 / template_dual_v2 / Structural Rebuild Baseline v1`
- 简写：`template_dual_v2-sr1`

---

## 3. 当前已成立的能力

### 3.1 生成链路已打通

当前 Stage2 已能完成从输入到出图的完整流程，不再处于接口不可用或返回不完整的状态。

### 3.2 渲染引擎路径已明确

本轮基线使用的是 Puppeteer 路径，而不是 Pillow fallback 结果。

这对后续工程意味着：

- 当前问题应按 Puppeteer structured path 处理
- 不应再把问题误判为 fallback 行为
- 后续结构增强应以 Puppeteer 为主执行路径验证

### 3.3 调试基线已成立

当前可以持续观察：

- background layer
- product/material layer
- foreground layer
- final composed poster
- renderer metadata

这意味着后续工程可以围绕 layer、region、contract 去定位问题，而不是回到“猜测是哪一层坏了”的状态。

### 3.4 核心绑定已成立

当前以下关键资产已确认能够进入：

- logo
- scenario image
- product image
- gallery images
- title
- subtitle
- feature callout

因此，当前工程问题已经从“绑定缺失”转向“进入之后如何被稳定安放”。

---

## 4. 当前主要结构问题

### 4.1 Header lane 仍未收口

当前 header 已基本回到可用状态，但仍有明显缺口：

- `agent_pill_layer` 容易裁断
- brand / agent 右侧 lane 宽度不稳定
- pill 与文本 lane 的安全边界还未锁死

这意味着 header 的 contract 仍不够确定。

### 4.2 Scenario 区被壳层压弱

左侧场景图虽然已进入，但当前呈现偏“被罩住”“被雾化”，不像一个完整、独立的主视觉区。

说明：

- scenario 内容已存在
- 但 scenario shell 与 background / foreground 的层次关系不正确

### 4.3 Product 与 Scenario 不在同一结构层级

中间产品区偏重，左侧场景区偏虚，两者没有形成同一套 region 体系下的视觉对等关系。

工程上应判断为：

- 不是素材问题
- 不是单张图质量问题
- 而是 region shell 不一致

### 4.4 Feature 区仍存在 ghost / count / box 问题

当前右侧 feature 已出现，但仍有以下问题：

- 文本被截断
- callout 容器高度不一致
- connector 与文本 box 的绑定不稳定
- 未使用 slot 的 collapse 行为未彻底锁死

### 4.5 Bottom 区仍然混层

当前底部 title band 与 gallery strip 虽然同时出现，但仍处于混合状态：

- 结构职责不清晰
- gallery 更像贴图条
- 标题、副标题与底部图区的空间关系不够干净

工程上应继续推进：

- `title_band_region`
- `gallery_strip_region`

的明确拆分。

---

## 5. 本轮实施原则

### 原则 1：从稳定基线出发

不要从“层级洗白”的问题版本继续修，而要以当前 binding-complete stable baseline 为唯一基线继续推进。

基线标准：

- logo 可进入
- scenario 可进入
- product 可进入
- gallery 可进入
- `render_engine_used = puppeteer`
- `degraded = false`

### 原则 2：先做结构，不做美化

本轮不处理：

- 配色体系升级
- 阴影 polish
- 字体统一
- 背景 prompt 策略
- 更激进的视觉风格增强

本轮只处理：

- region shell
- slot bound
- collapse 规则
- count 规则
- safe bounds
- shell / content 分离

### 原则 3：一轮只解决一个变量

禁止再同时改动：

- 模板结构
- 前端交互
- API contract
- 背景逻辑
- 视觉 polish

应按单变量方式推进，每轮只解决一个结构问题。

### 原则 4：调试能力不得被破坏

在推进结构重建时，必须持续保留：

- final output
- debug artifacts
- renderer metadata
- diagnostics

后续即使做模板重构，也不应牺牲这些观测能力。

---

## 6. 本轮冻结范围

本轮明确冻结以下内容：

- 不改 Stage1 资产输入逻辑
- 不改 `/api/v2/generate-poster` 的主 contract
- 不引入新的背景生成逻辑
- 不扩新模板
- 不调整整体产品流程定义
- 不把视觉美化当作当前主任务
- 不同时重构前端页面与后端结构协议

冻结的目的，是避免再次把结构、逻辑、交互和视觉问题混在一起。

---

## 7. 本轮迭代顺序

## Iteration 1：Header 闭环

目标：

- 固定 logo lane
- 固定 brand text lane
- 固定 agent pill lane

实施重点：

- pill 裁断治理
- brand lane 溢出治理
- header 最大宽度规则
- lane 间距与 padding 固定
- header safe bounds 明确

交付判断：

- 任意正常长度的 brand / agent 文本不裁断
- logo、brand、pill 三者不互相压占
- header 在不同输入下保持稳定轮廓

## Iteration 2：Scenario / Product 双区对齐

目标：

- 让 scenario_region 与 product_region 成为同一套层级体系

实施重点：

- 场景区从“被压弱的视觉占位感”恢复为真实主视觉区
- 产品区与场景区的壳层厚度、权重、边界对齐
- shell 只管容器，content 只管图像
- 禁止再用浅色遮罩修视觉

交付判断：

- scenario 不再呈现洗白占位感
- product 与 scenario 视觉权重接近
- 两区边界明确、互不压制

## Iteration 3：Feature 区闭环

目标：

- feature 渲染数量与输入真实数量严格一致

实施重点：

- `feature_count` 成为唯一数量来源
- 未使用 slot 完全 collapse
- connector 只服务真实 slot
- 文本 box 高度与留白规则统一
- 文本截断规则明确

交付判断：

- 真实数量 = 渲染数量
- 无 ghost connector
- 无无效占位 callout
- feature 文本不出现半截裁断

## Iteration 4：Bottom 区拆分

目标：

- 将当前 bottom 区拆成两个独立 region

拆分结果：

- `title_band_region`
- `gallery_strip_region`

实施重点：

- 标题与副标题回归标题带结构
- gallery strip 独立承担系列图容器职责
- 两者各自定义独立 padding、height、safe bounds

交付判断：

- 标题带不再被 gallery 侵入
- gallery 不再像贴图条临时附着
- subtitle 不再夹在混合结构中间

## Iteration 5：轻量视觉校正

前提：

- 前四轮结构已稳定

可处理内容：

- scene / product balance
- shadow
- border radius 微调
- 对齐与留白 polish

注意：

- 本轮仍不应重新打开大范围视觉实验
- 视觉校正只能建立在结构稳定之后

---

## 8. 验收标准

本轮验收禁止使用“整体看起来更顺眼”作为标准，必须改用结构硬标准。

### A. 引擎与状态

- `render_engine_used = puppeteer`
- `degraded = false`
- diagnostics 持续可见
- debug artifacts 持续可见

### B. Header

- `agent_pill_layer` 不裁断
- brand text 不压 logo
- logo / brand / pill 三条 lane 在较长文本下仍稳定

### C. Scenario / Product

- 场景区不再呈现被洗白占位感
- 产品区与场景区视觉权重接近
- 两区边界明确且层级对等

### D. Feature

- 真实数量 = 渲染数量
- 未使用 slot 全部 collapse
- connector 不残留
- 文本不出现半截裁断
- 各 callout 高度与边界一致

### E. Bottom

- `title_band_region` 与 `gallery_strip_region` 完全分离
- gallery 图片条不侵入标题带
- subtitle 不再夹在底部混合结构中间

### F. 工程连续性

- 不破坏 Stage2 现有主链路
- 不破坏 diagnostics
- 不破坏 artifacts 输出
- 不引入新的 fallback 误判

---

## 9. 分支与提交建议

建议围绕当前结构重建阶段使用更明确的分支命名，例如：

- `poster2/header-region-closeout`
- `poster2/scenario-product-alignment`
- `poster2/feature-region-closeout`
- `poster2/bottom-region-split`
- `poster2/structural-rebuild-sr1`

提交信息建议保持单变量：

- `fix(poster2): close header lane overflow and pill clipping`
- `refactor(poster2): align scenario and product region shells`
- `fix(poster2): enforce feature count and collapse unused slots`
- `refactor(poster2): split bottom region into title band and gallery strip`

---

## 10. 新工程开场描述

可直接用于新对话、新分支或 Codex 指令开场：

当前 poster2 已回到一个可工作的结构基线：Stage2 能稳定生成，`render_engine_used=puppeteer`，`degraded=false`，且 background / product-material / foreground / final / renderer metadata 等 debug artifacts 均可见。当前问题不再是链路不可用，也不是资产无法绑定，而是结构治理尚未收口：header 的 pill lane 裁断，scenario shell 压弱内容，product 与 scenario 不在同一 region 层级，feature slot 仍存在 count / connector / box 不一致，bottom 区仍混合了 title band 与 gallery strip。当前工程定义为 `template_dual_v2 Structural Rebuild Baseline v1`，目标是从当前基线出发，优先重建 region shell / content layer / slot contract，先完成结构闭环，再进入视觉优化。

---

## 11. 一句话工程定义

> 当前工程不是继续修链路，而是以可工作的 Puppeteer baseline 为起点，完成 `template_dual_v2` 的结构收口、区域分层和 slot contract 硬化。
