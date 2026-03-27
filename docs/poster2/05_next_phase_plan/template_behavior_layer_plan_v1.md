# Template Behavior Layer 计划 v1

## 1. 文档定位

本文档用于定义 `poster2` 下一阶段新增的 **Template Behavior Layer**。

其目标不是重写现有架构，而是在已验证的 contract-first 基线上，把当前仍分散在：

- template JSON
- slot spec
- CSS
- Python renderer 条件逻辑

中的行为决策，逐步上浮成统一、可声明、可治理的行为层。

---

## 2. 为什么需要 Template Behavior Layer

当前工程已经证明：

- 结构 contract 可以守住
- 内容注入可以受控
- 结果可复现、可审查

但仍未真正证明：

- 模板行为可驱动
- 两类模板家族可由统一的行为层驱动

问题的根本原因在于：

> 当前模板行为仍然是“半声明式”的。

也就是说：

- 模板文件描述了一部分结构
- 但很多关键行为还写在 CSS 和 Python 条件逻辑里
- 每做一个新设计，仍需要改具体实现

因此，必须引入独立的 Template Behavior Layer。

---

## 3. Template Behavior Layer 的职责

Template Behavior Layer 负责定义：

- 某类模板在给定输入条件下，应采用什么布局行为
- 各 region 内部应以什么模式组织内容
- 各种模式如何折叠、截断、切换、降级

它不负责：

- 背景生成
- 基础 region / slot contract 定义
- 美化风格的具体实现
- 最终渲染服务治理

一句话：

> region / slot contract 负责“骨架是什么”，
> behavior layer 负责“骨架怎么动”。

---

## 4. 行为层与现有架构的关系

当前 `poster2` 的基线不应被推翻。

Behavior Layer 应位于：

- template family / region matrix / slot contract 之上
- renderer runtime 之下

推荐关系如下：

1. Template Family / Template Metadata
2. Region Matrix / Slot Contract
3. **Template Behavior Layer**
4. Renderer Routing
5. Render Service Layer
6. Quality Guard / Geometry Evidence

也就是说：

- contract 定义结构边界
- behavior 定义结构行为模式
- renderer 负责执行行为

---

## 5. 首批应上浮的行为维度

建议不要一次性把所有行为都抽上来。

第一阶段只上浮最关键、最有收益的 mode。

## 5.1 `header_mode`

候选值示例：

- `identity_left_agent_right`
- `brand_block_two_line`
- `brand_only`

职责：

- 定义 header 内部 identity zone / agent zone 的关系
- 定义单行/双行/折叠规则
- 不涉及具体美化

## 5.2 `hero_mode`

候选值示例：

- `single_product`
- `primary_secondary_dual`
- `scenario_cover_product_contain`

职责：

- 定义 hero 区的主产品图模式
- 定义单图 / 双图关系
- 定义 scenario / product 的主次关系

## 5.3 `feature_mode`

候选值示例：

- `right_stack`
- `top_copy_band`
- `count_driven_callout_stack`

职责：

- 定义 feature 是右侧纵向列，还是 hero 顶部信息带
- 定义 1/2/3 项模式
- 定义 connector / box / truncation 行为

## 5.4 `bottom_mode`

候选值示例：

- `title_gallery_split`
- `title_only`
- `gallery_only`

职责：

- 定义底部是标题带与系列图区分离，还是只出现其一
- 定义 collapse 条件

## 5.5 `gallery_mode`

候选值示例：

- `strip_local_visible_only`
- `supporting_packshots`
- `grid_supporting`

职责：

- 定义 gallery 如何在底部 strip 内组织
- 定义最大数量、主次关系、溢出策略

---

## 6. 首轮实施建议

## 6.1 第一批只选 1~2 个 mode

建议从：

- `hero_mode`
- `feature_mode`

先开始。

原因：

- 它们对画面影响最大
- 当前实现中也最依赖 template-specific tuning
- 最能证明“模板行为可驱动”

## 6.2 首轮原则

第一轮上浮 behavior mode 时必须满足：

- 可见结果尽量不变
- diagnostics 不变
- deliverable 不变
- 不引入新的美化层耦合
- 不破坏当前 region / slot contract

也就是说：

> 第一轮的目标不是“把图变好看”，
> 而是“证明行为可以从实现层迁到协议层”。

---

## 7. 行为层的最小输出形式

建议第一轮先以 metadata / resolver 的方式存在，而不要直接引入复杂 DSL。

最小形式例如：

```json
{
  "behavior_modes": {
    "header_mode": "identity_left_agent_right",
    "hero_mode": "single_product",
    "feature_mode": "count_driven_callout_stack",
    "bottom_mode": "title_gallery_split",
    "gallery_mode": "strip_local_visible_only"
  }
}
```

然后通过一个 `behavior_resolver`：

- 读取 mode
- 解析为 renderer 可执行的行为配置
- 保持 diagnostics 可解释

---

## 8. 与两类模板家族的关系

Behavior Layer 必须从一开始就考虑两类模板家族，而不是只服务一个模板。

要求：

- mode 命名不能只绑死 `template_dual_v2`
- mode 应可在 A 类与 B 类模板之间复用或变体化
- family A / family B 应共享同一种行为层治理方式，而不是各写一套 renderer 条件逻辑

---

## 9. 不应做的事

### 9.1 不要把 behavior layer 做成 renderer-specific hack layer

行为层不应等于：

- Puppeteer-only 条件开关
- CSS-only 模式常量
- Python if/else 大集合

### 9.2 不要把 behavior layer 做成 editor-first widget config

行为层不是：

- widget tree
- page snapshot
- editable editor state

### 9.3 不要同时引入大规模美化

第一轮只证明：

- mode 能声明
- mode 能解析
- mode 能稳定驱动现有行为

---

## 10. 首轮成功标准

如果以下条件同时满足，就说明 Template Behavior Layer 第一轮成功：

1. 当前至少 1~2 个核心行为维度已上浮为声明式 mode
2. 可见结果基本不变
3. diagnostics / deliverable 不回归
4. renderer 代码中的 template-specific 分支有所减少
5. 行为决策开始由模板 metadata 驱动，而不是继续分散在 CSS / Python 条件里

---

## 11. 一句话结论

> Template Behavior Layer 的目标，不是让模板一下子变得更复杂，而是让当前已经验证过的版式行为从“代码扶着走”逐步升级为“模板协议自己驱动”。