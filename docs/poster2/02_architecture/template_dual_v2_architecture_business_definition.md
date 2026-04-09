# poster2 / template_dual_v2 架构与业务定义

## 0. 文档锚点说明

本文档是顶层产品基线 [poster_generation_product_design_baseline_v1.md](poster_generation_product_design_baseline_v1.md) 之下的 Family A 工程定义文档。

它服务于：

- `Family A: Campaign Explainer Poster`
- `Background / Shell / Content` 的执行层分解

它不替代顶层产品基线，也不改变 `Structure / Control / Beautification` 的治理顺序。

## 1. 项目定位

poster2 / template_dual_v2 的目标，不是生成“任意创意海报”，而是建立一套**面向运营可用、结构稳定、品牌可控、可持续扩展**的营销海报生成体系。

该体系的核心要求不是随机美观，而是**确定性结构**：

- 输入资产可预测地进入固定版面
- 不同品牌与素材组合仍保持统一结构
- 输出结果可解释、可复查、可审计
- 模板能力可持续扩展，而不依赖一次性视觉拼接

因此，poster2 的本质是：

> 以结构为先导的动态模板系统，而不是自由拼接式海报生成器。

---

## 2. 核心业务目标

### 2.1 结构稳定

无论 logo、场景图、产品图、底部系列图是否完整，系统都必须在固定结构中完成渲染，不漂移、不串层、不破版。

### 2.2 品牌可控

Header、场景区、产品区、卖点区、标题区、底部图区必须遵循统一版式逻辑，不能因输入变化而破坏品牌一致性。

### 2.3 资产可治理

系统必须能清晰表达每一类资产在结构中的位置与职责，包括：

- 品牌资产
- 场景资产
- 产品资产
- 系列资产
- 文本资产

每类资产都应进入确定位置，而不是临时占位或视觉性混用。

### 2.4 输出可审查

系统输出不仅是 final poster，还应具备结构级的可审查性，使运营、产品、工程能够确认：

- 哪些资产进入了最终成图
- 哪些结构被激活
- 哪些 slot 被折叠
- 当前使用了哪条渲染路径

### 2.5 能力可扩展

系统在结构稳定后，才能继续扩展视觉风格、品牌皮肤、模板变体、字体策略、阴影与配色，而不是从一开始就把视觉美化与结构控制混在一起。

---

## 3. 架构原则

### 3.1 结构优先于美化

先定义版式结构与内容边界，再做视觉增强。视觉效果不能替代结构问题的解决。

### 3.2 Shell 与 Content 严格分离

- Shell 负责区域边界、布局、留白、圆角、容器关系
- Content 负责图片、文字、图标等真实内容

两者不得混用，不允许通过遮罩、浅色片层、视觉补片等方式代替结构设计。

### 3.3 Region 优先于单元素拼接

版面先被拆成稳定的 region，再在 region 内定义 slot 与 layer。系统不再以“每个元素单独找位置”为核心逻辑。

### 3.4 Contract 优先于临时修补

每个区域、slot、layer 都应有明确 contract，包括：

- 输入类型
- 容器边界
- 布局规则
- 数量规则
- collapse 规则
- 安全边界

### 3.5 引擎服务于结构，而不是反过来

渲染引擎的职责是执行结构，而不是替代结构决策。模板能力的确定性必须来自 contract，而不是依赖某个引擎“尽量排好看”。

---

## 4. 三层架构模型

## 4.1 Background Layer

职责：

- 提供背景氛围
- 承载底图与整体视觉基底
- 为前景结构提供衬底

边界：

- 不承担 slot 占位职责
- 不承担内容布局职责
- 不替代场景区、产品区、底部图区等真实内容区域

## 4.2 Region / Slot Shell Layer

职责：

- 将海报拆成固定结构区域
- 在区域内建立稳定壳层与 slot contract
- 锁定版式边界与层级关系

最小 region 结构应包括：

- `header_region`
- `scenario_region`
- `product_region`
- `feature_region`
- `bottom_region`

在 region 内继续定义 shell 与 slot，例如：

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

边界：

- shell 只负责结构，不承载内容本身
- shell 必须具备清晰的边界、留白与安全区域
- shell 不通过视觉遮挡修正内容问题

## 4.3 Content / Text Layer

职责：

- 承载真正内容输入
- 将品牌资产、产品资产、场景资产、卖点文案、标题副标题注入既定结构

典型内容包括：

- logo
- 场景图
- 产品图
- 底部系列图
- 标题
- 副标题
- 卖点文案
- 品牌文案与代理文案

边界：

- content 不反向定义结构
- content 不能承担布局职责
- content 必须服从 slot / shell contract

---

## 5. 确定性的版面结构

poster2 / template_dual_v2 应被视为一种**固定结构模板**，其核心不是“元素越多越丰富”，而是“区域职责越清晰越稳定”。

### 5.1 Header Region

职责：

- 承载品牌识别与代理身份信息
- 形成版头统一入口

子结构：

- logo lane
- brand text lane
- agent pill lane

### 5.2 Scenario Region

职责：

- 承载情境视觉
- 提供产品使用场景或品牌氛围

要求：

- 作为独立主视觉区存在
- 不被背景层替代
- 不与产品区职责混淆

### 5.3 Product Region

职责：

- 承载产品主体展示
- 形成视觉上的产品中心点

要求：

- 作为独立产品容器存在
- 与 scenario_region 保持对等但不冲突的层级关系

### 5.4 Feature Region

职责：

- 承载卖点表达
- 将卖点结构化映射为可控 callout

要求：

- 数量由输入真实决定
- 多余 slot 可完全折叠
- 连接器只为真实内容服务

### 5.5 Bottom Region

职责：

- 承载标题区与系列图展示
- 形成海报底部收束结构

建议进一步拆分为：

- `title_band_region`
- `gallery_strip_region`

从结构上避免标题带与底部图区混用。

---

## 6. 资产模型与内容输入

poster2 的业务输入可抽象为五类核心资产：

### 6.1 品牌资产

- `logo`
- `brand_name`
- `agent_name`

### 6.2 场景资产

- `scenario_image`

### 6.3 产品资产

- `product_image`

### 6.4 系列资产

- `gallery_images`

### 6.5 文本资产

- `title`
- `subtitle`
- `features`

这些资产并不是自由落点输入，而是必须映射到既定 region 与 slot。

---

## 7. 运行架构与双引擎原则

poster2 当前采用双引擎增强路线。

### 7.1 Puppeteer 的职责

Puppeteer 负责承接复杂模板、精确排版与更强图层控制，是结构化模板渲染的主增强路径。

适用场景：

- 多 region 复杂版式
- 精确 layer 组合
- 强 slot contract 执行
- 更高保真结构输出

### 7.2 Pillow 的职责

Pillow 继续保留为稳定 fallback。

职责不是承接复杂结构演进，而是：

- 提供基础可交付路径
- 作为简化模板或回退路径使用
- 在复杂模板能力未完全收敛前提供稳定兜底

### 7.3 双引擎的架构原则

- 结构 contract 是唯一真相源
- 渲染引擎只是执行层
- Puppeteer 与 Pillow 不应各自定义不同模板语义
- 长期方向是以统一结构 contract 驱动不同引擎执行

---

## 8. 标准业务流程

### Stage 1：Core Assets

系统收集核心资产：

- logo
- scenario_image
- product_image
- gallery_images
- brand_name
- agent_name
- title
- subtitle
- features

### Stage 2：Generate Poster

系统在既定模板下完成海报生成。

关键控制维度包括：

- renderer mode
- preset
- 标题与卖点的结构参数
- 各 region 的模板策略

### Stage 3：Operator Review

运营对输出进行结果审查与结构复核。

该阶段的目标不是“再编辑一遍海报”，而是确认：

- 结构是否正确执行
- 资产是否正确进入
- 输出是否符合模板约束

---

## 9. 架构边界与非目标

为保证架构确定性，poster2 当前阶段明确不以以下事项为核心目标：

- 不追求开放式创意生成
- 不追求任意布局自由编辑
- 不将背景生成能力视为结构能力
- 不把视觉 polish 当作主架构任务
- 不依赖单次 prompt 或单次调色解决模板治理问题

poster2 的当前目标是：

> 建立一套可控的动态模板架构，让海报在输入变化下仍保持可预测结构与一致输出。

---

## 10. 目标状态

poster2 / template_dual_v2 的目标状态可以概括为：

- 有明确的 region 结构
- 有稳定的 slot contract
- 有可分离的 shell / content 体系
- 有统一的双引擎执行模型
- 有可审查、可复盘、可扩展的输出体系

一句话定义：

> poster2 / template_dual_v2 是一个以 region-shell architecture 为核心、以统一 contract 为真相源、以双引擎执行为支撑的可控营销海报生成体系。
