#!/usr/bin/env python3
"""REAL (non-stubbed) browser proof for CUISTANCE v1 state recovery + Step2/Step3 consistency.

Drives the REAL frontend/cuistance_trial.html against a REAL running backend (app.main) — NO route stubbing.
Verifies P0 hard-refresh recovery (localStorage workbench key + backend GET restore), Step 2 product summary,
backend-driven preview state, backend-confirmed selection, Step 3 email assembly stage, coherent preview, and
honest send. Screenshots + evidence.json (was_stubbed=false).

A backend must already serve page+API at BASE (default http://127.0.0.1:8799).
  PYTHONPATH=. ./.venv/bin/python scripts/poster2_cuistance_state_recovery_proof.py
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/poster2/assets/cuistance_state_recovery_step2_step3_consistency_v1"
OUT.mkdir(parents=True, exist_ok=True)
BASE = os.environ.get("CUIST_BASE", "http://127.0.0.1:8799")
FORBIDDEN_SUCCESS = ["发送成功", "真实发送成功", "已发送"]


def backend_json(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=30) as r:  # noqa: S310 (local trusted)
        return json.loads(r.read().decode("utf-8"))


def diagdump(page) -> dict:
    try:
        return json.loads(page.inner_text("#diagdump"))
    except Exception:
        return {}


def main() -> None:
    st: dict = {}
    ev: dict = {"was_stubbed": False, "base_url": BASE}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1400, "height": 1040})
        page = ctx.new_page()
        page.on("response", lambda r: st.__setitem__(
            "preview" if r.url.endswith("/email/preview") else ("send" if r.url.endswith("/email/send") else "_"),
            r.status))

        page.goto(f"{BASE}/cuistance_trial.html")
        page.wait_for_timeout(600)
        page.click("#btn-sample")
        page.wait_for_timeout(300)
        page.click("#nextBtn")
        page.wait_for_timeout(1500)
        page.screenshot(path=str(OUT / "01_step2_product_summary.png"), full_page=True)
        ev["s2_summary_text"] = page.inner_text("#sum-product") + " | " + page.inner_text("#sum-assets")

        # generate affiche (real chromium ~30s)
        page.click("#btn-gen-affiche")
        page.wait_for_selector("#affiche-real:visible", timeout=180_000)
        page.wait_for_timeout(600)
        d = diagdump(page)
        init_wb = d.get("workbench_key")
        ev["initial_workbench_key"] = init_wb
        ev["localStorage_key_present"] = bool(page.evaluate("() => localStorage.getItem('cuistance_trial_last_workbench_key')"))
        wb = backend_json(f"/api/v2/workbench/{init_wb}")
        aff = (wb.get("poster_candidates") or {}).get("affiche") or {}
        aff_pk = aff.get("poster_key")
        ev["affiche_status"] = aff.get("status")
        ev["affiche_poster_key"] = aff_pk
        ev["affiche_final_poster_url_present_before_refresh"] = page.eval_on_selector(
            "#affiche-real", "el => (el.getAttribute('src')||'').startsWith('data:') || (el.getAttribute('src')||'').startsWith('http')")
        page.screenshot(path=str(OUT / "02_step2_generated_poster_before_refresh.png"), full_page=True)

        # ---- P0: HARD REFRESH ----
        page.reload()
        page.wait_for_timeout(800)
        # auto-restore fires (auth open locally -> connected -> maybeRestore). Wait for the recovered poster.
        page.wait_for_selector("#affiche-real:visible", timeout=60_000)
        page.wait_for_timeout(500)
        d2 = diagdump(page)
        ev["recovered_workbench_key"] = d2.get("workbench_key")
        ev["recovered_after_refresh"] = (d2.get("workbench_key") == init_wb)
        ev["product_truth_restored"] = bool(page.eval_on_selector("#f-pname", "el => (el.value||'').length > 0"))
        ev["assets_restored"] = page.eval_on_selector("#thumb-prod1", "el => el && getComputedStyle(el).display !== 'none'")
        ev["affiche_final_poster_url_present_after_refresh"] = page.eval_on_selector(
            "#affiche-real", "el => (el.getAttribute('src')||'').startsWith('data:') || (el.getAttribute('src')||'').startsWith('http')")
        ev["on_step2_after_refresh"] = page.eval_on_selector("#screen-2", "el => el.classList.contains('active')")
        page.screenshot(path=str(OUT / "03_after_refresh_recovered_workbench.png"), full_page=True)
        page.screenshot(path=str(OUT / "04_step2_generated_poster_after_refresh.png"), full_page=True)

        # ---- select affiche (backend-confirmed) ----
        page.click("#btn-select-affiche")
        page.wait_for_timeout(1500)
        ev["selected_email_body_visual"] = backend_json(f"/api/v2/workbench/{init_wb}").get("selected_email_body_visual")
        page.screenshot(path=str(OUT / "05_step2_selected_body_visual.png"), full_page=True)

        # ---- Step 3 ----
        page.click("#nextBtn")
        page.wait_for_timeout(700)
        ev["step3_unlocked"] = page.eval_on_selector("#screen-3", "el => el.classList.contains('active')")
        ev["step3_has_fill_format"] = page.locator("#fillFormatOptions .banner-opt").count() == 2
        ev["step3_has_banner"] = page.locator("#bannerOptions .banner-opt").count() >= 1
        page.screenshot(path=str(OUT / "06_step3_email_assembly_stage.png"), full_page=True)

        page.click("#btn-preview")
        page.wait_for_timeout(2500)
        ev["preview_status"] = st.get("preview")
        pv = (diagdump(page).get("preview_diag") or {})
        ev["preview_uses_body_visual_poster_key"] = bool(pv.get("body_visual_poster_key") and pv.get("body_visual_poster_key") == aff_pk)
        ev["final_preview_rendered"] = page.eval_on_selector(
            "#mailFrame", "el => el && getComputedStyle(el).display !== 'none' && (el.contentWindow.document.body ? el.contentWindow.document.body.innerText.length : 0) > 20")
        page.screenshot(path=str(OUT / "07_step3_final_email_preview.png"), full_page=True)

        # ---- P0 second refresh: selection + Step 3 restored (lands on step 3, not step 2) ----
        page.reload()
        page.wait_for_timeout(800)
        # restore is async; wait until the workbench has been restored into diagnostics
        page.wait_for_function(
            "() => { try { return !!JSON.parse(document.getElementById('diagdump').textContent).workbench_key } catch(e){ return false } }",
            timeout=60_000)
        page.wait_for_timeout(900)
        ev["selected_state_restored_after_refresh"] = backend_json(f"/api/v2/workbench/{init_wb}").get("selected_email_body_visual") == "affiche"
        ev["step3_active_after_2nd_refresh"] = page.eval_on_selector("#screen-3", "el => el.classList.contains('active')")

        # ---- send (mode=real, inline_only) ----
        if not ev["step3_active_after_2nd_refresh"]:
            # navigate to step3 if restore landed on step2
            try:
                page.click('#stepper .step[data-step="3"]'); page.wait_for_timeout(500)
            except Exception:
                pass
        page.check('input[name="mode"][value="real"]')
        page.check("#f-confirm")
        page.click("#btn-send")
        page.wait_for_timeout(400)
        page.click("#modalConfirm")
        page.wait_for_timeout(1500)
        last = (backend_json(f"/api/v2/workbench/{init_wb}").get("send_attempts") or [{}])[-1]
        summary = page.inner_text("#send-summary")
        page.screenshot(path=str(OUT / "08_send_preview_only_semantics_if_run.png"), full_page=True)
        page.click("#diagBtn")
        page.wait_for_timeout(400)
        ev["diag_excerpt"] = page.inner_text("#diagdump")[:1400]
        page.screenshot(path=str(OUT / "09_diagnostics_recovery_evidence.png"), full_page=True)
        browser.close()

    ev.update({
        "send_mode": last.get("mode"),
        "send_provider": last.get("provider"),
        "send_status": last.get("status"),
        "send_error_code": last.get("error_code"),
        "provider_message_id_present": bool(last.get("provider_message_id")),
        "real_email_sent": bool(last.get("status") == "sent" and last.get("provider_message_id")),
        "send_summary_text": summary,
        "ui_send_label_correct": (not any(s in summary for s in FORBIDDEN_SUCCESS)) and ("未真实投递" in summary),
    })
    (OUT / "evidence.json").write_text(json.dumps(ev, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in ev.items() if k != "diag_excerpt"}, ensure_ascii=False, indent=2))
    print("\nScreenshots ->", OUT)


if __name__ == "__main__":
    main()
