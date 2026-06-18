# CUISTANCE 商业试用 · PR-2 Candidates + Selected Visual — 实施状态 v1

Purpose: Record the PR-2 implementation of Step-2 email body visual candidates + selected-visual persistence.
Status: submitted (PR-2 complete; awaiting Owner review).
Scope: Generate affiche/fiche candidates by reusing /api/v2/generate-poster; persist poster_key refs + one selected visual. No PR-3 behavior.
Source dependencies: docs/poster2/cuistance_commercial_trial_pr1_workbench_truth_status_v1.md; docs/poster2/cuistance_commercial_trial_backend_alignment_plan_v1.md; app/main.py; app/services/workbench_records.py; app/services/poster_records.py.
Owner gate: Owner review of PR-2 before PR-3 (Email Banner Module decoupling + Email Assembly).
Next action: On approval, request PR-3.

---

## 1. 范围 / Scope

实现 backend alignment plan 的 **PR-2**：第二步两个邮件主体视觉候选的生成与「选定视觉」持久化。**复用**现有
`/api/v2/generate-poster` 代码路径，**不**分叉 renderer，**不**复制 poster_record 真值。不做 PR-3（横幅解耦 /
Email Assembly）。

## 2. 文件变更 / Files changed

| 文件 | 变更 |
|---|---|
| `app/schemas/poster2.py` | 新增 `CandidateType` + `WorkbenchSelectVisualRequest` |
| `app/services/workbench_candidate_generation.py` | **新增**：`build_candidate_payload(record, candidate_type)`（workbench 真值 → generate-poster 载荷，纯映射，无 renderer） |
| `app/services/workbench_records.py` | 新增 `set_poster_candidate(...)`、`select_email_body_visual(...)`（候选引用 + 选定视觉规则） |
| `app/main.py` | 导入新模型/服务；新增 2 个端点；候选生成**复用** `generate_poster_v2` |
| `tests/poster2/test_workbench_candidates.py` | **新增**：15 个测试 |
| docs status + README + log | 索引 + 日志 |

## 3. 端点 / Endpoints

新增（thin orchestration，不复制 renderer）：
- `POST /api/v2/workbench/{workbench_key}/candidates/{candidate_type}/generate` —— 从 workbench 真值生成一个候选；
  内部**复用** `generate_poster_v2`（同一 `/api/v2/generate-poster` 逻辑），仅把 `poster_key` 引用写入 workbench；
  返回更新后的 workbench 记录。
- `PATCH /api/v2/workbench/{workbench_key}/selected-visual` —— 持久化唯一选定视觉（affiche|fiche）。

复用（未改）：`/api/v2/generate-poster`、`/api/v2/posters/{poster_key}`、PR-1 的 workbench CRUD。

## 4. 候选模型字段 / Candidate fields

`workbench.poster_candidates[candidate_type]`：
- `poster_key`（仅引用；候选真值留在 `poster_record`）
- `status`：`ready | failed`
- `generated_at`（ISO）
- `template_id`（`email_campaign_composite_v1` | `template_product_sheet_v1`）
- `contract_review_summary`（轻量摘要：structure_complete / render_engine_used / degraded / callout_count；**非**完整
  poster_record 真值）

`workbench.selected_email_body_visual`：`null | affiche | fiche`（标量，唯一）。

## 5. 候选类型与映射 / Candidate types + input mapping

- **affiche** → `template_id=email_campaign_composite_v1`，`renderer_mode=puppeteer`（业务真值仍确定性 case001）。
- **fiche** → `template_id=template_product_sheet_v1`，`renderer_mode=auto`；当有第二张产品图时带
  `product_secondary_image`（双图）。

载荷由 workbench 真值构建：`product_name`/`reference`/`description`、`product_images`（主图 + 可选第二张）、
`gallery_images`、`atmosphere`（`is_truth=false` 作 substrate）、`email_banner.logo`（PR-2 暂保留在生成路径，横幅解耦
留 PR-3）。`features` 置空 → 候选保留其已验证的默认 contract 门（如 composite callout_count=3）。

## 6. 选择规则 / Selection rules

- 选定值必须恰为 `affiche` 或 `fiche`；标量字段，选一个即替换上一个。
- 不能选 **无 poster_key 或非 ready** 的候选（→ `422 candidate_not_ready`）。
- **重新生成被选中的候选** → `selected_email_body_visual` 复位为 `null`。
- **重新生成未被选中的候选** → 不影响当前选择。
- 无版本历史；无多候选画廊；无自动选择（仅手动选择）。

## 7. 测试与验证 / Tests & validation

`tests/poster2/test_workbench_candidates.py` —— **15 passed**：生成 affiche/fiche 候选并存 poster_key；fiche 接受
主图+第二张（也验证单图无 secondary）；候选 poster_key 可经 `/api/v2/posters/{key}` 读取；选 affiche/fiche；不能选
未就绪；选择替换；重生成被选中候选清除选择；重生成未选候选保留选择；GET 返回候选+选定；190°C 仍为普通参数（无温控行
也能生成）；缺产品图 → 422；非法候选类型 → 422；未知 workbench → 404。

回归：`tests/poster2/test_workbench_truth_model.py` = **19 passed**；`tests/poster2/test_api.py` = **35 passed**
（设置 `CORS_ALLOW_ORIGINS` 后）。

文档预检：`python3 scripts/check_docs_router.py --all` → PASS（ERROR=0）。

**CORS 预先存在产物（如实记录）：** `test_api.py` 中 6 个 generate-poster 错误/超时用例在**未设置**
`CORS_ALLOW_ORIGINS` 的本地环境会断言 `access-control-allow-origin == origin` 失败（得到 `*`）——这是**预先存在的环境
配置产物**（PR-1 已记录，与本 PR 无关；设置该 env 后 35/35 通过）。

## 8. 未实现 / Not implemented（边界）

- 不解耦 Email Banner Module；不实现 Email Assembly（PR-3）。
- 不改 `/api/v2/email/preview`、`/api/v2/email/send`；不实现多收件人；不发真实邮件（PR-4）。
- 不改 renderer 内部；不改 `email_campaign_composite` 真值门 / `template_product_sheet_v1` contract。
- 190°C 不作平台规则；无通讯录导入 / 定时 / 统计 / CRM / dashboard / 自动化。
- 无 tag / merge / push / 部署配置更改。

## 9. PR-3 是否就绪 / Is PR-3 ready to request?

**就绪。** PR-2 已提供：两候选生成（复用生成路径）、`poster_candidates` 引用、唯一 `selected_email_body_visual` 持久化
与重生成清除规则。PR-3 可在此基础上做 Email Banner Module 解耦 + Email Assembly 预览（消费选定候选的 `poster_key`）。
**待 Owner 批准 PR-2 后再开 PR-3。**

**STATUS: PR-2 CANDIDATES AND SELECTED VISUAL SUBMITTED FOR OWNER REVIEW**
