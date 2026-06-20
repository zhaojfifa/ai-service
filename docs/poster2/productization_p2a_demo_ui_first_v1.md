# Productization P2A — Demo UI First v1

Status: **DEMO UI ONLY. No backend alignment. No baseline mutation. No real send.**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.

Owner-approved direction for this slice:

```
Demo UI first
No backend alignment yet
No existing baseline mutation
User/operator-facing workflow first
```

The prior engineering-diagnostics pass (truth/visual labels in Step-1 + §6 contract panel in the internal
drawer of `cuistance_trial.html`) was **stashed, not committed** — useful later for diagnostics, but not the
requested P2A demo.

Artifacts (the ONLY files this slice creates/changes):

```
frontend/cuistance_productization_demo.html          (new, standalone)
docs/cuistance_productization_demo.html              (byte-identical mirror)
docs/poster2/productization_p2a_demo_ui_first_v1.md  (this doc)
docs/poster2/assets/productization_p2a_demo_ui_first_v1/evidence.json
docs/poster2/current_branch_execution_log_v1.md      (append-only log entry)
```

Untouched (hard boundary): `frontend/cuistance_trial.html`, `docs/cuistance_trial.html`, `app/`, `schemas/`,
email assembly, poster generation, `tests/`.

---

## 1. Why UI demo comes before backend alignment

The operator workflow (what content goes into which email container, what is editable vs locked, where real
send is held) must be validated visually with real operators *before* committing backend shape — especially
`products[]` (multi-product), which does not exist in the runtime today. A static, data-driven demo lets the
Owner approve the operator perspective with zero risk to the live baseline, no schema churn, and no API calls.
Backend alignment (P2B+) only starts after this UI is approved.

## 2. Supported demo workflow

```
准备内容 (prepare content)
→ 选择邮件容器 (choose email container)
→ 装配预览 (compose preview: insert product/material/text into the 600px container)
→ 检查结果 (readiness & contract check)
```

All four sections render on one page; all interaction is local-only (no network).

## 3. Product limit: max 2 products

```
max products = 2
Product A / Product B = DISTINCT products
```

Product A is the confirmed truth product (CUISTANCE Friteuse électrique double EF132V). Product B is an
explicitly-marked **占位 · 待确认** placeholder (Friteuse électrique simple EF112V) and is visibly flagged
unconfirmed everywhere it appears.

## 4. Product image limit: max 3 views per product

```
max product views per product = 3
View 1 / View 2 / View 3 = images of ONE product
```

The demo clarifies in the UI that views are images of a single product (not different products). The primary
view is operator-selectable for single-product containers.

## 5. Container options

```
目标海报邮件   Target Poster Email          route: affiche   (supported route, demo render)
简单产品页邮件 Simple Product Sheet Email    route: fiche     (supported route, demo render)
双产品对比邮件 Dual Product Comparison Email route: demo      (DEMO ONLY — products[] backend not implemented)
```

The dual-product container is rendered for UX evaluation only and is marked **Demo only**; it cannot be
generated or sent (no backend `products[]`).

## 6. Editable vs locked fields

Editable (presentation / demo-local):

```
邮件容器 (container)
展示产品 (Product A / B)
主图 (primary image / View 1·2·3)
标题 (title)
引言 (intro)
CTA 文案 (CTA label)
```

Locked (事实 / truth, never edited in the demo):

```
产品名称 (product name)
型号 (reference)
技术参数 (capacity / power / thermostat ...)
联系方式 (contact email / phone)
```

## 7. Demo-only boundaries

Surfaced in the UI as business-readable engineering status:

```
仅演示，未接后台
不写入 Workbench
不调用生成 API
不实现 products[] 后台
不真实发送（真实发送仍 HOLD）
```

Verified: the page contains 0 `fetch(`, 0 `/api/` references, 0 `localStorage` / `sessionStorage` usage.

## 8. What Owner must confirm before backend work

```
1. The four-section operator workflow is the right shape.
2. The 2-product / 3-view limits match the commercial intent.
3. Editable-vs-locked split is correct (truth stays locked).
4. Whether the dual-product comparison email is in-scope to productize at all
   (it requires a real products[] backend; currently DEMO ONLY).
5. Container module order / fields for affiche and fiche match the P1 container contract.
```

## 9. Next recommended step after UI approval

```
POSTER2-PRODUCTIZATION-P2B-DEMO-TO-CONTRACT-MAPPING
  — map each approved demo control to the existing single-product contract fields
    (no products[] yet), keeping multi-product and real send on HOLD.
```

Only after that mapping is approved should any backend / schema work begin.
