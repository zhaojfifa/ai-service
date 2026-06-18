"""CUISTANCE commercial trial — PR-2 candidate payload builder.

Pure mapping from workbench truth -> a GeneratePosterV2Request-shaped payload dict for the two Step-2 email
body visual candidates. It does NOT render and does NOT import app.main: the endpoint reuses the existing
/api/v2/generate-poster code path. Renderer logic is never forked.

Candidate types:
  - affiche -> template_id=email_campaign_composite_v1  (Affiche produit)
  - fiche   -> template_id=template_product_sheet_v1     (Fiche produit simplifiée, primary+secondary images)

PR-2 note: the Email Banner Module is NOT decoupled yet (PR-3). If the existing generation path still expects a
logo, we pass email_banner.logo through unchanged.
"""
from __future__ import annotations

from typing import Any

CANDIDATE_TEMPLATE = {
    "affiche": "email_campaign_composite_v1",
    "fiche": "template_product_sheet_v1",
}


def _ref(asset: dict[str, Any] | None) -> dict[str, Any] | None:
    if not asset or not asset.get("url"):
        return None
    out: dict[str, Any] = {"url": asset["url"]}
    if asset.get("key"):
        out["key"] = asset["key"]
    return out


def build_candidate_payload(record: dict[str, Any], candidate_type: str) -> dict[str, Any]:
    """Build a GeneratePosterV2Request-shaped dict from workbench truth.

    Raises ValueError('product_image_required') when no product image is present, or
    ValueError('invalid_candidate_type') for an unknown type.
    """
    if candidate_type not in CANDIDATE_TEMPLATE:
        raise ValueError("invalid_candidate_type")

    truth = record.get("product_truth") or {}
    assets = record.get("product_assets") or {}
    banner = record.get("email_banner") or {}

    product_images = [img for img in (assets.get("product_images") or []) if img and img.get("url")]
    if not product_images:
        raise ValueError("product_image_required")

    name = (truth.get("product_name") or truth.get("reference") or "Produit").strip() or "Produit"
    reference = (truth.get("reference") or "").strip()
    description = (truth.get("description") or "").strip()
    gallery = [g for g in (assets.get("gallery_images") or []) if g and g.get("url")]
    atmosphere = assets.get("atmosphere")
    logo_ref = _ref(banner.get("logo"))

    payload: dict[str, Any] = {
        "brand_name": (name[:80] or "CUISTANCE"),
        "agent_name": ((reference or name)[:80] or "CUISTANCE"),
        "title": name[:120],
        "subtitle": description[:120],
        "features": [],  # PR-2: empty -> candidates keep their validated default contract gates
        "product_image": _ref(product_images[0]),
        "gallery_images": [_ref(g) for g in gallery[:4]],
        "template_id": CANDIDATE_TEMPLATE[candidate_type],
    }
    scenario = _ref(atmosphere)  # atmosphere is visual-only (is_truth=false), used as substrate
    if scenario:
        payload["scenario_image"] = scenario
    if logo_ref:
        payload["logo"] = logo_ref

    if candidate_type == "affiche":
        # email_campaign_composite_v1 business truth stays deterministic (case001); puppeteer path.
        payload["renderer_mode"] = "puppeteer"
    else:  # fiche -> template_product_sheet_v1 (PosterPipeline; auto renderer)
        payload["renderer_mode"] = "auto"
        if len(product_images) > 1:
            payload["product_secondary_image"] = _ref(product_images[1])
        if reference:
            payload["sku_text"] = reference[:80]
        if description:
            payload["description_body"] = description[:500]

    return payload
