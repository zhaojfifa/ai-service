from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage3_consumes_live_backend_poster_and_email_payloads():
    html = (ROOT / "frontend" / "stage3.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")

    assert "email-preview-text" in html
    assert "email-text" in html
    assert "email-html" in html
    assert "refresh-email-preview" in html
    assert "email-html-preview" in html

    assert "/api/v2/posters/" in js
    assert "/api/v2/email/preview" in js
    assert "/api/v2/email/send" in js
    assert "buildStage3Url" in js
    assert "poster_key" in js
    assert "delivery_mode: 'inline_only'" in js
    assert "/api/send-email" not in js
    assert "buildEmailSubject(" not in js


def test_docs_publish_mirror_contains_same_stage3_email_closure_surface():
    frontend_html = (ROOT / "frontend" / "stage3.html").read_text(encoding="utf-8")
    frontend_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    docs_html = (ROOT / "docs" / "stage3.html").read_text(encoding="utf-8")
    docs_js = (ROOT / "docs" / "app.js").read_text(encoding="utf-8")

    assert docs_html == frontend_html
    assert docs_js == frontend_js
