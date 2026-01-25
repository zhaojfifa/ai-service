from __future__ import annotations

from typing import Literal, Optional

from pydantic import Field, constr

from app.schemas import _CompatModel, field_validator


class KitPosterCopy(_CompatModel):
    title: constr(strip_whitespace=True, min_length=1)
    bullets: list[constr(strip_whitespace=True, min_length=1)] = Field(
        default_factory=list, max_length=4
    )
    tagline: Optional[constr(strip_whitespace=True, min_length=1)] = None


class KitPosterOptions(_CompatModel):
    seed: Optional[int] = Field(None, ge=0)
    language: Optional[str] = None
    quality_mode: Literal["stable", "creative"] = "stable"
    allow_auto_fill: bool = True


class KitPosterDraft(_CompatModel):
    template_id: Literal["template_dual", "template_single"]
    variant: Literal["a", "b"]
    product_images: list[constr(strip_whitespace=True, min_length=1)] = Field(
        ..., min_length=1, max_length=2
    )
    copy: KitPosterCopy
    options: KitPosterOptions = Field(default_factory=KitPosterOptions)

    @field_validator("product_images")
    @classmethod
    def _strip_images(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]


__all__ = ["KitPosterCopy", "KitPosterOptions", "KitPosterDraft"]
