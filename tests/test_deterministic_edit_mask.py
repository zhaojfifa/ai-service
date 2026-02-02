from __future__ import annotations

from app.services.glibatree import _build_editable_mask_for_template, _load_template_resources


def _center(rect: dict[str, int]) -> tuple[int, int]:
    x = int(rect.get("x", 0))
    y = int(rect.get("y", 0))
    w = int(rect.get("width", 0))
    h = int(rect.get("height", 0))
    return (x + max(w // 2, 0), y + max(h // 2, 0))


def _inside(rect: dict[str, int], point: tuple[int, int]) -> bool:
    x = int(rect.get("x", 0))
    y = int(rect.get("y", 0))
    w = int(rect.get("width", 0))
    h = int(rect.get("height", 0))
    px, py = point
    return x <= px <= x + max(w, 0) and y <= py <= y + max(h, 0)


def test_template_dual_edit_mask_protects_template_ui_and_unlocks_slots() -> None:
    template = _load_template_resources("template_dual")
    mask = _build_editable_mask_for_template(template)
    assert mask is not None
    alpha = mask.split()[-1]

    slots = template.spec.get("slots") or {}
    scenario_cx, scenario_cy = _center(slots["scenario"])
    title_cx, title_cy = _center(slots["title"])
    agent_cx, agent_cy = _center(slots["agent_name"])
    feature_callouts = template.spec.get("feature_callouts") or []
    label_box = feature_callouts[0]["label_box"]
    callout_cx, callout_cy = _center(label_box)
    product_sample = (
        int(slots["product"]["x"]) + 24,
        int(slots["product"]["y"]) + int(slots["product"]["height"]) - 24,
    )
    assert not any(_inside(c.get("label_box") or {}, product_sample) for c in feature_callouts)

    # Editable regions.
    assert alpha.getpixel((scenario_cx, scenario_cy)) == 0
    assert alpha.getpixel(product_sample) == 0
    # Protected template UI regions.
    assert alpha.getpixel((title_cx, title_cy)) == 255
    assert alpha.getpixel((agent_cx, agent_cy)) == 255
    assert alpha.getpixel((callout_cx, callout_cy)) == 255
