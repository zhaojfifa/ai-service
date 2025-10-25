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
        width: int = 1024,
        height: int = 1024,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        guidance_scale: Optional[float] = None,
    ) -> bytes:
        response = self.model.generate_images(
            prompt=prompt,
            number_of_images=1,
            negative_prompt=negative_prompt,
            guidance=guidance_scale,
            seed=seed,
        )

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
