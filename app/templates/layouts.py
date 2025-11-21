"""Load poster layout templates with relative coordinates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.schemas import TemplateLayout

_TEMPLATES_DIR = Path(__file__).resolve().parent


def load_layout(template_id: str) -> TemplateLayout:
    """Load a layout JSON by template id and normalise into TemplateLayout."""

    template = template_id or "template_dual"
    path = _TEMPLATES_DIR / f"{template}_layout.json"
    with path.open("r", encoding="utf-8") as handle:
        payload: dict[str, Any] = json.load(handle)

    try:
        return TemplateLayout.model_validate(payload)  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover - Pydantic v1 fallback
        return TemplateLayout.parse_obj(payload)


__all__ = ["load_layout"]
