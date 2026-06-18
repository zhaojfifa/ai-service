# CUISTANCE 商业试用 · 全流程运行时 Smoke 结果 v1

Purpose: Record the end-to-end runtime smoke of the CUISTANCE workbench v1 backend loop (truth → candidates → selected visual → EmailBodyPlan preview → manual confirmed send → evidence).
Status: submitted (runtime smoke result; awaiting Owner review).
Scope: Runtime smoke only — no new features, no scope change. In-process FastAPI run against the real app.
Source dependencies: app/main.py; app/services/email/*; app/services/workbench_records.py; docs/poster2/cuistance_commercial_trial_pr4_manual_send_evidence_status_v1.md.
Owner gate: Owner review of smoke evidence → GO/HOLD for operator trial.
Next action: Configure a real Resend provider + verified sender (and Vertex if fiche is needed), then re-run real-mode send to an Owner-approved address.

---

## 1. 环境摘要（无密钥）/ Environment summary (no secrets)

| 项 | 状态 |
|---|---|
| docs router check | **PASS** (ERROR=0) |
| Gemini copy optimizer | `gemini_enabled=False`（key 存在但优化器未启用 → 确定性文案）|
| email attachment | `enabled=False`（预览/发送不构建 PNG/PDF）|
| **Resend provider** | **`is_configured=False`**（无 `RESEND_API_KEY` / `from_email`）→ **无法真实投递** |
| R2 storage | 未配置（endpoint/bucket/public_base 缺）→ 海报托管回退 `inline_data_url`；记录走 `/tmp` 本地 |
| Vertex Imagen3 | 未初始化（fiche/PosterPipeline 背景生成依赖它）|
| 网络 / Chromium | 可联网取公共图；Chromium 可启动（affiche 真实渲染可行）|

> 诚实结论：本地运行时**邮件 provider 与 Vertex/R2 均未配置**。affiche（composite/Chromium）可真实渲染；fiche
> （PosterPipeline）因 Vertex 缺失而失败；真实邮件**无法**发送（Resend 未配置）。

## 2. 是否跑通全流程 / Did the full flow run

**是（主路线 affiche 全程跑通）。** 步骤：创建 workbench → patch product_truth（EF132V）→ patch
product_assets + email_banner（真实公共图 URL）→ 生成 affiche + fiche 候选 → 选定 → 预览 → test 模式确认发送 →
读回 send_attempts 证据。

## 3. 关键标识 / Identifiers

- `workbench_key` = **wb_33656232431e46a4**
- affiche `poster_key` = **p2_4fb82bb4ba5e4120**（status=ready；real_engine=chromium；degraded=false；
  structure_complete=true；callout_count=3）
- fiche `poster_key` = **None**（status=failed）
- `selected_email_body_visual` = **affiche**

## 4. 候选生成 / Candidate generation

| 候选 | template_id | HTTP | 结果 |
|---|---|---|---|
| affiche | `email_campaign_composite_v1` | 200 | **ready**，Chromium 真实渲染，degraded=false，callout_count=3 |
| fiche | `template_product_sheet_v1` | 422 | **failed** — `stage=material_prepare`，`code=background_prepare_failed`，detail=**"Vertex Imagen3 client is not initialised"**（本地 Vertex 未配置）|

fiche 失败被正确记录为 `poster_candidates.fiche.status=failed`（无 poster_key），未污染 affiche 证据。

## 5. 预览结果 / Preview result（POST /api/v2/workbench/{key}/email/preview → 200）

全部检查通过：

| 检查 | 结果 |
|---|---|
| `email_body_plan` 存在 | ✅ |
| `layout_type` | `single_product_promo` |
| `container_width` | `600` |
| `selected_body_visual_slot.poster_key` | `p2_4fb82bb4ba5e4120`（= 选定 affiche）|
| `final_poster_url` 存在 | ✅（`data:image/png;base64,...`，因 R2 未配置而内联）|
| 600px 表格 shell | ✅（`width="600"` + `max-width:600px`）|
| Email Banner Module | ✅（深色 `#1f2329`）|
| 红 filet | ✅（`background:#E1002A`）|
| CTA | ✅（`Nous contacter`）|
| footer / legal 占位 | ✅（`Se désabonner`）|

`body_visual` 来自加载的 poster_record（`url=data:image/png;base64,…`），**非**前端输入。

## 6. 发送 / Send

### 6.1 test 模式 · inline_only（主 smoke）
请求：`recipients=["owner-internal-test@cuistance.eu","dup@cuistance.eu","DUP@cuistance.eu","bad@@"]`,
`mode=test`, `confirm_send=true`, `delivery_mode=inline_only`。

- recipient count（去重后唯一）= **3**；`deduplicated_count=1`（`DUP@`≡`dup@`）。
- `sent_count=0` · `skipped_count=2` · `failed_count=1`。
- 逐个证据：

| recipient | status | provider | error_code | provider_message_id |
|---|---|---|---|---|
| owner-internal-test@cuistance.eu | **skipped** | inline_only | preview_only | — |
| dup@cuistance.eu | **skipped** | inline_only | preview_only | — |
| bad@@ | **error** | validation | invalid_recipient | — |

每个 attempt 含 `layout_type=single_product_promo`、`body_visual_poster_key=p2_4fb82bb4ba5e4120`、`subject` 快照、
`at` 时间戳。workbench `status` 仍为 `draft`（test 模式不置 sent）。

### 6.2 resend 探针（揭示 provider 行为）
请求：`mode=test`, `delivery_mode=resend`, 内部收件人。结果：`status=error`, `provider=resend`,
`error_message="Resend is not configured."`, `provider_message_id=None`。

## 7. 是否真实发送了邮件 / Was any real email sent

**否。** inline_only 返回 `preview_only`（skipped，无 provider_message_id）；resend 返回
`"Resend is not configured."`（error）。**没有任何 provider_message_id**，无真实投递。real 模式**未运行**
（Resend 未配置 + 无 Owner 批准的内部地址）。

## 8. Provider 行为 / Provider behavior

- `inline_only` → `preview_only` → 记为 **skipped**（设计内：仅预览，不投递）。
- `resend` → **error / "Resend is not configured."**（config missing）。
- 无 sent；无 message id；无客户名单触达。

## 9. 阻塞项 / Blockers found

1. **Resend 未配置** → 无法真实发送（需 `RESEND_API_KEY` + 已验证 `from_email`/发件域）。
2. **Vertex Imagen3 未初始化** → **fiche（简化产品页）候选生成失败**；affiche（composite）不依赖 Vertex，正常。
3. **R2 未配置** → 海报以 `inline_data_url` 内联（邮件正文图为大 data URL；生产应配 R2 得 HTTPS URL）。
4. （非阻塞）Gemini 优化器未启用 / 附件未启用 —— 属可选，确定性文案正常。

以上均为**运行时环境配置缺口**，非工作台后端逻辑缺陷；后端 v1 闭环逻辑本身全程跑通。

## 10. 验证 / Validation

- `scripts/check_docs_router.py --all` → PASS（ERROR=0）。
- `pytest tests/poster2/test_workbench_email_send.py tests/poster2/test_workbench_email_body_plan.py -q` → **25 passed**。

## 11. GO / HOLD 建议 / Recommendation

**HOLD（用于真实客户发送）→ 在配置就绪后 GO。** 后端 v1 闭环**逻辑已跑通且确定性**（truth→candidate→select→
plan preview→confirmed send→evidence），但**真实投递被环境阻塞**（Resend 未配置）。建议运营试用前（运维动作，非代码）：
1. 配置 **Resend**（API key + 已验证发件域/`from_email`）；
2. 若需要 fiche 简化产品页，配置 **Vertex Imagen3**（affiche 不需）；
3. 配置 **R2** 以获得 HTTPS 海报 URL（替代内联 data URL）；
4. 先 **test 模式**发到自身/测试地址验证 provider_message_id，再 **real 模式**发给少量 Owner 批准的内部地址；
5. 复跑本 smoke 确认出现 `status=sent` + `provider_message_id`。

**STATUS: FULL FLOW SMOKE SUBMITTED FOR OWNER REVIEW**
