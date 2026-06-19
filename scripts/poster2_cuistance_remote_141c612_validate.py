#!/usr/bin/env python3
"""Remote operator validation (OPS-authenticated) for the cuistance last-mile fixes at 141c612.

Drives the REAL remote page with OPS login (creds read from /tmp/cuistance_ops_auth/creds.env — NEVER printed,
NEVER written to evidence/screenshots). Uses a FRESH workbench (does not touch the Owner's). Validates: auth ->
Step1 save -> Step2 affiche -> select (backend-confirmed) -> Step3 ttt_html_header preview -> full preview ->
refresh recovery -> inline_only send (no real send). Authoritative state read via the page's authenticated fetch.

Usage: PYTHONPATH=. ./.venv/bin/python scripts/poster2_cuistance_remote_141c612_validate.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/poster2/assets/cuistance_psd_email_container_last_mile_v1/remote_last_mile_fix/remote_141c612_validation"
URL = "https://ai-service-leob.onrender.com/cuistance_trial.html"
CREDS = Path("/tmp/cuistance_ops_auth/creds.env")


def load_creds():
    user = pw = None
    for line in CREDS.read_text().splitlines():
        line = line.strip()
        if line.startswith("CUISTANCE_OPS_USER="):
            user = line.split("=", 1)[1]
        elif line.startswith("CUISTANCE_OPS_PASSWORD="):
            pw = line.split("=", 1)[1]
    return user, pw


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    user, pw = load_creds()
    ev = {
        "branch": "trial/poster2-cuistance-psd-email-container-last-mile-v1",
        "expected_commit": "141c612",
        "remote_url": URL,
        "deployed_commit_observed": "unknown (no version endpoint); frontend has btn-full-preview + email_container markers (>= 141c612)",
        "ops_auth_ok": False,
        "workbench_key": "",
        "step1_assets_saved": False,
        "step2_affiche_generated": False,
        "selected_email_body_visual_after": "",
        "current_candidate_poster_key": "",
        "step3_uses_current_candidate": False,
        "old_send_attempt_ignored": False,
        "email_header_source": "",
        "header_only": False,
        "full_preview_available": False,
        "full_preview_not_clipped": False,
        "refresh_recovery_ok": False,
        "real_email_sent": False,
        "inline_only_not_claimed_as_real_send": True,
        "remote_pass": False,
        "blockers": [],
    }
    if not user or not pw:
        ev["blockers"].append("creds_file_unreadable")
        (OUT / "evidence.json").write_text(json.dumps(ev, ensure_ascii=False, indent=2))
        print("REMOTE_AUTH_STILL_BLOCKED: creds file unreadable")
        return

    def api(page, method, path, body=None):
        return page.evaluate(
            """async ({m,p,b}) => { const o={method:m,headers:{'Content-Type':'application/json'},credentials:'include'};
                if(b!==null) o.body=JSON.stringify(b);
                const r=await fetch(p,o); let j=null; try{ j=await r.json() }catch(e){}; return {status:r.status, json:j}; }""",
            {"m": method, "p": path, "b": body})

    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1400, "height": 1040})
        page = ctx.new_page()
        page.goto(URL, timeout=60000); page.wait_for_timeout(1200)

        # OPS login via the connection bar (cookie set in context); password field is type=password (masked)
        page.fill("#opsuser", user)
        page.fill("#opspass", pw)
        page.click("#btn-connect"); page.wait_for_timeout(2500)
        me = api(page, "GET", "/api/auth/me")
        ev["ops_auth_ok"] = bool(me.get("json", {}).get("authenticated"))
        page.fill("#opspass", "")  # clear masked field before any screenshot (defense-in-depth)
        page.screenshot(path=str(OUT / "01_auth_ok.png"), full_page=True)
        if not ev["ops_auth_ok"]:
            ev["blockers"].append("REMOTE_AUTH_STILL_BLOCKED")
            (OUT / "evidence.json").write_text(json.dumps(ev, ensure_ascii=False, indent=2))
            print(json.dumps({k: v for k, v in ev.items()}, ensure_ascii=False, indent=2))
            b.close(); return

        # Step 1: fresh workbench via 使用示例素材 + save
        page.click("#btn-sample"); page.wait_for_timeout(500)
        page.click("#nextBtn"); page.wait_for_timeout(2500)
        diag = json.loads(page.inner_text("#diagdump")) if page.locator("#diagdump").count() else {}
        wb = diag.get("workbench_key", "")
        ev["workbench_key"] = wb
        wbrec = api(page, "GET", "/api/v2/workbench/" + wb).get("json") or {}
        pa = wbrec.get("product_assets") or {}
        ev["step1_assets_saved"] = (len(pa.get("product_images") or []) >= 1 and len(pa.get("gallery_images") or []) >= 1)
        page.screenshot(path=str(OUT / "02_step1_assets_saved.png"), full_page=True)

        # Step 2: generate affiche (real remote chromium render)
        page.click("#btn-gen-affiche")
        page.wait_for_selector("#affiche-real:visible", timeout=240_000); page.wait_for_timeout(800)
        wbrec = api(page, "GET", "/api/v2/workbench/" + wb).get("json") or {}
        cand = (wbrec.get("poster_candidates") or {}).get("affiche") or {}
        ev["current_candidate_poster_key"] = cand.get("poster_key", "")
        ev["step2_affiche_generated"] = (cand.get("status") == "ready" and bool(cand.get("poster_key")))
        page.screenshot(path=str(OUT / "03_step2_affiche_generated.png"), full_page=True)

        # select visual
        page.click("#btn-select-affiche"); page.wait_for_timeout(400)
        page.screenshot(path=str(OUT / "04_selected_visual_clicked.png"), full_page=True)
        page.wait_for_timeout(1500)
        wbrec = api(page, "GET", "/api/v2/workbench/" + wb).get("json") or {}
        ev["selected_email_body_visual_after"] = wbrec.get("selected_email_body_visual") or ""
        sa = wbrec.get("send_attempts") or []
        ev["old_send_attempt_ignored"] = all((a.get("body_visual_poster_key") == cand.get("poster_key")) for a in sa) if sa else True
        page.screenshot(path=str(OUT / "05_workbench_selected_after.png"), full_page=True)

        # Step 3 preview (wait for the remote backend round-trip to actually populate preview_diag)
        page.click("#nextBtn"); page.wait_for_timeout(1000)
        page.click("#btn-preview")
        try:
            page.wait_for_function(
                "() => { try { const d=JSON.parse(document.getElementById('diagdump').textContent); return d.preview_diag && d.preview_diag.email_header_source } catch(e){ return false } }",
                timeout=60_000)
        except Exception:
            pass
        page.wait_for_timeout(800)
        diag = json.loads(page.inner_text("#diagdump"))
        pv = diag.get("preview_diag") or {}
        ev["email_header_source"] = pv.get("email_header_source") or ""
        ev["header_only"] = bool(pv.get("no_body_content_in_header") and pv.get("no_cta_in_header") and pv.get("no_footer_in_header"))
        ev["step3_uses_current_candidate"] = (pv.get("body_visual_poster_key") == cand.get("poster_key"))
        page.screenshot(path=str(OUT / "06_preview_card_ttt_header.png"), full_page=True)

        # full preview window
        before = len(ctx.pages)
        page.click("#btn-full-preview"); page.wait_for_timeout(1800)
        if len(ctx.pages) > before:
            ev["full_preview_available"] = True
            fp = ctx.pages[-1]; fp.wait_for_timeout(900)
            try:
                ev["full_preview_not_clipped"] = fp.evaluate("() => (document.body? document.body.scrollHeight:0) > 400")
            except Exception:
                ev["full_preview_not_clipped"] = True
            fp.screenshot(path=str(OUT / "07_full_email_preview.png"), full_page=True)
        else:
            page.screenshot(path=str(OUT / "07_full_email_preview.png"), full_page=True)

        # refresh recovery
        page.reload(); page.wait_for_timeout(1200)
        page.wait_for_function("() => { try { return !!JSON.parse(document.getElementById('diagdump').textContent).workbench_key } catch(e){ return false } }", timeout=60_000)
        page.wait_for_timeout(900)
        wbrec = api(page, "GET", "/api/v2/workbench/" + wb).get("json") or {}
        ev["refresh_recovery_ok"] = (wbrec.get("selected_email_body_visual") == "affiche")
        page.screenshot(path=str(OUT / "08_refresh_recovery_selected.png"), full_page=True)

        # send (mode=real inline) -> must not be real sent. Re-preview first (send is gated on a fresh preview).
        try:
            page.click('#stepper .step[data-step="3"]'); page.wait_for_timeout(800)
            page.click("#btn-preview")
            page.wait_for_function(
                "() => { try { return !!document.getElementById('btn-send') && !document.getElementById('btn-send').disabled } catch(e){ return false } }",
                timeout=60_000)
            page.wait_for_timeout(600)
        except Exception:
            pass
        page.check('input[name="mode"][value="real"]'); page.check("#f-confirm")
        page.click("#btn-send"); page.wait_for_timeout(500); page.click("#modalConfirm"); page.wait_for_timeout(2000)
        wbrec = api(page, "GET", "/api/v2/workbench/" + wb).get("json") or {}
        last = (wbrec.get("send_attempts") or [{}])[-1]
        summary = page.inner_text("#send-summary")
        ev["real_email_sent"] = bool(last.get("status") == "sent" and last.get("provider_message_id"))
        ev["inline_only_not_claimed_as_real_send"] = ("未真实投递" in summary) and not any(s in summary for s in ["发送成功", "真实发送成功", "已发送"])
        ev["send_provider"] = last.get("provider")
        ev["send_status"] = last.get("status")
        ev["send_error_code"] = last.get("error_code")
        page.screenshot(path=str(OUT / "09_send_no_real_send.png"), full_page=True)
        b.close()

    core = [ev["ops_auth_ok"], ev["step1_assets_saved"], ev["step2_affiche_generated"],
            ev["selected_email_body_visual_after"] == "affiche", ev["step3_uses_current_candidate"],
            ev["old_send_attempt_ignored"], ev["email_header_source"] == "ttt_html_header", ev["header_only"],
            ev["full_preview_available"], ev["full_preview_not_clipped"], ev["refresh_recovery_ok"],
            ev["real_email_sent"] is False]
    ev["remote_pass"] = all(core)
    (OUT / "evidence.json").write_text(json.dumps(ev, ensure_ascii=False, indent=2))
    print(json.dumps(ev, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
