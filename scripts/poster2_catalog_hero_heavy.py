#!/usr/bin/env python3
"""
HX-POSTER2-REFERENCE-TO-POSTER-V2 — heavy reconstruction renderer (iterative).

Pushes the catalog_hero reconstruction toward >=4.5/5 reference likeness. Standalone
(new experimental family; Family A/B untouched). Renders with the project's Chromium
engine. Supports iteration history via --iter N (saves labeled outputs).

Usage:
  PYTHONPATH=. ./.venv/bin/python scripts/poster2_catalog_hero_heavy.py --iter 2

Outputs:
  scripts/out/reference_grammar_v1/heavy/iter_<N>.png
  docs/poster2/assets/reconstruction_v1/reconstruction_render_v2.png   (latest "best")
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import sys
import urllib.parse
from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage, ImageEnhance

_REPO = Path(__file__).resolve().parents[1]
_POSTER = Path("/Users/tylerzhao/poster")
_OUT = _REPO / "scripts/out/reference_grammar_v1/heavy"
_DOCS = _REPO / "docs/poster2/assets/reconstruction_v1"

RED = "#E1002A"
CHARCOAL = "#1f2024"
INK = "#262626"
STEEL = "#8a9099"
ORANGE = "#E8531F"
W, H = 1240, 1754

ASSETS = {
    "logo": _POSTER / "logo_01.jpg",
    "food": _POSTER / "SOP" / "Golden fries and crispy nuggets frying.png",
    "product": _POSTER / "产品图.jpg",
    "product2": _POSTER / "产品图2.jpg",
    "fryer1": _POSTER / "demo图" / "Electric Fryer1.jpg",
}


def _cap(img, max_dim=1500):
    if img.width <= max_dim and img.height <= max_dim:
        return img
    img = img.copy(); img.thumbnail((max_dim, max_dim), PILImage.LANCZOS); return img


def _warm_food(img):
    img = img.convert("RGB")
    # tight crop on the golden nugget basket (right) -> warm food fills frame, no handle
    img = img.crop((int(img.width * 0.58), int(img.height * 0.39),
                    int(img.width * 0.95), int(img.height * 0.585)))
    img = ImageEnhance.Brightness(img).enhance(1.16)
    img = ImageEnhance.Color(img).enhance(1.66)
    img = ImageEnhance.Contrast(img).enhance(1.08)
    r, g, b = img.split()
    r = r.point(lambda v: min(255, int(v * 1.12)))
    g = g.point(lambda v: min(255, int(v * 1.03)))
    b = b.point(lambda v: int(v * 0.80))
    return PILImage.merge("RGB", (r, g, b))


def _whiten_bg(img, lo=232):
    """Push the near-white studio background of isolated products to pure white,
    so the product floats clean (no grey panel)."""
    import numpy as np
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    mask = (r >= lo) & (g >= lo) & (b >= lo) & (abs(r - g) < 22) & (abs(g - b) < 22) & (abs(r - b) < 26)
    a[mask] = [255, 255, 255]
    return PILImage.fromarray(a.astype("uint8"), "RGB")


def _cover(img, w, h):
    img = img.convert("RGB")
    ratio = max(w / img.width, h / img.height)
    nw, nh = int(img.width * ratio), int(img.height * ratio)
    img = img.resize((nw, nh), PILImage.LANCZOS)
    l, t = (nw - w) // 2, (nh - h) // 2
    return img.crop((l, t, l + w, t + h))


def _trim_white(img, thresh=244):
    """Crop surrounding near-white margins so isolated products sit tight."""
    img = img.convert("RGB")
    from PIL import ImageChops
    bg = PILImage.new("RGB", img.size, (255, 255, 255))
    diff = ImageChops.difference(img, bg).convert("L")
    bbox = diff.point(lambda v: 255 if v > (255 - thresh) else 0).getbbox()
    return img.crop(bbox) if bbox else img


def _data_url(img, fmt="PNG"):
    img = _cap(img)
    buf = BytesIO()
    img.convert("RGBA" if fmt == "PNG" else "RGB").save(buf, format=fmt)
    mime = "png" if fmt == "PNG" else "jpeg"
    return f"data:image/{mime};base64," + base64.b64encode(buf.getvalue()).decode()


def _hex_pattern_uri():
    # large, clearly-visible carbon honeycomb (reads as texture even at small scale)
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='84' height='74' viewBox='0 0 84 74'>"
        "<path d='M21 1 L42 13 L42 38 L21 50 L0 38 L0 13 Z M63 1 L84 13 L84 38 L63 50 L42 38 L42 13 Z "
        "M42 38 L63 50 L63 74 L42 74 M21 50 L21 74 L42 74' "
        "fill='none' stroke='#666a74' stroke-width='2'/></svg>"
    )
    return "data:image/svg+xml," + urllib.parse.quote(svg)


def _font_face():
    out = []
    noto = _REPO / "assets/fonts/NotoSansSC-SemiBold.ttf"
    out.append("@font-face{font-family:'NotoSC';font-weight:600;"
               f"src:url(data:font/ttf;base64,{base64.b64encode(noto.read_bytes()).decode()}) format('truetype');}}")
    anton = _REPO / "assets/fonts/Anton-Regular.ttf"
    if anton.exists():
        out.append("@font-face{font-family:'Anton';"
                   f"src:url(data:font/ttf;base64,{base64.b64encode(anton.read_bytes()).decode()}) format('truetype');}}")
    return "".join(out)


def build_html():
    logo = _data_url(PILImage.open(ASSETS["logo"]).convert("RGBA"))
    food = _data_url(_cover(_warm_food(PILImage.open(ASSETS["food"])), 430, 836), fmt="JPEG")
    product = _data_url(_whiten_bg(_trim_white(PILImage.open(ASSETS["product"])), lo=224), fmt="JPEG")
    g0 = _data_url(_whiten_bg(_trim_white(PILImage.open(ASSETS["product"])), lo=224), fmt="JPEG")
    g1 = _data_url(_whiten_bg(_trim_white(PILImage.open(ASSETS["product2"])), lo=224), fmt="JPEG")
    g2 = _data_url(_whiten_bg(_trim_white(PILImage.open(ASSETS["fryer1"])), lo=224), fmt="JPEG")
    hexuri = _hex_pattern_uri()

    # Organic radial callouts: varied y stagger + curved leaders to varied anchors.
    # (text, side, anchor_x, anchor_y, label_y) — anchors fan around the product.
    callouts = [
        ("Cuve inox amovible", "left", 690, 560, 506),
        ("Sécurité anti-surchauffe", "left", 666, 706, 686),
        ("Structure acier inox AISI 304", "left", 714, 852, 854),
        ("Thermostat réglable 0–200°C", "right", 1058, 552, 506),
        ("Double cuve indépendante", "right", 1078, 700, 686),
        ("Panier grillagé à poignée", "right", 1014, 856, 858),
    ]
    DY = 26  # push the callout cluster down -> breathing room under the title
    svg_lines, label_divs = [], []
    for text, side, ax, ay, ly in callouts:
        ay += DY
        ly += DY
        if side == "left":
            label_left, label_w, ta = 454, 152, "right"
            x_end = 612
            cx = (x_end + ax) / 2 - 20   # control point bows the leader (organic)
        else:
            label_left, label_w, ta = 1104, 134, "left"
            x_end = 1096
            cx = (x_end + ax) / 2 + 20
        cy = (ly + 12 + ay) / 2 - 16
        svg_lines.append(
            f'<path d="M {x_end} {ly+12} Q {cx:.0f} {cy:.0f} {ax} {ay}" stroke="{INK}" '
            f'stroke-width="1.3" stroke-dasharray="2.5 4" fill="none" opacity="0.72"/>'
            f'<circle cx="{ax}" cy="{ay}" r="5.5" fill="{RED}"/>'
            f'<circle cx="{ax}" cy="{ay}" r="10" fill="none" stroke="{RED}" stroke-width="1" opacity="0.35"/>'
            f'<circle cx="{x_end}" cy="{ly+12}" r="2.6" fill="{INK}"/>'
        )
        label_divs.append(
            f'<div class="callout" style="left:{label_left}px;top:{ly}px;'
            f'width:{label_w}px;text-align:{ta}">{text}</div>'
        )

    # Gallery: frameless isolated-on-white, ESCALATING scale (small -> large), name only.
    gallery = [
        (g1, "Compacte · 6 L", 290, 224),
        (g0, "Simple cuve · 8 L", 350, 270),
        (g2, "Double cuve · 2×8 L", 416, 320),
    ]
    g_html = ""
    for src, cap, w_, h_ in gallery:
        g_html += (
            f'<div class="g-item"><div class="g-img" style="height:330px">'
            f'<img src="{src}" style="max-width:{w_}px;max-height:{h_}px"></div>'
            f'<div class="g-cap">{cap}</div></div>'
        )

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{_font_face()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:#fff}}
#poster-root{{position:relative;width:{W}px;height:{H}px;background:#fff;
  font-family:'Helvetica Neue',Arial,'NotoSC',sans-serif;overflow:hidden}}
.header{{position:absolute;top:0;left:0;width:{W}px;height:120px;background:{CHARCOAL};
  background-image:url("{hexuri}");background-repeat:repeat;
  display:flex;align-items:center;justify-content:space-between;padding:0 52px}}
.header .wave{{position:absolute;inset:0;background:
  radial-gradient(140% 200% at 90% -60%,rgba(90,94,104,.22) 0%,rgba(31,32,36,0) 55%)}}
.header .brand{{position:relative;display:flex;align-items:center;gap:18px}}
.header .emblem{{width:50px;height:56px;background:{RED};position:relative;
  clip-path:polygon(50% 0,100% 27%,100% 73%,50% 100%,0 73%,0 27%)}}
.header .emblem:after{{content:'';position:absolute;left:50%;top:50%;
  width:20px;height:20px;transform:translate(-50%,-50%);
  border:3px solid #fff;border-radius:4px}}
.header img{{height:54px;filter:brightness(0) invert(1);position:relative}}
.header .rgt{{position:relative;display:flex;align-items:center;gap:20px}}
/* partner co-brand lockup (icon + wordmark), mirrors the reference's dual-brand bar */
.header .partner{{display:flex;align-items:center;gap:11px}}
.header .partner .mk{{width:38px;height:38px;border:2px solid #cfd2d6;border-radius:7px;
  display:flex;align-items:center;justify-content:center}}
.header .partner .mk span{{display:block;width:16px;height:16px;border:2px solid {RED};
  border-radius:50%}}
.header .partner .wm{{line-height:1.05}}
.header .partner .wm .a{{color:#fff;font-size:19px;font-weight:800;letter-spacing:2px}}
.header .partner .wm .b{{color:{STEEL};font-size:10px;letter-spacing:3px}}
.header .accent{{height:5px;background:{RED};position:absolute;left:0;bottom:0;width:{W}px}}
/* hero food — full-bleed left, tall warm block, clear white gutter to the product */
.food{{position:absolute;left:0;top:125px;width:406px;height:846px;
  background-image:url('{food}');background-size:cover;background-position:center}}
.food:after{{content:'';position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(0,0,0,0) 88%,rgba(12,7,2,.16) 100%)}}
.food .tag{{position:absolute;left:0;bottom:26px;background:{RED};color:#fff;
  font-weight:800;font-style:italic;font-size:20px;letter-spacing:1px;padding:8px 20px;
  text-transform:uppercase}}
/* title — heavy black-condensed solid red ALL-CAPS italic mass */
.title{{position:absolute;left:462px;top:146px;width:770px}}
.title h1{{color:{RED};font-family:'Anton','Arial Narrow',sans-serif;
  font-weight:400;font-style:normal;text-transform:uppercase;
  font-size:120px;line-height:.78;letter-spacing:-2px;
  transform:skewX(-9deg) scaleX(.96);transform-origin:left}}
.title h1 .sm{{font-size:100px}}
/* product — floats on a clean white field, pushed right under the title */
.product{{position:absolute;left:640px;top:498px;width:452px;height:444px}}
.product:before{{content:'';position:absolute;left:50%;top:50%;width:600px;height:400px;
  transform:translate(-50%,-50%);
  background:radial-gradient(closest-side,#ffffff 90%,rgba(255,255,255,0) 100%)}}
.product img{{position:relative;width:100%;height:100%;object-fit:contain;
  filter:drop-shadow(0 12px 16px rgba(0,0,0,.15))}}
/* callouts */
.callouts{{position:absolute;left:0;top:0;width:{W}px;height:930px;pointer-events:none}}
.callout{{position:absolute;font-family:'NotoSC','Helvetica Neue',Arial,sans-serif;
  font-size:18px;line-height:1.16;color:{INK};font-weight:600}}
/* restated title — UPRIGHT heavy red (reference restates non-italic, larger) */
.band{{position:absolute;left:0;top:936px;width:{W}px;text-align:center}}
.band h2{{color:{RED};text-transform:uppercase;
  font-family:'Anton','Arial Narrow',sans-serif;font-weight:400;
  font-size:78px;letter-spacing:0px}}
.band .sub{{color:#3a3d42;font-size:22px;letter-spacing:2px;margin-top:14px;
  font-weight:800;text-transform:uppercase}}
/* gallery — isolated on white, varied scale, no chrome (closing beat) */
.gallery{{position:absolute;left:40px;top:1226px;width:{W-80}px;
  display:flex;justify-content:space-between;align-items:flex-end;gap:14px}}
.g-item{{flex:1;text-align:center}}
.g-img{{display:flex;align-items:flex-end;justify-content:center}}
.g-img img{{object-fit:contain;filter:drop-shadow(0 5px 7px rgba(0,0,0,.07))}}
.g-cap{{font-family:'NotoSC',sans-serif;font-weight:700;color:{INK};font-size:20px;margin-top:16px}}
/* whisper-weight contact line (operator usability, no visual weight) */
.contact{{position:absolute;left:0;bottom:30px;width:{W}px;text-align:center}}
.contact .line{{color:#c4c8ce;font-size:13px;letter-spacing:2px;font-weight:600}}
</style></head><body>
<div id="poster-root">
  <div class="header"><div class="wave"></div>
    <div class="brand"><div class="emblem"></div><img src="{logo}"></div>
    <div class="rgt">
      <div class="partner"><div class="mk"><span></span></div>
        <div class="wm"><div class="a">FRANCE&nbsp;CHR</div><div class="b">DISTRIBUTION&nbsp;PRO</div></div></div>
    </div>
    <div class="accent"></div></div>
  <div class="food"></div>
  <div class="title">
    <h1>LES<br>FRITEUSES<br><span class="sm">ÉLECTRIQUES</span></h1></div>
  <div class="product"><img src="{product}"></div>
  <svg class="callouts" viewBox="0 0 {W} 930">{''.join(svg_lines)}</svg>
  {''.join(label_divs)}
  <div class="band"><div class="line"></div>
    <h2>LES FRITEUSES ÉLECTRIQUES</h2>
    <div class="sub">Quand le croustillant fait toute la différence&nbsp;!</div></div>
  <div class="gallery">{g_html}</div>
  <div class="contact"><div class="line">cuistance.com&nbsp;&nbsp;·&nbsp;&nbsp;contact@cuistance.com</div></div>
</div></body></html>"""


async def render(html, path):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        b = await pw.chromium.launch(headless=True,
            args=["--disable-dev-shm-usage", "--font-render-hinting=none"])
        page = await b.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        await page.set_content(html, wait_until="networkidle")
        await page.locator("#poster-root").wait_for(state="visible")
        await page.locator("#poster-root").screenshot(path=str(path), type="png")
        await b.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iter", type=int, default=2)
    args = ap.parse_args()
    _OUT.mkdir(parents=True, exist_ok=True)
    _DOCS.mkdir(parents=True, exist_ok=True)
    html = build_html()
    (_OUT / f"catalog_hero_v2_iter{args.iter}.html").write_text(html, encoding="utf-8")
    out = _OUT / f"iter_{args.iter}.png"
    asyncio.run(render(html, out))
    import shutil
    shutil.copy(out, _DOCS / "reconstruction_render_v2.png")
    print("rendered:", out.relative_to(_REPO), "| best:", (_DOCS / "reconstruction_render_v2.png").relative_to(_REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
