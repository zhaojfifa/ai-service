from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())


def _truncate(value: str, limit: int) -> str:
    clean = _clean_text(value)
    if len(clean) <= limit:
        return clean
    return clean[: max(limit - 1, 0)].rstrip() + "…"


def build_deterministic_email_draft(canonical_input: dict[str, Any]) -> dict[str, Any]:
    brand_name = _clean_text(canonical_input.get("brand_name")) or "Brand"
    agent_name = _clean_text(canonical_input.get("agent_name"))
    title = _clean_text(canonical_input.get("title")) or "Poster Update"
    subtitle = _clean_text(canonical_input.get("subtitle"))
    summary_points = [
        _clean_text(item)
        for item in (canonical_input.get("summary_points") or [])
        if _clean_text(item)
    ][:3]
    final_url = _clean_text(canonical_input.get("final_poster_url"))

    subject = _truncate(f"{brand_name} | {title}", 140)
    if summary_points:
        preview_text = _truncate(" • ".join(summary_points[:2]), 160)
    elif subtitle:
        preview_text = _truncate(subtitle, 160)
    else:
        preview_text = _truncate(f"{brand_name} poster is ready to review.", 160)

    intro_line = f"{brand_name} poster is ready."
    if agent_name:
        intro_line = f"{brand_name} / {agent_name} poster is ready."

    text_lines = [intro_line, "", f"Title: {title}"]
    if summary_points:
        text_lines.extend(["", "Highlights:"])
        text_lines.extend([f"- {point}" for point in summary_points])
    elif subtitle:
        text_lines.append(f"Support line: {subtitle}")
    if final_url:
        text_lines.extend(["", f"Preview: {final_url}"])
    text = "\n".join(text_lines).strip()

    html_parts = [
        "<div style=\"font-family:Arial,sans-serif;color:#1a1917;line-height:1.5;\">",
        f"<p><strong>{escape(intro_line)}</strong></p>",
        f"<p style=\"margin:0 0 8px;\"><strong>{escape(title)}</strong></p>",
    ]
    if summary_points:
        html_parts.append("<ul style=\"margin:0 0 12px;padding-left:18px;\">")
        for point in summary_points:
            html_parts.append(f"<li>{escape(point)}</li>")
        html_parts.append("</ul>")
    elif subtitle:
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
        "summary_points": summary_points,
        "tone": "clean_product_business",
        "generated_from": "deterministic",
        "generated_at": _utc_now(),
    }


def build_email_draft_from_poster_record(record: dict[str, Any]) -> dict[str, Any]:
    from app.services.email.copy_optimizer import build_canonical_copy_input

    canonical = build_canonical_copy_input(record)
    return build_deterministic_email_draft(canonical)
