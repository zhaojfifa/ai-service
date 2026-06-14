#!/usr/bin/env python3
"""
Poster2 Visual Relaxation stability + visual-evidence harness.

Drives PosterPipeline.run() directly (NOT the HTTP route) with mocked Firefly /
R2 I/O and the REAL in-process Puppeteer (Playwright/Chromium) renderer, so the
deterministic foreground — where relaxation actually applies — is exercised end
to end without external services.

For each of:
  a) template_dual_v2        (relaxation_preset = none  -> baseline)
  b) template_dual_v2_airy   (relaxation_preset = airy)

it runs N identical generations, records engine / wall-ms / final_hash /
failed-checks, requires >= 95% success AND validator pass on every run, captures
the run-0 final + foreground PNGs (for the before/after evidence), and writes a
JSON quality report including the relaxation preset and validator result.

Usage:
    PYTHONPATH=. ./.venv/bin/python scripts/poster2_relaxation_stability_harness.py [--runs N]

Outputs (under scripts/out/relaxation/):
    template_dual_v2_final.png         template_dual_v2_fg.png         (baseline)
    template_dual_v2_airy_final.png    template_dual_v2_airy_fg.png    (airy)
    relaxation_quality_report.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from PIL import Image as PILImage

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from app.services.poster2.asset_loader import AssetLoader  # noqa: E402
from app.services.poster2.background import (  # noqa: E402
    BackgroundResult,
    FireflyBackgroundService,
)
from app.services.poster2.composer import Composer  # noqa: E402
from app.services.poster2.contracts import AssetRef, PosterSpec, ResolvedAssets, StyleSpec  # noqa: E402
from app.services.poster2.font_registry import FontRegistry  # noqa: E402
from app.services.poster2.pipeline import PosterPipeline, load_template  # noqa: E402
from app.services.poster2.renderer import (  # noqa: E402
    LayoutRenderer,
    PuppeteerStructuredRenderer,
    RendererSelector,
)

_OUT = _REPO / "scripts" / "out" / "relaxation"

_TARGETS = [
    {"label": "baseline", "template_id": "template_dual_v2", "expected_preset": "none"},
    {"label": "airy", "template_id": "template_dual_v2_airy", "expected_preset": "airy"},
]


def _img(w: int, h: int, color) -> PILImage.Image:
    return PILImage.new("RGBA", (w, h), color)


def _make_assets() -> ResolvedAssets:
    # No scenario asset: that keeps the background on the mocked Firefly path
    # (self._bg.generate) instead of build_template_dual_v2_background, which
    # uploads directly to R2. The foreground (product / title / features /
    # gallery) — where relaxation applies — still renders deterministically.
    return ResolvedAssets(
        product=_img(640, 900, (210, 120, 60, 255)),
        logo=_img(240, 120, (40, 40, 40, 255)),
        gallery=[_img(360, 240, c) for c in [
            (180, 90, 60, 255), (90, 140, 170, 255),
            (150, 160, 120, 255), (200, 180, 120, 255),
        ]],
    )


def _mock_bg_service() -> FireflyBackgroundService:
    svc = MagicMock(spec=FireflyBackgroundService)
    svc.generate = AsyncMock(
        return_value=BackgroundResult(
            url="https://r2.example.com/bg.png",
            key="poster2/bg/harness.png",
            prompt_used="studio background, no text, no logo",
            seed_used=42,
            model="firefly-v3",
            width=1024,
            height=1024,
        )
    )
    return svc


def _mock_loader() -> AssetLoader:
    loader = MagicMock(spec=AssetLoader)
    loader.load = AsyncMock(return_value=_make_assets())
    loader.load_url = AsyncMock(return_value=PILImage.new("RGB", (1024, 1024), (235, 235, 235)))
    return loader


def _spec(template_id: str) -> PosterSpec:
    return PosterSpec(
        brand_name="厨匠 Kitchen",
        agent_name="智能销售顾问",
        title="商用电炸炉 高效之选",
        subtitle="高效稳定 安全耐用",
        features=("精准控温", "节能省电", "一键清洁", "稳定耐用"),
        product_image=AssetRef(url="mock://product"),
        gallery_images=tuple(AssetRef(url=f"mock://gallery/{i}") for i in range(4)),
        style=StyleSpec(seed=42),
        template_id=template_id,
        renderer_mode="puppeteer",
    )


def _build_pipeline(captured: dict) -> PosterPipeline:
    def _put(key, data, **kw):
        captured[key] = data
        ext = "png" if key.endswith(".png") else "json"
        return f"https://r2.example.com/{key.replace('/', '_')}.{ext}"

    return PosterPipeline(
        background_svc=_mock_bg_service(),
        renderer=RendererSelector(
            pillow_renderer=LayoutRenderer(FontRegistry()),
            puppeteer_renderer=PuppeteerStructuredRenderer(),
        ),
        composer=Composer(),
        asset_loader=_mock_loader(),
        put_bytes_fn=_put,
    )


def _run_once(template_id: str) -> tuple[dict, dict[str, bytes]]:
    captured: dict[str, bytes] = {}
    pipeline = _build_pipeline(captured)
    spec = _spec(template_id)
    template = load_template(template_id)
    t0 = time.time()
    manifest = asyncio.run(pipeline.run(spec, template))
    wall_ms = int((time.time() - t0) * 1000)

    failed_checks: list[str] = []
    if manifest.render_engine_used != "puppeteer":
        failed_checks.append(f"engine={manifest.render_engine_used}")
    if manifest.degraded:
        failed_checks.append(f"degraded:{manifest.degraded_reason or manifest.fallback_reason_code}")
    if not manifest.deliverable:
        failed_checks.append("not_deliverable")
    if manifest.missing_mandatory_regions:
        failed_checks.append("missing_regions:" + ",".join(manifest.missing_mandatory_regions))
    if manifest.missing_required_slots:
        failed_checks.append("missing_slots:" + ",".join(manifest.missing_required_slots))

    record = {
        "engine": manifest.render_engine_used,
        "wall_ms": wall_ms,
        "renderer_ms": manifest.timings_ms.get("foreground_render_ms")
        or manifest.timings_ms.get("foreground_ms"),
        "final_hash": manifest.final_hash,
        "foreground_hash": manifest.foreground_hash,
        "deliverable": manifest.deliverable,
        "relaxation_preset": manifest.relaxation_preset,
        "failed_checks": failed_checks,
        "ok": not failed_checks,
    }
    return record, captured


def _save_png(captured: dict[str, bytes], prefix: str, label_id: str) -> dict:
    saved = {}
    for kind in ("final", "fg"):
        match = next((v for k, v in captured.items() if f"poster2/{kind}/" in k), None)
        if match:
            path = _OUT / f"{label_id}_{kind}.png"
            path.write_bytes(match)
            saved[kind] = str(path.relative_to(_REPO))
    return saved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=10)
    args = parser.parse_args()
    _OUT.mkdir(parents=True, exist_ok=True)

    report = {"runs_per_target": args.runs, "targets": [], "overall_pass": True}

    for target in _TARGETS:
        tid = target["template_id"]
        print(f"\n=== {target['label']} ({tid}) x{args.runs} ===", flush=True)
        runs: list[dict] = []
        screenshots: dict = {}
        for i in range(args.runs):
            record, captured = _run_once(tid)
            runs.append(record)
            status = "ok" if record["ok"] else "FAIL " + ";".join(record["failed_checks"])
            print(
                f"  run {i:>2}: engine={record['engine']} "
                f"wall={record['wall_ms']}ms hash={(record['final_hash'] or '')[:12]} {status}",
                flush=True,
            )
            if i == 0:
                screenshots = _save_png(captured, target["label"], tid)

        ok_count = sum(1 for r in runs if r["ok"])
        success_rate = ok_count / len(runs)
        validator_pass = all(r["deliverable"] and not r["failed_checks"] for r in runs)
        distinct_hashes = sorted({r["final_hash"] for r in runs})
        preset_used = runs[0]["relaxation_preset"]
        target_pass = success_rate >= 0.95 and validator_pass

        # preset truth check: the manifest must report the expected preset.
        preset_ok = (preset_used or {}).get("preset") == target["expected_preset"]
        target_pass = target_pass and preset_ok

        report["targets"].append({
            "label": target["label"],
            "template_id": tid,
            "expected_relaxation_preset": target["expected_preset"],
            "relaxation_preset": preset_used,
            "relaxation_preset_ok": preset_ok,
            "runs": len(runs),
            "ok_count": ok_count,
            "success_rate": round(success_rate, 3),
            "success_rate_threshold": 0.95,
            "validator_pass": validator_pass,
            "engines": sorted({r["engine"] for r in runs}),
            "distinct_final_hash_count": len(distinct_hashes),
            "distinct_final_hashes": distinct_hashes,
            "avg_wall_ms": round(sum(r["wall_ms"] for r in runs) / len(runs)),
            "screenshots": screenshots,
            "pass": target_pass,
            "per_run": runs,
        })
        report["overall_pass"] = report["overall_pass"] and target_pass
        print(
            f"  -> success_rate={success_rate:.2%} validator_pass={validator_pass} "
            f"preset={preset_used.get('preset') if preset_used else None} pass={target_pass}",
            flush=True,
        )

    report_path = _OUT / "relaxation_quality_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nQuality report: {report_path.relative_to(_REPO)}")
    print(f"OVERALL PASS: {report['overall_pass']}")
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
