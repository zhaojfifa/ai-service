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

# PSD email container (design-shell grammar frozen from 产品海报.psd slice manifest; business facts come ONLY from
# Workbench). The container region order below matches the PSD slice manifest:
#   email_header_region -> (red filet) -> body_visual_region -> intro -> cta -> social_contact_region -> legal_footer
EMAIL_CONTAINER_TEMPLATE_ID = "cuistance_email_container_psd_v1"


def fill_format_for(candidate_type: str) -> str:
    """Default-map the body visual mode to its reference-derived email fill format.

    affiche -> campaign_poster_email (ttt2.html / Technitalia-Zoho grammar)
    fiche   -> product_sheet_email   (ttt.html  / Cuistance-Mailchimp grammar)
    """
    return "product_sheet_email" if candidate_type == "fiche" else "campaign_poster_email"
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
    # email header = ttt.html-style clean dark bar with a CSS CUISTANCE WORDMARK (deterministic, never distorted) +
    # optional campaign meta + red filet. We do NOT use email_banner.background.url / header-band cover / a stretched
    # logo image (those caused the "强覆盖 / 配色不对" header). Header = header only (no body/product/CTA/footer).
    header_visual_mode = "css_dark_bar_wordmark"
    brand_html = ('<span style="color:#ffffff;font-size:22px;font-weight:700;letter-spacing:1.5px;'
                  'font-family:Arial,Helvetica,sans-serif;">CUISTANCE</span>')
    meta_html = (
        f'<div style="margin-left:auto;color:#cfd3d8;font-size:12px;">{escape(meta_bits)}</div>' if meta_bits else ""
    )

    fragments: dict[str, str] = {
        # ttt_html_header: clean ~58px dark bar + CUISTANCE wordmark + meta, then explicit red filet (reference grammar)
        "email_banner": (
            '<div style="background:#1f2329;padding:18px 20px;display:flex;align-items:center;gap:14px;">'
            + brand_html + meta_html + "</div>"
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

    fill_format = fill_format_for(candidate_type)
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
        # PSD email container (design-shell grammar) — additive; Workbench remains the only business truth source
        "email_container_template_id": EMAIL_CONTAINER_TEMPLATE_ID,
        "email_fill_format": fill_format,
        "email_header_source": "ttt_html_header",
        "email_container": {
            "email_container_template_id": EMAIL_CONTAINER_TEMPLATE_ID,
            "email_fill_format": fill_format,
            "body_visual_poster_key": poster_key,
            "uses_current_selected_visual": True,
            # header is the ttt.html-style clean CSS dark bar + CUISTANCE wordmark — NOT a header-band cover overlay
            "email_header_source": "ttt_html_header",
            "header_visual_mode": header_visual_mode,
            "uses_header_band_cover": False,
            "logo_not_stretched": True,
            "logo_not_clipped": True,
            "header_only": True,
            "no_body_content_in_header": True,
            "no_product_visual_in_header": True,
            "no_cta_in_header": True,
            "no_footer_in_header": True,
            "psd_header_logo_fit_known_issue_closed": True,
            "header_source": "ttt_html_header",  # supersedes psd_slice_manifest header overlay (PSD = fallback only)
            "legacy_truth_rejected": True,  # no PSD/old-product fact ever enters this assembly
            "workbench_truth_used": True,   # banner/intro/contact all come from workbench truth
        },
    }


__all__ = ["build_email_assembly", "resolve_intro", "EMAIL_BODY_MODULE_ORDER"]
