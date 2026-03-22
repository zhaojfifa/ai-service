from __future__ import annotations

import asyncio

import pytest

from app.services.poster2.background import VertexBackgroundProvider
from app.services.poster2.vertex_runtime import (
    get_vertex_poster_client,
    set_vertex_poster_client,
)


class _FakeVertexPosterClient:
    def __init__(self):
        self.calls = []

    async def generate_async(self, **kwargs):
        self.calls.append(kwargs)
        return [b"vertex-image-bytes"]


class _FakeVertexPosterBytesClient:
    def __init__(self):
        self.calls = []

    def generate_bytes(self, **kwargs):
        self.calls.append(kwargs)
        return b"vertex-image-bytes-from-generate-bytes"


def test_vertex_background_provider_reads_shared_runtime_holder():
    client = _FakeVertexPosterClient()
    set_vertex_poster_client(client)

    result = asyncio.run(
        VertexBackgroundProvider().generate(
            prompt="clean studio",
            width=1024,
            height=1024,
            seed=42,
            negative_prompt="text, logo",
        )
    )

    assert result == b"vertex-image-bytes"
    assert client.calls[0]["prompt"] == "clean studio"
    assert get_vertex_poster_client() is client


def test_vertex_background_provider_falls_back_to_generate_bytes():
    client = _FakeVertexPosterBytesClient()
    set_vertex_poster_client(client)

    result = asyncio.run(
        VertexBackgroundProvider().generate(
            prompt="clean studio",
            width=1024,
            height=1024,
            seed=42,
            negative_prompt="text, logo",
        )
    )

    assert result == b"vertex-image-bytes-from-generate-bytes"
    assert client.calls[0]["prompt"] == "clean studio"
    assert client.calls[0]["width"] == 1024
    assert client.calls[0]["height"] == 1024
    assert client.calls[0]["negative_prompt"] == "text, logo"


def test_vertex_background_provider_raises_when_runtime_unset():
    set_vertex_poster_client(None)

    with pytest.raises(RuntimeError, match="not initialised"):
        asyncio.run(
            VertexBackgroundProvider().generate(
                prompt="clean studio",
                width=1024,
                height=1024,
                seed=42,
                negative_prompt="text, logo",
            )
        )
