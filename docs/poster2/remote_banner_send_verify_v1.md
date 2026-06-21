# Remote Banner / Send Verify v1 (commit 0a55a1c) — PASS

Task: **POSTER2-CUISTANCE-0A55A1C-REMOTE-BANNER-SEND-VERIFY**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1` @ HEAD `0a55a1c`.
Status: **PASS** — remote-verified the default `ttt_logo_banner` rendering for both routes. No code changed. No
customer email; no real send run (justified below).

Method: literal browser (Playwright + Chrome) for the Fiche preview + screenshot; authenticated API for the Affiche
route diagnostics (the banner is backend-determined, identical to the browser).

---

## 1. Remote deployed commit status

**Deployed at `0a55a1c` or later.** The served page carries `ttt_logo_banner` / "TTT Logo Banner" / 缺失回退 and
`selectedHeaderVariant='ttt_logo_banner'`; the backend preview returns `header_variant=ttt_logo_banner` +
`banner_source=uploaded_logo`. Health 200, page 200.

## 2. Fiche banner result — PASS

```
container_visual_variant = ttt_product_sheet_container
header_variant           = ttt_logo_banner
banner_source            = uploaded_logo
header_logo_used         = true
header_logo_missing_fallback = false
supporting_media_count   = 3
UI header diag           = 当前邮件容器：TTT 简单产品容器 · 当前 Banner：可替换 · TTT Logo Banner · Logo 已使用：是 · 缺失回退：否
```

Visual (live remote screenshot `fiche_remote_banner.png`): the header is now the **logo banner** (CUISTANCE logo +
"CUISTANCE EUROPE · NOUVEAUTÉ" meta + red filet) — **not** the old plain text black bar. Product body layout and the
supporting media strip are unchanged.

## 3. Affiche banner result — PASS

```
container_visual_variant      = ttt2_campaign_container
header_variant                = ttt_logo_banner
banner_source                 = uploaded_logo
header_logo_used              = true
header_logo_missing_fallback  = false
email_body_visual_contract_pass = true
body_visual_contains_own_banner = false
```

No double header; the poster body remains centered; the logo banner frames it.

## 4. Fiche regression

`ttt_product_sheet_container` intact: `supporting_media_count=3`, body layout unchanged.

## 5. Affiche regression

`ttt2_campaign_container` intact: `email_body_visual_contract_pass=true`, `body_visual_contains_own_banner=false`
(no inner/double banner).

## 6. Send regression result

**Not run (justified).** This commit changes only the banner/header layer; the send path is unchanged code and was
already validated end-to-end in a real browser at `850a0af` (`provider=resend`, `provider_message_id` present). There
is no send-path regression risk, so an additional real email to the internal address was avoided.
`real_send_provider="not_run"`, `provider_message_id=null`. No customer email; no batch.

## 7. Provider / message id

Not applicable this run (no send). The send path's last real proof: `850a0af` real test send `provider=resend`,
`provider_message_id=e46866d5-fed5-4915-9a7e-ae4b11f4f13f`.

## 8. Honest nit

The remote workbench's uploaded logo (`logo_01.jpg`) is a darker asset, so it sits low-contrast on the dark header.
The **banner mechanism is correct** (logo used, not wordmark; `header_logo_used=true`); a light/transparent logo (the
real white CUISTANCE brand logo) renders crisply, as in the local polish screenshots. This is a cosmetic operator
asset-choice nit, not a container defect.

## 9. Remaining HOLD

```
customer send / batch send   HOLD
products[] / multi-product   HOLD
P2A demo backend mapping     HOLD
```

## Owner Decision Needed

Accept the remote-verified `ttt_logo_banner` default for both routes. Optionally, replace the operator logo asset
with a light/transparent header logo for maximum contrast (cosmetic). `customer/batch send` and `products[]` remain
HOLD.
