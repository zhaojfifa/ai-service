#!/usr/bin/env python3
"""Focused remote diagnostic: authenticated /email/preview response shape at 141c612 (no screenshots).

Logs in via the page (cookie), then runs create->patch->generate->select->preview via the page's authenticated
fetch and prints the preview HTTP status + key response fields (email_header_source / html present / detail).
Creds from /tmp/cuistance_ops_auth/creds.env (never printed). Uses a fresh workbench.
"""
from __future__ import annotations

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://ai-service-leob.onrender.com/cuistance_trial.html"
SAMPLE = {
    "prod1": "https://mcusercontent.com/43cb582d3a744559eaf77eab0/images/15545c0b-96a8-fbf3-e83c-bb9d69c44d7a.jpg",
    "prod2": "https://mcusercontent.com/43cb582d3a744559eaf77eab0/images/da42d592-d955-23d6-9560-a7a501b2bb24.jpg",
    "logo": "https://mcusercontent.com/43cb582d3a744559eaf77eab0/images/0a50184e-bee5-bf53-0c1b-45fb63855e78.png",
}


def creds():
    u = pw = None
    for ln in Path("/tmp/cuistance_ops_auth/creds.env").read_text().splitlines():
        if ln.startswith("CUISTANCE_OPS_USER="): u = ln.split("=", 1)[1]
        if ln.startswith("CUISTANCE_OPS_PASSWORD="): pw = ln.split("=", 1)[1]
    return u, pw


def main():
    u, pw = creds()
    with sync_playwright() as p:
        b = p.chromium.launch(); page = b.new_page()
        page.goto(URL, timeout=60000); page.wait_for_timeout(1000)
        page.fill("#opsuser", u); page.fill("#opspass", pw); page.click("#btn-connect"); page.wait_for_timeout(2500)

        def api(m, path, body=None):
            return page.evaluate(
                """async ({m,p,b})=>{const o={method:m,headers:{'Content-Type':'application/json'},credentials:'include'};if(b!==null)o.body=JSON.stringify(b);const r=await fetch(p,o);let t=await r.text();let j=null;try{j=JSON.parse(t)}catch(e){};return{status:r.status,json:j,text:t.slice(0,400)}}""",
                {"m": m, "p": path, "b": body})

        me = api("GET", "/api/auth/me")
        print("auth_me:", me["json"])
        wb = api("POST", "/api/v2/workbench", {"language": "zh"})["json"]["workbench_key"]
        print("wb:", wb)
        api("PATCH", "/api/v2/workbench/" + wb, {"product_truth": {"product_name": "Friteuse", "reference": "EF132V"},
            "product_assets": {"product_images": [{"url": SAMPLE["prod1"]}, {"url": SAMPLE["prod2"]}], "gallery_images": [{"url": SAMPLE["prod2"]}]},
            "email_banner": {"logo": {"url": SAMPLE["logo"]}, "channel_name": "CUISTANCE Europe", "campaign_label": "Nouveauté", "selected_banner_ref": "option_1"}})
        gen = api("POST", "/api/v2/workbench/" + wb + "/candidates/affiche/generate", None)
        print("generate status:", gen["status"], "| affiche:", ((gen.get("json") or {}).get("poster_candidates") or {}).get("affiche", {}) if gen.get("json") else gen["text"])
        sel = api("PATCH", "/api/v2/workbench/" + wb + "/selected-visual", {"selected_email_body_visual": "affiche"})
        print("select status:", sel["status"], "selected:", (sel.get("json") or {}).get("selected_email_body_visual"))
        prev = api("POST", "/api/v2/workbench/" + wb + "/email/preview", None)
        pj = prev.get("json") or {}
        print("PREVIEW status:", prev["status"])
        if prev["status"] == 200:
            print("  email_header_source:", pj.get("email_header_source"))
            print("  email_container_template_id:", pj.get("email_container_template_id"))
            print("  html_present:", bool(pj.get("html")), "len:", len(pj.get("html") or ""))
            print("  body_visual.poster_key:", (pj.get("body_visual") or {}).get("poster_key"))
            ec = pj.get("email_container") or {}
            print("  email_container keys:", sorted(ec.keys()))
        else:
            print("  PREVIEW ERROR body:", prev["text"])
        # send semantics check (mode=real, inline_only -> must be preview_only / not real sent; internal recipient)
        snd = api("POST", "/api/v2/workbench/" + wb + "/email/send",
                  {"recipients": ["owner-internal-test@cuistance.eu"], "mode": "real", "confirm_send": True, "delivery_mode": "inline_only"})
        sj = snd.get("json") or {}
        att = (sj.get("attempts") or [{}])[-1] if sj.get("attempts") else {}
        print("SEND status:", snd["status"], "| attempt:", json.dumps({k: att.get(k) for k in ("status", "provider", "error_code", "provider_message_id")}, ensure_ascii=False))
        print("  real_email_sent:", bool(att.get("status") == "sent" and att.get("provider_message_id")))
        b.close()


if __name__ == "__main__":
    main()
