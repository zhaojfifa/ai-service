#!/usr/bin/env python3
"""Phase 3 operator-flow proof for the CUISTANCE PSD email container (REAL backend, NO stubbing).

Runs the 3-step CUISTANCE trial against a REAL app.main backend and captures operator screenshots 05-10 +
flow evidence: Step1 save -> Step2 affiche generate -> select (backend-confirmed) -> Step3
cuistance_email_container_psd_v1 preview -> hard-refresh recovery + re-preview -> inline_only send (not real).

A backend must already serve page+API at BASE (default http://127.0.0.1:8799).
  PYTHONPATH=. ./.venv/bin/python scripts/poster2_cuistance_psd_container_operator_proof.py
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OPS = REPO / "docs/poster2/assets/cuistance_psd_email_container_last_mile_v1/operator_screenshots"
BASE = os.environ.get("CUIST_BASE", "http://127.0.0.1:8799")


def bj(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=30) as r:  # noqa: S310
        return json.loads(r.read().decode("utf-8"))


def diag(page) -> dict:
    try:
        return json.loads(page.inner_text("#diagdump"))
    except Exception:
        return {}


def main() -> None:
    OPS.mkdir(parents=True, exist_ok=True)
    st: dict = {}
    ev: dict = {"was_stubbed": False}
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": 1400, "height": 1040})
        page.on("response", lambda r: st.__setitem__(
            "preview" if r.url.endswith("/email/preview") else ("send" if r.url.endswith("/email/send") else "_"),
            r.status))

        page.goto(f"{BASE}/cuistance_trial.html"); page.wait_for_timeout(600)
        page.click("#btn-sample"); page.wait_for_timeout(300)
        page.click("#nextBtn"); page.wait_for_timeout(1800)
        wb = diag(page).get("workbench_key")
        w = bj(f"/api/v2/workbench/{wb}"); pa = w.get("product_assets") or {}
        ev["step1_assets_saved"] = (len(pa.get("product_images") or []) >= 1 and len(pa.get("gallery_images") or []) >= 1)
        page.screenshot(path=str(OPS / "05_step1_assets_saved.png"), full_page=True)

        page.click("#btn-gen-affiche")
        page.wait_for_selector("#affiche-real:visible", timeout=180_000); page.wait_for_timeout(600)
        gp = (diag(page).get("generated_poster_diag") or {}).get("generated_poster_key")
        ev["step2_affiche_generated"] = bool(gp)
        page.screenshot(path=str(OPS / "06_step2_affiche_generated.png"), full_page=True)

        page.click("#btn-select-affiche"); page.wait_for_timeout(1500)
        ev["selected_visual_confirmed"] = bj(f"/api/v2/workbench/{wb}").get("selected_email_body_visual") == "affiche"
        page.screenshot(path=str(OPS / "07_step2_selected_visual_confirmed.png"), full_page=True)

        page.click("#nextBtn"); page.wait_for_timeout(700)
        page.click('#fillFormatOptions .banner-opt[data-fmt="campaign_poster_email"]'); page.wait_for_timeout(300)
        page.click("#btn-preview"); page.wait_for_timeout(2800)
        pv = diag(page).get("preview_diag") or {}
        ev["step3_preview_ok"] = (st.get("preview") == 200 and bool(pv.get("final_preview_rendered")))
        ev["email_container"] = {
            "template_id": pv.get("email_container_template_id"),
            "email_fill_format": pv.get("email_fill_format"),
            "header_source": pv.get("header_source"),
            "legacy_truth_rejected": pv.get("legacy_truth_rejected"),
            "workbench_truth_used": pv.get("workbench_truth_used"),
            "uses_current_selected_visual": pv.get("uses_current_selected_visual"),
            "body_visual_poster_key": pv.get("body_visual_poster_key"),
            "preview_contains_header": pv.get("preview_contains_header"),
            "preview_contains_body_visual": pv.get("preview_contains_body_visual"),
            "preview_contains_cta": pv.get("preview_contains_cta"),
            "preview_contains_footer": pv.get("preview_contains_footer"),
            "no_body_content_in_header_banner": pv.get("no_body_content_in_header_banner"),
        }
        page.screenshot(path=str(OPS / "08_step3_psd_email_container_preview.png"), full_page=True)

        # hard refresh -> recover -> re-preview same selected visual
        page.reload(); page.wait_for_timeout(900)
        page.wait_for_function("() => { try { return !!JSON.parse(document.getElementById('diagdump').textContent).workbench_key } catch(e){ return false } }", timeout=60_000)
        page.wait_for_timeout(700)
        # navigate to step 3 if needed and re-preview
        try:
            page.click('#stepper .step[data-step="3"]'); page.wait_for_timeout(500)
        except Exception:
            pass
        page.click("#btn-preview"); page.wait_for_timeout(2800)
        pv2 = diag(page).get("preview_diag") or {}
        ev["refresh_recovery_ok"] = (bj(f"/api/v2/workbench/{wb}").get("selected_email_body_visual") == "affiche"
                                     and st.get("preview") == 200)
        ev["recovered_workbench_key"] = diag(page).get("workbench_key")
        page.screenshot(path=str(OPS / "09_refresh_recovery_preview.png"), full_page=True)

        # send mode=real inline -> must read preview-only, not real sent
        page.check('input[name="mode"][value="real"]'); page.check("#f-confirm")
        page.click("#btn-send"); page.wait_for_timeout(400); page.click("#modalConfirm"); page.wait_for_timeout(1500)
        last = (bj(f"/api/v2/workbench/{wb}").get("send_attempts") or [{}])[-1]
        summary = page.inner_text("#send-summary")
        ev["send"] = {"mode": last.get("mode"), "provider": last.get("provider"), "status": last.get("status"),
                      "error_code": last.get("error_code"), "provider_message_id": last.get("provider_message_id"),
                      "real_email_sent": bool(last.get("status") == "sent" and last.get("provider_message_id")),
                      "ui_send_label_correct": ("未真实投递" in summary) and not any(s in summary for s in ["发送成功", "真实发送成功", "已发送"])}
        page.screenshot(path=str(OPS / "10_send_semantics_no_real_send.png"), full_page=True)
        b.close()

    ev["workbench_key"] = wb
    ev["generated_poster_key"] = gp
    (OPS.parent / "operator_flow_evidence.json").write_text(json.dumps(ev, ensure_ascii=False, indent=2))
    print(json.dumps(ev, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
