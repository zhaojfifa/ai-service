"""Lightweight poster payload schemas for asset validation."""
from __future__ import annotations

from typing import Any, List, Optional

from pydantic import Field

from app.schemas import DATA_URL_RX, _CompatModel, field_validator, model_validator, root_validator

_ALLOWED_URL_PREFIXES = ("r2://", "s3://", "gs://", "https://", "http://")


class AssetRef(_CompatModel):
    """Reference to an uploaded asset (by key and/or URL)."""

    url: Optional[str] = None
    key: Optional[str] = None

    if model_validator is not None:  # pragma: no cover - executed on Pydantic v2

        @model_validator(mode="before")
        @classmethod
        def _coerce(cls, value: Any) -> Any:
            if value is None or isinstance(value, cls):
                return value
            if isinstance(value, str):
                return {"url": value}
            if isinstance(value, dict):
                return value
            data: dict[str, Any] = {}
            for attr in (
                "url",
                "asset",
                "public_url",
                "publicUrl",
                "remote_url",
                "remoteUrl",
                "cdn_url",
                "cdnUrl",
                "data_url",
                "dataUrl",
            ):
                candidate = getattr(value, attr, None)
                if isinstance(candidate, str):
                    data.setdefault("url", candidate)
            for attr in ("key", "r2Key"):
                candidate = getattr(value, attr, None)
                if isinstance(candidate, str):
                    data.setdefault("key", candidate)
            return data or value
    else:  # pragma: no cover - executed on Pydantic v1

        @root_validator(pre=True)
        def _coerce(cls, values: Any) -> Any:  # type: ignore[override]
            value = values
            if value is None or isinstance(value, cls):
                return value
            if isinstance(value, str):
                return {"url": value}
            if isinstance(value, dict):
                return value
            data: dict[str, Any] = {}
            for attr in (
                "url",
                "asset",
                "public_url",
                "publicUrl",
                "remote_url",
                "remoteUrl",
                "cdn_url",
                "cdnUrl",
                "data_url",
                "dataUrl",
            ):
                candidate = getattr(value, attr, None)
                if isinstance(candidate, str):
                    data.setdefault("url", candidate)
            for attr in ("key", "r2Key"):
                candidate = getattr(value, attr, None)
                if isinstance(candidate, str):
                    data.setdefault("key", candidate)
            return data or values

    @field_validator("url", "key", mode="before")
    @classmethod
    def _strip_and_reject_base64(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        text = value.strip()
        if not text:
            return None
        if DATA_URL_RX.match(text):
            raise ValueError("base64 not allowed; upload to R2/GCS first")
        return text

    @field_validator("url", mode="after")
    @classmethod
    def _validate_url_scheme(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value.startswith(_ALLOWED_URL_PREFIXES):
            return value
        if "://" in value:
            raise ValueError("invalid url; expected r2://, s3://, gs:// or http(s)")
        return value


class GalleryItemRef(_CompatModel):
    """Subset of gallery metadata focusing on stored assets."""

    asset: Optional[AssetRef] = None
    key: Optional[str] = None
    mode: Optional[str] = None

    @field_validator("key", mode="before")
    @classmethod
    def _strip_key(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        text = value.strip()
        if DATA_URL_RX.match(text):
            raise ValueError("base64 not allowed; upload to R2/GCS first")
        return text or None


class PosterPayload(_CompatModel):
    """Lean representation that enforces asset references."""

    brand_logo: Optional[AssetRef] = None
    scenario_asset: Optional[AssetRef] = None
    product_asset: Optional[AssetRef] = None
    scenario_key: Optional[str] = None
    product_key: Optional[str] = None
    scenario_image: Optional[str] = None
    product_image: Optional[str] = None
    gallery_items: List[GalleryItemRef] = Field(default_factory=list)

    @field_validator("scenario_key", "product_key", "scenario_image", "product_image", mode="before")
    @classmethod
    def _reject_base64_strings(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        text = value.strip()
        if not text:
            return None
        if DATA_URL_RX.match(text):
            raise ValueError("base64 not allowed; upload to R2/GCS first")
        return text


class GeneratePosterReq(_CompatModel):
    poster: PosterPayload
    trace_id: Optional[str] = None


class GeneratePosterResp(_CompatModel):
    poster_url: str
    key: Optional[str] = None
    template_id: Optional[str] = None


__all__ = [
    "AssetRef",
    "GalleryItemRef",
    "PosterPayload",
    "GeneratePosterReq",
    "GeneratePosterResp",
]
