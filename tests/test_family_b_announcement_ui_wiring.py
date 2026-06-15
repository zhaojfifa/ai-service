"""Focused drift-guard for the Family B Product Announcement operator UI wiring.

Asserts the three additive display-only announcement copy slots are wired through
the frontend AND mirrored into the docs/ publish copy. This protects the Stage1 ->
payload -> Stage2 mapping from silently drifting or losing docs parity.

Scope: Family B / template_product_sheet_v1 only. No backend behavior is exercised here
(that is covered by tests/poster2/test_pipeline.py + test_api.py).
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Field tokens that must appear in the JS payload wiring (Stage1 collect + v2 payload).
APP_JS_TOKENS = [
    "availability_badge",
    "tariff_mode",
    "on_poster_cta_label",
    "on_poster_cta_email",
    "availabilityBadge",
    "tariffMode",
    "onPosterCtaLabel",
    "onPosterCtaEmail",
]

# Stage1 input element ids (operator entry surface).
INDEX_HTML_TOKENS = [
    'id="availability-badge-stage1"',
    'id="tariff-on-request-stage1"',
    'id="on-poster-cta-label-stage1"',
    'id="on-poster-cta-email-stage1"',
    'data-variant-visible="b"',
]

# Stage2 read-only summary fields.
STAGE2_HTML_TOKENS = [
    'id="s2-b-availability"',
    'id="s2-b-tariff"',
    'id="s2-b-cta"',
]


@pytest.mark.parametrize("rel", ["frontend/app.js", "docs/app.js"])
def test_app_js_has_announcement_wiring(rel):
    text = (ROOT / rel).read_text(encoding="utf-8")
    for token in APP_JS_TOKENS:
        assert token in text, f"{rel} missing announcement wiring token: {token}"


@pytest.mark.parametrize("rel", ["frontend/index.html", "docs/index.html"])
def test_index_html_has_announcement_inputs(rel):
    text = (ROOT / rel).read_text(encoding="utf-8")
    assert 'id="s1-template-b-announcement"' in text, f"{rel} missing announcement fieldset"
    for token in INDEX_HTML_TOKENS:
        assert token in text, f"{rel} missing announcement input token: {token}"


@pytest.mark.parametrize("rel", ["frontend/stage2.html", "docs/stage2.html"])
def test_stage2_html_has_announcement_summary(rel):
    text = (ROOT / rel).read_text(encoding="utf-8")
    for token in STAGE2_HTML_TOKENS:
        assert token in text, f"{rel} missing Stage2 summary token: {token}"


@pytest.mark.parametrize("rel", ["frontend/stage2_request_helpers.js", "docs/stage2_request_helpers.js"])
def test_request_summary_surfaces_announcement_fields(rel):
    text = (ROOT / rel).read_text(encoding="utf-8")
    for token in ["availability_badge", "tariff_mode", "on_poster_cta_label", "on_poster_cta_email"]:
        assert token in text, f"{rel} request summary missing: {token}"


def test_tariff_is_constrained_to_on_request_only_no_price_in_ui():
    """v1 must not expose a price entry; tariff is on_request only."""
    index = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
    # The tariff control is a single on_request checkbox; no price input/select option.
    assert 'name="tariff_on_request"' in index
    assert 'name="tariff_price"' not in index
    assert 'name="price"' not in index
    app = (ROOT / "frontend/app.js").read_text(encoding="utf-8")
    # The only tariff_mode value emitted by the UI is 'on_request'.
    assert "'on_request'" in app
