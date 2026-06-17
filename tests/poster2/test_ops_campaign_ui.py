"""Tests for the additive operator page (ops_campaign) + resolver passthrough.

Verifies the dedicated CUISTANCE Email Campaign Composite operator page exists, is byte-synced between
frontend/ and docs/, hardcodes the correct route (email_campaign_composite_v1 + puppeteer), and that the
Stage2 resolvers pass the additive families through unchanged (never remapped to template_dual_v2).
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _read(p):
    return (REPO / p).read_text(encoding="utf-8")


def test_ops_campaign_page_exists_and_synced():
    for name in ("ops_campaign.html", "ops_campaign.js"):
        f = _read(f"frontend/{name}")
        d = _read(f"docs/{name}")
        assert f == d, f"{name} not byte-synced between frontend/ and docs/"


def test_ops_campaign_routes_directly_to_email_campaign_composite():
    js = _read("frontend/ops_campaign.js")
    assert "email_campaign_composite_v1" in js
    assert "renderer_mode: 'puppeteer'" in js
    assert "/api/v2/generate-poster" in js
    # send is Owner-gated (disabled in the HTML, never auto-sent in JS)
    html = _read("frontend/ops_campaign.html")
    assert 'id="send"' in html and "disabled" in html


def test_resolver_passthrough_present_in_both_app_js():
    for path in ("frontend/app.js", "docs/app.js"):
        s = _read(path)
        assert "POSTER2_DIRECT_TEMPLATE_IDS" in s
        assert "email_campaign_composite_v1" in s
        assert "catalog_hero_v1" in s


def test_registry_lists_email_campaign_option_both_mirrors():
    import json
    for path in ("frontend/templates/registry.json", "docs/templates/registry.json"):
        ids = [e["id"] for e in json.loads(_read(path))]
        assert "email_campaign_composite_v1" in ids
        # existing options preserved (no regression)
        for keep in ("template_dual", "template_dual_studio", "template_product_sheet_v1"):
            assert keep in ids


def test_ops_campaign_uses_r2_presign_not_base64():
    """The fix: assets go through /api/r2/presign-put (url/key), never inline base64 in the payload."""
    js = _read("frontend/ops_campaign.js")
    assert "/api/r2/presign-put" in js
    assert "r2UploadFile" in js
    # must NOT read files as data URLs into the generate payload anymore
    assert "readAsDataURL" not in js
    # R2-unavailable must block (no base64 fallback)
    assert "R2 upload unavailable" in js


def test_ops_campaign_handles_non_json_and_sends_request_id():
    """502 fix: ops_campaign must NOT blind-parse responses (no 'Unexpected token <') and must send X-Request-ID."""
    js = _read("frontend/ops_campaign.js")
    assert "fetchSafe" in js          # safe response reader (text + content-type)
    assert "X-Request-ID" in js       # traceable in Render logs
    assert "content-type" in js       # shows content-type on failure
    assert "newRequestId" in js
