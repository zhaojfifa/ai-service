# 海报可控生成总体方案（目标研发文档）

## 1. 文档定位

本方案用于指导当前营销海报生成服务从“已恢复可运行”推进到“可控、可复现、可运营、可扩展”的目标状态。

适用范围：
- Render 部署的 FastAPI 后端
- GitHub Pages / Render 托管的前端页面
- Vertex / Firefly 驱动的背景与素材生成
- R2/S3 对象存储
- 当前 KitPoster / Poster 2.0 模板体系

本方案的核心原则是：

**AI 只负责素材与局部背景，结构与排版必须由程序确定性控制。**

---

## 2. 当前状态判断

### 2.1 已经成立的部分

当前系统已经完成以下基础闭环：

1. Render 服务可成功部署并通过健康检查。
2. GCP 凭据可通过 `GCP_KEY_B64` 加载，Vertex 主链路可调用。
3. R2/S3 对象存储已打通，图片产物可上传并返回 URL/Key。
4. 前端 Stage1 / Stage2 / Stage3 三段式流程已经建立。
5. 海报生成接口已经能够返回成功结果，并落盘到对象存储。
6. 锁版模板、spec、mask、prompt presets、前后端协同机制已具备基本雏形。

### 2.2 当前核心问题

当前“服务健康但海报质量不稳定”的根因，不是部署层，而是生成控制层仍未完全收口：

1. **结构保护不够硬**：编辑区边界曾过宽，AI 会污染不应编辑的区域。
2. **字体与排版风险仍需制度化治理**：CJK 字体问题会直接导致测量失真和“要素飘”。
3. **Prompt 与 preset 仍偏开放**：厨房 / 场景类素材容易引入伪文字、UI、标牌、面板数字、反光干扰。
4. **后处理保护层需要标准化**：编辑后必须强制覆盖锁版前景层，不能依赖模型“听话”。
5. **模板协议仍偏弱**：目前 spec 更像配置文件，还不是完整的模板 DSL。
6. **版式引擎长期能力不足**：Pillow 可支撑当前阶段，但对复杂文字排版、CJK 测量、SVG callout、模板快速演进仍不如浏览器渲染稳定。

### 2.3 架构结论

当前主架构方向是正确的：

- **保留自研后端生成链路**
- **保留锁版模板 + mask + spec + 后端合成的范式**
- **不采用 Adobe Express Headless 作为后端生成主链路**
- **不以 Bannerbear / Templated / Canva 取代当前动态锚点模板体系**

结论：

**短期继续收口现有自研链路；中期升级前景排版引擎；长期形成双引擎体系。**

---

## 3. 目标定义

### 3.1 总目标

建设一套“海报可控生成系统”，满足以下能力：

1. **可控**：Logo、标题、功能点、引导线、CTA、底部小图位置稳定，不被模型篡改。
2. **可复现**：相同输入、相同模板、相同 seed 下，输出结果可预测。
3. **可运营**：运营人员可在不改代码前提下完成模板切换、素材输入、预设选择、结果复核。
4. **可扩展**：支持更多模板、更多产品类目、更多渠道尺寸。
5. **可回退**：编辑链路异常时，系统应自动降级到保守可交付模式。
6. **可观测**：可从日志和接口响应中判断当前是否走了 edit、fallback、preset fallback、gallery 补位等路径。

### 3.2 分阶段目标

#### 第一阶段：可控底线
目标：不乱、不飘、不脏、不误判。

#### 第二阶段：稳定可运营
目标：不同产品和操作员下，也能稳定得到 80 分以上海报。

#### 第三阶段：模板平台化
目标：模板协议化、前景渲染可视化、后端双引擎可切换。

---

## 4. 总体技术路线

## 4.1 架构分层

### L1. 模板结构控制层（程序主控）
负责：
- 版式模板
- 文案槽位
- Logo / 品牌 / 代理位
- 产品框
- 功能点文字与 leader line
- CTA pill
- 底部 gallery 区
- 字体、字号、颜色、对齐、缩放、裁切规则

要求：
- 不能交给 AI 自由生成
- 必须由程序基于模板协议决定

### L2. 内容注入层（AI 辅助）
负责：
- 场景背景
- 局部背景补光 / 氛围延展
- 产品 packshot 生成
- 系列图槽位补图
- 有明确边界的 inpainting / insert

要求：
- 只能在明确的 mask 内工作
- 不得修改文字、Logo、功能点、产品边缘

### L3. 合成与输出层（程序主控）
负责：
- 锁版底图与前景层叠加
- 编辑区掩膜管理
- 最终 PNG 输出
- R2 上传
- 返回结构化调试信息

---

## 5. 技术选型决策

## 5.1 当前生产主引擎

### 方案 A：Pillow + 锁版模板 + mask + spec

定位：
- 当前生产主引擎
- 低成本、低风险、可继续迭代

保留理由：
- 已与现有仓库深度集成
- 已支持 JSON spec、模板、前景合成、对象存储链路
- 动态锚点 / 功能点 / leader line 能力已存在
- 修复成本远低于替换成本

结论：
- **继续保留为当前生产主引擎与 fallback 引擎**

## 5.2 中期增强主引擎

### 方案 B：HTML/CSS + Puppeteer

定位：
- 作为前景排版层升级方案
- 先从一套主模板试点

适用原因：
- 浏览器原生处理 CJK 字体与文本测量
- CSS 负责布局，SVG 负责 callout 和 leader line
- 模板改动从 Python 坐标改为 HTML/CSS
- 设计协作效率更高

结论：
- **作为阶段二 / 三的主升级方向**
- **不直接替换 Pillow，而是与之双引擎并存**

## 5.3 作为素材能力的 AI 供应商

### Vertex / Firefly

定位：
- 用于背景生成、局部编辑、素材生成
- 不用于海报结构排版

结论：
- Vertex 保持当前主链路
- Firefly 保留为专业背景增强或长期专业模板运营能力

## 5.4 明确排除项

### Adobe Express Headless

排除原因：
- 不具备真正服务端 REST 自动化能力
- 更适合浏览器嵌入设计器，而不是当前后端生成管线

### Bannerbear / Templated / Placid / Canva

结论：
- 可用于“固定版式 + 简单动态文字图片”的轻模板场景
- 不适合当前需要动态锚点、leader line、局部保护与结构化海报的主场景
- 可作为未来轻量渠道图的旁路方案，不作为主引擎

---

## 6. 目标架构

```text
前端（GitHub Pages / Render Static）
  ├─ Stage1: 素材输入 + 模板预览
  ├─ Stage2: Prompt / Preset / 生成控制
  └─ Stage3: 邮件与交付

FastAPI 后端（Render）
  ├─ Config / Env Resolve
  ├─ Template Registry
  ├─ Poster State Machine
  ├─ Renderer Engine
  │    ├─ Pillow Renderer（当前生产）
  │    └─ Puppeteer Renderer（中期增强）
  ├─ Edit Orchestrator
  │    ├─ Vertex Edit / Generate
  │    └─ Firefly Background (optional)
  ├─ Quality Guard
  │    ├─ Mask Guard
  │    ├─ Foreground Reapply
  │    ├─ Prompt Hardening
  │    └─ Score / Warnings
  └─ Storage Adapter (R2/S3)
```

---

## 7. 研发策略

## 7.1 第一原则：结构绝不交给 AI

以下元素必须是确定性渲染：
- 品牌名 / Logo
- 代理名 / CTA
- 标题 / 副标题
- 功能点文字
- leader line / callout dots
- 产品主体位置框
- 底部 gallery 框与数量

## 7.2 第二原则：AI 只工作在纯背景区

对 AI 的要求：
- 仅允许在 mask 透明区域内工作
- 编辑区必须尽量收紧
- 文字区、标题区、功能点区、产品区必须设置 carve-out margin
- 编辑后必须统一叠加完整锁版前景层

## 7.3 第三原则：所有降级必须显式可见

每次生成都应明确返回：
- 是否走 edit
- 是否走 fallback
- 是否使用 scenario fallback
- 是否触发 gallery 补位
- 是否发生 prompt preset fallback
- 当前 renderer engine 是 Pillow 还是 Puppeteer

---

## 8. P0：可控底线方案（立即执行）

目标：先把“可控”站稳。

### 8.1 部署与环境固化

1. 统一健康检查：`/health` + `/healthz`
2. 固化 Render buildCommand：安装依赖 + 拉取字体
3. 统一 env 真值源，保留兼容别名，但明确 canonical names
4. 前端 backend base 与 localStorage 机制可视化
5. 对象存储只传 URL/Key，不再走内联 base64

### 8.2 字体治理

建立字体治理为硬性要求：
- 构建期确保 CJK 字体下载到 `app/assets/fonts`
- 启动日志明确输出字体加载状态
- CI / 启动检查中加入 FontRegistry 校验
- 若字体缺失，明确 warning，不允许静默回退

### 8.3 编辑区治理

当前编辑路径必须执行以下约束：
- editable zones 仅允许纯背景区
- gallery_strip 不作为默认可编辑区
- title / subtitle / logo / brand / agent / feature blocks 周围增加 carve-out 安全边界
- 产品主体周边设置保护 margin
- 编辑后强制 `_apply_locked_frame(...)` 或等效全前景回盖

### 8.4 Prompt 与 Preset 硬化

在 KitPoster edit 路径强制加入高优先级 negative bundle：

- no text
- no letters
- no typography
- no signage
- no labels
- no numbers
- no UI
- no screen content
- no captions
- no packaging text
- no watermark

并建立模板级 preset 白名单，避免高噪声厨房场景直接进入主模板。

### 8.5 数据默认值治理

修复以下业务层问题：
- `agent_name` 不得回退为 `channel`
- `gallery` 补位不得优先重复相同图片
- `default` 这类占位文案不得直接进入正式输出
- 标题 / 副标题必须分别有独立策略，不允许简单镜像复用

### 8.6 质量守护输出

每次生成返回中增加或标准化以下字段：
- renderer_engine
- edit_enabled
- edit_model
- fallback_used
- degraded
- warnings
- mask_profile
- preset_bundle
- font_profile

---

## 9. P1：模板协议化方案（1~2 周）

目标：让模板从“配置文件”升级为“模板协议”。

### 9.1 建立 Template Spec 2.0

建议在现有 `spec.json` 上升级，新增以下字段：

- `text_slots`
  - max_lines
  - min_font_size
  - max_font_size
  - shrink_strategy
  - overflow_strategy
  - letter_spacing
  - line_height

- `protected_regions`
  - zone_id
  - bbox
  - carve_out_margin
  - protected_reason

- `editable_regions`
  - zone_id
  - mask_policy
  - allowed_providers
  - provider_modes

- `gallery_rules`
  - required_count
  - duplication_policy
  - fallback_order

- `prompt_bundles`
  - scenario
  - hero
  - pack
  - global_negative

- `quality_policy`
  - dirty_text_risk
  - layout_completeness
  - duplicate_gallery_penalty

### 9.2 模板注册中心

新增 Template Registry：
- 模板元数据注册
- 模板版本控制
- 模板状态（draft / prod / deprecated）
- 模板适用类目
- 预设白名单

### 9.3 前端模板感知

Stage1 / Stage2 应完全模板驱动：
- 素材槽位由模板声明
- Prompt Inspector 由模板驱动
- 每个模板显示其风险提示与适用场景

---

## 10. P2：双引擎渲染方案（2~4 周）

目标：建立 Pillow + Puppeteer 双引擎。

## 10.1 渲染职责拆分

### Pillow
- 现阶段生产 fallback
- 轻量保底
- 快速服务端渲染

### Puppeteer
- 主模板精控版式
- CJK 文本强控制
- SVG callout / leader line
- 更高设计迭代效率

## 10.2 迁移策略

第一步只迁移一套主模板，例如：`template_dual`

迁移方式：
1. 将锁版前景转为 HTML 模板
2. 文本、产品图、功能点改为 HTML/CSS 渲染
3. leader line 改为 SVG
4. 导出 `foreground.png`
5. 保持背景生成与最终合成链路不变

## 10.3 引擎路由

后端可按模板或 feature flag 切换：
- `renderer_engine = pillow`
- `renderer_engine = puppeteer`

输出层保持统一接口，不影响前端调用。

---

## 11. 质量评估体系

为实现“可控生成”，必须引入结构化质量评估。

### 11.1 质量维度

1. **结构完整性**
   - 所有关键元素是否存在
   - 是否被遮挡
   - 是否越界

2. **文字清洁度**
   - 是否出现伪文字 / 脏字 / UI 幻觉
   - 是否出现 watermark / logo 污染

3. **模板一致性**
   - 是否保持模板规范
   - 标题 / CTA / callout 是否符合规则

4. **素材一致性**
   - 产品图是否匹配
   - gallery 是否重复
   - 场景是否符合类目

5. **运营可交付性**
   - 是否可直接投放
   - 是否需要人工修图
   - 风险等级

### 11.2 质量输出策略

每次生成输出评分：
- score_structure
- score_cleanliness
- score_layout
- score_asset_fit
- delivery_grade

并配合 warnings 解释风险来源。

---

## 12. 工程模块规划

建议形成以下目标模块：

### 12.1 Poster Orchestrator
负责：
- 输入规范化
- 模板解析
- provider 调度
- run state 记录

### 12.2 Template Engine
负责：
- 模板注册
- spec 解析
- 保护区与编辑区计算
- 槽位规则

### 12.3 Render Engine
负责：
- Pillow 路径
- Puppeteer 路径
- 统一 foreground 输出

### 12.4 Edit Guard
负责：
- mask 收紧
- carve-out 应用
- provider capability 检查
- negative bundle 注入
- fallback 管理

### 12.5 Quality Guard
负责：
- 后处理回盖
- 质量打分
- warnings
- debug trace

### 12.6 Asset Policy
负责：
- gallery 去重
- scenario 白名单
- 主产品图要求
- 输入合法性校验

---

## 13. 工具与平台决策

## 13.1 主工具
- FastAPI：后端 API 编排
- Render：当前 Web Service 托管
- R2/S3：图片对象存储
- Vertex：主图生图 / 编辑
- Pillow：当前生产前景渲染
- GitHub Pages：当前前端托管

## 13.2 中期工具
- Puppeteer / Playwright：前景 HTML 渲染
- SVG：callout 与 line 系统
- 模板 registry：模板版本管理

## 13.3 长期可选工具
- Firefly / Photoshop API：专业模板运营
- 轻量 SaaS（Bannerbear 等）：旁路简单模板图

---

## 14. 里程碑路线图

## M1：恢复可控底线（1~3 天）

交付：
- 字体问题收口
- health / healthz 双通
- env 真值源清晰
- edit 区域收紧
- negative prompt 加固
- 锁版前景回盖可验证
- agent_name / gallery / default 文案问题修复

验收：
- 主模板连续生成 10 张无乱码、无脏字、无明显错位

## M2：模板协议化（3~7 天）

交付：
- spec 2.0
- Template Registry
- Quality Policy 输出
- 前端模板驱动增强

验收：
- 同一模板适配至少 3 种产品场景
- 输出结构风险可解释

## M3：Puppeteer 试点（1~2 周）

交付：
- `template_dual` HTML 版
- Pillow / Puppeteer 双引擎切换
- 统一输出接口

验收：
- CJK 排版稳定
- callout 与 CTA 精度优于 Pillow 路径

## M4：模板平台化（2~4 周）

交付：
- 多模板注册
- 多渠道尺寸支持
- 模板版本与发布流程
- 运营工作流稳定化

---

## 15. 不做事项

以下事项当前阶段不建议优先投入：

1. 不将 Adobe Express Headless 作为主链路替代。
2. 不以商业模板 SaaS 替代现有动态锚点海报体系。
3. 不让 AI 直接生成完整海报结构。
4. 不在部署恢复阶段同步做大规模架构重构。
5. 不在未完成模板协议化前盲目扩展模板数量。

---

## 16. 执行建议

本方案建议作为仓库中的目标研发文档，建议文件名：

`docs/architecture/POSTER_CONTROLLABLE_GENERATION_PLAN.md`

配套建议新增以下文档：
- `docs/architecture/TEMPLATE_SPEC_2_0.md`
- `docs/ops/POSTER_RUNTIME_VERIFICATION.md`
- `docs/quality/POSTER_QUALITY_SCORING.md`
- `docs/roadmap/POSTER_RENDERER_MIGRATION.md`

---

## 17. 最终结论

当前项目的正确方向不是“换平台”，而是：

**短期继续收口现有自研链路，确保 AI 只能碰背景；中期把前景排版层升级到浏览器渲染；长期形成模板协议 + 双引擎 + 质量守护的海报可控生成平台。**

这条路线兼顾：
- 当前恢复速度
- 结构可控性
- 研发成本
- 长期扩展性
- 运营可交付性

