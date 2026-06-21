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

    product_name = clean_copy_text(product_truth.get("product_name") or "")
    product_reference = clean_copy_text(product_truth.get("reference") or "")
    # product sheet (fiche / product_sheet_email): spec block in the ttt.html editorial grammar
    # (✔ red check + bold name + clean spec rows + reference line). Business facts ONLY (confirmed parameters).
    is_product_sheet = (candidate_type == "fiche")
    spec_block_html = ""
    has_spec_items = False
    if is_product_sheet:
        spec_rows = "".join(
            f'<li style="margin:4px 0;"><strong style="color:#16181b;">'
            f'{escape(str(p.get("label") or p.get("key") or ""))}</strong> : {escape(str(p.get("value") or ""))}</li>'
            for p in (product_truth.get("parameters") or []) if p and p.get("value")
        )
        has_spec_items = bool(spec_rows)
        if has_spec_items or product_reference:
            spec_block_html = (
                '<div style="display:inline-block;text-align:left;max-width:460px;margin:6px auto 0;">'
                + (f'<p style="margin:0 0 8px;font-family:Georgia,\'Times New Roman\',serif;font-size:17px;color:#16181b;">'
                   f'<span style="color:#df3004;font-weight:700;">&#10004;</span> <strong>{escape(product_name)}</strong></p>'
                   if product_name else "")
                + (f'<ul style="margin:0;padding-left:20px;font-family:Helvetica,Arial,sans-serif;font-size:14px;'
                   f'line-height:1.7;color:#454b50;list-style:disc;">{spec_rows}</ul>' if spec_rows else "")
                + (f'<p style="margin:10px 0 0;font-family:Helvetica,Arial,sans-serif;font-size:13px;color:#6b7178;">'
                   f'R&eacute;f&eacute;rence : <strong>{escape(product_reference)}</strong> &middot; Tarif = Nous contacter</p>'
                   if product_reference else "")
                + "</div>"
            )

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
        '<div style="padding:8px 28px 0;text-align:center;">'
        '<p style="margin:0 0 8px;font-family:Helvetica,Arial,sans-serif;font-size:12px;color:#8a8f94;'
        'font-weight:700;letter-spacing:1px;text-transform:uppercase;">Vues produit / D&eacute;tails</p>'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" '
        'style="border-collapse:collapse;width:100%;max-width:460px;margin:0 auto;"><tr>' + strip_cells + "</tr></table></div>"
    ) if strip_items else ""

    # ---- container visual variant (default per route): ttt.html (Fiche) / ttt2.html (Affiche) grammar ----
    container_visual_variant = "ttt_product_sheet_container" if is_product_sheet else "ttt2_campaign_container"
    footer_bg = "#333333" if is_product_sheet else "#3F3F3F"

    # ---- email_banner_composite: a first-class composite header MODULE (not just a logo flag) ----
    # variants: ttt_banner_composite (default w/ logo) | compact_logo_banner | text_wordmark_fallback.
    # header_variant (css_dark_bar_wordmark | logo_image_bar | ttt_logo_banner) is kept backward-compatible and maps
    # 1:1 to the banner_variant. DEFAULT prefers the logo composite when email_banner.logo exists. The banner/logo uses
    # email_banner.logo ONLY — NEVER product / gallery / atmosphere / generated-poster / AI visuals.
    LOGO_VARIANTS = ("ttt_logo_banner", "logo_image_bar")
    requested_header_variant = clean_copy_text(banner.get("header_variant") or "")  # "" = default (prefer logo)
    explicit_wordmark = (requested_header_variant == "css_dark_bar_wordmark")
    wants_logo = not explicit_wordmark
    has_logo = bool(logo_url)
    header_logo_missing_fallback = bool(wants_logo and not has_logo)
    if has_logo and wants_logo:
        header_variant = requested_header_variant if requested_header_variant in LOGO_VARIANTS else "ttt_logo_banner"
    else:
        header_variant = "css_dark_bar_wordmark"
    header_logo_used = header_variant in LOGO_VARIANTS
    header_visual_mode = header_variant
    # ---- ROUTE-SPECIFIC product banner variant (designer intent) ----
    #   Fiche   -> brand_standard_header  (professional product-sheet header; stable, premium, doesn't overpower title)
    #   Affiche -> campaign_poster_header (lighter/tighter framing; the generated poster body stays the hero)
    #   no usable logo -> text_fallback_header (safe fallback, not preferred)
    if not header_logo_used:
        banner_variant = "text_fallback_header"
    elif is_product_sheet:
        banner_variant = "brand_standard_header"
    else:
        banner_variant = "campaign_poster_header"
    banner_composite_used = (banner_variant != "text_fallback_header")
    banner_source = ("uploaded_logo" if header_logo_used
                     else ("default_wordmark" if explicit_wordmark else "wordmark_fallback"))
    # contrast: on_dark (default; light logo) | light_plate (dark/colored logo gets a subtle white plate so it stays
    # visible on the dark banner). Operator setting; never leave a dark logo invisible dark-on-dark.
    banner_logo_contrast_mode = clean_copy_text(banner.get("banner_logo_contrast_mode") or "") or "on_dark"
    if banner_logo_contrast_mode not in ("on_dark", "light_plate"):
        banner_logo_contrast_mode = "on_dark"
    banner_background_mode = "dark_plate"
    banner_filet_used = True

    def _brand_lockup(logo_h: int, word_size: int) -> str:
        if header_logo_used:
            img = _img(logo_url, style=f"height:{logo_h}px;max-width:230px;object-fit:contain;display:block;margin:0 auto;", alt="CUISTANCE")
            if banner_logo_contrast_mode == "light_plate":
                # subtle white plate so a dark/colored logo is never invisible on the dark banner
                return ('<span style="display:inline-block;background:#ffffff;padding:9px 16px;border-radius:10px;">'
                        + img + "</span>")
            return img
        return (f'<span style="color:#ffffff;font-size:{word_size}px;font-weight:700;letter-spacing:2px;'
                f'font-family:Georgia,\'Times New Roman\',serif;">CUISTANCE</span>')

    # route geometry + meta hierarchy:
    #   brand_standard_header : medium height, larger logo, channel line + subtle campaign (small caps, not a loud pill)
    #   campaign_poster_header: tighter height, smaller logo, compact single meta line (poster stays the hero)
    #   text_fallback_header  : medium, wordmark + channel/campaign
    if banner_variant == "brand_standard_header":
        header_pad, logo_h, word_size = "36px 24px 28px", 46, 30
        meta = " · ".join([b for b in (channel_name, campaign_label) if b])
        header_meta_html = (
            (f'<div style="margin-top:8px;height:1px;width:46px;background:rgba(255,255,255,.18);margin-left:auto;margin-right:auto;"></div>' if meta else "")
            + (f'<div style="margin-top:11px;color:#cfd4d9;font-size:11.5px;letter-spacing:2.5px;text-transform:uppercase;'
               f'font-family:Helvetica,Arial,sans-serif;">{escape(meta)}</div>' if meta else "")
        )
    elif banner_variant == "campaign_poster_header":
        header_pad, logo_h, word_size = "22px 24px 15px", 34, 24
        meta = " · ".join([b for b in (channel_name, campaign_label) if b])
        header_meta_html = (f'<div style="margin-top:8px;color:#c9ced3;font-size:11px;letter-spacing:2px;'
                            f'text-transform:uppercase;font-family:Helvetica,Arial,sans-serif;">{escape(meta)}</div>' if meta else "")
    else:  # text_fallback_header
        header_pad, logo_h, word_size = "30px 24px 24px", 26, 26
        meta = " · ".join([b for b in (channel_name, campaign_label) if b])
        header_meta_html = (f'<div style="margin-top:11px;color:#c9ced3;font-size:11px;letter-spacing:2px;'
                            f'text-transform:uppercase;font-family:Helvetica,Arial,sans-serif;">{escape(meta)}</div>' if meta else "")

    # Fiche: reference line + big serif title; description (serif) + spec block. Affiche: modest campaign lead only
    # (the generated poster already carries the product hero/title/specs — the container must NOT duplicate them).
    if is_product_sheet:
        title_intro_html = (
            '<div style="padding:34px 28px 4px;text-align:center;">'
            + (f'<p style="margin:0 0 10px;font-family:Georgia,\'Times New Roman\',serif;font-style:italic;'
               f'font-size:14px;color:#8a8f94;letter-spacing:0.5px;">R&Eacute;F&Eacute;RENCE PRODUIT : {escape(product_reference)}</p>'
               if product_reference else "")
            + (f'<h1 style="margin:0;font-family:Georgia,\'Times New Roman\',serif;font-size:30px;line-height:1.22;'
               f'font-weight:700;color:#16181b;">{escape(product_name or subject)}</h1>' if (product_name or subject) else "")
            + "</div>"
        ) if (product_name or subject or product_reference) else ""
        body_visual_html = (
            '<div style="padding:24px 28px 6px;text-align:center;">'
            + _img(body_visual_url, style="width:100%;max-width:430px;border-radius:8px;display:inline-block;border:1px solid #ececec;", alt="produit")
            + "</div>"
        ) if body_visual_url else ""
        desc_html = (
            '<div style="padding:14px 32px 0;text-align:center;">'
            + (f'<p style="margin:0 0 16px;font-family:Georgia,\'Times New Roman\',serif;font-style:italic;'
               f'font-size:16px;line-height:1.65;color:#454b50;">{escape(intro)}</p>' if intro else "")
            + spec_block_html
            + "</div>"
        ) if (intro or spec_block_html) else ""
    else:
        title_intro_html = (
            '<div style="padding:32px 28px 0;text-align:center;">'
            + (f'<h1 style="margin:0 0 8px;font-family:Georgia,\'Times New Roman\',serif;font-size:24px;line-height:1.25;'
               f'font-weight:700;color:#16181b;">{escape(subject)}</h1>' if subject else "")
            + (f'<p style="margin:0;font-family:Helvetica,Arial,sans-serif;font-size:15px;line-height:1.6;color:#5a6066;">{escape(intro)}</p>'
               if intro else "")
            + "</div>"
        ) if (subject or intro) else ""
        body_visual_html = (
            '<div style="padding:22px 24px 6px;text-align:center;">'
            + _img(body_visual_url, style="width:100%;max-width:540px;border-radius:8px;display:inline-block;", alt="affiche produit")
            + "</div>"
        ) if body_visual_url else ""
        desc_html = ""  # affiche poster carries its own product copy/specs; the container does NOT duplicate

    divider_html = ('<div style="padding:20px 28px 0;"><div style="border-top:2px solid #eaeaea;line-height:0;'
                    'font-size:0;">&nbsp;</div></div>')
    cta_html = (
        '<div style="padding:22px 28px 30px;text-align:center;">'
        + f'<a href="{escape(cta_href, quote=True)}" style="display:inline-block;background:#df3004;color:#ffffff;'
        + 'font-family:Helvetica,Arial,sans-serif;font-weight:700;font-size:16px;padding:15px 34px;border-radius:14px;'
        + f'text-decoration:none;letter-spacing:0.3px;">{escape(cta_label)}</a>'
        + "</div>"
    )

    fragments: dict[str, str] = {
        # dark header (ttt grammar): centered brand element + meta, then the red filet (#E1002A). Header only.
        "email_banner": (
            f'<div style="background:#1f2329;padding:{header_pad};text-align:center;">'
            + "<div>" + _brand_lockup(logo_h, word_size) + "</div>" + header_meta_html + "</div>"
            + '<div style="height:3px;line-height:3px;font-size:0;background:#E1002A;">&nbsp;</div>'
        ),
        "title_intro": title_intro_html,
        # selected body visual — the primary product/poster visual (the ONLY place it enters the email)
        "selected_body_visual": body_visual_html,
        # supporting media strip — same-product views + supporting visuals (fiche only); never truth
        "supporting_media_strip": supporting_media_strip_html,
        "product_description": desc_html,
        "cta": (divider_html + cta_html),
        # dark contact footer (ttt grammar): brand + CONTACT (CUISTANCE's own facts, deterministic)
        "contact_footer": (
            f'<div style="background:{footer_bg};padding:34px 24px 8px;text-align:center;">'
            + "<div>" + _brand_lockup(26, 20) + "</div>"
            + '<div style="margin-top:18px;font-family:Helvetica,Arial,sans-serif;font-size:12px;line-height:1.85;color:#e7e9ec;">'
            + '<span style="text-decoration:underline;letter-spacing:1px;">CONTACT</span><br>'
            + 'T&eacute;l&eacute;phone : +33 (0)1 71 84 11 20<br>'
            + 'Email : <a href="mailto:commercial@cuistance.eu" style="color:#ffffff;text-decoration:none;">commercial@cuistance.eu</a>'
            + "</div></div>"
        ),
        # legal footer — deterministic; NO Mailchimp tracking / list-manage unsubscribe (placeholder link only)
        "legal_footer": (
            f'<div style="background:{footer_bg};padding:8px 24px 34px;text-align:center;'
            + 'font-family:Helvetica,Arial,sans-serif;font-size:11px;line-height:1.75;color:#aeb3b8;">'
            + 'Tous droits r&eacute;serv&eacute;s &middot; <a href="https://cuistance-europe.com" style="color:#cfd3d8;text-decoration:underline;">cuistance-europe.com</a><br>'
            + '&copy; Cuistance Europe &middot; ZI Garonor, tour G, lot 409 &middot; 93600 Aulnay-sous-Bois<br>'
            + '<a href="#" style="color:#aeb3b8;text-decoration:underline;">Se désabonner</a>'
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
    # header_variant (brand-element variant: css_dark_bar_wordmark | logo_image_bar) is resolved above with the header
    # fragment. The header GRAMMAR/source stays "ttt_html_header" (email_header_source / header_source).
    if is_product_sheet:
        spec_display_mode = "spec_list" if has_spec_items else "spec_list_empty"
        resolved_body_visual_mode = body_visual_variant or "product_image"
    else:
        spec_display_mode = "in_visual"  # affiche specs are baked into the poster body visual
        resolved_body_visual_mode = body_visual_variant or "email_embedded_no_header"
    # ---- container fillability: which fields are filled from truth, and what is still missing (no fake fallback) ----
    # (product_name / product_reference resolved near the top for the ttt headline/spec grammar)
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
        "container_visual_variant": container_visual_variant,
        "banner_source": banner_source,
        "banner_replaceable": True,
        # ---- composite banner module diagnostics ----
        "banner_variant": banner_variant,
        "banner_composite_used": banner_composite_used,
        "banner_logo_url": logo_url,
        "banner_logo_contrast_mode": banner_logo_contrast_mode,
        "banner_background_mode": banner_background_mode,
        "banner_filet_used": banner_filet_used,
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
        # ---- replaceable banner/header diagnostics ----
        "header_variant": header_variant,
        "header_logo_url": logo_url,
        "header_logo_used": header_logo_used,
        "header_logo_missing_fallback": header_logo_missing_fallback,
        "header_channel_name": channel_name,
        "header_campaign_label": campaign_label,
        "email_container": {
            "email_container_template_id": EMAIL_CONTAINER_TEMPLATE_ID,
            "email_fill_format": fill_format,
            "container_profile": resolved_profile,
            "container_visual_variant": container_visual_variant,
            "banner_source": banner_source,
            "banner_replaceable": True,
            "banner_variant": banner_variant,
            "banner_composite_used": banner_composite_used,
            "banner_logo_contrast_mode": banner_logo_contrast_mode,
            "banner_background_mode": banner_background_mode,
            "banner_filet_used": banner_filet_used,
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
            "header_variant": header_variant,
            "header_logo_used": header_logo_used,
            "header_logo_missing_fallback": header_logo_missing_fallback,
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
