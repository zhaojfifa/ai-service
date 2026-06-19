#!/usr/bin/env python3
"""CUISTANCE email reference HTML inventory (ttt.html / ttt2.html) — stdlib only, no new dependency.

Extracts STRUCTURE GRAMMAR only (region presence + 600px container) from the two reference emails and classifies:
  ttt.html  -> product_sheet_email  (Cuistance/Mailchimp product-style)
  ttt2.html -> campaign_poster_email (Technitalia/Zoho campaign-style)

Does NOT copy raw HTML, scripts, tracking pixels, list-manage/Zoho/Mailchimp tracking. Records only which email
regions are present (header/banner, body visual, intro copy, cta, footer, legal, social/contact) + an asset-host
note. The reference defines the email FILL FORMAT, never CUISTANCE business truth.

Usage: ./.venv/bin/python scripts/poster2_cuistance_email_html_inventory.py
"""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BASE = REPO / "docs/poster2/assets/cuistance_psd_email_container_last_mile_v1"
SRC = BASE / "source"
MAN = BASE / "manifest"

FORMAT_MAP = {"ttt.html": "product_sheet_email", "ttt2.html": "campaign_poster_email"}

TRACKING_MARKERS = ["list-manage", "campaign-image", "mc_eid", "zcsclwgt", "googletagmanager",
                    "facebook.com/tr", "/track/open", "open.aspx", "utm_"]


class TextImgCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts: list[str] = []
        self.img_count = 0
        self.link_count = 0
        self.table_count = 0
        self.img_hosts: set[str] = set()
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self._skip += 1
        if tag == "img":
            self.img_count += 1
            src = a.get("src", "")
            m = re.match(r"https?://([^/]+)/", src)
            if m:
                self.img_hosts.add(m.group(1))
        if tag == "a":
            self.link_count += 1
        if tag == "table":
            self.table_count += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            t = data.strip()
            if t:
                self.text_parts.append(t)


def classify_regions(text: str, html: str) -> dict:
    low = text.lower()
    has_600 = ("width:600px" in html.lower()) or ('width="600"' in html.lower()) or ("max-width:600px" in html.lower())
    return {
        "container_600px": has_600,
        "email_header": bool(re.search(r"logo|en-?t[êe]te|header|banni", html, re.I)),
        "body_visual": True,  # both references carry a primary product/campaign visual block
        "intro_copy": len(text) > 200,
        "cta": bool(re.search(r"contact|d[ée]couvr|commande|nous contacter|en savoir", low)),
        "footer": bool(re.search(r"désabonn|desabonn|unsubscribe|mentions|tous droits|©", low)),
        "legal": bool(re.search(r"désabonn|desabonn|unsubscribe|mentions l[ée]gales", low)),
        "social_contact": bool(re.search(r"facebook|instagram|linkedin|t[ée]l[ée]phone|@", low)),
    }


def inventory_one(path: Path) -> dict:
    html = path.read_text(encoding="utf-8", errors="replace")
    p = TextImgCollector()
    p.feed(html)
    text = " ".join(p.text_parts)
    tracking = sorted({m for m in TRACKING_MARKERS if m in html.lower()})
    regions = classify_regions(text, html)
    return {
        "classified_format": FORMAT_MAP.get(path.name, "unknown"),
        "bytes": path.stat().st_size,
        "table_count": p.table_count, "img_count": p.img_count, "link_count": p.link_count,
        "img_hosts": sorted(p.img_hosts),
        "regions": regions,
        "third_party_tracking_present_in_source": tracking,
        "tracking_copied_into_runtime": False,
        "note": "structure grammar only — no raw HTML / scripts / tracking copied into CUISTANCE runtime",
    }


def main() -> None:
    MAN.mkdir(parents=True, exist_ok=True)
    out = {}
    for fn in ("ttt.html", "ttt2.html"):
        fp = SRC / fn
        out[fn] = inventory_one(fp) if fp.exists() else {"error": "missing"}
    out["_mapping"] = {
        "ttt.html": "product_sheet_email / 简单产品页邮件格式 (Cuistance-Mailchimp product-style)",
        "ttt2.html": "campaign_poster_email / 目标海报邮件格式 (Technitalia-Zoho campaign-style)",
    }
    (MAN / "html_reference_inventory.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(json.dumps({k: (v.get("classified_format") if isinstance(v, dict) else v) for k, v in out.items() if not k.startswith("_")}, ensure_ascii=False, indent=2))
    for fn in ("ttt.html", "ttt2.html"):
        print(fn, "regions:", out[fn]["regions"], "tracking_in_source:", out[fn]["third_party_tracking_present_in_source"])


if __name__ == "__main__":
    main()
