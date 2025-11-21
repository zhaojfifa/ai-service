"""Load poster layout templates with relative coordinates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_TEMPLATES_DIR = Path(__file__).resolve().parent


def load_layout(template_id: str) -> dict[str, Any]:
    """Load a layout JSON by template id.

    Raises FileNotFoundError / json.JSONDecodeError on invalid files so callers can surface
    configuration errors early.
    """

    template = template_id or "template_dual"
    path = _TEMPLATES_DIR / f"{template}_layout.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


__all__ = ["load_layout"]
