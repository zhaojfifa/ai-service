from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, constr, field_validator, model_validator

Aspect = Literal["1:1", "4:5", "4:3", "16:9", "9:16"]


class _CompatModel(BaseModel):
    """Base model configured to ignore unknown fields (Pydantic v2 only)."""

    model_config = ConfigDict(extra="ignore")


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _strip_optional(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _strip_required(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalise_prompt_payload(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}

    if isinstance(value, str):
        return {"prompt": value}

    if isinstance(value, dict):
        data = dict(value)
    elif hasattr(value, "model_dump"):
        data = value.model_dump(exclude_none=False)
    elif hasattr(value, "dict"):
        data = value.dict(exclude_none=False)
    else:
        return {"prompt": str(value)}

    if "positive" in data and "prompt" not in data:
        data["prompt"] = data.pop("positive")
    if "text" in data and "prompt" not in data:
        data["prompt"] = data.pop("text")
    if "negative" in data and "negative_prompt" not in data:
        data["negative_prompt"] = data.pop("negative")
    if "aspect_ratio" in data and "aspect" not in data:
        data["aspect"] = data.pop("aspect_ratio")

    return data


def _coerce_prompt_slot(value: Any, slot: str) -> "PromptSlotConfig":
    defaults: dict[str, str] = {
        "scenario": "1:1",
        "product": "4:5",
        "gallery": "4:3",
    }
    allowed: set[str] = {"1:1", "4:5", "4:3", "16:9", "9:16"}
    payload = _normalise_prompt_payload(value)

    aspect = payload.get("aspect") or defaults.get(slot, "1:1")
    if aspect not in allowed:
        aspect = defaults.get(slot, "1:1")

    prompt = _strip_required(payload.get("prompt"))
    negative = _strip_required(payload.get("negative_prompt"))
    preset = _strip_optional(payload.get("preset"))

    return PromptSlotConfig(preset=preset, prompt=prompt, negative_prompt=negative, aspect=aspect)


# -----------------------------------------------------------------------------
# Asset references
# -----------------------------------------------------------------------------


class AssetRef(_CompatModel):
    """Reference to an uploaded asset by key or URL."""

    key: constr(strip_whitespace=True, min_length=1) | None = Field(
        None, description="R2 storage key pointing to the asset."
    )
    url: constr(strip_whitespace=True, min_length=1) | None = Field(
        None, description="Public or signed URL to the asset."
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_str(cls, value: Any) -> Any:
        if isinstance(value, str):
            return {"url": value}
        return value

    @model_validator(mode="after")
    def _ensure_reference(self) -> "AssetRef":
        if not (self.key or self.url):
            raise ValueError("asset reference must include key or url")
        return self


class PosterGalleryItem(_CompatModel):
    """Represents a single gallery thumbnail and its optional metadata."""

    caption: constr(strip_whitespace=True, min_length=1) | None = Field(
        None, description="Optional caption describing the series thumbnail."
    )
    asset: AssetRef | None = None
    key: Optional[str] = Field(
        None, description="Optional storage key when the asset reference is absent."
    )
    mode: Literal["upload", "prompt"] = "upload"
    prompt: Optional[str] = None

    @field_validator("prompt", "key", mode="before")
    @classmethod
    def _strip_optional_text(cls, value: Any) -> Optional[str]:
        return _strip_optional(value)


# -----------------------------------------------------------------------------
# Poster payloads
# -----------------------------------------------------------------------------


class PosterInput(_CompatModel):
    """Data structure describing all poster inputs for the workflow."""

    brand_name: constr(strip_whitespace=True, min_length=1)
    agent_name: constr(strip_whitespace=True, min_length=1)
    scenario_image: constr(strip_whitespace=True, min_length=1)
    product_name: constr(strip_whitespace=True, min_length=1)

    template_id: constr(strip_whitespace=True, min_length=1) = Field(
        "template_dual",
        description="Identifier of the locked layout template to use when rendering.",
    )

    features: list[constr(strip_whitespace=True, min_length=1)] = Field(
        ...,
        min_length=3,
        max_length=4,
    )

    title: constr(strip_whitespace=True, min_length=1)
    series_description: constr(strip_whitespace=True, min_length=1)
    subtitle: constr(strip_whitespace=True, min_length=1)

    brand_logo: Optional[str] = Field(
        None,
        description="Optional data URL for the brand logo shown in the top banner.",
    )
    scenario_asset: Optional[str] = Field(
        None,
        description="Optional data URL for the scenario image displayed in the hero column.",
    )
    product_asset: Optional[str] = Field(
        None,
        description="Optional data URL for the primary product render shown on the poster.",
    )
    scenario_key: Optional[str] = Field(
        None,
        description="Optional Cloudflare R2 key for the uploaded scenario image.",
    )
    product_key: Optional[str] = Field(
        None,
        description="Optional Cloudflare R2 key for the uploaded product render.",
    )

    gallery_items: list[PosterGalleryItem] = Field(
        default_factory=list,
        max_length=4,
        description="Bottom gallery entries paired with captions for the series strip.",
    )
    gallery_label: Optional[str] = Field(
        None,
        description="Optional descriptive label for the gallery strip.",
    )
    gallery_limit: Optional[int] = Field(
        None,
        ge=0,
        le=6,
        description="Maximum number of gallery entries permitted by the template.",
    )
    gallery_allows_prompt: Optional[bool] = Field(
        None,
        description="Whether the template allows prompt-based gallery generation.",
    )
    gallery_allows_upload: Optional[bool] = Field(
        None,
        description="Whether the template allows uploading gallery assets.",
    )

    scenario_mode: Literal["upload", "prompt"] = Field(
        "upload",
        description="How the scenario asset should be sourced (upload or prompt).",
    )
    scenario_prompt: Optional[str] = Field(
        None,
        description="Prompt text used when generating the scenario asset via AI.",
    )
    product_mode: Literal["upload", "prompt"] = Field(
        "upload",
        description="How the product asset should be sourced (upload or prompt).",
    )
    product_prompt: Optional[str] = Field(
        None,
        description="Prompt text used when generating the product asset via AI.",
    )


class PosterImage(_CompatModel):
    """Represents the generated poster asset returned to the client."""

    filename: str = Field(..., description="Suggested filename for the poster image")
    media_type: str = Field(
        "image/png", description="MIME type of the generated poster image"
    )
    data_url: Optional[str] = Field(
        None,
        description="Embedded data URL (base64) fallback when object storage is unavailable",
    )
    url: Optional[str] = Field(
        None, description="Public or signed URL pointing to the generated poster asset"
    )
    storage_key: Optional[str] = Field(
        None, description="Object storage key for the generated poster when uploaded."
    )
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)


# -----------------------------------------------------------------------------
# Prompt bundle
# -----------------------------------------------------------------------------


class PromptSlotConfig(_CompatModel):
    """Normalised configuration for a single prompt slot."""

    preset: Optional[str] = None
    prompt: str = ""
    negative_prompt: str = ""
    aspect: str = ""

    @model_validator(mode="before")
    @classmethod
    def _coerce_input(cls, value: Any) -> Any:
        return _normalise_prompt_payload(value)

    @field_validator("preset", mode="before")
    @classmethod
    def _clean_preset(cls, value: Any) -> Optional[str]:
        return _strip_optional(value)

    @field_validator("prompt", "negative_prompt", mode="before")
    @classmethod
    def _clean_prompt_text(cls, value: Any) -> str:
        return _strip_required(value)

    @field_validator("aspect", mode="before")
    @classmethod
    def _clean_aspect(cls, value: Any) -> str:
        return _strip_required(value)

    # Legacy aliases (v1 schemas used positive/negative)
    @property
    def positive(self) -> str:
        return self.prompt

    @property
    def negative(self) -> str:
        return self.negative_prompt


class PromptBundle(_CompatModel):
    scenario: PromptSlotConfig = Field(default_factory=lambda: _coerce_prompt_slot({}, "scenario"))
    product: PromptSlotConfig = Field(default_factory=lambda: _coerce_prompt_slot({}, "product"))
    gallery: PromptSlotConfig = Field(default_factory=lambda: _coerce_prompt_slot({}, "gallery"))

    @field_validator("scenario", mode="before")
    @classmethod
    def _coerce_scenario(cls, value: Any) -> PromptSlotConfig:
        return _coerce_prompt_slot(value, "scenario")

    @field_validator("product", mode="before")
    @classmethod
    def _coerce_product(cls, value: Any) -> PromptSlotConfig:
        return _coerce_prompt_slot(value, "product")

    @field_validator("gallery", mode="before")
    @classmethod
    def _coerce_gallery(cls, value: Any) -> PromptSlotConfig:
        return _coerce_prompt_slot(value, "gallery")


# -----------------------------------------------------------------------------
# R2 upload helpers
# -----------------------------------------------------------------------------


class R2PresignPutRequest(_CompatModel):
    folder: str = Field(
        default="uploads",
        description="Logical directory such as scenario / product / gallery",
    )
    filename: str = Field(..., description="Original filename supplied by the browser")
    content_type: str = Field(..., description="Detected MIME type of the upload")
    size: Optional[int] = Field(
        None,
        ge=0,
        description="Optional byte size reported by the browser for validation",
    )


class R2PresignPutResponse(_CompatModel):
    key: str
    put_url: str
    public_url: Optional[str] = Field(
        None, description="Public URL when the bucket exposes a static endpoint"
    )


# -----------------------------------------------------------------------------
# Template posters
# -----------------------------------------------------------------------------


class TemplatePosterUploadRequest(_CompatModel):
    slot: Literal["variant_a", "variant_b"] = Field(
        ..., description="Target slot for the uploaded template poster variant."
    )
    filename: constr(strip_whitespace=True, min_length=1)
    content_type: constr(strip_whitespace=True, min_length=1)
    data: constr(strip_whitespace=True, min_length=1)


class TemplatePosterEntry(_CompatModel):
    slot: Literal["variant_a", "variant_b"]
    poster: PosterImage


class TemplatePosterCollection(_CompatModel):
    posters: list[TemplatePosterEntry] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Generate poster
# -----------------------------------------------------------------------------


class GeneratePosterRequest(_CompatModel):
    template_id: constr(strip_whitespace=True, min_length=1) = "template_dual"
    brand_logo: AssetRef
    scenario: AssetRef
    product: AssetRef
    gallery: list[PosterGalleryItem] = Field(default_factory=list, max_length=4)

    brand_name: Optional[constr(strip_whitespace=True, min_length=1)] = None
    agent_name: Optional[constr(strip_whitespace=True, min_length=1)] = None
    scenario_text: Optional[constr(strip_whitespace=True, min_length=1)] = None
    product_name: Optional[constr(strip_whitespace=True, min_length=1)] = None
    title: Optional[constr(strip_whitespace=True, min_length=1)] = None
    subtitle: Optional[constr(strip_whitespace=True, min_length=1)] = None
    series_description: Optional[constr(strip_whitespace=True, min_length=1)] = None
    features: list[constr(strip_whitespace=True, min_length=1)] | None = None

    prompt_bundle: PromptBundle | dict[str, Any] | None = None

    variants: int = Field(1, ge=1, le=3, description="Number of variants to generate (1–3).")
    seed: Optional[int] = Field(
        None,
        ge=0,
        description="Optional seed value used when invoking the image backend.",
    )
    lock_seed: bool = Field(False, description="Whether the provided seed should be respected across runs.")

    @model_validator(mode="before")
    @classmethod
    def _coerce_prompt_bundle(cls, data: Any) -> Any:
        if isinstance(data, dict) and "prompt_bundle" not in data and "prompts" in data:
            data = dict(data)
            data["prompt_bundle"] = data.pop("prompts")
        return data

    @field_validator("prompt_bundle", mode="before")
    @classmethod
    def _build_prompt_bundle(cls, value: PromptBundle | dict[str, Any] | None) -> PromptBundle | None:
        if value is None:
            return None
        if isinstance(value, PromptBundle):
            return value
        if isinstance(value, dict):
            return PromptBundle.model_validate(value)
        raise TypeError("prompt_bundle must be a PromptBundle, dictionary, or None")


class GeneratePosterResponse(_CompatModel):
    """Aggregated response after preparing all marketing assets."""

    layout_preview: str
    prompt: str
    email_body: str
    poster_image: PosterImage

    poster_url: Optional[str] = None
    poster_key: Optional[str] = None
    gallery_images: list[str] = Field(default_factory=list)

    prompt_details: dict[str, str] | None = Field(
        None,
        description="Per-slot prompt summary returned by the backend.",
    )

    prompt_bundle: PromptBundle | None = Field(
        None,
        description=(
            "Optional combined prompt bundle for inspector display. When provided "
            "it mirrors the PromptBundle schema."
        ),
    )

    variants: list[PosterImage] = Field(
        default_factory=list,
        description="Optional collection of variant posters for A/B comparison.",
    )

    scores: dict[str, float] | None = Field(
        None,
        description="Optional quality metrics calculated for the generated poster.",
    )

    seed: Optional[int] = Field(None, description="Seed echoed back from the backend.")
    lock_seed: Optional[bool] = Field(None, description="Whether the backend honoured the locked seed request.")

    @field_validator("prompt_bundle", mode="before")
    @classmethod
    def _coerce_prompt_bundle(cls, value: PromptBundle | dict[str, Any] | None) -> PromptBundle | None:
        if value is None or isinstance(value, PromptBundle):
            return value
        if isinstance(value, dict):
            return PromptBundle.model_validate(value)
        raise TypeError("prompt_bundle must be a PromptBundle, dictionary, or None")


# -----------------------------------------------------------------------------
# Emails
# -----------------------------------------------------------------------------


class SendEmailRequest(_CompatModel):
    """Payload expected when requesting the backend to send an email."""

    to: EmailStr
    subject: str
    body: str
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    poster_key: Optional[str] = None


class SendEmailResponse(_CompatModel):
    success: bool
    message: str | None = None


GeneratePosterRequest.model_rebuild()
GeneratePosterResponse.model_rebuild()
