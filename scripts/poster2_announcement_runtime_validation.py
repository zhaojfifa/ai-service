"""POSTER2-FAMILY-B-ANNOUNCEMENT-RESULT-VALIDATION-V1

Render a Cuistance-style Family B Product Announcement through the EXISTING
/api/v2/generate-poster pipeline path (Pillow operator path — Template B disables
Puppeteer) and save runtime artifacts for visual review.

No runtime contract change. No new slots. Uses only the implemented variant fields.
Run: PYTHONPATH=. ./.venv/bin/python scripts/poster2_announcement_runtime_validation.py
"""
from __future__ import annotations

import asyncio
import json
import os
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from PIL import Image as PILImage, ImageDraw

from app.services.poster2.asset_loader import AssetLoader
from app.services.poster2.background import BackgroundResult, FireflyBackgroundService
from app.services.poster2.composer import Composer
from app.services.poster2.contracts import AssetRef, PosterSpec, ResolvedAssets, StyleSpec, TemplateSpec
from app.services.poster2.pipeline import PosterPipeline
from app.services.poster2.renderer import LayoutRenderer

OUT = Path(os.environ.get("POSTER2_VALIDATION_OUT", "docs/poster2/assets/announcement_runtime_v1"))
OUT.mkdir(parents=True, exist_ok=True)
TEMPLATE_B = Path("app/templates/specs/template_product_sheet_v1.json")


def _rice_cooker_packshot() -> PILImage.Image:
    """A simple, recognizable, portrait commercial rice-cooker silhouette on
    transparent background — lets us judge contain-fit (no distortion)."""
    w, h = 620, 760
    img = PILImage.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body_top, body_bottom = 250, 700
    # stainless body (rounded)
    d.rounded_rectangle([90, body_top, w - 90, body_bottom], radius=60, fill=(206, 209, 214, 255))
    d.rounded_rectangle([90, body_top, w - 90, body_bottom], radius=60, outline=(150, 154, 160, 255), width=3)
    # vertical brushed-steel hint
    for x in range(120, w - 120, 26):
        d.line([(x, body_top + 30), (x, body_bottom - 30)], fill=(190, 193, 198, 120), width=2)
    # lid dome
    d.ellipse([110, 150, w - 110, 330], fill=(232, 234, 237, 255), outline=(150, 154, 160, 255), width=3)
    # lid handle
    d.rounded_rectangle([w // 2 - 70, 150, w // 2 + 70, 188], radius=18, fill=(60, 63, 68, 255))
    # control panel + indicator
    d.rounded_rectangle([w // 2 - 78, 470, w // 2 + 78, 560], radius=14, fill=(40, 42, 46, 255))
    d.ellipse([w // 2 - 12, 500, w // 2 + 12, 524], fill=(214, 64, 52, 255))  # red indicator
    # side handles
    d.rounded_rectangle([54, 430, 96, 540], radius=16, fill=(70, 73, 78, 255))
    d.rounded_rectangle([w - 96, 430, w - 54, 540], radius=16, fill=(70, 73, 78, 255))
    # contact shadow
    d.ellipse([150, 690, w - 150, 730], fill=(0, 0, 0, 40))
    return img


def _logo() -> PILImage.Image:
    w, h = 360, 150
    img = PILImage.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([8, 36, w - 8, h - 36], radius=14, fill=(255, 255, 255, 255), outline=(200, 64, 52, 255), width=4)
    d.text((36, 60), "CUISTANCE", fill=(40, 42, 46, 255))
    d.rectangle([36, 96, 150, 100], fill=(200, 64, 52, 255))
    return img


def _build_spec() -> PosterSpec:
    return PosterSpec(
        brand_name="CUISTANCE",
        agent_name="Cuistance Europe",
        title="NOUVEAUTE ! CUISEUR A RIZ PROFESSIONNEL",
        subtitle="Cuiseur a riz professionnel 10 litres",
        features=(),
        product_image=AssetRef(url="mock://rice-cooker"),
        logo=AssetRef(url="mock://logo"),
        template_id="template_product_sheet_v1",
        renderer_mode="pillow",
        sku_text="311011 (RC10L)",
        description_title="Inox - maintien au chaud 24h",
        description_body=(
            "Structure exterieure en acier inoxydable, revetement interieur "
            "antiadhesif, voyants de cuisson, livre avec cuillere et doseur a riz."
        ),
        availability_badge="EN STOCK",
        tariff_mode="on_request",
        on_poster_cta_label="Nous contacter",
        on_poster_cta_email="commercial@cuistance.eu",
        style=StyleSpec(seed=42),
    )


def _payload_dict(spec: PosterSpec) -> dict:
    """The equivalent /api/v2/generate-poster request body."""
    return {
        "brand_name": spec.brand_name,
        "agent_name": spec.agent_name,
        "title": spec.title,
        "subtitle": spec.subtitle,
        "template_id": spec.template_id,
        "renderer_mode": "pillow",
        "sku_text": spec.sku_text,
        "description_title": spec.description_title,
        "description_body": spec.description_body,
        "availability_badge": spec.availability_badge,
        "tariff_mode": spec.tariff_mode,
        "on_poster_cta_label": spec.on_poster_cta_label,
        "on_poster_cta_email": spec.on_poster_cta_email,
        "product_image": {"url": "https://assets.example/cuistance/rc10l.png"},
        "logo": {"url": "https://assets.example/cuistance/logo.png"},
    }


def main() -> None:
    spec = _build_spec()
    assets = ResolvedAssets(product=_rice_cooker_packshot(), logo=_logo())

    saved: dict[str, bytes] = {}

    def put(*args, **kwargs):
        key = kwargs.get("key") or (args[0] if args else None)
        data = kwargs.get("data") if "data" in kwargs else (args[1] if len(args) > 1 else None)
        if isinstance(data, (bytes, bytearray)):
            saved[key] = bytes(data)
        return f"https://local/{key}"

    bg = MagicMock(spec=FireflyBackgroundService)
    bg.generate = AsyncMock(return_value=BackgroundResult(
        url="https://local/bg.png", key="bg", prompt_used="sheet bg",
        seed_used=42, model="firefly-v3", width=1024, height=1024,
    ))
    loader = MagicMock(spec=AssetLoader)
    loader.load = AsyncMock(return_value=assets)
    loader.load_url = AsyncMock(return_value=PILImage.new("RGB", (1024, 1024), (245, 242, 237)))

    pipe = PosterPipeline(
        background_svc=bg,
        renderer=LayoutRenderer(),
        composer=Composer(),
        asset_loader=loader,
        put_bytes_fn=put,
    )
    template = TemplateSpec.from_json(TEMPLATE_B)
    manifest = asyncio.run(pipe.run(spec, template))

    # final composited image
    final_key = manifest.final_url.replace("https://local/", "")
    final_bytes = saved.get(final_key)
    if not final_bytes:
        # fall back to the largest PNG recorded
        pngs = {k: v for k, v in saved.items() if v[:8] == b"\x89PNG\r\n\x1a\n"}
        final_bytes = max(pngs.values(), key=len) if pngs else None
    if final_bytes:
        (OUT / "final_poster.png").write_bytes(final_bytes)
        img = PILImage.open(BytesIO(final_bytes))
        print(f"final_poster.png saved: {img.size} {len(final_bytes)} bytes")
    else:
        print("WARNING: no final image bytes captured; keys=", list(saved))

    # payload
    (OUT / "sample_payload.json").write_text(
        json.dumps(_payload_dict(spec), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # diagnostics
    diagnostics = {
        "template_id": manifest.template_id,
        "render_engine_used": manifest.render_engine_used,
        "renderer_mode": manifest.renderer_mode,
        "degraded": manifest.degraded,
        "fallback_reason_code": manifest.fallback_reason_code,
        "structure_complete": manifest.structure_complete,
        "deliverable": manifest.deliverable,
        "region_render_status": manifest.region_render_status,
        "announcement_variant_contract_review": manifest.announcement_variant_contract_review,
        "top_copy_contract_review": manifest.top_copy_contract_review,
        "description_contract_review": manifest.description_contract_review,
        "product_contract_review": manifest.product_contract_review,
    }
    (OUT / "diagnostics.json").write_text(
        json.dumps(diagnostics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    print("diagnostics.json saved")
    print("structure_complete=", manifest.structure_complete, "deliverable=", manifest.deliverable)
    avc = manifest.announcement_variant_contract_review
    print("announcement structure_complete=", avc.get("structure_complete"))
    print("new_copy_slots rendered:", {k: v.get("rendered") for k, v in avc.get("new_copy_slots", {}).items()})
    print("materials collapse:", avc.get("materials_strip_region", {}).get("collapsed_by_design"))


if __name__ == "__main__":
    main()
