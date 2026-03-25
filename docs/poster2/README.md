# poster2 文档索引与架构模式

## 1. 文档定位

`docs/poster2/` 目录不再只是阶段性记录，而应作为 poster2 的正式架构文档域。

从当前版本开始，poster2 的文档结构按“架构模式 → 工程实施 → 后续扩展”的方式组织，避免把架构定义、业务目标、实施细节和调试内容混写在一份文档里。

poster2 的正式文档模式定义为：

- **架构层文档**：定义确定性的架构目标、结构模型、业务目标、运行原则
- **工程层文档**：定义当前工程基线、实施范围、迭代顺序、验收标准
- **索引层文档**：负责建立阅读顺序、版本关系与文档职责边界

这意味着 poster2 进入了一个真正可持续维护的架构文档模式，而不再依赖单篇大文档承载全部内容。

---

## 2. 当前推荐阅读顺序

### A. 先读：架构与业务定义

文件：`template_dual_v2_architecture_business_definition.md`

职责：

- 定义 poster2 / template_dual_v2 的项目定位
- 定义确定性的业务目标
- 定义三层架构模型
- 定义 region / slot / shell / content 的边界
- 定义双引擎原则
- 定义标准业务流程与目标状态

适用角色：

- 架构师
- 产品负责人
- 技术负责人
- 需要理解系统长期方向的人

### B. 再读：工程实施与验收清单

文件：`template_dual_v2_engineering_implementation_and_acceptance.md`

职责：

- 定义当前工程基线
- 记录当前主要结构问题
- 定义冻结范围与实施原则
- 给出迭代顺序与验收标准
- 提供分支与提交建议
- 提供新工程开场口径

适用角色：

- 工程师
- Codex / 自动化执行代理
- 项目推进负责人
- 需要按阶段推进的协同人员

### C. 最后读：阶段索引与版本摘要

文件：`template_dual_v2_structural_rebuild_baseline_v1.md`

职责：

- 说明当前阶段的版本定义
- 建立当前阶段与正式文档之间的索引关系
- 作为结构重建阶段的版本入口，而不再承担全部正文内容

---

## 3. poster2 的正式架构模式

当前 poster2 的架构模式可以概括为：

> **Architecture Definition → Engineering Implementation → Iterative Acceptance**

也就是三层文档治理模式：

### 3.1 Architecture Definition

解决的问题是：

- 这个系统到底是什么
- 它的确定性目标是什么
- 它为什么不是自由拼接海报
- 它的结构模型是什么
- 双引擎在其中分别承担什么职责

产物对应：

- `template_dual_v2_architecture_business_definition.md`

### 3.2 Engineering Implementation

解决的问题是：

- 当前工程处于哪个基线
- 现在最应该解决什么问题
- 哪些范围被冻结
- 迭代顺序如何安排
- 每一步怎样验收

产物对应：

- `template_dual_v2_engineering_implementation_and_acceptance.md`

### 3.3 Iterative Acceptance

解决的问题是：

- 当前轮次做到哪里
- 这一轮是否符合结构标准
- 是否还能继续进入下一轮视觉优化或模板扩展

这一层目前由工程实施文档承载，后续可继续拆出独立的：

- contract 文档
- 验收基线文档
- 模板版本文档

---

## 4. 当前阶段的架构结论

当前 poster2 / template_dual_v2 的正式方向已经明确：

- 它不是创意型任意拼接工具
- 它是以 region-shell architecture 为核心的可控动态模板系统
- 它以统一 contract 为真相源
- 它以双引擎执行为支撑
- 它以结构稳定优先于视觉美化
- 它以运营可审查、工程可复盘、模板可扩展为长期目标

因此，当前所有工程推进都应服从这套架构模式，而不是回到“见问题就局部补视觉”的旧路径。

---

## 5. 当前文档清单

### 核心文档

- `README.md`
- `template_dual_v2_architecture_business_definition.md`
- `template_dual_v2_engineering_implementation_and_acceptance.md`
- `template_dual_v2_structural_rebuild_baseline_v1.md`

### 后续建议扩展文档

在结构重建阶段继续推进后，建议逐步补齐以下文档：

- `template_dual_v2_contract_definition.md`
- `template_dual_v2_region_slot_spec.md`
- `template_dual_v2_acceptance_baseline.md`
- `template_dual_v2_renderer_contract.md`

这样 poster2 才会形成真正完整的架构文档体系，而不是只有架构总述与工程计划。

---

## 6. 一句话定义

> `docs/poster2/` 从当前版本开始，按“索引层 + 架构层 + 工程层”的方式组织，形成 poster2 的正式架构模式与持续演进文档域。
