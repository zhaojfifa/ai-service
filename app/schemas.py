from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, constr

try:  # pragma: no cover - available only on Pydantic v2
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover
    ConfigDict = None  # type: ignore

try:  # pragma: no cover - prefer Pydantic v2 APIs when available
    from pydantic import model_validator
except ImportError:  # pragma: no cover - fall back to v1 root validators
    model_validator = None  # type: ignore
    from pydantic import root_validator

# ---- Pydantic v1/v2 兼容导入 -------------------------------------------------
try:  # Pydantic v2
    from pydantic import field_validator  # type: ignore
except ImportError:  # Pydantic v1
    from pydantic import validator as field_validator  # type: ignore

try:  # Pydantic v2
    from pydantic import model_validator  # type: ignore
except ImportError:  # Pydantic v1
    model_validator = None  # type: ignore
    from pydantic import root_validator  # type: ignore

IS_PYDANTIC_V2 = hasattr(BaseModel, "model_validate")

# ------------------------------------------------------------------------------
# 基础结构
# ------------------------------------------------------------------------------

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

    class Config:  # v1
        extra = "ignore"


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

    class Config:  # v1
        extra = "ignore"


class PosterImage(BaseModel):
    """Represents the generated poster asset returned to the client."""

    filename: str = Field(..., description="Suggested filename for the poster image")
    media_type: str = Field("image/png", description="MIME type of the generated poster image")
    data_url: Optional[str] = Field(
        None,
        description="Embedded data URL (base64) fallback when object storage is unavailable",
    )
    url: Optional[str] = Field(
        None, description="Public or signed URL pointing to the generated poster asset"
    )
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)

    class Config:  # v1
        extra = "ignore"

# ------------------------------------------------------------------------------
# Prompt 归一化工具
# ------------------------------------------------------------------------------

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


def _normalise_prompt_slot_payload(value: Any) -> dict[str, Any]:
    """Convert loose payloads into a PromptSlotConfig-compatible dict."""

    if value is None:
        return {}

    if isinstance(value, str):
        return {"prompt": value}

    if hasattr(value, "model_dump"):
        try:
            return value.model_dump(exclude_none=False)  # type: ignore[attr-defined]
        except TypeError:  # pragma: no cover - defensive
            return value.model_dump()  # type: ignore[attr-defined]

    if hasattr(value, "dict"):
        return value.dict(exclude_none=False)  # type: ignore[attr-defined]

    if isinstance(value, dict):
        data = dict(value)
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


class PromptSlotConfig(BaseModel):
    """统一的 prompt 槽结构（v1/v2 兼容校验器）"""

    preset: Optional[str] = None
    prompt: str = ""
    negative_prompt: str = ""
    aspect: str = ""

    if model_validator:  # pragma: no cover - executed on Pydantic v2

        @model_validator(mode="before")
        @classmethod
        def _coerce_input(cls, value: Any) -> Any:
            return _normalise_prompt_slot_payload(value)

    else:  # pragma: no cover - executed on Pydantic v1

        @root_validator(pre=True)
        def _coerce_input(cls, values: Any) -> Any:  # type: ignore[misc]
            return _normalise_prompt_slot_payload(values)

    @field_validator("preset", mode="before")
    @classmethod
    def _clean_preset(cls, value: Any) -> Optional[str]:
        return _strip_optional_text(value)

    @field_validator("prompt", "negative_prompt", mode="before")
    @classmethod
    def _clean_prompt_text(cls, value: Any) -> str:
        return _strip_required_text(value)

    @field_validator("aspect", mode="before")
    @classmethod
    def _clean_aspect(cls, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    if ConfigDict:  # pragma: no cover - executed on Pydantic v2
        model_config = ConfigDict(extra="ignore")
    else:  # pragma: no cover - executed on Pydantic v1

        class Config:  # type: ignore[override]
            extra = "ignore"


def _clone_prompt_slot(slot: PromptSlotConfig, **updates: Any) -> PromptSlotConfig:
    if hasattr(slot, "model_dump"):
        data = slot.model_dump(exclude_none=False)
    else:  # pragma: no cover - legacy Pydantic v1
        data = slot.dict(exclude_none=False)
    data.update(updates)
    if hasattr(PromptSlotConfig, "model_validate"):
        return PromptSlotConfig.model_validate(data)
    return PromptSlotConfig.parse_obj(data)  # type: ignore[no-any-return]


# 默认工厂：依据不同槽位给到不同默认画幅
def _default_scenario_slot() -> PromptSlotConfig:
    return _clone_prompt_slot(PromptSlotConfig(), aspect=PROMPT_SLOT_DEFAULT_ASPECT["scenario"])


def _default_product_slot() -> PromptSlotConfig:
    return _clone_prompt_slot(PromptSlotConfig(), aspect=PROMPT_SLOT_DEFAULT_ASPECT["product"])


def _default_gallery_slot() -> PromptSlotConfig:
    return _clone_prompt_slot(PromptSlotConfig(), aspect=PROMPT_SLOT_DEFAULT_ASPECT["gallery"])


# 通用的 slot 归一化函数（支持 str / dict / PromptSlotConfig）
def _coerce_prompt_slot(value: Any, slot_name: str) -> PromptSlotConfig:
    if isinstance(value, PromptSlotConfig):
        slot = value
    else:
        payload = _normalise_prompt_slot_payload(value)
        if hasattr(PromptSlotConfig, "model_validate"):
            slot = PromptSlotConfig.model_validate(payload)
        else:
            slot = PromptSlotConfig.parse_obj(payload)  # type: ignore[assignment]

    desired_aspect = _normalise_aspect(slot.aspect, slot_name)
    if slot.aspect != desired_aspect:
        slot = _clone_prompt_slot(slot, aspect=desired_aspect)
    if slot.preset == "":
        slot = _clone_prompt_slot(slot, preset=None)
    return slot


class PromptBundle(BaseModel):
    scenario: PromptSlotConfig = Field(default_factory=_default_scenario_slot)
    product: PromptSlotConfig = Field(default_factory=_default_product_slot)
    gallery: PromptSlotConfig = Field(default_factory=_default_gallery_slot)

    # 入参归一化：允许 str/dict/PromptSlotConfig
    @field_validator("scenario", mode="before")
    @classmethod
    def _coerce_scenario(cls, v: Any) -> PromptSlotConfig:
        return _coerce_prompt_slot(v, "scenario")

    @field_validator("product", mode="before")
    @classmethod
    def _coerce_product(cls, v: Any) -> PromptSlotConfig:
        return _coerce_prompt_slot(v, "product")

    @field_validator("gallery", mode="before")
    @classmethod
    def _coerce_gallery(cls, v: Any) -> PromptSlotConfig:
        return _coerce_prompt_slot(v, "gallery")

    class Config:  # v1
        extra = "ignore"

# ------------------------------------------------------------------------------
# 直传 / 预签名
# ------------------------------------------------------------------------------

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

    class Config:  # v1
        extra = "ignore"


class R2PresignPutResponse(BaseModel):
    key: str
    put_url: str
    public_url: Optional[str] = Field(
        None, description="Public URL when the bucket exposes a static endpoint"
    )

    class Config:  # v1
        extra = "ignore"

# ------------------------------------------------------------------------------
# 生成请求 / 响应
# ------------------------------------------------------------------------------

class GeneratePosterRequest(BaseModel):
    poster: PosterInput

    render_mode: Literal["locked", "hybrid", "free"] = "locked"

    variants: int = Field(1, ge=1, le=3, description="Number of variants to generate (1–3).")

    seed: Optional[int] = Field(
        None,
        ge=0,
        description="Optional seed value used when invoking the image backend.",
    )

    lock_seed: bool = Field(False, description="Whether the provided seed should be respected across runs.")

    # 新字段（结构化 prompts）
    prompt_bundle: PromptBundle = Field(
        default_factory=PromptBundle,
        description="Structured prompt overrides for each template slot.",
    )

    # 兼容旧字段名 "prompts" -> prompt_bundle
    if model_validator:  # Pydantic v2
        @model_validator(mode="before")
        @classmethod
        def _prompts_alias(cls, data: Any) -> Any:
            if isinstance(data, dict) and "prompt_bundle" not in data and "prompts" in data:
                data = dict(data)
                data["prompt_bundle"] = data.pop("prompts")
            return data
    else:  # Pydantic v1
        @root_validator(pre=True)
        def _prompts_alias(cls, values: dict[str, Any]) -> dict[str, Any]:  # type: ignore[misc]
            if "prompt_bundle" not in values and "prompts" in values:
                values = dict(values)
                values["prompt_bundle"] = values.pop("prompts")
            return values

    class Config:  # v1
        extra = "ignore"


class GeneratePosterResponse(BaseModel):
    """Aggregated response after preparing all marketing assets."""

    layout_preview: str

    # 详细字段（保持向后兼容）
    prompt: str
    email_body: str
    poster_image: PosterImage

    prompt_details: dict[str, str] | None = Field(
        None,
        description="Per-slot prompt summary returned by the backend.",
    )

    # 结构化返回（可选）
    prompt_bundle: PromptBundle | None = Field(
        None,
        description=(
            "Optional combined prompt bundle for inspector display. When provided "
            "it mirrors the PromptBundle schema."
        ),
    )

    # 兼容最初的 images 列表（例如直接返回图片 URL）
    images: list[str] = Field(
        default_factory=list,
        description="Optional list of image URLs (legacy/simple mode).",
    )

    # 变体集合
    variants: list[PosterImage] = Field(
        default_factory=list,
        description="Optional collection of variant posters for A/B comparison.",
    )

    # 可选评分
    scores: dict[str, float] | None = Field(
        None,
        description="Optional quality metrics calculated for the generated poster.",
    )

    # 随机种子与锁定标志
    seed: Optional[int] = Field(None, description="Seed echoed back from the backend.")
    lock_seed: Optional[bool] = Field(None, description="Whether the backend honoured the locked seed request.")

    @field_validator("prompt_bundle", mode="before")
    @classmethod
    def _coerce_prompt_bundle(cls, v: PromptBundle | dict[str, Any] | None) -> PromptBundle | None:
        if v is None or isinstance(v, PromptBundle):
            return v
        if isinstance(v, dict):
            if hasattr(PromptBundle, "model_validate"):
                return PromptBundle.model_validate(v)  # v2
            if hasattr(PromptBundle, "parse_obj"):
                return PromptBundle.parse_obj(v)  # v1
            return PromptBundle(**v)
        raise TypeError("prompt_bundle must be a PromptBundle, dictionary, or None")

    class Config:  # v1
        extra = "ignore"

# ------------------------------------------------------------------------------
# 邮件
# ------------------------------------------------------------------------------

class SendEmailRequest(BaseModel):
    """Payload expected when requesting the backend to send an email."""

    recipient: EmailStr
    subject: constr(strip_whitespace=True, min_length=1)
    body: constr(strip_whitespace=True, min_length=1)
    attachment: Optional[PosterImage] = Field(
        None,
        description="Optional poster attachment. When omitted the email will be sent without attachments.",
    )

    class Config:  # v1
        extra = "ignore"


class SendEmailResponse(BaseModel):
    status: Literal["sent", "skipped"]
    detail: str

    class Config:  # v1
        extra = "ignore"

# ------------------------------------------------------------------------------
# 前向引用修复（v1 与 v2）
# ------------------------------------------------------------------------------

if hasattr(GeneratePosterResponse, "model_rebuild"):  # v2
    GeneratePosterResponse.model_rebuild()
    GeneratePosterRequest.model_rebuild()
else:  # v1
    GeneratePosterResponse.update_forward_refs()
    GeneratePosterRequest.update_forward_refs()
