#!/usr/bin/env python3
"""Lightweight ADVISORY check: the two reference-HTML-derived email fill formats are not forgotten.

Maps:
  ttt.html  (Cuistance/Mailchimp product-style)  -> product_sheet_email  / 简单产品页邮件格式
  ttt2.html (Technitalia/Zoho campaign-style)     -> campaign_poster_email / 目标海报邮件格式

Warns (does NOT fail / does NOT block legacy docs) if:
  - the reference extraction doc is missing
  - the dual-body-mode status doc is missing
  - the Step-3 UI does not mention BOTH 目标海报邮件格式 and 简单产品页邮件格式
  - the docs do not mention the ttt.html / ttt2.html -> fill-format mapping

Usage: python3 scripts/check_email_fill_format_alignment.py
Exit code is always 0 (advisory); prints OK/WARN lines.
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REF_DOC = REPO / "docs/poster2/cuistance_commercial_trial_reference_email_html_extraction_v1.md"
STATUS_DOC = REPO / "docs/poster2/cuistance_commercial_trial_dual_body_mode_email_fill_format_alignment_status_v1.md"
CORR_DOC = REPO / "docs/poster2/cuistance_commercial_trial_step3_email_fill_format_preview_correction_status_v1.md"
UI = REPO / "frontend/cuistance_trial.html"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def main() -> int:
    warns: list[str] = []
    oks: list[str] = []

    if REF_DOC.exists():
        oks.append(f"reference extraction doc present: {REF_DOC.relative_to(REPO)}")
    else:
        warns.append(f"reference extraction doc MISSING: {REF_DOC.relative_to(REPO)}")

    if STATUS_DOC.exists():
        oks.append(f"dual-body-mode status doc present: {STATUS_DOC.relative_to(REPO)}")
    else:
        warns.append(f"dual-body-mode status doc MISSING: {STATUS_DOC.relative_to(REPO)}")

    ui = _read(UI)
    for name in ("目标海报邮件格式", "简单产品页邮件格式"):
        if name in ui:
            oks.append(f"Step-3 UI mentions fill format: {name}")
        else:
            warns.append(f"Step-3 UI does NOT mention fill format: {name}")

    docs_blob = _read(REF_DOC) + _read(STATUS_DOC) + _read(CORR_DOC)
    mapping_ok = (
        "ttt.html" in docs_blob and "ttt2.html" in docs_blob
        and "product_sheet_email" in docs_blob and "campaign_poster_email" in docs_blob
    )
    if mapping_ok:
        oks.append("docs record ttt.html->product_sheet_email and ttt2.html->campaign_poster_email mapping")
    else:
        warns.append("docs do NOT clearly record ttt.html/ttt2.html -> fill-format mapping")

    # Step-3 separates the email HEADER module from the fill format, and exposes the final preview
    for needle, label in (("邮件页眉", "Step-3 UI separates 邮件页眉 (header) from fill format"),
                          ("邮件最终预览", "Step-3 UI exposes 邮件最终预览 (final preview)")):
        (oks if needle in ui else warns).append(label if needle in ui else label + " — MISSING")

    # the two formats must be present as internal keys somewhere the UI can drive them (diagnostics-grade)
    for key in ("campaign_poster_email", "product_sheet_email"):
        (oks if key in ui else warns).append(
            ("Step-3 UI carries fill-format key: " + key) if key in ui else ("Step-3 UI missing fill-format key: " + key))

    # header band assets must be header-only strips (wide aspect, never a 3:2 body/email screenshot)
    for fn in ("header_band_01.png", "header_band_02.png"):
        ap = REPO / "frontend" / "assets" / fn
        if not ap.exists():
            warns.append("header band asset MISSING: frontend/assets/" + fn)
            continue
        try:
            from PIL import Image  # type: ignore
            w, h = Image.open(ap).size
            if w / max(h, 1) >= 3.0:
                oks.append(f"header band {fn} is a header strip ({w}x{h}, aspect {w/h:.1f}:1) — header-only")
            else:
                warns.append(f"header band {fn} aspect {w/h:.1f}:1 is NOT a header strip (>=3:1 required)")
        except Exception:
            oks.append(f"header band asset present: frontend/assets/{fn} (aspect check skipped — PIL unavailable)")

    # no third-party tracking/scripts/pixels/list-manage/Zoho/Mailchimp tracking copied into the UI
    tracking = [t for t in ("list-manage", "campaign-image", "mc_eid", "zcsclwgt", "googletagmanager",
                            "facebook.com/tr", "/track/open") if t in ui]
    if tracking:
        warns.append("third-party tracking markers found in UI (must NOT be copied): " + ", ".join(tracking))
    else:
        oks.append("no third-party tracking/scripts/pixels copied into the UI")

    for line in oks:
        print(f"  [ok]    {line}")
    for line in warns:
        print(f"  [warn]  {line}")
    print(f"RESULT: {'PASS' if not warns else 'PASS-with-warnings'} (advisory; non-blocking)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
