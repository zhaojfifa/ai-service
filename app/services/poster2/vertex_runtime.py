"""
Shared Vertex runtime holder for poster2.

This keeps poster2 decoupled from glibatree module globals while still letting
app startup register the already-initialised VertexImagen3 client once.
"""
from __future__ import annotations

from typing import Any

_vertex_poster_client: Any = None


def set_vertex_poster_client(client: Any) -> None:
    global _vertex_poster_client
    _vertex_poster_client = client


def get_vertex_poster_client() -> Any:
    return _vertex_poster_client
