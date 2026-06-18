# CUISTANCE v1 · 远程浏览器功能验证（含 OPS 鉴权）v1

Purpose: Remote functional validation of /cuistance_trial.html on the deployed trial service, using Owner-provided OPS auth.
Status: submitted — **GO (affiche main route)**.
Scope: Validation only. No backend/renderer/send change; no customer send; no secret stored.
Source dependencies: https://ai-service-leob.onrender.com/cuistance_trial.html (deployed ed99ee5 markers); v1 workbench endpoints.
Owner gate: Owner review of remote GO.
Next action: Operator trial may proceed on the affiche route; configure send provider + R2 for real send/upload when desired.

---

## 1. 远程 URL / 部署版本

- Remote: `https://ai-service-leob.onrender.com/cuistance_trial.html` → **HTTP 200**.
- Deployed version: **ed99ee5 或更新**（页面标记确认：每卡片内置上传槽位 `file-prod1/prod2/g1-3/atmo/logo/banner`、
  「使用示例素材」按钮、连接栏 `btn-connect`、`refreshState`、真实 CUISTANCE logo、3-step 分屏、诊断默认折叠）。

## 2. 预检 / Preflight

- 真实 CUISTANCE logo ✅；中文优先 ✅；3 步分屏（one screen at a time）✅；资产槽位在卡片内 ✅；后端连接栏可见 ✅；
  诊断默认折叠 ✅。
- 主屏**可见区禁用工程术语扫描 = NONE** ✅。

## 3. 验证流程结果 / Flow results（通过页面所用的同一受 OPS 鉴权的后端端点）

| 步骤 | 结果 |
|---|---|
| OPS 登录（Owner 提供的临时凭据文件，密钥不打印/不入库）| ✅ HTTP 200，`authenticated=true` → 页面「已连接」|
| 创建工作台 | ✅ `workbench_key = wb_a3b6e54e3fa343f0` |
| 使用示例素材 + 保存产品/素材 | ✅ `product_images=2`、`gallery_images=1`、`email_banner.background=set`（含可选槽位）|
| 生成产品海报（affiche，远程真实渲染）| ✅ HTTP 200，`status=ready`，poster 已生成 |
| 复用 ready 候选（不强制重生成）| ✅（已就绪即可直接选用）|
| 选为邮件主体 | ✅ HTTP 200 |
| **selected_email_body_visual** | **= `affiche`**（后端确认）|
| **Step 3 解锁** | ✅ |
| 预览邮件 | ✅ HTTP 200，版式 `single_product_promo`，宽度 600 |
| 预览内容 | ✅ 品牌页眉 + 选定产品海报视觉 + CTA「Nous contacter」+ 页脚/法律占位 |
| 测试发送（内部收件人、test、confirm、inline）| ✅ HTTP 200，total=1 / sent=0 / **skipped=1（preview_only）** / failed=0 |
| **是否真实发送邮件** | **否**（无 provider_message_id；inline 仅预览；内部地址）|
| 发送证据（业务语言）| ✅ 收件人 / 状态（已跳过）/ 时间 已记录 |

## 4. 安全 / Security

- OPS 凭据仅从 `/tmp/cuistance_ops.json` 读取，**未打印、未入库、未出现在日志/截图/文档/提交/Owner Summary**。
- 验证后**已删除** `/tmp/cuistance_ops.json`（确认 gone）。
- 仅内部测试收件人；**未向任何客户/真实地址投递**。

## 5. 可见工程术语检查

远程页面可见区（剥离 `<script>` + 折叠诊断 + 注释）：**NONE** ✅。工程字段仅在折叠「内部诊断 / 工程证据」。

## 6. 阻塞项 / Blockers

- 无主路线阻塞。允许的非阻塞项：远程上传需 R2（本次走「使用示例素材」）；fiche 视图像生成配置；真实发送需发件
  provider（本次 test/inline，无真实投递）。

## 7. 验收 / Acceptance — **GO**

满足全部 GO 判据：OPS 登录成功；示例素材跑通主路线；产品海报生成/复用成功；`selected_email_body_visual=affiche`；
Step 3 解锁；邮件预览构建成功；测试发送证据已记录；未发送任何客户邮件；主屏全业务语言、无工程术语。

**STATUS: REMOTE BROWSER FUNCTIONAL VALIDATION WITH OPS AUTH SUBMITTED FOR OWNER REVIEW**
