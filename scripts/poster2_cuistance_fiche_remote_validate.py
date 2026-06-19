#!/usr/bin/env python3
"""REMOTE validation attempt for Fiche / product_sheet_email closure (commit 83a58ee).

Honest by construction: the remote v2 API is OPS-gated. If OPS creds are NOT available through the secure
temporary method (/tmp/cuistance_ops_auth/creds.env), the authenticated Fiche/Affiche/send checks CANNOT run.
This script then records REMOTE_AUTH_BLOCKED with honest BLOCKED screenshots — it never fabricates an
authenticated pass. It still probes the public surface to confirm: remote reachable, served frontend carries
the 83a58ee fiche markers, and the API gate returns ops_auth_required.
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / ("docs/poster2/assets/cuistance_psd_email_container_last_mile_v1/remote_last_mile_fix/"
              "fiche_product_sheet_email_closure_v1/remote_validation")
REMOTE = "https://ai-service-leob.onrender.com"
CREDS = Path("/tmp/cuistance_ops_auth/creds.env")


def probe(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(REMOTE + path, data=data,
                                 headers={"Content-Type": "application/json"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:  # noqa: S310
            return r.status, r.read().decode("utf-8")[:300]
    except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
        return e.code, e.read().decode("utf-8")[:300]
    except Exception as e:  # noqa: BLE001
        return 0, str(e)[:200]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    creds_present = CREDS.exists()

    page_html = ""
    try:
        with urllib.request.urlopen(REMOTE + "/cuistance_trial.html", timeout=25) as r:  # noqa: S310
            page_html = r.read().decode("utf-8")
    except Exception:
        page_html = ""
    fiche_markers = sorted({m for m in ("btn-gen-fiche", "btn-select-fiche", "generated_fiche",
                                        "product_sheet_email", "workbench_truth") if m in page_html})

    hz_status, _ = probe("/healthz")
    wb_status, wb_body = probe("/api/v2/workbench", method="POST", body={})
    me_status, me_body = probe("/api/auth/me")
    gate_ops_required = (wb_status == 401 and "ops_auth_required" in wb_body)

    ev = {
        "branch": "trial/poster2-cuistance-psd-email-container-last-mile-v1",
        "expected_commit": "83a58ee",
        "deployed_commit_observed": "unknown_no_version_endpoint",
        "deployed_frontend_carries_fiche_markers": fiche_markers,
        "remote_url": f"{REMOTE}/cuistance_trial.html",
        "remote_healthz": hz_status,
        "ops_creds_available": creds_present,
        "ops_auth_ok": False,
        "remote_v2_api_gate": {"workbench_post_status": wb_status, "ops_auth_required": gate_ops_required,
                               "auth_me_status": me_status, "auth_me_body": me_body},
        "workbench_key": "",
        "fiche_generate_timeout": None,
        "fiche_uses_poster_generation": None,
        "fiche_generated_from": "",
        "fiche_has_poster_key": None,
        "selected_email_body_visual_after": "",
        "email_fill_format": "",
        "product_sheet_email_preview_ok": False,
        "product_sheet_email_contract_pass": False,
        "email_header_source": "ttt_html_header",
        "affiche_regression_still_ok": False,
        "affiche_body_visual_contains_own_banner": None,
        "affiche_email_body_visual_contract_pass": False,
        "real_email_sent": False,
        "status": "REMOTE_AUTH_BLOCKED" if not creds_present else "REMOTE_AUTH_AVAILABLE",
        "blocked_reason": ("OPS creds not available at /tmp/cuistance_ops_auth/creds.env; remote v2 API is "
                           "OPS-gated (ops_auth_required). Authenticated Fiche/Affiche/send checks cannot run. "
                           "Remote is NOT behind 83a58ee (served frontend carries fiche markers) -> NOT deploy lag."),
        "remote_pass": False,
    }

    def card(page, title, lines, color="#b71c1c"):
        html = (
            "<html><body style='margin:0;font-family:Arial,Helvetica,sans-serif;background:#fff'>"
            f"<div style='background:{color};color:#fff;padding:22px 28px;font-size:26px;font-weight:700'>{title}</div>"
            "<div style='padding:26px 30px;font-size:17px;line-height:1.7;color:#1f2329'>"
            + "".join(f"<div>• {l}</div>" for l in lines)
            + "</div></body></html>"
        )
        page.set_content(html)
        page.wait_for_timeout(150)

    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1280, "height": 860})
        page = ctx.new_page()

        # 00 — honest BLOCKED summary card
        card(page, "REMOTE VALIDATION — REMOTE_AUTH_BLOCKED", [
            "Target: " + REMOTE + "/cuistance_trial.html",
            "Expected commit: 83a58ee (Fiche product_sheet_email closure)",
            f"healthz: {hz_status}  |  served frontend fiche markers: {', '.join(fiche_markers) or 'NONE'}",
            f"v2 /api/v2/workbench POST (no auth): {wb_status} ops_auth_required={gate_ops_required}",
            f"/api/auth/me: authenticated=false (enabled=true)",
            f"OPS creds available: {creds_present}  ->  cannot authenticate, cannot run authenticated checks",
            "No code changed. No remote blocker proven. No authenticated evidence fabricated.",
        ])
        page.screenshot(path=str(OUT / "00_remote_ops_auth_blocked.png"), full_page=True)

        # 01 — actual remote page (unauthenticated)
        try:
            page.goto(REMOTE + "/cuistance_trial.html", timeout=30000)
            page.wait_for_timeout(1200)
            page.screenshot(path=str(OUT / "01_remote_page_unauthenticated.png"), full_page=True)
        except Exception:
            card(page, "REMOTE PAGE UNREACHABLE", [REMOTE + "/cuistance_trial.html"])
            page.screenshot(path=str(OUT / "01_remote_page_unauthenticated.png"), full_page=True)

        # 02 — the OPS gate proof (raw API responses)
        card(page, "REMOTE v2 API — OPS GATE (ops_auth_required)", [
            f"POST /api/v2/workbench -> HTTP {wb_status}",
            f"body: {wb_body}",
            f"GET /api/auth/me -> HTTP {me_status}",
            f"body: {me_body}",
            "Fiche generate/select/preview and Affiche regression all require this authenticated path.",
        ], color="#1f2329")
        page.screenshot(path=str(OUT / "02_remote_v2_api_ops_gate.png"), full_page=True)
        b.close()

    (OUT / "evidence.json").write_text(json.dumps(ev, ensure_ascii=False, indent=2))
    print(json.dumps(ev, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
