from __future__ import annotations

import os
from pathlib import Path

from types import SimpleNamespace

from app.services.glibatree import (
    _build_edit_mask_for_template,
    _load_template_resources,
    _render_template_frame,
)


def _center(rect: dict[str, int]) -> tuple[int, int]:
    x = int(rect.get("x", 0))
    y = int(rect.get("y", 0))
    w = int(rect.get("width", 0))
    h = int(rect.get("height", 0))
    return (x + max(w // 2, 0), y + max(h // 2, 0))


def main() -> None:
    template = _load_template_resources("template_dual")
    edit_mask = _build_edit_mask_for_template(template)
    if edit_mask is None:
        raise RuntimeError("edit mask not built")

    dummy_poster = SimpleNamespace(
        brand_name="Brand",
        agent_name="Agent",
        scenario_asset=None,
        scenario_key=None,
        scenario_image="Scenario",
        product_asset=None,
        product_key=None,
        product_name="Product",
        title="Title",
        subtitle="Subtitle",
        features=[],
        gallery_items=[],
    )
    locked_frame = _render_template_frame(
        poster=dummy_poster,  # type: ignore[arg-type]
        template=template,
        fill_background=False,
    )

    base_dir = Path("/tmp/kitposter_debug/manual")
    base_dir.mkdir(parents=True, exist_ok=True)

    template.template.save(base_dir / "base_template.png")
    locked_frame.save(base_dir / "locked_frame.png")
    edit_mask.save(base_dir / "edit_mask.png")
    locked_frame.save(base_dir / "final_after_overlay.png")

    alpha = edit_mask
    slots = template.spec.get("slots") or {}
    scenario_cx, scenario_cy = _center(slots["scenario"])
    gallery_cx, gallery_cy = _center(slots["gallery_strip"])
    title_cx, title_cy = _center(slots["title"])
    agent_cx, agent_cy = _center(slots["agent_name"])
    callout = (template.spec.get("feature_callouts") or [])[0]["label_box"]
    callout_cx, callout_cy = _center(callout)

    assert alpha.getpixel((scenario_cx, scenario_cy)) == 255
    assert alpha.getpixel((gallery_cx, gallery_cy)) == 255
    assert alpha.getpixel((title_cx, title_cy)) == 0
    assert alpha.getpixel((agent_cx, agent_cy)) == 0
    assert alpha.getpixel((callout_cx, callout_cy)) == 0

    white = sum(1 for p in alpha.getdata() if p > 0)
    total = alpha.size[0] * alpha.size[1]
    ratio = white / total if total else 0.0
    print(f"editable_ratio={ratio:.6f}")
    print(f"artifacts={base_dir}")


if __name__ == "__main__":
    main()
