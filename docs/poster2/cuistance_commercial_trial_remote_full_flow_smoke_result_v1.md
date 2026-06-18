# CUISTANCE v1 · 远程全流程 Smoke 结果 v1

Purpose: Record the trial-branch push + remote deployment verification + remote full-flow smoke attempt for the CUISTANCE v1 backend loop.
Status: submitted (push DONE; remote deploy + remote smoke BLOCKED — Owner Decision Needed).
Scope: Branch + deployment validation only. No merge, no tag, no new features, no send-behavior change, no deploy-config change.
Source dependencies: render.yaml; docs/poster2/cuistance_commercial_trial_operator_validation_branch_prep_v1.md; docs/poster2/cuistance_commercial_trial_full_flow_smoke_result_v1.md.
Owner gate: Owner decision on the Render deploy target for the trial branch (see §4) + OPS credentials for the gated API.
Next action: Owner selects a deploy option; then re-run the remote smoke against the deployed trial branch.

---

## 1. 分支与提交 / Branch & commit

- **Branch:** `trial/poster2-cuistance-v1-operator-trial`
- **Base:** `feature/poster2-email-campaign-composite-remote-smoke-v1` @ `11ece26`
- **Commit:** `972bdc3f5190a7cde73377b2e2dad06ff84084b9` — *"poster2: prepare cuistance v1 operator trial loop"*
  （25 files, +4706 / -1；**仅范围内文件**：PR-1…PR-4 代码 + 6 测试 + 治理 + CUISTANCE 文档；无 `.DS_Store` / `.env` /
  deploy / frontend / 无关 churn）。
- **Push 结果:** ✅ 成功 —— `* [new branch] trial/poster2-cuistance-v1-operator-trial -> origin`
  （`https://github.com/zhaojfifa/ai-service`）。**未 merge、未 tag、未推 main。**

## 2. Docs router / 测试 / router & tests

- `scripts/check_docs_router.py --all` → **PASS**（ERROR=0）。
- 6 trial 套件（truth/candidates/assembly/reference/body-plan/send）→ **78 passed**（本地）。
- `test_api.py`：35 passed（设 `CORS_ALLOW_ORIGINS` 时；已知 CORS-env 预存产物）。

## 3. 远程部署验证 / Remote deployment verification

- `render.yaml`：**单一 web 服务** `marketing-poster-api`，**未 pin branch**，**无独立 validation 服务**。
  → Render 不会自动部署 `trial/*` 分支；切换分支需 **Render 控制台动作**（我无控制台/API 访问，且禁止改 deploy
  config）。
- 已知 Render host：
  - `https://ai-service-leob.onrender.com` → `/health` **200**（在线），但服务的部署分支由控制台决定，**并非**本 trial
    分支。
  - `https://ai-service-x758.onrender.com` → `/health` **404**（非活动服务）。
- **远程 API 受 OPS 鉴权门控**：`POST /api/v2/workbench`、`GET /api/v2/workbench/{k}`、`POST /api/v2/generate-poster`
  全部 **HTTP 401（ops_auth_required）**；`GET /api/auth/me` 200。→ 无 OPS 凭据无法调用任何 `/api/v2/*`（**不打印/不使用
  密钥**）。
- **结论：trial 分支未部署，且现网 API 鉴权门控** → **远程 smoke 无法执行**。

## 4. Owner Decision Needed — 部署目标 / deploy target options

无法从本侧确定/触发 trial 分支部署。请 Owner 选择**确切选项**：

- **Option A（推荐）：** 在 Render 新建/指定一个**验证服务**，将其部署分支设为
  `trial/poster2-cuistance-v1-operator-trial`，并配置所需 env（见 §5）；提供该服务 URL + OPS 凭据投放方式（不在此
  文档明文）。
- **Option B：** 在现有 `marketing-poster-api` 服务上临时切换部署分支到 trial 分支做一次性验证（**会改动现网服务**，
  需 Owner 明确批准；风险：影响现网）。
- **Option C：** 提供一个**预览/PR 环境**（Render PR preview）URL + OPS 凭据，针对该环境跑 smoke。
- 无论哪种：需在目标环境配置 **Resend**（真实发送）+ 视需要 **R2**（HTTPS 海报 URL）。

## 5. 远程运行时配置就绪（无密钥推断）/ Remote config readiness (no secrets)

依据 `render.yaml` 声明的 env var **名称**（非值；实际值在控制台）：

| 项 | 远程推断 |
|---|---|
| Vertex（`GCP_PROJECT_ID`/`GCP_LOCATION`/`GOOGLE_APPLICATION_CREDENTIALS`/`GCP_KEY_B64`/`VERTEX_*`）| **声明存在** → Vertex 可能已配置（**fiche 远程或可成功**，与本地不同）|
| Firefly（`FIREFLY_CLIENT_ID`/`SECRET`）| **声明存在** → PosterPipeline 背景或可用 |
| **Resend**（`RESEND_API_KEY` / `RESEND_FROM_EMAIL` / `EMAIL_FROM*`）| **render.yaml 未声明** → 真实发送很可能**不可用** |
| **R2 / S3**（`R2_*` / `S3_*`）| **render.yaml 未声明** → 海报很可能仍 `inline_data_url` |
| `EMAIL_ATTACHMENT_*` / `EMAIL_PROVIDER` / `EMAIL_SEND_ENABLED` / `EMAIL_PREVIEW_ENABLED` / `EMAIL_OUTBOX_ENABLED` | **render.yaml 未声明**（控制台或另有设置，无法确认）|
| OPS 鉴权（`OPS_UI_ENABLED`/`OPS_USERNAME`/`OPS_PASSWORD`/...）| **声明存在** → 现网 `/api/v2/*` 401 一致 |
| Chromium | `buildCommand` 含 `python -m playwright install chromium` → **可用**（affiche 远程可渲染）|

> 注：以上为**基于 render.yaml 声明名称的推断**，非确认值；实际由 Render 控制台 env 决定（不可见、不打印密钥）。

## 6. 远程 smoke 结果 / Remote smoke result

| 项 | 值 |
|---|---|
| remote URL | `https://ai-service-leob.onrender.com`（在线，但**非** trial 分支 + **OPS 401**）|
| workbench_key | — （未执行：未部署 + 鉴权门控）|
| affiche poster_key | — |
| fiche poster_key / 失败原因 | — |
| selected_email_body_visual | — |
| preview checks | — |
| send mode | — |
| provider_message_id | — |
| **是否真实发送邮件** | **否**（未执行任何发送）|
| send_attempts 证据 | — |

**远程 full-flow smoke 未执行**（阻塞于：trial 分支未部署 + 现网 API OPS 门控 + Resend/R2 远程未声明）。

## 7. 阻塞项 / Blockers

1. **部署目标未定/不可触发**（render.yaml 单服务、无 branch pin、无 validation 服务；无控制台/API 访问；禁止改
   deploy config）→ §4 Owner Decision Needed。
2. **现网 API OPS 鉴权 401** → 无凭据无法跑远程 smoke（不使用/不打印密钥）。
3. **Resend 远程未声明** → 真实发送很可能不可用。
4. **R2 远程未声明** → 海报很可能仍内联 data URL。

均为**部署/配置层**阻塞，非工作台后端逻辑问题（本地 78 测试 + 全流程 affiche smoke 已通过）。

## 8. GO / HOLD（人工运营验证）/ recommendation

- **代码/分支：GO** —— trial 分支已 push（`972bdc3`），范围干净，本地全绿。
- **远程人工运营验证：HOLD** —— 待 Owner 选定 §4 部署选项并在目标环境配置 Resend（+ 视需要 R2），并提供 OPS 凭据
  投放方式；随后复跑本远程 smoke：先 `mode=test`（验 `provider_message_id`），再 `mode=real` 发 Owner 批准的**内部
  地址**（严禁客户名单）。

**STATUS: TRIAL BRANCH REMOTE SMOKE SUBMITTED FOR OWNER REVIEW**
