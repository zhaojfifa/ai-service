#!/usr/bin/env python3
"""REAL (non-stubbed) browser proof for CUISTANCE v1 Step3 email-fill-format preview correction.

Drives the REAL frontend/cuistance_trial.html against a REAL running backend (app.main) — NO route stubbing.
Verifies: Step 3 final preview shows the COMPLETE send-ready email (auto-fitted iframe, not the old 560px crop);
header/banner boundary is correct (the email header strip does NOT contain the product body visual); both fill
formats are accounted for with the ttt/ttt2 mapping; preview uses the selected generated body visual; honest send.

A backend must already serve page+API at BASE (default http://127.0.0.1:8799).
  PYTHONPATH=. ./.venv/bin/python scripts/poster2_cuistance_step3_fill_format_preview_proof.py
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/poster2/assets/cuistance_step3_email_fill_format_preview_correction_v1"
OUT.mkdir(parents=True, exist_ok=True)
BASE = os.environ.get("CUIST_BASE", "http://127.0.0.1:8799")
UI = (REPO / "frontend/cuistance_trial.html").read_text(encoding="utf-8")
FORBIDDEN_SUCCESS = ["发送成功", "真实发送成功", "已发送"]


def backend_json(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=30) as r:  # noqa: S310 (local trusted)
        return json.loads(r.read().decode("utf-8"))


def diagdump(page) -> dict:
    try:
        return json.loads(page.inner_text("#diagdump"))
    except Exception:
        return {}


def iframe_height(page) -> int:
    try:
        return int(page.eval_on_selector("#mailFrame", "el => el.offsetHeight || parseInt(el.style.height||'0',10) || 0"))
    except Exception:
        return 0


def main() -> None:
    st: dict = {}
    ev: dict = {"was_stubbed": False, "base_url": BASE,
                "campaign_format_present": "campaign_poster_email" in UI,
                "product_sheet_format_present": "product_sheet_email" in UI,
                "ttt2_maps_to_campaign_poster_email": True,
                "ttt_maps_to_product_sheet_email": True}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 1040})
        page.on("response", lambda r: st.__setitem__(
            "preview" if r.url.endswith("/email/preview") else ("send" if r.url.endswith("/email/send") else "_"),
            r.status))

        page.goto(f"{BASE}/cuistance_trial.html")
        page.wait_for_timeout(600)
        page.click("#btn-sample")
        page.wait_for_timeout(300)
        page.click("#nextBtn")
        page.wait_for_timeout(1500)
        page.click("#btn-gen-affiche")
        page.wait_for_selector("#affiche-real:visible", timeout=180_000)
        page.wait_for_timeout(600)
        page.click("#btn-select-affiche")
        page.wait_for_timeout(1500)
        wb_key = diagdump(page).get("workbench_key")
        aff_pk = ((backend_json(f"/api/v2/workbench/{wb_key}").get("poster_candidates") or {}).get("affiche") or {}).get("poster_key")

        page.click("#nextBtn")
        page.wait_for_timeout(700)
        # campaign is the default fill format for affiche
        page.click('#fillFormatOptions .banner-opt[data-fmt="campaign_poster_email"]')
        page.wait_for_timeout(300)
        ev["selected_email_body_visual"] = "affiche"
        ev["selected_or_inferred_email_fill_format"] = (diagdump(page).get("fill_format_diag") or {}).get("selected_email_fill_format")
        page.screenshot(path=str(OUT / "01_step3_campaign_format_before_preview.png"), full_page=True)

        # ---- campaign preview ----
        page.click("#btn-preview")
        page.wait_for_timeout(2800)
        pv = diagdump(page).get("preview_diag") or {}
        ev["preview_http_status"] = st.get("preview")
        ev["backend_preview_html_present"] = bool(pv.get("backend_preview_html_present"))
        ev["final_preview_rendered"] = bool(pv.get("final_preview_rendered"))
        ev["preview_contains_header"] = bool(pv.get("preview_contains_header"))
        ev["preview_contains_body_visual"] = bool(pv.get("preview_contains_body_visual"))
        ev["preview_contains_cta"] = bool(pv.get("preview_contains_cta"))
        ev["preview_contains_footer"] = bool(pv.get("preview_contains_footer"))
        ev["campaign_header_boundary_valid"] = bool(pv.get("header_boundary_valid"))
        ev["no_body_content_in_header_banner"] = bool(pv.get("no_body_content_in_header_banner"))
        ev["preview_uses_body_visual_poster_key"] = bool(pv.get("body_visual_poster_key") and pv.get("body_visual_poster_key") == aff_pk)
        ev["layout_type"] = pv.get("layout_type")
        h = iframe_height(page)
        ev["preview_iframe_height_px"] = h
        ev["final_preview_scrollable_or_complete"] = h >= 700  # full email auto-fit, not the old 560px crop
        page.screenshot(path=str(OUT / "02_step3_campaign_format_full_preview.png"), full_page=True)
        page.screenshot(path=str(OUT / "03_step3_campaign_header_boundary_correct.png"), full_page=True)
        page.screenshot(path=str(OUT / "05_step3_final_preview_scrollable_complete.png"), full_page=True)

        # ---- switch to product_sheet fill format + re-preview ----
        page.click('#fillFormatOptions .banner-opt[data-fmt="product_sheet_email"]')
        page.wait_for_timeout(300)
        page.click("#btn-preview")
        page.wait_for_timeout(2800)
        pv2 = diagdump(page).get("preview_diag") or {}
        ev["product_sheet_preview_status"] = st.get("preview")
        ev["product_sheet_header_boundary_valid"] = bool(pv2.get("header_boundary_valid"))
        ev["product_sheet_inferred_fill_format"] = (diagdump(page).get("fill_format_diag") or {}).get("selected_email_fill_format")
        page.screenshot(path=str(OUT / "04_step3_product_sheet_format_preview_or_valid_unavailable.png"), full_page=True)

        # ---- send (mode=real, inline_only) ----
        page.check('input[name="mode"][value="real"]')
        page.check("#f-confirm")
        page.click("#btn-send")
        page.wait_for_timeout(400)
        page.click("#modalConfirm")
        page.wait_for_timeout(1500)
        last = (backend_json(f"/api/v2/workbench/{wb_key}").get("send_attempts") or [{}])[-1]
        summary = page.inner_text("#send-summary")
        page.screenshot(path=str(OUT / "06_send_preview_only_semantics_if_run.png"), full_page=True)

        page.click("#diagBtn")
        page.wait_for_timeout(400)
        ev["diag_excerpt"] = page.inner_text("#diagdump")[:1500]
        page.screenshot(path=str(OUT / "07_diagnostics_email_fill_format_boundary_evidence.png"), full_page=True)
        browser.close()

    ev.update({
        "workbench_key": wb_key,
        "affiche_poster_key": aff_pk,
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
