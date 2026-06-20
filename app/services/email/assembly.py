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

# Container flexibility — the email container is a NAMED PROFILE with deterministic per-route modes (NOT a free
# template engine). Each canonical fill format maps to exactly one internal profile name; both stay backward
# compatible with the existing fill-format values (which remain the public/selection truth).
CONTAINER_PROFILE_FOR_FILL_FORMAT: dict[str, str] = {
    "campaign_poster_email": "single_product_campaign_email",
    "product_sheet_email": "single_product_sheet_email",
}


def container_profile_for(fill_format: str | None) -> str | None:
    return CONTAINER_PROFILE_FOR_FILL_FORMAT.get(fill_format or "")


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
    "supporting_media_strip",   # fiche-only structural module (product_images[1..] + gallery_images[]); empty for affiche
    "product_description",
    "cta",
    "contact_footer",
    "legal_footer",
]

# supporting_media_strip (Fiche / single_product_sheet_email): same-product views + supporting visuals, NEVER truth.
SUPPORTING_MEDIA_MAX = 3


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
    body_visual_variant: str | None = None,
    body_visual_contains_own_banner: bool | None = None,
    standalone_poster_url: str | None = None,
    container_profile: str | None = None,
    supporting_media: list[dict[str, Any]] | None = None,
    product_image_count: int = 0,
    gallery_image_count: int = 0,
    atmosphere_present: bool = False,
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

    # product sheet (fiche / product_sheet_email): reference line + spec list from CONFIRMED workbench parameters
    is_product_sheet = (candidate_type == "fiche")
    sheet_extra = ""
    has_spec_items = False
    if is_product_sheet:
        reference = clean_copy_text(product_truth.get("reference") or "")
        spec_items = "".join(
            f'<li style="margin:3px 0;"><b>{escape(str(p.get("label") or p.get("key") or ""))}</b> '
            f'{escape(str(p.get("value") or ""))}</li>'
            for p in (product_truth.get("parameters") or []) if p and p.get("value")
        )
        has_spec_items = bool(spec_items)
        if reference:
            sheet_extra += f'<p style="margin:0 0 8px;color:#6b7178;font-size:13px;font-weight:700;">RÉF. {escape(reference)}</p>'
        if spec_items:
            sheet_extra += f'<ul style="margin:0 0 12px;padding-left:18px;font-size:13px;color:#33363b;list-style:disc;">{spec_items}</ul>'

    # ---- supporting_media_strip (Fiche-only): same-product views (product_images[1..]) then supporting visuals
    # (gallery_images[]), max 3, priority product views first. Atmosphere is NEVER included. These are supporting
    # VISUALS only — never business truth. Empty (and absent) for Affiche, whose poster already carries the views.
    strip_items: list[dict[str, Any]] = []
    if is_product_sheet and supporting_media:
        strip_items = [m for m in supporting_media if m and m.get("url")][:SUPPORTING_MEDIA_MAX]
    supporting_media_count = len(strip_items)
    supporting_media_strip_present = supporting_media_count > 0
    supporting_media_sources = [str(m.get("role") or "supporting_visual") for m in strip_items]
    primary_product_visual_present = bool(body_visual_url)
    atmosphere_used_in_fiche = False  # contract: atmosphere is visual-only, never enters the Fiche fact/visual area
    strip_cells = "".join(
        '<td style="width:33.33%;padding:0 4px;vertical-align:top;">'
        + _img(m.get("url"), style="width:100%;height:84px;object-fit:cover;border:1px solid #e4e2de;"
               "border-radius:6px;display:block;", alt=("vue produit" if m.get("role") == "same_product_view" else "détail"))
        + "</td>"
        for m in strip_items
    )
    supporting_media_strip_html = (
        '<div style="padding:0 12px 4px;">'
        '<p style="margin:0 0 6px;font-size:12px;color:#6b7178;font-weight:700;">Vues produit / Détails</p>'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" '
        'style="border-collapse:collapse;width:100%;"><tr>' + strip_cells + "</tr></table></div>"
    ) if strip_items else ""

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
        # selected body visual — the primary product visual (the ONLY place the primary poster/product image enters)
        "selected_body_visual": (
            '<div style="padding:16px;border-bottom:1px solid #e4e2de;">'
            + _img(body_visual_url, style="max-width:100%;border-radius:6px;display:block;", alt="aperçu produit")
            + "</div>"
        ),
        # supporting media strip — same-product views + supporting visuals (fiche only); never truth
        "supporting_media_strip": supporting_media_strip_html,
        "product_description": (
            '<div style="padding:12px 16px 0;">'
            + (f'<p style="margin:0 0 12px;">{escape(intro)}</p>' if intro else "")
            + sheet_extra
            + "</div>"
        ) if (intro or sheet_extra) else "",
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
    # ---- container flexibility: named profile + deterministic per-route container modes (NOT a template engine) ----
    resolved_profile = container_profile or container_profile_for(fill_format)
    header_variant = "ttt_html_header"
    if is_product_sheet:
        spec_display_mode = "spec_list" if has_spec_items else "spec_list_empty"
        resolved_body_visual_mode = body_visual_variant or "product_image"
    else:
        spec_display_mode = "in_visual"  # affiche specs are baked into the poster body visual
        resolved_body_visual_mode = body_visual_variant or "email_embedded_no_header"
    # ---- container fillability: which fields are filled from truth, and what is still missing (no fake fallback) ----
    product_name = clean_copy_text(product_truth.get("product_name") or "")
    product_reference = clean_copy_text(product_truth.get("reference") or "")
    filled_subject = bool(subject)
    filled_intro = bool(intro)
    filled_cta = bool(cta_label)
    filled_footer = bool(meta_bits)
    missing_required_fields: list[str] = []
    if not body_visual_url:
        missing_required_fields.append("product_image" if is_product_sheet else "email_body_visual")
    if is_product_sheet and not (product_name or product_reference):
        missing_required_fields.append("product_identity")
    if not subject:
        missing_required_fields.append("subject")
    if not cta_label:
        missing_required_fields.append("cta_label")
    preview_ready = not missing_required_fields
    # contract guard: a campaign_poster_email with a ttt_html_header must embed a body visual WITHOUT its own banner
    own_banner = (body_visual_contains_own_banner if body_visual_contains_own_banner is not None
                  else (template_id in _BODY_VISUALS_WITH_OWN_BANNER))
    contract_pass = not own_banner
    contract_reason = "" if contract_pass else "embedded_body_visual_contains_own_banner"
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
        # the EMBEDDED body visual's banner state (the resolver passes the no-header variant's flag); fall back to the
        # template default only if the caller did not supply it.
        "body_visual_contains_own_banner": (own_banner if own_banner is not None else (template_id in _BODY_VISUALS_WITH_OWN_BANNER)),
        "body_visual_variant": body_visual_variant,
        "standalone_poster_url": standalone_poster_url,
        "email_body_visual_url": body_visual_url,
        "email_body_visual_contract_pass": contract_pass,
        "email_body_visual_contract_reason": contract_reason,
        # fiche / product_sheet_email evidence (deterministic from Workbench truth — never poster generation)
        "fiche_uses_poster_generation": (False if is_product_sheet else None),
        "fiche_generated_from": ("workbench_truth" if is_product_sheet else None),
        "product_sheet_email_contract_pass": (bool(is_product_sheet and not own_banner) if is_product_sheet else None),
        "email_body_plan": email_body_plan,
        # PSD email container (design-shell grammar) — additive; Workbench remains the only business truth source
        "email_container_template_id": EMAIL_CONTAINER_TEMPLATE_ID,
        "email_fill_format": fill_format,
        "email_header_source": "ttt_html_header",
        # ---- container flexibility + fillability (additive diagnostics; no behavior/truth change) ----
        "container_profile": resolved_profile,
        "header_variant": header_variant,
        "spec_display_mode": spec_display_mode,
        "body_visual_mode": resolved_body_visual_mode,
        "filled_subject": filled_subject,
        "filled_intro": filled_intro,
        "filled_cta": filled_cta,
        "filled_footer": filled_footer,
        "missing_required_fields": missing_required_fields,
        "preview_ready": preview_ready,
        # ---- container structure + supporting-media fillability (structure-first) ----
        "container_modules": modules,
        "primary_product_visual_present": primary_product_visual_present,
        "supporting_media_strip_present": supporting_media_strip_present,
        "supporting_media_count": supporting_media_count,
        "supporting_media_sources": supporting_media_sources,
        "product_image_count": int(product_image_count),
        "gallery_image_count": int(gallery_image_count),
        "atmosphere_present": bool(atmosphere_present),
        "atmosphere_used_in_fiche": atmosphere_used_in_fiche,
        "email_container": {
            "email_container_template_id": EMAIL_CONTAINER_TEMPLATE_ID,
            "email_fill_format": fill_format,
            "container_profile": resolved_profile,
            "header_variant": header_variant,
            "spec_display_mode": spec_display_mode,
            "body_visual_mode": resolved_body_visual_mode,
            "filled_subject": filled_subject,
            "filled_intro": filled_intro,
            "filled_cta": filled_cta,
            "filled_footer": filled_footer,
            "missing_required_fields": missing_required_fields,
            "preview_ready": preview_ready,
            "primary_product_visual_present": primary_product_visual_present,
            "supporting_media_strip_present": supporting_media_strip_present,
            "supporting_media_count": supporting_media_count,
            "supporting_media_sources": supporting_media_sources,
            "product_image_count": int(product_image_count),
            "gallery_image_count": int(gallery_image_count),
            "atmosphere_present": bool(atmosphere_present),
            "atmosphere_used_in_fiche": atmosphere_used_in_fiche,
            "body_visual_poster_key": poster_key,
            "body_visual_variant": body_visual_variant,
            "body_visual_contains_own_banner": (own_banner if own_banner is not None else (template_id in _BODY_VISUALS_WITH_OWN_BANNER)),
            "email_body_visual_contract_pass": contract_pass,
            "email_body_visual_contract_reason": contract_reason,
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


__all__ = [
    "build_email_assembly",
    "resolve_intro",
    "EMAIL_BODY_MODULE_ORDER",
    "CONTAINER_PROFILE_FOR_FILL_FORMAT",
    "container_profile_for",
]
