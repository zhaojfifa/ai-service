# Codex 分步执行方案：海报可控生成

## 1. 任务目标

本执行方案用于指导 Codex 按阶段推进“海报可控生成”研发，不做大跃迁，不做宽泛重构，遵循：

- 先稳态
- 再协议化
- 后双引擎
- 每一步都必须可验证、可回滚、可提交

---

## 2. 执行总规则

1. **先审查，再改动**
   - 每个阶段先确认现状与真值源
   - 不凭猜测直接大改

2. **改动必须窄范围**
   - 单阶段只做该阶段目标
   - 不顺手改 unrelated code

3. **每阶段必须产出**
   - 代码补丁
   - markdown 说明
   - 验证清单
   - 回滚点

4. **优先保持兼容**
   - 优先 additive changes
   - 避免破坏现有前端和 API

5. **所有 fallback 必须可观测**
   - 生成成功不代表质量成功
   - 任何 degraded/fallback 都要明确记录

---

## 3. 阶段执行顺序

# Phase 0
**目标：把当前产线拉到“可控底线”**

# Phase 1
**目标：把模板行为协议化**

# Phase 2
**目标：在不替换 Pillow 的前提下，引入 Puppeteer 试点**

---

## 4. Phase 0：可控底线收口

### 4.1 目标

让当前 `template_dual` 在现有 Render + Vertex + R2 + Pillow 体系下，达到：

- 不污染文字区
- 不误伤锁版元素
- 不 silent fallback
- 不出现明显伪文字/UI/水印伪影
- 日志可解释生成路径

### 4.2 允许改动范围

允许改：
- render.yaml
- app/config.py
- app/main.py
- app/services/vertex_imagen3.py
- app/services/glibatree.py
- mask / carve-out / protection zone 相关代码
- prompt bundle / negative bundle 相关代码
- 字体与 renderer 配置
- 质量输出字段与 warning 生成

不允许改：
- 前端大重写
- 模板大重设计
- API 语义大变更
- 业务流程重构
- 将现有引擎整体替换为 Puppeteer

### 4.3 Phase 0 子任务

#### Task 0.1：配置与字体真值对齐
目标：
- 确认 Render 构建稳定安装 CJK 字体
- 确认 generate/edit model 的 resolved 值有明确日志
- 对齐 /health 与 /healthz

输出：
- `P0_CONFIG_AND_FONT_AUDIT.md`
- 最小补丁

验收：
- 启动日志明确显示 runtime config
- 日志无 font fallback warning
- `/health` `/healthz` 均 200

#### Task 0.2：收紧 edit mask
目标：
- editable 区域只保留纯背景
- 移除对 gallery_strip 等不稳定区域的开放
- 为 brand/logo/agent/product/title/subtitle/callouts 增加 margin carve-out

输出：
- `P0_MASK_HARDENING.md`
- 补丁

验收：
- 调试输出能证明可编辑区缩小
- 标题和副标题区域不再被污染

#### Task 0.3：强化 negative prompt
目标：
- 在 force_edit / kitposter edit 路径下自动附加强负向约束词
- 压制 text / signage / labels / UI / watermark / packaging text 幻觉

推荐负向词基线：
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

输出：
- `P0_NEGATIVE_PROMPT_HARDENING.md`

验收：
- 左侧场景区伪文字显著减少
- 无新增 UI/标牌样式噪声

#### Task 0.4：锁版前景重叠校验
目标：
- 明确编辑后是否完整重叠 locked foreground
- 如未完整重叠，则补全
- 确保品牌、标题、功能点、缩略图区前景层稳定恢复

输出：
- `P0_FOREGROUND_REAPPLY_REVIEW.md`

验收：
- edit 后标题/副标题/CTA/callout 不再被背景污染
- 叠层顺序在代码中清晰可读

#### Task 0.5：默认数据与质量告警收口
目标：
- 禁止 `agent_name=email`
- gallery 重复补位需显式 warning
- title/subtitle 默认策略分离
- 输出更清晰的 degraded / warnings / fallback_path

输出：
- `P0_OUTPUT_AND_WARNING_CLEANUP.md`

验收：
- API 响应能解释异常结果来源
- 前端可据此显示“本次为 fallback / 补位 / 重复图风险”

### 4.4 Phase 0 提交规则

每完成 1 个子任务：
- 单独 commit
- commit message 明确写 P0.x
- 不混入其他阶段内容

推荐提交粒度：
- `fix(poster): harden render config and health aliases`
- `fix(kitposter): tighten edit mask and protection carve-outs`
- `fix(kitposter): strengthen negative prompt for edit mode`
- `fix(kitposter): reapply locked foreground after edit`
- `fix(poster): clean fallback warnings and default field behavior`

### 4.5 Phase 0 停止条件

满足以下条件即可停：
- 当前模板连续多次生成，无明显文字污染
- warnings 可解释
- 日志可明确判断是否走 edit/fallback
- 运营可基于现有 UI 做稳定测试

未满足则不要进入 Phase 1。

---

## 5. Phase 1：模板协议化

### 5.1 目标

把当前模板体系从“若干 PNG + 若干脚本逻辑”升级为“模板协议 2.0”。

### 5.2 核心原则

- 不先追求更多模板
- 先让当前模板行为可解释
- 先把协议立住，再扩模板数量

### 5.3 Phase 1 子任务

#### Task 1.1：定义模板协议 2.0
为每个模板定义统一 schema，至少包含：

- template_id
- template_version
- renderer_mode
- slots
- typography rules
- protection zones
- allowed presets
- gallery fill strategy
- fallback behavior
- quality hints

输出：
- `docs/architecture/TEMPLATE_PROTOCOL_V2.md`
- 示例协议文件

#### Task 1.2：将 spec.json 行为显式化
目标：
- 把字号、行数、缩放下限、overflow 策略从隐式逻辑变为显式配置
- 将 protection zone 从代码常量移到协议

输出：
- `P1_SPEC_PROTOCOLIZATION.md`

#### Task 1.3：绑定 prompt bundle
目标：
- 场景 / 产品 / packshot 的 prompt 与 negative bundle 与模板绑定
- 模板限制运营可选 preset 范围

输出：
- `P1_PROMPT_BUNDLE_BINDING.md`

#### Task 1.4：增加质量评分输出
目标：
- 输出结构完整性分
- 文本污染风险分
- gallery 重复风险
- fallback 风险
- renderer path

输出：
- `P1_QUALITY_SCORING.md`

### 5.4 Phase 1 验收标准

- 当前模板行为可由协议解释
- 新模板可按协议接入
- prompt 与模板绑定，不再四散
- 输出结果可结构化评估

---

## 6. Phase 2：Puppeteer 前景渲染试点

### 6.1 目标

引入 Puppeteer，但不替换 Pillow。  
先让 `template_dual` 支持一个 HTML/CSS/SVG 前景层试点。

### 6.2 允许改动范围

允许改：
- renderer 抽象层
- 新增 HTML 模板目录
- 新增 Puppeteer 渲染工具
- render.yaml / buildCommand（仅与 Chromium 安装相关）

不允许改：
- 删除现有 Pillow 路径
- 改 API 主契约
- 一次迁移全部模板

### 6.3 Phase 2 子任务

#### Task 2.1：抽象前景渲染接口
目标：
- 从业务流程中拆出 foreground renderer 抽象
- 允许 `pillow` / `puppeteer` 双实现

输出：
- `P2_RENDERER_ABSTRACTION.md`

#### Task 2.2：建立 template_dual HTML 模板
目标：
- 用 HTML/CSS/SVG 实现：
  - 品牌条
  - CTA pill
  - 产品框
  - callout lines
  - 功能点
  - 标题 / 副标题
  - 底部缩略图区

输出：
- `P2_TEMPLATE_DUAL_HTML_PILOT.md`

#### Task 2.3：建立对比验证
目标：
- 对比 Pillow 与 Puppeteer foreground 输出
- 记录 CJK 稳定性、锚点精度、维护成本

输出：
- `P2_RENDER_COMPARISON.md`

### 6.4 Phase 2 验收标准

- Puppeteer 可生成与 Pillow 同尺寸前景层
- 与现有 compose 链路兼容
- 至少一套模板可试运行
- 可通过配置切换 renderer_mode

---

## 7. 每阶段统一验证模板

每个阶段都必须产出 `VERIFICATION_CHECKLIST.md`，至少包含：

1. 启动日志检查
2. `/health` `/healthz` 检查
3. 端到端海报生成检查
4. R2 URL 可访问检查
5. warnings / degraded 字段检查
6. 样张人工目检项：
   - 是否有伪文字
   - 是否污染标题区
   - 是否污染副标题区
   - 是否污染 CTA / brand / agent
   - 是否 gallery 重复
   - 是否功能点位置异常

---

## 8. 分支与提交建议

### 分支策略

- `fix/p0-config-font-health`
- `fix/p0-mask-hardening`
- `fix/p0-negative-prompt-hardening`
- `fix/p0-foreground-reapply`
- `fix/p0-warning-cleanup`
- `feat/p1-template-protocol-v2`
- `feat/p1-quality-scoring`
- `feat/p2-puppeteer-foreground-pilot`

### PR 原则

- 一个 PR 只做一类问题
- 文档与代码可同 PR
- 每个 PR 必须带验证截图或日志摘录
- 每个 PR 必须明确回滚方式

---

## 9. Codex 执行注意事项

1. 不要把“服务健康”误判为“成图质量健康”。
2. 不要把“看起来像 prompt 问题”的问题，绕过 mask/protection layer 真因。
3. 不要在 P0 阶段引入大范围架构重写。
4. 不要在 P2 之前删除 Pillow。
5. 不要把运营数据问题与模型问题混为一谈。
6. 如果结论无法从代码证明，必须明确写“不确定”。

---

## 10. 最终执行口令

Codex should execute in this order:

1. P0 config/font/health truth
2. P0 mask hardening
3. P0 negative prompt hardening
4. P0 locked foreground reapply verification
5. P0 warning/default-field cleanup
6. only after P0 passes, start P1 template protocol
7. only after P1 stabilizes, start P2 Puppeteer pilot

The default rule is:
**stabilize current pipeline first, protocolize second, dual-engine third.**
