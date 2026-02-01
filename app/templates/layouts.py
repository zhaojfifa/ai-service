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
    for key, slot in (spec.get("slots") or {}).items():
        if not isinstance(slot, dict):
            continue
        x = float(slot.get("x", 0)) / float(canvas_w)
        y = float(slot.get("y", 0)) / float(canvas_h)
        w = float(slot.get("width", 0)) / float(canvas_w)
        h = float(slot.get("height", 0)) / float(canvas_h)
        guidance = slot.get("guidance") or {}
        text = slot.get("text") or {}
        kind = "text" if (guidance.get("mode") == "place_text" or text) else "image"
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
