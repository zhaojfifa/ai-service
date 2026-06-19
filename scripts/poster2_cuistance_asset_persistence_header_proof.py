#!/usr/bin/env python3
"""REAL (non-stubbed) browser proof for CUISTANCE v1 asset persistence + generate payload + header asset fix.

Drives the REAL frontend/cuistance_trial.html against a REAL running backend (app.main) — NO route stubbing.
Verifies: Step 1 assets (incl. gallery) persist to backend workbench on save AND on re-save; generation runs from
backend-confirmed asset state (counts recorded); the generated poster is the current poster_key; selection is
backend-confirmed (not falsely shown); header band assets are header-only and the assembled email header excludes
the product body. Screenshots + evidence.json (was_stubbed=false).

A backend must already serve page+API at BASE (default http://127.0.0.1:8799).
  PYTHONPATH=. ./.venv/bin/python scripts/poster2_cuistance_asset_persistence_header_proof.py
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/poster2/assets/cuistance_asset_persistence_generate_payload_header_fix_v1"
OUT.mkdir(parents=True, exist_ok=True)
BASE = os.environ.get("CUIST_BASE", "http://127.0.0.1:8799")
FORBIDDEN_SUCCESS = ["发送成功", "真实发送成功", "已发送"]


def bj(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=30) as r:  # noqa: S310 (local trusted)
        return json.loads(r.read().decode("utf-8"))


def diag(page) -> dict:
    try:
        return json.loads(page.inner_text("#diagdump"))
    except Exception:
        return {}


def header_only(fn: str) -> bool:
    try:
        from PIL import Image
        w, h = Image.open(REPO / "frontend/assets" / fn).size
        return (w / max(h, 1)) >= 3.0
    except Exception:
        return False


def main() -> None:
    st: dict = {}
    ev: dict = {"was_stubbed": False, "base_url": BASE,
                "banner_option_01_header_only": header_only("header_band_01.png"),
                "banner_option_02_header_only": header_only("header_band_02.png")}
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
        page.screenshot(path=str(OUT / "01_step1_gallery_selected.png"), full_page=True)

        # save Step 1 -> assets persist to backend
        page.click("#nextBtn")
        page.wait_for_timeout(1800)
        wb_key = diag(page).get("workbench_key")
        wb = bj(f"/api/v2/workbench/{wb_key}")
        pa, eb = wb.get("product_assets") or {}, wb.get("email_banner") or {}
        ev.update({
            "workbench_key": wb_key,
            "product_images_count_after_save": len(pa.get("product_images") or []),
            "gallery_images_count_after_save": len(pa.get("gallery_images") or []),
            "atmosphere_present_after_save": bool(pa.get("atmosphere")),
            "logo_present_after_save": bool(eb.get("logo")),
            "banner_background_present_after_save": bool(eb.get("background")),
            "selected_banner_ref": eb.get("selected_banner_ref"),
        })

        # RE-SAVE test (the actual bug): change a Step-1 field on an EXISTING workbench, save again, confirm persisted
        page.click('#stepper .step[data-step="1"]')
        page.wait_for_timeout(400)
        page.fill("#f-pname", "Friteuse RESAVE EF132V")
        page.click("#nextBtn")
        page.wait_for_timeout(1500)
        wb2 = bj(f"/api/v2/workbench/{wb_key}")
        ev["resave_field_persisted"] = (wb2.get("product_truth") or {}).get("product_name") == "Friteuse RESAVE EF132V"
        ev["resave_gallery_still_present"] = len((wb2.get("product_assets") or {}).get("gallery_images") or []) > 0
        page.screenshot(path=str(OUT / "02_workbench_after_save_gallery_persisted.png"), full_page=True)

        # generate affiche (from backend-confirmed assets)
        page.click("#btn-gen-affiche")
        page.wait_for_selector("#affiche-real:visible", timeout=180_000)
        page.wait_for_timeout(600)
        d = diag(page)
        ga = d.get("generation_assets_diag") or {}
        gp = d.get("generated_poster_diag") or {}
        ev.update({
            "generate_candidate_type": "affiche",
            "generation_product_images_count": ga.get("product_images_count"),
            "generation_gallery_images_count": ga.get("gallery_images_count"),
            "generation_atmosphere_present": ga.get("atmosphere_present"),
            "generated_poster_key": gp.get("generated_poster_key"),
        })
        rec = bj(f"/api/v2/posters/{gp.get('generated_poster_key')}") if gp.get("generated_poster_key") else {}
        ev["final_poster_url_present"] = bool((rec.get("final_poster") or {}).get("url"))
        page.screenshot(path=str(OUT / "03_step2_generation_with_asset_counts.png"), full_page=True)

        # selection is backend-confirmed: before select must be null (not falsely selected)
        ev["selected_email_body_visual_before_select"] = bj(f"/api/v2/workbench/{wb_key}").get("selected_email_body_visual")
        page.screenshot(path=str(OUT / "04_step2_current_generated_poster_not_old_send_attempt.png"), full_page=True)

        page.click("#btn-select-affiche")
        page.wait_for_timeout(1500)
        wb3 = bj(f"/api/v2/workbench/{wb_key}")
        ev["selected_email_body_visual_after_select"] = wb3.get("selected_email_body_visual")
        cur_cand = (wb3.get("poster_candidates") or {}).get("affiche") or {}
        ev["selected_poster_key_matches_current_candidate"] = (cur_cand.get("poster_key") == gp.get("generated_poster_key"))
        sa = wb3.get("send_attempts") or []
        ev["old_send_attempt_poster_key_ignored_for_current_selection"] = all(
            (a.get("body_visual_poster_key") == cur_cand.get("poster_key")) for a in sa) if sa else True
        page.screenshot(path=str(OUT / "05_step2_selected_visual_confirmed.png"), full_page=True)

        # Step 3 header options (header-only) + preview
        page.click("#nextBtn")
        page.wait_for_timeout(700)
        page.screenshot(path=str(OUT / "06_step3_header_options_corrected.png"), full_page=True)
        page.click("#btn-preview")
        page.wait_for_timeout(2800)
        pv = diag(page).get("preview_diag") or {}
        ev.update({
            "preview_http_status": st.get("preview"),
            "final_preview_rendered": bool(pv.get("final_preview_rendered")),
            "preview_contains_header": bool(pv.get("preview_contains_header")),
            "preview_contains_body_visual": bool(pv.get("preview_contains_body_visual")),
            "preview_contains_cta": bool(pv.get("preview_contains_cta")),
            "preview_contains_footer": bool(pv.get("preview_contains_footer")),
            "no_body_content_in_header_banner": bool(pv.get("no_body_content_in_header_banner")),
            "header_boundary_valid": bool(pv.get("header_boundary_valid")),
        })
        ev["banner_background_url_is_header_band"] = "header_band" in (((bj(f"/api/v2/workbench/{wb_key}").get("email_banner") or {}).get("background") or {}).get("url") or "")
        page.screenshot(path=str(OUT / "07_step3_final_preview_correct_header.png"), full_page=True)

        # send (mode=real, inline_only)
        page.check('input[name="mode"][value="real"]')
        page.check("#f-confirm")
        page.click("#btn-send")
        page.wait_for_timeout(400)
        page.click("#modalConfirm")
        page.wait_for_timeout(1500)
        last = (bj(f"/api/v2/workbench/{wb_key}").get("send_attempts") or [{}])[-1]
        summary = page.inner_text("#send-summary")
        page.screenshot(path=str(OUT / "08_send_preview_only_if_run.png"), full_page=True)
        page.click("#diagBtn")
        page.wait_for_timeout(400)
        ev["diag_excerpt"] = page.inner_text("#diagdump")[:1500]
        page.screenshot(path=str(OUT / "09_diagnostics_asset_payload_header_evidence.png"), full_page=True)
        browser.close()

    ev.update({
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
