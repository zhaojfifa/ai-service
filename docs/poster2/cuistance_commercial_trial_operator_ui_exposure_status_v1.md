# CUISTANCE v1 · 运营试用 UI 暴露状态 v1

Purpose: Expose a minimal operator-trial UI page for the CUISTANCE v1 workbench loop on the deployed trial branch.
Status: submitted (UI page added + pushed; awaiting Owner review + remote deploy refresh).
Scope: Static UI exposure only. No backend logic change, no new product feature, no renderer/send-behavior change.
Source dependencies: frontend/ (StaticFiles mount in app/main.py); the v1 workbench endpoints (PR-1…PR-4).
Owner gate: Owner review + confirm the trial service serves /cuistance_trial.html after deploy.
Next action: After deploy refresh, run the remote flow (test mode) and, only with Resend + Owner-approved internal address, a real-mode internal send.

---

## 1. 新页面 / New page

- **Path:** `/cuistance_trial.html`  ·  Source: `frontend/cuistance_trial.html`  ·  Mirror: `docs/cuistance_trial.html`
- **Served by:** existing `app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True))` —— **无需新增路由**。
- **Title:** “CUISTANCE v1 · Operator Trial · 商业试用工作台”，并显式标注 *“NOT the old poster workbench /
  ops_campaign”*，与 `/`（旧营销海报工作台）和 `/ops_campaign.html`（旧诊断页）区分。

## 2. 是否改后端 API / Backend changed?

**否。** 仅新增 2 个静态文件（frontend + docs 镜像）。未改 renderer、`email_campaign_composite_v1`、
`template_product_sheet_v1`、`/api/v2/email/send`、workbench 后端逻辑，未改部署配置。

## 3. 页面驱动的 v1 流程 / Flow the page drives

按钮 + 状态面板覆盖完整 v1 闭环（全部走现有端点）：
1. `POST /api/v2/workbench`（language=fr）
2. `PATCH …`：product_truth（EF132V 样例；参数 confirmed；**190°C 仅样例值**）
3. `PATCH …`：product_assets（图 URL/key）+ email_banner（logo + channel + campaign）
4. `POST …/candidates/affiche/generate`
5. `POST …/candidates/fiche/generate`（**允许 Vertex 缺失时失败**，UI 显示失败原因，不阻断）
6. `PATCH …/selected-visual`（默认 affiche；fiche 失败时自动用 affiche）
7. `POST …/email/preview` → 展示 **EmailBodyPlan**：`layout_type` / `container_width` / `selected_body_visual_slot`
   / `final_poster_url` + 预览 HTML（iframe）
8. `POST …/email/send`（**默认 test + inline_only**；真实发送需 ① Mode=Envoyer(réel) ② 勾选 Confirmer）
9. `GET …/workbench/{key}` 读回 → send_attempts 表

UI 展示：workbench_key、affiche poster_key、fiche status/poster_key/失败原因、selected_email_body_visual、预览状态、
send mode、send_attempts 表（recipient/status/provider/error_code/message_id）、provider 结果、**是否真实发送**
（仅当存在 `provider_message_id` 才标“是”）。

## 4. 安全 / Safety

- 默认 **test 模式**，**不默认真实发送**；真实发送需显式切 Mode + 勾选 Confirmer（双重确认）。
- 收件人为**手动单个内部地址**输入（默认内部占位），**无**客户名单、**无**通讯录/Excel 导入、**无** CRM/定时/统计/
  dashboard。
- 远程 `/api/v2/*` 受 OPS 鉴权：页面提供最小 `Se connecter`（→ `/api/auth/ops-login`，cookie 会话，
  `credentials:'include'`）；本地未开启鉴权时无需登录。**不打印/不硬编码密钥。**
- 资产仅 URL/key（无 base64）。

## 5. 验证 / Validation

- `scripts/check_docs_router.py --all` → PASS（ERROR=0）。
- 本地（in-process）：`GET /cuistance_trial.html` → **200**，含标题与 `商业试用工作台`；API 接线
  create → affiche(**ready**, poster_key) → select → preview(**200**, layout=single_product_promo,
  container_width=600, slot.poster_key 一致, 600px shell) 全通过。示例 `workbench_key=wb_7d17dce109fc475f`,
  affiche `p2_25fdb43b2e5f4ad8`。
- 发送步骤：本地 inline_only → `preview_only`（不投递）；真实发送依赖远程 Resend 配置（见 blockers），故标记为
  **远程能力**。
- 远程：本页 push 后需等待 trial 服务部署刷新；静态页不受 OPS 门控（仅 `/api/*` 受门控），部署后应可在
  `https://<trial-service>/cuistance_trial.html` 打开。

## 6. 阻塞项 / Blockers

1. **远程真实发送**仍取决于目标服务 **Resend + 已验证发件域**配置（render.yaml 未声明 → 很可能未配置；real 模式将
   返回 “Resend is not configured.”）。
2. **fiche 远程**取决于 Vertex（render.yaml 声明存在 → 远程或可成功；本地缺失会按预期失败）。
3. 远程 `/api/v2/*` OPS 鉴权 → 运营需先在页面 `Se connecter`。
4. 新页面需 **trial 服务部署刷新**后才在远程可见。

## 7. 运营人工验证是否就绪 / Operator manual validation ready?

**就绪（test 模式）。** 部署刷新后，运营可在 `/cuistance_trial.html` 一键跑 create→affiche→select→preview→test 发送
并查看 send_attempts 证据；affiche 主路线不依赖 Resend/Vertex。**真实内部发送**仍 HOLD，待目标服务配置 Resend + 由
Owner 批准的内部地址。

**STATUS: OPERATOR TRIAL UI EXPOSURE SUBMITTED FOR OWNER REVIEW**
