# CUISTANCE v1 · UI 资产槽位 + 选择契约修复状态 v1

Purpose: Fix Step-1 asset slots and Step-2 candidate selection so /cuistance_trial.html matches the approved CUISTANCE workflow.
Status: submitted (frontend fix + pushed; remote browser flow needs operator OPS login).
Scope: Frontend-only. No backend API/renderer/send change (no backend bug found; backend already supports all slots).
Source dependencies: frontend/cuistance_trial.html; app/schemas/poster2.py (ProductAssets/EmailBanner); v1 workbench endpoints.
Owner gate: Operator OPS login to exercise the remote flow.
Next action: After deploy refresh, operator runs Step1→Step3 on the remote page.

---

## 1. 根因确认 / Root causes confirmed

1. **Step 1 资产上传错误**：上传控件在卡片**外**（两行独立 file 输入），且 product_images 之外的可选槽位
   （gallery / atmosphere / email_banner.background-pattern）**未暴露、未 PATCH** → 后端观测 `gallery_images=[]`、
   `atmosphere=null`、`email_banner.background=null`。
2. **Step 2 选择未持久化 / Step 3 未解锁**：affiche 生成成功（`status=ready` + `poster_key`），但「选为邮件主体」
   的旧逻辑在某些路径下未确认 PATCH 结果 → `selected_email_body_visual=null`，Step 3 不解锁。
3. **重生成超时**：已 ready 的候选被「生成」按钮路径强制再次生成，超时；UI 未复用已存在的 ready 候选。

## 2. 资产槽位映射 / Asset slot mapping

每个槽位的上传控件现在**位于其可视卡片内**；保存时映射到后端字段：

| UI 卡片槽位 | 后端字段 |
|---|---|
| 产品主图（必填）| `product_assets.product_images[0]` |
| 第二产品图 | `product_assets.product_images[1]` |
| 画廊 1 / 2 / 3 | `product_assets.gallery_images[0..2]` |
| 氛围 / 场景图 | `product_assets.atmosphere = {url, is_truth:false}`（仅视觉，非业务事实）|
| 邮件 Logo | `email_banner.logo` |
| 邮件横幅 / 背景 | `email_banner.background` |
| 渠道名 / 活动标签 | `email_banner.channel_name / campaign_label` |

「使用示例素材」一键填充 产品主图/第二图/画廊1/Logo/横幅 的已托管示例 URL（氛围可选，留空）。

## 3. 文件变更 / Files changed

- `frontend/cuistance_trial.html`（+ `docs/cuistance_trial.html` 镜像）。
- `docs/poster2/cuistance_commercial_trial_ui_asset_selection_contract_fix_status_v1.md`（本文）+ README + log。
- **后端未改**（schema 已支持 product_images/gallery_images/atmosphere/email_banner.logo+background；无需改）。

## 4. Step 1 修复 / fixes

- 移除卡片外的独立 file 输入行；每个可视卡片内置上传/更换控件（含缩略图占位 → 上传/示例后就地更新）。
- 暴露并 PATCH：`product_images[0..1]`、`gallery_images[0..3]`、`atmosphere`、`email_banner.logo`、
  `email_banner.background`。
- 上传走 `/api/r2/presign-put` + PUT；R2 未启用 → 业务回退「当前环境未启用上传，请使用示例素材」。
- 「使用示例素材」填满必需槽位，affiche 主路线无需上传即可运行。缺产品主图 → 「请先添加产品主图或使用示例素材」。
- 氛围图保留「仅作视觉 / 非业务事实」标记（`is_truth:false`）。

## 5. Step 2 修复 / fixes

- affiche `ready` + `poster_key` 存在时：显示「产品海报已生成，可选为邮件主体」，**不强制重生成**。
- 「选为邮件主体」→ `PATCH /api/v2/workbench/{key}/selected-visual {selected_email_body_visual:"affiche"}`；
  成功后 **GET 工作台确认** `selected_email_body_visual`，再 `applySelectVisual` 并解锁 Step 3，提示「已选为邮件主体」。
- 选择按钮**不再自动触发生成**（无 ready 候选 → 「请先生成产品海报」）。
- 「重新生成」与「生成产品海报」**分离**；重生成 **504 超时不清除**已 ready 候选（提示「生成超时，可继续使用已生成
  版本或稍后重试」）。
- `refreshState()`：进入 Step 2 / 重新进入时，从后端读取 `poster_candidates` 与 `selected_email_body_visual`，
  反映 ready / 已选状态（页面刷新后状态正确）。

## 6. Step 3 门控 / gate

Step 3 仅在 `selected_email_body_visual ∈ {affiche, fiche}` 且选定候选 ready+poster_key 时解锁；**不**因 fiche 失败 /
R2 上传 / 真实发送 / 画廊·氛围可选项而阻断。

## 7. 错误处理 / error handling（业务可读，主屏）

401→「请先连接后端」；缺主图→「请先添加产品主图或使用示例素材」；生成超时→「生成超时，可继续使用已生成版本或稍后
重试」；fiche 失败→「简化产品页暂不可用，建议改用产品海报」；未选主体→「请先选择邮件主体」；其他→「生成失败，请查看
内部诊断」。工程字段仅在折叠「内部诊断 / 工程证据」。

## 8. 本地验证 / Local validation

- HTML 结构 OK；8 槽位 file 输入齐全；可见区禁用工程术语 = NONE；docs router PASS。
- 流程：保存（**product_images=2 / gallery_images=1 / email_banner.background=set**）→ 生成产品海报 ready →
  **选为邮件主体 → selected_email_body_visual=affiche → Step 3 解锁** → 预览邮件 200（single_product_promo）。
- presign 在本地（R2 关闭）→ 503 → 业务回退「当前环境未启用上传，请使用示例素材」。

## 9. 远程验证 / Remote validation

- 远程页面/CSS/资产已对齐 200；本修复已 push 到 trial 分支（部署刷新后生效）。
- **远程浏览器完整流程需运营/Owner 用 OPS 凭据在「后端连接」登录**；本环境无凭据，**不据本地单独判 GO**。
- 远程 `/api/v2/*` 401（未登录）→ 页面显示「请先连接后端」。

## 10. 剩余阻塞 / Remaining blockers

1. 远程走查需运营 OPS 登录（Owner 持有凭据）。
2. 远程上传取决于 R2 配置（否则「使用示例素材」）。
3. 远程真实发送取决于发件 provider（默认 test/inline 预览）。
4. 新页面需 trial 服务部署刷新到本提交后远程可见。

**STATUS: UI ASSET SLOT AND SELECTION CONTRACT FIX SUBMITTED FOR OWNER REVIEW**
