#!/usr/bin/env python3
"""Remote validation capture for the CUISTANCE PSD email container (REAL remote, honest gating).

Captures the reachable remote state of https://ai-service-leob.onrender.com/cuistance_trial.html and ATTEMPTS the
Step-1 save. The v2 workbench API is OPS-gated (POST /api/v2/workbench -> 401 ops_auth_required); without OPS
credentials the functional flow (save/generate/select/preview/send) cannot execute, so those steps are recorded as
NOT validated (HOLD) rather than fabricated. Produces real screenshots for what is reachable + honest 'blocked'
cards for the gated steps.

Usage: PYTHONPATH=. ./.venv/bin/python scripts/poster2_cuistance_psd_container_remote_validate.py
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/poster2/assets/cuistance_psd_email_container_last_mile_v1/remote_validation"
URL = "https://ai-service-leob.onrender.com/cuistance_trial.html"
API = "https://ai-service-leob.onrender.com"
FB = REPO / "assets/fonts/NotoSansSC-SemiBold.ttf"
FR = REPO / "assets/fonts/NotoSansSC-Regular.ttf"


def blocked_card(path: Path, title: str, lines: list[str]) -> None:
    im = Image.new("RGB", (1200, 360), (250, 244, 238))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 1200, 8], fill=(184, 134, 11))
    d.text((40, 40), title, font=ImageFont.truetype(str(FB), 30), fill=(122, 95, 6))
    y = 110
    for ln in lines:
        d.text((40, y), ln, font=ImageFont.truetype(str(FR), 20), fill=(60, 60, 60)); y += 38
    im.save(path)


def get_json(path: str) -> dict:
    try:
        with urllib.request.urlopen(API + path, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)[:80]}


def post_status(path: str, body: dict) -> int:
    req = urllib.request.Request(API + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:  # type: ignore
        return e.code
    except Exception:
        return 0


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ev = {
        "remote_url": URL,
        "branch": "trial/poster2-cuistance-psd-email-container-last-mile-v1",
        "expected_commit": "9aee266",
        "deployed_commit_observed": "",
        "step1_assets_saved": False,
        "step2_affiche_generated": False,
        "selected_visual_confirmed": False,
        "step3_psd_container_preview_ok": False,
        "refresh_recovery_ok": False,
        "legacy_truth_leakage": False,
        "real_email_sent": False,
        "known_issue_header_logo_fit": True,
        "remote_pass": False,
    }

    # backend probes (no auth)
    me = get_json("/api/auth/me")
    wb_status = post_status("/api/v2/workbench", {"language": "zh"})
    ev["auth_me"] = me
    ev["workbench_create_status_no_auth"] = wb_status
    ev["api_ops_gated"] = (wb_status == 401)

    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": 1400, "height": 1040})
        page.goto(URL, timeout=60000)
        page.wait_for_timeout(1500)
        # detect deployed frontend version via the PSD-container marker
        content = page.content()
        ev["frontend_psd_container_marker_present"] = ("email_container_template_id" in content)
        ev["frontend_asset_chain_marker_present"] = ("素材就绪检查" in content) or ("header_band" in content)
        ev["deployed_commit_observed"] = (
            "unknown (no version endpoint); frontend includes email_container_template_id marker (>= Phase 2 ebdfea7)"
            if ev["frontend_psd_container_marker_present"] else
            "unknown (no version endpoint); PSD-container marker ABSENT in deployed frontend"
        )
        page.screenshot(path=str(OUT / "01_remote_version.png"), full_page=True)

        # attempt Step 1 (use sample + save) -> OPS-gated -> business flash 请先连接后端
        try:
            page.click("#btn-sample"); page.wait_for_timeout(500)
            page.click("#nextBtn"); page.wait_for_timeout(2500)
            ev["step1_save_flash"] = page.inner_text("#flash")
        except Exception as e:
            ev["step1_save_flash"] = f"(no flash: {str(e)[:60]})"
        page.screenshot(path=str(OUT / "02_remote_step1_saved.png"), full_page=True)
        # open diagnostics to record what the page knows (auth/me)
        try:
            page.click("#diagBtn"); page.wait_for_timeout(400)
            ev["diag_excerpt"] = page.inner_text("#diagdump")[:600]
        except Exception:
            pass
        b.close()

    # gated steps -> honest 'blocked' cards (NOT validated; no OPS credentials)
    blocked_lines = [
        "Remote v2 workbench API is OPS-gated: POST /api/v2/workbench -> 401 ops_auth_required.",
        "No OPS credentials were provided this pass, so this step could NOT be validated remotely.",
        "Status recorded as NOT validated (HOLD). No fabrication.",
    ]
    blocked_card(OUT / "03_remote_step2_generated.png", "Step 2 — Affiche generation: BLOCKED (OPS login required)", blocked_lines)
    blocked_card(OUT / "04_remote_selected_visual.png", "Selected visual confirm: BLOCKED (OPS login required)", blocked_lines)
    blocked_card(OUT / "05_remote_step3_psd_preview.png", "Step 3 — PSD email container preview: BLOCKED (OPS login required)", blocked_lines)
    blocked_card(OUT / "06_remote_refresh_recovery.png", "Refresh recovery: BLOCKED (OPS login required)", blocked_lines)
    blocked_card(OUT / "07_remote_send_no_real_send.png", "Send semantics: NOT RUN (no real email; OPS login required)", blocked_lines)

    ev["hold_reason"] = ("Remote v2 API is OPS-gated (401 ops_auth_required) and no OPS credentials were provided; "
                         "Step1 save -> Step3 preview -> send could not be executed remotely. The PSD-container "
                         "frontend IS deployed (marker present). Local REAL-backend validation already PASSED "
                         "(see evidence.json). remote_pass=false (HOLD).")
    (OUT / "remote_evidence.json").write_text(json.dumps(ev, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in ev.items() if k != "diag_excerpt"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
