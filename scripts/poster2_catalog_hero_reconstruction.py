#!/usr/bin/env python3
"""
HX-POSTER2-REFERENCE-RECONSTRUCTION-V1 — catalog_hero_v1 reconstruction renderer.

Standalone, experimental NEW template family `catalog_hero_v1`. Reconstructs the
reference poster's editorial catalog-hero design system with the operator's CUISTANCE
brand + supplied fryer products. Renders an ACTUAL poster PNG via the same Chromium
(Playwright) engine the project uses. Family A code is NOT touched.

Inputs (operator-supplied + on-theme supporting assets from the poster kit):
  logo_01.jpg              CUISTANCE wordmark
  产品图.jpg                dual-tank fryer (hero product)
  产品图2.jpg               single-tank fryer (gallery)
  Electric Fryer1.jpg      fryer (gallery)
  Golden fries ... .png    food hero (fryer in action, warm)

Output:
  scripts/out/reference_grammar_v1/reconstruction/reconstruction_render_v1.png
  docs/poster2/assets/reconstruction_v1/reconstruction_render_v1.png  (tracked copy)
"""
from __future__ import annotations

import asyncio
import base64
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage, ImageEnhance

_REPO = Path(__file__).resolve().parents[1]
_POSTER = Path("/Users/tylerzhao/poster")
_OUT = _REPO / "scripts/out/reference_grammar_v1/reconstruction"
_DOCS = _REPO / "docs/poster2/assets/reconstruction_v1"

# ---- design tokens (measured from reference + CUISTANCE target) -------------
RED = "#E1002A"
CHARCOAL = "#232428"
INK = "#2b2b2b"
STEEL = "#8a9099"
ORANGE = "#E8531F"

W, H = 1240, 1754  # A4 portrait ratio 0.707

ASSETS = {
    "logo": _POSTER / "logo_01.jpg",
    "food": _POSTER / "SOP" / "Golden fries and crispy nuggets frying.png",
    "product": _POSTER / "产品图.jpg",
    "product2": _POSTER / "产品图2.jpg",
    "fryer1": _POSTER / "demo图" / "Electric Fryer1.jpg",
}


def _cap(img: PILImage.Image, max_dim: int = 1400) -> PILImage.Image:
    if img.width <= max_dim and img.height <= max_dim:
        return img
    img = img.copy()
    img.thumbnail((max_dim, max_dim), PILImage.LANCZOS)
    return img


def _warm_food(img: PILImage.Image) -> PILImage.Image:
    """Bias the hero toward the golden food (lower ~72% of the frame) and warm-grade
    it so the left rail reads as an appetite-warm anchor, not a cool steel scene."""
    img = img.convert("RGB")
    top = int(img.height * 0.28)
    img = img.crop((0, top, img.width, img.height))  # drop the cool steel headroom
    img = ImageEnhance.Color(img).enhance(1.22)       # +saturation (golden food pops)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    # gentle warm tint
    r, g, b = img.split()
    r = r.point(lambda v: min(255, int(v * 1.05)))
    b = b.point(lambda v: int(v * 0.95))
    return PILImage.merge("RGB", (r, g, b))


def _cover(img: PILImage.Image, w: int, h: int) -> PILImage.Image:
    img = img.convert("RGB")
    ratio = max(w / img.width, h / img.height)
    nw, nh = int(img.width * ratio), int(img.height * ratio)
    img = img.resize((nw, nh), PILImage.LANCZOS)
    left, top = (nw - w) // 2, (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def _data_url(img: PILImage.Image, fmt: str = "PNG") -> str:
    img = _cap(img)
    buf = BytesIO()
    img.convert("RGBA" if fmt == "PNG" else "RGB").save(buf, format=fmt)
    mime = "png" if fmt == "PNG" else "jpeg"
    return f"data:image/{mime};base64," + base64.b64encode(buf.getvalue()).decode()


def _font_face() -> str:
    f = _REPO / "assets/fonts/NotoSansSC-SemiBold.ttf"
    b64 = base64.b64encode(f.read_bytes()).decode()
    return (
        "@font-face{font-family:'NotoSC';font-weight:600;"
        f"src:url(data:font/ttf;base64,{b64}) format('truetype');}}"
    )


def build_html() -> str:
    logo = _data_url(PILImage.open(ASSETS["logo"]).convert("RGBA"))
    # Hero food: cover-crop to the tall left rail, slightly warm-boosted by treatment.
    food = _data_url(_cover(_warm_food(PILImage.open(ASSETS["food"])), 474, 772), fmt="JPEG")
    product = _data_url(PILImage.open(ASSETS["product"]).convert("RGBA"))
    g0 = _data_url(PILImage.open(ASSETS["product"]).convert("RGBA"))
    g1 = _data_url(PILImage.open(ASSETS["product2"]).convert("RGBA"))
    g2 = _data_url(PILImage.open(ASSETS["fryer1"]).convert("RGBA"))

    # Callouts: (text, side, anchor_x, anchor_y, label_y) within the right product
    # lane only (x>=486, clear of the food rail). anchors sit on the product; labels
    # fan left/right of it (editorial radial grammar).
    callouts = [
        ("Cuve inox amovible", "left", 706, 580, 556),
        ("Sécurité anti-surchauffe", "left", 694, 706, 690),
        ("Structure acier inox AISI 304", "left", 724, 824, 812),
        ("Thermostat réglable 0–200°C", "right", 1012, 580, 556),
        ("Double cuve indépendante", "right", 1024, 706, 690),
        ("Panier grillagé à poignée", "right", 980, 824, 812),
    ]
    svg_lines = []
    label_divs = []
    for text, side, ax, ay, ly in callouts:
        if side == "left":
            text_align, label_left, label_w = "right", 484, 156
            x_lab_end = 648          # inner edge of left label column -> toward product
        else:
            text_align, label_left, label_w = "left", 1080, 156
            x_lab_end = 1072         # inner edge of right label column
        svg_lines.append(
            f'<path d="M {x_lab_end} {ly+12} L {ax} {ay}" stroke="{INK}" '
            f'stroke-width="1.4" stroke-dasharray="3 4" fill="none" opacity="0.7"/>'
            f'<circle cx="{ax}" cy="{ay}" r="5.5" fill="{RED}"/>'
            f'<circle cx="{x_lab_end}" cy="{ly+12}" r="3" fill="{INK}"/>'
        )
        label_divs.append(
            f'<div class="callout" style="left:{label_left}px;top:{ly}px;'
            f'width:{label_w}px;text-align:{text_align}">{text}</div>'
        )

    gallery_items = [
        (g0, "Double cuve · 2×8 L", "Réf. EF-82D"),
        (g1, "Simple cuve · 8 L", "Réf. EF-81S"),
        (g2, "Compacte · 6 L", "Réf. EF-60C"),
    ]
    gallery_html = ""
    for src, cap, ref in gallery_items:
        gallery_html += (
            f'<div class="g-item"><div class="g-imgwrap"><img src="{src}"></div>'
            f'<div class="g-cap">{cap}</div><div class="g-ref">{ref}</div></div>'
        )

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{_font_face()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:#fff}}
#poster-root{{position:relative;width:{W}px;height:{H}px;background:#fff;
  font-family:'Helvetica Neue',Arial,'NotoSC',sans-serif;overflow:hidden}}
/* header */
.header{{position:absolute;top:0;left:0;width:{W}px;height:116px;background:{CHARCOAL};
  background-image:radial-gradient(120% 180% at 80% -40%,#3a3c42 0%,{CHARCOAL} 55%);
  display:flex;align-items:center;justify-content:space-between;padding:0 48px}}
.header img{{height:46px;filter:brightness(0) invert(1)}}
.header .rgt{{color:#cfd2d6;font-size:15px;letter-spacing:3px;font-weight:600}}
.header .accent{{height:6px;background:{RED};position:absolute;left:0;bottom:0;width:{W}px}}
/* hero food rail — full-bleed left, aligned under header (editorial) */
.food{{position:absolute;left:0;top:122px;width:474px;height:772px;
  background-image:url('{food}');background-size:cover;background-position:center}}
.food:after{{content:'';position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(0,0,0,0) 60%,rgba(20,12,6,.28) 100%)}}
/* title */
.title{{position:absolute;left:498px;top:144px;width:706px}}
.title .kick{{color:{INK};font-size:19px;font-weight:700;letter-spacing:6px;margin-bottom:6px}}
.title h1{{color:{RED};font-weight:900;font-style:italic;text-transform:uppercase;
  font-size:84px;line-height:.86;letter-spacing:-1px;transform:skewX(-6deg);
  transform-origin:left}}
.title h1 .sm{{font-size:52px}}
.title .zh{{font-family:'NotoSC',sans-serif;font-weight:600;color:{INK};
  font-size:30px;margin-top:12px;letter-spacing:4px}}
/* product */
.product{{position:absolute;left:660px;top:498px;width:400px;height:384px}}
.product img{{width:100%;height:100%;object-fit:contain;
  filter:drop-shadow(0 16px 22px rgba(0,0,0,.16))}}
/* callouts */
.callouts{{position:absolute;left:0;top:0;width:{W}px;height:920px;pointer-events:none}}
.callout{{position:absolute;font-family:'NotoSC','Helvetica Neue',Arial,sans-serif;
  font-size:18px;line-height:1.18;color:{INK};font-weight:600}}
/* restated title band */
.band{{position:absolute;left:0;top:946px;width:{W}px;text-align:center}}
.band .line{{width:240px;height:3px;background:{RED};margin:0 auto 22px}}
.band h2{{color:{RED};font-weight:900;font-style:italic;text-transform:uppercase;
  font-size:56px;letter-spacing:-.5px;transform:skewX(-6deg)}}
.band .sub{{color:{STEEL};font-size:22px;letter-spacing:3px;margin-top:14px;
  font-weight:600;text-transform:uppercase}}
/* gallery */
.gallery{{position:absolute;left:44px;top:1150px;width:{W-88}px;
  display:flex;justify-content:space-between;gap:26px}}
.g-item{{width:362px;text-align:center}}
.g-imgwrap{{height:300px;background:#fafafa;border:1px solid #ededed;border-radius:10px;
  display:flex;align-items:center;justify-content:center;padding:18px}}
.g-imgwrap img{{max-width:100%;max-height:100%;object-fit:contain}}
.g-cap{{font-family:'NotoSC',sans-serif;font-weight:600;color:{INK};font-size:21px;margin-top:16px}}
.g-ref{{color:{STEEL};font-size:16px;margin-top:4px;letter-spacing:1px}}
/* footer */
.footer{{position:absolute;left:0;bottom:0;width:{W}px;height:128px;background:{CHARCOAL};
  display:flex;align-items:center;justify-content:space-between;padding:0 48px}}
.footer img{{height:34px;filter:brightness(0) invert(1)}}
.footer .mid{{color:#cfd2d6;font-size:17px;letter-spacing:2px}}
.footer .cta{{background:{ORANGE};color:#fff;font-weight:700;font-size:19px;
  padding:14px 30px;border-radius:8px;letter-spacing:1px;font-family:'NotoSC',sans-serif}}
</style></head><body>
<div id="poster-root">
  <div class="header"><img src="{logo}"><div class="rgt">CUISINE PROFESSIONNELLE</div>
    <div class="accent"></div></div>
  <div class="food"></div>
  <div class="title"><div class="kick">RÉF. 1210 · GAMME PRO</div>
    <h1>LES<br>FRITEUSES<br><span class="sm">ÉLECTRIQUES</span></h1>
    <div class="zh">专业商用电炸炉</div></div>
  <div class="product"><img src="{product}"></div>
  <svg class="callouts" viewBox="0 0 {W} 920">{''.join(svg_lines)}</svg>
  {''.join(label_divs)}
  <div class="band"><div class="line"></div>
    <h2>LES FRITEUSES ÉLECTRIQUES</h2>
    <div class="sub">Quand le croustillant fait toute la différence&nbsp;!</div></div>
  <div class="gallery">{gallery_html}</div>
  <div class="footer"><img src="{logo}">
    <div class="mid">contact@cuistance.com · +33 1 41 53 12 12</div>
    <div class="cta">CONTACTEZ-NOUS</div></div>
</div></body></html>"""


async def render(html: str, path: Path) -> None:
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True,
            args=["--disable-dev-shm-usage", "--font-render-hinting=none"])
        page = await browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        await page.set_content(html, wait_until="networkidle")
        await page.locator("#poster-root").wait_for(state="visible")
        await page.locator("#poster-root").screenshot(path=str(path), type="png")
        await browser.close()


def main() -> int:
    _OUT.mkdir(parents=True, exist_ok=True)
    _DOCS.mkdir(parents=True, exist_ok=True)
    html = build_html()
    (_OUT / "catalog_hero_v1.html").write_text(html, encoding="utf-8")
    out = _OUT / "reconstruction_render_v1.png"
    asyncio.run(render(html, out))
    # tracked copy
    import shutil
    shutil.copy(out, _DOCS / "reconstruction_render_v1.png")
    print("rendered:", out.relative_to(_REPO))
    print("tracked :", (_DOCS / "reconstruction_render_v1.png").relative_to(_REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
