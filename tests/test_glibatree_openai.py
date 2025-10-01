from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.config import GlibatreeConfig
from app.services.glibatree import OPENAI_IMAGE_SIZE, _request_glibatree_openai


def make_config(**overrides: str | None) -> GlibatreeConfig:
    defaults = {
        "api_url": "https://api.example.com/v1",
        "api_key": "sk-test",
        "model": "gpt-image-1",
        "proxy": None,
        "client": "openai",
    }
    defaults.update(overrides)
    return GlibatreeConfig(**defaults)  # type: ignore[arg-type]


def test_openai_client_initialisation_supports_proxy() -> None:
    config = make_config(proxy="http://127.0.0.1:7890")

    mock_client = MagicMock()
    mock_image = MagicMock()
    mock_image.b64_json = "ZmFrZQ=="
    mock_image.mime_type = "image/png"
    mock_image.size = "800x600"
    mock_image.filename = "poster.png"
    mock_response = MagicMock()
    mock_response.data = [mock_image]
    mock_client.images.generate.return_value = mock_response

    with patch("app.services.glibatree.OpenAI", return_value=mock_client) as patched_openai, patch(
        "app.services.glibatree.httpx.Client"
    ) as patched_httpx:
        httpx_instance = MagicMock()
        patched_httpx.return_value = httpx_instance

        result = _request_glibatree_openai(config, "示例提示词")

    patched_httpx.assert_called_once()
    _args, kwargs = patched_httpx.call_args
    assert kwargs["proxies"] == "http://127.0.0.1:7890"
    patched_openai.assert_called_once_with(
        api_key="sk-test",
        base_url="https://api.example.com/v1",
        http_client=httpx_instance,
    )
    httpx_instance.close.assert_called_once()
    mock_client.images.generate.assert_called_once_with(
        model="gpt-image-1",
        prompt="示例提示词",
        size=OPENAI_IMAGE_SIZE,
        response_format="b64_json",
    )

    assert result.filename == "poster.png"
    assert result.media_type == "image/png"
    assert result.width == 800 and result.height == 600
    assert result.data_url.startswith("data:image/png;base64,ZmFrZQ==")


def test_openai_client_without_proxy_omits_http_client() -> None:
    config = make_config(api_url=None, proxy=None)

    mock_client = MagicMock()
    mock_image = MagicMock()
    mock_image.b64_json = "ZmFrZQ=="
    mock_image.mime_type = None
    mock_image.size = None
    mock_image.filename = None
    mock_response = MagicMock()
    mock_response.data = [mock_image]
    mock_client.images.generate.return_value = mock_response

    with patch("app.services.glibatree.OpenAI", return_value=mock_client) as patched_openai, patch(
        "app.services.glibatree.httpx.Client"
    ) as patched_httpx:
        result = _request_glibatree_openai(config, "prompt")

    patched_httpx.assert_not_called()
    patched_openai.assert_called_once_with(api_key="sk-test")
    mock_client.images.generate.assert_called_once_with(
        model="gpt-image-1",
        prompt="prompt",
        size=OPENAI_IMAGE_SIZE,
        response_format="b64_json",
    )

    assert result.media_type == "image/png"
    assert result.filename == "poster.png"
    assert result.width == 1024 and result.height == 1024
    assert result.data_url == "data:image/png;base64,ZmFrZQ=="
