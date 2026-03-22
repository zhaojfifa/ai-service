# 海报可控生成研发目标方案

## 1. 文档目的

本文档作为当前营销海报生成能力的目标研发基线，用于统一架构、产品、研发与运营的判断口径。

核心目标不是“生成一张看起来还不错的图”，而是构建一条**可控、可复现、可运营、可评估、可扩展**的海报生成产线。

---

## 2. 当前状态判断

当前系统已经完成部署恢复，主链路具备以下基础能力：

- Render 后端已可稳定启动，健康检查可通过。
- Vertex 生成链路已可调用，R2 对象存储已可读写。
- Stage2 海报生成已可返回成图 URL。
- KitPoster 编辑链路已从完全 fallback，推进到可调用 edit path 的阶段。
- 现有模板体系已具备 `template + spec + mask + presets + renderer/composer` 的基础骨架。

但当前结果仍未达到“可控生成”标准，问题集中在以下四类：

1. **结构保护不足**  
   AI 仍可能污染标题、副标题、功能点、代理名、底部缩略图区附近区域。

2. **版式引擎稳定性不足**  
   Pillow 路径在字体、文本测量、CJK 渲染、自动缩放方面仍有不稳定性。

3. **内容注入边界不足**  
   编辑 mask 过宽、负向词不足、场景 preset 过开放时，容易出现伪文字、标牌、UI、噪声场景。

4. **运营数据与模板协议不足**  
   `agent_name -> email`、gallery 重复补位、标题/副标题复用等问题，会放大“成图不专业”的感受。

---

## 3. 总体研发目标

### 3.1 总目标

建立一套“结构由程序控制、内容由 AI 辅助、最终像素由后端合成”的营销海报生成系统。

### 3.2 分目标

#### G1. 结构可控
Logo、品牌名、代理名、标题、副标题、功能点、引导线、产品位、缩略图区必须由程序确定性控制，禁止由模型自由生成。

#### G2. 内容可控
AI 仅用于：
- 局部背景补足
- 场景图/槽位图生成
- 产品图衍生素材生成

AI 不得直接决定：
- 文字内容
- 文本位置
- 结构元素位置
- 品牌与 CTA 位置

#### G3. 结果可复现
相同输入 + 相同 seed + 相同模板版本，应可稳定复现同等级结果。

#### G4. 质量可评估
每次成图必须输出可观测指标与告警，包括：
- 是否走 fallback
- 是否走 edit path
- mask 覆盖区域
- 文本区污染风险
- gallery 是否重复补位
- 模板结构完整性

#### G5. 方案可演进
短期保留 Pillow 主路径；中期引入 Puppeteer 作为高可控前景层引擎；长期保留双引擎并存能力。

---

## 4. 核心架构原则

## 4.1 三层架构

### A. 模板结构控制层
负责：
- 模板坐标
- 文本槽位
- 字号/行数/缩放策略
- callout / leader line
- 保护区 / carve-out
- 图层顺序
- 模板版本与协议

该层必须**100% 程序控制**。

### B. 内容注入层
负责：
- 场景背景生成或补足
- 产品衍生图
- 底部 packshot
- 局部润色

该层由 AI 辅助，但必须被 mask、preset、prompt、negative prompt、保护区严格约束。

### C. 最终合成层
负责：
- 结构层与内容层合成
- 编辑后重叠完整锁版前景
- 输出最终 poster png/jpg
- 上传 R2 并输出 key/url

该层必须由后端确定性完成。

---

## 5. 工具与技术选型决策

## 5.1 当前主方案：Pillow + Vertex + R2

短期继续以以下组合为生产主路径：

- **后端**：FastAPI / Render
- **对象存储**：Cloudflare R2
- **生成能力**：Vertex Imagen
- **前景渲染**：Pillow renderer
- **模板协议**：template + spec + mask + presets
- **前端**：GitHub Pages / 静态页面

选择理由：

- 当前代码与部署已基本可用。
- 结构控制已在现有体系内成立。
- 改造成本最低，适合快速收口。
- 与现有运营流程兼容。

## 5.2 中期增强方案：HTML/CSS + Puppeteer

中期将新增 Puppeteer 前景渲染路径，承担：
- 文本排版
- SVG 引导线
- CTA pill
- 动态锚点
- 更稳定的 CJK 字体渲染

该方案不立即替换 Pillow，而是与 Pillow 双引擎并存。

## 5.3 不作为主路径的方案

以下方案不作为当前主链路：

- Adobe Express Headless：不适合作为服务端自动化海报生成主引擎
- Bannerbear / Templated / Placid：可作为固定版式商业替代，但不适合当前动态锚点与结构控制要求
- Firefly/Photoshop API：可作为长期专业设计运营增强链路，但不作为当前恢复主线

---

## 6. 目标架构图（逻辑）

```text
Operator Input / Frontend
    ↓
Poster Request Builder
    ↓
Template Protocol Resolver
    ├─ template metadata
    ├─ slot rules
    ├─ typography rules
    ├─ protection zones
    └─ allowed presets
    ↓
Content Injection Orchestrator
    ├─ scenario image
    ├─ product image
    ├─ gallery packshots
    └─ prompt bundle / negative bundle
    ↓
Render Engine
    ├─ Pillow foreground renderer (current)
    └─ Puppeteer foreground renderer (future)
    ↓
Edit / Compose Engine
    ├─ mask generation
    ├─ protected-zone carve-out
    ├─ Vertex edit or fallback
    └─ re-apply locked foreground
    ↓
Quality Guard
    ├─ degraded / fallback flags
    ├─ duplicate gallery detection
    ├─ text pollution detection
    └─ structure completeness checks
    ↓
R2 Upload + URL Output
```

---

## 7. 阶段路线图

## 7.1 P0：建立“可控底线”

目标：先做到“不乱、不脏、不被 AI 篡改”。

### P0 必做项

1. 固化 Render 字体安装，确保 CJK 字体稳定存在。
2. 将 edit mask 收紧到纯背景区，禁止波及标题、副标题、callout、gallery、logo、agent。
3. 对所有文本/结构元素增加 protection zone 与 carve-out margin。
4. 强化 negative prompt，抑制：
   - text
   - letters
   - typography
   - signage
   - labels
   - numbers
   - UI
   - screen content
   - captions
   - packaging text
   - watermark
5. 编辑后统一重叠完整 locked foreground。
6. 修正默认数据回退：
   - 禁止 `agent_name=email`
   - 避免 gallery 重复补位无提示
   - 区分 title/subtitle 默认值策略
7. 输出明确的 runtime 观测字段：
   - edit_enabled
   - edit_model
   - degraded
   - warnings
   - fallback_path
   - mask_debug_ref（调试环境）

### P0 验收标准

- 无乱码/伪文字污染正文区
- 无标题/副标题被编辑污染
- 无 gallery 覆盖正文
- 无 logo / brand / agent 被篡改
- 无 silent fallback
- 运营可通过日志判断生成路径

---

## 7.2 P1：模板协议化

目标：让模板从“图片+脚本”升级为“可维护协议”。

### P1 必做项

1. 升级 `spec.json` 为模板协议 2.0，至少包含：
   - slot 类型
   - 坐标
   - 最大行数
   - 最小字号
   - 自动缩放下限
   - overflow 策略
   - protection zone
   - allowed preset whitelist
   - gallery 填充策略
   - fallback 展示策略

2. 将 prompt bundle 与模板绑定：
   - 场景 preset
   - 产品 preset
   - packshot preset
   - 模板级 negative bundle

3. 建立模板版本治理：
   - template_id
   - template_version
   - renderer_mode
   - compatibility note

4. 建立质量评分：
   - 结构完整分
   - 文本污染风险分
   - 素材一致性分
   - 重复图警告
   - fallback 风险

### P1 验收标准

- 同模板不同素材的结果稳定性明显提高
- 模板行为可通过协议解释，而不是靠隐式代码猜测
- 新模板接入不需要复制大段逻辑

---

## 7.3 P2：Puppeteer 试点

目标：把“结构可控”进一步升级为“排版可控”。

### P2 必做项

1. 为 `template_dual` 建立 HTML/CSS/SVG 模板。
2. 在 renderer 层增加 Puppeteer 分支，不删除 Pillow。
3. 引入前景渲染接口抽象：
   - render_foreground_via_pillow()
   - render_foreground_via_puppeteer()
4. 对比两种前景层输出：
   - 字体稳定性
   - CJK 渲染
   - CTA 圆角
   - callout line 精度
   - 维护成本

### P2 验收标准

- Puppeteer 路径可产出同规格 foreground png
- 结构元素 100% 可控
- 文本排版优于 Pillow
- Render 资源占用可接受
- 可与 Pillow 并存切换

---

## 8. 工程模块目标

## 8.1 后端配置层
目标：
- 消除 env 平行命名歧义
- 输出 resolved runtime config
- 明确 generate/edit model 来源

## 8.2 模板解析层
目标：
- 统一模板协议
- 统一 protection zone 计算
- 统一 slot 数据校验

## 8.3 内容生成层
目标：
- 将 prompt bundle 与模板/类目绑定
- 收口 scenario/product/gallery 生成边界
- 输出可观测 trace

## 8.4 渲染层
目标：
- 前景渲染确定性
- 字体可控
- fallback 可观测
- 为 Puppeteer 留抽象接口

## 8.5 质量守护层
目标：
- 识别 degraded/fallback
- 检查 gallery 重复
- 检查文本污染风险
- 输出质量标签，供前端/运营展示

---

## 9. 运营与产品协同规则

1. 运营输入不等于模板直传。  
   所有输入必须经过模板协议与字段校验。

2. 运营可调的是“内容”，不是“结构”。  
   结构由模板控制，内容由运营选择 preset 和素材。

3. 任何 fallback 都必须显式展示。  
   不允许“看起来生成成功，实际上静默降级”。

4. 样张评价必须区分：
   - 架构问题
   - 模板问题
   - prompt 问题
   - 素材问题
   - 运维配置问题

---

## 10. 里程碑

### M1：P0 完成
结果：
- 当前 `template_dual` 达到可控底线
- 可连续生成若干张无明显污染样张
- 日志可判断路径与风险

### M2：P1 完成
结果：
- 模板协议 2.0 上线
- 模板接入与维护成本下降
- 质量问题可结构化定位

### M3：P2 完成
结果：
- Puppeteer 前景渲染试点通过
- 形成双引擎策略
- 为高可控商业模板奠定基础

---

## 11. 明确不做事项

当前阶段不做：

- 不将 Adobe Express 作为主后端生成引擎
- 不把 SaaS 模板平台作为主结构控制层
- 不让 AI 直接生成文字与结构元素
- 不在恢复期做大规模架构重写
- 不在未建立模板协议前扩大量产模板数量

---

## 12. 成功定义

当以下条件成立时，视为“海报可控生成”阶段性成功：

1. 相同模板在多组真实素材下，结构稳定，不漂移。
2. AI 不再污染标题、副标题、callout、brand、agent、gallery 区。
3. 日志与接口能明确说明是否 edit/fallback/degraded。
4. 运营能通过前端稳定使用，不依赖研发人工兜底。
5. 模板接入与调整可以通过协议和小范围代码改动完成。
6. 系统已具备迁移至 Puppeteer 的清晰边界，而不影响现有产线。
