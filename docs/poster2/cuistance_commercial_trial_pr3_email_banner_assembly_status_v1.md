# CUISTANCE 商业试用 · PR-3 Email Banner + Assembly Preview — 实施状态 v1

Purpose: Record the PR-3 implementation of the email-level Email Banner Module + Email Assembly preview.
Status: submitted (PR-3 complete; awaiting Owner review).
Scope: Email-level banner assembly + workbench email preview that consumes selected_email_body_visual. No send change, no renderer rewrite.
Source dependencies: docs/poster2/cuistance_commercial_trial_pr2_candidates_selected_visual_status_v1.md; app/main.py; app/services/email/copy_optimizer.py; app/services/email/attachments.py; app/services/workbench_records.py.
Owner gate: Owner review of PR-3 before PR-4 (manual multi-recipient send + evidence).
Next action: On approval, request PR-4.

---

## 1. 范围 / Scope

实现 backend alignment plan 的 **PR-3**：把 Logo/Banner 提升为**邮件层一等模块（Email Banner Module）**，并实现
**Email Assembly 预览**——确定性消费 `workbench.selected_email_body_visual`，拼装「横幅 + 选定主体视觉 + 引言/CTA +
页脚/联系 + 附件就绪」。**不**改 renderer，**不**改发送，**不**重写 `email_campaign_composite_v1` /
`template_product_sheet_v1`。

## 2. 文件变更 / Files changed

| 文件 | 变更 |
|---|---|
| `app/schemas/poster2.py` | 新增 `EmailAssemblyBannerView` / `EmailAssemblyBodyVisual` / `EmailAssemblyPreviewResponse` |
| `app/services/email/assembly.py` | **新增**：`build_email_assembly(...)`（邮件层拼装；横幅来自 `workbench.email_banner`；intro 来自 `product_truth.description`） |
| `app/main.py` | 导入 assembly + 新模型；新增 1 个 thin 端点；**复用**现有 draft / 附件路径 |
| `tests/poster2/test_workbench_email_assembly.py` | **新增**：12 个测试 |
| docs status + README + log | 索引 + 日志 |

## 3. 端点 / Endpoints

新增（thin，最小变更）：
- `POST /api/v2/workbench/{workbench_key}/email/preview` —— 装配并返回完整邮件预览包。

**未改**：现有 `POST /api/v2/email/preview`（按 `poster_key`）保持原样、向后兼容；`/api/v2/email/send` 未触碰。

## 4. Email Banner Module 行为 / Banner module behavior

- 源 = `workbench.email_banner`：`logo` / `background` / `pattern` / `channel_name` / `campaign_label` /
  `selected_banner_ref`。
- 在**邮件装配层**渲染（深色品牌页眉 + logo + 渠道/活动 + 红色收口线），**不作为产品海报主体真值**。
- **affiche 与 fiche 共用**同一横幅模块。
- 响应在 `banner` 字段回显横幅视图，HTML 中含邮件层横幅头部。

## 5. 选定视觉消费 / Selected visual consumption（确定性）

- 读取 `workbench.selected_email_body_visual`（必须 `affiche` | `fiche`）。
- 解析 `workbench.poster_candidates[selected].poster_key` → `load_poster_record(poster_key)` →
  `final_poster.url` 作为邮件主体视觉图。
- **视觉只由后端 workbench 选择决定**——Gemini / 前端状态**不**参与选择。
- 失败语义：未选 → `422 no_selected_email_body_visual`；选中候选无 poster_key/未就绪 → `422
  selected_candidate_not_ready`；选中候选的 poster_record 缺失 → `404 selected_poster_record_not_found`。

## 6. 主题/引言/CTA + 附件就绪 / Subject·Intro·CTA + attachments

- `subject` / `preview_text`：来自现有 `build_email_draft_for_poster_record`（确定性 + 可选**已落地的** Gemini 措辞
  优化，全部经 grounding 校验）。
- `intro`：来自 `product_truth.description`（确认真值），回退到 draft preview。
- `cta_label`：默认 `Nous contacter`。
- **附件就绪**：复用现有 `build_email_assets_for_record`（受 `EMAIL_ATTACHMENT_ENABLED` /
  `..._BUILD_ON_PREVIEW` 控制）；返回 `email_assets` / `available_attachment_types` /
  `buildable_attachment_types`。**预览就绪，PR-3 不改发送。**

## 7. AI/参数边界 / AI + parameter safety

- `build_canonical_copy_input` 暴露给 Gemini 的字段**仅**：brand/agent/title/subtitle/summary_points/
  final_poster_url —— **结构上不含** `product_truth.parameters`。因此 **Gemini 无法发明或更改技术参数**。
- 测试证实：Gemini 收到的 canonical 输入中无 `parameters`、不含参数值（如 `190`）；预览后 workbench
  `product_truth.parameters` 不变。**190°C 仍是普通参数，非平台规则。**

## 8. 横幅解耦边界（重要）/ Banner decoupling boundary — NO Owner Decision Needed

- PR-3 在**邮件装配层**新增了一等 Email Banner Module，**无需改 renderer**即可让最终邮件预览**显式包含 横幅 +
  选定主体视觉**。
- **过渡状态（已记录）：** 候选主体视觉（affiche 的 composite、fiche 的 product_sheet）目前仍由各自 renderer 在主体内
  自带 logo/banner。PR-3 **未深改 renderer**；通过 `body_visual_contains_own_banner` 标志把该过渡状态透明上报（仅诊断）。
- 完整的 body-only 渲染需要 renderer 合同改造，**明确不在 PR-3 范围**。**本 PR 未触及该边界 → 无需 Owner 决策。**

## 9. 测试与验证 / Tests & validation

`tests/poster2/test_workbench_email_assembly.py` —— **12 passed**：选 affiche/fiche 各用对应 poster_key；未选 →
422；选中候选无 poster_key → 422；预览含 Email Banner Module（logo/channel/campaign + 深色页眉）；预览含选定
final_poster URL；切换选定 → 主体确定性切换；Gemini 不能改技术参数（canonical 无 parameters 且参数不变）；190°C 普通
参数（含无温控也能预览）；过渡 banner 标志；未知 workbench 404；intro 源自 description + CTA `Nous contacter`。

回归：`test_workbench_truth_model.py`（19）+ `test_workbench_candidates.py`（15）= **34 passed**；
`test_api.py` = **35 passed**（设 `CORS_ALLOW_ORIGINS`）。现有 `/api/v2/email/preview`、`/send` 测试保持兼容。
文档预检：`python3 scripts/check_docs_router.py --all` → PASS（ERROR=0）。

**CORS 预先存在产物（如实记录）：** `test_api.py` 6 个 generate-poster 错误/超时用例在未设 `CORS_ALLOW_ORIGINS`
本地环境断言 origin 头失败（得 `*`）——预先存在环境产物（PR-1 已记录，与本 PR 无关）。

## 10. 未实现 / Not implemented（边界）

- 不实现 PR-4；不改 `/api/v2/email/send`；不实现多收件人；不发真实邮件。
- 不改 renderer 内部；不重写 `email_campaign_composite_v1` / `template_product_sheet_v1`；不改 composite 真值门。
- 190°C 不作平台规则；无通讯录导入 / 定时 / 统计 / CRM / dashboard / 自动化；无 tag/merge/push/部署配置更改。

## 11. PR-4 是否就绪 / Is PR-4 ready to request?

**就绪。** PR-3 已提供完整的 Email Assembly 预览包（含选定主体、横幅、intro/CTA、附件就绪）。PR-4 可在此基础上做
**手动多收件人确认发送 + 证据记录**（复用现有 send provider，扩展 `recipients[]` + 逐个隔离）。**待 Owner 批准 PR-3
后再开 PR-4。**

**STATUS: PR-3 EMAIL BANNER AND ASSEMBLY PREVIEW SUBMITTED FOR OWNER REVIEW**

---

## PR-3R 补丁 / Patch — Reference Email HTML alignment (2026-06-18)

Owner 在 PR-4 前要求一个小补丁：用新提供的参考 HTML（`~/poster/SOP/ttt.html`、`ttt2.html`）提取邮件结构语法并轻量
对齐 Email Assembly。提取文档：
[`cuistance_commercial_trial_reference_email_html_extraction_v1.md`](cuistance_commercial_trial_reference_email_html_extraction_v1.md)。

- **采用（最小增量，仅 `app/services/email/assembly.py`）：** 容器 640px → **600px** 并包入**表格安全 shell**
  （`<table role="presentation" width="600">`）；横幅下新增**显式红色 filet** `#E1002A`；页脚新增**法律/退订占位**
  （非功能 `href="#"`，无第三方退订）。保留 Email Banner Module / 选定主体视觉 / intro·CTA / 附件就绪；端点
  `POST /api/v2/workbench/{key}/email/preview` 不变；`/api/v2/email/send` 未触碰。
- **未复制：** Zoho/Mailchimp 脚本、追踪、分享/评论 widget、view-in-browser、隐藏 campaign IDs、第三方退订实现、原始
  邮件 HTML 整体（ttt2 含 103 处第三方命中、ttt 含 7 处，均不入库）。
- **测试：** `tests/poster2/test_workbench_email_assembly_reference.py`（**7 passed**）断言 600px 表格 shell / 横幅模块 /
  红 filet / 选定主体视觉 / CTA / 页脚+法律占位 / **无第三方追踪**。PR-3 原 12 + PR-3R 7 = 19 passed；PR-1+PR-2 = 34；
  `test_api.py` = 35（CORS env）。
- **PR-3R 性质：** code+docs（最小增量）。**未实现 PR-4。**

**STATUS: PR-3R REFERENCE EMAIL HTML EXTRACTION PATCH SUBMITTED FOR OWNER REVIEW**
