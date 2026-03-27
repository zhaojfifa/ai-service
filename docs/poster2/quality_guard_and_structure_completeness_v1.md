# Quality Guard 与 Structure Completeness v1

## 1. 文档定位

本文档用于把 poster2 的“可解释、可审查、可回退”要求推进到工程可执行层。

本文档关注：

- 什么叫结构成立
- 什么叫结构不完整
- 什么叫结果可交付
- Quality Guard 在什么时候介入
- 哪些检查属于 renderer 之前，哪些属于 renderer 之后

本文档与以下文档配套：

- `template_family_region_matrix_v1.md`
- `template_family_slot_contract_baseline_v1.md`
- `renderer_routing_and_fallback_rules_v1.md`

---

## 2. 核心目标

Quality Guard 的目标不是让结果“更好看”，而是保证：

- 结构成立条件被明确判断
- 输入不合格时不进入错误渲染
- fallback 后结果重新接受结构审查
- 输出对运营、产品、工程都是可解释的

一句话：

> **Quality Guard 负责把“能出图”与“可交付”分开。**

---

## 3. 三个核心判定

## 3.1 `structure_complete`

表示模板家族要求的 mandatory regions 与 required slots 已按契约成立。

为 `true` 的最低条件：

- mandatory regions 全部成立
- required slots 全部成立
- reading order 未被破坏
- 主产品图未变形
- family minimum deliverable structure 满足

## 3.2 `incomplete_structure`

表示模板结构未按契约成立。

触发条件包括：

- mandatory region 缺失
- required slot 缺失
- title / spec / product 等核心内容失位
- fallback 后仍不能满足 family minimum deliverable rules

`incomplete_structure = true` 时，不应视为正常可交付成品。

## 3.3 `deliverable`

表示该次结果是否可交付给运营与后续邮件链路继续使用。

建议判定：

- `structure_complete = true` 且无致命错误 → `deliverable = true`
- `degraded = true` 但 `structure_complete = true` → `deliverable = true`
- `incomplete_structure = true` → `deliverable = false`

---

## 4. Quality Guard 的介入时点

## 4.1 Render 之前：Preflight Guard

职责：

- 判断输入是否具备基本生成条件
- 判断模板协议是否完整
- 判断 family / region / slot 关系是否合法

检查内容：

- template family 是否存在
- template id / version 是否合法
- region matrix 是否可解析
- slot contract 是否可解析
- product_image 是否存在
- 文本输入是否至少具备最小 required set

若 preflight 失败：

- 不应进入正式 renderer
- 直接输出 `deliverable = false`
- 标记输入或协议级错误

## 4.2 Render 之后：Post-render Guard

职责：

- 判断渲染结果是否满足结构交付要求
- 判断 fallback 后结果是否仍成立
- 生成可解释 metadata

检查内容：

- mandatory regions 是否 rendered
- required slots 是否 rendered
- collapse 是否按规则发生
- 是否存在 ghost connector / ghost box / empty shell
- 主产品图是否存在、是否变形
- title / copy / spec 是否仍在所属 region 中

---

## 5. 检查层次划分

## 5.1 协议级检查

检查：

- family 是否存在
- region matrix 是否存在
- slot contract 是否存在
- renderer preference 是否存在

失败示例：

- 模板配置缺失
- mandatory region 未定义
- required slot 无绑定规则

这类错误不应交给 fallback 处理。

## 5.2 输入级检查

检查：

- 主产品图是否存在
- family 所需最小文本是否存在
- 参考号 / spec / copy 是否满足当前 family mode 的最低要求

失败示例：

- Family A 无主产品图
- Family B 无主产品图且无说明信息

这类错误属于 `input_invalid`，不应通过 renderer 兜底。

## 5.3 渲染级检查

检查：

- renderer 是否超时
- renderer 是否 crash
- 页面是否完成生成
- artifacts 是否生成

这类错误才属于 renderer routing / fallback 范畴。

## 5.4 结构级检查

检查：

- mandatory regions 是否完整
- required slots 是否完整
- region / slot 是否按 contract 呈现

这是最终决定 `deliverable` 的核心检查层。

---

## 6. Family A / B 的最低交付标准

## 6.1 Family A：营销讲解型

最低可交付要求：

- `header_region` 成立
- `product_region` 成立
- `title_band_region` 成立
- 主产品图不变形

可折叠但不影响可交付：

- `scenario_region`
- `feature_region`
- `gallery_strip_region`

直接判 `incomplete_structure` 的情形：

- header 丢失
- 主产品图区丢失
- title 丢失或漂移
- hero 主骨架失效

## 6.2 Family B：产品图录型

最低可交付要求：

- `brand_banner_region` 成立
- `hero_product_region` 成立
- `spec_region` 或 `copy_region` 至少一个核心信息区成立
- 主产品图不变形

可折叠但不影响可交付：

- `reference_region`
- `supporting_visual_region`
- `cta_region`
- `footer_brand_region`

直接判 `incomplete_structure` 的情形：

- 品牌锚点丢失
- 主产品图区丢失
- spec 与 copy 同时失效

---

## 7. 结构完整性输出对象

建议工程上固定输出：

### 7.1 Region Completeness

- `rendered_regions`
- `collapsed_regions`
- `missing_mandatory_regions`
- `region_violation_reasons`

### 7.2 Slot Completeness

- `rendered_required_slots`
- `missing_required_slots`
- `collapsed_optional_slots`
- `slot_violation_reasons`

### 7.3 Deliverability

- `structure_complete`
- `incomplete_structure`
- `deliverable`
- `deliverable_reason`

---

## 8. 典型错误语义

建议统一以下语义：

- `template_contract_invalid`
- `region_matrix_missing`
- `slot_contract_invalid`
- `input_invalid_product_missing`
- `input_invalid_required_text_missing`
- `renderer_timeout`
- `renderer_exception`
- `fallback_used`
- `missing_mandatory_region`
- `missing_required_slot`
- `ghost_structure_detected`
- `main_product_distorted`
- `incomplete_structure`

这些语义应可直接进入 metadata 与 diagnostics。

---

## 9. 当前阶段的最小工程落地要求

在真正进入大规模布局控制前，Quality Guard 至少应先支持：

- preflight guard
- post-render structure check
- family minimum deliverable rules
- degraded / incomplete_structure / deliverable 三者分离
- region / slot completeness 输出

---

## 10. 一句话结论

> **Quality Guard 的任务不是修样式，而是把模板家族契约真正执行成“可交付判定系统”，让每一次出图都能回答：结构是否成立、结果是否可交付、问题究竟出在哪一层。**
