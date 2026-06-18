# CUISTANCE 商业试用 · 参考邮件 HTML 结构提取 v1 (PR-3R)

Purpose: Extract reusable email structure grammar from the reference CUISTANCE/Technitalia emails and lightly align PR-3 Email Assembly with them.
Status: submitted (PR-3R patch; awaiting Owner review).
Scope: Structure-grammar extraction + a minimal additive Email Assembly alignment. NO raw HTML copy, NO tracking/scripts, NO renderer change.
Source dependencies: ~/poster/SOP/ttt.html; ~/poster/SOP/ttt2.html; app/services/email/assembly.py; docs/poster2/cuistance_commercial_trial_pr3_email_banner_assembly_status_v1.md.
Owner gate: Owner review of PR-3R before PR-4.
Next action: On approval, request PR-4 (manual multi-recipient send + evidence).

---

## 1. 检查的源文件 / Source files inspected

| 文件 | 体量 | 来源/类型 | 关键宿主 |
|---|---|---|---|
| `~/poster/SOP/ttt.html` | 22.7 KB / 666 行 / 31 tables | CUISTANCE «NOUVEAUTÉ» Mailchimp 邮件 | `mcusercontent.com/43cb582d3a744559eaf77eab0/...` |
| `~/poster/SOP/ttt2.html` | 114 KB / 2091 行 / 40 tables | Technitalia（via CUISTANCE）Zoho Campaigns 邮件 | `stratus.campaign-image.eu/images/44519000011065166_...` |

两者均为**表格式（table-based）600px 邮件**。仅提取**结构语法 + 资产 URL 清单**，**不**复制原始 HTML。

## 2. 有用结构块 / Useful structure blocks

1. **600px 邮件容器** —— `max-width:600px`（两文件均有）+ Zoho 版 `width:600px` / `width="600"` 表格列宽。居中
   单列；外层 `background` 浅灰，内容卡片白底。
2. **顶部横幅模块** —— 全宽横幅图作为第一块（ttt: Mailchimp `0a50184e` 页眉；ttt2: `bandeau_technitalia` /
   `banniere_1` / `banniere_2`）。深色品牌底（`#333333` / `#515151` / `#000000`）。
3. **红/橙强调分隔条（filet）** —— 横幅与正文之间的细色条；参考色 `#df3004`（ttt）、`#db4b38` / `#eb7a00`（ttt2）。
4. **标题 / 产品引言块** —— 横幅下的标题 + 简短引言段落（产品名 + 一句卖点）。
5. **选定主体视觉位置** —— 产品图块（ttt2 `rechauds_(1).png`；ttt Mailchimp 产品图），位于引言下、CTA 上。
6. **CTA 块** —— 单一按钮/链接（«contacter» 等）；ttt2 多处 CTA-ish 锚点（22）。
7. **联系/页脚块** —— 联系信息行；ttt2 含**4 图标联系行**：`telephone_(1).png` / `email.png` / `catalogue_(2).png`
   / `site_(1).png`。
8. **社交/联系图标行** —— ttt2 社交三图标：`..._1_...fb5.png`（Facebook）/ `..._2_...lin5.png`（LinkedIn）/
   `..._3_...insta5.png`（Instagram）。
9. **法律/退订页脚占位** —— 页脚末尾的退订/法律行（仅作**占位**，不复制第三方退订实现）。
10. **资产 URL 清单** —— 见 §4。

## 3. 有用视觉令牌 / Useful visual tokens

- 容器宽度：**600px**（对齐参考；PR-3 原为 640px）。
- 强调色：参考 `#df3004`/`#db4b38`/`#eb7a00`（橙红）；本平台沿用既定品牌红 **`#E1002A`**（更接近 CUISTANCE
  emblem）作为 filet/CTA，不照搬参考的橙红。
- 深色页眉底：`#1f2329`（本平台既有，近似参考 `#333/#515151`）。
- 页脚底：浅灰 `#f5f5f5`/`#f2f2f2`（参考）→ 本平台 `#f7f8fa`。
- 单列、表格安全、图片 `max-width:100%`、圆角轻。

## 4. 资产 URL 清单 / Asset URL inventory（仅记录，未下载入库）

**ttt.html（CUISTANCE Mailchimp）**
- 页眉横幅：`https://mcusercontent.com/43cb582d3a744559eaf77eab0/images/0a50184e-bee5-bf53-0c1b-45fb63855e78.png`
- 产品图：`.../15545c0b-96a8-fbf3-e83c-bb9d69c44d7a.jpg`、`.../da42d592-d955-23d6-9560-a7a501b2bb24.jpg`

**ttt2.html（Technitalia Zoho）** host `https://stratus.campaign-image.eu/images/44519000011065166_...`
- 横幅：`..._zc_v1_1690285503645_bandeau_technitalia_(6).png`、`..._zc_v1_1693294036250_banniere_1_(6).png`、
  `..._zc_v1_1693294050586_banniere_2_(8).png`
- 产品：`..._zc_v1_1693233131044_rechauds_(1).png`
- 联系图标：`..._telephone_(1).png`、`..._email.png`、`..._catalogue_(2).png`、`..._site_(1).png`
- 社交图标：`..._1_..._zcsclwgtfb5.png`（FB）、`..._2_..._zcsclwgtlin5.png`（LinkedIn）、
  `..._3_..._zcsclwgtinsta5.png`（Instagram）

> 注：横幅候选 `0a50184e...` / `banniere_1` 已在 UI Mockup（`ui_mockups/.../assets/banner_option_0{1,2}.jpg`）落地；
> 本 PR-3R **不**新增下载，仅记录清单供 `email_banner` 运营上传时参考。

## 5. 绝不复制 / What must NOT be copied

- Zoho / Mailchimp 脚本、追踪像素、`list-manage`/`campaign-image` 追踪参数。
- 分享 widget、评论 widget、view-in-browser 浮层、隐藏 campaign IDs。
- 第三方退订实现（仅保留**法律/退订占位**文字 + `href="#"`）。
- 原始生成邮件 HTML 整体（ttt2 含 103 处第三方/追踪命中，ttt 含 7 处——**均不入库**）。

## 6. 映射到 Email Assembly / How findings map to assembly

| 参考语法 | 映射到 `build_email_assembly` |
|---|---|
| 600px 容器 | 外层表格 shell `width=600` + `max-width:600px`（table-safe） |
| 顶部横幅 | 既有 Email Banner Module（`workbench.email_banner`，深色 `#1f2329` + logo + 渠道/活动） |
| 红 filet | 横幅下显式红色分隔条 `#E1002A` |
| 标题/引言 | `subject` + `intro`（来自 `product_truth.description`） |
| 选定主体视觉 | 选定候选 `final_poster.url` 图块 |
| CTA | `Nous contacter` 按钮 |
| 联系/页脚 | 渠道·活动联系行 + 法律/退订占位 |
| 社交/联系图标行 | **future**（需在 workbench 建模图标/链接，PR-3R 不做） |

## 7. 现在采用 / Adopted now（最小增量）

`app/services/email/assembly.py` 最小对齐：
1. 容器由 640px → **600px**，并包入**表格安全 shell**（`<table role="presentation" width="600">`）。
2. 横幅下新增**显式红色 filet** `#E1002A`（除既有横幅红色描边外，作可断言的独立分隔条）。
3. 页脚新增**法律/退订占位**行（非功能性 `href="#"`，无第三方退订）。
保留：Email Banner Module、选定主体视觉、intro/CTA、附件就绪；端点 `POST /api/v2/workbench/{key}/email/preview`
不变；`/api/v2/email/send` 未触碰。

## 8. 保留为未来 / Future work

- 联系图标行（telephone/email/catalogue/site）与社交图标行（FB/LinkedIn/Instagram）——需先在 workbench 建模联系/社交
  资产与链接。
- 真正的 body-only 横幅解耦（renderer 合同改造）——见 PR-3 状态文档，明确非当前范围。
- 多产品/多 CTA 版式（参考 ttt2 富版式）——非 v1 商业试用范围。

**STATUS: PR-3R REFERENCE EMAIL HTML EXTRACTION PATCH SUBMITTED FOR OWNER REVIEW**
