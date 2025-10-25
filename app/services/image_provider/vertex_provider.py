from __future__ import annotations

import os
from typing import Optional

from vertexai.vision_models import ImageGenerationModel


class VertexImagen3:
    """Legacy Vertex AI Imagen 3 provider kept for fallback deployments."""

    def __init__(self) -> None:
        name = os.getenv("VERTEX_IMAGEN_MODEL", "imagen-3.0-generate-001")
        self.model = ImageGenerationModel.from_pretrained(name)

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
