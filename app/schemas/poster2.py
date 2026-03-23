"""
Poster 2.0 — HTTP request / response Pydantic models.

Kept intentionally slim: only what the HTTP boundary needs.
Internal pipeline uses dataclasses from app.services.poster2.contracts.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


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
    logo: Optional[AssetRefInput] = None
    scenario_image: Optional[AssetRefInput] = None
    gallery_images: list[AssetRefInput] = Field(default_factory=list, max_length=4)

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
    slot_structure_layer_url: str = ""
    content_layer_url: str = ""
    text_layer_url: str = ""
    structure_overlay_url: str = ""
    slot_metadata_url: str = ""


class GeneratePosterV2Response(BaseModel):
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
    font_preflight: dict = Field(default_factory=dict)
    debug_artifacts: Poster2DebugArtifacts
    fallback_reason_code: Optional[str] = None
    fallback_reason_detail: Optional[str] = None
    degraded: bool = False
    degraded_reason: Optional[str] = None
