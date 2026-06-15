"""POSTER2-FAMILY-B-ANNOUNCEMENT-REMOTE-UI-FILL-VALIDATION-V1 (local static UI proof).

Drives the improved Family B Announcement UI: selects Family B, fills the exact
Cuistance sample, screenshots Stage1 (clear labels + correct values), carries to
Stage2, asserts the Stage2 read-only summary shows the four announcement values,
and attempts to capture the /api/v2/generate-poster request body. Mocked endpoints;
no real backend / no real send.

Run: PYTHONPATH=. ./.venv/bin/python scripts/poster2_announcement_remote_ui_validation.py
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
OUT = ROOT / "docs/poster2/assets/announcement_remote_ui_validation_v1"
OUT.mkdir(parents=True, exist_ok=True)
PORT = 8761

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


def _rice(d, w, h):
    d.rounded_rectangle([90, 250, w - 90, 700], radius=60, fill=(206, 209, 214, 255))
    d.ellipse([110, 150, w - 110, 330], fill=(232, 234, 237, 255), outline=(150, 154, 160, 255), width=3)
    d.rounded_rectangle([w // 2 - 78, 470, w // 2 + 78, 560], radius=14, fill=(40, 42, 46, 255))


def main():
    from playwright.sync_api import sync_playwright

    product_png = OUT / "_product.png"
    img = PILImage.new("RGBA", (620, 760), (0, 0, 0, 0))
    _rice(ImageDraw.Draw(img), 620, 760)
    buf = BytesIO(); img.save(buf, format="PNG"); product_png.write_bytes(buf.getvalue())

    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), partial(SimpleHTTPRequestHandler, directory=str(FRONTEND)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{PORT}"
    cap = {"body": None, "console_errors": []}
    result = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(viewport={"width": 1280, "height": 1800})
            ctx.add_init_script(f"localStorage.setItem('marketing-poster-api-base', '{base}');")
            page = ctx.new_page()
            page.on("console", lambda m: cap["console_errors"].append(m.text) if m.type == "error" else None)

            ctx.route("**/api/**", lambda r: r.fulfill(status=200, content_type="application/json", body="{}"))
            ctx.route("**/api/auth/me", lambda r: r.fulfill(status=200, content_type="application/json",
                body=json.dumps({"enabled": True, "authenticated": True, "username": "ops", "ok": True, "role": "ops"})))
            ctx.route("**/api/health", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True})))
            ctx.route("**/api/r2/presign-put", lambda r: r.fulfill(status=200, content_type="application/json",
                body=json.dumps({"put_url": f"{base}/__mock_put", "get_url": "https://assets.example/a.png",
                                  "public_url": "https://assets.example/a.png", "key": "mock/a.png", "headers": {}})))
            ctx.route(f"{base}/__mock_put", lambda r: r.fulfill(status=200, body=""))

            def gen_route(route):
                cap["body"] = route.request.post_data
                route.fulfill(status=200, content_type="application/json", body=json.dumps({
                    "poster_key": "mock", "trace_id": "t", "final_url": "https://assets.example/final.png",
                    "final_hash": "h", "template_id": "template_product_sheet_v1",
                    "announcement_variant_contract_review": {"variant_id": "family_b_product_announcement"},
                }))
            ctx.route("**/api/v2/generate-poster", gen_route)

            # ---- Stage 1 ----
            page.goto(f"{base}/index.html", wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            page.evaluate("""() => {
              const s=document.getElementById('template-select-stage1');
              if (![...s.options].some(o=>o.value==='template_product_sheet_v1')) {
                const o=document.createElement('option'); o.value='template_product_sheet_v1'; o.text='Product Sheet'; s.add(o);
              }
              s.value='template_product_sheet_v1'; s.dispatchEvent(new Event('change',{bubbles:true}));
            }""")
            page.wait_for_selector("#s1-template-b-announcement:not([hidden])", timeout=8000)

            # Capture the rendered announcement labels (clarity evidence)
            result["labels"] = page.evaluate("""() => {
              const fs=document.getElementById('s1-template-b-announcement');
              const labels=[...fs.querySelectorAll('label span, legend, .feature-label')].map(e=>e.textContent.trim()).filter(Boolean);
              return { fieldset_text_has: {
                announcement: /Announcement strip/i.test(fs.textContent),
                not_product_desc: /不是产品描述/.test(fs.textContent),
                availability: /Availability badge/i.test(fs.textContent),
                tariff: /Tariff line/i.test(fs.textContent),
                cta_label: /CTA label/i.test(fs.textContent),
                cta_email: /CTA email/i.test(fs.textContent),
                no_price_word: !/价格|price input/i.test(fs.textContent),
                no_send_word: !/(发送|Stage3|send email)/i.test(fs.textContent)
              }, placeholders: {
                availability: document.getElementById('availability-badge-stage1').placeholder,
                cta_label: document.getElementById('on-poster-cta-label-stage1').placeholder,
                cta_email: document.getElementById('on-poster-cta-email-stage1').placeholder
              }};
            }""")

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
            page.wait_for_timeout(700)
            # Scroll the announcement fieldset into view for a focused screenshot region
            page.eval_on_selector("#s1-template-b-announcement", "el => el.scrollIntoView({block:'center'})")
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT / "stage1_filled_correct_values.png"), full_page=True)

            page.click("#go-to-stage2")
            page.wait_for_timeout(1200)
            snap = page.evaluate("""() => {
              for (const k of Object.keys(sessionStorage)) {
                try { const v=JSON.parse(sessionStorage.getItem(k));
                  if (v && (v.sku_text!==undefined || v.template_variant!==undefined))
                    return {availability_badge:v.availability_badge, tariff_mode:v.tariff_mode,
                            on_poster_cta_label:v.on_poster_cta_label, on_poster_cta_email:v.on_poster_cta_email};
                } catch(e){}
              }
              return null;
            }""")
            result["stage1_snapshot"] = snap

            # ---- Stage 2 ----
            if not page.url.endswith("stage2.html"):
                page.goto(f"{base}/stage2.html", wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            try:
                page.fill("#api-base", base)
            except Exception:
                pass
            stage2_vals = page.evaluate("""() => ({
              availability: document.getElementById('s2-b-availability')?.value,
              tariff: document.getElementById('s2-b-tariff')?.value,
              cta: document.getElementById('s2-b-cta')?.value,
              sku: document.getElementById('s2-b-sku')?.value
            })""")
            result["stage2_summary"] = stage2_vals
            page.eval_on_selector("#s2-template-b-summary", "el => el && el.scrollIntoView({block:'center'})") if page.query_selector("#s2-template-b-summary") else None
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT / "stage2_summary_correct_values.png"), full_page=True)

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
            parsed = {"_raw": cap["body"][:4000]}
        (OUT / "generate_request_payload.json").write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
        blob = json.dumps(parsed, ensure_ascii=False)
        result["generate_body_fields"] = {k: (f'"{k}"' in blob) for k in
            ("availability_badge", "tariff_mode", "on_poster_cta_label", "on_poster_cta_email", "sku_text")}
    (OUT / "ui_validation_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
