"""
Poster 2.0 — HTTP request / response Pydantic models.

Kept intentionally slim: only what the HTTP boundary needs.
Internal pipeline uses dataclasses from app.services.poster2.contracts.
"""
from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator
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

    # Style (background only)
    style: StyleInput = Field(default_factory=StyleInput)

    # Rendering
    template_id: str = Field(default="template_dual_v2", max_length=80)
    export_format: str = Field(default="png", pattern=r"^(png|jpeg|webp)$")
    renderer_mode: Literal["auto", "pillow", "puppeteer"] = Field(default="auto")

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
    hero_contract_review: dict = Field(default_factory=dict)
    product_contract_review: dict = Field(default_factory=dict)
    header_contract_review: dict = Field(default_factory=dict)
    feature_contract_review: dict = Field(default_factory=dict)
    bottom_contract_review: dict = Field(default_factory=dict)
    product_annotation_contract_review: dict = Field(default_factory=dict)
    scenario_contract_review: dict = Field(default_factory=dict)
    title_text_layer: dict = Field(default_factory=dict)
    subtitle_text_layer: dict = Field(default_factory=dict)
    header_text_layer: dict = Field(default_factory=dict)


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
    generated_at: str


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
    email_deliveries: list[PosterRecordEmailDelivery] = Field(default_factory=list)


class EmailPreviewRequest(BaseModel):
    poster_key: str = Field(..., min_length=1, max_length=120)


class EmailPreviewResponse(BaseModel):
    poster_key: str
    subject: str
    preview_text: str
    html: str
    text: str
    generated_from: Literal["poster_record"] = "poster_record"


class EmailSendV2Request(BaseModel):
    poster_key: str = Field(..., min_length=1, max_length=120)
    recipient: EmailStr
    subject: Optional[str] = Field(default=None, max_length=160)
    preview_text: Optional[str] = Field(default=None, max_length=200)
    html: Optional[str] = None
    text: Optional[str] = None
    delivery_mode: Literal["inline_only", "resend"] = "inline_only"


class EmailSendV2Response(BaseModel):
    poster_key: str
    provider: str
    delivery_mode: Literal["inline_only", "resend"]
    status: Literal["preview_only", "sent", "error"]
    recipient: EmailStr
    provider_message_id: Optional[str] = None
    error: Optional[str] = None
