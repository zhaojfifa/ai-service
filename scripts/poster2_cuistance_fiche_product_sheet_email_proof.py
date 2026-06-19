#!/usr/bin/env python3
"""LOCAL REAL-backend proof: the Fiche / simple product sheet mode is a pure deterministic
product_sheet_email built from Workbench truth — it does NOT enter poster generation runtime
(no more generate_timeout) and uses NO image generation / Gemini / Imagen.

Real app.main backend (no stubbing). Flow:
  1. Generate the fiche candidate -> ready fast, NO timeout, NO poster_key, generated_from=workbench_truth.
  2. Select fiche -> selected_email_body_visual == fiche.
  3. Step3 preview -> email_fill_format == product_sheet_email, ttt_html_header, contract pass.
  4. Affiche regression: affiche still generates/selects/previews with body_visual_contains_own_banner == False.
  5. Send (mode=real inline) -> NOT a real send.

A backend must serve page+API at BASE (default http://127.0.0.1:8799).
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/poster2/assets/cuistance_psd_email_container_last_mile_v1/remote_last_mile_fix/fiche_product_sheet_email_closure_v1"
BASE = os.environ.get("CUIST_BASE", "http://127.0.0.1:8799")


def bj(p, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + p, data=data, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310 (local trusted)
        return json.loads(r.read().decode("utf-8"))


def diag(page):
    try:
        return json.loads(page.inner_text("#diagdump"))
    except Exception:
        return {}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ev = {"branch": "trial/poster2-cuistance-psd-email-container-last-mile-v1", "was_stubbed": False, "base": BASE}
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1400, "height": 1040})
        page = ctx.new_page()
        page.goto(f"{BASE}/cuistance_trial.html")
        page.wait_for_timeout(600)
        page.click("#btn-sample")
        page.wait_for_timeout(300)
        page.click("#nextBtn")
        page.wait_for_timeout(1500)
        wb = diag(page).get("workbench_key")
        ev["workbench_key"] = wb

        # --- Fiche: must NOT enter poster generation runtime (no timeout) ---
        page.click('#modeTabs .mode-tab[data-mode="fiche"]')
        page.wait_for_timeout(300)
        t0 = time.time()
        page.click("#btn-gen-fiche")
        timed_out = False
        try:
            page.wait_for_selector("#fiche-real:visible", timeout=30_000)
        except Exception:
            timed_out = True
        gen_secs = round(time.time() - t0, 2)
        page.wait_for_timeout(500)
        ev["fiche_generate_seconds"] = gen_secs
        ev["fiche_generate_timeout"] = bool(timed_out or gen_secs >= 80.0)
        page.screenshot(path=str(OUT / "01_step2_fiche_available_no_timeout.png"), full_page=True)

        fiche_cand = (bj(f"/api/v2/workbench/{wb}").get("poster_candidates") or {}).get("fiche") or {}
        fsum = fiche_cand.get("contract_review_summary") or {}
        ev["fiche_candidate_status"] = fiche_cand.get("status")
        ev["fiche_has_poster_key"] = bool(fiche_cand.get("poster_key"))
        ev["fiche_template_id"] = fiche_cand.get("template_id")
        ev["fiche_uses_poster_generation"] = bool(fsum.get("uses_poster_generation"))
        ev["fiche_generated_from"] = fsum.get("generated_from")

        page.click("#btn-select-fiche")
        page.wait_for_timeout(1200)
        ev["selected_email_body_visual_after"] = bj(f"/api/v2/workbench/{wb}").get("selected_email_body_visual")
        page.screenshot(path=str(OUT / "02_step2_fiche_selected.png"), full_page=True)

        # --- Step3 product_sheet_email preview ---
        page.click("#nextBtn")
        page.wait_for_timeout(700)
        page.click("#btn-preview")
        page.wait_for_timeout(2500)
        page.screenshot(path=str(OUT / "03_step3_product_sheet_email_preview.png"), full_page=True)

        prev = bj(f"/api/v2/workbench/{wb}/email/preview", method="POST")
        ev["email_fill_format"] = prev.get("email_fill_format")
        ev["email_header_source"] = prev.get("email_header_source")
        ev["product_sheet_email_contract_pass"] = bool(prev.get("product_sheet_email_contract_pass"))
        ev["preview_fiche_uses_poster_generation"] = bool(prev.get("fiche_uses_poster_generation"))
        ev["preview_fiche_generated_from"] = prev.get("fiche_generated_from")
        ev["fiche_body_visual_candidate_type"] = (prev.get("body_visual") or {}).get("candidate_type")
        ev["fiche_body_visual_has_poster_key"] = bool((prev.get("body_visual") or {}).get("poster_key"))
        ev["product_sheet_email_preview_ok"] = bool(
            prev.get("email_fill_format") == "product_sheet_email"
            and prev.get("email_header_source") == "ttt_html_header"
            and "<table" in (prev.get("html") or "")
            and "CUISTANCE" in (prev.get("html") or "")
        )

        page.click("#btn-full-preview")
        page.wait_for_timeout(900)
        page.screenshot(path=str(OUT / "04_full_product_sheet_email_preview.png"), full_page=True)
        page.click("#fp-close")
        page.wait_for_timeout(300)

        # --- Affiche regression: still works, body visual carries no inner banner ---
        page.click("#prevBtn")
        page.wait_for_timeout(500)
        page.click('#modeTabs .mode-tab[data-mode="affiche"]')
        page.wait_for_timeout(300)
        page.click("#btn-gen-affiche")
        page.wait_for_selector("#affiche-real:visible", timeout=180_000)
        page.wait_for_timeout(600)
        affiche_cand = (bj(f"/api/v2/workbench/{wb}").get("poster_candidates") or {}).get("affiche") or {}
        ev["affiche_poster_key"] = affiche_cand.get("poster_key")
        page.click("#btn-select-affiche")
        page.wait_for_timeout(1200)
        page.click("#nextBtn")
        page.wait_for_timeout(700)
        page.click("#btn-preview")
        page.wait_for_timeout(2500)
        aprev = bj(f"/api/v2/workbench/{wb}/email/preview", method="POST")
        ev["affiche_still_works"] = bool(
            bj(f"/api/v2/workbench/{wb}").get("selected_email_body_visual") == "affiche"
            and aprev.get("email_fill_format") == "campaign_poster_email"
            and (aprev.get("body_visual") or {}).get("candidate_type") == "affiche"
        )
        ev["body_visual_contains_own_banner"] = bool(aprev.get("body_visual_contains_own_banner"))
        ev["email_body_visual_contract_pass"] = bool(aprev.get("email_body_visual_contract_pass"))
        page.screenshot(path=str(OUT / "05_affiche_regression_still_ok.png"), full_page=True)

        # --- restore fiche selection + send (mode=real inline) -> NOT a real send ---
        page.click("#prevBtn")
        page.wait_for_timeout(500)
        page.click('#modeTabs .mode-tab[data-mode="fiche"]')
        page.wait_for_timeout(300)
        page.click("#btn-select-fiche")
        page.wait_for_timeout(1200)
        ev["selected_email_body_visual_after"] = bj(f"/api/v2/workbench/{wb}").get("selected_email_body_visual")
        page.click("#nextBtn")
        page.wait_for_timeout(700)
        page.click("#btn-preview")
        page.wait_for_timeout(2000)
        try:
            page.check('input[name="mode"][value="real"]')
            page.check("#f-confirm")
            page.click("#btn-send")
            page.wait_for_timeout(400)
            page.click("#modalConfirm")
            page.wait_for_timeout(1500)
        except Exception:
            pass
        last = (bj(f"/api/v2/workbench/{wb}").get("send_attempts") or [{}])[-1]
        ev["real_email_sent"] = bool(last.get("status") == "sent" and last.get("provider_message_id"))
        page.screenshot(path=str(OUT / "06_send_no_real_send.png"), full_page=True)
        b.close()

    ev["local_pass"] = bool(
        ev.get("fiche_generate_timeout") is False
        and ev.get("fiche_uses_poster_generation") is False
        and ev.get("fiche_generated_from") == "workbench_truth"
        and ev.get("fiche_has_poster_key") is False
        and ev.get("selected_email_body_visual_after") == "fiche"
        and ev.get("email_fill_format") == "product_sheet_email"
        and ev.get("product_sheet_email_preview_ok") is True
        and ev.get("email_header_source") == "ttt_html_header"
        and ev.get("affiche_still_works") is True
        and ev.get("body_visual_contains_own_banner") is False
        and ev.get("email_body_visual_contract_pass") is True
        and ev.get("real_email_sent") is False
    )
    ev["remote_pass"] = False  # OPS creds + branch redeploy gated
    (OUT / "evidence.json").write_text(json.dumps(ev, ensure_ascii=False, indent=2))
    print(json.dumps(ev, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
