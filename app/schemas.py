from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, constr
from typing import Literal, Optional


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
        ..., min_items=3, max_items=4
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
    gallery_items: list[PosterGalleryItem] = Field(
        default_factory=list,
        max_items=4,
        description="Bottom gallery entries paired with captions for the series strip.",

    )


class PosterImage(BaseModel):
    """Represents the generated poster asset returned to the client."""

    filename: str = Field(..., description="Suggested filename for the poster image")
    media_type: str = Field(
        "image/png", description="MIME type of the generated poster image"
    )
    data_url: str = Field(
        ..., description="Data URL (base64) that can be displayed directly in browsers"
    )
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)


class GeneratePosterResponse(BaseModel):
    """Aggregated response after preparing all marketing assets."""

    layout_preview: str
    prompt: str
    email_body: str
    poster_image: PosterImage


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

