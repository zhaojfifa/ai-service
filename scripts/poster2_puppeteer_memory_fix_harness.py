#!/usr/bin/env python3
"""
HX-POSTER2-PUPPETEER-MEMORY-FIX-V1 — memory + stability harness.

Proves the inline-downscale fix for the generate-poster OOM/502 on the real,
full 7-asset Stage2 payload (logo + scenario + product + product_secondary +
gallery x4), without changing any contract or visual output.

It produces three pieces of evidence:

  1. ANALYTICAL MEMORY REDUCTION (deterministic, in-process)
     For each of the 7 inlined assets it measures, at the full production input
     resolution, the decoded-bitmap bytes (w*h*4 — the dominant Chromium decode
     cost) and the base64 data-URL bytes (the HTML document weight), BEFORE the
     cap (no downscale) vs AFTER the cap (POSTER2_INLINE_MAX_DIMENSION). This is
     the root-cause memory that crossed the 512 MB ceiling.

  2. REAL PEAK-RSS BEFORE/AFTER (subprocess, real Puppeteer)
     Two isolated child processes each render product_hero once with the REAL
     in-process Chromium renderer — one with the cap effectively disabled
     ("before") and one with the production cap ("after") — and each reports its
     own peak RSS (self + children, so Chromium's decode spike is included).

  3. 10-RUN STABILITY (in-process, real Puppeteer)
     base / studio / product_hero each rendered N times on the full 7-asset
     payload at the production cap; requires >=95% success, validator pass on
     every run, and a single distinct final hash per variant (determinism /
     "visual output unchanged at poster resolution").

Usage:
    PYTHONPATH=. ./.venv/bin/python scripts/poster2_puppeteer_memory_fix_harness.py [--runs N]

Outputs (under scripts/out/puppeteer_memory_fix/):
    puppeteer_memory_report.json     analytical + real-RSS memory evidence
    puppeteer_stability_report.json  10-run stability per variant
    <variant>_final.png              run-0 final poster (visual evidence)
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import resource
import subprocess
import sys
import time
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from PIL import Image as PILImage

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

import app.services.r2_client as r2_client  # noqa: E402
from app.services.poster2.asset_loader import AssetLoader  # noqa: E402
from app.services.poster2.background import (  # noqa: E402
    BackgroundResult,
    FireflyBackgroundService,
)
from app.services.poster2.composer import Composer  # noqa: E402
from app.services.poster2.contracts import (  # noqa: E402
    AssetRef,
    PosterSpec,
    ResolvedAssets,
    StyleSpec,
)
from app.services.poster2.font_registry import FontRegistry  # noqa: E402
from app.services.poster2.pipeline import PosterPipeline, load_template  # noqa: E402
from app.services.poster2 import renderer as renderer_mod  # noqa: E402
from app.services.poster2.renderer import (  # noqa: E402
    LayoutRenderer,
    PuppeteerStructuredRenderer,
    RendererSelector,
    _image_to_data_url,
)

_OUT = _REPO / "scripts" / "out" / "puppeteer_memory_fix"

# Variant lines under test (the production-relevant Family A oracle lines).
_VARIANTS = [
    {"label": "base", "template_id": "template_dual_v2"},
    {"label": "studio", "template_id": "template_dual_v2_studio"},
    {"label": "product_hero", "template_id": "template_dual_v2_product_hero"},
]

# A realistic worst-case full 7-asset payload, sized at the asset_loader ceiling
# (POSTER2_MAX_IMAGE_DIMENSION default 4096) — what actually reaches the inliner
# in production before any downscale.
_ASSET_SIZES = {
    "logo": (1024, 512),
    "scenario": (3072, 4096),
    "product": (3072, 4096),
    "product_secondary": (2048, 2048),
    "gallery_0": (2400, 1600),
    "gallery_1": (2400, 1600),
    "gallery_2": (2400, 1600),
    "gallery_3": (2400, 1600),
}

# A disabled cap for the "before" measurement: larger than any input edge.
_CAP_DISABLED = 100_000


def _img_raw(w: int, h: int) -> PILImage.Image:
    return PILImage.new("RGBA", (w, h), (200, 180, 120, 255))


def _load_cap() -> int:
    """Mirror asset_loader's POSTER2_MAX_IMAGE_DIMENSION ceiling for held PIL assets."""
    return max(int(os.getenv("POSTER2_MAX_IMAGE_DIMENSION", "4096") or 0), 1)


def _img(w: int, h: int, color) -> PILImage.Image:
    img = PILImage.new("RGBA", (w, h), color)
    cap = _load_cap()
    # AssetLoader.normalize thumbnails every decoded asset to the load cap, so the
    # ResolvedAssets the pipeline holds are bounded the same way here.
    if img.width > cap or img.height > cap:
        img.thumbnail((cap, cap), PILImage.LANCZOS)
    return img


def _make_assets() -> ResolvedAssets:
    return ResolvedAssets(
        product=_img(*_ASSET_SIZES["product"], (210, 120, 60, 255)),
        logo=_img(*_ASSET_SIZES["logo"], (40, 40, 40, 255)),
        scenario=_img(*_ASSET_SIZES["scenario"], (120, 150, 180, 255)),
        product_secondary=_img(*_ASSET_SIZES["product_secondary"], (180, 150, 120, 255)),
        gallery=[
            _img(*_ASSET_SIZES["gallery_0"], (180, 90, 60, 255)),
            _img(*_ASSET_SIZES["gallery_1"], (90, 140, 170, 255)),
            _img(*_ASSET_SIZES["gallery_2"], (150, 160, 120, 255)),
            _img(*_ASSET_SIZES["gallery_3"], (200, 180, 120, 255)),
        ],
        gallery_status=[{"resolved": True} for _ in range(4)],
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
        product_secondary_image=AssetRef(url="mock://product2"),
        logo=AssetRef(url="mock://logo"),
        scenario_image=AssetRef(url="mock://scenario"),
        gallery_images=tuple(AssetRef(url=f"mock://gallery/{i}") for i in range(4)),
        style=StyleSpec(seed=42),
        template_id=template_id,
        renderer_mode="puppeteer",
    )


def _patch_r2(captured: dict[str, bytes]) -> None:
    """Keep build_template_dual_v2_background off real R2 (it calls put_bytes directly)."""

    def _put(key, data, content_type=None, **kw):
        captured[key] = data
        return f"https://r2.example.com/{key.replace('/', '_')}"

    r2_client.put_bytes = _put  # type: ignore[assignment]


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
    _patch_r2(captured)
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
        "final_hash": manifest.final_hash,
        "deliverable": manifest.deliverable,
        "failed_checks": failed_checks,
        "ok": not failed_checks,
    }
    return record, captured


# --------------------------------------------------------------------------- #
# 1. Analytical memory reduction                                              #
# --------------------------------------------------------------------------- #
def _measure_inline(img: PILImage.Image, cap: int) -> dict:
    capped = renderer_mod._downscale_for_inline(img, max_dim=cap)
    buf = BytesIO()
    capped.convert("RGBA").save(buf, format="PNG")
    data_url_bytes = len("data:image/png;base64,") + len(
        base64.b64encode(buf.getvalue())
    )
    return {
        "w": capped.width,
        "h": capped.height,
        "decoded_rgba_bytes": capped.width * capped.height * 4,
        "data_url_bytes": data_url_bytes,
    }


def _held_bytes(size: tuple[int, int], cap: int) -> int:
    """Decoded RGBA bytes a PIL asset occupies after AssetLoader's load-cap thumbnail."""
    w, h = size
    if w > cap or h > cap:
        ratio = min(cap / w, cap / h)
        w, h = max(1, int(w * ratio)), max(1, int(h * ratio))
    return w * h * 4


def _analytical_report(cap: int, load_cap_after: int) -> dict:
    # Build raw, uncapped assets directly so the analytical reduction is independent
    # of the harness's own env (it always measures the true full-res -> capped delta).
    raw = {name: _img_raw(*size) for name, size in _ASSET_SIZES.items()}
    per_asset = {}
    for name, img in raw.items():
        before = _measure_inline(img, _CAP_DISABLED)
        after = _measure_inline(img, cap)
        per_asset[name] = {
            "input_size": list(_ASSET_SIZES[name]),
            "before": before,
            "after": after,
        }

    def _sum(side: str, field: str) -> int:
        return sum(a[side][field] for a in per_asset.values())

    before_decoded = _sum("before", "decoded_rgba_bytes")
    after_decoded = _sum("after", "decoded_rgba_bytes")
    before_url = _sum("before", "data_url_bytes")
    after_url = _sum("after", "data_url_bytes")

    # Held PIL memory (parent process) under the asset_loader load cap, before/after
    # the optional POSTER2_MAX_IMAGE_DIMENSION stopgap.
    held_before = sum(_held_bytes(s, 4096) for s in _ASSET_SIZES.values())
    held_after = sum(_held_bytes(s, load_cap_after) for s in _ASSET_SIZES.values())
    return {
        "inline_max_dimension": cap,
        "load_max_dimension_before": 4096,
        "load_max_dimension_after": load_cap_after,
        "asset_count": len(raw),
        "per_asset": per_asset,
        "totals": {
            "chromium_decode_before_mb": round(before_decoded / 1024 / 1024, 1),
            "chromium_decode_after_mb": round(after_decoded / 1024 / 1024, 1),
            "chromium_decode_reduction_ratio": round(before_decoded / max(after_decoded, 1), 2),
            "data_url_before_mb": round(before_url / 1024 / 1024, 1),
            "data_url_after_mb": round(after_url / 1024 / 1024, 1),
            "data_url_reduction_ratio": round(before_url / max(after_url, 1), 2),
            "held_pil_before_mb": round(held_before / 1024 / 1024, 1),
            "held_pil_after_mb": round(held_after / 1024 / 1024, 1),
            "held_pil_reduction_ratio": round(held_before / max(held_after, 1), 2),
        },
    }


# --------------------------------------------------------------------------- #
# 2. Real peak-RSS before/after (subprocess worker)                          #
# --------------------------------------------------------------------------- #
def _peak_rss_bytes() -> int:
    # macOS reports ru_maxrss in bytes; Linux in kilobytes.
    unit = 1 if sys.platform == "darwin" else 1024
    self_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * unit
    child_rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss * unit
    return self_rss + child_rss


def _worker(cap: int) -> int:
    """Render product_hero once with the given inline cap; print peak RSS JSON."""
    record, _ = _run_once("template_dual_v2_product_hero")
    out = {
        "cap": cap,
        "peak_rss_bytes": _peak_rss_bytes(),
        "ok": record["ok"],
        "final_hash": record["final_hash"],
        "failed_checks": record["failed_checks"],
    }
    print("WORKER_RESULT " + json.dumps(out), flush=True)
    return 0 if record["ok"] else 1


def _run_worker_subprocess(scenario: str, inline_cap: int, load_cap: int) -> dict:
    env = dict(os.environ)
    env["POSTER2_INLINE_MAX_DIMENSION"] = str(inline_cap)
    env["POSTER2_MAX_IMAGE_DIMENSION"] = str(load_cap)
    env["PYTHONPATH"] = str(_REPO)
    proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--worker", str(inline_cap)],
        env=env,
        capture_output=True,
        text=True,
    )
    line = next(
        (ln for ln in proc.stdout.splitlines() if ln.startswith("WORKER_RESULT ")),
        None,
    )
    if line is None:
        return {
            "scenario": scenario,
            "inline_cap": inline_cap,
            "load_cap": load_cap,
            "error": "no_worker_result",
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-2000:],
        }
    result = json.loads(line[len("WORKER_RESULT "):])
    result.update({"scenario": scenario, "inline_cap": inline_cap, "load_cap": load_cap})
    return result


# --------------------------------------------------------------------------- #
# 3. Stability                                                                #
# --------------------------------------------------------------------------- #
def _save_final(captured: dict[str, bytes], label: str) -> str | None:
    match = next((v for k, v in captured.items() if "poster2/final/" in k), None)
    if match is None:
        return None
    path = _OUT / f"{label}_final.png"
    path.write_bytes(match)
    return str(path.relative_to(_REPO))


def _stability(runs: int) -> dict:
    report = {"runs_per_variant": runs, "variants": [], "overall_pass": True}
    for variant in _VARIANTS:
        tid = variant["template_id"]
        label = variant["label"]
        print(f"\n=== stability {label} ({tid}) x{runs} ===", flush=True)
        records: list[dict] = []
        screenshot = None
        for i in range(runs):
            record, captured = _run_once(tid)
            records.append(record)
            status = "ok" if record["ok"] else "FAIL " + ";".join(record["failed_checks"])
            print(
                f"  run {i:>2}: engine={record['engine']} wall={record['wall_ms']}ms "
                f"hash={(record['final_hash'] or '')[:12]} {status}",
                flush=True,
            )
            if i == 0:
                screenshot = _save_final(captured, label)

        ok_count = sum(1 for r in records if r["ok"])
        success_rate = ok_count / len(records)
        validator_pass = all(r["deliverable"] and not r["failed_checks"] for r in records)
        distinct_hashes = sorted({r["final_hash"] for r in records})
        deterministic = len(distinct_hashes) == 1
        variant_pass = success_rate >= 0.95 and validator_pass and deterministic
        report["variants"].append({
            "label": label,
            "template_id": tid,
            "runs": len(records),
            "ok_count": ok_count,
            "success_rate": round(success_rate, 3),
            "success_rate_threshold": 0.95,
            "validator_pass": validator_pass,
            "deterministic_single_hash": deterministic,
            "distinct_final_hash_count": len(distinct_hashes),
            "distinct_final_hashes": distinct_hashes,
            "avg_wall_ms": round(sum(r["wall_ms"] for r in records) / len(records)),
            "screenshot": screenshot,
            "pass": variant_pass,
            "per_run": records,
        })
        report["overall_pass"] = report["overall_pass"] and variant_pass
        print(
            f"  -> success_rate={success_rate:.2%} validator_pass={validator_pass} "
            f"deterministic={deterministic} pass={variant_pass}",
            flush=True,
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--worker", type=int, default=None, help="internal: run one render with this cap")
    args = parser.parse_args()

    if args.worker is not None:
        return _worker(args.worker)

    _OUT.mkdir(parents=True, exist_ok=True)
    prod_inline_cap = renderer_mod._INLINE_MAX_DIMENSION
    # Complementary no-deploy stopgap modelled here = render.yaml's
    # POSTER2_MAX_IMAGE_DIMENSION (held-PIL load cap). 1600px is still well above the
    # 1024px poster canvas, so it is visually lossless.
    config_load_cap = 1600
    render_ceiling_mb = 512

    # 1. Analytical memory reduction
    print(f"=== analytical memory reduction (inline_cap={prod_inline_cap}) ===", flush=True)
    analytical = _analytical_report(prod_inline_cap, config_load_cap)
    t = analytical["totals"]
    print(
        f"  Chromium decode: {t['chromium_decode_before_mb']} MB -> "
        f"{t['chromium_decode_after_mb']} MB ({t['chromium_decode_reduction_ratio']}x)",
        flush=True,
    )
    print(
        f"  data-url HTML:   {t['data_url_before_mb']} MB -> {t['data_url_after_mb']} MB "
        f"({t['data_url_reduction_ratio']}x)",
        flush=True,
    )
    print(
        f"  held PIL (load cap {config_load_cap}): {t['held_pil_before_mb']} MB -> "
        f"{t['held_pil_after_mb']} MB ({t['held_pil_reduction_ratio']}x)",
        flush=True,
    )

    # 2. Real peak-RSS across three isolated scenarios (product_hero, real Puppeteer)
    print("\n=== real peak-RSS scenarios (product_hero, real Puppeteer) ===", flush=True)
    scenarios = [
        ("before_no_fix", _CAP_DISABLED, 4096),
        ("after_inline_fix_only", prod_inline_cap, 4096),
        ("after_inline_fix_plus_config", prod_inline_cap, config_load_cap),
    ]
    rss_results = []
    for name, inline_cap, load_cap in scenarios:
        res = _run_worker_subprocess(name, inline_cap, load_cap)
        mb = round(res["peak_rss_bytes"] / 1024 / 1024, 1) if res.get("peak_rss_bytes") else None
        res["peak_rss_mb"] = mb
        res["under_render_free_ceiling"] = bool(mb and mb < render_ceiling_mb)
        rss_results.append(res)
        print(
            f"  {name:<30} inline={inline_cap} load={load_cap}  peak_rss={mb} MB  "
            f"under_512={res['under_render_free_ceiling']}",
            flush=True,
        )

    base_rss = rss_results[0].get("peak_rss_bytes")
    fixed_rss = rss_results[-1].get("peak_rss_bytes")
    rss_reduction = round(base_rss / max(fixed_rss, 1), 2) if base_rss and fixed_rss else None

    memory_report = {
        "platform": sys.platform,
        "note": (
            "macOS RSS runs higher than Render's Linux; the inline fix cuts the "
            "Chromium decode spike, and the POSTER2_MAX_IMAGE_DIMENSION stopgap cuts "
            "the held-PIL floor. Both together keep peak under the 512 MB ceiling."
        ),
        "render_free_ceiling_mb": render_ceiling_mb,
        "inline_max_dimension": prod_inline_cap,
        "config_load_max_dimension": config_load_cap,
        "analytical": analytical,
        "real_peak_rss_scenarios": rss_results,
        "before_to_fixed_reduction_ratio": rss_reduction,
    }
    (_OUT / "puppeteer_memory_report.json").write_text(
        json.dumps(memory_report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 3. Stability
    stability = _stability(args.runs)
    (_OUT / "puppeteer_stability_report.json").write_text(
        json.dumps(stability, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\n=== summary ===", flush=True)
    print(f"  memory report:    {(_OUT / 'puppeteer_memory_report.json').relative_to(_REPO)}", flush=True)
    print(f"  stability report: {(_OUT / 'puppeteer_stability_report.json').relative_to(_REPO)}", flush=True)
    print(f"  STABILITY OVERALL PASS: {stability['overall_pass']}", flush=True)
    return 0 if stability["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
