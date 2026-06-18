# CUISTANCE v1 · 运营 UI 功能验证结果 v1

Purpose: Functional validation of the aligned commercial operator page /cuistance_trial.html (affiche main route first).
Status: submitted (remote visual GO; remote functional gated by OPS login; local functional GO).
Scope: Validation only. No backend/API/renderer/send change; no customer send.
Source dependencies: https://ai-service-leob.onrender.com/cuistance_trial.html; v1 workbench endpoints; docs/poster2/cuistance_commercial_trial_operator_ui_alignment_status_v1.md.
Owner gate: Owner/operator OPS login for the remote functional walkthrough.
Next action: Operator logs in (ⓘ 内部诊断 OPS login) on the remote page and runs the affiche route → preview → test send.

---

## 1. 远程 URL / 部署 / Remote URL & deploy

- Remote: `https://ai-service-leob.onrender.com/cuistance_trial.html` → **HTTP 200**.
- Deployed branch/commit: trial branch deploy (Owner-confirmed refreshed). Static assets `cuistance_trial.css`,
  `assets/logo_01.jpg`, `assets/banner_option_01.jpg` all **200** (i.e. the mockup-first commit is live; the
  earlier 404s are resolved).

## 2. 视觉页面检查（远程，curl）/ Visual page check (remote)

| 检查 | 结果 |
|---|---|
| 真实 CUISTANCE logo（`assets/logo_01.jpg`，非红色六边形）| ✅ |
| mockup CSS（`cuistance_trial.css`）| ✅ 200 |
| 三步分屏（3 × `class="screen"`）| ✅ |
| 旧 emblem 占位 logo 已移除 | ✅ |
| 中文优先 stepper（产品与素材 / 生成海报主体 / 邮件预览与测试发送）| ✅ |
| 可见区禁用工程术语扫描（剥离 script + 折叠诊断 + 注释）| ✅ **NONE** |

## 3. 远程功能门控 / Remote functional gating

- 远程 `/api/v2/*` 受 **OPS 鉴权**：`POST /api/v2/workbench` → **401**；`GET /api/auth/me` → 200。
- 本环境**无 OPS 凭据**（Render 控制台 secret；本地 MISSING；不猜测/不打印）。因此**远程功能流程需运营/Owner 在页面
  「ⓘ 内部诊断」OPS 登录后**自行走查 —— 这正是页面内置的运营登录入口。

## 4. 本地功能验证（in-process，鉴权关闭；验证远程所服务的同一后端 + 页面 API 契约）

> 这是对“远程页面驱动的同一后端代码 + 同一请求契约”的端到端功能验证；唯一无法在远程主机本侧执行的原因是 OPS 鉴权。

| 步骤 | 结果 |
|---|---|
| **Step 1** 保存产品与素材信息 | ✅ 200（create + product_truth + product_assets/email_banner） |
| **Step 2** 生成产品海报（affiche）| ✅ 200，`status=ready`（真实 Chromium 合成渲染）|
| **fiche（简化产品页）** | **未在本验证中测试**（可选；本地缺图像生成会按预期失败 → 业务琥珀「暂不可用」；不阻断主路线）|
| **选定邮件主体** | ✅ `selected_email_body_visual=affiche` |
| **Step 3** 邮件预览 | ✅ 200；版式=`single_product_promo`、宽度=600、含品牌页眉 + 选定产品海报 + CTA「Nous contacter」+ 页脚/法律「Se désabonner」|
| **测试发送** | ✅ 200（mode=test, inline, 内部收件人, 确认）；total=1 / sent=0 / **skipped=1（preview_only）** / failed=0 |
| **是否真实发送邮件** | **否**（无 provider_message_id；inline 仅预览）|

- `workbench_key = wb_467be491724b415b`
- 产品海报 `poster_key = p2_16339662144d44cd`（仅记录于本证据/诊断；主 UI 不展示）

## 5. 选定邮件主体 / Selected email body visual

`affiche`（产品海报主体）。

## 6. 预览结果 / Preview result

**通过。** 计划化商业邮件主体齐备：品牌页眉（横幅一等模块）+ 选定产品海报视觉 + CTA + 页脚/法律占位；版式
`single_product_promo`、容器 600px。所选视觉来源为后端选定（非前端/AI）。

## 7. 发送证据 / Send evidence

业务语言记录：本次 test/inline → 「已跳过（仅预览，不投递）」。逐条含 收件人 / 状态 / 时间。**未真实投递。**
（真实投递需目标服务配置发件 provider；本验证不做真实客户发送。）

## 8. 可见工程术语检查 / Visible forbidden-term check

远程可见 markup（剥离 `<script>` + 折叠 `内部诊断 / 工程证据` 抽屉 + 注释）：**NONE**。工程字段（poster_key /
workbench_key / send_attempts / provider / 等）仅在折叠诊断抽屉/JS。

## 9. 阻塞项 / Blockers

1. **远程功能走查需 OPS 登录**：远程 `/api/v2/*` 为 401；本侧无凭据（不可打印/不可猜测）。→ 运营/Owner 在页面
   `ⓘ 内部诊断` 登录后即可走查（这是预期运营动作，非缺陷）。
2. **真实发送**仍需目标服务发件 provider 配置（test/inline 为预览态）。
3. **fiche** 远程依赖图像生成配置（可选，不阻断 affiche 主路线）。

## 10. GO / HOLD 建议 / Recommendation

- **运营试用：GO（affiche 主路线）。** 判据满足：affiche 路线贯通至预览 + 测试发送证据（本地对同一后端验证全绿）；
  远程页面视觉对齐、主屏无工程术语、无真实客户发送。
- 远程功能走查仅需运营用 OPS 凭据登录（页面已内置入口）；真实发送在配置发件 provider 后由 Owner 批准内部地址进行。

**STATUS: OPERATOR UI FUNCTIONAL VALIDATION SUBMITTED FOR OWNER REVIEW**
