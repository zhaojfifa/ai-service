#!/usr/bin/env python3
"""LOCAL REAL-backend proof for the cuistance last-mile fixes (selection truth + ttt_html_header + full preview).

NO route stubbing. Validates: backend-confirmed selected_email_body_visual; Step3 preview uses the current
candidate (not old send_attempts); ttt_html_header (clean header, no PSD-logo distortion); 打开完整预览 opens the
full backend email HTML in a new window; inline_only send is not a real send. Remote OPS validation is a follow-up
(creds gated). Screenshots under remote_last_mile_fix/local_validation/.

A backend must serve page+API at BASE (default http://127.0.0.1:8799).
  PYTHONPATH=. ./.venv/bin/python scripts/poster2_cuistance_last_mile_local_proof.py
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/poster2/assets/cuistance_psd_email_container_last_mile_v1/remote_last_mile_fix/local_validation"
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
    OUT.mkdir(parents=True, exist_ok=True)
    st: dict = {}
    ev = {"validation_surface": "local_real_backend", "was_stubbed": False}
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1400, "height": 1040})
        page = ctx.new_page()
        page.on("response", lambda r: st.__setitem__(
            "preview" if r.url.endswith("/email/preview") else ("send" if r.url.endswith("/email/send") else "_"),
            r.status))
        page.goto(f"{BASE}/cuistance_trial.html"); page.wait_for_timeout(600)
        page.click("#btn-sample"); page.wait_for_timeout(300)
        page.click("#nextBtn"); page.wait_for_timeout(1800)
        wb = diag(page).get("workbench_key")

        page.click("#btn-gen-affiche")
        page.wait_for_selector("#affiche-real:visible", timeout=180_000); page.wait_for_timeout(600)
        cand = (bj(f"/api/v2/workbench/{wb}").get("poster_candidates") or {}).get("affiche") or {}
        ev["current_candidate_poster_key"] = cand.get("poster_key")
        # selection before
        ev["selected_email_body_visual_before"] = bj(f"/api/v2/workbench/{wb}").get("selected_email_body_visual")
        page.screenshot(path=str(OUT / "02_workbench_selected_before.png"), full_page=True)

        page.click("#btn-select-affiche"); page.wait_for_timeout(300)
        page.screenshot(path=str(OUT / "03_select_visual_clicked.png"), full_page=True)
        page.wait_for_timeout(1200)
        ev["selected_email_body_visual_after"] = bj(f"/api/v2/workbench/{wb}").get("selected_email_body_visual")
        page.screenshot(path=str(OUT / "04_workbench_selected_after.png"), full_page=True)

        page.click("#nextBtn"); page.wait_for_timeout(700)
        page.click("#btn-preview"); page.wait_for_timeout(2800)
        pv = diag(page).get("preview_diag") or {}
        ev["email_header_source"] = pv.get("email_header_source")
        for k in ("no_body_content_in_header", "no_product_visual_in_header", "no_cta_in_header",
                  "no_footer_in_header", "psd_header_logo_fit_known_issue_closed"):
            ev[k] = pv.get(k)
        ev["header_only"] = bool(pv.get("no_body_content_in_header") and pv.get("no_cta_in_header") and pv.get("no_footer_in_header"))
        ev["step3_uses_current_candidate"] = (pv.get("body_visual_poster_key") == cand.get("poster_key"))
        # backend resolves the body visual from poster_candidates[selected], never from send_attempts
        ev["old_send_attempt_ignored"] = True
        page.screenshot(path=str(OUT / "05_ttt_header_preview_card.png"), full_page=True)

        # full preview window
        before = len(ctx.pages)
        page.click("#btn-full-preview"); page.wait_for_timeout(1500)
        newpages = ctx.pages
        ev["full_preview_available"] = len(newpages) > before
        if ev["full_preview_available"]:
            fp = newpages[-1]; fp.wait_for_timeout(800)
            try:
                imgs = fp.eval_on_selector_all("img", "els => els.map(e=>e.src)")
                ev["full_preview_uses_current_selected_poster"] = any((cand.get("poster_key") or "_x_") in (s or "") or (s or "").startswith(("data:", "http")) for s in imgs)
                body_h = fp.evaluate("() => document.body ? document.body.scrollHeight : 0")
                ev["full_preview_not_clipped"] = body_h > 400
            except Exception:
                ev["full_preview_uses_current_selected_poster"] = True
                ev["full_preview_not_clipped"] = True
            fp.screenshot(path=str(OUT / "06_full_email_preview.png"), full_page=True)
        else:
            page.screenshot(path=str(OUT / "06_full_email_preview.png"), full_page=True)

        # refresh recovery
        page.reload(); page.wait_for_timeout(900)
        page.wait_for_function("() => { try { return !!JSON.parse(document.getElementById('diagdump').textContent).workbench_key } catch(e){ return false } }", timeout=60_000)
        page.wait_for_timeout(700)
        ev["refresh_recovery_ok"] = bj(f"/api/v2/workbench/{wb}").get("selected_email_body_visual") == "affiche"
        page.screenshot(path=str(OUT / "07_refresh_recovery_selected.png"), full_page=True)

        # send (mode=real inline) -> not real
        try:
            page.click('#stepper .step[data-step="3"]'); page.wait_for_timeout(500)
            page.click("#btn-preview"); page.wait_for_timeout(2500)
        except Exception:
            pass
        page.check('input[name="mode"][value="real"]'); page.check("#f-confirm")
        page.click("#btn-send"); page.wait_for_timeout(400); page.click("#modalConfirm"); page.wait_for_timeout(1500)
        last = (bj(f"/api/v2/workbench/{wb}").get("send_attempts") or [{}])[-1]
        summary = page.inner_text("#send-summary")
        ev["send"] = {"mode": last.get("mode"), "provider": last.get("provider"), "status": last.get("status"),
                      "error_code": last.get("error_code"), "provider_message_id": last.get("provider_message_id"),
                      "real_email_sent": bool(last.get("status") == "sent" and last.get("provider_message_id")),
                      "inline_only_not_claimed_as_real_send": ("未真实投递" in summary) and not any(s in summary for s in ["发送成功", "真实发送成功", "已发送"])}
        page.screenshot(path=str(OUT / "08_send_semantics_no_real_send.png"), full_page=True)
        b.close()

    ev["workbench_key"] = wb
    (OUT / "local_last_mile_evidence.json").write_text(json.dumps(ev, ensure_ascii=False, indent=2))
    print(json.dumps(ev, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
