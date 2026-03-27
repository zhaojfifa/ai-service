# AI Service 项目索引

## 1. 文档定位

本文件位于 repo 根目录，用于帮助快速理解：

- 当前项目的总体方向
- 主要业务链路
- 当前 poster2 文档域的结构
- 现阶段最重要的基线文档与重构文档

本文件不是详细设计文档，而是仓库级索引入口。

---

## 2. 当前项目基本情况

当前项目的海报生成方向，已经从原型探索进入“可项目化落地”的阶段。

核心业务链路为：

> 输入素材 → 生成海报文案 → 生成海报 → 发送邮件

其中真正的核心壁垒是：

> **海报的稳定可控生成能力**

当前 poster2 的设计方向已经明确：

- 采用一套共同模板语法
- 支撑两个模板家族
- 以结构层 / 控制层 / 美化层三层逻辑推进
- 采用双引擎路线：Pillow + Puppeteer
- 当前优先级是结构稳定与控制层重构，而不是视觉大改

---

## 3. poster2 文档域

poster2 相关文档统一放在：

- `docs/poster2/`

该目录当前已经按“索引层 + 架构层 + 工程层 + 产品基线层”方式组织。

### 3.1 推荐阅读顺序

1. `docs/poster2/README.md`
   - poster2 文档索引与架构模式

2. `docs/poster2/poster_generation_product_design_baseline_v1.md`
   - 海报可控生成产品设计基线 v1

3. `docs/poster2/poster_generation_project_restructure_checklist_v1.md`
   - 海报生成项目落地重构清单 v1

4. `docs/poster2/template_dual_v2_architecture_business_definition.md`
   - template_dual_v2 架构与业务定义

5. `docs/poster2/template_dual_v2_engineering_implementation_and_acceptance.md`
   - template_dual_v2 工程实施与验收清单

6. `docs/poster2/template_dual_v2_structural_rebuild_baseline_v1.md`
   - Structural Rebuild Baseline v1 阶段索引

---

## 4. 当前 poster2 的正式口径

当前 poster2 的正式口径可以概括为：

- 产品目标不是自由拼图，而是稳定可控生成
- 模板体系不是散模板，而是两个模板家族
- 生成逻辑按结构层 / 控制层 / 美化层推进
- 当前阶段只优先推进：结构层固化 + 控制层第一阶段（稳定性控制）
- 视觉美化后置

---

## 5. 当前最重要的两份基础文档

### A. 产品设计基线

- `docs/poster2/poster_generation_product_design_baseline_v1.md`

用于定义：

- 产品本质
- 两类模板家族
- 三层逻辑
- 稳定性控制边界
- 当前阶段工程优先级

### B. 项目落地重构清单

- `docs/poster2/poster_generation_project_restructure_checklist_v1.md`

用于定义：

- 哪些设计保留
- 哪些模块重构
- 哪些工作延后
- 实施顺序与交付物

---

## 6. 当前阶段结论

当前项目不需要推翻基础架构，而应在已验证方向上继续推进：

- 保留三层逻辑
- 保留双引擎方向
- 保留两类模板家族
- 重构模板协议、控制层、质量守护与双引擎路由
- 延后大规模视觉美化

一句话：

> **当前 repo 在 poster2 方向上，已经从“原型探索”进入“稳定可控生成系统”的项目化落地阶段。**
