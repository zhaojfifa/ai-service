# Beautification Layer 计划 v1

## 1. 文档定位

本文档用于定义 `poster2` 下一阶段新增的 **Beautification Layer**。

其目标不是“让海报立刻更花哨”，而是：

> 在不破坏已经验证过的 structure contract 与 behavior contract 的前提下，
> 给现有 shell 与 text 增加可治理、可复用、可逐步增强的视觉表达能力。

---

## 2. 为什么现在需要独立的 Beautification Layer

当前阶段已经证明：

- 结构可以控制
- 内容可以控制
- 结果可以复现
- deliverable / diagnostics 语义成立

但当前尚未证明：

- 结果可以在不破坏 contract 的前提下稳定变美
- 样式能力可以从局部 CSS 调整，上升为系统级、可复用的审美层

这意味着：

> 当前 poster2 的“结构控制架构”已经成立，
> 但“视觉表达架构”还没有独立出来。

因此，需要新增 Beautification Layer。

---

## 3. Beautification Layer 的职责

Beautification Layer 负责：

- 给现有 shell 提供 surface/border/shadow/accent 等视觉层
- 给文本提供 emphasis / hierarchy / text effect 词汇
- 在不改 geometry 的情况下提升视觉成熟度
- 为后续多模板家族提供可复用的美化 vocabulary

Beautification Layer 不负责：

- 修改 region geometry
- 替代 behavior layer
- 修补 contract 失败
- 用视觉方式掩盖结构问题

一句话：

> 结构层负责“边界正确”，
> 行为层负责“行为正确”，
> 美化层负责“表达更好”。

---

## 4. 与现有架构的关系

Beautification Layer 必须建立在以下前提上：

1. Region / Slot contract 已经成立
2. Behavior modes 已经明确或至少开始上浮
3. deliverable / diagnostics 不被破坏

因此它应位于：

- Structure Layer / Behavior Layer 之后
- Render Service Layer 之前（或作为 renderer 消费的 style token）

推荐关系：

1. Template Family / Metadata
2. Region Matrix / Slot Contract
3. Template Behavior Layer
4. **Beautification Layer**
5. Renderer Routing / Render Service Layer
6. Geometry / Evidence Layer

---

## 5. 当前最小美化目标

当前阶段不要直接追求“完整风格系统”，而应先证明：

> 在不改 region geometry 的前提下，
> 可以通过独立 beauty tokens 提升视觉质量。

这意味着第一轮美化只能作用于：

- shell 外观
- text emphasis
- 轻量 accent

不能作用于：

- 布局结构
- slot 几何关系
- region 位置关系

---

## 6. 最小 beauty token families

建议第一轮至少定义以下 token families。

## 6.1 `shell_surface`

职责：

- 定义壳层底色/透明度/材质感
- 作用对象：
  - header banner
  - scenario shell
  - product shell
  - title band shell
  - gallery strip shell

示例语义：

- `solid_soft`
- `glass_light`
- `panel_clean`
- `panel_dark_soft`

## 6.2 `shell_border`

职责：

- 定义边框存在与强度
- 定义分隔感与精细度

示例语义：

- `none`
- `soft_line`
- `clean_frame`

## 6.3 `shell_shadow`

职责：

- 定义壳层阴影深度
- 增加层次，但不抢结构

示例语义：

- `none`
- `soft`
- `medium`

## 6.4 `accent_tone`

职责：

- 定义当前模板的强调色系
- 作用在：
  - feature connector
  - 小图边缘强调
  - 局部高亮文本

示例语义：

- `warm_red`
- `brand_gold`
- `cool_blue`

## 6.5 `text_emphasis`

职责：

- 定义文本层级表达
- 作用对象：
  - brand
  - title
  - subtitle
  - feature text
  - agent text

示例语义：

- `hero_title`
- `secondary_caption`
- `support_label`
- `small_meta`

---

## 7. 首轮作用范围

第一轮 Beautification Layer 不应该面向所有对象，而应只覆盖当前已验证稳定的对象。

### 7.1 Header banner

允许增强：

- banner surface
- banner border
- text hierarchy
- logo 与 brand 的轻量视觉关系

不允许改变：

- banner 两区 contract
- identity zone / agent zone 几何关系

### 7.2 Scenario shell / Product shell

允许增强：

- shell surface
- shell border
- shell shadow

不允许改变：

- hero/product geometry

## 8. 当前实现边界

当前工程线已经有最小 beauty token schema 与 resolver 接口，但本阶段判断仍然成立：

- 当前已证明 token 可以被 renderer 消费
- 当前还没有完成 beauty preset 的可复用扩展闭环
- 当前也还没有完成 Pillow 对 shell/token 的最小语义对齐

因此当前文档边界应保持清晰：

- behavior layer 进展不等于 beautification layer 已成熟
- 任何 shell/text 改动都必须继续服从现有 geometry
- 不允许把局部 CSS 调整描述成 beautification architecture 完成
- product non-distortion rule
- scenario/product peer relationship

### 7.3 Title band shell

允许增强：

- 文字层级
- surface/border/shadow
- title emphasis

不允许改变：

- title / subtitle line budget
- title band 高度 contract

### 7.4 Gallery strip shell

允许增强：

- strip surface
- strip border
- supporting image frames

不允许改变：

- strip visibility rules
- item count behavior
- title/gallery split contract

---

## 8. 首轮不应做的事

### 8.1 不要把美化层做成“大改样式”

第一轮不是重做整套品牌视觉，也不是更换大主题。

### 8.2 不要用美化层去修 behavior 问题

例如：

- 不要用阴影去掩盖错位
- 不要用遮罩去掩盖内容越界
- 不要用背景渐变去掩盖 region 关系不稳

### 8.3 不要引入 editor-style widget effects

`poster-design` 的很多效果词汇值得借鉴，但不能直接把整套 widget 配置搬过来。

我们要的是：

- beauty tokens
n- effect presets
- style vocabulary

而不是 editor-first effect state。

---

## 9. 首轮实施建议

建议第一轮只做最小可行验证：

### 步骤 1：新增 beauty token schema

最小结构例如：

```json
{
  "beauty_tokens": {
    "shell_surface": "panel_clean",
    "shell_border": "soft_line",
    "shell_shadow": "soft",
    "accent_tone": "warm_red",
    "text_emphasis": {
      "title": "hero_title",
      "subtitle": "secondary_caption",
      "agent": "small_meta"
    }
  }
}
```

### 步骤 2：仅作用于 shell 和 text

不改 geometry，只改：

- fill
- border
- shadow
- hierarchy
- text emphasis

### 步骤 3：保持 diagnostics 不变

美化层第一轮不应引入新的 deliverable semantics。

### 步骤 4：选择一个模板做基线验证

建议先在：

- `template_dual_v2`

上验证。

---

## 10. 首轮成功标准

如果以下条件同时满足，则可判定 Beautification Layer 第一轮成功：

1. 已有 shell 可以通过独立 beauty tokens 改善视觉成熟度
2. region geometry 不变
3. behavior modes 不变
4. deliverable / diagnostics 不回归
5. 结果明显更整洁、更成熟，但仍可解释、可复现

---

## 11. 后续扩展方向

在第一轮验证成功后，后续可逐步扩展：

- richer text effect presets
- shell tone families by template family
- gallery item frame styles
- scenario/product emphasis presets
- template-family-specific beautification profiles

但这些都必须在：

- Structure Layer 稳定
- Behavior Layer 初步成立

之后再做。

---

## 12. 一句话结论

> Beautification Layer 的目标，不是让当前模板立刻“更花”，而是在不破坏 contract-first 架构的前提下，让现有 shell 和 text 拥有可治理、可复用、可逐步增强的视觉表达能力。
