"""Additive portrait family: email_campaign_composite_v1 (Campaign Explainer composite).

Productizes the validated P2 case_001 Campaign Explainer design (~4.75/5). ADDITIVE and ISOLATED — it
does NOT alter Family A/B, Product Sheet, Catalog Hero, the shared PosterPipeline / RendererSelector, or
Stage1/2/3. Rendered by this dedicated module (mirroring app/services/poster2/catalog_hero.py).

Layered runtime contract (6 regions):
  banner_region          — deterministic charcoal hex header + white logo chip + red accent
  campaign_visual_region — operator-gated visual atmosphere SUBSTRATE only (never business truth)
  truth_overlay_region   — deterministic title / product hero / 3 callouts / EF132V spec strip
  restated_band_region   — deterministic restated title + strapline
  gallery_region         — deterministic product gallery
  footer_region          — deterministic CUISTANCE contact

Truth invariants: logo / product / title / callouts / spec / strapline / contact are ALWAYS deterministic.
The campaign substrate is operator-gated/candidate-only and is NEVER treated as business truth. The
thermostat default is the evidence-backed "jusqu'à 190°C" — the unsupported "0–200°C" is forbidden as a
default. No Technitalia / Codimatel / gas-stove / target-email business truth may appear.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from typing import Optional, Sequence

from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont

from . import catalog_hero as ch  # read-only reuse of asset/font helpers + canvas/colour tokens

CAMPAIGN_COMPOSITE_FAMILY = "campaign_composite_portrait"
EMAIL_CAMPAIGN_COMPOSITE_TEMPLATE_ID = "email_campaign_composite_v1"
EMAIL_CAMPAIGN_COMPOSITE_TEMPLATE_VERSION = "1.0.0"
EMAIL_CAMPAIGN_COMPOSITE_CONTRACT_VERSION = "poster2.email_campaign_composite_v1.v1"

CANVAS_W, CANVAS_H = ch.CANVAS_W, ch.CANVAS_H  # 1240 x 1754
RED, CHARCOAL, INK = ch.RED, ch.CHARCOAL, ch.INK
MAX_CALLOUTS = 3

RUNTIME_CONTRACT_REGIONS = (
    "banner_region", "campaign_visual_region", "truth_overlay_region",
    "restated_band_region", "gallery_region", "footer_region",
)

# Case001 productionized deterministic truth defaults (evidence-backed / owner-approved).
CASE001_DEFAULT_TRUTH = {
    "brand_name": "",  # the CUISTANCE wordmark logo carries the brand; empty text avoids a double mark
    "title": "Les Friteuses Électriques",
    "strapline": "Cuisson professionnelle, croustillant maîtrisé",
    "callouts": (
        "2 cuves inox amovibles",
        "Thermostat réglable jusqu'à 190°C",          # evidence-backed (Planche p09). NOT "0–200°C".
        "Construction inox / usage professionnel",
    ),
    "spec_row": "RÉF. EF132V · 2 cuves 13 + 13 L · 3 + 3 kW / 230 V · L630 × P520 × H345 mm",
    "product_ref": "EF132V",
    "product_ref_owner_review": True,                 # EF132V vs EF102V image↔ref confirmation pending
    "contact": "commercial@cuistance.eu · +33 (0)1 71 84 11 20 · cuistance-europe.com",
}

# A default that contains any of these (case-insensitive) is a truth-leak and is rejected by the gate.
FORBIDDEN_TRUTH_TOKENS = (
    "technitalia", "codimatel", "réchaud", "rechaud", "gas stove", "réchauds gaz",
    "kaly@", "0–200°c", "0-200°c", "0 – 200", "0-200",
)

# ---- P2 polished geometry ----
FOOD_W, SEAM_FEATHER = 392, 150
HERO_TOP, HERO_BOT = 130, 980
P_LEFT, P_W, P_TOP, P_H = 648, 432, 498, 438
TITLE_LEFT, TITLE_TOP, TITLE_W = 548, 150, 660
SPEC_TOP = 884
_CALLOUTS = (  # (idx, side, label_x, label_w, anchor_x, anchor_y, label_y)
    (0, "left", 448, 150, P_LEFT, 560, 548),
    (1, "right", 1098, 132, P_LEFT + P_W, 612, 600),
    (2, "left", 448, 165, P_LEFT, 812, 800),
)


@dataclass
class EmailCampaignCompositeInputs:
    """Resolved inputs. Business truth is deterministic; the substrate is operator-gated."""
    title: str = CASE001_DEFAULT_TRUTH["title"]
    strapline: str = CASE001_DEFAULT_TRUTH["strapline"]
    callouts: tuple[str, ...] = CASE001_DEFAULT_TRUTH["callouts"]
    spec_row: str = CASE001_DEFAULT_TRUTH["spec_row"]
    contact: str = CASE001_DEFAULT_TRUTH["contact"]
    logo: Optional[PILImage.Image] = None
    product: Optional[PILImage.Image] = None              # required (truth_overlay product hero)
    gallery: tuple[PILImage.Image, ...] = ()
    substrate: Optional[PILImage.Image] = None            # operator-gated campaign visual; NEVER truth
    substrate_source: str = "absent"                      # operator_upload | absent (never "ai_generated")

    @property
    def callout_labels(self) -> list[str]:
        return [c for c in self.callouts if c and c.strip()][:MAX_CALLOUTS]


@dataclass
class EmailCampaignCompositeResult:
    image: PILImage.Image
    engine: str                                           # "chromium" | "pillow_fallback"
    degraded: bool
    contract_review: dict
    timings_ms: dict = field(default_factory=dict)


def resolve_inputs(
    *,
    title: Optional[str] = None,
    strapline: Optional[str] = None,
    callouts: Optional[Sequence[str]] = None,
    spec_row: Optional[str] = None,
    contact: Optional[str] = None,
    logo: Optional[PILImage.Image] = None,
    product: Optional[PILImage.Image] = None,
    gallery_images: Optional[Sequence[PILImage.Image]] = None,
    substrate_image: Optional[PILImage.Image] = None,     # operator-supplied candidate atmosphere only
) -> EmailCampaignCompositeInputs:
    """Build inputs from operator payload, defaulting to the case001 deterministic truth. The substrate
    is operator-gated: provided -> 'operator_upload'; never AI-sourced in runtime truth."""
    return EmailCampaignCompositeInputs(
        title=title or CASE001_DEFAULT_TRUTH["title"],
        strapline=strapline or CASE001_DEFAULT_TRUTH["strapline"],
        callouts=tuple(callouts) if callouts else CASE001_DEFAULT_TRUTH["callouts"],
        spec_row=spec_row or CASE001_DEFAULT_TRUTH["spec_row"],
        contact=contact or CASE001_DEFAULT_TRUTH["contact"],
        logo=logo, product=product,
        gallery=tuple(gallery_images or ()),
        substrate=substrate_image,
        substrate_source="operator_upload" if substrate_image is not None else "absent",
    )


def business_truth_lock(inputs: EmailCampaignCompositeInputs) -> dict:
    """Deterministic, evidence-backed truth + leakage verdict. Used by the contract review + tests."""
    fields = {
        "title": inputs.title, "strapline": inputs.strapline,
        "callouts": list(inputs.callout_labels), "spec_row": inputs.spec_row, "contact": inputs.contact,
    }
    blob = " ".join([fields["title"], fields["strapline"], fields["spec_row"], fields["contact"],
                     *fields["callouts"]]).lower()
    leaks = sorted({t for t in FORBIDDEN_TRUTH_TOKENS if t in blob})
    return {
        "brand": "CUISTANCE",
        "product_ref": CASE001_DEFAULT_TRUTH["product_ref"],
        "product_ref_owner_review": CASE001_DEFAULT_TRUTH["product_ref_owner_review"],
        "fields": fields,
        "thermostat_uses_unsupported_0_200C": ("0–200" in blob or "0-200" in blob),
        "target_business_leakage_tokens": leaks,
        "leakage_clean": not leaks,
        "ai_substrate_is_truth": False,
        "substrate_source": inputs.substrate_source,
    }


def build_contract_review(inputs: EmailCampaignCompositeInputs, *, engine: str, degraded: bool) -> dict:
    product_ok = inputs.product is not None
    title_ok = bool(inputs.title.strip())
    missing = []
    if not product_ok:
        missing.append("product_slot")
    if not title_ok:
        missing.append("title_slot")
    truth = business_truth_lock(inputs)
    structure_complete = product_ok and title_ok and truth["leakage_clean"] and not truth["thermostat_uses_unsupported_0_200C"]
    return {
        "template_id": EMAIL_CAMPAIGN_COMPOSITE_TEMPLATE_ID,
        "contract_version": EMAIL_CAMPAIGN_COMPOSITE_CONTRACT_VERSION,
        "regions": list(RUNTIME_CONTRACT_REGIONS),
        "structure_complete": structure_complete,
        "missing_required_slots": missing,
        "callout_count": len(inputs.callout_labels),
        "callout_ceiling": MAX_CALLOUTS,
        "business_truth": truth,
        "ai_runtime_asset_used": False,                   # substrate is operator-gated, never AI in runtime
        "engine": engine, "degraded": degraded,
    }


# ------------------------------------------------------------------------- HTML build ----
def _title_html(title: str) -> str:
    lines = ch._title_lines(title) or [title.upper()]
    maxlen = max(len(x) for x in lines)
    size = int(min(120, max(60, TITLE_W / (maxlen * 0.55))))
    return "".join(
        f'<div class="tl" style="font-size:{size}px;color:{RED if (len(lines) >= 2 and i == 1) else INK}">'
        f'{ch._esc(ln)}</div>' for i, ln in enumerate(lines))


def _callouts_html(labels: list[str]) -> tuple[str, str]:
    svg, divs = [], []
    for idx, side, lx, lw, ax, ay, ly in _CALLOUTS:
        if idx >= len(labels):
            continue
        text = labels[idx]
        x_end = lx + lw if side == "left" else lx
        cx = (x_end + ax) / 2 + (-18 if side == "left" else 18)
        cy = (ly + 12 + ay) / 2 - 14
        svg.append(
            f'<path d="M {x_end} {ly+12} Q {cx:.0f} {cy:.0f} {ax} {ay}" stroke="{INK}" stroke-width="1.3" '
            f'stroke-dasharray="2.5 4" fill="none" opacity="0.72"/><circle cx="{ax}" cy="{ay}" r="5.5" '
            f'fill="{RED}"/><circle cx="{ax}" cy="{ay}" r="10" fill="none" stroke="{RED}" stroke-width="1" opacity="0.35"/>')
        ta = "right" if side == "left" else "left"
        divs.append(f'<div class="co" style="left:{lx}px;top:{ly}px;width:{lw}px;text-align:{ta}">{ch._esc(text)}</div>')
    return "".join(svg), "".join(divs)


def build_html(inputs: EmailCampaignCompositeInputs) -> str:
    W, H = CANVAS_W, CANVAS_H
    logo_html = ""
    if inputs.logo is not None:
        logo_html = f'<div class="logochip"><img src="{ch._data_url(ch._trim_white(inputs.logo).convert("RGBA"), fmt="PNG")}"></div>'
    product_uri = ch._data_url(ch._whiten_bg(ch._trim_white(inputs.product), lo=224)) if inputs.product else ""
    # campaign_visual_region: operator-gated substrate (else a flat warm field — still deterministic, no AI)
    if inputs.substrate is not None:
        sub_uri = ch._data_url(ch._cover(ch._warm(inputs.substrate), FOOD_W + SEAM_FEATHER, HERO_BOT - HERO_TOP))
        food_bg = f"#111 url('{sub_uri}') left center/cover"
    else:
        food_bg = "linear-gradient(160deg,#3a2417,#7a3a16 60%,#b8682a)"
    svg, callout_divs = _callouts_html(inputs.callout_labels)
    spec = f'<div class="specstrip">{ch._esc(inputs.spec_row)}</div>' if inputs.spec_row.strip() else ""
    g_html = ""
    for i, gp in enumerate(list(inputs.gallery)[:3]):
        sc = 0.78 + 0.12 * i
        gu = ch._data_url(ch._whiten_bg(ch._trim_white(gp), lo=224))
        g_html += f'<div class="gi"><img src="{gu}" style="max-width:{int(300*sc)}px;max-height:{int(300*sc)}px"></div>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{ch._font_face()}
*{{margin:0;padding:0;box-sizing:border-box}} html,body{{background:#fff}}
#poster-root{{position:relative;width:{W}px;height:{H}px;background:#fff;overflow:hidden;font-family:'Helvetica Neue',Arial,'NotoSC',sans-serif}}
.header{{position:absolute;top:0;left:0;width:{W}px;height:130px;background:{CHARCOAL};background-image:url("{ch._hex_pattern_uri()}");background-repeat:repeat;display:flex;align-items:center;padding:0 48px;gap:18px}}
.emblem{{width:46px;height:52px;background:{RED};clip-path:polygon(50% 0,100% 27%,100% 73%,50% 100%,0 73%,0 27%)}}
.logochip{{background:#fff;border-radius:10px;padding:11px 18px;box-shadow:0 4px 12px rgba(0,0,0,.35)}} .logochip img{{height:44px;display:block}}
.accent{{position:absolute;left:0;bottom:0;width:{W}px;height:6px;background:{RED}}}
.food{{position:absolute;left:0;top:{HERO_TOP}px;width:{FOOD_W+SEAM_FEATHER}px;height:{HERO_BOT-HERO_TOP}px;background:{food_bg}}}
.food:after{{content:'';position:absolute;inset:0;background:linear-gradient(90deg,rgba(255,255,255,0) 40%,rgba(255,255,255,.45) 66%,rgba(255,255,255,.85) 86%,#fff 100%)}}
.title{{position:absolute;left:{TITLE_LEFT}px;top:{TITLE_TOP}px;width:{TITLE_W}px}}
.tl{{font-family:'Anton','Arial Narrow',sans-serif;text-transform:uppercase;line-height:.90;letter-spacing:-1px;transform:skewX(-9deg) scaleX(.97);transform-origin:left;white-space:nowrap}}
.product{{position:absolute;left:{P_LEFT}px;top:{P_TOP}px;width:{P_W}px;height:{P_H}px}} .product img{{width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 12px 16px rgba(0,0,0,.16))}}
.callouts{{position:absolute;left:0;top:0;width:{W}px;height:990px;pointer-events:none}}
.co{{position:absolute;font-family:'NotoSC','Helvetica Neue',Arial,sans-serif;font-size:18px;line-height:1.16;color:{INK};font-weight:700}}
.specstrip{{position:absolute;left:200px;top:{SPEC_TOP}px;width:{W-400}px;height:60px;background:#f4f5f7;border-radius:12px;display:flex;align-items:center;justify-content:center;box-shadow:inset 0 0 0 1px #e6e8ec;font-family:'NotoSC',Arial,sans-serif;font-weight:800;font-size:19px;color:{INK};letter-spacing:.5px}}
.band{{position:absolute;left:0;top:992px;width:{W}px;text-align:center}}
.band h2{{color:{RED};font-family:'Anton','Arial Narrow',sans-serif;text-transform:uppercase;font-weight:400;font-size:70px;letter-spacing:0}}
.band .sub{{color:#3a3d42;font-size:23px;letter-spacing:2px;margin-top:14px;font-weight:800;text-transform:uppercase}}
.gallery{{position:absolute;left:40px;top:1252px;width:{W-80}px;height:316px;display:flex;justify-content:space-around;align-items:flex-end;gap:14px}}
.gi{{flex:1;text-align:center}} .gi img{{object-fit:contain;filter:drop-shadow(0 5px 7px rgba(0,0,0,.08))}}
.contact{{position:absolute;left:0;bottom:28px;width:{W}px;text-align:center;color:#9aa0a8;font-size:15px;letter-spacing:2px;font-weight:600}}
</style></head><body><div id="poster-root">
  <div class="header"><div class="emblem"></div>{logo_html}<div class="accent"></div></div>
  <div class="food"></div><div class="title">{_title_html(inputs.title)}</div>
  <div class="product"><img src="{product_uri}"></div>
  <svg class="callouts" viewBox="0 0 {W} 990">{svg}</svg>{callout_divs}{spec}
  <div class="band"><h2>{ch._esc(inputs.title.upper())}</h2><div class="sub">{ch._esc(inputs.strapline.upper())}</div></div>
  <div class="gallery">{g_html}</div>
  <div class="contact">{ch._esc(inputs.contact)}</div>
</div></body></html>"""


# ----------------------------------------------------------------- Pillow fallback ----
def render_pillow_fallback(inputs: EmailCampaignCompositeInputs) -> PILImage.Image:
    """Chromium-free deterministic render (lower fidelity) so an artifact is always produced offline."""
    W, H = CANVAS_W, CANVAS_H
    im = PILImage.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    title_font = ch._font(ch._ANTON if ch._ANTON.exists() else ch._NOTO_SB, 96)
    band_font = ch._font(ch._ANTON if ch._ANTON.exists() else ch._NOTO_SB, 60)
    body = ch._font(ch._NOTO_SB, 22)
    small = ch._font(ch._NOTO_R, 16)
    # banner
    d.rectangle([0, 0, W, 130], fill=(31, 32, 36))
    d.polygon([(70, 39), (94, 50), (94, 76), (70, 87), (46, 76), (46, 50)], fill=(225, 0, 42))
    if inputs.logo is not None:
        chip = ch._trim_white(inputs.logo); chip.thumbnail((220, 48))
        d.rectangle([110, 38, 110 + chip.width + 24, 38 + chip.height + 22], fill=(255, 255, 255))
        im.paste(chip, (122, 49))
    d.rectangle([0, 124, W, 130], fill=(225, 0, 42))
    # campaign substrate (operator-gated)
    if inputs.substrate is not None:
        im.paste(ch._cover(ch._warm(inputs.substrate), FOOD_W, HERO_BOT - HERO_TOP), (0, HERO_TOP))
    # title
    ty = TITLE_TOP
    for i, ln in enumerate(ch._title_lines(inputs.title)):
        d.text((TITLE_LEFT, ty), ln, font=title_font, fill=(225, 0, 42) if i == 1 else (38, 38, 38)); ty += 92
    # product
    if inputs.product is not None:
        p = ch._whiten_bg(ch._trim_white(inputs.product), lo=224); p.thumbnail((P_W, P_H))
        im.paste(p, (P_LEFT + (P_W - p.width) // 2, P_TOP + (P_H - p.height) // 2))
    # callouts
    for idx, side, lx, lw, ax, ay, ly in _CALLOUTS:
        if idx < len(inputs.callout_labels):
            d.ellipse([ax - 5, ay - 5, ax + 5, ay + 5], fill=(225, 0, 42))
            d.text((lx, ly), inputs.callout_labels[idx], font=body, fill=(38, 38, 38))
    # spec strip
    if inputs.spec_row.strip():
        d.rectangle([200, SPEC_TOP, W - 200, SPEC_TOP + 60], fill=(244, 245, 247))
        d.text((W / 2 - d.textlength(inputs.spec_row, font=body) / 2, SPEC_TOP + 18), inputs.spec_row, font=body, fill=(38, 38, 38))
    # band + strapline
    t = inputs.title.upper()
    d.text(((W - d.textlength(t, font=band_font)) / 2, 1000), t, font=band_font, fill=(225, 0, 42))
    s = inputs.strapline.upper()
    d.text(((W - d.textlength(s, font=body)) / 2, 1110), s, font=body, fill=(58, 61, 66))
    # gallery
    gal = list(inputs.gallery)[:3]
    if gal:
        slot = (W - 80) // len(gal)
        for i, gp in enumerate(gal):
            g = ch._whiten_bg(ch._trim_white(gp), lo=224); g.thumbnail((int(240 * (0.78 + 0.12 * i)),) * 2)
            im.paste(g, (40 + i * slot + (slot - g.width) // 2, 1560 - g.height))
    d.text(((W - d.textlength(inputs.contact, font=small)) / 2, 1700), inputs.contact, font=small, fill=(154, 160, 168))
    return im


async def render_async(inputs: EmailCampaignCompositeInputs) -> EmailCampaignCompositeResult:
    engine, degraded = "pillow_fallback", True
    image: Optional[PILImage.Image] = None
    try:
        from playwright.async_api import async_playwright

        html = build_html(inputs)
        async with async_playwright() as pw:
            b = await pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage", "--font-render-hinting=none"])
            page = await b.new_page(viewport={"width": CANVAS_W, "height": CANVAS_H}, device_scale_factor=2)
            await page.set_content(html, wait_until="networkidle")
            await page.locator("#poster-root").wait_for(state="visible")
            png = await page.locator("#poster-root").screenshot(type="png")
            await b.close()
        image = PILImage.open(BytesIO(png)).convert("RGB")
        engine, degraded = "chromium", False
    except Exception:
        image = render_pillow_fallback(inputs)
        engine, degraded = "pillow_fallback", True
    return EmailCampaignCompositeResult(
        image=image, engine=engine, degraded=degraded,
        contract_review=build_contract_review(inputs, engine=engine, degraded=degraded),
    )


def render(inputs: EmailCampaignCompositeInputs) -> EmailCampaignCompositeResult:
    """Sync wrapper. Prefers Chromium; falls back to Pillow. Safe outside an event loop."""
    import asyncio

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(render_async(inputs))
    image = render_pillow_fallback(inputs)
    return EmailCampaignCompositeResult(
        image=image, engine="pillow_fallback", degraded=True,
        contract_review=build_contract_review(inputs, engine="pillow_fallback", degraded=True),
    )
