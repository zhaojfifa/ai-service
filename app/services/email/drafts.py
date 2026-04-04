from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _first_non_empty(*values: Any, default: str = "") -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return default


def build_email_draft_from_poster_record(record: dict[str, Any]) -> dict[str, str]:
    request_snapshot = record.get("request_snapshot") or {}
    render_result = record.get("render_result") or {}
    final_poster = record.get("final_poster") or {}

    brand_name = _first_non_empty(
        request_snapshot.get("brand_name"),
        render_result.get("header_contract_review", {}).get("rendered_brand_excerpt"),
        default="Brand",
    )
    agent_name = _first_non_empty(
        request_snapshot.get("agent_name"),
        render_result.get("header_contract_review", {}).get("rendered_agent_excerpt"),
    )
    title = _first_non_empty(
        request_snapshot.get("title"),
        render_result.get("title_text_layer", {}).get("rendered_excerpt"),
        default="Poster Update",
    )
    subtitle = _first_non_empty(
        request_snapshot.get("subtitle"),
        render_result.get("subtitle_text_layer", {}).get("rendered_excerpt"),
    )
    final_url = _first_non_empty(final_poster.get("url"), render_result.get("final_url"))

    subject = f"{brand_name} | {title}".strip()
    preview_text = subtitle or f"{brand_name} poster is ready to review."

    intro_line = f"{brand_name} poster is ready."
    if agent_name:
        intro_line = f"{brand_name} / {agent_name} poster is ready."

    text_lines = [
        intro_line,
        "",
        f"Title: {title}",
    ]
    if subtitle:
        text_lines.append(f"Subtitle: {subtitle}")
    if final_url:
        text_lines.extend(["", f"Preview: {final_url}"])
    text = "\n".join(text_lines).strip()

    html_parts = [
        "<div style=\"font-family:Arial,sans-serif;color:#1a1917;line-height:1.5;\">",
        f"<p><strong>{escape(intro_line)}</strong></p>",
        f"<p style=\"margin:0 0 8px;\"><strong>{escape(title)}</strong></p>",
    ]
    if subtitle:
        html_parts.append(f"<p style=\"margin:0 0 12px;color:#4f4a43;\">{escape(subtitle)}</p>")
    if final_url:
        safe_url = escape(final_url, quote=True)
        html_parts.append(
            f"<p style=\"margin:0 0 12px;\"><a href=\"{safe_url}\">Open final poster</a></p>"
        )
        html_parts.append(
            f"<p style=\"margin:0;\"><img src=\"{safe_url}\" alt=\"Poster preview\" style=\"max-width:100%;border-radius:8px;border:1px solid #e4e2de;\" /></p>"
        )
    html_parts.append("</div>")

    return {
        "subject": subject,
        "preview_text": preview_text,
        "html": "".join(html_parts),
        "text": text,
        "generated_at": _utc_now(),
    }
