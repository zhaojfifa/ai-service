#!/usr/bin/env python3
"""REAL (non-stubbed) browser proof for CUISTANCE v1 email preview/send semantics calibration.

Drives the REAL frontend/cuistance_trial.html against a REAL running backend (app.main) — NO route stubbing.
Verifies: explicit email-banner selection; the generated poster's view/copy URL actions; Step-3 preview rendered
from the backend email/preview and clearly bound to the selected generated poster; and honest send semantics
(inline_only/preview_only must NOT read as a real send — only a provider_message_id counts as real). Captures
screenshots + evidence.json with was_stubbed=false.

A backend must already serve page+API at BASE (default http://127.0.0.1:8799).
  PYTHONPATH=. ./.venv/bin/python scripts/poster2_cuistance_email_preview_send_semantics_proof.py
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/poster2/assets/cuistance_email_preview_send_semantics_v1"
OUT.mkdir(parents=True, exist_ok=True)
BASE = os.environ.get("CUIST_BASE", "http://127.0.0.1:8799")
FORBIDDEN_SUCCESS = ["发送成功", "真实发送成功", "已发送"]  # must NOT appear for inline_only/preview_only


def backend_json(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=30) as r:  # noqa: S310 (local trusted)
        return json.loads(r.read().decode("utf-8"))


def main() -> None:
    statuses: dict = {}
    evidence: dict = {"was_stubbed": False, "base_url": BASE}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1380, "height": 1000})

        def on_response(resp):
            if "/email/preview" in resp.url:
                statuses["preview"] = resp.status
            elif "/email/send" in resp.url:
                statuses["send"] = resp.status
        page.on("response", on_response)

        page.goto(f"{BASE}/cuistance_trial.html")
        page.wait_for_timeout(600)

        # ---- Step 1: explicit banner option + sample assets ----
        page.click("#btn-sample")                         # fills product/gallery/logo + selects banner Option 1
        page.wait_for_timeout(200)
        page.click('#s1-bannerOptions .banner-opt[data-ref="option_2"]')   # explicit banner choice
        page.wait_for_timeout(200)
        evidence["banner_hint"] = page.inner_text("#s1-banner-hint")
        page.screenshot(path=str(OUT / "01_step1_banner_option_selected.png"), full_page=True)

        # save -> Step 2
        page.click("#nextBtn")
        page.wait_for_timeout(1500)

        # ---- Step 2: generate real poster + view/copy actions ----
        page.click("#btn-gen-affiche")
        page.wait_for_selector("#affiche-real:visible", timeout=180_000)
        page.wait_for_timeout(800)
        evidence["ui_has_open_generated_image_action"] = page.eval_on_selector(
            "#affiche-actions", "el => getComputedStyle(el).display !== 'none'")
        open_href = page.get_attribute("#affiche-open", "href") or ""
        evidence["open_action_href_is_poster"] = open_href.startswith("data:") or open_href.startswith("http")
        page.screenshot(path=str(OUT / "02_step2_generated_poster_with_open_link.png"), full_page=True)

        # authoritative backend truth
        diag = json.loads(page.inner_text("#diagdump"))
        wb_key = diag.get("workbench_key")
        wb = backend_json(f"/api/v2/workbench/{wb_key}")
        banner = wb.get("email_banner") or {}
        affiche = (wb.get("poster_candidates") or {}).get("affiche") or {}
        poster_key = affiche.get("poster_key")
        rec = backend_json(f"/api/v2/posters/{poster_key}") if poster_key else {}
        fp_url = (rec.get("final_poster") or {}).get("url") or ""

        # ---- select the poster as the email body, confirm from backend GET ----
        page.click("#btn-select-affiche")
        page.wait_for_timeout(1500)
        wb2 = backend_json(f"/api/v2/workbench/{wb_key}")
        evidence["selected_email_body_visual_after_get"] = wb2.get("selected_email_body_visual")

        # ---- Step 3: preview from backend, bound to the selected generated poster ----
        page.click("#nextBtn")
        page.wait_for_timeout(700)
        page.click("#btn-preview")
        page.wait_for_timeout(2500)
        prev = backend_json  # noqa (unused alias kept for clarity)
        evidence["email_preview_status"] = statuses.get("preview")
        evidence["preview_badge"] = page.inner_text("#email-preview-badge")
        evidence["preview_body_binding"] = page.inner_text("#email-body-binding")
        # preview body_visual.poster_key matches selected generated poster (read from diagnostics dump)
        diag2 = json.loads(page.inner_text("#diagdump"))
        prev_diag = diag2.get("preview_diag") or {}
        evidence["preview_uses_body_visual_poster_key"] = bool(
            prev_diag.get("body_visual_poster_key") and prev_diag.get("body_visual_poster_key") == poster_key)
        evidence["final_poster_url_present"] = bool(fp_url) and bool(prev_diag.get("final_poster_url_present"))
        page.screenshot(path=str(OUT / "03_step3_preview_uses_generated_poster.png"), full_page=True)

        # ---- send: mode=real but inline_only provider -> must NOT read as real sent ----
        page.check('input[name="mode"][value="real"]')
        page.check("#f-confirm")
        page.click("#btn-send")
        page.wait_for_timeout(400)
        page.click("#modalConfirm")
        page.wait_for_timeout(1500)
        send = backend_json(f"/api/v2/workbench/{wb_key}")
        attempts = send.get("send_attempts") or []
        last = attempts[-1] if attempts else {}
        send_summary = page.inner_text("#send-summary")
        evidence.update({
            "workbench_key": wb_key,
            "selected_banner_ref": banner.get("selected_banner_ref"),
            "banner_background_url_present": bool((banner.get("background") or {}).get("url")),
            "poster_key": poster_key,
            "send_mode": last.get("mode"),
            "send_provider": last.get("provider"),
            "provider_message_id_present": bool(last.get("provider_message_id")),
            "send_status": last.get("status"),
            "send_error_code": last.get("error_code"),
            "real_email_sent": bool(last.get("status") == "sent" and last.get("provider_message_id")),
            "send_summary_text": send_summary,
            "ui_send_label_correct": (not any(s in send_summary for s in FORBIDDEN_SUCCESS))
                                      and ("未真实投递" in send_summary or "preuve" in send_summary.lower()),
        })
        page.screenshot(path=str(OUT / "04_send_preview_only_not_real_sent.png"), full_page=True)

        page.click("#diagBtn")
        page.wait_for_timeout(400)
        evidence["diag_excerpt"] = page.inner_text("#diagdump")[:1200]
        page.screenshot(path=str(OUT / "05_diagnostics_email_preview_send_evidence.png"), full_page=True)

        browser.close()

    (OUT / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
    printable = {k: v for k, v in evidence.items() if k != "diag_excerpt"}
    print(json.dumps(printable, ensure_ascii=False, indent=2))
    print("\nScreenshots ->", OUT)


if __name__ == "__main__":
    main()
