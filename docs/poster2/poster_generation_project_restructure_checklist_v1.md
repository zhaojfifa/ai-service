# 海报生成项目落地重构清单 v1

## 1. 文档定位

本文档用于承接 poster2 从“已验证架构方向”进入“项目化落地重构”的阶段。

其目标不是讨论单次样式调整，而是明确：

- 哪些设计应保留
- 哪些模块必须重构
- 哪些工作应延后
- 项目化落地时的实施顺序与交付物

本文档与《海报可控生成产品设计基线 v1》配套使用：前者定义产品与架构口径，本文档定义落地重构路线。

---

## 2. 当前阶段判断

之前的工程已经验证了以下方向是有效的：

- 三层逻辑有效：结构层、控制层、美化层
- 双引擎方向有效：Pillow 作为稳定 fallback，Puppeteer 承接复杂模板
- 三段式业务流程有效：输入素材 → 生成海报 → 发送邮件
- 两类模板家族有效：营销讲解型、产品图录型

因此，当前项目不应推翻基础架构，而应从“可生成”升级为：

> **可落地项目的稳定可控海报生成系统**

当前主矛盾不是“有没有图”，而是：

- 模板协议尚未真正工程化
- 控制层尚未完成稳定性治理
- 双引擎切换与质量守护尚未完全业务化
- 结果虽然可生成，但还没有达到长期可运营的稳定标准

---

## 3. 重构总原则

### 3.1 保留已验证正确的方向

不推翻：

- 三层逻辑
- 双引擎总体方向
- 两类模板家族
- Stage1 / Stage2 / Stage3 的产品流程骨架

### 3.2 重构真正未收口的中间层

重点重构：

- 模板协议
- 控制层
- 质量守护
- 引擎路由
- region / slot 的工程表达

### 3.3 延后视觉大改

在结构与控制稳定之前，不将以下内容作为主任务：

- 大规模视觉美化
- 氛围层加强
- 单样本级 CSS 微调
- 通过遮罩或特效掩盖结构问题

---

## 4. 保留 / 重构 / 延后 清单

## 4.1 保留项

以下设计已经验证有效，继续作为项目基座：

### A. 三层逻辑

- 结构层：决定 region 与 slot 的确定性结构
- 控制层：保证输入波动下的稳定性
- 美化层：在结构稳定后统一视觉语言

### B. 双引擎路线

- Pillow：稳定 fallback / 简化模板保底路径
- Puppeteer：复杂模板 / 更强排版 / 更强图层控制

### C. 两类模板家族

- 模板家族 A：营销讲解型
- 模板家族 B：产品图录型

### D. 三段式产品流程

- Stage1：素材与文案输入
- Stage2：海报生成
- Stage3：邮件发送

## 4.2 重构项

以下是当前项目化落地必须重构的部分：

### A. 模板协议

将模板从“页面样式定义”升级为“模板协议定义”，至少包括：

- template family
- template id / version
- region contract
- slot contract
- fallback compatibility
- renderer preference

### B. 控制层

将控制层拆成两段：

- 稳定性控制
- 布局控制

当前优先重构稳定性控制，不先重构美化。

### C. 质量守护

把 quality guard 从“成图后观察”前移为“渲染过程即判定”，至少输出：

- degraded
- fallback_reason
- render_engine_used
- region_render_status
- structure completeness
- diagnostics / explainability

### D. 双引擎路由

将 renderer routing 从“隐式尝试”升级为“模板家族可解释路由”，明确：

- preferred renderer
- fallback allowed / not allowed
- fallback 后最低可交付结构

### E. Region / Slot Schema

必须定义：

- mandatory regions
- collapsible regions
- required slots
- optional slots
- collapse rules
- replacement rules
- forbidden overlap rules

## 4.3 延后项

以下工作在当前阶段不作为主任务：

- 大规模字体体系重做
- 整体彩色体系重做
- 背景视觉氛围增强
- 复杂阴影与材质表达
- 视觉风格多主题化
- 模板大量扩展

---

## 5. 项目化落地的核心重构对象

## 5.1 模板家族注册表（Template Family Registry）

职责：

- 维护模板家族 A / B
- 维护 template_id / template_version
- 维护 preferred renderer
- 维护 allowed fallback
- 维护 family-level output semantics

交付物：

- family registry 配置对象
- template metadata registry

## 5.2 Region Contract Resolver

职责：

- 从模板家族解析出实际 region 结构
- 标记 mandatory / collapsible regions
- 输出 region bounds / z-order / replacement rules

交付物：

- region contract schema
- per-family mandatory region matrix

## 5.3 Slot Contract Resolver

职责：

- 定义每个 region 内的 slot 结构
- 区分 required slots / optional slots
- 输出 collapse rules / max count / fallback content rules

交付物：

- slot schema
- slot validity rules

## 5.4 Input Qualification / Normalizer

职责：

- 对输入做先验治理，而不是直接渲染
- 识别文本长度等级、图片比例等级、gallery 完整度、spec 信息完整度

交付物：

- input qualification rules
- input grading schema

## 5.5 Content Injection Orchestrator

职责：

- 将品牌资产、产品图、场景图、文案、gallery、参数信息注入模板协议
- 受模板约束，不允许自由越界注入

交付物：

- injection manifest
- injection validity checks

## 5.6 Foreground Render Router

职责：

- 决定使用 Puppeteer 还是 Pillow
- 失败时决定是否允许 fallback
- fallback 后决定是否仍满足模板交付标准

交付物：

- renderer selection rules
- fallback decision rules

## 5.7 Quality Guard / Explainability Layer

职责：

- 输出结构与渲染是否成立
- 给运营、产品、工程提供可解释结果

交付物：

- degraded / fallback semantics
- structure completeness report
- region render status report
- debug artifact links / metadata output

---

## 6. 两类模板家族的落地重点

## 6.1 模板家族 A：营销讲解型

### 当前重点保留

- 品牌头部
- 场景 + 产品的双主视觉理念
- feature callout 表达
- 底部系列条

### 当前重点重构

- header lane contract
- scenario_region / product_region 的 peer relationship
- feature count-driven modes
- title band / gallery strip 的结构拆分
- fallback 后的最小交付标准

### 当前不优先处理

- 复杂视觉材质感
- 高级阴影与氛围层
- 大范围品牌感精修

## 6.2 模板家族 B：产品图录型

### 当前重点保留

- 品牌横幅 / 品牌锚点
- 单品主图主导
- 参数与说明块
- CTA / footer 的纵向信息秩序

### 当前重点重构

- hero product 不变形规则
- spec block / copy block / CTA block 的稳定位置
- 移动端长图的垂直节奏规则
- footer / CTA 与主图区的互不抢位规则
- fallback 后的信息完整性标准

### 当前不优先处理

- 过强的图录风格美术包装
- 品牌皮肤多样化

---

## 7. 当前阶段的实施顺序

## Phase 1：锁定模板协议基座

目标：

- 两类模板家族正式建模
- 模板 id / version 规则稳定
- mandatory / collapsible regions 明确
- slot schema 明确

交付物：

- template family registry
- mandatory region checklist
- slot contract baseline

## Phase 2：稳定性控制前移

目标：

- 定义结构成立标准
- 定义 degraded / fallback 语义
- 定义 renderer routing 规则
- 定义 structure completeness checks

交付物：

- stability control rules
- renderer routing baseline
- quality guard baseline

## Phase 3：布局控制落地

目标：

- title / subtitle budget
- header lane behavior
- feature count mode
- scenario / product fitting policy
- spec / copy vertical rhythm

交付物：

- region layout behavior rules
- per-family layout modes

## Phase 4：视觉美化后置收口

目标：

- 在结构与控制稳定后，再统一视觉语言

交付物：

- design token baseline
- beauty layer guidelines

---

## 8. 当前阶段的验收口径

当前不是按“更好看了”验收，而按以下条件验收：

### 8.1 结构验收

- 产品主图不变形
- mandatory regions 成立
- collapsible regions 按规则折叠
- fallback 不导致结构无解释失真

### 8.2 控制验收

- degraded / fallback 语义清晰
- renderer 路由有规则可循
- 输入不理想时仍有可预期行为
- 结果可解释、可审查、可复盘

### 8.3 业务验收

- 能支撑真实素材输入
- 能支撑文案确定性注入
- 能生成可用于邮件发送的最终海报
- 运营能理解结果为什么如此

---

## 9. 当前阶段建议新增文档

为便于工程落地，建议后续继续补齐以下文档：

- `template_family_region_matrix_v1.md`
- `template_family_slot_contract_baseline_v1.md`
- `renderer_routing_and_fallback_rules_v1.md`
- `quality_guard_and_structure_completeness_v1.md`
- `region_layout_control_phase_plan_v1.md`

---

## 10. 一句话结论

> **当前项目不需要推翻基础架构，而需要围绕模板协议、控制层、质量守护与双引擎路由完成重构，使 poster2 从“可生成”升级为“可项目化落地的稳定可控海报生成系统”。**
