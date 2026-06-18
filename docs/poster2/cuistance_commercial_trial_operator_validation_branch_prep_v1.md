# CUISTANCE v1 · 运营验证分支准备 v1

Purpose: Prepare a clean operator-trial branch + validation package for human verification of the completed CUISTANCE v1 backend loop.
Status: submitted (branch PREPARED — not yet created/committed/pushed; awaiting Owner approval).
Scope: Branch-prep + validation package only. No new features, no scope change, no send-logic/renderer change.
Source dependencies: docs/poster2/cuistance_commercial_trial_pr4_manual_send_evidence_status_v1.md; docs/poster2/cuistance_commercial_trial_full_flow_smoke_result_v1.md; app/main.py; app/services/*; tests/poster2/*.
Owner gate: Owner approval to (a) create the trial branch with a scoped commit and (b) push/deploy.
Next action: On approval, run the proposed scoped-commit + branch-create commands; do NOT push/merge/tag without explicit approval.

---

## 1. 分支 / Branch

- **Trial branch name:** `trial/poster2-cuistance-v1-operator-trial`
- **Base branch:** `feature/poster2-email-campaign-composite-remote-smoke-v1`
- **Base commit (HEAD):** `11ece2616ad9664480e8468deebd8cf3efe416a7` (`11ece26`)
- **Status:** **PREPARED, not created.** See §9 — the PR-1…PR-4 work is currently **uncommitted in the working
  tree**; a curated scoped commit is required before the branch is "clean". Branch creation + commit + push are
  **held for Owner approval**.

## 2. Docs router 结果 / result

`python3 scripts/check_docs_router.py --all` → **PASS** (OK=5, WARN=15 legacy/advisory, **ERROR=0**).

## 3. 测试结果 / Test result

| Suite | Result |
|---|---|
| test_workbench_truth_model.py (PR-1) | ✅ |
| test_workbench_candidates.py (PR-2) | ✅ |
| test_workbench_email_assembly.py (PR-3) | ✅ |
| test_workbench_email_assembly_reference.py (PR-3R) | ✅ |
| test_workbench_email_body_plan.py (PR-3S) | ✅ |
| test_workbench_email_send.py (PR-4) | ✅ |
| **6 trial suites combined** | **78 passed** |
| tests/poster2/test_api.py (existing) | **35 passed** with `CORS_ALLOW_ORIGINS` set (known caveat: 6 generate-poster error/CORS cases fail only **without** that env — pre-existing environment artifact, unrelated to this work) |

## 4. 功能就绪矩阵 / Feature readiness matrix

| Stage | Capability | State |
|---|---|---|
| PR-1 | workbench truth model (product_truth / assets / email_banner; structured params; 190°C ordinary) | ✅ in working tree |
| PR-2 | two candidates (affiche/fiche) + `selected_email_body_visual` persistence + regenerate-clears | ✅ |
| PR-3 | Email Banner Module + Email Assembly preview | ✅ |
| PR-3R | reference email grammar (600px shell, red filet, footer/legal); no tracking copied | ✅ |
| PR-3S | deterministic `EmailBodyPlan` (fixed module order; selected visual via planned slot) | ✅ |
| PR-4 | manual multi-recipient confirmed send + per-recipient evidence (`send_attempts`) | ✅ |
| Smoke | full-flow runtime smoke result (affiche ready; preview pass; test send evidence) | ✅ recorded |

**Scope confirmation:** `app/` changes are exactly the workbench/email PR-1…PR-4 files (`main.py`,
`schemas/poster2.py`, new `services/workbench_records.py`, `services/workbench_candidate_generation.py`,
`services/email/assembly.py`, `services/email/workbench_send.py`). **No tracked frontend modifications; no
deploy / render / CI / requirements / `.env` changes.**

## 5. 运行时配置就绪（无密钥）/ Runtime config readiness (no secrets)

| Var / setting | This environment |
|---|---|
| `EMAIL_PROVIDER` | unset |
| `EMAIL_SEND_ENABLED` | unset |
| `EMAIL_PREVIEW_ENABLED` | unset |
| `EMAIL_OUTBOX_ENABLED` | unset |
| `RESEND_API_KEY` | **missing** |
| `RESEND_FROM_EMAIL` / `EMAIL_FROM` / `EMAIL_FROM_NAME` / verified sender | **missing / unset** |
| `resend.is_configured` | **False** |
| R2 configured | **False** |
| Vertex configured | **False** |
| attachment enabled | False |
| Gemini optimizer enabled | False |

> 诚实结论：本地运行时**未配置任何邮件 provider / Vertex / R2**。可验证范围 = affiche 主路线 + 预览 + test 模式
> inline 证据；**真实发送与 fiche 在本环境不可用**。

## 6. 已知限制 / Known limitations

1. **fiche 路线** 在 **Vertex 缺失**时失败（`background_prepare_failed` — "Vertex Imagen3 client is not
   initialised"）。affiche 不依赖 Vertex。
2. **真实发送** 在 **Resend 缺失**时不可用（`inline_only`→`preview_only/skipped`；`resend`→"Resend is not
   configured."）。无 `provider_message_id` = 无真实投递。
3. **R2 缺失**时海报以 `inline_data_url` 内联（邮件正文图为大 data URL；生产应配 R2 得 HTTPS URL）。
4. （非阻塞）Gemini / 附件未启用——可选；确定性文案与无附件预览正常。

## 7. 手动验证步骤 / Manual validation steps

**主路线（必做，本环境即可）:**
1. `POST /api/v2/workbench`（language=fr）→ 记 `workbench_key`。
2. `PATCH /api/v2/workbench/{key}` 写 `product_truth`（CUISTANCE 样例，EF132V；参数 confirmed；190°C 仅普通温控值）。
3. `PATCH /api/v2/workbench/{key}` 写 `product_assets`（产品图 url/key）+ `email_banner`（logo + channel + campaign）。
4. `POST /api/v2/workbench/{key}/candidates/affiche/generate` → 期望 `status=ready` + `poster_key`。
5. `PATCH /api/v2/workbench/{key}/selected-visual` `{selected_email_body_visual:"affiche"}`。
6. `POST /api/v2/workbench/{key}/email/preview` → 核对：`email_body_plan`、`selected_body_visual_slot.poster_key`、
   `final_poster_url`、600px shell、Email Banner Module、CTA `Nous contacter`、footer/legal `Se désabonner`。
7. `POST /api/v2/workbench/{key}/email/send` `{recipients:["<internal-test>"], mode:"test", confirm_send:true,
   delivery_mode:"inline_only"}` → 期望 `skipped/preview_only`（无真实投递）。
8. `GET /api/v2/workbench/{key}` → 检查 `send_attempts`（recipient/status/provider/error_code/at/
   selected_email_body_visual/body_visual_poster_key/layout_type/subject）。

**可选（仅当对应配置就绪）:**
- **fiche 路线**：仅当 Vertex 配置后，`candidates/fiche/generate` → ready。
- **真实内部发送**：仅当 Resend + 已验证发件域配置后，`mode=test`（验 `provider_message_id`）再 `mode=real` 发给
  **Owner 批准的内部地址**（**严禁**客户名单）。
- **HTTPS 海报 URL**：仅当 R2 配置后，`final_poster_url` 为 https 而非 data URL。

## 8. GO / HOLD 建议 / Recommendation

- **逻辑就绪：GO**（后端 v1 闭环逻辑完整、确定性、可审计；78 trial 测试通过；docs router PASS；范围干净）。
- **真实客户发送：HOLD**（本环境 Resend/Vertex/R2 未配置）。运营试用应在**已配置环境**进行，先 test 模式验
  `provider_message_id`，再 real 模式发 Owner 批准的内部地址。

## 9. 分支创建（提议命令，待 Owner 批准；勿擅自 push）/ Proposed branch commands

> **关键发现：** PR-1…PR-4 + 治理 + trial 文档目前**未提交**（HEAD 仍为 `11ece26`），且工作树含大量**无关未跟踪
> 文件**（catalog_hero/hybrid 文档、`.DS_Store`、字体、harness-x 等，非本次范围）。因此需**精确范围提交**，不要
> `git add -A`。以下命令**仅建议**，未执行：

```bash
# 0) 从已证 HEAD 切出 trial 分支
git checkout -b trial/poster2-cuistance-v1-operator-trial 11ece26

# 1) 仅添加 PR-1..PR-4 范围内的代码 + 测试 + 治理 + CUISTANCE 文档（不要 git add -A）
git add app/main.py app/schemas/poster2.py \
        app/services/workbench_records.py app/services/workbench_candidate_generation.py \
        app/services/email/assembly.py app/services/email/workbench_send.py \
        tests/poster2/test_workbench_truth_model.py tests/poster2/test_workbench_candidates.py \
        tests/poster2/test_workbench_email_assembly.py tests/poster2/test_workbench_email_assembly_reference.py \
        tests/poster2/test_workbench_email_body_plan.py tests/poster2/test_workbench_email_send.py \
        scripts/check_docs_router.py docs/DOCS_INDEX_AND_ROUTER.md PROJECT_STATUS.md \
        docs/poster2/README.md docs/poster2/current_branch_execution_log_v1.md \
        docs/poster2/cuistance_commercial_trial_*.md \
        docs/poster2/ui_mockups/cuistance_commercial_trial_v1/

# 2) 单次范围提交（不含 .DS_Store / 无关 catalog_hero/hybrid churn）
git commit -m "feat(poster2): CUISTANCE v1 workbench backend loop (PR-1..PR-4, PR-3R/3S) + docs governance + operator-trial prep" \
  -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"

# 3) 推送（仅 Owner 明确批准后执行）
# git push -u origin trial/poster2-cuistance-v1-operator-trial
```

- **未执行任何**：未切分支、未 commit、未 push、未 merge、未 tag、未改部署配置。
- 建议提交前把 `.DS_Store` 加入 `.gitignore`（独立小动作）。

**STATUS: OPERATOR VALIDATION BRANCH PREP SUBMITTED FOR OWNER REVIEW**
