from __future__ import annotations

import base64
import logging
import os
from typing import Optional

from vertexai.vision_models import ImageGenerationModel

log = logging.getLogger("ai-service")


class VertexImagen3:
    """Vertex Imagen 3 provider configured via environment variables."""

    def __init__(self) -> None:
        key_b64 = os.getenv("GCP_KEY_B64")
        if key_b64:
            credentials_path = os.path.abspath("gcp-key.json")
            with open(credentials_path, "wb") as handle:
                handle.write(base64.b64decode(key_b64))
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            log.info("[vertex.auth] service account key material written to %s", credentials_path)

        self.project = os.getenv("VERTEX_PROJECT_ID")
        self.location = os.getenv("VERTEX_LOCATION")
        name = os.getenv("VERTEX_IMAGEN_MODEL", "imagen-3.0-generate-001")

        # The Imagen SDK resolves project/location from ADC; name identifies the
        # pre-trained model variant.
        self.model = ImageGenerationModel.from_pretrained(name)
        log.info("[vertex.model] ready name=%s", name)

    def generate(
        self,
        prompt: str,
        *,
        width: Optional[int] = None,
        height: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        add_watermark: Optional[bool] = True,
    ) -> bytes:
        aspect_ratio = self._to_aspect_ratio(width, height)

        effective_add_watermark = True if add_watermark is None else bool(add_watermark)
        if seed is not None and effective_add_watermark:
            log.info("vertex_provider: seed ignored because add_watermark=True")
            seed = None

        params: dict[str, object] = {
            "prompt": prompt,
            "number_of_images": 1,
            "aspect_ratio": aspect_ratio,
            "add_watermark": effective_add_watermark,
        }

        if negative_prompt:
            params["negative_prompt"] = negative_prompt
        if guidance_scale is not None:
            params["guidance_scale"] = guidance_scale
        if seed is not None:
            params["seed"] = seed

        log.debug("[vertex.generate] params=%s", {k: v for k, v in params.items() if k != "prompt"})

        response = self.model.generate_images(**params)

        if not response.images:
            raise RuntimeError("Vertex Imagen returned no images")

        image = response.images[0]
        for attr in ("_image_bytes", "image_bytes"):
            data = getattr(image, attr, None)
            if isinstance(data, (bytes, bytearray)):
                return bytes(data)

        if hasattr(image, "as_bytes"):
            return bytes(image.as_bytes())

        raise RuntimeError("Unable to extract image bytes from Vertex Imagen response")

    @staticmethod
    def _to_aspect_ratio(width: Optional[int], height: Optional[int]) -> str:
        """Translate width/height inputs into the closest supported aspect ratio."""

        if not width or not height:
            return "1:1"

        ratio = width / height
        candidates = {
            "1:1": 1.0,
            "16:9": 16 / 9,
            "9:16": 9 / 16,
            "4:3": 4 / 3,
            "3:4": 3 / 4,
        }

        return min(candidates, key=lambda key: abs(candidates[key] - ratio))
