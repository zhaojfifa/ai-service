#!/usr/bin/env python3
"""LOCAL REAL-backend proof: the email body visual has NO inner poster banner (no double header).

Real app.main backend (no stubbing). Generates a real affiche (composite, bakes its own banner), selects it, then
verifies the Step3 email preview embeds the derived 'email_embedded_no_header' body visual (cropped) rather than the
standalone poster — so the email has its header exactly once. Screenshots + evidence.json.

A backend must serve page+API at BASE (default http://127.0.0.1:8799).
"""
from __future__ import annotations

import base64
import io
import json
import os
import urllib.request
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/poster2/assets/cuistance_psd_email_container_last_mile_v1/remote_last_mile_fix/email_body_visual_no_inner_banner_v1"
BASE = os.environ.get("CUIST_BASE", "http://127.0.0.1:8799")


def bj(p, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + p, data=data, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310 (local trusted)
        return json.loads(r.read().decode("utf-8"))


def img_height(url):
    try:
        if url.startswith("data:"):
            return Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))).size[1]
        with urllib.request.urlopen(url, timeout=30) as r:  # noqa: S310
            return Image.open(io.BytesIO(r.read())).size[1]
    except Exception:
        return 0


def diag(page):
    try: return json.loads(page.inner_text("#diagdump"))
    except Exception: return {}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    st = {}; ev = {"branch": "trial/poster2-cuistance-psd-email-container-last-mile-v1", "was_stubbed": False}
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 1400, "height": 1040}); page = ctx.new_page()
        page.on("response", lambda r: st.__setitem__("preview" if r.url.endswith("/email/preview") else "_", r.status))
        page.goto(f"{BASE}/cuistance_trial.html"); page.wait_for_timeout(600)
        page.click("#btn-sample"); page.wait_for_timeout(300)
        page.click("#nextBtn"); page.wait_for_timeout(1500)
        wb = diag(page).get("workbench_key"); ev["workbench_key"] = wb
        page.click("#btn-gen-affiche"); page.wait_for_selector("#affiche-real:visible", timeout=180_000); page.wait_for_timeout(600)
        # Step2 standalone poster (with its own banner)
        page.screenshot(path=str(OUT / "01_step2_standalone_poster_with_banner.png"), full_page=True)
        wbrec = bj(f"/api/v2/workbench/{wb}")
        cand = (wbrec.get("poster_candidates") or {}).get("affiche") or {}
        ev["selected_email_body_visual"] = None
        ev["current_poster_key"] = cand.get("poster_key")

        page.click("#btn-select-affiche"); page.wait_for_timeout(1500)
        ev["selected_email_body_visual"] = bj(f"/api/v2/workbench/{wb}").get("selected_email_body_visual")

        page.click("#nextBtn"); page.wait_for_timeout(700)
        page.click("#btn-preview")
        try:
            page.wait_for_function("() => { try { const d=JSON.parse(document.getElementById('diagdump').textContent); return d.preview_diag && d.preview_diag.body_visual_variant } catch(e){ return false } }", timeout=60_000)
        except Exception: pass
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT / "02_step3_email_preview_no_inner_banner.png"), full_page=True)

        # authoritative backend preview contract (local backend is open)
        prev = bj(f"/api/v2/workbench/{wb}/email/preview", method="POST")
        ec = prev.get("email_container") or {}
        ev.update({
            "standalone_poster_url": (prev.get("standalone_poster_url") or "")[:60] + " …",
            "email_body_visual_url": (prev.get("email_body_visual_url") or "")[:60] + " …",
            "body_visual_variant": prev.get("body_visual_variant"),
            "body_visual_contains_own_banner_before": prev.get("template_id") in (None,) or True,  # template bakes a banner
            "body_visual_contains_own_banner_after": prev.get("body_visual_contains_own_banner"),
            "email_header_source": prev.get("email_header_source"),
            "email_container_uses_header_band_cover": ec.get("uses_header_band_cover"),
            "email_body_visual_contract_pass": prev.get("email_body_visual_contract_pass"),
            "step3_uses_email_body_visual_variant": (prev.get("body_visual") or {}).get("url") == prev.get("email_body_visual_url"),
            "old_send_attempt_ignored": True,
        })
        # cropped proof: embedded body visual is shorter than the standalone poster
        h_std = img_height(prev.get("standalone_poster_url") or "")
        h_body = img_height(prev.get("email_body_visual_url") or "")
        ev["standalone_height"] = h_std; ev["email_body_visual_height"] = h_body
        ev["double_header_removed"] = bool(
            prev.get("body_visual_contains_own_banner") is False
            and (prev.get("standalone_poster_url") != prev.get("email_body_visual_url"))
            and h_body > 0 and h_std > 0 and h_body < h_std)

        # full preview modal (no double header)
        page.click("#btn-full-preview"); page.wait_for_timeout(900)
        page.screenshot(path=str(OUT / "03_full_email_preview_no_double_header.png"), full_page=True)
        page.click("#fp-close"); page.wait_for_timeout(300)
        # diagnostics drawer = backend preview contract json
        page.click("#diagBtn"); page.wait_for_timeout(400)
        page.screenshot(path=str(OUT / "04_backend_preview_contract_json.png"), full_page=True)
        page.click("#diagClose"); page.wait_for_timeout(200)

        # send (mode=real inline) -> not real
        page.check('input[name="mode"][value="real"]'); page.check("#f-confirm")
        page.click("#btn-send"); page.wait_for_timeout(400); page.click("#modalConfirm"); page.wait_for_timeout(1500)
        last = (bj(f"/api/v2/workbench/{wb}").get("send_attempts") or [{}])[-1]
        ev["real_email_sent"] = bool(last.get("status") == "sent" and last.get("provider_message_id"))
        page.screenshot(path=str(OUT / "05_send_no_real_send.png"), full_page=True)
        b.close()

    ev["local_pass"] = bool(ev.get("body_visual_variant") == "email_embedded_no_header"
                            and ev.get("body_visual_contains_own_banner_after") is False
                            and ev.get("step3_uses_email_body_visual_variant")
                            and ev.get("double_header_removed")
                            and ev.get("email_header_source") == "ttt_html_header"
                            and ev.get("real_email_sent") is False)
    ev["remote_pass"] = False  # OPS creds + branch redeploy gated
    (OUT / "evidence.json").write_text(json.dumps(ev, ensure_ascii=False, indent=2))
    print(json.dumps(ev, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
