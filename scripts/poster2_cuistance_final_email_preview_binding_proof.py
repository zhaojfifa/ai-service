#!/usr/bin/env python3
"""REAL (non-stubbed) browser proof for CUISTANCE v1 final email preview binding.

Drives the REAL frontend/cuistance_trial.html against a REAL running backend (app.main) — NO route stubbing.
Verifies: Step 3 right-side preview is bound to POST /api/v2/workbench/{key}/email/preview (HTTP 200 → backend
assembled HTML rendered, label 邮件预览已生成); send is gated until a preview exists; inline_only/preview_only is not
labeled real sent. Screenshots + evidence.json (was_stubbed=false).

A backend must already serve page+API at BASE (default http://127.0.0.1:8799).
  PYTHONPATH=. ./.venv/bin/python scripts/poster2_cuistance_final_email_preview_binding_proof.py
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/poster2/assets/cuistance_final_email_preview_binding_v1"
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
        d = diagdump(page)
        wb_key = d.get("workbench_key")
        wb = backend_json(f"/api/v2/workbench/{wb_key}")
        aff = (wb.get("poster_candidates") or {}).get("affiche") or {}
        aff_pk = aff.get("poster_key")

        # enter Step 3
        page.click("#nextBtn")
        page.wait_for_timeout(700)
        # BEFORE preview: panel must say preview not generated; send disabled
        ev["before_preview_badge"] = page.inner_text("#email-preview-badge")
        ev["send_disabled_before_preview"] = page.eval_on_selector("#btn-send", "el => el.disabled")
        page.screenshot(path=str(OUT / "01_step3_before_preview_not_generated.png"), full_page=True)

        # click 预览邮件 -> backend preview
        page.click("#btn-preview")
        page.wait_for_timeout(2500)
        ev["preview_http_status"] = st.get("preview")
        ev["after_preview_badge"] = page.inner_text("#email-preview-badge")
        ev["send_disabled_after_preview"] = page.eval_on_selector("#btn-send", "el => el.disabled")
        pv = diagdump(page).get("preview_diag") or {}
        ev["backend_preview_html_present"] = bool(pv.get("backend_preview_html_present"))
        ev["final_preview_rendered"] = bool(pv.get("final_preview_rendered")) and page.eval_on_selector(
            "#mailFrame", "el => el && getComputedStyle(el).display !== 'none' && (el.contentWindow.document.body ? el.contentWindow.document.body.innerText.length : 0) > 20")
        ev["selected_email_body_visual"] = pv.get("selected_email_body_visual")
        ev["body_visual_poster_key"] = pv.get("body_visual_poster_key")
        ev["selected_or_inferred_email_fill_format"] = pv.get("selected_email_fill_format")
        ev["layout_type"] = pv.get("layout_type")
        # does the rendered preview contain the generated poster image (data:/http img) ?
        ev["preview_contains_generated_poster"] = page.eval_on_selector(
            "#mailFrame",
            "el => { try { return Array.from(el.contentWindow.document.images).some(i => (i.src||'').startsWith('data:') || (i.src||'').startsWith('http')); } catch(e){ return false; } }")
        page.screenshot(path=str(OUT / "02_step3_after_backend_preview_generated.png"), full_page=True)
        page.screenshot(path=str(OUT / "03_step3_preview_contains_generated_poster.png"), full_page=True)

        # send (mode=real, inline_only) -> must NOT read as real sent
        page.check('input[name="mode"][value="real"]')
        page.check("#f-confirm")
        page.click("#btn-send")
        page.wait_for_timeout(400)
        page.click("#modalConfirm")
        page.wait_for_timeout(1500)
        last = (backend_json(f"/api/v2/workbench/{wb_key}").get("send_attempts") or [{}])[-1]
        summary = page.inner_text("#send-summary")
        page.screenshot(path=str(OUT / "04_send_preview_only_not_real_sent.png"), full_page=True)

        page.click("#diagBtn")
        page.wait_for_timeout(400)
        ev["diag_excerpt"] = page.inner_text("#diagdump")[:1400]
        page.screenshot(path=str(OUT / "05_diagnostics_email_preview_binding_evidence.png"), full_page=True)
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
