"""Image provider factory dedicated to Vertex Imagen 3."""
from __future__ import annotations

from typing import Optional

from .vertex_provider import VertexImagen3

_PROVIDER: Optional[VertexImagen3] = None


def get_provider() -> VertexImagen3:
    """Return the cached Vertex Imagen provider instance."""

    global _PROVIDER
    if _PROVIDER is None:
        _PROVIDER = VertexImagen3()
    return _PROVIDER
