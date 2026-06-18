# CUISTANCE 商业试用 · PR-3S Email Body Plan — 实施状态 v1

Purpose: Record the PR-3S Email Body Plan layer so PR-4 sends a planned email package, not an ad-hoc assembly.
Status: submitted (PR-3S patch; awaiting Owner review).
Scope: Deterministic Email Body Plan + plan-driven assembly HTML, exposed in the workbench email preview. No send change, no renderer change.
Source dependencies: app/services/email/assembly.py; app/schemas/poster2.py; app/main.py; docs/poster2/cuistance_commercial_trial_pr3_email_banner_assembly_status_v1.md; docs/poster2/cuistance_commercial_trial_reference_email_html_extraction_v1.md.
Owner gate: Owner review of PR-3S before PR-4.
Next action: On approval, request PR-4 (manual multi-recipient confirmed send + evidence).

---

## 1. 为什么暂停 PR-4 / Why PR-4 was paused

PR-3 / PR-3R 显示：发邮件**不只是**发送生成的海报图。邮件正文本身需要一个**有计划、确定性**的结构——被选中的
海报/产品视觉必须插入到**规划好的正文槽位**，而不是松散拼进 HTML。若 PR-4 直接发送 ad-hoc 拼装的邮件，发送内容
将不可预测、不可审计。因此先加 **Email Body Plan 层**，PR-4 再在其之上发送**已规划的邮件包**。

> 注：本任务还**回退**了此前误启动的 PR-4 发送端点/schema/helper（见执行日志），使分支回到「无发送路径」状态；
> 现有单收件人 `/api/v2/email/send` 保持原样、未改。

## 2. Email Body Plan 概念 / Concept

确定性正文计划（`EmailBodyPlanView`）：
- `layout_type = single_product_promo`
- `container_width = 600`
- **固定模块顺序**：① `email_banner` → ② `title_intro` → ③ `selected_body_visual` → ④ `product_description` →
  ⑤ `cta` → ⑥ `contact_footer` → ⑦ `legal_footer`（每个模块带 `order` + `present`）
- `selected_body_visual_slot`：`source = workbench.selected_email_body_visual`、`candidate_type`(affiche|fiche)、
  `poster_key`(= `workbench.poster_candidates[selected].poster_key`)、`final_poster_url`(= 加载的
  `poster_record.final_poster.url`)
- `cta`：默认 `label = Nous contacter`，`href`（暂为 `#`；如未来有 mailto 联系则注入）

## 3. 生成视觉如何进入正文槽位 / How the visual enters the slot

- 仅由后端 `workbench.selected_email_body_visual` 决定选用 affiche|fiche（**非** Gemini / 前端）。
- 解析 `poster_candidates[selected].poster_key` → `load_poster_record(poster_key)` → `final_poster.url`。
- 该 URL **只**通过 `selected_body_visual` 模块进入装配 HTML（测试断言该 URL 在 HTML 中**恰出现一次**，且
  `email_banner` 在其之前）。

## 4. 什么是确定性的 / What is deterministic

- 模块顺序与 `container_width=600` 固定；HTML **由计划顺序生成**（`assembly.py` 按 `EMAIL_BODY_MODULE_ORDER`
  拼接存在的模块）。
- 选中视觉来源 = 后端真值（workbench → poster_record）。
- 复用 PR-3R 表格安全 600px shell、红 filet、法律/退订占位。

## 5. 文件变更 / Files changed

| 文件 | 变更 |
|---|---|
| `app/schemas/poster2.py` | 新增 `SelectedBodyVisualSlot` / `EmailBodyPlanModule` / `EmailBodyPlanCta` / `EmailBodyPlanView`；`EmailAssemblyPreviewResponse` 增加 `email_body_plan` |
| `app/services/email/assembly.py` | `build_email_assembly` 重构为**按计划模块顺序生成 HTML**；新增 `poster_key` 参数；返回 `email_body_plan` |
| `app/main.py` | 预览端点传 `poster_key`、返回 `email_body_plan`（PR-4 发送端点/schema/helper 已回退） |
| `tests/poster2/test_workbench_email_body_plan.py` | **新增**：11 个测试 |
| docs status + README + log | 索引 + 日志 |

## 6. 测试与验证 / Tests & validation

`tests/poster2/test_workbench_email_body_plan.py` —— **11 passed**：预览含 `email_body_plan`；`layout_type ==
single_product_promo`；`container_width == 600`；模块顺序（email_banner 在 selected_body_visual 之前，order 1..7）；
affiche/fiche 槽位解析对应 poster_key；`final_poster_url` 来自加载的 poster_record（非前端）；HTML 中选中视觉仅经槽位
出现一次且横幅在前；CTA 默认 `Nous contacter`；legal/contact footer 模块存在；未选 → 422。

回归：PR-3 + PR-3R 邮件装配 = **19**；+ PR-1 + PR-2 = **53**；`test_api.py` = **35**（CORS env）。
现有 `/api/v2/email/preview`、`/api/v2/email/send` 兼容、未改。文档预检：`check_docs_router.py --all` → PASS。

## 7. 未实现 / Not implemented（边界）

- 不实现 PR-4；不加发送端点；不改 `/api/v2/email/send`；不多收件人；不发真实邮件。
- 不改 renderer；不重写 `email_campaign_composite_v1` / `template_product_sheet_v1`。
- 联系/社交图标行、完整联系模型、真正 body-only 横幅解耦 = 仍为 future（见 PR-3 / PR-3R 文档）。
- 190°C 不作平台规则；无 contact import / CRM / 定时 / 统计 / dashboard / 自动化；无 tag/merge/push/部署配置更改。

## 8. 为什么 PR-4 现在可安全发送 / Why PR-4 can safely send after this layer

PR-4 发送将消费 `email_body_plan` + 装配输出（确定性 HTML/文本）——被选中视觉位置固定、来源可审计、模块顺序稳定。
发送的是**已规划的邮件包**，而非临时拼装，从而保证：可预测、可复现、可作为证据记录。

**STATUS: PR-3S EMAIL BODY PLAN SUBMITTED FOR OWNER REVIEW**
