from __future__ import annotations

from ...family_a_runtime import build_family_a_control_surface as _build_family_a_control_surface

SKILL_ID = "family_a_control_surface_v1"


def build_control_surface(resolved_behavior) -> dict[str, object]:
    return _build_family_a_control_surface(resolved_behavior)
