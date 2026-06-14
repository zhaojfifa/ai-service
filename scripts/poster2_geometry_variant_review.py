#!/usr/bin/env python3
"""
Poster2 geometry style variant (template_dual_v2_studio) stability + invariant
review harness (HX-POSTER2-STYLE-VARIANT-V1).

Drives PosterPipeline.run() directly with mocked Firefly/R2 and the REAL in-process
Puppeteer renderer. For template_dual_v2 (baseline) and template_dual_v2_studio it:

  - runs N identical generations, recording engine / wall-ms / final_hash /
    failed-checks; requires >= 95% success AND validator pass per run;
  - captures run-0 final PNGs + a side-by-side;
  - asserts the geometry/ownership INVARIANTS a bounded variant must preserve:
      * every region_bounds box (header/scenario/product/feature/bottom/
        title_band/gallery_strip) is IDENTICAL base vs studio
        (the variant moves the product IMAGE slot, NOT any region);
      * ownership_guards identical;
      * gallery_strip_region geometry + visible gallery count identical
        (bottom SOP geometry untouched — only its surface differs in CSS);
      * the 3 product annotation slots + owner are preserved;
      * the ONLY intended geometry delta is slot_bounds['product_slot'].
  - writes a quality report JSON.

Usage:
    PYTHONPATH=. ./.venv/bin/python scripts/poster2_geometry_variant_review.py [--runs N]
Outputs under scripts/out/studio/.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from PIL import Image as PILImage, ImageDraw

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from app.services.poster2.asset_loader import AssetLoader  # noqa: E402
from app.services.poster2.background import BackgroundResult, FireflyBackgroundService  # noqa: E402
from app.services.poster2.composer import Composer  # noqa: E402
from app.services.poster2.contracts import AssetRef, PosterSpec, ResolvedAssets, StyleSpec  # noqa: E402
from app.services.poster2.font_registry import FontRegistry  # noqa: E402
from app.services.poster2.pipeline import PosterPipeline, load_template  # noqa: E402
from app.services.poster2.renderer import (  # noqa: E402
    LayoutRenderer,
    PuppeteerStructuredRenderer,
    RendererSelector,
)

_OUT = _REPO / "scripts" / "out" / "studio"
_BASE = "template_dual_v2"
_STUDIO = "template_dual_v2_studio"

# Regions whose bounds MUST be byte-identical between base and the variant.
_PROTECTED_REGIONS = (
    "header_region", "scenario_region", "product_region", "feature_region",
    "bottom_region", "title_band_region", "gallery_strip_region",
)


def _img(w, h, c):
    return PILImage.new("RGBA", (w, h), c)


def _assets():
    return ResolvedAssets(
        product=_img(640, 900, (210, 120, 60, 255)),
        logo=_img(240, 120, (40, 40, 40, 255)),
        gallery=[_img(360, 240, c) for c in [
            (180, 90, 60, 255), (90, 140, 170, 255), (150, 160, 120, 255), (200, 180, 120, 255)]],
    )


def _bg():
    s = MagicMock(spec=FireflyBackgroundService)
    s.generate = AsyncMock(return_value=BackgroundResult(
        url="https://r2/bg.png", key="poster2/bg/h.png", prompt_used="studio background",
        seed_used=42, model="firefly-v3", width=1024, height=1024))
    return s


def _loader():
    l = MagicMock(spec=AssetLoader)
    l.load = AsyncMock(return_value=_assets())
    l.load_url = AsyncMock(return_value=PILImage.new("RGB", (1024, 1024), (235, 235, 235)))
    return l


def _spec(tid):
    return PosterSpec(
        brand_name="厨匠 Kitchen", agent_name="智能销售顾问", title="商用电炸炉 高效之选",
        subtitle="高效稳定 安全耐用", features=("精准控温", "节能省电", "一键清洁", "稳定耐用"),
        product_image=AssetRef(url="mock://product"),
        gallery_images=tuple(AssetRef(url=f"mock://g/{i}") for i in range(4)),
        style=StyleSpec(seed=42), template_id=tid, renderer_mode="puppeteer")


def _run_once(tid):
    cap = {}
    p = PosterPipeline(
        background_svc=_bg(),
        renderer=RendererSelector(pillow_renderer=LayoutRenderer(FontRegistry()),
                                  puppeteer_renderer=PuppeteerStructuredRenderer()),
        composer=Composer(), asset_loader=_loader(),
        put_bytes_fn=lambda k, d, **kw: cap.__setitem__(k, d) or f"https://r2/{k}")
    t0 = time.time()
    m = asyncio.run(p.run(_spec(tid), load_template(tid)))
    wall = int((time.time() - t0) * 1000)
    failed = []
    if m.render_engine_used != "puppeteer":
        failed.append(f"engine={m.render_engine_used}")
    if m.degraded:
        failed.append("degraded")
    if not m.deliverable:
        failed.append("not_deliverable")
    if m.missing_mandatory_regions:
        failed.append("missing_regions")
    if m.missing_required_slots:
        failed.append("missing_slots")
    return {
        "engine": m.render_engine_used, "wall_ms": wall, "final_hash": m.final_hash,
        "deliverable": m.deliverable, "failed_checks": failed, "ok": not failed,
        "geometry_evidence": m.geometry_evidence,
        "template_behavior": m.template_behavior,
    }, cap


def _invariants(base_ev, studio_ev, base_tb, studio_tb):
    out = {"checks": [], "ok": True}

    def chk(name, cond, detail=""):
        out["checks"].append({"check": name, "pass": bool(cond), "detail": detail})
        out["ok"] = out["ok"] and bool(cond)

    bregs, sregs = base_ev["region_bounds"], studio_ev["region_bounds"]
    for r in _PROTECTED_REGIONS:
        chk(f"region_bounds:{r} identical", bregs.get(r) == sregs.get(r),
            f"base={bregs.get(r)} studio={sregs.get(r)}")
    chk("visible_item_count identical", base_ev.get("visible_item_count") == studio_ev.get("visible_item_count"),
        f"base={base_ev.get('visible_item_count')} studio={studio_ev.get('visible_item_count')}")
    # ownership guards (from template_behavior.family_control_surface)
    bo = (base_tb.get("family_control_surface") or {}).get("ownership_guards")
    so = (studio_tb.get("family_control_surface") or {}).get("ownership_guards")
    chk("ownership_guards identical", bo == so, f"base={bo} studio={so}")
    # the intended delta: the product IMAGE geometry differs. Both 'product_slot'
    # and 'product_primary_slot' name the same floated product image.
    _product_image_slots = {"product_slot", "product_primary_slot"}
    bps = base_ev["slot_bounds"].get("product_slot")
    sps = studio_ev["slot_bounds"].get("product_slot")
    chk("product image slot CHANGED (intended breathing)", bps != sps, f"base={bps} studio={sps}")
    # every NON-product slot bound is identical (only the product image moves)
    other_changed = [k for k in set(base_ev["slot_bounds"]) | set(studio_ev["slot_bounds"])
                     if k not in _product_image_slots
                     and base_ev["slot_bounds"].get(k) != studio_ev["slot_bounds"].get(k)]
    chk("only the product image slot changed among slots", not other_changed, f"other_changed={other_changed}")
    return out


def _summary(tid, runs):
    ok = sum(1 for r in runs if r["ok"])
    rate = ok / len(runs)
    hashes = sorted({r["final_hash"] for r in runs})
    return {
        "template_id": tid, "runs": len(runs), "ok_count": ok,
        "success_rate": round(rate, 3), "success_rate_threshold": 0.95,
        "validator_pass": all(r["deliverable"] and not r["failed_checks"] for r in runs),
        "engines": sorted({r["engine"] for r in runs}),
        "distinct_final_hashes": hashes, "deterministic": len(hashes) == 1,
        "avg_wall_ms": round(sum(r["wall_ms"] for r in runs) / len(runs)),
        "pass": rate >= 0.95 and all(r["deliverable"] and not r["failed_checks"] for r in runs),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=10)
    args = ap.parse_args()
    _OUT.mkdir(parents=True, exist_ok=True)

    report = {"targets": {}, "invariants": None, "overall_pass": True}
    first = {}
    for tid in (_BASE, _STUDIO):
        print(f"\n=== {tid} x{args.runs} ===", flush=True)
        runs = []
        for i in range(args.runs):
            rec, cap = _run_once(tid)
            runs.append(rec)
            print(f"  run {i:>2}: engine={rec['engine']} wall={rec['wall_ms']}ms "
                  f"hash={(rec['final_hash'] or '')[:12]} {'ok' if rec['ok'] else 'FAIL ' + ';'.join(rec['failed_checks'])}",
                  flush=True)
            if i == 0:
                first[tid] = rec
                final = next((v for k, v in cap.items() if "poster2/final/" in k), None)
                if final:
                    (_OUT / f"{tid}_final.png").write_bytes(final)
        s = _summary(tid, runs)
        report["targets"][tid] = s
        report["overall_pass"] = report["overall_pass"] and s["pass"]
        print(f"  -> success={s['success_rate']:.0%} validator_pass={s['validator_pass']} "
              f"deterministic={s['deterministic']} pass={s['pass']}", flush=True)

    inv = _invariants(first[_BASE]["geometry_evidence"], first[_STUDIO]["geometry_evidence"],
                      first[_BASE]["template_behavior"], first[_STUDIO]["template_behavior"])
    report["invariants"] = inv
    report["overall_pass"] = report["overall_pass"] and inv["ok"]
    print("\n=== geometry / ownership invariants ===")
    for c in inv["checks"]:
        print(f"  [{'PASS' if c['pass'] else 'FAIL'}] {c['check']}" + ("" if c["pass"] else f"  ({c['detail']})"))

    # side-by-side
    bp, sp = _OUT / f"{_BASE}_final.png", _OUT / f"{_STUDIO}_final.png"
    if bp.exists() and sp.exists():
        b, s = PILImage.open(bp).convert("RGB"), PILImage.open(sp).convert("RGB")
        pad, lbl = 20, 40
        c = PILImage.new("RGB", (b.width * 2 + pad * 3, b.height + lbl + pad * 2), (245, 245, 245))
        c.paste(b, (pad, lbl + pad)); c.paste(s, (b.width + pad * 2, lbl + pad))
        d = ImageDraw.Draw(c)
        d.text((pad + 8, 12), "BASELINE  template_dual_v2", fill=(20, 20, 20))
        d.text((b.width + pad * 2 + 8, 12), "STUDIO  template_dual_v2_studio  (geometry variant)", fill=(20, 20, 20))
        c.save(_OUT / "studio_side_by_side.png")

    (_OUT / "geometry_variant_quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nQuality report: {(_OUT / 'geometry_variant_quality_report.json').relative_to(_REPO)}")
    print(f"OVERALL PASS: {report['overall_pass']}")
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
