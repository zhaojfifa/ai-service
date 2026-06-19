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

    docs_blob = _read(REF_DOC) + _read(STATUS_DOC)
    mapping_ok = (
        "ttt.html" in docs_blob and "ttt2.html" in docs_blob
        and "product_sheet_email" in docs_blob and "campaign_poster_email" in docs_blob
    )
    if mapping_ok:
        oks.append("docs record ttt.html->product_sheet_email and ttt2.html->campaign_poster_email mapping")
    else:
        warns.append("docs do NOT clearly record ttt.html/ttt2.html -> fill-format mapping")

    for line in oks:
        print(f"  [ok]    {line}")
    for line in warns:
        print(f"  [warn]  {line}")
    print(f"RESULT: {'PASS' if not warns else 'PASS-with-warnings'} (advisory; non-blocking)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
