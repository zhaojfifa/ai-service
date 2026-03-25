from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_frontend_stage2_surfaces_guard_diagnostic_fields():
    html = (ROOT / "frontend" / "stage2.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")

    for marker in (
        "poster2-structure-complete",
        "poster2-incomplete-structure",
        "poster2-deliverable",
        "poster2-missing-mandatory-regions",
        "poster2-missing-required-slots",
        "poster2-region-render-status",
        "poster2-slot-binding-status",
    ):
        assert marker in html

    for field in (
        "structure_complete",
        "incomplete_structure",
        "deliverable",
        "missing_mandatory_regions",
        "missing_required_slots",
        "region_render_status",
        "slot_binding_status",
    ):
        assert field in js


def test_docs_publish_mirror_contains_same_guard_diagnostics():
    frontend_html = (ROOT / "frontend" / "stage2.html").read_text(encoding="utf-8")
    frontend_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    docs_html = (ROOT / "docs" / "stage2.html").read_text(encoding="utf-8")
    docs_js = (ROOT / "docs" / "app.js").read_text(encoding="utf-8")

    assert docs_html == frontend_html
    assert docs_js == frontend_js
