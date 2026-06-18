# CUISTANCE v1 · 运营 UI ↔ 后端契约对齐状态 v1

Purpose: Diagnose + fix the /cuistance_trial.html UI-to-backend wiring so the operator can run the affiche route from the browser.
Status: submitted (functional wiring fixed + pushed; remote browser flow needs operator OPS login — no creds held here).
Scope: Functional alignment (frontend wiring) only. No visual redesign; no backend business-logic/renderer/send change.
Source dependencies: frontend/cuistance_trial.html; app/main.py (/api/auth/*, /api/r2/presign-put, /api/v2/workbench*); app/services/r2_client.py.
Owner gate: Operator/Owner OPS login to exercise the remote browser flow.
Next action: On the remote page top «后端连接» enter OPS creds → 连接 → 使用示例素材 → 保存并进入下一步 → 生成产品海报 → 选为邮件主体 → 预览邮件 → 发送测试邮件.

---

## 1. 根因 / Root causes

- **上传失败根因：** 之前的页面**没有任何上传控件，也没有可编辑的素材字段** —— 产品图/Logo 是 JS 里写死的示例 URL +
  静态缩略图，运营无法上传或更换素材。且 `/api/r2/presign-put` 受 OPS 鉴权（401），远程未声明 R2 变量（presign 在
  R2 未配置时返回 503）。
- **生成失败根因：** 远程 `/api/v2/*` 全部 **OPS 鉴权 401**；页面**主屏无可见连接/登录状态**（登录埋在 ⓘ 诊断里）；
  且 401/错误只写到第一步隐藏 hint（`s1-hint`），第二步点「生成产品海报」时**静默无反馈** → 表现为“生成不工作”。

## 2. UI 动作 → 后端端点契约 / UI action → backend endpoint

| UI 动作 | 后端端点 | 备注 |
|---|---|---|
| 连接后端（顶部「后端连接」连接按钮）| `POST /api/auth/ops-login` ；状态来自 `GET /api/auth/me` | 主屏可见状态：未连接/已连接/连接失败 |
| 上传产品主图 / 邮件 Logo（file 输入）| `POST /api/r2/presign-put` + 预签 `PUT` | R2 未配置时 503 → 业务回退「当前环境未启用上传，请使用示例素材」 |
| 使用示例素材（按钮）| —（填入已托管示例 URL）| 让 affiche 主路线无需上传即可运行 |
| 创建工作台 | `POST /api/v2/workbench` | 首次保存时自动创建 |
| 保存产品信息 | `PATCH /api/v2/workbench/{key}`（product_truth + product_assets + email_banner）| 「保存并进入下一步」 |
| 生成产品海报 | `POST /api/v2/workbench/{key}/candidates/affiche/generate` | 结果/错误在当前步以业务语言提示 |
| 生成简化产品页 | `POST /api/v2/workbench/{key}/candidates/fiche/generate` | 失败 → 琥珀「暂不可用，改用产品海报」（不阻断）|
| 选为邮件主体 | `PATCH /api/v2/workbench/{key}/selected-visual` | affiche/fiche 二选一 |
| 预览邮件 | `POST /api/v2/workbench/{key}/email/preview` | 真实 HTML 注入 iframe |
| 测试发送 | `POST /api/v2/workbench/{key}/email/send`（mode=test, inline, confirm）| 业务化证据；默认不真实投递 |

## 3. 已修复 / Fixes applied（仅前端 frontend + docs 镜像）

1. **主屏连接状态 + 登录**：顶部「后端连接」栏，可见 `未连接 / 已连接 / 连接失败` 状态 + 账号/密码 + 连接按钮；
   加载时 `GET /api/auth/me` 自动判定（本地鉴权关闭时显示「已连接」）。**不再只把连接埋在诊断里。**
2. **401 业务化**：任何 401 → 全局提示「请先连接后端」（不再原始 JSON / 静默）。
3. **上传支持**：产品主图 / 邮件 Logo 的 file 控件接 `/api/r2/presign-put` + PUT；R2 未启用（503）→ 业务回退
   「当前环境未启用上传，请使用示例素材」。**不假装上传成功。**
4. **「使用示例素材」**：一键填入已托管示例 URL，affiche 主路线无需上传即可跑通（验收允许）。
5. **生成按钮**：「生成产品海报」确实调用 `…/candidates/affiche/generate`（带会话 + 已保存的 workbench），并在
   当前步以业务语言显示成功/失败。
6. **错误处理**：401→「请先连接后端」；422/缺主图→「请先保存产品信息 / 产品主图缺失」；fiche 失败→「当前环境暂不
   可用，请改用产品海报」；其他→「生成失败，请查看内部诊断」。
7. **工程细节**仅在折叠「内部诊断 / 工程证据」抽屉（原始 evidence/keys）。
8. **测试发送为默认**；真实发送需切换 + 确认。

## 4. 是否改后端 / Backend changed?

**否。** 仅修改 `frontend/cuistance_trial.html`（+ `docs/` 镜像）。`/api/auth/ops-login`、`/api/auth/me`、
`/api/r2/presign-put`、`/api/v2/workbench*` 均为**既有端点**；未改任何后端业务逻辑、renderer、发送行为、部署配置。
（未发现需修的后端 bug。）

## 5. 本地验证 / Local validation

- `/cuistance_trial.html`、`/cuistance_trial.css`、`/assets/logo_01.jpg` 均 200。
- `GET /api/auth/me` `enabled=false`（本地鉴权关闭）→ 连接状态显示「已连接」。
- 使用示例素材 → 保存 → **生成产品海报 = 200 ready** → 选为邮件主体 → **预览邮件 = 200**（single_product_promo）。
- `POST /api/r2/presign-put`（本地 R2 未配置）→ **503** → 页面映射为「当前环境未启用上传，请使用示例素材」（验证回退路径）。
- 可见区禁用工程术语扫描 = NONE；docs router PASS。

## 6. 远程验证 / Remote validation

- 远程页面/CSS/资产已对齐 + 200；本次修复（连接栏 + 示例素材 + 上传回退 + 业务错误）已 push 到 trial 分支。
- **远程浏览器完整流程需运营/Owner 用 OPS 凭据在页面「后端连接」登录**：本环境**无 OPS 凭据**（不可打印/不可猜测），
  因此**本侧无法代为完成远程浏览器流程**。修复后页面已具备：可见连接状态、一键示例素材、上传回退、当前步业务错误，
  使运营登录后可真正跑通 affiche 路线。
- 远程部署刷新到本次提交后，运营即可走查（静态页不受门控；`/api/v2/*` 由 `后端连接` 登录解锁）。

## 7. 剩余阻塞 / Remaining blockers

1. 远程浏览器走查需运营 **OPS 登录**（凭据由 Owner 持有；本侧无）。
2. 远程**上传**取决于目标服务 **R2** 配置；未配置时走「使用示例素材」（affiche 路线不依赖上传）。
3. 远程**真实发送**取决于发件 provider 配置（默认 test/inline 预览态）。
4. 新页面需 **trial 服务部署刷新**到本提交后远程可见。

## 8. 运营功能验证是否可恢复 / Can operator functional validation resume?

**可以（affiche 主路线）。** 修复后运营在远程页面：① 顶部「后端连接」登录 → ② 「使用示例素材」（或上传，若 R2 启用）
→ ③ 保存并进入下一步 → ④ 生成产品海报 → ⑤ 选为邮件主体 → ⑥ 预览邮件 → ⑦ 发送测试邮件并查看业务化证据。任一步失败
都会显示明确的业务可读阻塞，不再静默。

**STATUS: OPERATOR UI BACKEND CONTRACT ALIGNMENT SUBMITTED FOR OWNER REVIEW**
