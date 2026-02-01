"""Load poster layout templates with relative coordinates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.schemas import TemplateLayout

_TEMPLATES_DIR = Path(__file__).resolve().parent
_FRONTEND_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "frontend" / "templates"


def _spec_to_layout(template_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    size = spec.get("size") or {}
    canvas_w = (
        spec.get("canvas_w")
        or spec.get("canvas_width")
        or size.get("width")
        or 1024
    )
    canvas_h = (
        spec.get("canvas_h")
        or spec.get("canvas_height")
        or size.get("height")
        or 1024
    )

    slots_payload = []
    TEXT_KEYS = {"brand_name", "agent_name", "title", "subtitle"}
    for key, slot in (spec.get("slots") or {}).items():
        if not isinstance(slot, dict):
            continue
        x = float(slot.get("x", 0)) / float(canvas_w)
        y = float(slot.get("y", 0)) / float(canvas_h)
        w = float(slot.get("width", 0)) / float(canvas_w)
        h = float(slot.get("height", 0)) / float(canvas_h)
        guidance = slot.get("guidance") or {}
        text = slot.get("text") or {}
        kind = (
            "text"
            if (key in TEXT_KEYS or guidance.get("mode") == "place_text" or text)
            else "image"
        )
        align = guidance.get("align") or text.get("align") or "left"
        valign = guidance.get("valign") or text.get("valign") or "middle"
        if valign == "center":
            valign = "middle"
        slots_payload.append(
            {
                "key": key,
                "kind": kind,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "align": align,
                "valign": valign,
            }
        )

    # --- Derive gallery_1..4 from spec.gallery.items (legacy/UI expects gallery_1..4) ---
    gallery = spec.get("gallery") or {}
    items = gallery.get("items") or []
    if isinstance(items, list):
        for i, it in enumerate(items[:4], start=1):
            if not isinstance(it, dict):
                continue
            gx = float(it.get("x", 0)) / float(canvas_w)
            gy = float(it.get("y", 0)) / float(canvas_h)
            gw = float(it.get("width", 0)) / float(canvas_w)
            gh = float(it.get("height", 0)) / float(canvas_h)
            slots_payload.append(
                {
                    "key": f"gallery_{i}",
                    "kind": "image",
                    "x": gx,
                    "y": gy,
                    "w": gw,
                    "h": gh,
                    "align": "center",
                    "valign": "middle",
                }
            )

    # --- Derive feature_1..4 from spec.feature_callouts[*].label_box ---
    callouts = spec.get("feature_callouts") or []
    if isinstance(callouts, list):
        for i, c in enumerate(callouts[:4], start=1):
            if not isinstance(c, dict):
                continue
            box = c.get("label_box") or {}
            if not isinstance(box, dict):
                continue
            fx = float(box.get("x", 0)) / float(canvas_w)
            fy = float(box.get("y", 0)) / float(canvas_h)
            fw = float(box.get("width", 0)) / float(canvas_w)
            fh = float(box.get("height", 0)) / float(canvas_h)
            slots_payload.append(
                {
                    "key": f"feature_{i}",
                    "kind": "text",
                    "x": fx,
                    "y": fy,
                    "w": fw,
                    "h": fh,
                    "align": "left",
                    "valign": "middle",
                }
            )

    return {
        "layout_key": template_id,
        "canvas_width": int(canvas_w),
        "canvas_height": int(canvas_h),
        "slots": slots_payload,
    }


def load_layout(template_id: str) -> TemplateLayout:
    """Load a layout JSON by template id and normalise into TemplateLayout."""

    template = template_id or "template_dual"
    spec_path = _FRONTEND_TEMPLATES_DIR / f"{template}_spec.json"
    if spec_path.exists():
        with spec_path.open("r", encoding="utf-8") as handle:
            spec: dict[str, Any] = json.load(handle)
        payload: dict[str, Any] = _spec_to_layout(template, spec)
    else:
        path = _TEMPLATES_DIR / f"{template}_layout.json"
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

    try:
        return TemplateLayout.model_validate(payload)  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover - Pydantic v1 fallback
        return TemplateLayout.parse_obj(payload)


__all__ = ["load_layout"]
