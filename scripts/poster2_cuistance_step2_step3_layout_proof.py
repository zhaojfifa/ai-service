#!/usr/bin/env python3
"""REAL (non-stubbed) browser proof for CUISTANCE v1 Step2/Step3 layout + preview consistency fix.

Drives the REAL frontend/cuistance_trial.html against a REAL running backend (app.main) — NO route stubbing.
Verifies: Step 2 balanced dual-mode TAB layout (segmented control; active mode controls + prominent preview);
affiche generates + openable; fiche shown as an official-mode-temporarily-unavailable (not fallback); selection
backend-confirmed; Step 3 owns banner/header + fill format; coherent backend-rendered final preview; honest send.

A backend must already serve page+API at BASE (default http://127.0.0.1:8799).
  PYTHONPATH=. ./.venv/bin/python scripts/poster2_cuistance_step2_step3_layout_proof.py
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/poster2/assets/cuistance_step2_step3_layout_preview_consistency_v1"
OUT.mkdir(parents=True, exist_ok=True)
BASE = os.environ.get("CUIST_BASE", "http://127.0.0.1:8799")
FORBIDDEN_SUCCESS = ["发送成功", "真实发送成功", "已发送"]
FALLBACK_WORDS = ["fallback", "degraded", "备用", "降级", "失败路径"]


def backend_json(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=30) as r:  # noqa: S310 (local trusted)
        return json.loads(r.read().decode("utf-8"))


def main() -> None:
    st: dict = {}
    ev: dict = {"was_stubbed": False, "base_url": BASE}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 1040})
        page.on("response", lambda r: st.__setitem__(
            "preview" if r.url.endswith("/email/preview") else ("send" if r.url.endswith("/email/send") else "_"),
            r.status))

        page.goto(f"{BASE}/cuistance_trial.html")
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT / "01_step1_still_simplified.png"), full_page=True)
        ev["step1_has_banner_format_chooser"] = page.locator("#s1-bannerOptions").count() > 0

        page.click("#btn-sample")
        page.wait_for_timeout(300)
        page.click("#nextBtn")
        page.wait_for_timeout(1500)

        # Step 2 layout: segmented tabs + active controls (left) + preview (right)
        ev["step2_has_mode_tabs"] = page.locator("#modeTabs .mode-tab").count() == 2
        ev["affiche_controls_visible"] = page.eval_on_selector("#card-affiche", "el => getComputedStyle(el).display !== 'none'")
        ev["affiche_preview_visible"] = page.eval_on_selector("#pv-affiche", "el => getComputedStyle(el).display !== 'none'")
        page.screenshot(path=str(OUT / "02_step2_dual_mode_balanced_layout.png"), full_page=True)

        # generate affiche (real chromium ~30s)
        page.click("#btn-gen-affiche")
        page.wait_for_selector("#affiche-real:visible", timeout=180_000)
        page.wait_for_timeout(600)
        ev["affiche_open_action_visible"] = page.eval_on_selector("#affiche-actions", "el => getComputedStyle(el).display !== 'none'")
        ev["affiche_open_href_is_poster"] = (page.get_attribute("#affiche-open", "href") or "").startswith(("data:", "http"))
        page.screenshot(path=str(OUT / "03_step2_affiche_generated_openable.png"), full_page=True)

        # switch to fiche tab + attempt generation (image-gen unavailable -> official-mode amber, NOT fallback)
        page.click('#modeTabs .mode-tab[data-mode="fiche"]')
        page.wait_for_timeout(300)
        page.click("#btn-gen-fiche")
        page.wait_for_timeout(3000)
        ev["fiche_unavailable_shown"] = page.eval_on_selector("#fiche-unavailable", "el => getComputedStyle(el).display !== 'none'")
        ev["fiche_unavailable_text"] = page.inner_text("#fiche-unavailable-text")
        fiche_card_text = page.inner_text("#card-fiche")
        ev["fiche_official_mode_present"] = ("简单产品页模式" in fiche_card_text and "正式模式" in fiche_card_text)
        ev["fiche_not_labeled_fallback"] = not any(w in fiche_card_text for w in FALLBACK_WORDS)
        page.screenshot(path=str(OUT / "04_step2_fiche_mode_status.png"), full_page=True)

        diag = json.loads(page.inner_text("#diagdump"))
        wb_key = diag.get("workbench_key")
        wb = backend_json(f"/api/v2/workbench/{wb_key}")
        pc = wb.get("poster_candidates") or {}
        aff, fic = pc.get("affiche") or {}, pc.get("fiche") or {}
        aff_pk = aff.get("poster_key")
        aff_rec = backend_json(f"/api/v2/posters/{aff_pk}") if aff_pk else {}
        aff_url = (aff_rec.get("final_poster") or {}).get("url") or ""

        # select affiche (switch back to its tab), confirm from backend GET
        page.click('#modeTabs .mode-tab[data-mode="affiche"]')
        page.wait_for_timeout(200)
        page.click("#btn-select-affiche")
        page.wait_for_timeout(1500)
        ev["selected_email_body_visual"] = backend_json(f"/api/v2/workbench/{wb_key}").get("selected_email_body_visual")
        ev["continue_btn_label"] = page.inner_text("#nextBtn")
        page.screenshot(path=str(OUT / "05_step2_selected_body_visual.png"), full_page=True)

        # Step 3: banner controls + fill format
        page.click("#nextBtn")
        page.wait_for_timeout(700)
        ev["step3_banner_controls_present"] = page.locator("#bannerOptions .banner-opt").count() >= 1
        ev["step3_fill_format_present"] = page.locator("#fillFormatOptions .banner-opt").count() == 2
        diag2 = json.loads(page.inner_text("#diagdump"))
        ev["selected_or_inferred_email_fill_format"] = (diag2.get("fill_format_diag") or {}).get("selected_email_fill_format")
        page.screenshot(path=str(OUT / "06_step3_email_format_and_banner_controls.png"), full_page=True)

        # preview (backend-rendered)
        page.click("#btn-preview")
        page.wait_for_timeout(2500)
        ev["preview_status"] = st.get("preview")
        diag3 = json.loads(page.inner_text("#diagdump"))
        pv = diag3.get("preview_diag") or {}
        ev["preview_uses_body_visual_poster_key"] = bool(pv.get("body_visual_poster_key") and pv.get("body_visual_poster_key") == aff_pk)
        ev["final_preview_rendered"] = page.eval_on_selector(
            "#mailFrame", "el => el && getComputedStyle(el).display !== 'none' && (el.contentWindow.document.body ? el.contentWindow.document.body.innerText.length : 0) > 20")
        ev["preview_badge"] = page.inner_text("#email-preview-badge")
        page.screenshot(path=str(OUT / "07_step3_final_email_preview_coherent.png"), full_page=True)

        # send: mode=real but inline_only -> must NOT read as real sent
        page.check('input[name="mode"][value="real"]')
        page.check("#f-confirm")
        page.click("#btn-send")
        page.wait_for_timeout(400)
        page.click("#modalConfirm")
        page.wait_for_timeout(1500)
        last = (backend_json(f"/api/v2/workbench/{wb_key}").get("send_attempts") or [{}])[-1]
        summary = page.inner_text("#send-summary")
        page.screenshot(path=str(OUT / "08_send_preview_only_label.png"), full_page=True)

        page.click("#diagBtn")
        page.wait_for_timeout(400)
        ev["diag_excerpt"] = page.inner_text("#diagdump")[:1400]
        page.screenshot(path=str(OUT / "09_diagnostics_layout_preview_evidence.png"), full_page=True)
        browser.close()

    ev.update({
        "workbench_key": wb_key,
        "affiche_status": aff.get("status"),
        "affiche_poster_key": aff_pk,
        "affiche_final_poster_url_present": bool(aff_url),
        "fiche_status": fic.get("status"),
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
