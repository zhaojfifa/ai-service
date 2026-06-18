# CUISTANCE v1 · 运营 UI 与 Mockup 对齐状态 v1

Purpose: Realign /cuistance_trial.html with the approved commercial operator mockup (visual/product first), hiding engineering language.
Status: submitted (UI realigned + pushed; awaiting Owner visual review + remote deploy refresh).
Scope: Static UI alignment only. No backend API change, no send-behavior change, no renderer change, no new feature.
Source dependencies: docs/poster2/ui_mockups/cuistance_commercial_trial_v1/index.html (source of truth); v1 workbench endpoints (PR-1…PR-4).
Owner gate: Owner visual review + confirm trial service serves the refreshed page.
Next action: After deploy refresh, run the operator flow (test mode) on the remote page.

---

## 1. 文件变更 / Files changed

- `frontend/cuistance_trial.html`（重写，对齐 mockup）+ `docs/cuistance_trial.html`（镜像）
- `docs/poster2/cuistance_commercial_trial_operator_ui_alignment_status_v1.md`（本文）
- `docs/poster2/README.md`、`docs/poster2/current_branch_execution_log_v1.md`

**后端是否改动：否。** 仅静态页面；未改任何 `/api/*`、发送行为、renderer、部署配置。

## 2. 与批准 mockup 的对齐 / Alignment with the approved mockup

来源真值：`docs/poster2/ui_mockups/cuistance_commercial_trial_v1/index.html`。

| Mockup 方向 | 本页落地 |
|---|---|
| 顶部 header（品牌 + 标题 + 副标 + 语言切换 + 状态 chip）| ✅ CUISTANCE emblem + 商业试用工作台 + 副标语 + 中文/Français 切换 + 状态 chip |
| 3 步进度条 | ✅ 步骤 1 产品与素材 / 步骤 2 生成海报主体 / 步骤 3 邮件预览与测试发送（active/done 态）|
| 左输入 / 右预览两栏 + B2B SaaS 卡片 | ✅ 左：产品信息·素材与品牌·海报主体·测试发送；右：邮件预览·生成检查·测试发送已记录·进度·诊断 |
| 品牌横幅一等、与海报主体分离 | ✅ 右栏「品牌页眉」mini 预览 + 邮件 iframe；文案“最终邮件 = 品牌页眉 + 产品主体 + 正文 + 联系方式” |
| 简化产品页为有用选项（非失败） | ✅ 失败时琥珀提示“暂不可用，建议改用产品海报”，非红色报错 |
| 底部单行操作提示 | ✅ action-bar（步骤提示 + 仅内部测试声明）|

视觉风格：深色品牌 header、红色仅用于主操作/当前步、安静卡片、弱阴影、强留白 —— 与 mockup 一致；不再是 smoke runner。

## 3. 截图/视觉校验摘要 / Visual validation summary

本地（in-process）：`GET /cuistance_trial.html` → **200**；含 `商业试用工作台`、stepper `产品与素材`、诊断抽屉
`内部诊断`。结构 = header + 3 步 + 左输入/右预览卡片，与 mockup 层级一致（无原始 API/debug 布局）。

## 4. 语言策略 / Language strategy

- **默认中文**；右上 `中文 / Français` 切换；French 仅作次级标签/切换（`data-zh`/`data-fr`，JS textContent 交换）。
- 邮件预览内容本身为法语成品（发给法国客户），UI chrome 随切换。
- 无英文-only 运营界面；无混杂流程术语。

## 5. 主屏禁用工程术语检查 / Forbidden-term check

自动扫描（剥离 `<script>` + 折叠的 `<details>` 诊断 + 注释后）：**VISIBLE forbidden hits = NONE ✓**。
即 EmailBodyPlan / send_attempts / poster_key / workbench_key / inline_only / provider_message_id / Vertex / R2 /
URL/key only / no base64 / template_id / renderer / API / payload / fixture / generate affiche / generate fiche
**均不出现在默认可见 UI**。主屏改用业务语言：版式/宽度/邮件主体/成功·失败·已跳过/收件人/时间/状态。

## 6. 诊断抽屉行为 / Diagnostic drawer

- 折叠的 `<details class="diag">`「内部诊断 / 工程证据（默认折叠）」**默认折叠**。
- 内含（仅此处）：远程登录（ops user/pass + API base + 登录）、原始证据 JSON（workbench_key / poster_key /
  provider / 原始 send_attempts / 预览 plan 等）、配置提示。
- 工程字段只在运行时写入此抽屉的 `<pre>`；主流程不展示。

## 7. 本地/远程验证 / Local & remote validation

- 本地：页面 200；API 接线 create → 产品海报(ready) → 选为邮件主体 → 预览(200, 版式=单产品推广) 全通过。
- 发送：本地 inline → 业务态“已跳过”（不真实投递）；证据表以业务语言展示（收件人/状态/时间）。
- 远程：push 后需 trial 服务部署刷新；静态页不受 OPS 门控（其 API 调用才需在诊断抽屉登录）。
- docs router：PASS（ERROR=0）。

## 8. 保留的功能缺口 / Known functional gaps retained

- **简化产品页（fiche）** 远程依赖图像生成配置；缺失时按业务语言显示“暂不可用，改用产品海报”（不阻断）。
- **真实发送** 依赖目标服务发件配置；未配置时测试发送记为业务态“已跳过”（无真实投递）。
- 这些为运行时/配置层，不影响视觉对齐与主路线（产品海报 → 预览 → 测试发送 → 证据）。

## 9. 运营视觉评审是否可恢复 / Operator visual review ready?

**可恢复。** 首屏已是商用工作台外观（非 smoke runner），中文默认、业务语言、诊断折叠；部署刷新后即可在
`/cuistance_trial.html` 进行运营视觉评审与 test 模式主路线走查。

**STATUS: OPERATOR UI MOCKUP ALIGNMENT SUBMITTED FOR OWNER REVIEW**

## 10. 远程部署状态（push 后）/ Remote deploy status after push

- 推送：`9718d59` → origin trial 分支（aligned 版本）。
- `https://ai-service-leob.onrender.com/cuistance_trial.html` → **HTTP 200**，但**仍提供上一提交**（`143a7f0` 预对齐
  版：header 有「商业试用工作台」但正文仍是旧形态，含 EmailBodyPlan/send_attempts 等可见工程字段）。
- 等待 ~4 分钟后远程仍未刷新到 `9718d59` → **部署滞后 / 需触发部署**（Render 自动部署延迟或服务部署提交未跟进；
  我无控制台/API 访问，无法强制 rebuild）。本地 aligned 版校验全绿。
- **远程对齐前置：** 将 trial 服务部署刷新到 `9718d59`。刷新后 `/cuistance_trial.html` 应显示 3 步 stepper + 业务按钮
  + 折叠「内部诊断」，且可见区无工程术语（本地已验证）。

## 11. Mockup-first 迁移 + 资产同步修复（2026-06-18）

- 方法：**mockup-first 迁移**（非重写）。直接以 `docs/poster2/ui_mockups/cuistance_commercial_trial_v1/index.html`
  结构/CSS/资产为视觉契约，复制到部署静态路径，再把现有后端动作接线进该结构。
- 资产同步（确定性静态路径）：`frontend/assets/` + `docs/assets/` 同时落入真实资产
  `logo_01.jpg`（真实 CUISTANCE wordmark 400×80）、`banner_option_01.jpg`、`banner_option_02.jpg`、
  `product_01.jpg`、`product_02.jpg`、`product.svg`、`gallery.svg`；mockup `styles.css` → `cuistance_trial.css`
  （frontend+docs，重命名避免与旧 `frontend/styles.css` 冲突）。
- Logo 来源：仓库内 mockup 真实资产 `…/assets/logo_01.jpg`（= `~/poster/SOP/logo_01.jpg`）；并加 `onerror` 回退到
  真实 CUISTANCE 邮件 logo URL。**不再使用红色六边形占位 logo。**
- 三步分屏修复：保留 mockup 的 3 个 `<section class="screen">`，CSS `.screen{display:none}` + `.screen.active
  {display:block}` —— **同一时刻只显示一个步骤**；底部 `上一步 / 保存并进入下一步` 导航；步骤间不再纵向堆叠。
- 后端接线（结构内）：第一步「保存并进入下一步」→ create + 保存产品/素材；第二步生成产品海报 / 简化产品页 + 选为
  邮件主体（真实候选 + 选定）；第三步预览（真实 HTML 注入 iframe）+ 测试发送（确认弹窗 + 内部收件人 + 业务化结果）。
  简化产品页失败 → 业务琥珀提示「暂不可用，改用产品海报」（非红色工程错误）。
- 校验：所有静态资源 `/cuistance_trial.html`、`/cuistance_trial.css`、`/assets/logo_01.jpg|banner_option_01.jpg|
  product_01.jpg` 均 200；real logo 引用真实路径；CSS 单屏规则在位；中文默认；**可见区禁用工程术语扫描 = NONE**。

## 12. 远程部署状态（mockup-first 提交后）

- 推送 `280a026`（mockup-first：真实 logo + 3 步分屏 + 资产同步 + cuistance_trial.css）。
- 远程探针（push 后 + 等待 ~5 分钟）：`/cuistance_trial.html` 仍 200 但**为旧版本**（`/cuistance_trial.css` 404、
  `/assets/logo_01.jpg` 404、无 `.screen` 分屏、仍含旧 emblem）。→ **trial 服务未刷新到 `280a026`**（部署滞后 /
  需触发部署；无 Render 控制台/API 访问，无法强制 rebuild）。
- 本地校验全绿（真实 logo、单屏分步、资产 200、无可见工程术语）。**远程对齐前置 = 将 trial 服务部署刷新到
  `280a026`**（届时 `/cuistance_trial.css` 与 `/assets/*` 应 200，页面显示 3 步分屏 + 真实 CUISTANCE logo）。
