"""Payload-facing models shared between the API layer and prompt builders."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class PosterSpec(BaseModel):
    """Thin view model describing copy choices for poster generation."""

    lang: Literal["en", "zh"] = Field(
        default="en", description="Language of copy surfaced on the poster"
    )
    title: Optional[str] = Field(
        default=None,
        description="Primary headline presented on the poster",
    )
    subtitle: Optional[str] = Field(
        default=None,
        description="Secondary supporting line shown under the headline",
    )
    features: List[str] = Field(
        default_factory=list,
        description="Feature call-outs displayed alongside the hero product",
    )
    brand_name: Optional[str] = Field(
        default=None, description="Displayed brand name for the poster copy"
    )

    class Config:
        extra = "ignore"

    def ensure_defaults(
        self,
        *,
        default_title: str,
        default_subtitle: str,
        default_features: List[str],
    ) -> "PosterSpec":
        """Return a copy with fallbacks applied for missing copy fields."""

        payload = self.model_dump(exclude_none=False)
        payload["title"] = (self.title or default_title).strip()
        payload["subtitle"] = (self.subtitle or default_subtitle).strip()
        features = [item.strip() for item in self.features if item and item.strip()]
        resolved = features or list(default_features)
        payload["features"] = resolved[:4]
        return type(self)(**payload)

