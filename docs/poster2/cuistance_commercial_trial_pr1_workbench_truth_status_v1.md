# CUISTANCE 商业试用 · PR-1 Workbench Truth Model — 实施状态 v1

Purpose: Record the PR-1 implementation of the backend-owned workbench truth model for the CUISTANCE commercial trial.
Status: submitted (PR-1 complete; awaiting Owner review).
Scope: Backend-owned workbench/product-truth/assets/banner model + 3 endpoints + tests ONLY. No PR-2…PR-4 behavior.
Source dependencies: docs/poster2/cuistance_commercial_trial_backend_alignment_plan_v1.md; app/main.py; app/schemas/poster2.py; app/services/poster_records.py; app/services/r2_client.py.
Owner gate: Owner review of PR-1 before PR-2 candidates + selected-visual persistence.
Next action: On approval, request PR-2 (Step-2 two candidates + selected_email_body_visual persistence).

---

## 1. 范围 / Scope

实现 backend alignment plan 的 **PR-1**：仅最小、后端自有的 workbench 真值模型（workbench/trial_campaign 存储 +
product_truth + product_assets + email_banner）+ 3 个端点 + 测试。**不**做 PR-2…PR-4 的任何行为。

## 2. 文件变更 / Files changed

| 文件 | 变更 |
|---|---|
| `app/schemas/poster2.py` | 新增 workbench 模型（WorkbenchAssetRef / WorkbenchAtmosphereAsset / ProductParameterRow / ProductTruth / ProductAssets / EmailBanner / WorkbenchCreateRequest / WorkbenchPatchRequest / WorkbenchRecordResponse）+ `model_validator` 导入 |
| `app/services/workbench_records.py` | **新增**：workbench 真值存储（R2 JSON + `/tmp` 兜底，镜像 poster_records 模式）：`generate_workbench_key` / `create_workbench_record` / `load_workbench_record` / `save_workbench_record` / `update_workbench_record` |
| `app/main.py` | 导入新模型 + workbench 存储；新增 3 个端点 |
| `tests/poster2/test_workbench_truth_model.py` | **新增**：19 个测试 |
| `docs/poster2/cuistance_commercial_trial_pr1_workbench_truth_status_v1.md` | 本文 |
| `docs/poster2/README.md` / `current_branch_execution_log_v1.md` | 索引 + 日志 |

## 3. 新增端点 / Endpoints added

- `POST /api/v2/workbench` — 创建 workbench 记录（返回完整记录）。
- `GET /api/v2/workbench/{workbench_key}` — 读取（404 = `workbench_record_not_found`）。
- `PATCH /api/v2/workbench/{workbench_key}` — 更新（仅替换提供的字段；校验在 schema 边界完成）。

## 4. 模型字段 / Model fields

- **顶层**：`workbench_key`、`created_at`、`updated_at`、`language(zh|fr)`、`status(draft|assets|candidates|email_ready|sent)`、
  `product_truth`、`product_assets`、`email_banner`、`poster_candidates({})`、`selected_email_body_visual(null)`、
  `email_package_ref(null)`、`recipients([])`、`send_attempts([])`。
- **product_truth**：`product_name`、`reference`、`description`（与参数分离）、`parameters[]`、`parameters_locked`。
- **parameter row**：`key(reference|capacity|power|voltage|dimensions|material|thermostat|other)`、`label`、`value`、
  `source(manual|imported|recognized)`、`state(pending|confirmed)`、`locked(bool)`。
- **product_assets**：`product_images[]`（≤2）、`gallery_images[]`（≤3）、`atmosphere`（可选，`is_truth` 仅 `false`）。
- **email_banner**：`logo`、`background`、`pattern`、`channel_name`、`campaign_label`、`selected_banner_ref`。

## 5. 真值与约束 / Truth + constraints

- **仅 URL/key**：所有资产字段拒绝 `data:`/`;base64,`（无二进制/base64）。
- **参数确认/锁定**：`locked` 行必须 `state=confirmed`；`parameters_locked=true` 要求至少一行且全部 `confirmed`。
- **190°C**：仅作为普通 `thermostat` 参数值被接受；**无温控行的产品同样有效** —— 190°C **不是平台规则**。
- **氛围图**：`is_truth` 仅允许 `false`（视觉用途，非业务事实）。
- **占位**：`poster_candidates`/`selected_email_body_visual`/`email_package_ref`/`recipients`/`send_attempts` 在 PR-1
  保持惰性占位（不实现）。

## 6. 测试与验证 / Tests & validation

新增 `tests/poster2/test_workbench_truth_model.py`（**19 passed**）覆盖：创建空 workbench、fr 语言、patch
product_truth、确认参数行、锁定已确认参数、未确认即锁定被拒、非法参数 key/state 被拒、base64 资产被拒
（product image + banner logo）、product_assets / email_banner 仅 url/key、往返读写一致、190°C 作为普通值且非必填、
非法 status 被拒、product_images 超过 2 张被拒、未知/缺失 workbench 404、PR-2…PR-4 占位惰性。

回归：`tests/poster2/test_api.py`（生成/邮件预览/发送）与新测试一并运行 = **54 passed**（设置
`CORS_ALLOW_ORIGINS` 后）。说明：6 个 generate-poster 错误/超时/CORS 用例在**未设置** `CORS_ALLOW_ORIGINS` 的本地
环境下断言 `access-control-allow-origin == 'https://zhaojfifa.github.io'` 会失败（返回 `*`）——这是**预先存在的
环境配置产物**（设置该 env 后全部通过），**与本 PR-1 无关**（在 main.py/schemas 改动 stash 出后仍同样失败）。

验证命令：
```
python3 scripts/check_docs_router.py --all              # 文档治理预检（PASS）
python -m pytest tests/poster2/test_workbench_truth_model.py -q   # 19 passed
CORS_ALLOW_ORIGINS=... python -m pytest tests/poster2/test_workbench_truth_model.py tests/poster2/test_api.py -q  # 54 passed
```

## 7. 未实现 / Not implemented（边界）

- 不生成 Affiche produit / Fiche produit simplifiée 候选（PR-2）。
- `selected_email_body_visual` 仅可空占位（PR-2）。
- 不做 Email Banner Module 解耦 / Email Assembly（PR-3）。
- 不改 `email_campaign_composite` / `template_product_sheet_v1` renderer。
- 不改 `/api/v2/email/preview` / `/api/v2/email/send`；不做多收件人发送（PR-4）；不发真实邮件。
- 无通讯录导入 / 定时 / 统计 / CRM / dashboard / 自动化。

## 8. PR-2 是否就绪 / Is PR-2 ready to request?

**就绪。** PR-1 提供了 workbench 真值底座（含 `poster_candidates` / `selected_email_body_visual` 占位），PR-2 可
在此之上接入两候选生成（复用 `generate-poster` 的 `template_id` 分派）与选定视觉持久化。**待 Owner 批准 PR-1 后再开
PR-2。**

**STATUS: PR-1 WORKBENCH TRUTH MODEL SUBMITTED FOR OWNER REVIEW**
