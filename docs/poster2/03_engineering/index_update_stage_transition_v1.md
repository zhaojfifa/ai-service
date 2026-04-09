# poster2 索引更新（阶段切换）v1

## 0. 文档锚点说明

本文档是顶层产品基线 [poster_generation_product_design_baseline_v1.md](poster_generation_product_design_baseline_v1.md) 之下的阶段切换索引补丁。

它只负责帮助读者从较早阶段阅读顺序切到当前阶段，不单独定义新的产品架构。

## 1. 文档定位

本文档用于在不破坏现有索引结构的前提下，补充当前阶段切换后的推荐阅读顺序。

当前阶段已经不再适合继续只按“结构重建 / 工程收口”来阅读 poster2 文档。

现在的正确阶段判断是：

- 架构目标与基本路线已被验证正确
- 工程路径与实施技术仍需优化
- 下一阶段重点不再是基础稳定化
- 下一阶段重点转为：
  - Template Behavior Layer
  - Beautification Pathfinding
  - Geometry / Evidence Layer
  - Render Service Layer

---

## 2. 当前推荐阅读顺序（更新版）

### A. 架构与业务定义

- `template_dual_v2_architecture_business_definition.md`

### B. 当前阶段判断与工程路径修订

- `current_stage_assessment_and_engineering_path_update_v1.md`

### C. 外部参考迁移判断

- `external_reference_poster_design_review_and_migration_v1.md`

### D. 下一阶段计划文档

- `template_behavior_layer_plan_v1.md`
- `beautification_layer_plan_v1.md`

### E. 早期工程基线与结构收口记录

- `template_dual_v2_engineering_implementation_and_acceptance.md`
- 其他 PosterSop01 阶段文档

---

## 3. 当前阶段的正式结论

当前应统一按以下口径理解 poster2：

> 我们已经证明了 contract-first 架构在 poster2 中成立：结构可控、内容可控、结果可复现、诊断可解释；但尚未证明模板行为可驱动、结果可稳定美化。下一阶段应围绕 Template Behavior Layer 与 Beautification Layer 继续推进，并同步补 Geometry / Evidence Layer 与 Render Service Layer。

---

## 4. 为什么需要本索引更新文档

现有 `README.md` 仍然承接较早阶段的阅读顺序与架构模式说明。

本文件用于确保当前协作方：

- 不再把 poster2 误判为“继续做基础稳定化”
- 不再只盯着单模板局部 CSS 调整
- 能够把工程重心切换到：
  - 行为层上浮
  - 美化层独立
  - 几何证据增强
  - 渲染服务层硬化

---

## 5. 一句话定义

> `index_update_stage_transition_v1.md` 作为当前阶段切换的索引补丁文档，明确 poster2 已经从“结构收口阶段”进入“Template Behavior Layer + Beautification Pathfinding”阶段。
