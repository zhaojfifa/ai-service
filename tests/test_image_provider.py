import base64

from app.services.image_provider import ImageProvider


def test_generate_placeholder_when_backend_missing(monkeypatch):
    monkeypatch.delenv("IMAGE_API_BASE", raising=False)
    monkeypatch.delenv("IMAGE_API_KIND", raising=False)
    provider = ImageProvider()

    data = provider.generate(prompt="Placeholder", size="64x48")

    assert data.startswith(b"\xff\xd8")  # JPEG magic number
    assert len(data) > 100


def test_generate_via_openai_backend(monkeypatch):
    fake_b64 = base64.b64encode(b"openai-image").decode()
    calls: dict[str, object] = {}

    class DummyResponse:
        status_code = 200

        def json(self):
            return {"data": [{"b64_json": fake_b64}]}

    class DummyClient:
        def __init__(self, *args, **kwargs):
            calls["kwargs"] = kwargs

        def __enter__(self):
            calls["entered"] = True
            return self

        def __exit__(self, exc_type, exc, tb):
            calls["exited"] = True

        def post(self, url, json, headers):
            calls["request"] = {"url": url, "json": json, "headers": headers}
            return DummyResponse()

    monkeypatch.setenv("IMAGE_API_BASE", "https://example.com")
    monkeypatch.setenv("IMAGE_API_KIND", "openai")
    monkeypatch.setattr("app.services.image_provider.httpx.Client", DummyClient)

    provider = ImageProvider()
    result = provider.generate(prompt="Hummingbird", size="512x512")

    assert result == base64.b64decode(fake_b64)
    request = calls["request"]
    assert request["url"] == "https://example.com/v1/images/generations"
    assert request["json"]["prompt"] == "Hummingbird"
    assert request["json"]["size"] == "512x512"
    assert request["headers"]["Content-Type"] == "application/json"


def test_generate_via_vertex_backend(monkeypatch):
    calls: dict[str, object] = {}

    class DummyResponse:
        status_code = 200
        content = b"vertex-bytes"

    class DummyClient:
        def __init__(self, *args, **kwargs):
            calls["kwargs"] = kwargs

        def __enter__(self):
            calls["entered"] = True
            return self

        def __exit__(self, exc_type, exc, tb):
            calls["exited"] = True

        def post(self, url, json, headers):
            calls["request"] = {"url": url, "json": json, "headers": headers}
            return DummyResponse()

    monkeypatch.setenv("IMAGE_API_BASE", "https://vertex.example.com")
    monkeypatch.setenv("IMAGE_API_KIND", "vertex")
    monkeypatch.setattr("app.services.image_provider.httpx.Client", DummyClient)

    provider = ImageProvider()
    result = provider.generate(prompt="Product", width=128, height=256)

    assert result == b"vertex-bytes"
    request = calls["request"]
    assert request["url"] == "https://vertex.example.com/generate"
    assert request["json"]["size"] == "128x256"
    assert request["json"]["prompt"] == "Product"
