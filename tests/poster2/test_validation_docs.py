from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _load_fixture(name: str) -> dict:
    path = ROOT / "tests" / "poster2" / "fixtures" / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_family_a_practical_closure_docs_align_with_acceptance_fixture():
    fixture = _load_fixture("family_a_practical_closure_acceptance_v1.json")
    practical_status = (
        ROOT / "docs" / "poster2" / "05_validation" / "family_a" / "family_a_practical_closure_status_v1.md"
    ).read_text(encoding="utf-8")
    matrix = (
        ROOT / "docs" / "poster2" / "05_validation" / "family_a" / "family_a_practical_closure_verification_matrix_v1.md"
    ).read_text(encoding="utf-8")
    root_matrix = (
        ROOT / "docs" / "poster2" / "05_validation" / "family_a_four_layer_verification_matrix_v1.md"
    ).read_text(encoding="utf-8")

    assert fixture["canonical_sample_name"] in practical_status
    assert fixture["final_hash"] in practical_status
    assert fixture["metadata_sha256"] in practical_status
    assert fixture["product_layout_mode"] in practical_status
    assert fixture["secondary_product_mode"] in practical_status

    assert fixture["canonical_sample_name"] in matrix
    assert fixture["final_hash"] in matrix
    assert fixture["metadata_sha256"] in matrix
    assert fixture["subtitle_state"] == "present_rendered"
    assert "subtitle present and rendered" in matrix

    assert fixture["canonical_sample_name"] in root_matrix
    assert fixture["final_hash"] in root_matrix
    assert fixture["metadata_sha256"] in root_matrix


def test_family_a_practical_closure_fixture_matches_existing_runtime_and_golden_anchors():
    acceptance = _load_fixture("family_a_practical_closure_acceptance_v1.json")
    runtime = _load_fixture("family_a_runtime_rebaseline_smoke.json")
    golden = _load_fixture("family_a_golden_sample_matrix.json")

    assert acceptance["template_id"] == runtime["template_id"] == golden["template_id"]
    assert acceptance["render_engine_used"] == runtime["expected_render_engine_used"]
    assert acceptance["degraded"] is runtime["expected_degraded"]
    assert acceptance["structure_complete"] is runtime["expected_structure_complete"]
    assert acceptance["deliverable"] is runtime["expected_deliverable"]
    assert acceptance["product_layout_mode"] == runtime["expected_behavior_modes"]["product_layout_mode"]
    assert acceptance["secondary_product_mode"] == runtime["expected_behavior_modes"]["secondary_product_mode"]
    assert any(
        sample["sample_id"] == acceptance["canonical_sample_name"]
        and sample["subtitle_present"] is True
        for sample in golden["samples"]
    )
