"""
Poster 2.0 — HTTP request / response Pydantic models.

Kept intentionally slim: only what the HTTP boundary needs.
Internal pipeline uses dataclasses from app.services.poster2.contracts.
"""
from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic import EmailStr


class AssetRefInput(BaseModel):
    """Flexible asset reference accepted from callers."""
    url: str
    key: Optional[str] = None

    @field_validator("url")
    @classmethod
    def url_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("asset url must not be empty")
        return v.strip()


class StyleInput(BaseModel):
    prompt: str = "clean studio background, soft diffused light"
    negative_prompt: str = "text, logo, watermark, UI elements, buttons, people"
    seed: Optional[int] = Field(default=None, ge=0, le=2**31 - 1)
    palette: Optional[list[str]] = Field(default=None, max_length=5)


class Poster2CopyOptimizationInput(BaseModel):
    mode: Literal["off", "suggest", "apply"] = "off"
    decision: Literal["pending", "accepted", "rejected"] = "pending"
    accepted_title: str = Field(default="", max_length=120)
    accepted_subtitle: str = Field(default="", max_length=120)
    accepted_features: list[str] = Field(default_factory=list, max_length=4)


class GeneratePosterV2Request(BaseModel):
    # Text content
    brand_name: str = Field(..., min_length=1, max_length=80)
    agent_name: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=120)
    subtitle: str = Field(default="", max_length=120)
    features: list[str] = Field(default_factory=list, max_length=4)

    # Assets
    product_image: AssetRefInput
    product_secondary_image: Optional[AssetRefInput] = None
    logo: Optional[AssetRefInput] = None
    scenario_image: Optional[AssetRefInput] = None
    gallery_images: list[AssetRefInput] = Field(default_factory=list, max_length=4)
    gallery_input_count_raw: Optional[int] = Field(default=None, ge=0, le=4)
    gallery_input_count_normalized: Optional[int] = Field(default=None, ge=0, le=4)
    gallery_requested_count: Optional[int] = Field(default=None, ge=0, le=4)
    gallery_autofill_applied: bool = False
    bottom_mode: Optional[Literal["title_gallery_split", "title_only", "gallery_only", "text_only_expanded", "text_gallery_expanded"]] = Field(default=None)
    gallery_mode: Optional[Literal["strip_local_visible_only", "supporting_packshots"]] = Field(default=None)

    # Template B extensions
    materials_images: list[AssetRefInput] = Field(default_factory=list, max_length=5)
    description_title: str = Field(default="", max_length=120)
    description_body: str = Field(default="", max_length=500)
    sku_text: str = Field(default="", max_length=80)

    # Family B Product Announcement variant — three additive optional copy slots.
    # All display-only; no Stage3 / send behavior. tariff_mode is on_request only
    # (a "price" value is rejected at the schema boundary — no silent fallback).
    availability_badge: str = Field(default="", max_length=40)
    tariff_mode: Optional[Literal["on_request"]] = Field(default=None)
    on_poster_cta_label: str = Field(default="", max_length=60)
    on_poster_cta_email: str = Field(default="", max_length=120)

    # Style (background only)
    style: StyleInput = Field(default_factory=StyleInput)
    copy_optimization: Poster2CopyOptimizationInput = Field(default_factory=Poster2CopyOptimizationInput)

    # Rendering
    template_id: str = Field(default="template_dual_v2", max_length=80)
    export_format: str = Field(default="png", pattern=r"^(png|jpeg|webp)$")
    renderer_mode: Literal["auto", "pillow", "puppeteer"] = Field(default="auto")
    # Composition Priority Layer (operator "海报风格策略"). Additive + optional;
    # None/"balanced" reproduces the un-composed render. Validated server-side
    # against the closed enum in app/services/poster2/composition.py.
    composition_strategy: Optional[str] = Field(default=None, max_length=40)

    model_config = {"json_schema_extra": {
        "example": {
            "brand_name": "厨厨房",
            "agent_name": "智能厨房顾问",
            "title": "烹饪更智慧，生活更美味",
            "subtitle": "系列智能厨房解决方案",
            "features": ["智能温控", "语音操控", "节能环保", "极简设计"],
            "product_image": {"url": "https://example.com/product.png"},
            "bottom_mode": "title_gallery_split",
            "gallery_mode": "strip_local_visible_only",
            "style": {"prompt": "warm kitchen atmosphere, soft bokeh", "seed": 42},
            "template_id": "template_dual_v2",
            "renderer_mode": "pillow"
        }
    }}


class Poster2DebugArtifacts(BaseModel):
    background_layer_url: str = ""
    product_material_layer_url: str = ""
    foreground_layer_url: str = ""
    final_composited_url: str = ""
    renderer_metadata_url: str = ""


class GeneratePosterV2Response(BaseModel):
    poster_key: str
    trace_id: str
    final_url: str
    final_hash: str
    foreground_url: str
    background_url: str
    background_seed: int
    background_model: str
    template_id: str
    template_version: str
    template_contract_version: str
    engine_version: str
    renderer_mode: Literal["auto", "pillow", "puppeteer"]
    render_engine_used: str
    foreground_renderer: str
    background_renderer: str
    poster_spec_hash: str
    timings_ms: dict
    debug_artifacts: Poster2DebugArtifacts
    fallback_reason_code: Optional[str] = None
    fallback_reason_detail: Optional[str] = None
    degraded: bool = False
    degraded_reason: Optional[str] = None
    structure_complete: Optional[bool] = None
    incomplete_structure: Optional[bool] = None
    deliverable: Optional[bool] = None
    structure_evidence_source: Optional[str] = None
    structure_evidence_complete: Optional[bool] = None
    missing_mandatory_regions: list[str] = Field(default_factory=list)
    missing_required_slots: list[str] = Field(default_factory=list)
    region_render_status: dict = Field(default_factory=dict)
    slot_binding_status: dict = Field(default_factory=dict)
    template_behavior: dict = Field(default_factory=dict)
    geometry_evidence: dict = Field(default_factory=dict)
    relaxation_preset: dict = Field(default_factory=dict)
    composition_strategy: dict = Field(default_factory=dict)
    hero_contract_review: dict = Field(default_factory=dict)
    product_contract_review: dict = Field(default_factory=dict)
    header_contract_review: dict = Field(default_factory=dict)
    feature_contract_review: dict = Field(default_factory=dict)
    bottom_contract_review: dict = Field(default_factory=dict)
    product_annotation_contract_review: dict = Field(default_factory=dict)
    scenario_contract_review: dict = Field(default_factory=dict)
    top_copy_contract_review: dict = Field(default_factory=dict)
    description_contract_review: dict = Field(default_factory=dict)
    announcement_variant_contract_review: dict = Field(default_factory=dict)
    title_text_layer: dict = Field(default_factory=dict)
    subtitle_text_layer: dict = Field(default_factory=dict)
    header_text_layer: dict = Field(default_factory=dict)
    copy_optimization_review: dict = Field(default_factory=dict)
    visible_truth_evidence: dict = Field(default_factory=dict)
    template_b_parity_review: Optional[dict] = None
    # Additive portrait catalog-hero family diagnostics (12-dim grammar profile +
    # contract review). Defaults None and is omitted for Family A/B responses.
    catalog_hero_contract_review: Optional[dict] = None
    catalog_hero_grammar_profile: Optional[dict] = None
    # Additive campaign-composite family diagnostics (email_campaign_composite_v1). Defaults None
    # and is omitted for Family A/B, Product Sheet, and Catalog Hero responses.
    email_campaign_composite_contract_review: Optional[dict] = None


class PosterRecordPoster(BaseModel):
    filename: str
    media_type: str = "image/png"
    width: Optional[int] = None
    height: Optional[int] = None
    storage_key: Optional[str] = None
    url: Optional[str] = None
    key: Optional[str] = None


class PosterRecordEmailDraft(BaseModel):
    subject: str
    preview_text: str
    html: str
    text: str
    summary_points: list[str] = Field(default_factory=list)
    tone: str = "clean_product_business"
    generated_from: Literal["deterministic", "gemini", "gemini_fallback_deterministic"] = "deterministic"
    generated_at: str


class PosterRecordEmailAsset(BaseModel):
    asset_type: Literal["poster_png", "poster_pdf"]
    filename: str
    content_type: str
    storage_backend: str
    size_bytes: int = 0
    created_at: str
    url: Optional[str] = None
    key: Optional[str] = None


class PosterRecordEmailDelivery(BaseModel):
    sent_at: str
    provider: str
    delivery_mode: Literal["inline_only", "resend"]
    status: Literal["preview_only", "sent", "error"]
    recipient: EmailStr
    provider_message_id: Optional[str] = None
    error: Optional[str] = None


class PosterRecordResponse(BaseModel):
    poster_key: str
    created_at: str
    updated_at: str
    template_id: str
    trace_id: str
    final_hash: str
    final_poster: PosterRecordPoster
    request_snapshot: dict[str, Any] = Field(default_factory=dict)
    render_result: dict[str, Any] = Field(default_factory=dict)
    email_draft: Optional[PosterRecordEmailDraft] = None
    email_assets: dict[str, PosterRecordEmailAsset] = Field(default_factory=dict)
    email_deliveries: list[PosterRecordEmailDelivery] = Field(default_factory=list)


class EmailPreviewRequest(BaseModel):
    poster_key: str = Field(..., min_length=1, max_length=120)


class EmailPreviewResponse(BaseModel):
    poster_key: str
    subject: str
    preview_text: str
    html: str
    text: str
    summary_points: list[str] = Field(default_factory=list)
    tone: str = "clean_product_business"
    generated_from: Literal["deterministic", "gemini", "gemini_fallback_deterministic"] = "deterministic"
    email_assets: dict[str, PosterRecordEmailAsset] = Field(default_factory=dict)
    available_attachment_types: list[str] = Field(default_factory=list)
    buildable_attachment_types: list[str] = Field(default_factory=list)


class EmailSendV2Request(BaseModel):
    poster_key: str = Field(..., min_length=1, max_length=120)
    recipient: EmailStr
    subject: Optional[str] = Field(default=None, max_length=160)
    preview_text: Optional[str] = Field(default=None, max_length=200)
    html: Optional[str] = None
    text: Optional[str] = None
    delivery_mode: Literal["inline_only", "resend"] = "inline_only"
    attachment_types: list[Literal["poster_png", "poster_pdf"]] = Field(default_factory=list, max_length=2)


class EmailSendV2Response(BaseModel):
    poster_key: str
    provider: str
    delivery_mode: Literal["inline_only", "resend"]
    status: Literal["preview_only", "sent", "error"]
    recipient: EmailStr
    provider_message_id: Optional[str] = None
    error: Optional[str] = None
    attachment_types: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# CUISTANCE commercial trial — PR-1 workbench truth model (backend-owned).
# Minimal, additive, URL/key-only. No binary/base64. No renderer/email behavior
# change. poster_candidates / selected_email_body_visual / email_package_ref /
# recipients / send_attempts are PR-2…PR-4 placeholders only.
# ---------------------------------------------------------------------------

WorkbenchLanguage = Literal["zh", "fr"]
WorkbenchStatus = Literal["draft", "assets", "candidates", "email_ready", "sent"]
ParameterKey = Literal[
    "reference", "capacity", "power", "voltage", "dimensions", "material", "thermostat", "other"
]
ParameterSource = Literal["manual", "imported", "recognized"]
ParameterState = Literal["pending", "confirmed"]


def _reject_base64(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    text = value.strip()
    low = text.lower()
    if low.startswith("data:") or ";base64," in low:
        raise ValueError("base64/data URL not allowed; use a url/key reference")
    return text


class WorkbenchAssetRef(BaseModel):
    """URL/key-only asset reference. Rejects inline base64/data URLs by design."""
    url: str = Field(..., min_length=1, max_length=2048)
    key: Optional[str] = Field(default=None, max_length=1024)

    @field_validator("url")
    @classmethod
    def _url_no_base64(cls, v: str) -> str:
        cleaned = _reject_base64(v)
        if not cleaned:
            raise ValueError("asset url must not be empty")
        return cleaned

    @field_validator("key")
    @classmethod
    def _key_no_base64(cls, v: Optional[str]) -> Optional[str]:
        return _reject_base64(v)


class WorkbenchAtmosphereAsset(WorkbenchAssetRef):
    """Atmosphere/scene image — visual-only; never business truth."""
    is_truth: Literal[False] = False


class ProductParameterRow(BaseModel):
    key: ParameterKey
    label: str = Field(default="", max_length=80)
    value: str = Field(default="", max_length=200)
    source: ParameterSource = "manual"
    state: ParameterState = "pending"
    locked: bool = False

    @model_validator(mode="after")
    def _locked_requires_confirmed(self) -> "ProductParameterRow":
        if self.locked and self.state != "confirmed":
            raise ValueError("a locked parameter row must be confirmed first")
        return self


class ProductTruth(BaseModel):
    product_name: str = Field(default="", max_length=120)
    reference: str = Field(default="", max_length=80)
    description: str = Field(default="", max_length=2000)
    parameters: list[ProductParameterRow] = Field(default_factory=list, max_length=16)
    parameters_locked: bool = False

    @model_validator(mode="after")
    def _lock_requires_all_confirmed(self) -> "ProductTruth":
        if self.parameters_locked:
            if not self.parameters:
                raise ValueError("parameters_locked requires at least one confirmed parameter row")
            if any(row.state != "confirmed" for row in self.parameters):
                raise ValueError("parameters_locked requires all parameter rows to be confirmed")
        return self


class ProductAssets(BaseModel):
    product_images: list[WorkbenchAssetRef] = Field(default_factory=list, max_length=2)
    gallery_images: list[WorkbenchAssetRef] = Field(default_factory=list, max_length=3)
    atmosphere: Optional[WorkbenchAtmosphereAsset] = None


class EmailBanner(BaseModel):
    logo: Optional[WorkbenchAssetRef] = None
    background: Optional[WorkbenchAssetRef] = None
    pattern: Optional[WorkbenchAssetRef] = None
    channel_name: str = Field(default="", max_length=80)
    campaign_label: str = Field(default="", max_length=80)
    selected_banner_ref: Optional[str] = Field(default=None, max_length=200)


class WorkbenchCreateRequest(BaseModel):
    language: WorkbenchLanguage = "zh"
    status: WorkbenchStatus = "draft"
    product_truth: Optional[ProductTruth] = None
    product_assets: Optional[ProductAssets] = None
    email_banner: Optional[EmailBanner] = None


class WorkbenchPatchRequest(BaseModel):
    language: Optional[WorkbenchLanguage] = None
    status: Optional[WorkbenchStatus] = None
    product_truth: Optional[ProductTruth] = None
    product_assets: Optional[ProductAssets] = None
    email_banner: Optional[EmailBanner] = None


# PR-2 — Step 2 email body visual candidates + selection.
CandidateType = Literal["affiche", "fiche"]


class WorkbenchSelectVisualRequest(BaseModel):
    selected_email_body_visual: CandidateType


# PR-3 — Email Banner Module + Email Assembly preview (workbench-level).
class EmailAssemblyBannerView(BaseModel):
    """First-class email-level banner module, assembled from workbench.email_banner (NOT poster body truth)."""
    logo_url: Optional[str] = None
    background_url: Optional[str] = None
    pattern_url: Optional[str] = None
    channel_name: str = ""
    campaign_label: str = ""
    selected_banner_ref: Optional[str] = None


class EmailAssemblyBodyVisual(BaseModel):
    candidate_type: CandidateType
    poster_key: str
    url: Optional[str] = None
    template_id: Optional[str] = None


# PR-3S — explicit, deterministic Email Body Plan (the selected visual enters ONLY via the planned slot).
EmailBodyModuleKey = Literal[
    "email_banner", "title_intro", "selected_body_visual", "product_description",
    "cta", "contact_footer", "legal_footer",
]


class SelectedBodyVisualSlot(BaseModel):
    source: str = "workbench.selected_email_body_visual"
    candidate_type: CandidateType
    poster_key: str
    final_poster_url: Optional[str] = None


class EmailBodyPlanModule(BaseModel):
    order: int
    key: EmailBodyModuleKey
    present: bool = True


class EmailBodyPlanCta(BaseModel):
    label: str = "Nous contacter"
    href: str = "#"


class EmailBodyPlanView(BaseModel):
    layout_type: Literal["single_product_promo"] = "single_product_promo"
    container_width: int = 600
    modules: list[EmailBodyPlanModule] = Field(default_factory=list)
    selected_body_visual_slot: SelectedBodyVisualSlot
    cta: EmailBodyPlanCta = Field(default_factory=EmailBodyPlanCta)


class EmailAssemblyPreviewResponse(BaseModel):
    workbench_key: str
    selected_email_body_visual: CandidateType
    email_body_plan: EmailBodyPlanView
    banner: EmailAssemblyBannerView
    body_visual: EmailAssemblyBodyVisual
    subject: str
    preview_text: str
    intro: str
    cta_label: str = "Nous contacter"
    html: str
    text: str
    generated_from: Literal["deterministic", "gemini", "gemini_fallback_deterministic"] = "deterministic"
    email_assets: dict[str, PosterRecordEmailAsset] = Field(default_factory=dict)
    available_attachment_types: list[str] = Field(default_factory=list)
    buildable_attachment_types: list[str] = Field(default_factory=list)
    # transitional note surfaced for diagnostics (banner decoupling status)
    body_visual_contains_own_banner: bool = False
    # PSD email container (cuistance_email_container_psd_v1) — additive, deterministic, design-shell only.
    # The container GRAMMAR derives from the frozen PSD slice manifest; all business facts come from Workbench.
    email_container_template_id: str = "cuistance_email_container_psd_v1"
    email_fill_format: Optional[Literal["campaign_poster_email", "product_sheet_email"]] = None
    email_header_source: str = "ttt_html_header"
    email_container: dict[str, Any] = Field(default_factory=dict)


# PR-4 — manual multi-recipient confirmed send + evidence.
# The send path consumes the deterministic PR-3S package verbatim; it does NOT accept arbitrary HTML/subject
# overrides (no body reconstruction).
SendMode = Literal["test", "real"]


class WorkbenchEmailSendRequest(BaseModel):
    # recipients are manual free-text strings (NOT EmailStr) so one bad address does not 422 the whole batch;
    # per-recipient validation + isolation happens server-side.
    recipients: list[str] = Field(default_factory=list, max_length=50)
    mode: SendMode = "test"
    confirm_send: bool = False
    delivery_mode: Literal["inline_only", "resend"] = "inline_only"
    attachment_types: list[Literal["poster_png", "poster_pdf"]] = Field(default_factory=list, max_length=2)


class WorkbenchSendAttempt(BaseModel):
    recipient: str
    mode: SendMode
    status: Literal["sent", "error", "skipped"]
    provider: str
    provider_message_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    attachment_types: list[str] = Field(default_factory=list)
    at: str
    selected_email_body_visual: Optional[CandidateType] = None
    body_visual_poster_key: Optional[str] = None
    layout_type: Optional[str] = None
    subject: Optional[str] = None
    deduplicated: bool = False


class WorkbenchEmailSendResponse(BaseModel):
    workbench_key: str
    mode: SendMode
    total: int
    sent_count: int
    failed_count: int
    skipped_count: int
    deduplicated_count: int
    attempts: list[WorkbenchSendAttempt] = Field(default_factory=list)


class WorkbenchRecordResponse(BaseModel):
    workbench_key: str
    created_at: str
    updated_at: str
    language: WorkbenchLanguage
    status: WorkbenchStatus
    product_truth: ProductTruth
    product_assets: ProductAssets
    email_banner: EmailBanner
    # PR-2…PR-4 placeholders (kept inert in PR-1)
    poster_candidates: dict[str, Any] = Field(default_factory=dict)
    selected_email_body_visual: Optional[Literal["affiche", "fiche"]] = None
    email_package_ref: Optional[str] = None
    recipients: list[Any] = Field(default_factory=list)
    send_attempts: list[Any] = Field(default_factory=list)
