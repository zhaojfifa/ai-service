#!/usr/bin/env python3
"""
Poster2 Composition Priority Layer review harness (HX-POSTER2-COMPOSITION-PRIORITY-V1).

Drives PosterPipeline.run() with mocked Firefly + a stubbed r2_client (so the
scenario-cover background builder runs offline) and the REAL in-process Puppeteer
renderer. Renders three composition outputs WITH a real scenario image:

  base         = template_dual_v2            + composition_strategy=balanced
  studio       = template_dual_v2_studio     + composition_strategy=studio
  product_hero = template_dual_v2_product_hero+ composition_strategy=product_hero

For each: 10 identical runs (>=95% success + validator pass + deterministic).
Plus geometry/ownership invariants + a composition-is-non-geometric proof + a
scenario-recede metric. Writes screenshots, side-by-side, heatmap, and a quality
report JSON under scripts/out/composition/.

Usage:  PYTHONPATH=. ./.venv/bin/python scripts/poster2_composition_review.py [--runs N]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import numpy as np
from PIL import Image as PILImage, ImageChops, ImageDraw

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

import app.services.r2_client as _r2  # noqa: E402

_r2.put_bytes = lambda key, data, **kw: f"https://r2.example/{key}"  # offline stub

from app.services.poster2.asset_loader import AssetLoader  # noqa: E402
from app.services.poster2.background import BackgroundResult, FireflyBackgroundService  # noqa: E402
from app.services.poster2.composer import Composer  # noqa: E402
from app.services.poster2.composition import composition_css_vars  # noqa: E402
from app.services.poster2.contracts import AssetRef, PosterSpec, ResolvedAssets, StyleSpec  # noqa: E402
from app.services.poster2.font_registry import FontRegistry  # noqa: E402
from app.services.poster2.pipeline import PosterPipeline, load_template  # noqa: E402
from app.services.poster2.renderer import (  # noqa: E402
    LayoutRenderer,
    PuppeteerStructuredRenderer,
    RendererSelector,
)
from app.services.poster2.skills.control.family_a_control_surface_v1 import build_control_surface  # noqa: E402
from app.services.poster2.skills.structure.family_a_structure_surface_v1 import build_structure_surface  # noqa: E402
from app.services.poster2.template_behavior import resolve_template_behavior  # noqa: E402

_OUT = _REPO / "scripts" / "out" / "composition"
_PROTECTED_REGIONS = (
    "header_region", "scenario_region", "product_region", "feature_region",
    "bottom_region", "title_band_region", "gallery_strip_region",
)
_TARGETS = [
    {"label": "base", "template_id": "template_dual_v2", "strategy": "balanced"},
    {"label": "studio", "template_id": "template_dual_v2_studio", "strategy": "studio"},
    {"label": "product_hero", "template_id": "template_dual_v2_product_hero", "strategy": "product_hero"},
]


def _img(w, h, c):
    return PILImage.new("RGBA", (w, h), c)


def _scenario_img():
    im = PILImage.new("RGB", (576, 1040), (70, 90, 120))
    d = ImageDraw.Draw(im)
    for y in range(1040):
        d.line([(0, y), (576, y)], fill=(60 + y // 12, 90 + y // 20, 130 - y // 16))
    d.ellipse([120, 300, 460, 640], fill=(220, 180, 120))
    d.rectangle([60, 720, 520, 980], fill=(40, 60, 80))
    return im


def _assets():
    return ResolvedAssets(
        product=_img(640, 900, (210, 120, 60, 255)),
        logo=_img(240, 120, (40, 40, 40, 255)),
        scenario=_scenario_img(),
        gallery=[_img(360, 240, c) for c in [
            (180, 90, 60, 255), (90, 140, 170, 255), (150, 160, 120, 255), (200, 180, 120, 255)]],
    )


def _loader():
    l = MagicMock(spec=AssetLoader)
    l.load = AsyncMock(return_value=_assets())
    l.load_url = AsyncMock(return_value=PILImage.new("RGB", (1024, 1024), (235, 235, 235)))
    return l


def _bg():
    b = MagicMock(spec=FireflyBackgroundService)
    b.generate = AsyncMock(return_value=BackgroundResult(
        url="x", key="k", prompt_used="p", seed_used=42, model="firefly-v3", width=1024, height=1024))
    return b


def _spec(tid, strategy):
    return PosterSpec(
        brand_name="厨匠 Kitchen", agent_name="智能销售顾问", title="商用电炸炉 高效之选",
        subtitle="高效稳定 安全耐用", features=("精准控温", "节能省电", "一键清洁", "稳定耐用"),
        product_image=AssetRef(url="mock://p"), scenario_image=AssetRef(url="mock://s"),
        gallery_images=tuple(AssetRef(url=f"mock://g/{i}") for i in range(4)),
        style=StyleSpec(seed=42), template_id=tid, renderer_mode="puppeteer",
        composition_strategy=strategy)


def _run_once(tid, strategy):
    cap = {}
    p = PosterPipeline(
        background_svc=_bg(),
        renderer=RendererSelector(pillow_renderer=LayoutRenderer(FontRegistry()),
                                  puppeteer_renderer=PuppeteerStructuredRenderer()),
        composer=Composer(), asset_loader=_loader(),
        put_bytes_fn=lambda k, d, **kw: cap.__setitem__(k, d) or f"https://r2/{k}")
    t0 = time.time()
    m = asyncio.run(p.run(_spec(tid, strategy), load_template(tid)))
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
    if (m.composition_strategy or {}).get("strategy") != strategy:
        failed.append("composition_strategy_mismatch")
    final = next((v for k, v in cap.items() if "poster2/final/" in k), None)
    return {
        "engine": m.render_engine_used, "wall_ms": wall, "final_hash": m.final_hash,
        "deliverable": m.deliverable, "failed_checks": failed, "ok": not failed,
        "composition_strategy": m.composition_strategy,
        "geometry_evidence": m.geometry_evidence,
        "template_behavior": m.template_behavior,
    }, final


def _resolve(tid, strategy):
    return resolve_template_behavior(
        load_template(tid), feature_count=3, product_image_size=(640, 900),
        title_text="商用电炸炉 高效之选", subtitle_text="高效稳定 安全耐用",
        brand_name="厨匠", agent_name="顾问",
        gallery_requested_count=4, gallery_input_count_normalized=4, gallery_resolved_count=4,
        composition_strategy=strategy)


def _geometry(tid, strategy):
    return build_structure_surface(load_template(tid), resolved_behavior=_resolve(tid, strategy),
                                   layer_render_status={}, region_render_status={})


def _invariants(first):
    out = {"checks": [], "ok": True}

    def chk(name, cond, detail=""):
        out["checks"].append({"check": name, "pass": bool(cond), "detail": "" if cond else detail})
        out["ok"] = out["ok"] and bool(cond)

    base = first["base"]["geometry_evidence"]
    # protected regions + counts + ownership identical across ALL three outputs
    for t in ("studio", "product_hero"):
        ge = first[t]["geometry_evidence"]
        for r in _PROTECTED_REGIONS:
            chk(f"{t}: region_bounds[{r}] == base", base["region_bounds"][r] == ge["region_bounds"][r],
                f"base={base['region_bounds'][r]} {t}={ge['region_bounds'][r]}")
        chk(f"{t}: visible_item_count == base", base.get("visible_item_count") == ge.get("visible_item_count"))
        bo = (first["base"]["template_behavior"].get("family_control_surface") or {}).get("ownership_guards")
        to = (first[t]["template_behavior"].get("family_control_surface") or {}).get("ownership_guards")
        chk(f"{t}: ownership_guards == base", bo == to, f"base={bo} {t}={to}")
    # product_hero uses FULL product geometry (== base); studio floats it
    ph = first["product_hero"]["geometry_evidence"]["slot_bounds"].get("product_slot")
    st = first["studio"]["geometry_evidence"]["slot_bounds"].get("product_slot")
    chk("product_hero product slot == base (full product)", ph == base["slot_bounds"].get("product_slot"),
        f"base={base['slot_bounds'].get('product_slot')} hero={ph}")
    chk("studio product slot floats (!= base)", st != base["slot_bounds"].get("product_slot"))
    # composition is NON-geometric: same template, balanced vs product_hero strategy -> geometry identical
    g_bal = _geometry("template_dual_v2", "balanced")
    g_hero = _geometry("template_dual_v2", "product_hero")
    chk("composition non-geometric: base region_bounds identical balanced vs product_hero",
        g_bal["region_bounds"] == g_hero["region_bounds"])
    chk("composition non-geometric: base slot_bounds identical balanced vs product_hero",
        g_bal["slot_bounds"] == g_hero["slot_bounds"])
    # whitelist proof
    from app.services.poster2.composition import COMPOSITION_CSS_VAR_WHITELIST, COMPOSITION_STRATEGIES
    for s in COMPOSITION_STRATEGIES:
        chk(f"composition[{s}] vars within non-geometry whitelist",
            set(composition_css_vars(s)).issubset(COMPOSITION_CSS_VAR_WHITELIST))
    return out


def _scenario_saturation(png_path):
    a = np.asarray(PILImage.open(png_path).convert("RGB").crop((96, 188, 384, 708))).astype("float32")
    mx = a.max(axis=2); mn = a.min(axis=2)
    return float(((mx - mn) / (mx + 1e-3)).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=10)
    args = ap.parse_args()
    _OUT.mkdir(parents=True, exist_ok=True)
    report = {"targets": {}, "invariants": None, "scenario_recede": {}, "overall_pass": True}
    first = {}

    for t in _TARGETS:
        label, tid, strat = t["label"], t["template_id"], t["strategy"]
        print(f"\n=== {label} ({tid} + {strat}) x{args.runs} ===", flush=True)
        runs = []
        for i in range(args.runs):
            rec, final = _run_once(tid, strat)
            runs.append(rec)
            if i == 0:
                first[label] = rec
                if final:
                    (_OUT / f"{label}_final.png").write_bytes(final)
            print(f"  run {i:>2}: engine={rec['engine']} wall={rec['wall_ms']}ms "
                  f"hash={(rec['final_hash'] or '')[:12]} {'ok' if rec['ok'] else 'FAIL ' + ';'.join(rec['failed_checks'])}",
                  flush=True)
        ok = sum(1 for r in runs if r["ok"]); rate = ok / len(runs)
        hashes = sorted({r["final_hash"] for r in runs})
        s = {"template_id": tid, "strategy": strat, "runs": len(runs), "ok_count": ok,
             "success_rate": round(rate, 3), "validator_pass": all(r["deliverable"] and not r["failed_checks"] for r in runs),
             "deterministic": len(hashes) == 1, "distinct_final_hashes": hashes,
             "engines": sorted({r["engine"] for r in runs}),
             "pass": rate >= 0.95 and all(r["deliverable"] and not r["failed_checks"] for r in runs)}
        report["targets"][label] = s
        report["overall_pass"] = report["overall_pass"] and s["pass"]
        print(f"  -> success={rate:.0%} validator_pass={s['validator_pass']} deterministic={s['deterministic']} pass={s['pass']}", flush=True)

    inv = _invariants(first)
    report["invariants"] = inv
    report["overall_pass"] = report["overall_pass"] and inv["ok"]
    print("\n=== geometry / ownership / composition invariants ===")
    for c in inv["checks"]:
        print(f"  [{'PASS' if c['pass'] else 'FAIL'}] {c['check']}" + ("" if c["pass"] else f"  ({c['detail']})"))

    # scenario recede metric (base vs product_hero)
    if (_OUT / "base_final.png").exists() and (_OUT / "product_hero_final.png").exists():
        sb = _scenario_saturation(_OUT / "base_final.png")
        sh = _scenario_saturation(_OUT / "product_hero_final.png")
        report["scenario_recede"] = {"base_saturation": round(sb, 3), "product_hero_saturation": round(sh, 3),
                                     "ratio": round(sh / sb, 3), "receded": sh < sb * 0.8}
        print(f"\nscenario saturation base={sb:.3f} product_hero={sh:.3f} ratio={sh/sb:.2f} "
              f"(receded={report['scenario_recede']['receded']})")

    # side-by-side + heatmap
    labels = [t["label"] for t in _TARGETS]
    imgs = [PILImage.open(_OUT / f"{l}_final.png").convert("RGB") for l in labels]
    pad, lbl = 18, 36
    W = sum(i.width for i in imgs) + pad * (len(imgs) + 1)
    c = PILImage.new("RGB", (W, imgs[0].height + lbl + pad * 2), (245, 245, 245))
    d = ImageDraw.Draw(c); x = pad
    for lab, im in zip(["BASE / Balanced", "STUDIO / Studio", "PRODUCT HERO"], imgs):
        c.paste(im, (x, lbl + pad)); d.text((x + 6, 12), lab, fill=(20, 20, 20)); x += im.width + pad
    c.save(_OUT / "composition_side_by_side.png")
    diff = np.asarray(ImageChops.difference(imgs[0], imgs[2])).sum(axis=2)
    faded = (np.asarray(imgs[0]).astype("float32") * 0.35 + 255 * 0.65).astype("uint8")
    faded[diff > 8] = [230, 30, 30]
    PILImage.fromarray(faded).save(_OUT / "composition_diff_heatmap.png")

    (_OUT / "composition_quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nQuality report: {(_OUT / 'composition_quality_report.json').relative_to(_REPO)}")
    print(f"OVERALL PASS: {report['overall_pass']}")
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
