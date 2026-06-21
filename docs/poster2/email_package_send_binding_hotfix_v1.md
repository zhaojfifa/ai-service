# Email Package Send-Binding Hotfix v1 (P0)

Task: **POSTER2-EMAIL-PACKAGE-SEND-BINDING-HOTFIX-V1**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.

P0 fix: the operator selected/previewed **Affiche** but the send delivered **Fiche**. Now the send binds
authoritatively to the explicitly-selected package, and the UI proves which package was sent. No new features, no
banner polish, no body redesign, no send-provider rebuild, P2A demo untouched.

---

## 1. Root cause

Two compounding bugs:

```
BACKEND: the send endpoint called _resolve_workbench_email_package(workbench_key) with NO route -> it resolved the
         PERSISTED selected_email_body_visual and ignored payload.selected_email_package (used only as a guard).

FRONTEND: the send payload used the JS global `selectedVisual`; and viewing the Affiche PACKAGE CARD (rendered via
          /email/packages, independent of the persisted selection) NEVER changed the persisted selection. So the
          bottom send could send the stale persisted route (Fiche) while the operator was looking at Affiche, with
          no mismatch (selectedVisual == persisted == fiche).
```

## 2. Files changed

```
app/main.py                   : send resolves from payload.selected_email_package (route=...) -> AUTHORITATIVE;
                                keeps the 422 mismatch guard vs the persisted selection; response +email_fill_format.
app/schemas/poster2.py        : WorkbenchEmailSendResponse.email_fill_format (additive).
frontend/cuistance_trial.html : "发送这个版本" is now a COMPLETE explicit send of THAT route (select -> preview ->
                                bind -> modal); send re-confirms the persisted selection, sends selected_email_package
                                = that route, and VERIFIES sent_package_type matches (else error, not success);
                                staleness warning; "已发送版本" shows the sent package + container + provider_message_id.
                                (+ docs mirror)
tests/poster2/test_workbench_email_packages.py : +4 binding tests.
```

## 3. Send payload before / after

```
BEFORE: { recipients:[r], mode, confirm_send:true, delivery_mode, selected_email_package: selectedVisual /*stale JS*/ }
AFTER : "发送这个版本"(route) -> PATCH selected-visual=route -> GET-confirm -> preview(route) -> open modal ->
        modalConfirm re-GETs the persisted selection, requires it == route, then sends
        { ..., selected_email_package: route } and verifies response.sent_package_type == route.
```

## 4. Backend package resolver behavior

```
pkg = _resolve_workbench_email_package(workbench_key, route=payload.selected_email_package)   # EXPLICIT wins
sent_package_type = pkg.selected   # = the requested route (fiche|affiche)
guard: if selected_email_package and persisted_selected and they differ -> 422 selected_package_mismatch
response: sent_package_type, selected_email_body_visual, email_fill_format, body_visual_poster_key,
          container_visual_variant, real_email_sent
```

Affiche → `email_fill_format=campaign_poster_email`, `container_visual_variant=ttt2_campaign_container`,
`body_visual_poster_key` present. Fiche → `product_sheet_email`, `ttt_product_sheet_container`, `poster_key=null`.

## 5. UI package send behavior

```
"发送这个版本"(card) : selects + previews THAT route, binds the send to it, warns if maybe_stale.
bottom "发送测试邮件" : binds to the currently selected package; modalConfirm re-confirms the backend persisted
                       selection == the bound package (else blocks with "用版本卡片的发送这个版本"); no hidden Fiche default.
after send           : if response.sent_package_type != requested -> ERROR, NOT marked success.
                       else "已发送版本：<目标海报邮件|简单产品页邮件> · 容器 · 海报Key · provider_message_id".
stale                : maybe_stale -> confirm dialog before sending; never silently sends stale.
```

## 6. Affiche / Fiche send binding result

```
test_send_affiche_binds_to_affiche : sent_package_type=affiche, email_fill_format=campaign_poster_email,
                                     container_visual_variant=ttt2_campaign_container, body_visual_poster_key present, real_email_sent=true
test_send_fiche_binds_to_fiche     : sent_package_type=fiche, email_fill_format=product_sheet_email,
                                     container_visual_variant=ttt_product_sheet_container, body_visual_poster_key=null
test_explicit_package_is_authoritative_over_legacy : affiche->ttt2 (poster_key), fiche->ttt (no poster_key)
```

## 7. Mismatch guard

`selected_email_package` ≠ persisted `selected_email_body_visual` → `422 selected_package_mismatch`
(`test_send_rejects_package_mismatch`).

## 8. Tests

```
+4 binding tests (affiche binds / fiche binds / explicit authoritative / response container_visual_variant).
Focused suites = 96 passed ; test_api -k email/workbench/selected/fiche/preview/send/package = 11 passed ;
node --check cuistance_trial.html = TRIAL_JS_OK ; check_docs_router --all = PASS.
```

## 9. Remote verification

See the evidence JSON / log entry. Performed after Render deploys this commit (authenticated API mirrors the UI
calls; one Affiche send to the internal authorized recipient only). If not yet deployed at verify time: PENDING_REDEPLOY.

## 10. Remaining HOLD

```
customer send / batch send   HOLD
products[] / multi-product   HOLD
final designer banner assets HOLD
P2A demo backend mapping     HOLD
```
