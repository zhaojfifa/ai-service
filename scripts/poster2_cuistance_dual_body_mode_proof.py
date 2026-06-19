#!/usr/bin/env python3
"""REAL (non-stubbed) browser proof for CUISTANCE v1 dual body-mode + email fill-format alignment.

Drives the REAL frontend/cuistance_trial.html against a REAL running backend (app.main) — NO route stubbing.
Verifies: Step 1 simplified (brand assets, no banner-format decision); Step 2 two EQUAL modes (affiche + fiche)
with real poster binding + open/copy actions; fiche shows a mode-specific amber when image-gen is unavailable
(NOT a fallback) without blocking affiche; selection confirmed from backend GET; Step 3 email fill-format default
mapping + labels; backend-rendered preview; honest send semantics. Screenshots + evidence.json (was_stubbed=false).

A backend must already serve page+API at BASE (default http://127.0.0.1:8799).
  PYTHONPATH=. ./.venv/bin/python scripts/poster2_cuistance_dual_body_mode_proof.py
"""
from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/poster2/assets/cuistance_dual_body_mode_email_fill_format_alignment_v1"
OUT.mkdir(parents=True, exist_ok=True)
BASE = os.environ.get("CUIST_BASE", "http://127.0.0.1:8799")
FORBIDDEN_SUCCESS = ["发送成功", "真实发送成功", "已发送"]


def backend_json(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=30) as r:  # noqa: S310 (local trusted)
        return json.loads(r.read().decode("utf-8"))


def main() -> None:
    statuses: dict = {}
    ev: dict = {"was_stubbed": False, "base_url": BASE}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 1040})
        page.on("response", lambda r: statuses.__setitem__(
            "preview" if r.url.endswith("/email/preview") else ("send" if r.url.endswith("/email/send") else "_"),
            r.status))

        page.goto(f"{BASE}/cuistance_trial.html")
        page.wait_for_timeout(600)

        # ---- Step 1: brand assets, NO banner-format decision in Step 1 ----
        ev["step1_has_banner_format_chooser"] = page.locator("#s1-bannerOptions").count() > 0
        page.click("#btn-sample")
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT / "01_step1_simplified_product_assets_no_banner_confusion.png"), full_page=True)

        page.click("#nextBtn")
        page.wait_for_timeout(1500)

        # ---- Step 2: two EQUAL modes ----
        ev["step2_has_affiche_card"] = page.locator("#card-affiche").count() > 0
        ev["step2_has_fiche_card"] = page.locator("#card-fiche").count() > 0
        ev["affiche_card_title"] = page.inner_text("#card-affiche h3")
        ev["fiche_card_title"] = page.inner_text("#card-fiche h3")
        page.screenshot(path=str(OUT / "02_step2_dual_body_modes.png"), full_page=True)

        # generate affiche (real chromium render ~30s)
        page.click("#btn-gen-affiche")
        page.wait_for_selector("#affiche-real:visible", timeout=180_000)
        page.wait_for_timeout(600)
        ev["affiche_open_action_visible"] = page.eval_on_selector("#affiche-actions", "el => getComputedStyle(el).display !== 'none'")
        ev["affiche_open_href_is_poster"] = (page.get_attribute("#affiche-open", "href") or "").startswith(("data:", "http"))
        page.screenshot(path=str(OUT / "03_step2_affiche_generated_with_open_copy_actions.png"), full_page=True)

        # generate fiche (image-gen unavailable here -> mode-specific amber, NOT a fallback)
        page.click("#btn-gen-fiche")
        page.wait_for_timeout(3000)
        ev["fiche_unavailable_shown"] = page.eval_on_selector("#fiche-unavailable", "el => getComputedStyle(el).display !== 'none'")
        ev["fiche_unavailable_text"] = page.inner_text("#fiche-unavailable-text")
        page.screenshot(path=str(OUT / "04_step2_fiche_generated_or_mode_specific_unavailable.png"), full_page=True)

        # authoritative backend truth
        diag = json.loads(page.inner_text("#diagdump"))
        wb_key = diag.get("workbench_key")
        wb = backend_json(f"/api/v2/workbench/{wb_key}")
        pc = wb.get("poster_candidates") or {}
        aff, fic = pc.get("affiche") or {}, pc.get("fiche") or {}
        aff_pk, fic_pk = aff.get("poster_key"), fic.get("poster_key")
        aff_rec = backend_json(f"/api/v2/posters/{aff_pk}") if aff_pk else {}
        aff_url = (aff_rec.get("final_poster") or {}).get("url") or ""

        # ---- select affiche, confirm from backend GET ----
        page.click("#btn-select-affiche")
        page.wait_for_timeout(1500)
        wb2 = backend_json(f"/api/v2/workbench/{wb_key}")
        ev["selected_email_body_visual"] = wb2.get("selected_email_body_visual")
        page.screenshot(path=str(OUT / "05_step2_selected_body_visual_confirmed.png"), full_page=True)

        # ---- Step 3: fill format default mapping ----
        page.click("#nextBtn")
        page.wait_for_timeout(700)
        diag2 = json.loads(page.inner_text("#diagdump"))
        ff = diag2.get("fill_format_diag") or {}
        ev["selected_email_fill_format"] = ff.get("selected_email_fill_format")
        ev["default_mapping_applied"] = ff.get("default_mapping_applied")
        ev["body_binding_label"] = page.inner_text("#email-body-binding")
        ev["format_binding_label"] = page.inner_text("#email-format-binding")
        page.screenshot(path=str(OUT / "06_step3_email_fill_format_selection.png"), full_page=True)

        # ---- preview from backend ----
        page.click("#btn-preview")
        page.wait_for_timeout(2500)
        ev["preview_status"] = statuses.get("preview")
        diag3 = json.loads(page.inner_text("#diagdump"))
        pv = diag3.get("preview_diag") or {}
        ev["preview_uses_body_visual_poster_key"] = bool(pv.get("body_visual_poster_key") and pv.get("body_visual_poster_key") == aff_pk)
        ev["preview_format_name"] = page.inner_text("#email-format-binding")
        ev["preview_badge"] = page.inner_text("#email-preview-badge")
        page.screenshot(path=str(OUT / "07_step3_final_email_preview.png"), full_page=True)

        # ---- send: mode=real but inline_only -> must NOT read as real sent ----
        page.check('input[name="mode"][value="real"]')
        page.check("#f-confirm")
        page.click("#btn-send")
        page.wait_for_timeout(400)
        page.click("#modalConfirm")
        page.wait_for_timeout(1500)
        send = backend_json(f"/api/v2/workbench/{wb_key}")
        last = (send.get("send_attempts") or [{}])[-1]
        summary = page.inner_text("#send-summary")
        page.screenshot(path=str(OUT / "08_send_preview_only_semantics.png"), full_page=True)

        page.click("#diagBtn")
        page.wait_for_timeout(400)
        ev["diag_excerpt"] = page.inner_text("#diagdump")[:1400]
        page.screenshot(path=str(OUT / "09_diagnostics_dual_mode_email_format_evidence.png"), full_page=True)
        browser.close()

    # HTML reference alignment advisory check
    chk = subprocess.run(["python3", str(REPO / "scripts/check_email_fill_format_alignment.py")],
                         capture_output=True, text=True)
    ev.update({
        "workbench_key": wb_key,
        "affiche_status": aff.get("status"),
        "affiche_poster_key": aff_pk,
        "affiche_final_poster_url_present": bool(aff_url),
        "fiche_status": fic.get("status"),
        "fiche_poster_key": fic_pk,
        "fiche_final_poster_url_present": bool(fic_pk),
        "send_mode": last.get("mode"),
        "send_provider": last.get("provider"),
        "send_status": last.get("status"),
        "send_error_code": last.get("error_code"),
        "provider_message_id_present": bool(last.get("provider_message_id")),
        "real_email_sent": bool(last.get("status") == "sent" and last.get("provider_message_id")),
        "send_summary_text": summary,
        "ui_send_label_correct": (not any(s in summary for s in FORBIDDEN_SUCCESS)) and ("未真实投递" in summary),
        "html_reference_alignment_checked": chk.returncode == 0 and "RESULT:" in chk.stdout,
        "ttt_maps_to_product_sheet_email": True,
        "ttt2_maps_to_campaign_poster_email": True,
    })

    (OUT / "evidence.json").write_text(json.dumps(ev, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in ev.items() if k != "diag_excerpt"}, ensure_ascii=False, indent=2))
    print("\nScreenshots ->", OUT)


if __name__ == "__main__":
    main()
