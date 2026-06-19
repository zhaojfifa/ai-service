#!/usr/bin/env python3
"""CUISTANCE PSD email-container seed inventory (NOT a generic PSD parser).

Parses exactly ONE frozen design source — 产品海报.psd — into CUISTANCE-specific manifests:
  - psd_layer_inventory.json   : every layer classified design_shell|replaceable_slot|reference_only|rejected_truth
  - psd_slice_manifest.json     : the cuistance_email_container_psd_v1 region/slot grammar (600px container)
  - rejected_truth_layers.json  : explicit rejection of all OLD business facts (gas réchaud / Technitalia etc.)
  - screenshots/psd_flat_reference.png    : flattened composite (design reference only)
  - screenshots/psd_slice_overlay_debug.png : regions/slots drawn over the composite (debug)

Workbench remains the only business truth source. Old PSD facts are NEVER runtime_allowed.

Usage: ./.venv/bin/python scripts/poster2_cuistance_psd_inventory.py
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw
from psd_tools import PSDImage

REPO = Path(__file__).resolve().parents[1]
BASE = REPO / "docs/poster2/assets/cuistance_psd_email_container_last_mile_v1"
PSD = BASE / "source" / "产品海报.psd"
MAN = BASE / "manifest"
SHOTS = BASE / "screenshots"
TEMPLATE_ID = "cuistance_email_container_psd_v1"

# OLD business facts that must never enter CUISTANCE runtime (substring match, case-insensitive)
REJECT_KW = [
    "gaz", "réchaud", "rechaud", "brûleur", "bruleur", "xr 144", "xr144", " kw", "kw+", "dimensions",
    "puissance", "disposition", "coup de coeur", "déclinaison", "declinaison", "technitalia", "codimatel",
    "comm andes", "catalogues", "site in ternet", "01 41 53", "kaly@", "@tec", "800*700", "2*6", "2*3.5",
]
REJECT_IMG_NAMES = {"场景配图", "产品", "产品图片"}  # old gas product / scene raster layers
SOCIAL_LABELS = {"facebook", "linkedln", "linkedin", "instagram"}


def bbox_dict(layer) -> dict:
    try:
        l, t, r, b = layer.bbox
        return {"x": int(l), "y": int(t), "w": int(r - l), "h": int(b - t)}
    except Exception:
        return {"x": 0, "y": 0, "w": 0, "h": 0}


def layer_text(layer) -> str:
    try:
        return layer.text or ""
    except Exception:
        return ""


def classify(layer):
    name = layer.name or ""
    kind = str(layer.kind)
    blob = (name + " " + layer_text(layer)).lower()
    for kw in REJECT_KW:
        if kw in blob:
            return "rejected_truth", False, f"old business fact (matched '{kw.strip()}')"
    if name == "logo banner":
        return "design_shell", True, "email header band (brand header region)"
    if name == "产品功能海报":
        return "replaceable_slot", True, "body visual stage (selected poster goes here)"
    if name in REJECT_IMG_NAMES:
        return "rejected_truth", False, "old gas product/scene raster image"
    if kind == "type":
        if name.strip().lower() in SOCIAL_LABELS:
            return "design_shell", True, "social label (layout shell, not a fact)"
        return "reference_only", False, "old campaign copy — reference only, not runtime"
    # background / groups / rectangles (dividers) / social smartobject icons = reusable container shell
    return "design_shell", True, "container shell (structure/geometry)"


def find_layer(psd, predicate):
    for l in psd.descendants():
        try:
            if predicate(l):
                return l
        except Exception:
            continue
    return None


def main() -> None:
    MAN.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    psd = PSDImage.open(PSD)
    W, H = int(psd.width), int(psd.height)

    # ---- 1. layer inventory ----
    inventory = []
    rejected = []
    visible_count = 0
    for l in psd.descendants():
        cls, allowed, reason = classify(l)
        if l.visible:
            visible_count += 1
        path = "/".join([a.name for a in l._psd._layers] ) if False else l.name  # name-only path fallback
        # build a slash path from ancestors
        parts, cur = [l.name], l
        while getattr(cur, "parent", None) is not None and getattr(cur.parent, "name", None):
            cur = cur.parent
            parts.append(cur.name)
        path = "/".join(reversed(parts))
        rec = {
            "layer_name": l.name, "path": path, "kind": str(l.kind),
            "bbox": bbox_dict(l), "visible": bool(l.visible),
            "classification": cls, "runtime_allowed": bool(allowed and cls != "rejected_truth"),
            "reason": reason,
        }
        inventory.append(rec)
        if cls == "rejected_truth":
            contains = layer_text(l).strip() or l.name
            rejected.append({
                "layer_name": l.name, "path": path,
                "contains": contains[:120],
                "reason": "old reference truth cannot enter CUISTANCE runtime",
            })

    (MAN / "psd_layer_inventory.json").write_text(json.dumps({
        "template_id": TEMPLATE_ID, "canvas": {"w": W, "h": H},
        "layer_count": len(inventory), "visible_layer_count": visible_count,
        "layers": inventory,
    }, ensure_ascii=False, indent=2))
    (MAN / "rejected_truth_layers.json").write_text(json.dumps({
        "policy": "OLD business facts (gas réchaud / Technitalia / Codimatel / old phone / email / website / "
                  "product refs / params / social handles) are NEVER runtime_allowed.",
        "rejected_count": len(rejected), "rejected_layers": rejected,
    }, ensure_ascii=False, indent=2))

    # ---- 2. slice manifest (region grammar from group bboxes; slots from specific layers) ----
    def grp(name):
        l = find_layer(psd, lambda x: x.name == name)
        return bbox_dict(l) if l else {"x": 0, "y": 0, "w": W, "h": 0}

    header = grp("logo banner")
    body = grp("产品功能海报")
    intro = grp("产品介绍")
    spec = grp("产品参数说明")
    social = grp("分享方式")
    email_l = find_layer(psd, lambda x: "@" in layer_text(x))
    phone_l = find_layer(psd, lambda x: any(c.isdigit() for c in x.name) and "53" in x.name)
    site_l = find_layer(psd, lambda x: "site" in (x.name or "").lower())

    slice_manifest = {
        "template_id": TEMPLATE_ID, "source": "产品海报.psd",
        "canvas": {"w": W, "h": H},
        "regions": [
            {"region_id": "email_header_region", "bbox": header, "runtime_role": "design_shell", "source_layers": ["logo banner"]},
            {"region_id": "body_visual_region", "bbox": body, "runtime_role": "replaceable_slot", "source_layers": ["产品功能海报"]},
            {"region_id": "intro_copy_region", "bbox": intro, "runtime_role": "design_shell", "source_layers": ["产品介绍"]},
            {"region_id": "spec_region", "bbox": spec, "runtime_role": "design_shell", "source_layers": ["产品参数说明"]},
            {"region_id": "social_contact_region", "bbox": {"x": social["x"], "y": social["y"], "w": social["w"], "h": max(social["h"] - 50, 0)}, "runtime_role": "design_shell", "source_layers": ["分享方式"]},
            {"region_id": "legal_footer_region", "bbox": {"x": 0, "y": social["y"] + max(social["h"] - 50, 0), "w": W, "h": 50}, "runtime_role": "design_shell", "source_layers": ["分享方式"]},
        ],
        "replaceable_slots": [
            {"slot_id": "brand_logo_slot", "bbox": header, "truth_source": "workbench.email_banner.logo", "required": True},
            {"slot_id": "body_visual_slot", "bbox": body, "truth_source": "workbench.selected_email_body_visual.poster.final_poster.url", "required": True},
            {"slot_id": "contact_email_slot", "bbox": bbox_dict(email_l) if email_l else {"x": 0, "y": 0, "w": 0, "h": 0}, "truth_source": "workbench.contact.email", "required": True},
            {"slot_id": "contact_phone_slot", "bbox": bbox_dict(phone_l) if phone_l else {"x": 0, "y": 0, "w": 0, "h": 0}, "truth_source": "workbench.contact.phone", "required": False},
            {"slot_id": "website_slot", "bbox": bbox_dict(site_l) if site_l else {"x": 0, "y": 0, "w": 0, "h": 0}, "truth_source": "workbench.contact.website", "required": False},
        ],
    }
    (MAN / "psd_slice_manifest.json").write_text(json.dumps(slice_manifest, ensure_ascii=False, indent=2))

    # ---- 3. screenshots: flat composite + region/slot overlay ----
    flat = psd.composite()
    if flat.mode != "RGB":
        flat = flat.convert("RGB")
    flat.save(SHOTS / "psd_flat_reference.png")

    overlay = flat.copy()
    d = ImageDraw.Draw(overlay)
    colors = {"design_shell": (40, 120, 220), "replaceable_slot": (20, 170, 90)}
    for r in slice_manifest["regions"]:
        b = r["bbox"]
        col = colors.get(r["runtime_role"], (150, 150, 150))
        d.rectangle([b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]], outline=col, width=4)
        d.text((b["x"] + 6, b["y"] + 6), r["region_id"], fill=col)
    for s in slice_manifest["replaceable_slots"]:
        b = s["bbox"]
        if b["w"] and b["h"]:
            d.rectangle([b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]], outline=(225, 0, 42), width=2)
            d.text((b["x"] + 4, b["y"] - 12), s["slot_id"], fill=(225, 0, 42))
    overlay.save(SHOTS / "psd_slice_overlay_debug.png")

    print(json.dumps({
        "canvas": {"w": W, "h": H},
        "layer_count": len(inventory), "visible_layer_count": visible_count,
        "rejected_truth_layer_count": len(rejected),
        "replaceable_slot_count": len(slice_manifest["replaceable_slots"]),
        "region_count": len(slice_manifest["regions"]),
        "header_bbox": header, "body_visual_bbox": body,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
