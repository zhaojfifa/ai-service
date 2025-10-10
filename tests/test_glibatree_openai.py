from __future__ import annotations

import unittest
from unittest.mock import ANY, MagicMock, patch

try:
    from app.config import GlibatreeConfig
    from app.services.glibatree import (
        OPENAI_IMAGE_SIZE,
        TemplateResources,
        _request_glibatree_openai_edit,
    )
    from PIL import Image
except ModuleNotFoundError as exc:  # pragma: no cover - exercised via skip
    DEPENDENCY_ERROR = exc
    GlibatreeConfig = TemplateResources = _request_glibatree_openai_edit = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment]
else:
    DEPENDENCY_ERROR = None


@unittest.skipIf(DEPENDENCY_ERROR is not None, f"Missing dependency: {DEPENDENCY_ERROR}")
class GlibatreeOpenAITestCase(unittest.TestCase):
    def make_config(self, **overrides: str | None) -> GlibatreeConfig:  # type: ignore[override]
        defaults = {
            "api_url": "https://api.example.com/v1",
            "api_key": "sk-test",
            "model": "gpt-image-1",
            "proxy": None,
            "client": "openai",
        }
        defaults.update(overrides)
        return GlibatreeConfig(**defaults)  # type: ignore[arg-type]

    def test_openai_client_initialisation_supports_proxy(self) -> None:
        config = self.make_config(proxy="http://127.0.0.1:7890")

        mock_client = MagicMock()
        mock_image = MagicMock()
        mock_image.b64_json = "ZmFrZQ=="
        mock_image.mime_type = "image/png"
        mock_image.size = "800x600"
        mock_image.filename = "poster.png"
        mock_response = MagicMock()
        mock_response.data = [mock_image]
        mock_client.images.edit.return_value = mock_response

        locked_frame = Image.new("RGBA", (1024, 1024), (255, 255, 255, 255))
        template = TemplateResources(
            id="template_dual",
            spec={"size": {"width": 1024, "height": 1024}, "slots": {}},
            template=Image.new("RGBA", (1024, 1024), (0, 0, 0, 0)),
            mask_background=Image.new("RGBA", (1024, 1024), (255, 255, 255, 255)),
            mask_scene=None,
        )

        with patch("app.services.glibatree.OpenAI", return_value=mock_client) as patched_openai, patch(
            "app.services.glibatree.httpx.Client"
        ) as patched_httpx:
            httpx_instance = MagicMock()
            patched_httpx.return_value = httpx_instance

            result = _request_glibatree_openai_edit(config, "示例提示词", locked_frame, template)

        patched_httpx.assert_called_once()
        _args, kwargs = patched_httpx.call_args
        assert kwargs["proxies"] == "http://127.0.0.1:7890"
        patched_openai.assert_called_once_with(
            api_key="sk-test",
            base_url="https://api.example.com/v1",
            http_client=httpx_instance,
        )
        httpx_instance.close.assert_called_once()
        mock_client.images.edit.assert_called_once_with(
            model="gpt-image-1",
            prompt="示例提示词",
            size=OPENAI_IMAGE_SIZE,
            response_format="b64_json",
            image=ANY,
            mask=ANY,
        )

        assert result.filename == "poster.png"
        assert result.media_type == "image/png"
        assert result.data_url or result.url
        if result.data_url:
            assert result.data_url.startswith("data:image/png;base64,")

    def test_openai_client_without_proxy_omits_http_client(self) -> None:
        config = self.make_config(api_url=None, proxy=None)

        mock_client = MagicMock()
        mock_image = MagicMock()
        mock_image.b64_json = "ZmFrZQ=="
        mock_image.mime_type = None
        mock_image.size = None
        mock_image.filename = None
        mock_response = MagicMock()
        mock_response.data = [mock_image]
        mock_client.images.edit.return_value = mock_response

        locked_frame = Image.new("RGBA", (1024, 1024), (255, 255, 255, 255))
        template = TemplateResources(
            id="template_dual",
            spec={"size": {"width": 1024, "height": 1024}, "slots": {}},
            template=Image.new("RGBA", (1024, 1024), (0, 0, 0, 0)),
            mask_background=Image.new("RGBA", (1024, 1024), (255, 255, 255, 255)),
            mask_scene=None,
        )

        with patch("app.services.glibatree.OpenAI", return_value=mock_client) as patched_openai, patch(
            "app.services.glibatree.httpx.Client"
        ) as patched_httpx:
            result = _request_glibatree_openai_edit(config, "prompt", locked_frame, template)

        patched_httpx.assert_not_called()
        patched_openai.assert_called_once_with(api_key="sk-test")
        mock_client.images.edit.assert_called_once_with(
            model="gpt-image-1",
            prompt="prompt",
            size=OPENAI_IMAGE_SIZE,
            response_format="b64_json",
            image=ANY,
            mask=ANY,
        )

        assert result.media_type == "image/png"
        assert result.filename == "poster.png"
        assert result.data_url or result.url
        if result.data_url:
            assert result.data_url.startswith("data:image/png;base64,")


if __name__ == "__main__":
    unittest.main()
