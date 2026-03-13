"""Poster 2.0 — structure/style decoupled poster generation pipeline."""

from .contracts import (
    AssetRef,
    StyleSpec,
    PosterSpec,
    TextSlotSpec,
    ImageSlotSpec,
    GalleryStripSpec,
    TemplateSpec,
    ResolvedAssets,
    RenderManifest,
)

# PosterPipeline is NOT imported here to avoid pulling in boto3/r2_client
# at module load time.  Import explicitly when needed:
#   from app.services.poster2.pipeline import PosterPipeline

__all__ = [
    "AssetRef",
    "StyleSpec",
    "PosterSpec",
    "TextSlotSpec",
    "ImageSlotSpec",
    "GalleryStripSpec",
    "TemplateSpec",
    "ResolvedAssets",
    "RenderManifest",
]
