# 模板家族 Region Matrix v1

## 1. 文档定位

本文档用于推动 poster2 的工程落地，先锁定两类模板家族的：

- mandatory regions
- collapsible regions
- region 级替代与补位规则
- 结构成立 / 结构失效的判断边界

本文档不讨论视觉 polish，也不讨论具体 CSS 或样式微调。

本文档的目标是：

> **先把模板家族的区域结构定成可执行的工程基线。**

---

## 2. 共同原则

### 2.1 先判断结构，再做布局

系统必须先判断 region 是否成立，再进入布局控制。不能在 region 未定义清楚时直接盲排。

### 2.2 mandatory region 不允许静默消失

mandatory region 如果缺失，必须触发以下之一：

- 判定模板结构失败
- 触发同家族降级模式
- 触发明确的 fallback
- 输出 degraded / incomplete_structure

不允许出现“mandatory region 实际消失但结果仍被当作成功”的情况。

### 2.3 collapsible region 只能按规则折叠

collapsible region 可以隐藏，但必须满足：

- 没有可绑定内容
- 或该 region 在当前 family mode 下被明确关闭
- 且折叠后不会破坏 mandatory region 的边界与阅读顺序

### 2.4 不允许跨 region 偷位

一个 region 折叠后，其他 region 只能按预定义规则扩展，不能无约束侵占新的版面。

### 2.5 产品主图属于硬约束

无论哪一类模板家族：

- `product_image` 对应的主产品区域都属于核心结构
- 不允许自动隐藏
- 不允许因布局压缩而变形

---

## 3. 共同 Region 语法

为便于模板家族共用协议，poster2 统一使用以下抽象语法：

- `branding_region`
- `hero_region`
- `supporting_visual_region`
- `proof_region`
- `conversion_region`
- `footer_region`

两类模板家族只是对这些抽象 region 做不同实例化。

---

## 4. 模板家族 A：营销讲解型（Campaign Explainer）

## 4.1 家族目标

该家族用于“先吸引，再解释，再带出系列感”的营销海报。

其核心阅读顺序是：

- 先品牌识别
- 再看主产品 / 场景
- 再看卖点
- 最后看大标题与系列产品条

---

## 4.2 Family A Region Matrix

### A1. `header_region`

状态：**mandatory**

职责：

- 承载品牌识别
- 承载品牌名 / logo
- 可选承载 agent pill / 渠道标识

最小成立条件：

- 至少存在 `brand_logo_slot` 或 `brand_text_slot` 之一

禁止：

- 静默折叠
- 因 agent pill 过长导致整个 header 失效

折叠策略：

- `agent_pill_slot` 可折叠
- `brand_logo_slot` 与 `brand_text_slot` 至少保留一项

失效判定：

- logo 与品牌文字同时缺失
- header 完全不可见

### A2. `hero_region`

状态：**mandatory wrapper**

职责：

- 承载主视觉组合
- 管理场景区、产品区、卖点区之间的结构关系

组成：

- `scenario_region`
- `product_region`
- `feature_region`

`hero_region` 本身不得折叠。

### A3. `product_region`

状态：**mandatory**

职责：

- 承载主产品图
- 形成主视觉核心锚点

最小成立条件：

- 存在有效 `product_image`

禁止：

- 折叠
- 变形
- 被场景区或标题区替代

失效判定：

- 主产品图缺失
- 主产品图不可见
- 主产品图明显变形

### A4. `scenario_region`

状态：**collapsible / preferred**

职责：

- 提供场景氛围
- 与产品区形成双主视觉

可折叠条件：

- 没有有效 `scenario_image`
- 或当前运营模式关闭场景图

折叠后规则：

- `product_region` 可以在 `hero_region` 内扩展
- 不允许越过 `hero_region` 的既定边界
- 不允许侵入 `title_band_region`

失效不判整张模板失败，但应记录：

- `scenario_region.collapsed = true`

### A5. `feature_region`

状态：**collapsible**

职责：

- 承载卖点 callout / 引导线说明

可折叠条件：

- `features` 为空
- `feature_count = 0`

折叠后规则：

- 所有 connector 同时消失
- `product_region` 和 `scenario_region` 之间的主骨架保持不变
- 不允许出现 ghost connector / ghost box

### A6. `title_band_region`

状态：**mandatory**

职责：

- 承载标题 / 副标题 / slogan
- 形成海报的主要文案锚点

最小成立条件：

- 至少存在 `title_slot`

折叠策略：

- `subtitle_slot` 可折叠
- `title_slot` 不可折叠

失效判定：

- 没有 title
- title 漂移到非 title band 区域

### A7. `gallery_strip_region`

状态：**collapsible**

职责：

- 承载系列产品图 / packshot strip

可折叠条件：

- `gallery_images` 为空
- gallery 数量不足且当前模式不允许补位

折叠后规则：

- `title_band_region` 保持原有文案结构
- 不允许标题带整体塌缩为 gallery 的补位区

---

## 4.3 Family A 成功标准

判定 Family A 结构成立，至少要求：

- `header_region` 成立
- `hero_region` 成立
- `product_region` 成立
- `title_band_region` 成立

以下可接受为“结构成立但部分折叠”：

- `scenario_region` 折叠
- `feature_region` 折叠
- `gallery_strip_region` 折叠

以下应判为 `incomplete_structure`：

- `header_region` 失效
- `product_region` 失效
- `title_band_region` 失效
- `hero_region` 主骨架消失

---

## 5. 模板家族 B：产品图录型（Product Sheet / Product Story）

## 5.1 家族目标

该家族用于“先认产品，再读信息，再促转化”的产品说明、图册与邮件详情型海报。

其核心阅读顺序是：

- 先品牌锚点
- 再看型号 / 参考信息
- 再看单品主图
- 再看参数 / 说明
- 最后看 CTA / footer

---

## 5.2 Family B Region Matrix

### B1. `brand_banner_region`

状态：**mandatory**

职责：

- 承载顶部品牌横幅 / 品牌锚点
- 建立图录式可信入口

最小成立条件：

- 至少存在 `brand_logo_slot` 或 `brand_banner_asset`

折叠策略：

- 不允许整体折叠
- 品牌文字可退化为 logo-only

失效判定：

- 品牌锚点完全缺失

### B2. `reference_region`

状态：**collapsible / preferred**

职责：

- 承载参考号、型号、系列信息

可折叠条件：

- 没有 reference code / model code

折叠后规则：

- 不允许影响 `hero_product_region` 的位置
- 上方留白重新归并给标题或主图区上边距

### B3. `hero_product_region`

状态：**mandatory**

职责：

- 承载单品主图或主推组合图
- 形成整个产品图录页的核心视觉锚点

最小成立条件：

- 存在有效 `product_image`

禁止：

- 折叠
- 变形
- 被 copy / spec 区替代

失效判定：

- 主图缺失
- 主图严重变形
- 主图不可见

### B4. `supporting_visual_region`

状态：**collapsible**

职责：

- 承载配件图、辅图、局部细节图、第二主图

可折叠条件：

- 没有 supporting images
- 当前 family mode 为单主图模式

折叠后规则：

- 不影响 `hero_product_region`
- 不影响 `spec_region` 与 `copy_region` 的顺序

### B5. `spec_region`

状态：**conditional mandatory**

职责：

- 承载尺寸、功率、型号、参数等结构化信息

最小成立条件：

- 若 family mode = product_sheet，则必须存在
- 若 family mode = product_story，则可由 `copy_region` 替代为主信息区

折叠策略：

- 仅在 product_story 模式且 copy 信息完整时允许折叠

### B6. `copy_region`

状态：**conditional mandatory**

职责：

- 承载说明文案、卖点描述、双语产品说明等

最小成立条件：

- 若 family mode = product_story，则必须存在
- 若 family mode = product_sheet，则可弱化或折叠

折叠策略：

- 在纯参数型产品页中允许折叠

### B7. `cta_region`

状态：**collapsible**

职责：

- 承载“联系我们” / CTA / 联系方式

可折叠条件：

- 当前页面定位不是转化页
- 无 CTA 文案与联系信息

折叠后规则：

- 不得影响品牌 footer
- 不得导致 spec / copy 区越界下沉

### B8. `footer_brand_region`

状态：**collapsible / preferred**

职责：

- 承载品牌 footer、次级品牌锚点、联系收束区

可折叠条件：

- 当前页面不要求 footer 品牌区
- 已有足够强的上方品牌锚点且页面为短页模式

折叠后规则：

- 页面底部必须仍保留收束感，不得出现无解释空白

---

## 5.3 Family B 成功标准

判定 Family B 结构成立，至少要求：

- `brand_banner_region` 成立
- `hero_product_region` 成立
- `spec_region` 或 `copy_region` 至少成立一个核心信息区

以下可接受为“结构成立但部分折叠”：

- `reference_region` 折叠
- `supporting_visual_region` 折叠
- `cta_region` 折叠
- `footer_brand_region` 折叠

以下应判为 `incomplete_structure`：

- `brand_banner_region` 失效
- `hero_product_region` 失效
- `spec_region` 与 `copy_region` 同时缺失

---

## 6. 工程落地时的直接使用方式

本清单在工程侧至少应直接转化为以下对象：

### 6.1 Region Presence Matrix

为每个模板家族输出：

- mandatory regions
- collapsible regions
- conditional mandatory regions
- forbidden missing regions

### 6.2 Structure Completeness Check

渲染后必须基于本清单判断：

- `structure_complete = true/false`
- `incomplete_reason`
- `collapsed_regions`
- `missing_mandatory_regions`

### 6.3 Renderer Fallback Policy

fallback 不能只判断引擎是否成功，还要判断：

- fallback 后是否仍满足本清单
- 若不满足，则标记为 `degraded + incomplete_structure`

---

## 7. 一句话结论

> **模板家族 A / B 的工程落地，不是先调样式，而是先锁定 mandatory regions、collapsible regions 与结构成立条件，让模板从“会渲染”升级为“有结构契约地渲染”。**
