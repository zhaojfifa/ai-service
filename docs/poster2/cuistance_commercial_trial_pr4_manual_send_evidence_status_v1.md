# CUISTANCE 商业试用 · PR-4 Manual Multi-Recipient Send + Evidence — 实施状态 v1

Purpose: Record the PR-4 implementation of manual multi-recipient confirmed send of the deterministic EmailBodyPlan package + per-recipient evidence.
Status: submitted (PR-4 complete; awaiting Owner review). Completes the v1 commercial backend loop.
Scope: Workbench send endpoint consuming the PR-3S package; explicit confirm; per-recipient isolation; evidence on workbench.send_attempts. Reuses existing provider; no send-behavior change to the legacy endpoint.
Source dependencies: docs/poster2/cuistance_commercial_trial_pr3s_email_body_plan_status_v1.md; app/main.py; app/services/email/assembly.py; app/services/email/providers.py; app/services/workbench_records.py.
Owner gate: Owner review of PR-4; then operator-trial readiness decision.
Next action: On approval, request the operator trial (no further backend PR required for the v1 loop).

---

## 1. 范围 / Scope

实现 backend alignment plan 的 **PR-4**：把 **PR-3S 的确定性 EmailBodyPlan 邮件包**手动发送给运营手工录入的收件人，
需显式确认、逐个收件人隔离、并在 workbench 上记录证据。**复用**现有 email provider；**不**改既有单收件人
`/api/v2/email/send`。

## 2. 文件变更 / Files changed

| 文件 | 变更 |
|---|---|
| `app/schemas/poster2.py` | 新增 `SendMode` / `WorkbenchEmailSendRequest`（无 HTML/subject 覆盖）/ `WorkbenchSendAttempt` / `WorkbenchEmailSendResponse` |
| `app/services/email/workbench_send.py` | **新增**：`normalize_recipients`（trim/去重/校验，去重计数）+ `is_valid_email` |
| `app/services/workbench_records.py` | 新增 `append_send_attempts`（证据落库，不存 provider 密钥） |
| `app/main.py` | 新增 `_resolve_workbench_email_package`（preview 与 send **共用**的确定性包解析器）；preview 重构为复用解析器；新增 send 端点 |
| `tests/poster2/test_workbench_email_send.py` | **新增**：14 个测试 |
| docs status + README + log | 索引 + 日志 |

## 3. 端点 / Endpoint

新增：`POST /api/v2/workbench/{workbench_key}/email/send`。
**未改**：`POST /api/v2/email/send`（单收件人，backward compatible）；`POST /api/v2/workbench/{key}/email/preview`
（重构为复用解析器，行为不变）。

## 4. 发送确认行为 / Send confirmation

- `confirm_send` 必须为 `true`，否则 `422 confirm_send_required`。
- **test 与 real 模式都需确认**（统一安全规则）；无隐式发送。
- 守卫顺序：先解析确定性包（`no_selected_email_body_visual` / `selected_candidate_not_ready` /
  `email_body_plan_unavailable` / `selected_poster_record_not_found`），再 `confirm_send`，再 `recipients`。

## 5. 收件人处理 / Recipient handling

- **仅手动** `recipients[]`（free-text，非 EmailStr，避免一个坏地址 422 整批）。
- 空列表 → `422 recipients_required`。
- 去重：trim + 大小写不敏感、保序去重，回报 `deduplicated_count`（优先唯一收件人）。
- 逐个收件人**隔离**：非法地址 → `status=error, error_code=invalid_recipient`；provider 异常 →
  `status=error, error_code=provider_exception`；一个失败不影响其他证据。
- 无通讯录导入 / Excel / CRM / 定时 / 分组 / 统计。

## 6. EmailBodyPlan 消费行为 / Package consumption

- send **不重建/不重解释**正文：通过 `_resolve_workbench_email_package` 取得与 preview **完全相同**的确定性包
  （`email_body_plan` + `subject`/`preview_text`/`html`/`text` + `selected_body_visual_slot` + `body_visual_poster_key`）。
- send **不**选择候选视觉（由 `workbench.selected_email_body_visual` 决定）、**不**调用 Gemini 改事实、**不**生成新海报。
- `html`/`text`/`subject` 直接取自 PR-3S 装配输出；请求**不**接受任意 HTML/subject 覆盖。

## 7. 证据字段 / send_attempts evidence fields

每个 attempt（落 `workbench.send_attempts`，不存 provider 密钥）：
`recipient`、`mode(test|real)`、`status(sent|error|skipped)`、`provider`、`provider_message_id?`、`error_code?`、
`error_message?`、`attachment_types`、`at`（ISO 时间戳）、`selected_email_body_visual`、`body_visual_poster_key`、
`layout_type`（= `email_body_plan.layout_type`）、`subject`（快照）、`deduplicated`。
响应汇总：`total` / `sent_count` / `failed_count` / `skipped_count` / `deduplicated_count` / `attempts[]`。
（说明：`inline_only` provider 返回 `preview_only` → 记为 `skipped`；`resend` 实发 → `sent`。real 模式且有 sent 时
workbench `status` 置 `sent`。）

## 8. 测试与验证 / Tests & validation

`tests/poster2/test_workbench_email_send.py` —— **14 passed**：无选定 422；候选未就绪 422；plan 不可构建 422；
空收件人 422；confirm_send=false 422（test 与 real 都需确认）；有效收件人产生 attempts（inline→skipped 仍落证据）；
混合有效/无效隔离（fake resend：2 sent + 1 invalid error）；重复去重确定性（`deduplicated_count`）；attempt 含
selected_email_body_visual + body_visual_poster_key；含 layout_type=single_product_promo；含 subject 快照 + 时间戳；
未知 workbench 404；real 模式有 sent 时标记 workbench sent。**未发送真实邮件**（inline / fake provider）。

回归：PR-1+PR-2+PR-3+PR-3R+PR-3S+PR-4 workbench 套件 = **78 passed**；`test_api.py` = **35 passed**（CORS env）。
既有 `/api/v2/email/send` + 单收件人测试兼容。文档预检 `check_docs_router.py --all` → PASS。

## 9. 未实现 / Not implemented（边界）

- 无通讯录导入 / Excel / CRM / 定时 / 统计·打开·点击追踪 / dashboard / 自动化。
- 不改 renderer；不重写 `email_campaign_composite_v1` / `template_product_sheet_v1`。
- 不接受任意 HTML/subject 覆盖（严格消费 PR-3S 包）。190°C 不作平台规则。
- 无 tag / merge / push / 部署配置更改。测试不发真实邮件。

## 10. v1 商业后端闭环是否完成 / Is the v1 backend loop complete?

**是。** PR-1（workbench 真值）→ PR-2（双候选 + 选定视觉）→ PR-3（Email Banner + Assembly 预览）→ PR-3R（参考邮件
语法对齐）→ PR-3S（确定性 EmailBodyPlan）→ **PR-4（手动多收件人确认发送 + 证据）** 已贯通：产品与素材 → 生成海报主体
候选 → 选定视觉 → 拼接邮件预览 → 手动发送并留证。后端 v1 闭环完整。

## 11. 运营试用是否可申请 / Operator trial ready?

**可申请。** 后端闭环完整、确定性、可审计、发送受显式确认与逐个证据保护。建议运营试用前的人工准备：配置真实
provider（resend）+ 真实发件域；用 test 模式（发到自身/测试地址）先验证；再 real 模式手动发送给少量真实收件人。
（这些为运营/配置动作，非新代码。）

**STATUS: PR-4 MANUAL MULTI-RECIPIENT SEND EVIDENCE SUBMITTED FOR OWNER REVIEW**
