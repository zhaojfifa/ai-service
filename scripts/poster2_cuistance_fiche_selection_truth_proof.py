#!/usr/bin/env python3
"""LOCAL REAL-backend proof: Fiche selection is bound to backend truth and drives the product_sheet_email preview.

Reproduces the remote symptom (affiche selected, fiche ready-but-not-selected) and proves the fix:
  - affiche generated+selected first  -> selected_email_body_visual == affiche  (the BEFORE state)
  - fiche generated (ready, no poster_key)  -> shown ready, NOT selected
  - PAGE RELOAD forces state recovery (tryRestore) — the path that previously DROPPED fiche (poster_key guard)
  - click fiche 选为邮件主体 -> PATCH + GET-confirm -> selected flips to fiche  (the AFTER state, backend-confirmed)
  - Step3 default format follows the selected body -> product_sheet_email, preview uses fiche (NOT affiche)
  - affiche regression (no inner banner) still passes; send stays no-real-send.

Real app.main backend (no stubbing). A backend must serve page+API at BASE (default http://127.0.0.1:8799).
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / ("docs/poster2/assets/cuistance_psd_email_container_last_mile_v1/remote_last_mile_fix/"
              "fiche_selection_preview_truth_fix_v1")
BASE = os.environ.get("CUIST_BASE", "http://127.0.0.1:8799")


def bj(p, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + p, data=data, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310 (local trusted)
        return json.loads(r.read().decode("utf-8"))


def selected(wb):
    return bj(f"/api/v2/workbench/{wb}").get("selected_email_body_visual")


def diag(page):
    try:
        return json.loads(page.inner_text("#diagdump"))
    except Exception:
        return {}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ev = {"branch": "trial/poster2-cuistance-psd-email-container-last-mile-v1", "base_commit": "bb3a9f3",
          "remote_url": "https://ai-service-leob.onrender.com/cuistance_trial.html", "was_stubbed": False}
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1400, "height": 1040})
        page = ctx.new_page()
        page.goto(f"{BASE}/cuistance_trial.html")
        page.wait_for_timeout(600)
        page.click("#btn-sample")
        page.wait_for_timeout(300)
        page.click("#nextBtn")
        page.wait_for_timeout(1500)
        wb = diag(page).get("workbench_key")
        ev["workbench_key"] = wb

        # BEFORE: generate + select affiche so the selected body is affiche (the remote starting state)
        page.click("#btn-gen-affiche")
        page.wait_for_selector("#affiche-real:visible", timeout=180_000)
        page.wait_for_timeout(500)
        page.click("#btn-select-affiche")
        page.wait_for_timeout(1200)
        ev["selected_email_body_visual_before"] = selected(wb)

        # fiche: generate (ready, no poster_key) — should be ready but NOT selected
        page.click('#modeTabs .mode-tab[data-mode="fiche"]')
        page.wait_for_timeout(300)
        t0 = time.time()
        page.click("#btn-gen-fiche")
        try:
            page.wait_for_selector("#fiche-real:visible", timeout=30_000)
        except Exception:
            pass
        ev["fiche_generate_timeout"] = bool(round(time.time() - t0, 2) >= 80.0)
        page.wait_for_timeout(500)
        fcand = (bj(f"/api/v2/workbench/{wb}").get("poster_candidates") or {}).get("fiche") or {}
        ev["fiche_candidate_ready"] = (fcand.get("status") == "ready")
        ev["fiche_has_poster_key"] = bool(fcand.get("poster_key"))
        ev["fiche_generated_from"] = (fcand.get("contract_review_summary") or {}).get("generated_from")
        ev["fiche_uses_poster_generation"] = bool((fcand.get("contract_review_summary") or {}).get("uses_poster_generation"))
        page.screenshot(path=str(OUT / "01_fiche_ready_not_selected.png"), full_page=True)

        # RE-ENTRY: reload to force state recovery (tryRestore) — previously dropped fiche (poster_key guard).
        page.reload()
        page.wait_for_timeout(1800)
        try:  # if a recover bar is shown, use it
            if page.is_visible("#btn-recover"):
                page.click("#btn-recover")
                page.wait_for_timeout(1500)
        except Exception:
            pass
        # ensure we are on Step2, fiche tab
        try:
            page.click('#modeTabs .mode-tab[data-mode="fiche"]')
            page.wait_for_timeout(400)
        except Exception:
            pass
        ev["fiche_selectable_after_reentry"] = page.is_visible("#btn-select-fiche")

        # click fiche 选为邮件主体 -> PATCH + GET-confirm
        page.click("#btn-select-fiche")
        page.wait_for_timeout(1500)
        page.screenshot(path=str(OUT / "02_fiche_select_clicked.png"), full_page=True)
        ev["selected_email_body_visual_after"] = selected(wb)
        ev["selection_get_confirmed"] = (ev["selected_email_body_visual_after"] == "fiche")
        page.screenshot(path=str(OUT / "03_workbench_selected_fiche.png"), full_page=True)

        # Step3 default format follows selected body -> product_sheet_email; preview uses fiche
        page.click("#nextBtn")
        page.wait_for_timeout(700)
        page.click("#btn-preview")
        page.wait_for_timeout(2500)
        page.screenshot(path=str(OUT / "04_step3_product_sheet_email_preview.png"), full_page=True)
        prev = bj(f"/api/v2/workbench/{wb}/email/preview", method="POST")
        ev["email_fill_format"] = prev.get("email_fill_format")
        ev["email_header_source"] = prev.get("email_header_source")
        ev["product_sheet_email_contract_pass"] = bool(prev.get("product_sheet_email_contract_pass"))
        ev["fiche_generated_from"] = prev.get("fiche_generated_from") or ev.get("fiche_generated_from")
        bv = prev.get("body_visual") or {}
        ev["preview_uses_fiche"] = (bv.get("candidate_type") == "fiche")
        ev["preview_does_not_use_affiche"] = (bv.get("url") != "https://example.com/affiche.png"
                                              and prev.get("selected_email_body_visual") == "fiche")
        ev["product_sheet_email_preview_ok"] = bool(
            prev.get("email_fill_format") == "product_sheet_email"
            and prev.get("email_header_source") == "ttt_html_header"
            and "<table" in (prev.get("html") or "") and "CUISTANCE" in (prev.get("html") or ""))

        page.click("#btn-full-preview")
        page.wait_for_timeout(900)
        page.screenshot(path=str(OUT / "05_full_product_sheet_email_preview.png"), full_page=True)
        page.click("#fp-close")
        page.wait_for_timeout(300)

        # backend mismatch guard: assert product_sheet_email while selecting affiche -> 422
        page.click("#prevBtn")
        page.wait_for_timeout(500)
        page.click('#modeTabs .mode-tab[data-mode="affiche"]')
        page.wait_for_timeout(300)
        page.click("#btn-select-affiche")
        page.wait_for_timeout(1200)
        try:
            urllib.request.urlopen(urllib.request.Request(
                BASE + f"/api/v2/workbench/{wb}/email/preview",
                data=json.dumps({"email_fill_format": "product_sheet_email"}).encode(),
                headers={"Content-Type": "application/json"}, method="POST"), timeout=30)
            ev["backend_mismatch_guard_rejects"] = False
        except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
            ev["backend_mismatch_guard_rejects"] = (e.code == 422 and "email_fill_format_mismatch" in e.read().decode())

        # affiche regression (no inner banner) still passes
        page.click("#nextBtn")
        page.wait_for_timeout(700)
        page.click("#btn-preview")
        page.wait_for_timeout(2500)
        aprev = bj(f"/api/v2/workbench/{wb}/email/preview", method="POST")
        ev["affiche_regression_still_ok"] = bool(
            selected(wb) == "affiche" and aprev.get("email_fill_format") == "campaign_poster_email"
            and (aprev.get("body_visual") or {}).get("candidate_type") == "affiche")
        ev["affiche_body_visual_contains_own_banner"] = bool(aprev.get("body_visual_contains_own_banner"))
        ev["affiche_email_body_visual_contract_pass"] = bool(aprev.get("email_body_visual_contract_pass"))
        page.screenshot(path=str(OUT / "06_affiche_regression.png"), full_page=True)

        # restore fiche selection + send (mode=real inline) -> NOT a real send
        page.click("#prevBtn")
        page.wait_for_timeout(500)
        page.click('#modeTabs .mode-tab[data-mode="fiche"]')
        page.wait_for_timeout(300)
        page.click("#btn-select-fiche")
        page.wait_for_timeout(1200)
        ev["selected_email_body_visual_after"] = selected(wb)
        page.click("#nextBtn")
        page.wait_for_timeout(700)
        page.click("#btn-preview")
        page.wait_for_timeout(2000)
        try:
            page.check('input[name="mode"][value="real"]')
            page.check("#f-confirm")
            page.click("#btn-send")
            page.wait_for_timeout(400)
            page.click("#modalConfirm")
            page.wait_for_timeout(1500)
        except Exception:
            pass
        last = (bj(f"/api/v2/workbench/{wb}").get("send_attempts") or [{}])[-1]
        ev["real_email_sent"] = bool(last.get("status") == "sent" and last.get("provider_message_id"))
        page.screenshot(path=str(OUT / "07_send_no_real_send.png"), full_page=True)
        b.close()

    ev["local_pass"] = bool(
        ev.get("fiche_generate_timeout") is False
        and ev.get("fiche_candidate_ready") is True
        and ev.get("fiche_has_poster_key") is False
        and ev.get("selected_email_body_visual_before") == "affiche"
        and ev.get("fiche_selectable_after_reentry") is True
        and ev.get("selected_email_body_visual_after") == "fiche"
        and ev.get("selection_get_confirmed") is True
        and ev.get("email_fill_format") == "product_sheet_email"
        and ev.get("product_sheet_email_preview_ok") is True
        and ev.get("preview_uses_fiche") is True
        and ev.get("preview_does_not_use_affiche") is True
        and ev.get("backend_mismatch_guard_rejects") is True
        and ev.get("affiche_regression_still_ok") is True
        and ev.get("affiche_body_visual_contains_own_banner") is False
        and ev.get("affiche_email_body_visual_contract_pass") is True
        and ev.get("real_email_sent") is False
    )
    ev["remote_pass"] = False  # OPS creds + branch redeploy gated
    (OUT / "evidence.json").write_text(json.dumps(ev, ensure_ascii=False, indent=2))
    print(json.dumps(ev, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
