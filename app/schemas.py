from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, constr
try:  # pragma: no cover - fallback for Pydantic v1 deployments
    from pydantic import field_validator
except ImportError:  # pragma: no cover
    from pydantic import validator as field_validator
try:  # pragma: no cover - Pydantic v2 preferred API
    from pydantic import model_validator
except ImportError:  # pragma: no cover - compatibility with Pydantic v1
    model_validator = None  # type: ignore
    from pydantic import root_validator
from typing import Any, Literal, Optional


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


def _coerce_prompt_text(value: Any) -> str | None:
    """Convert rich prompt slot payloads into trimmed strings.

    The legacy UI used to send dictionaries shaped like ``PromptSlotConfig``
    while the backend schema expected bare strings. Render still runs that
    schema, so we need to collapse any structured payloads into a single
    positive prompt string.
    """

    if value is None:
        return None

    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None

    # PromptSlotConfig-like objects expose the fields as attributes.
    if hasattr(value, "model_dump"):
        value = value.model_dump(exclude_none=True)
    elif hasattr(value, "dict"):
        value = value.dict(exclude_none=True)

    if isinstance(value, dict):
        positive = value.get("positive") or value.get("prompt") or value.get("text")
        preset = value.get("preset")
        aspect = value.get("aspect")
        parts: list[str] = []

        if isinstance(positive, str) and positive.strip():
            parts.append(positive.strip())
        if isinstance(preset, str) and preset.strip():
            parts.append(f"Preset: {preset.strip()}")
        if isinstance(aspect, str) and aspect.strip():
            parts.append(f"Aspect: {aspect.strip()}")

        if parts:
            return " | ".join(parts)

    try:
        text = str(value)
    except Exception:  # pragma: no cover - defensive fallback
        return None

    stripped = text.strip()
    return stripped or None


Aspect = Literal["1:1", "4:5", "4:3"]


PROMPT_SLOT_DEFAULT_ASPECT: dict[str, Aspect] = {
    "scenario": "1:1",
    "product": "4:5",
    "gallery": "4:3",
}


def _normalise_aspect(value: Any, slot: str) -> Aspect:
    if isinstance(value, str):
        candidate = value.strip()
        if candidate in {"1:1", "4:5", "4:3"}:
            return candidate  # type: ignore[return-value]
    return PROMPT_SLOT_DEFAULT_ASPECT[slot]


def _coerce_prompt_slot(value: Any, slot: str) -> "PromptSlotConfig":
    if isinstance(value, PromptSlotConfig):
        return value

    if value is None:
        return PromptSlotConfig(aspect=PROMPT_SLOT_DEFAULT_ASPECT[slot])

    if hasattr(value, "model_dump"):
        value = value.model_dump(exclude_none=True)
    elif hasattr(value, "dict"):
        value = value.dict(exclude_none=True)

    if isinstance(value, str):
        text = value.strip()
        return PromptSlotConfig(
            aspect=PROMPT_SLOT_DEFAULT_ASPECT[slot],
            prompt=text,
        )

    if isinstance(value, dict):
        preset = value.get("preset")
        prompt = (
            value.get("prompt")
            or value.get("positive")
            or value.get("text")
            or ""
        )
        negative = value.get("negative_prompt") or value.get("negative") or ""
        aspect = value.get("aspect") or value.get("aspect_ratio")
        return PromptSlotConfig(
            preset=preset,
            aspect=_normalise_aspect(aspect, slot),
            prompt=prompt or "",
            negative_prompt=negative or "",
        )

    return PromptSlotConfig(
        aspect=PROMPT_SLOT_DEFAULT_ASPECT[slot],
        prompt=str(value).strip(),
    )


class PromptSlotConfig(BaseModel):
    preset: Optional[str] = None
    aspect: Aspect
    prompt: str = ""
    negative_prompt: str = ""

    @field_validator("preset", mode="before")
    @classmethod
    def _clean_preset(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("prompt", "negative_prompt", mode="before")
    @classmethod
    def _clean_prompt(cls, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    class Config:  # pragma: no cover - compatibility shim
        extra = "ignore"


def _default_scenario_slot() -> PromptSlotConfig:
    return PromptSlotConfig(aspect=PROMPT_SLOT_DEFAULT_ASPECT["scenario"])


def _default_product_slot() -> PromptSlotConfig:
    return PromptSlotConfig(aspect=PROMPT_SLOT_DEFAULT_ASPECT["product"])


def _default_gallery_slot() -> PromptSlotConfig:
    return PromptSlotConfig(aspect=PROMPT_SLOT_DEFAULT_ASPECT["gallery"])


class PromptBundle(BaseModel):
    scenario: PromptSlotConfig = Field(default_factory=_default_scenario_slot)
    product: PromptSlotConfig = Field(default_factory=_default_product_slot)
    gallery: PromptSlotConfig = Field(default_factory=_default_gallery_slot)

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

    class Config:  # pragma: no cover - compatibility shim
        extra = "ignore"


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
        description="Structured prompt overrides for each template slot.",
    )

    if model_validator:  # pragma: no cover - executed only on Pydantic v2
        @model_validator(mode="before")
        @classmethod
        def _prompts_alias(cls, data: Any) -> Any:
            if isinstance(data, dict) and "prompt_bundle" not in data and "prompts" in data:
                data = dict(data)
                data["prompt_bundle"] = data.pop("prompts")
            return data
    else:  # pragma: no cover - executed only on Pydantic v1
        @root_validator(pre=True)
        def _prompts_alias(cls, values: dict[str, Any]) -> dict[str, Any]:
            if "prompt_bundle" not in values and "prompts" in values:
                values = dict(values)
                values["prompt_bundle"] = values.pop("prompts")
            return values


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
        description=(
            "Optional combined prompt bundle for inspector display. When provided "
            "it mirrors the PromptBundle schema composed of PromptSlotConfig "
            "objects so the UI can repopulate the inspector overrides."
        ),
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

    @field_validator("prompt_bundle", mode="before")
    @classmethod
    def _coerce_prompt_bundle(
        cls, value: PromptBundle | dict[str, Any] | None
    ) -> PromptBundle | None:
        """Normalise prompt bundles coming from external services."""

        if value is None or isinstance(value, PromptBundle):
            return value

        if isinstance(value, dict):
            if hasattr(PromptBundle, "model_validate"):
                return PromptBundle.model_validate(value)
            if hasattr(PromptBundle, "parse_obj"):
                return PromptBundle.parse_obj(value)
            return PromptBundle(**value)

        raise TypeError(
            "prompt_bundle must be a PromptBundle, dictionary, or None"
        )


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
