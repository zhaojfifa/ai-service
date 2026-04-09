from __future__ import annotations

from ...contracts import TemplateSpec
from ...family_a_runtime import (
    FAMILY_A_STRUCTURE_REGION_ORDER,
    build_family_a_structure_surface as _build_family_a_structure_surface,
)

SKILL_ID = "family_a_structure_surface_v1"


def build_structure_surface(
    template: TemplateSpec,
    *,
    resolved_behavior,
    layer_render_status: dict[str, dict[str, object]],
    region_render_status: dict[str, dict[str, object]],
) -> dict[str, object]:
    return _build_family_a_structure_surface(
        template,
        resolved_behavior=resolved_behavior,
        layer_render_status=layer_render_status,
        region_render_status=region_render_status,
    )


def get_region_order() -> list[str]:
    return list(FAMILY_A_STRUCTURE_REGION_ORDER)
