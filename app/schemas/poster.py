"""Poster request/response helpers enforcing URL/Key asset usage."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from app.schemas import DATA_URL_RX, _CompatModel, field_validator

_ALLOWED_URL_PREFIXES = ("r2://", "s3://", "gs://", "https://", "http://")
_MAX_INLINE_FIELD = 4096


class AssetUrl(_CompatModel):
    """Reference to an asset that must already live in object storage."""

    url: str = Field(..., description="Pointer to an uploaded asset (R2/GCS/HTTP).")
    key: Optional[str] = Field(
        None,
        description="Optional object storage key associated with the asset reference.",
    )

    @field_validator("url", mode="before")
    @classmethod
    def _coerce(cls, value: Any) -> str:
        if isinstance(value, cls):  # pragma: no cover - defensive
            return value.url
        if isinstance(value, dict):
            candidate = value.get("url") or value.get("key")
            if isinstance(candidate, str):
                return candidate
        if isinstance(value, str):
            return value
        raise TypeError("asset url must be provided as string or dict with url/key")

    @field_validator("key", mode="before")
    @classmethod
    def _coerce_key(cls, value: Any) -> Optional[str]:
        if isinstance(value, cls):  # pragma: no cover - defensive
            return value.key
        if isinstance(value, dict):
            candidate = value.get("key")
            if isinstance(candidate, str):
                return candidate
        if isinstance(value, str):
            return value
        return value

    @field_validator("url")
    @classmethod
    def _validate(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("asset url cannot be empty")
        if DATA_URL_RX.match(text):
            raise ValueError("base64 not allowed — upload to R2/GCS and pass key/url")
        if len(text) > _MAX_INLINE_FIELD:
            raise ValueError("asset url too long; base64/data_url not allowed")
        if not text.startswith(_ALLOWED_URL_PREFIXES):
            raise ValueError("invalid url; expected r2://, s3://, gs:// or http(s)")
        return text

    @field_validator("key")
    @classmethod
    def _validate_key(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        text = value.strip()
        if not text:
            return None
        if DATA_URL_RX.match(text):
            raise ValueError("base64 not allowed — upload to R2/GCS and pass key/url")
        if len(text) > _MAX_INLINE_FIELD:
            raise ValueError("asset key too long; base64/data_url not allowed")
        return text


class PosterPayload(_CompatModel):
    """Minimal poster payload required by the simplified poster API."""

    brand_name: str = Field(..., description="Brand displayed on the poster.")
    agent_name: Optional[str] = Field(
        None, description="Agency or channel partner name (optional)."
    )
    product_name: Optional[str] = Field(
        None, description="Product name rendered on the poster (optional)."
    )
    scenario_image: AssetUrl = Field(
        ..., description="Primary background image reference (URL/Key)."
    )
    brand_logo: Optional[AssetUrl] = Field(
        None, description="Optional brand logo reference stored in R2/GCS."
    )
    template_id: Optional[str] = Field(
        None, description="Template identifier controlling the poster layout."
    )
    size: Optional[Literal["1024x1024", "1080x1350", "1080x1920", "1920x1080"]] = Field(
        "1024x1024", description="Target render size in WIDTHxHEIGHT format."
    )

    @field_validator("scenario_image", "brand_logo", mode="before")
    @classmethod
    def _coerce_assets(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, AssetUrl):
            return value
        if isinstance(value, dict):
            if "url" not in value and isinstance(value.get("key"), str):
                return {"url": value["key"], "key": value["key"]}
            return value
        if isinstance(value, str):
            return {"url": value}
        raise TypeError("asset reference must be string or mapping with url")


class GeneratePosterReq(_CompatModel):
    poster: PosterPayload
    trace_id: Optional[str] = None


class GeneratePosterResp(_CompatModel):
    poster_url: str
    key: Optional[str] = None
    template_id: Optional[str] = None


__all__ = ["AssetUrl", "PosterPayload", "GeneratePosterReq", "GeneratePosterResp"]
