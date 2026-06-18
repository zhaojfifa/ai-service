"""CUISTANCE commercial trial — PR-3 Email Assembly.

Assembles the final email PREVIEW at the email level (NOT inside any poster renderer):

    Email Banner Module (workbench.email_banner)
      -> selected body visual (the selected candidate's poster_record final_poster URL)
      -> intro (product_truth.description) + CTA (Nous contacter)
      -> footer / contact (channel + campaign)

Boundary (transitional): the candidate body visuals may still carry their own logo/banner baked in by the
existing renderers (email_campaign_composite_v1 / template_product_sheet_v1). PR-3 does NOT rewrite those
renderers; it adds the first-class email-level Email Banner Module on top. Full body-only rendering would
require a renderer contract change and is out of PR-3 scope.

No technical parameter ever flows to Gemini: copy optimization happens upstream in
build_email_draft_for_poster_record over a canonical input that excludes product_truth.parameters by design.
"""
from __future__ import annotations

from html import escape
from typing import Any

from app.services.email.copy_safety import clean_copy_text, sanitize_marketing_text


# affiche bakes a banner into the composite body today; fiche has a logo_banner_region too.
_BODY_VISUALS_WITH_OWN_BANNER = {"email_campaign_composite_v1", "template_product_sheet_v1"}


def _img(url: str | None, *, style: str, alt: str) -> str:
    if not url:
        return ""
    safe = escape(str(url), quote=True)
    return f'<img src="{safe}" alt="{escape(alt)}" style="{style}" />'


def resolve_intro(product_truth: dict[str, Any] | None, draft: dict[str, Any]) -> str:
    """Intro derives from confirmed product description; falls back to the (already-sanitized) draft preview."""
    description = sanitize_marketing_text((product_truth or {}).get("description"))
    if description:
        return description
    return clean_copy_text(draft.get("preview_text") or draft.get("subject") or "")


# PR-3S — deterministic Email Body Plan: layout type + fixed module order. The selected visual enters the email
# ONLY through the selected_body_visual slot; HTML is generated from this plan (not loosely concatenated).
EMAIL_BODY_LAYOUT_TYPE = "single_product_promo"
EMAIL_BODY_CONTAINER_WIDTH = 600
EMAIL_BODY_MODULE_ORDER = [
    "email_banner",
    "title_intro",
    "selected_body_visual",
    "product_description",
    "cta",
    "contact_footer",
    "legal_footer",
]


def build_email_assembly(
    *,
    workbench: dict[str, Any],
    draft: dict[str, Any],
    body_visual_url: str | None,
    candidate_type: str,
    template_id: str | None,
    poster_key: str | None = None,
    cta_label: str = "Nous contacter",
    cta_href: str = "#",
) -> dict[str, Any]:
    banner = workbench.get("email_banner") or {}
    product_truth = workbench.get("product_truth") or {}

    logo_url = ((banner.get("logo") or {}) or {}).get("url")
    background_url = ((banner.get("background") or {}) or {}).get("url")
    pattern_url = ((banner.get("pattern") or {}) or {}).get("url")
    channel_name = clean_copy_text(banner.get("channel_name") or "")
    campaign_label = clean_copy_text(banner.get("campaign_label") or "")

    subject = clean_copy_text(draft.get("subject") or "")
    preview_text = clean_copy_text(draft.get("preview_text") or "")
    intro = resolve_intro(product_truth, draft)
    meta_bits = " · ".join([b for b in (channel_name, campaign_label) if b])

    # ---- per-module HTML fragments (reference-aligned PR-3R grammar) ----
    banner_bg = f"background-image:url('{escape(str(background_url), quote=True)}');background-size:cover;" if background_url else ""
    pattern_layer = (
        f'background-image:url(\'{escape(str(pattern_url), quote=True)}\');background-repeat:repeat;'
        if pattern_url and not background_url else ""
    )
    banner_inner = []
    if logo_url:
        banner_inner.append(_img(logo_url, style="height:40px;display:block;", alt="logo"))
    if meta_bits:
        banner_inner.append(f'<div style="margin-left:auto;color:#cfd3d8;font-size:12px;">{escape(meta_bits)}</div>')

    fragments: dict[str, str] = {
        # banner module + explicit red filet (reference grammar)
        "email_banner": (
            '<div style="background:#1f2329;' + banner_bg + pattern_layer
            + 'padding:16px 20px;display:flex;align-items:center;gap:14px;border-bottom:3px solid #E1002A;">'
            + "".join(banner_inner) + "</div>"
            + '<div style="height:3px;line-height:3px;font-size:0;background:#E1002A;">&nbsp;</div>'
        ),
        "title_intro": (
            f'<div style="padding:16px 16px 0;"><p style="margin:0;font-weight:700;font-size:16px;">{escape(subject)}</p></div>'
            if subject else ""
        ),
        # selected body visual — the ONLY place the selected poster/product image enters the email
        "selected_body_visual": (
            '<div style="padding:16px;border-bottom:1px solid #e4e2de;">'
            + _img(body_visual_url, style="max-width:100%;border-radius:6px;display:block;", alt="aperçu produit")
            + "</div>"
        ),
        "product_description": (
            f'<div style="padding:12px 16px 0;"><p style="margin:0 0 12px;">{escape(intro)}</p></div>'
            if intro else ""
        ),
        "cta": (
            '<div style="padding:0 16px 16px;">'
            + f'<a href="{escape(cta_href, quote=True)}" style="display:inline-block;background:#E1002A;color:#fff;'
            + f'font-weight:600;padding:9px 16px;border-radius:6px;text-decoration:none;">{escape(cta_label)}</a>'
            + "</div>"
        ),
        "contact_footer": (
            '<div style="background:#f7f8fa;border-top:1px solid #e4e2de;padding:14px 16px 6px;font-size:12px;color:#6b7178;">'
            + escape(meta_bits or "CUISTANCE")
            + "</div>"
        ),
        "legal_footer": (
            '<div style="background:#f7f8fa;padding:0 16px 14px;font-size:11px;color:#9aa0a6;">'
            + 'Vous recevez cet email en tant que contact professionnel CUISTANCE. · '
            + '<a href="#" style="color:#9aa0a6;text-decoration:underline;">Se désabonner</a>'
            + "</div>"
        ),
    }

    present = {key: bool(fragments[key]) for key in EMAIL_BODY_MODULE_ORDER}
    modules = [
        {"order": idx + 1, "key": key, "present": present[key]}
        for idx, key in enumerate(EMAIL_BODY_MODULE_ORDER)
    ]

    # HTML is generated FROM the plan order (deterministic).
    inner = "".join(fragments[key] for key in EMAIL_BODY_MODULE_ORDER if present[key])
    html = (
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="{EMAIL_BODY_CONTAINER_WIDTH}" '
        f'align="center" style="width:{EMAIL_BODY_CONTAINER_WIDTH}px;max-width:{EMAIL_BODY_CONTAINER_WIDTH}px;'
        'margin:0 auto;border-collapse:collapse;font-family:Arial,sans-serif;color:#1a1917;line-height:1.5;background:#ffffff;">'
        '<tr><td style="padding:0;">'
        + inner
        + "</td></tr></table>"
    )

    text_lines = [subject or intro or "CUISTANCE"]
    if intro and intro != subject:
        text_lines += ["", intro]
    if body_visual_url:
        text_lines += ["", f"Aperçu : {body_visual_url}"]
    text_lines += ["", cta_label]
    if meta_bits:
        text_lines += ["", meta_bits]
    text = "\n".join(text_lines).strip()

    email_body_plan = {
        "layout_type": EMAIL_BODY_LAYOUT_TYPE,
        "container_width": EMAIL_BODY_CONTAINER_WIDTH,
        "modules": modules,
        "selected_body_visual_slot": {
            "source": "workbench.selected_email_body_visual",
            "candidate_type": candidate_type,
            "poster_key": poster_key,
            "final_poster_url": body_visual_url,
        },
        "cta": {"label": cta_label, "href": cta_href},
    }

    return {
        "banner": {
            "logo_url": logo_url,
            "background_url": background_url,
            "pattern_url": pattern_url,
            "channel_name": channel_name,
            "campaign_label": campaign_label,
            "selected_banner_ref": banner.get("selected_banner_ref"),
        },
        "subject": subject,
        "preview_text": preview_text,
        "intro": intro,
        "cta_label": cta_label,
        "html": html,
        "text": text,
        "body_visual_contains_own_banner": (template_id in _BODY_VISUALS_WITH_OWN_BANNER),
        "email_body_plan": email_body_plan,
    }


__all__ = ["build_email_assembly", "resolve_intro", "EMAIL_BODY_MODULE_ORDER"]
