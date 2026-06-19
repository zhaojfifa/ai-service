#!/usr/bin/env python3
"""REAL (non-stubbed) browser proof for the CUISTANCE v1 real-poster-binding + selection fix.

Drives the REAL frontend/cuistance_trial.html against a REAL running backend (app.main) — NO Playwright route
stubbing. The backend performs a real chromium composite render (template_id=email_campaign_composite_v1) and
persists a poster_record whose final_poster.url is the actual generated poster (a data: URL when R2 is not
configured). The UI must fetch GET /api/v2/posters/{poster_key} and bind that final_poster.url into the Step-2
card — never a static mock. Captures screenshots + evidence.json with was_stubbed=false.

Usage: a backend must already be serving the page+API at BASE_URL (default http://127.0.0.1:8799).
  PYTHONPATH=. ./.venv/bin/python scripts/poster2_cuistance_real_poster_binding_proof.py
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/poster2/assets/cuistance_real_poster_binding_selection_fix_v1"
OUT.mkdir(parents=True, exist_ok=True)
BASE = os.environ.get("CUIST_BASE", "http://127.0.0.1:8799")


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
            u = resp.url
            if "/candidates/affiche/generate" in u:
                statuses["generate"] = resp.status
            elif u.endswith("/email/preview"):
                statuses["preview"] = resp.status
        page.on("response", on_response)

        page.goto(f"{BASE}/cuistance_trial.html")
        page.wait_for_timeout(600)

        # Step 1: sample assets -> save -> enter Step 2
        page.click("#btn-sample")
        page.wait_for_timeout(300)
        page.click("#nextBtn")
        page.wait_for_timeout(1500)  # ensureWorkbench + refreshState

        # Screenshot 01: Step 2 BEFORE generation — static card must be labeled 预览示意，尚未生成
        evidence["placeholder_label"] = page.inner_text("#affiche-preview-label")
        evidence["placeholder_badge"] = page.inner_text("#affiche-card-badge")
        page.screenshot(path=str(OUT / "01_step2_before_generation_placeholder_labeled.png"), full_page=True)

        # Generate the REAL poster (real chromium render ~30s)
        page.click("#btn-gen-affiche")
        # wait until the real backend poster image is bound + visible (data: URL)
        page.wait_for_selector("#affiche-real:visible", timeout=180_000)
        page.wait_for_timeout(800)
        real_src = page.get_attribute("#affiche-real", "src") or ""
        evidence["affiche_card_badge_after_gen"] = page.inner_text("#affiche-card-badge")
        evidence["mock_hidden_after_gen"] = page.eval_on_selector(
            "#affiche-mock", "el => getComputedStyle(el).display === 'none'")
        page.screenshot(path=str(OUT / "02_step2_real_backend_poster_loaded.png"), full_page=True)

        # Pull authoritative backend truth (real endpoints, not the UI)
        diag = json.loads(page.inner_text("#diagdump"))
        wb_key = diag.get("workbench_key")
        wb = backend_json(f"/api/v2/workbench/{wb_key}")
        affiche = (wb.get("poster_candidates") or {}).get("affiche") or {}
        poster_key = affiche.get("poster_key")
        rec = backend_json(f"/api/v2/posters/{poster_key}") if poster_key else {}
        fp = rec.get("final_poster") or {}
        fp_url = fp.get("url") or ""
        rr = rec.get("render_result") or {}

        evidence.update({
            "workbench_key": wb_key,
            "generate_http_status": statuses.get("generate"),
            "affiche_status": affiche.get("status"),
            "poster_key": poster_key,
            "template_id": affiche.get("template_id") or rec.get("template_id"),
            "poster_record_loaded": bool(rec),
            "final_poster_url_present": bool(fp_url),
            "final_poster_url_origin": (
                "poster_record.final_poster.url=" + (fp_url[:48] + "…(len=%d)" % len(fp_url) if fp_url else "")),
            "render_engine_used": rr.get("render_engine_used"),
            "degraded": rr.get("degraded"),
            "structure_complete": rr.get("structure_complete"),
            "final_poster_width": fp.get("width"),
            "final_poster_height": fp.get("height"),
        })
        # UI bound to the SAME real poster? (both data: URLs; compare prefix + length)
        evidence["ui_image_bound_to_final_poster"] = bool(
            real_src and fp_url and real_src[:64] == fp_url[:64] and len(real_src) == len(fp_url))

        # Select the backend poster as the email body
        page.click("#btn-select-affiche")
        page.wait_for_timeout(1500)
        wb2 = backend_json(f"/api/v2/workbench/{wb_key}")
        evidence["selected_email_body_visual"] = wb2.get("selected_email_body_visual")
        evidence["select_btn_label"] = page.inner_text("#btn-select-affiche")
        evidence["next_btn_disabled_after_select"] = page.eval_on_selector("#nextBtn", "el => el.disabled")
        page.screenshot(path=str(OUT / "03_step2_selected_backend_poster.png"), full_page=True)

        # Step 3: continue + preview
        page.click("#nextBtn")
        page.wait_for_timeout(800)
        evidence["step3_active"] = page.eval_on_selector("#screen-3", "el => el.classList.contains('active')")
        evidence["step3_unlocked"] = bool(evidence["step3_active"]) and not evidence["next_btn_disabled_after_select"]
        page.click("#btn-preview")
        page.wait_for_timeout(2500)
        evidence["preview_status"] = statuses.get("preview")
        page.screenshot(path=str(OUT / "04_step3_email_preview_with_backend_poster.png"), full_page=True)

        # Diagnostics evidence (engineering fields only here, not on main UI)
        page.click("#diagBtn")
        page.wait_for_timeout(400)
        evidence["diag_dump_excerpt"] = page.inner_text("#diagdump")[:1200]
        page.screenshot(path=str(OUT / "05_diagnostics_real_poster_binding_evidence.png"), full_page=True)

        browser.close()

    (OUT / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
    printable = {k: v for k, v in evidence.items() if k not in ("diag_dump_excerpt",)}
    print(json.dumps(printable, ensure_ascii=False, indent=2))
    print("\nScreenshots ->", OUT)


if __name__ == "__main__":
    main()
