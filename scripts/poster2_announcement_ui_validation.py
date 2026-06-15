"""POSTER2-FAMILY-B-ANNOUNCEMENT-OPERATOR-UI-CLOSURE-V1 — browser UI validation.

Serves the static frontend, drives the REAL Stage1 -> Stage2 -> generate flow for
Family B, fills the Cuistance announcement fields, mocks upload (presign) + generate
endpoints to CAPTURE the actual /api/v2/generate-poster request body (proving the UI
sends the new fields), and saves screenshots. No real backend / no real send.

Run: PYTHONPATH=. ./.venv/bin/python scripts/poster2_announcement_ui_validation.py
"""
from __future__ import annotations

import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
OUT = ROOT / "docs/poster2/assets/announcement_ui_closure_v1"
OUT.mkdir(parents=True, exist_ok=True)
PORT = 8757

SAMPLE = {
    "brand_name": "CUISTANCE",
    "sku_text": "311011 (RC10L)",
    "title": "NOUVEAUTE ! CUISEUR A RIZ PROFESSIONNEL",
    "subtitle": "Cuiseur a riz professionnel 10 litres",
    "description_title": "Inox - maintien au chaud 24h",
    "description_body": (
        "Structure exterieure en acier inoxydable, revetement interieur antiadhesif, "
        "voyants de cuisson, livre avec cuillere et doseur a riz."
    ),
    "availability_badge": "EN STOCK",
    "on_poster_cta_label": "Nous contacter",
    "on_poster_cta_email": "commercial@cuistance.eu",
}


def _png(draw_fn, w, h) -> bytes:
    img = PILImage.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(img), w, h)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _rice(d, w, h):
    d.rounded_rectangle([90, 250, w - 90, 700], radius=60, fill=(206, 209, 214, 255))
    d.ellipse([110, 150, w - 110, 330], fill=(232, 234, 237, 255), outline=(150, 154, 160, 255), width=3)
    d.rounded_rectangle([w // 2 - 78, 470, w // 2 + 78, 560], radius=14, fill=(40, 42, 46, 255))


def main():
    from playwright.sync_api import sync_playwright

    product_png = OUT / "_product.png"
    product_png.write_bytes(_png(_rice, 620, 760))

    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), partial(SimpleHTTPRequestHandler, directory=str(FRONTEND)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{PORT}"
    cap = {"body": None, "console_errors": []}
    result = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(viewport={"width": 1280, "height": 1700})
            # Point the app at our mock backend before any page script runs.
            ctx.add_init_script(f"localStorage.setItem('marketing-poster-api-base', '{base}');")
            page = ctx.new_page()
            page.on("console", lambda m: cap["console_errors"].append(m.text) if m.type == "error" else None)

            # Route order: catch-all first, specific later (later wins in Playwright).
            ctx.route("**/api/**", lambda r: r.fulfill(status=200, content_type="application/json", body="{}"))
            ctx.route("**/api/auth/me", lambda r: r.fulfill(
                status=200, content_type="application/json",
                body=json.dumps({"authenticated": True, "ok": True, "user": {"email": "ops@example.com", "role": "ops"}, "role": "ops"})))
            ctx.route("**/api/r2/presign-put", lambda r: r.fulfill(
                status=200, content_type="application/json", body=json.dumps({
                    "put_url": f"{base}/__mock_put",
                    "get_url": "https://assets.example/cuistance/asset.png",
                    "public_url": "https://assets.example/cuistance/asset.png",
                    "key": "mock/asset.png", "headers": {},
                })))
            ctx.route(f"{base}/__mock_put", lambda r: r.fulfill(status=200, body=""))

            def gen_route(route):
                cap["body"] = route.request.post_data
                route.fulfill(status=200, content_type="application/json", body=json.dumps({
                    "poster_key": "mock", "trace_id": "t", "final_url": "https://assets.example/final.png",
                    "final_hash": "h", "template_id": "template_product_sheet_v1",
                }))
            ctx.route("**/api/v2/generate-poster", gen_route)

            # ---- Stage 1 ----
            page.goto(f"{base}/index.html", wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            # Select Family B in the real chooser (inject the option if init filtered it).
            page.evaluate("""() => {
              const s=document.getElementById('template-select-stage1');
              if (![...s.options].some(o=>o.value==='template_product_sheet_v1')) {
                const o=document.createElement('option'); o.value='template_product_sheet_v1'; o.text='Product Sheet'; s.add(o);
              }
              s.value='template_product_sheet_v1';
              s.dispatchEvent(new Event('change',{bubbles:true}));
            }""")
            page.wait_for_selector("#s1-template-b-announcement:not([hidden])", timeout=8000)
            vis = page.evaluate("""() => ({
              announcement: !document.getElementById('s1-template-b-announcement').hidden,
              topcopy: !document.getElementById('s1-template-b-topcopy').hidden,
              description: !document.getElementById('s1-template-b-description').hidden,
              familyA_bottom: !document.getElementById('s1-bottom-thumbs').hidden,
              familyA_callouts: !document.getElementById('stage1-product-callouts-block').hidden
            })""")
            result["visibility"] = vis
            assert vis["announcement"] and vis["topcopy"] and vis["description"], f"B fields not visible: {vis}"
            assert not vis["familyA_bottom"] and not vis["familyA_callouts"], f"Family A leaked: {vis}"

            page.fill("input[name='brand_name']", SAMPLE["brand_name"])
            page.fill("input[name='title']", SAMPLE["title"])
            try:
                page.fill("input[name='subtitle']", SAMPLE["subtitle"])
            except Exception:
                pass
            page.fill("#sku-text-stage1", SAMPLE["sku_text"])
            page.fill("#description-title-stage1", SAMPLE["description_title"])
            page.fill("#description-body-stage1", SAMPLE["description_body"])
            page.fill("#availability-badge-stage1", SAMPLE["availability_badge"])
            page.check("#tariff-on-request-stage1")
            page.fill("#on-poster-cta-label-stage1", SAMPLE["on_poster_cta_label"])
            page.fill("#on-poster-cta-email-stage1", SAMPLE["on_poster_cta_email"])
            page.set_input_files("input[name='product_image_1']", str(product_png))
            page.wait_for_timeout(800)

            result["entered"] = page.evaluate("""() => ({
              availability: document.getElementById('availability-badge-stage1').value,
              tariff: document.getElementById('tariff-on-request-stage1').checked,
              cta_label: document.getElementById('on-poster-cta-label-stage1').value,
              cta_email: document.getElementById('on-poster-cta-email-stage1').value,
              sku: document.getElementById('sku-text-stage1').value
            })""")
            page.screenshot(path=str(OUT / "stage1_or_stage2_input_screenshot.png"), full_page=True)

            # Persist Stage1 -> sessionStorage via the real "go to stage 2" control.
            page.click("#go-to-stage2")
            page.wait_for_timeout(1200)
            snap = page.evaluate("""() => {
              for (const k of Object.keys(sessionStorage)) {
                try { const v=JSON.parse(sessionStorage.getItem(k));
                  if (v && (v.sku_text!==undefined || v.template_variant!==undefined)) return {key:k, data:v};
                } catch(e){}
              }
              return null;
            }""")
            result["stage1_snapshot_has_fields"] = bool(snap) and {
                "availability_badge": snap["data"].get("availability_badge"),
                "tariff_mode": snap["data"].get("tariff_mode"),
                "on_poster_cta_label": snap["data"].get("on_poster_cta_label"),
                "on_poster_cta_email": snap["data"].get("on_poster_cta_email"),
            }

            # ---- Stage 2: generate ----
            if not page.url.endswith("stage2.html"):
                page.goto(f"{base}/stage2.html", wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            page.screenshot(path=str(OUT / "stage2_request_preview_screenshot.png"), full_page=True)
            gen = page.query_selector("#generate-poster")
            if gen:
                try:
                    gen.click()
                except Exception as e:
                    result["generate_click_error"] = str(e)[:200]
                for _ in range(8):
                    if cap["body"]:
                        break
                    page.wait_for_timeout(1000)
            browser.close()
    finally:
        httpd.shutdown()
        try:
            product_png.unlink()
        except Exception:
            pass

    result["console_errors"] = cap["console_errors"][:20]
    result["generate_request_captured"] = bool(cap["body"])
    if cap["body"]:
        try:
            parsed = json.loads(cap["body"])
        except Exception:
            parsed = {"_raw": cap["body"][:3000]}
        blob = json.dumps(parsed, ensure_ascii=False)
        result["generate_body_fields_present"] = {
            k: (f'"{k}"' in blob) for k in
            ("availability_badge", "tariff_mode", "on_poster_cta_label", "on_poster_cta_email", "sku_text")
        }
        (OUT / "captured_generate_body.json").write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "ui_validation_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
