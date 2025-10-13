from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, constr

try:  # pragma: no cover - compatibility for deployments pinned to Pydantic v1
    from pydantic import field_validator
except ImportError:  # pragma: no cover
    field_validator = None  # type: ignore

try:  # pragma: no cover - available only on Pydantic v2
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover
    ConfigDict = None  # type: ignore

try:  # pragma: no cover - prefer Pydantic v2 APIs when available
    from pydantic import model_validator
except ImportError:  # pragma: no cover - fall back to v1 root validators
    model_validator = None  # type: ignore
    from pydantic import root_validator


class PosterGalleryItem(BaseModel):
    """Represents a single grayscale gallery image with an optional caption."""

    caption: constr(strip_whitespace=True, min_length=1) | None = Field(
        None,
        description="Optional caption describing the series thumbnail.",
    )
    asset: Optional[str] = Field(
        None,
        description="Data URL of the uploaded gallery image (before灰度转换).",
    )
    key: Optional[str] = Field(
        None,
        description="Object storage key pointing to the uploaded gallery asset.",
    )
    mode: Literal["upload", "prompt"] = Field(
        "upload",
        description="Whether the gallery item was uploaded or generated from a prompt.",
    )
    prompt: Optional[str] = Field(
        None,
        description="Optional text prompt when the gallery item is AI generated.",
    )


class PosterInput(BaseModel):
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
        ..., min_length=3, max_length=4
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
        description="Optional data URL for the scenario image displayed on the left column.",
    )
    product_asset: Optional[str] = Field(
        None,
        description="Optional data URL for the 45° product render showcased in the focal area.",
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


class PosterImage(BaseModel):
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
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)


Aspect = Literal["1:1", "4:5", "4:3"]


def _strip_optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _strip_required_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


class PromptSlotConfig(BaseModel):
    """Structured prompt payload for a single template slot."""

    preset: Optional[str] = Field(
        default=None,
        description="Optional preset name applied before manual prompt overrides.",
    )
    aspect: Aspect = Field(
        default="1:1",
        description="Aspect ratio hint expected by the downstream image backend.",
    )
    prompt: str = Field(
        default="",
        description="Positive prompt instructions for the slot.",
    )
    negative_prompt: str = Field(
        default="",
        description="Negative prompt instructions for the slot.",
    )

    @classmethod
    def _normalise_payload(cls, value: Any) -> Any:
        if isinstance(value, cls):
            return value.model_dump(exclude_unset=False)

        if value is None:
            return {}

        if isinstance(value, str):
            text = value.strip()
            return {"prompt": text}

        if hasattr(value, "model_dump"):
            value = value.model_dump(exclude_none=True)
        elif hasattr(value, "dict"):
            value = value.dict(exclude_none=True)

        if isinstance(value, dict):
            data = dict(value)
            if "positive" in data and "prompt" not in data:
                data["prompt"] = data.pop("positive")
            if "negative" in data and "negative_prompt" not in data:
                data["negative_prompt"] = data.pop("negative")
            if "aspect_ratio" in data and "aspect" not in data:
                data["aspect"] = data.pop("aspect_ratio")
            return data

        return value

    if model_validator:  # pragma: no cover - executed on Pydantic v2

        @model_validator(mode="before")
        def _coerce_values(cls, values: Any) -> Any:
            return cls._normalise_payload(values)

    else:  # pragma: no cover - executed on Pydantic v1

        @root_validator(pre=True)
        def _coerce_values(cls, values: Any) -> Any:
            return cls._normalise_payload(values)

    if field_validator:  # pragma: no cover - executed on Pydantic v2

        @field_validator("preset", mode="before")
        def _clean_preset(cls, value: Any) -> Optional[str]:
            return _strip_optional_text(value)

        @field_validator("prompt", "negative_prompt", mode="before")
        def _clean_prompts(cls, value: Any) -> str:
            return _strip_required_text(value)

    else:  # pragma: no cover - executed on Pydantic v1

        @root_validator
        def _clean_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
            values = dict(values)
            values["preset"] = _strip_optional_text(values.get("preset"))
            values["prompt"] = _strip_required_text(values.get("prompt"))
            values["negative_prompt"] = _strip_required_text(values.get("negative_prompt"))
            return values

    class Config:  # pragma: no cover - compatibility shim for v1
        extra = "ignore"


class PromptBundle(BaseModel):
    scenario: PromptSlotConfig = Field(
        default_factory=lambda: PromptSlotConfig(aspect="1:1"),
        description="Prompt configuration for the scenario slot.",
    )
    product: PromptSlotConfig = Field(
        default_factory=lambda: PromptSlotConfig(aspect="4:5"),
        description="Prompt configuration for the product slot.",
    )
    gallery: PromptSlotConfig = Field(
        default_factory=lambda: PromptSlotConfig(aspect="4:3"),
        description="Prompt configuration for the gallery slot.",
    )

    @classmethod
    def _normalise(cls, values: Any) -> Any:
        if isinstance(values, cls):
            return values.model_dump(exclude_unset=False)

        if values is None:
            return values

        if hasattr(values, "model_dump"):
            values = values.model_dump(exclude_none=False)
        elif hasattr(values, "dict"):
            values = values.dict(exclude_none=False)

        if isinstance(values, dict):
            data: dict[str, Any] = {}
            for slot in ("scenario", "product", "gallery"):
                if slot in values:
                    data[slot] = values[slot]
            return data

        return values

    if model_validator:  # pragma: no cover - executed on Pydantic v2

        @model_validator(mode="before")
        def _coerce_bundle(cls, values: Any) -> Any:
            return cls._normalise(values)

    else:  # pragma: no cover - executed on Pydantic v1

        @root_validator(pre=True)
        def _coerce_bundle(cls, values: dict[str, Any]) -> dict[str, Any]:
            return cls._normalise(values)

    class Config:  # pragma: no cover - compatibility shim for v1
        extra = "ignore"


def _build_prompt_bundle(value: Any) -> PromptBundle | None:
    if value is None or isinstance(value, PromptBundle):
        return value

    if hasattr(value, "model_dump"):
        value = value.model_dump(exclude_none=True)
    elif hasattr(value, "dict"):
        value = value.dict(exclude_none=True)

    if not isinstance(value, dict):
        raise TypeError("prompt_bundle must be a mapping, PromptBundle, or None")

    if hasattr(PromptBundle, "model_validate"):
        return PromptBundle.model_validate(value)
    if hasattr(PromptBundle, "parse_obj"):
        return PromptBundle.parse_obj(value)
    return PromptBundle(**value)


class R2PresignPutRequest(BaseModel):
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


class R2PresignPutResponse(BaseModel):
    key: str
    put_url: str
    public_url: Optional[str] = Field(
        None, description="Public URL when the bucket exposes a static endpoint"
    )


class GeneratePosterRequest(BaseModel):
    poster: PosterInput
    render_mode: Literal["locked", "hybrid", "free"] = "locked"
    variants: int = Field(1, ge=1, le=3)
    seed: Optional[int] = Field(
        None,
        ge=0,
        description="Optional seed value used when invoking the image backend.",
    )
    lock_seed: bool = Field(
        False, description="Whether the provided seed should be respected across runs."
    )
    prompt_bundle: PromptBundle = Field(
        default_factory=PromptBundle,
        description="Prompt inspector overrides for each template slot.",
    )

    if model_validator:  # pragma: no cover - executed on Pydantic v2

        @model_validator(mode="before")
        def _alias_prompts(cls, values: Any) -> Any:
            if isinstance(values, dict) and "prompt_bundle" not in values and "prompts" in values:
                values = dict(values)
                values["prompt_bundle"] = values.pop("prompts")
            return values

    else:  # pragma: no cover - executed on Pydantic v1

        @root_validator(pre=True)
        def _alias_prompts(cls, values: dict[str, Any]) -> dict[str, Any]:
            if "prompt_bundle" not in values and "prompts" in values:
                values = dict(values)
                values["prompt_bundle"] = values.pop("prompts")
            return values

    if ConfigDict:  # pragma: no cover - executed on Pydantic v2
        model_config = ConfigDict(populate_by_name=True)
    else:  # pragma: no cover - executed on Pydantic v1

        class Config:  # type: ignore[override]
            allow_population_by_field_name = True


class GeneratePosterResponse(BaseModel):
    """Aggregated response after preparing all marketing assets."""

    layout_preview: str
    prompt: str
    email_body: str
    poster_image: PosterImage
    prompt_details: dict[str, str] | None = Field(
        None, description="Per-slot prompt summary returned by the backend."
    )
    prompt_bundle: PromptBundle | None = Field(
        None,
        description="Optional combined prompt bundle for inspector display.",
    )
    variants: list[PosterImage] = Field(
        default_factory=list,
        description="Optional collection of variant posters for A/B comparison.",
    )
    scores: dict[str, float] | None = Field(
        None, description="Optional quality metrics calculated for the generated poster."
    )
    seed: Optional[int] = Field(None, description="Seed echoed back from the backend.")
    lock_seed: Optional[bool] = Field(
        None, description="Whether the backend honoured the locked seed request."
    )

    if model_validator:  # pragma: no cover - executed on Pydantic v2

        @model_validator(mode="before")
        def _coerce_bundle(cls, values: Any) -> Any:
            if isinstance(values, dict) and "prompt_bundle" in values:
                values = dict(values)
                values["prompt_bundle"] = _build_prompt_bundle(values["prompt_bundle"])
            return values

    else:  # pragma: no cover - executed on Pydantic v1

        @root_validator(pre=True)
        def _coerce_bundle(cls, values: dict[str, Any]) -> dict[str, Any]:
            if "prompt_bundle" in values:
                values = dict(values)
                values["prompt_bundle"] = _build_prompt_bundle(values["prompt_bundle"])
            return values


class SendEmailRequest(BaseModel):
    """Payload expected when requesting the backend to send an email."""

    recipient: EmailStr
    subject: constr(strip_whitespace=True, min_length=1)
    body: constr(strip_whitespace=True, min_length=1)
    attachment: Optional[PosterImage] = Field(
        None,
        description=
        "Optional poster attachment. When omitted the email will be sent without attachments.",
    )


class SendEmailResponse(BaseModel):
    status: Literal["sent", "skipped"]
    detail: str

