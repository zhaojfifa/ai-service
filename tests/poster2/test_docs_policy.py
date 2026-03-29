from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_bottom_frozen_status_doc_declares_baseline_not_tuning_log():
    text = (ROOT / "docs" / "poster2" / "bottom_behavior_contract_status_v1.md").read_text(encoding="utf-8")

    assert "Bottom is now frozen as the first SOP baseline of poster2." in text
    assert "It must not be reused as a branch-local tuning log" in text
    assert "Allowed future changes:" in text
    assert "Disallowed future changes without a new architecture decision:" in text
