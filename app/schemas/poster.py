from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

try:  # pragma: no cover - prefer Pydantic v2
    from pydantic import ConfigDict  # type: ignore
except ImportError:  # pragma: no cover - fallback for v1
    ConfigDict = None  # type: ignore

try:  # pragma: no cover - prefer v2 validators
    from pydantic import field_validator  # type: ignore
except ImportError:  # pragma: no cover - fallback for v1
    from pydantic import validator as field_validator  # type: ignore


class _CompatModel(BaseModel):
    """Base model that ignores unknown fields across supported Pydantic versions."""

    if ConfigDict is not None:  # pragma: no cover - executed on Pydantic v2
        model_config = ConfigDict(extra="allow")
    else:  # pragma: no cover - executed on Pydantic v1

        class Config:  # type: ignore[override]
            extra = "allow"


class AssetRef(_CompatModel):
    key: str
    url: Optional[str] = None

    @field_validator("key")
    @classmethod
    def no_data_uri(cls, value: str) -> str:
        if value.strip().lower().startswith("data:"):
            raise ValueError("do not send base64/data uri; upload to R2 first")
        return value


class GalleryItem(_CompatModel):
    caption: Optional[str] = None
    mode: str = "upload"
    asset: Optional[AssetRef] = None
    prompt: Optional[str] = None


class PosterPayload(_CompatModel):
    template_id: str
    brand_name: Optional[str] = None
    agent_name: Optional[str] = None
    scenario_mode: str = "upload"
    scenario_asset: Optional[AssetRef] = None
    product_mode: str = "upload"
    product_asset: Optional[AssetRef] = None
    gallery_items: list[GalleryItem] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    title: Optional[str] = None
    subtitle: Optional[str] = None


class GenerateRequest(_CompatModel):
    poster: PosterPayload
    variants: int = 1


__all__ = ["AssetRef", "GalleryItem", "PosterPayload", "GenerateRequest"]
