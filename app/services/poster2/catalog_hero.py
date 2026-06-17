"""
Additive portrait Catalog-Hero family (catalog_hero_v1).

Productizes the `catalog_hero_v1` visual grammar (the 4.47/5 reconstruction) as an
ADDITIVE family. This module is a self-contained, parallel render path: it is dispatched
by the API endpoint ONLY for catalog-hero template ids and never enters the shared
PosterPipeline / RendererSelector — so Family A and Family B code paths are untouched.

Grammar (see docs/poster2/02_architecture/poster_visual_grammar_dimension_system_v1.md):
  charcoal brand bar (logo-L / partner-R) · warm food co-anchor (owner-gated) · heavy red
  ALL-CAPS title · isolated product with a dashed radial callout ring (<=3 frozen slots) ·
  restated centered title + strapline · isolated-on-white product range gallery.

Frozen-truth boundaries honored here:
  - annotation count clamped to exactly 3 (CATALOG_HERO_MAX_ANNOTATIONS)
  - food hero rendered ONLY from operator scenario_image (no runtime AI asset)
  - on-poster CTA is display-only (no Stage3 / send wiring)
"""
from __future__ import annotations

import base64
import urllib.parse
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Optional, Sequence

from PIL import Image as PILImage
from PIL import ImageChops, ImageDraw, ImageEnhance, ImageFont

# ----------------------------------------------------------------------------- consts --
CATALOG_HERO_FAMILY = "catalog_hero_portrait"
CATALOG_HERO_TEMPLATE_ID = "catalog_hero_v1"
CATALOG_HERO_TEMPLATE_VERSION = "1.0.0"
CATALOG_HERO_CONTRACT_VERSION = "poster2.catalog_hero_v1.v1"

# Frozen annotation ceiling — re-asserted here independently of template_behavior.py
# (which is NOT modified). Raising this is owner-gated.
CATALOG_HERO_MAX_ANNOTATIONS = 3

# Portrait canvas (~0.707), matching the reference design frame.
CANVAS_W, CANVAS_H = 1240, 1754

RED = "#E1002A"
CHARCOAL = "#1f2024"
INK = "#262626"
STEEL = "#8a9099"

_REPO = Path(__file__).resolve().parents[3]
_FONT_DIR = _REPO / "assets" / "fonts"
_ANTON = _FONT_DIR / "Anton-Regular.ttf"
_NOTO_SB = _FONT_DIR / "NotoSansSC-SemiBold.ttf"
_NOTO_R = _FONT_DIR / "NotoSansSC-Regular.ttf"


# ------------------------------------------------------------------------------ inputs --
@dataclass
class CatalogHeroInputs:
    """Resolved catalog-hero inputs (text + PIL images). Built from the request payload
    by `resolve_inputs` or directly by the deterministic smoke script."""

    brand_name: str = ""
    partner_name: str = ""              # request.agent_name
    title: str = ""                     # required
    subtitle: str = ""
    sku_text: str = ""
    features: tuple[str, ...] = ()      # callout labels (clamped to 3)
    cta_label: str = ""
    cta_email: str = ""
    logo: Optional[PILImage.Image] = None
    product: Optional[PILImage.Image] = None     # required (catalog_product_region)
    food_hero: Optional[PILImage.Image] = None   # owner-gated (scenario_image)
    gallery: tuple[PILImage.Image, ...] = ()
    # provenance: how the food hero arrived; never "ai_generated" in v1
    food_hero_source: str = "absent"             # operator_upload | absent

    @property
    def annotation_labels(self) -> list[str]:
        """The callout labels actually rendered — clamped to the frozen ceiling."""
        return [f for f in self.features if f and f.strip()][:CATALOG_HERO_MAX_ANNOTATIONS]


@dataclass
class CatalogHeroRenderResult:
    image: PILImage.Image
    engine: str                         # "chromium" | "pillow_fallback"
    degraded: bool
    grammar_profile: dict
    contract_review: dict
    timings_ms: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- helpers ----
def _trim_white(img: PILImage.Image, thresh: int = 244) -> PILImage.Image:
    img = img.convert("RGB")
    bg = PILImage.new("RGB", img.size, (255, 255, 255))
    diff = ImageChops.difference(img, bg).convert("L")
    bbox = diff.point(lambda v: 255 if v > (255 - thresh) else 0).getbbox()
    return img.crop(bbox) if bbox else img


def _whiten_bg(img: PILImage.Image, lo: int = 224) -> PILImage.Image:
    try:
        import numpy as np
    except Exception:
        return img.convert("RGB")
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    mask = (r >= lo) & (g >= lo) & (b >= lo) & (abs(r - g) < 22) & (abs(g - b) < 22) & (abs(r - b) < 26)
    a[mask] = [255, 255, 255]
    return PILImage.fromarray(a.astype("uint8"), "RGB")


def _cover(img: PILImage.Image, w: int, h: int) -> PILImage.Image:
    img = img.convert("RGB")
    ratio = max(w / img.width, h / img.height)
    nw, nh = max(1, int(img.width * ratio)), max(1, int(img.height * ratio))
    img = img.resize((nw, nh), PILImage.LANCZOS)
    l, t = (nw - w) // 2, (nh - h) // 2
    return img.crop((l, t, l + w, t + h))


def _warm(img: PILImage.Image) -> PILImage.Image:
    img = img.convert("RGB")
    img = ImageEnhance.Color(img).enhance(1.35)
    img = ImageEnhance.Contrast(img).enhance(1.06)
    return img


def _cap(img: PILImage.Image, max_dim: int = 1500) -> PILImage.Image:
    if img.width <= max_dim and img.height <= max_dim:
        return img
    img = img.copy()
    img.thumbnail((max_dim, max_dim), PILImage.LANCZOS)
    return img


def _data_url(img: PILImage.Image, fmt: str = "JPEG") -> str:
    img = _cap(img)
    buf = BytesIO()
    img.convert("RGBA" if fmt == "PNG" else "RGB").save(buf, format=fmt)
    mime = "png" if fmt == "PNG" else "jpeg"
    return f"data:image/{mime};base64," + base64.b64encode(buf.getvalue()).decode()


def _hex_pattern_uri() -> str:
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='84' height='74' viewBox='0 0 84 74'>"
        "<path d='M21 1 L42 13 L42 38 L21 50 L0 38 L0 13 Z M63 1 L84 13 L84 38 L63 50 L42 38 L42 13 Z "
        "M42 38 L63 50 L63 74 L42 74 M21 50 L21 74 L42 74' "
        "fill='none' stroke='#666a74' stroke-width='2'/></svg>"
    )
    return "data:image/svg+xml," + urllib.parse.quote(svg)


def _font_face() -> str:
    out = []
    if _NOTO_SB.exists():
        out.append(
            "@font-face{font-family:'NotoSC';font-weight:600;src:url(data:font/ttf;base64,"
            + base64.b64encode(_NOTO_SB.read_bytes()).decode() + ") format('truetype');}"
        )
    if _ANTON.exists():
        out.append(
            "@font-face{font-family:'Anton';src:url(data:font/ttf;base64,"
            + base64.b64encode(_ANTON.read_bytes()).decode() + ") format('truetype');}"
        )
    return "".join(out)


def _esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _title_lines(title: str) -> list[str]:
    """Split the title into <=3 ALL-CAPS lines for the heavy display block."""
    words = (title or "").upper().split()
    if not words:
        return [""]
    if len(words) <= 3:
        return words
    # group into 3 roughly-balanced lines
    out, per = [], (len(words) + 2) // 3
    for i in range(0, len(words), per):
        out.append(" ".join(words[i:i + per]))
    return out[:3]


# ------------------------------------------------------------------ grammar / contract --
def build_grammar_profile(inputs: CatalogHeroInputs, *, food_rendered: bool) -> dict:
    """The 12-dimension visual grammar profile emitted in diagnostics
    (poster_visual_grammar_dimension_system_v1.md)."""
    composition = "dual_co_anchor" if food_rendered else "product_led"
    return {
        "profile_id": "catalog_hero_v1",
        "governing_doc": "poster_visual_grammar_dimension_system_v1.md",
        "dimensions": {
            "1_composition_archetype": "editorial_catalog_hero",
            "2_focal_hierarchy": {
                "model": composition,
                "anchors": ["food_hero", "product"] if food_rendered else ["product"],
                "title_dominance": 5,
                "product_dominance": 4,
                "scene_dominance": 4 if food_rendered else 0,
                "reading_flow": (
                    ["food_hero", "title", "product", "callouts", "gallery"]
                    if food_rendered else ["title", "product", "callouts", "gallery"]
                ),
            },
            "3_typography_grammar": {
                "title": "heavy_condensed_caps", "case": "upper",
                "escalation": "per_line", "contrast": "high",
            },
            "4_color_grammar": {
                "field": "white", "accent": RED, "accent_role": "dominant_ink",
                "coupling": "warm_food<->red_title" if food_rendered else "red_title_led",
            },
            "5_asset_relationship": (
                "product+lifestyle_scene+annotations+matrix" if food_rendered
                else "product+annotations+matrix"
            ),
            "6_region_rhythm": {
                "sections": 6, "cadence": "loud_to_quiet",
                "whitespace": "high", "density_contrast": True,
            },
            "7_surface_language": {"primary": "white_editorial_field", "header": "dark_header"},
            "8_marketing_signal": (
                ["campaign_headline"]
                + (["availability_badge"] if inputs.sku_text else [])
                + (["cta_display"] if inputs.cta_label else [])
            ),
            "9_evidence_annotation": {
                "style": "dashed_radial_callout",
                "contract_nodes": CATALOG_HERO_MAX_ANNOTATIONS,
                "rendered_nodes": len(inputs.annotation_labels),
            },
            "10_beauty_tokens": {
                "background": "flat_white", "shadow": "product_contact_only",
                "header_texture": "hex", "accent_shapes": "red",
            },
            "11_content_density": "campaign_hero",
            "12_replication_risk": {
                "family_defining": ["1_composition_archetype", "6_region_rhythm", "11_content_density"],
                "owner_gated": ["5_asset_relationship(food_hero)", "8_marketing_signal"],
                "frozen": ["9_evidence_annotation(count=3)"],
            },
        },
        "invariants": [
            "hero.mass>=product.mass" if food_rendered else "product_is_primary_anchor",
            "title_in_product_lane",
            "gallery_isolated_on_white",
        ],
    }


def build_contract_review(
    inputs: CatalogHeroInputs,
    *,
    food_rendered: bool,
    engine: str,
    degraded: bool,
) -> dict:
    """catalog_hero_contract_review — structure completeness, slot rendering, frozen-truth
    evidence (annotation clamp, food-hero gating, display-only CTA, no AI runtime asset)."""
    brand_anchor = bool(inputs.logo) or bool(inputs.brand_name.strip())
    title_ok = bool(inputs.title.strip())
    product_ok = inputs.product is not None
    structure_complete = brand_anchor and title_ok and product_ok

    requested_features = len([f for f in inputs.features if f and f.strip()])
    rendered_annotations = len(inputs.annotation_labels)

    missing = []
    if not title_ok:
        missing.append("title_slot")
    if not product_ok:
        missing.append("product_image_slot")

    return {
        "family": CATALOG_HERO_FAMILY,
        "template_id": CATALOG_HERO_TEMPLATE_ID,
        "variant_id": "catalog_hero_v1",
        "render_engine_used": engine,
        "degraded": degraded,
        "canvas": {"w": CANVAS_W, "h": CANVAS_H, "orientation": "portrait"},
        "structure_complete": structure_complete,
        "missing_required_slots": missing,
        "core_information_area": {
            "brand_anchor_rendered": brand_anchor,
            "title_rendered": title_ok,
            "product_primary_rendered": product_ok,
        },
        "slots": {
            "brand_logo_slot": {"rendered": bool(inputs.logo)},
            "brand_text_slot": {"rendered": bool(inputs.brand_name.strip())},
            "partner_text_slot": {"rendered": bool(inputs.partner_name.strip())},
            "title_slot": {"rendered": title_ok},
            "subtitle_slot": {"rendered": bool(inputs.subtitle.strip())},
            "product_image_slot": {"rendered": product_ok},
            "gallery_item_slot": {"rendered_count": len(inputs.gallery), "max": 4},
            "sku_meta_slot": {"rendered": bool(inputs.sku_text.strip())},
        },
        "food_hero_slot": {
            "rendered": food_rendered,
            "source": inputs.food_hero_source,          # operator_upload | absent
            "owner_gated": True,
            "composition_mode": "dual_co_anchor" if food_rendered else "product_led",
        },
        "annotation_contract": {
            "annotation_slot_ids": [
                "product_annotation_slot_1",
                "product_annotation_slot_2",
                "product_annotation_slot_3",
            ],
            "max_slots": CATALOG_HERO_MAX_ANNOTATIONS,
            "requested_feature_count": requested_features,
            "rendered_annotation_count": rendered_annotations,
            "annotation_clamp_applied": requested_features > CATALOG_HERO_MAX_ANNOTATIONS,
        },
        "on_poster_cta_text": {
            "label": inputs.cta_label,
            "email": inputs.cta_email,
            "rendered": bool(inputs.cta_label.strip() or inputs.cta_email.strip()),
            "render_kind": "display_text_only",
            "cta_action_bound": False,
            "stage3_send_untouched": True,
        },
        "ai_runtime_asset_used": False,
    }


# ------------------------------------------------------------------------- HTML render --
def build_html(inputs: CatalogHeroInputs, *, food_rendered: bool) -> str:
    logo_html = ""
    if inputs.logo is not None:
        logo_html = f'<img class="logo" src="{_data_url(inputs.logo.convert("RGBA"), fmt="PNG")}">'

    product = _whiten_bg(_trim_white(inputs.product), lo=224) if inputs.product else None
    product_uri = _data_url(product) if product is not None else ""

    food_block = ""
    if food_rendered and inputs.food_hero is not None:
        food_uri = _data_url(_cover(_warm(inputs.food_hero), 406, 846))
        food_block = f'<div class="food" style="background-image:url(\'{food_uri}\')"></div>'

    # product placement shifts left into the hero lane when food is absent (product_led)
    product_left = 640 if food_rendered else 430
    product_w = 452 if food_rendered else 560

    # callouts (<=3 frozen) — dashed radial leaders + red node
    labels = inputs.annotation_labels
    anchors = [(690, 560, 506, "left"), (1058, 600, 686, "right"), (700, 760, 854, "left")]
    svg_lines, label_divs = [], []
    for i, text in enumerate(labels):
        ax, ay, ly, side = anchors[i]
        if side == "left":
            label_left, label_w, ta, x_end = 300, 170, "right", product_left - 28
        else:
            label_left, label_w, ta, x_end = product_left + product_w + 28, 160, "left", product_left + product_w + 20
        cx = (x_end + ax) / 2 + (-20 if side == "left" else 20)
        cy = (ly + 12 + ay) / 2 - 16
        svg_lines.append(
            f'<path d="M {x_end} {ly+12} Q {cx:.0f} {cy:.0f} {ax} {ay}" stroke="{INK}" '
            f'stroke-width="1.3" stroke-dasharray="2.5 4" fill="none" opacity="0.72"/>'
            f'<circle cx="{ax}" cy="{ay}" r="5.5" fill="{RED}"/>'
            f'<circle cx="{ax}" cy="{ay}" r="10" fill="none" stroke="{RED}" stroke-width="1" opacity="0.35"/>'
        )
        label_divs.append(
            f'<div class="callout" style="left:{label_left}px;top:{ly}px;width:{label_w}px;'
            f'text-align:{ta}">{_esc(text)}</div>'
        )

    # gallery — isolated-on-white, escalating scale, caption = name
    g_html = ""
    n = len(inputs.gallery)
    for i, gi in enumerate(inputs.gallery[:4]):
        scale = 0.74 + 0.12 * i
        g_uri = _data_url(_whiten_bg(_trim_white(gi), lo=224))
        cap = ""
        g_html += (
            f'<div class="g-item"><div class="g-img" style="height:330px">'
            f'<img src="{g_uri}" style="max-width:{int(300*scale)}px;max-height:{int(300*scale)}px"></div>'
            f'<div class="g-cap">{_esc(cap)}</div></div>'
        )

    title_lines = "<br>".join(_esc(l) for l in _title_lines(inputs.title))
    partner = ""
    if inputs.partner_name.strip():
        partner = (
            f'<div class="partner"><div class="mk"><span></span></div>'
            f'<div class="wm"><div class="a">{_esc(inputs.partner_name.upper())}</div>'
            f'<div class="b">DISTRIBUTION&nbsp;PRO</div></div></div>'
        )
    sku = f'<div class="sku">{_esc(inputs.sku_text)}</div>' if inputs.sku_text.strip() else ""
    restated = (
        f'<h2>{_esc(inputs.title.upper())}</h2>' if inputs.title.strip() else ""
    )
    subtitle = f'<div class="sub">{_esc(inputs.subtitle.upper())}</div>' if inputs.subtitle.strip() else ""
    contact_bits = " · ".join(b for b in [inputs.cta_label, inputs.cta_email] if b.strip())
    contact = f'<div class="contact"><div class="line">{_esc(contact_bits)}</div></div>' if contact_bits else ""

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{_font_face()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:#fff}}
#poster-root{{position:relative;width:{CANVAS_W}px;height:{CANVAS_H}px;background:#fff;
  font-family:'Helvetica Neue',Arial,'NotoSC',sans-serif;overflow:hidden}}
.header{{position:absolute;top:0;left:0;width:{CANVAS_W}px;height:120px;background:{CHARCOAL};
  background-image:url("{_hex_pattern_uri()}");background-repeat:repeat;
  display:flex;align-items:center;justify-content:space-between;padding:0 52px}}
.header .brand{{position:relative;display:flex;align-items:center;gap:16px}}
.header .emblem{{width:46px;height:52px;background:{RED};
  clip-path:polygon(50% 0,100% 27%,100% 73%,50% 100%,0 73%,0 27%)}}
.header .bname{{color:#fff;font-weight:800;font-size:26px;letter-spacing:2px}}
.header img.logo{{height:50px;filter:brightness(0) invert(1)}}
.header .partner{{display:flex;align-items:center;gap:11px}}
.header .partner .mk{{width:36px;height:36px;border:2px solid #cfd2d6;border-radius:7px;
  display:flex;align-items:center;justify-content:center}}
.header .partner .mk span{{display:block;width:15px;height:15px;border:2px solid {RED};border-radius:50%}}
.header .partner .wm .a{{color:#fff;font-size:18px;font-weight:800;letter-spacing:2px}}
.header .partner .wm .b{{color:{STEEL};font-size:10px;letter-spacing:3px}}
.header .accent{{height:5px;background:{RED};position:absolute;left:0;bottom:0;width:{CANVAS_W}px}}
.food{{position:absolute;left:0;top:125px;width:406px;height:846px;
  background-size:cover;background-position:center}}
.title{{position:absolute;left:462px;top:146px;width:770px}}
.title h1{{color:{RED};font-family:'Anton','Arial Narrow',sans-serif;font-weight:400;
  text-transform:uppercase;font-size:108px;line-height:.80;letter-spacing:-2px;
  transform:skewX(-9deg) scaleX(.96);transform-origin:left}}
.sku{{position:absolute;left:462px;top:120px;color:{RED};font-weight:700;font-size:18px;letter-spacing:1px}}
.product{{position:absolute;left:{product_left}px;top:498px;width:{product_w}px;height:444px}}
.product img{{width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 12px 16px rgba(0,0,0,.15))}}
.callouts{{position:absolute;left:0;top:0;width:{CANVAS_W}px;height:930px;pointer-events:none}}
.callout{{position:absolute;font-family:'NotoSC','Helvetica Neue',Arial,sans-serif;
  font-size:18px;line-height:1.16;color:{INK};font-weight:600}}
.band{{position:absolute;left:0;top:946px;width:{CANVAS_W}px;text-align:center}}
.band h2{{color:{RED};text-transform:uppercase;font-family:'Anton','Arial Narrow',sans-serif;
  font-weight:400;font-size:72px;letter-spacing:0px}}
.band .sub{{color:#3a3d42;font-size:22px;letter-spacing:2px;margin-top:14px;font-weight:800;text-transform:uppercase}}
.gallery{{position:absolute;left:40px;top:1226px;width:{CANVAS_W-80}px;
  display:flex;justify-content:space-around;align-items:flex-end;gap:14px}}
.g-item{{flex:1;text-align:center}}
.g-img{{display:flex;align-items:flex-end;justify-content:center}}
.g-img img{{object-fit:contain;filter:drop-shadow(0 5px 7px rgba(0,0,0,.07))}}
.g-cap{{font-family:'NotoSC',sans-serif;font-weight:700;color:{INK};font-size:20px;margin-top:14px}}
.contact{{position:absolute;left:0;bottom:26px;width:{CANVAS_W}px;text-align:center}}
.contact .line{{color:#9aa0a8;font-size:14px;letter-spacing:2px;font-weight:600}}
</style></head><body>
<div id="poster-root">
  <div class="header">
    <div class="brand"><div class="emblem"></div>{logo_html}
      <div class="bname">{_esc(inputs.brand_name.upper())}</div></div>
    {partner}
    <div class="accent"></div></div>
  {food_block}
  {sku}
  <div class="title"><h1>{title_lines}</h1></div>
  <div class="product"><img src="{product_uri}"></div>
  <svg class="callouts" viewBox="0 0 {CANVAS_W} 930">{''.join(svg_lines)}</svg>
  {''.join(label_divs)}
  <div class="band">{restated}{subtitle}</div>
  <div class="gallery">{g_html}</div>
  {contact}
</div></body></html>"""


# ------------------------------------------------------------------ Pillow fallback -----
def _font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(path), size)
    except Exception:
        return ImageFont.load_default()


def render_pillow_fallback(inputs: CatalogHeroInputs, *, food_rendered: bool) -> PILImage.Image:
    """Deterministic, Chromium-free render of the same portrait region rhythm (lower
    fidelity). Used when Playwright/Chromium is unavailable; flagged degraded."""
    im = PILImage.new("RGB", (CANVAS_W, CANVAS_H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    title_font = _font(_ANTON if _ANTON.exists() else _NOTO_SB, 104)
    band_font = _font(_ANTON if _ANTON.exists() else _NOTO_SB, 64)
    body = _font(_NOTO_SB, 22)
    small = _font(_NOTO_R, 18)

    # header
    d.rectangle([0, 0, CANVAS_W, 120], fill=(31, 32, 36))
    d.polygon([(104, 36), (128, 47), (128, 73), (104, 84), (80, 73), (80, 47)], fill=(225, 0, 42))
    d.text((150, 46), inputs.brand_name.upper(), font=_font(_NOTO_SB, 26), fill=(255, 255, 255))
    if inputs.partner_name.strip():
        t = inputs.partner_name.upper()
        d.text((CANVAS_W - 52 - d.textlength(t, font=body), 50), t, font=body, fill=(255, 255, 255))
    d.rectangle([0, 116, CANVAS_W, 120], fill=(225, 0, 42))

    # food co-anchor
    if food_rendered and inputs.food_hero is not None:
        im.paste(_cover(_warm(inputs.food_hero), 406, 846), (0, 125))

    # title (red caps)
    ty = 150
    for line in _title_lines(inputs.title):
        d.text((462, ty), line, font=title_font, fill=(225, 0, 42))
        ty += 92
    if inputs.sku_text.strip():
        d.text((462, 122), inputs.sku_text, font=small, fill=(225, 0, 42))

    # product
    if inputs.product is not None:
        p = _whiten_bg(_trim_white(inputs.product), lo=224)
        pw, ph = (452, 444) if food_rendered else (560, 460)
        px = 640 if food_rendered else 430
        p.thumbnail((pw, ph), PILImage.LANCZOS)
        im.paste(p, (px + (pw - p.width) // 2, 498 + (ph - p.height) // 2))

    # callouts (<=3)
    anchors = [(690, 560, 300, 506, "r"), (1058, 600, 1040, 686, "l"), (700, 760, 300, 854, "r")]
    for i, label in enumerate(inputs.annotation_labels):
        ax, ay, lx, ly, side = anchors[i]
        d.ellipse([ax - 6, ay - 6, ax + 6, ay + 6], fill=(225, 0, 42))
        anc = "right" if side == "r" else "left"
        tx = lx + 160 - d.textlength(label, font=body) if side == "r" else lx
        d.line([(lx + 160 if side == "r" else lx, ly + 10), (ax, ay)], fill=(38, 38, 38), width=1)
        d.text((tx, ly), label, font=body, fill=(38, 38, 38))

    # restated band + strapline
    if inputs.title.strip():
        t = inputs.title.upper()
        d.text(((CANVAS_W - d.textlength(t, font=band_font)) / 2, 960), t, font=band_font, fill=(225, 0, 42))
    if inputs.subtitle.strip():
        t = inputs.subtitle.upper()
        d.text(((CANVAS_W - d.textlength(t, font=body)) / 2, 1120), t, font=body, fill=(58, 61, 66))

    # gallery
    gal = list(inputs.gallery[:4])
    if gal:
        slot_w = (CANVAS_W - 80) // len(gal)
        for i, gi in enumerate(gal):
            g = _whiten_bg(_trim_white(gi), lo=224)
            scale = int(240 * (0.74 + 0.12 * i))
            g.thumbnail((scale, scale), PILImage.LANCZOS)
            gx = 40 + i * slot_w + (slot_w - g.width) // 2
            im.paste(g, (gx, 1556 - g.height))

    contact_bits = " · ".join(b for b in [inputs.cta_label, inputs.cta_email] if b.strip())
    if contact_bits:
        d.text(((CANVAS_W - d.textlength(contact_bits, font=small)) / 2, 1700), contact_bits,
               font=small, fill=(154, 160, 168))
    return im


# ------------------------------------------------------------------------ render API ----
async def render_catalog_hero_async(inputs: CatalogHeroInputs) -> CatalogHeroRenderResult:
    food_rendered = inputs.food_hero is not None
    grammar = build_grammar_profile(inputs, food_rendered=food_rendered)
    engine = "pillow_fallback"
    degraded = True
    image: Optional[PILImage.Image] = None
    try:
        from playwright.async_api import async_playwright

        html = build_html(inputs, food_rendered=food_rendered)
        async with async_playwright() as pw:
            b = await pw.chromium.launch(
                headless=True, args=["--disable-dev-shm-usage", "--font-render-hinting=none"]
            )
            page = await b.new_page(viewport={"width": CANVAS_W, "height": CANVAS_H}, device_scale_factor=2)
            await page.set_content(html, wait_until="networkidle")
            await page.locator("#poster-root").wait_for(state="visible")
            png = await page.locator("#poster-root").screenshot(type="png")
            await b.close()
        image = PILImage.open(BytesIO(png)).convert("RGB")
        engine, degraded = "chromium", False
    except Exception:
        image = render_pillow_fallback(inputs, food_rendered=food_rendered)
        engine, degraded = "pillow_fallback", True

    contract = build_contract_review(inputs, food_rendered=food_rendered, engine=engine, degraded=degraded)
    return CatalogHeroRenderResult(
        image=image, engine=engine, degraded=degraded,
        grammar_profile=grammar, contract_review=contract,
    )


def render_catalog_hero(inputs: CatalogHeroInputs) -> CatalogHeroRenderResult:
    """Sync wrapper. Prefers Chromium; falls back to Pillow. Safe to call outside an event loop."""
    import asyncio

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(render_catalog_hero_async(inputs))
    # already in a loop (shouldn't happen in sync callers) — use the pillow path directly
    food_rendered = inputs.food_hero is not None
    image = render_pillow_fallback(inputs, food_rendered=food_rendered)
    return CatalogHeroRenderResult(
        image=image, engine="pillow_fallback", degraded=True,
        grammar_profile=build_grammar_profile(inputs, food_rendered=food_rendered),
        contract_review=build_contract_review(inputs, food_rendered=food_rendered, engine="pillow_fallback", degraded=True),
    )


# ------------------------------------------------------------ endpoint input resolver ---
def resolve_inputs(
    *,
    brand_name: str,
    agent_name: str,
    title: str,
    subtitle: str,
    sku_text: str,
    features: Sequence[str],
    cta_label: str,
    cta_email: str,
    logo: Optional[PILImage.Image],
    product: Optional[PILImage.Image],
    scenario_image: Optional[PILImage.Image],
    gallery_images: Sequence[PILImage.Image],
) -> CatalogHeroInputs:
    """Build CatalogHeroInputs from already-resolved PIL assets. The food hero is
    owner-gated: rendered ONLY from the operator scenario_image (never AI)."""
    return CatalogHeroInputs(
        brand_name=brand_name or "",
        partner_name=agent_name or "",
        title=title or "",
        subtitle=subtitle or "",
        sku_text=sku_text or "",
        features=tuple(f for f in (features or ()) if f),
        cta_label=cta_label or "",
        cta_email=cta_email or "",
        logo=logo,
        product=product,
        food_hero=scenario_image,
        food_hero_source="operator_upload" if scenario_image is not None else "absent",
        gallery=tuple(gallery_images or ()),
    )
