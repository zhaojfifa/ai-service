#!/usr/bin/env python3
"""Browser screenshot proof for the CUISTANCE v1 operator-UI candidate-selection / preview state fix.

Serves the REAL frontend/cuistance_trial.html statically and drives it with Playwright/Chromium while
stubbing the existing v1 backend endpoints. The stub faithfully reproduces the Owner-observed backend state:
a product poster (affiche) candidate is already status=ready with a poster_key, while
selected_email_body_visual starts null — and candidate generation can return a gateway 504 timeout even though
the ready candidate exists. This proves the UI fix WITHOUT needing the renderer / auth / image-gen.

No backend code is exercised here; it only validates the frontend state machine + screenshots.

Usage: PYTHONPATH=. ./.venv/bin/python scripts/poster2_cuistance_ui_candidate_selection_proof.py
"""
from __future__ import annotations

import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
FRONTEND = REPO / "frontend"
OUT = REPO / "docs/poster2/assets/cuistance_ui_candidate_selection_state_fix_v1"
OUT.mkdir(parents=True, exist_ok=True)
PORT = 8791

WB_KEY = "wb_af43f59a05944611"
POSTER_KEY = "p2_2b0c5b002c59455d"
TEMPLATE_ID = "email_campaign_composite_v1"

# server-side workbench record reflecting the Owner-observed state (affiche ready, selection starts null)
STATE = {"selected_email_body_visual": None}


def record() -> dict:
    return {
        "workbench_key": WB_KEY,
        "language": "zh",
        "status": "draft",
        "product_truth": {"product_name": "Friteuse électrique double", "reference": "EF132V"},
        "product_assets": {"product_images": [{"url": "x"}, {"url": "y"}], "gallery_images": [{"url": "g"}]},
        "email_banner": {"channel_name": "CUISTANCE Europe", "campaign_label": "Nouveauté"},
        "poster_candidates": {
            # Owner-observed: affiche already generated and ready
            "affiche": {"status": "ready", "poster_key": POSTER_KEY, "template_id": TEMPLATE_ID,
                         "contract_review_summary": {"render_engine_used": "chromium", "degraded": False,
                                                     "structure_complete": True}},
        },
        "selected_email_body_visual": STATE["selected_email_body_visual"],
        "send_attempts": [],
    }


def serve_frontend() -> ThreadingHTTPServer:
    handler = lambda *a, **k: SimpleHTTPRequestHandler(*a, directory=str(FRONTEND), **k)  # noqa: E731
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main() -> None:
    httpd = serve_frontend()
    generate_calls = {"affiche": 0}
    evidence: dict = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1380, "height": 1000})

            def route_api(route):
                req = route.request
                url = req.url
                method = req.method
                path = url.split(str(PORT))[-1].split("?")[0] if str(PORT) in url else url

                def ok(body):
                    route.fulfill(status=200, content_type="application/json", body=json.dumps(body))

                if path == "/api/auth/me":
                    return ok({"authenticated": True, "enabled": True})
                if path == "/api/auth/ops-login":
                    return ok({"ok": True, "authenticated": True})
                if path == "/api/v2/workbench" and method == "POST":
                    return ok(record())
                if path.endswith("/selected-visual") and method == "PATCH":
                    data = json.loads(req.post_data or "{}")
                    STATE["selected_email_body_visual"] = data.get("selected_email_body_visual")
                    return ok(record())
                if "/candidates/affiche/generate" in path:
                    generate_calls["affiche"] += 1
                    # Reproduce the Owner-observed confusing case: gateway 504 timeout even though the
                    # backend already holds a ready affiche candidate.
                    return route.fulfill(status=504, content_type="application/json",
                                         body=json.dumps({"detail": "gateway_timeout"}))
                if "/candidates/fiche/generate" in path:
                    return route.fulfill(status=422, content_type="application/json",
                                         body=json.dumps({"detail": "fiche_unavailable",
                                                          "failure": {"detail": "image_gen_unavailable"}}))
                if path.startswith("/api/v2/workbench/") and path.endswith("/email/preview"):
                    html = ("<html><body style='font-family:sans-serif;margin:0'>"
                            "<div style='background:#0f2a4a;color:#fff;padding:14px'>CUISTANCE Europe · Nouveauté</div>"
                            "<div style='padding:16px'><h2>LES FRITEUSES ÉLECTRIQUES</h2>"
                            "<p>Cuisson professionnelle, croustillant maîtrisé</p>"
                            "<div style='border:1px solid #ccc;padding:10px'>RÉF. EF132V · 2 cuves 13 + 13 L · 3 + 3 kW / 230 V</div>"
                            "<p><a href='#'>Nous contacter</a></p></div>"
                            "<div style='padding:10px;color:#666;font-size:12px'>commercial@cuistance.eu · Se désabonner</div>"
                            "</body></html>")
                    return ok({"html": html,
                               "email_body_plan": {"layout_type": "single_product_promo", "container_width": 600},
                               "selected_email_body_visual": STATE["selected_email_body_visual"]})
                if path.startswith("/api/v2/workbench/") and method in ("GET", "PATCH"):
                    return ok(record())
                return ok({})

            page.route("**/api/**", route_api)

            page.goto(f"http://127.0.0.1:{PORT}/cuistance_trial.html")
            page.wait_for_timeout(500)

            # ---- Step 1: use sample assets, capture asset-readiness panel ----
            page.click("#btn-sample")
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT / "01_step1_asset_readiness.png"), full_page=True)
            evidence["step1_ready_badge"] = page.inner_text("#s1-ready")
            evidence["readiness_rows"] = {
                rid: page.inner_text(f"#rb-{rid}")
                for rid in ("prod1", "prod2", "gallery", "atmo", "logo", "banner")
            }

            # save -> advance to Step 2 (ensureWorkbench creates wb + refreshState reads ready affiche)
            page.click("#nextBtn")
            page.wait_for_timeout(700)

            # ---- Step 2 before selection: affiche shows backend-ready (Owner scenario) ----
            evidence["affiche_card_badge"] = page.inner_text("#affiche-card-badge")
            page.screenshot(path=str(OUT / "02_step2_before_select.png"), full_page=True)

            # exercise the timeout path: regenerate -> 504 -> ready candidate retained, business message shown
            page.click("#btn-regen-affiche")
            page.wait_for_timeout(600)
            evidence["after_regen_flash"] = page.inner_text("#flash")
            evidence["after_regen_affiche_badge"] = page.inner_text("#affiche-card-badge")
            page.screenshot(path=str(OUT / "02b_step2_timeout_retained.png"), full_page=True)

            # ---- Select the product poster as the email body ----
            page.click("#btn-select-affiche")
            page.wait_for_timeout(600)
            evidence["selected_email_body_visual_after_patch"] = STATE["selected_email_body_visual"]
            evidence["next_btn_disabled_after_select"] = page.eval_on_selector("#nextBtn", "el => el.disabled")
            evidence["affiche_select_btn_label"] = page.inner_text("#btn-select-affiche")
            page.screenshot(path=str(OUT / "03_step2_after_select.png"), full_page=True)

            # ---- Step 3: continue + email preview ----
            page.click("#nextBtn")
            page.wait_for_timeout(500)
            page.click("#btn-preview")
            page.wait_for_timeout(800)
            evidence["step3_active"] = page.eval_on_selector("#screen-3", "el => el.classList.contains('active')")
            evidence["send_summary"] = page.inner_text("#send-summary")
            page.screenshot(path=str(OUT / "04_step3_email_preview.png"), full_page=True)

            # ---- Diagnostics evidence (engineering fields live here, not on main UI) ----
            page.click("#diagBtn")
            page.wait_for_timeout(300)
            evidence["diag_dump"] = page.inner_text("#diagdump")
            page.screenshot(path=str(OUT / "05_diagnostics_evidence.png"), full_page=True)

            browser.close()
    finally:
        httpd.shutdown()

    evidence["generate_calls"] = generate_calls
    (OUT / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    print("\nScreenshots ->", OUT)


if __name__ == "__main__":
    main()
